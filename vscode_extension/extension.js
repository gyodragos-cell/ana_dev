"use strict";

const http = require("http");
const fs = require("fs");
const os = require("os");
const path = require("path");
const vscode = require("vscode");
const cp = require("child_process");

let runtimeProcess = undefined;
let logBuffer = [];
let panel = undefined;
let logChannel = undefined;
let liveConsoleTimer = undefined;
let mcpTailProcess = undefined;
let liveWatchdogProcess = undefined;
let mirrorWatchProcess = undefined;
let voiceBridgeProcess = undefined;
let voiceInboxProcess = undefined;
let conversationAuditTailProcess = undefined;
let lastVoiceLine = "";
let lastVoiceAt = 0;
let lastHeartbeatLine = "";
let lastAccessibilityCue = "";
let lastAccessibilityCueAt = 0;
let lastOrientationCue = "";
let lastOrientationCueAt = 0;
let codexGuardInFlight = false;
let lastCodexGuardAt = 0;
const MAX_LOG_LINES = 500;

function getConfig() {
  const config = vscode.workspace.getConfiguration("anaMax");
  return {
    safeMode: config.get("safeMode", true),
    runtimeUrl: config.get("runtimeUrl", "http://127.0.0.1:8766/mcp"),
    runtimeRoot: config.get("runtimeRoot", ""),
    pythonPath: config.get("pythonPath", ""),
    runtimePort: config.get("runtimePort", 8766),
    dashboardUrl: config.get("dashboardUrl", "http://127.0.0.1:8787"),
    preferredBrowserPath: config.get("preferredBrowserPath", "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"),
    codexServerName: config.get("codexServerName", "anamax"),
    autoStartRuntime: config.get("autoStartRuntime", true),
    goldenRulePreflight: config.get("goldenRulePreflight", true),
    codexGuardAutoStart: config.get("codexGuardAutoStart", true),
    codexGuardMinIntervalMs: config.get("codexGuardMinIntervalMs", 60000),
    codexGuardStrict: config.get("codexGuardStrict", false),
    voiceReadout: config.get("voiceReadout", true),
    voiceReadoutDirect: config.get("voiceReadoutDirect", false),
    voiceReadoutClipboard: config.get("voiceReadoutClipboard", true),
    voiceReadoutLogEvents: config.get("voiceReadoutLogEvents", true),
    voiceAccessibilityCues: config.get("voiceAccessibilityCues", true),
    voiceButtonAnnouncements: config.get("voiceButtonAnnouncements", true),
    voiceActionCompletion: config.get("voiceActionCompletion", true),
    voiceOrientationCues: config.get("voiceOrientationCues", true),
    voiceOrientationMinIntervalMs: config.get("voiceOrientationMinIntervalMs", 20000),
    voiceCueBeeps: config.get("voiceCueBeeps", true),
    voiceReadoutMaxChars: config.get("voiceReadoutMaxChars", 260),
    voiceFullReadout: config.get("voiceFullReadout", true),
    voiceFullReadoutMaxChars: config.get("voiceFullReadoutMaxChars", 6000),
    voiceFullReadoutChunkChars: config.get("voiceFullReadoutChunkChars", 700),
    voiceReadoutMinIntervalMs: config.get("voiceReadoutMinIntervalMs", 1500),
    voiceInboxAutoStart: config.get("voiceInboxAutoStart", true),
    voiceInboxAutoSubmit: config.get("voiceInboxAutoSubmit", true),
    voiceInboxPressEnter: config.get("voiceInboxPressEnter", true),
    voiceInboxDuration: config.get("voiceInboxDuration", 8),
    voiceInboxSubmitPrefix: config.get("voiceInboxSubmitPrefix", "codex,ana"),
    voiceInboxAllowedTitles: config.get("voiceInboxAllowedTitles", "Visual Studio Code,Code,Codex,ChatGPT"),
    conversationAuditLiveAutoStart: config.get("conversationAuditLiveAutoStart", true)
  };
}

function csvSetting(value) {
  return String(value || "")
    .split(",")
    .map(item => item.trim())
    .filter(Boolean);
}

function runtimeBaseUrl(config) {
  return config.runtimeUrl.replace(/\/mcp\/?$/, "");
}

async function getHealth(config) {
  return requestGetJson(`${runtimeBaseUrl(config)}/health`);
}

function requestGetJson(url) {
  return new Promise((resolve, reject) => {
    const req = http.get(url, (res) => {
      let data = "";
      res.setEncoding("utf8");
      res.on("data", (chunk) => data += chunk);
      res.on("end", () => {
        if (res.statusCode < 200 || res.statusCode >= 300) {
          reject(new Error(`HTTP ${res.statusCode}: ${data}`));
          return;
        }
        try {
          resolve(JSON.parse(data));
        } catch (e) {
          reject(new Error(`Invalid JSON from ${url}: ${e.message}`));
        }
      });
    });
    req.setTimeout(5000, () => {
      req.destroy(new Error(`Request timed out: ${url}`));
    });
    req.on("error", reject);
  });
}

function resolveRuntimePaths(config) {
  const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri?.fsPath || "";
  const remoteName = vscode.env.remoteName || "";
  const baseRoot = path.resolve(config.runtimeRoot || workspaceRoot || "");
  const searchedRoots = [
    process.env.ANA_MAX_RUNTIME_ROOT || "",
    baseRoot,
    path.join(baseRoot, "ANA_MAX"),
    workspaceRoot ? path.resolve(workspaceRoot) : "",
    workspaceRoot ? path.join(path.resolve(workspaceRoot), "ANA_MAX") : ""
  ].filter((item, index, list) => item && list.indexOf(item) === index);
  const runtimeRoot = searchedRoots.find(candidate => fs.existsSync(path.join(candidate, "main.py"))) || baseRoot;
  const workspaceVenvPython = workspaceRoot ? path.join(path.resolve(workspaceRoot), ".venv", "Scripts", "python.exe") : "";
  const runtimeVenvPython = path.join(runtimeRoot, "venv", "Scripts", "python.exe");
  const defaultPythonPath = fs.existsSync(workspaceVenvPython) ? workspaceVenvPython : runtimeVenvPython;
  const pythonPath = config.pythonPath
    ? path.resolve(config.pythonPath)
    : (fs.existsSync(defaultPythonPath) ? defaultPythonPath : "python");
  return {
    runtimeRoot,
    pythonPath,
    mainPy: path.join(runtimeRoot, "main.py"),
    searchedRoots,
    remoteName
  };
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function waitForRuntimeHealth(config, attempts = 20, delayMs = 750) {
  let lastError = undefined;
  for (let index = 0; index < attempts; index += 1) {
    try {
      const health = await getHealth(config);
      if (health && health.status === "online" && health.mcp_ready) {
        return health;
      }
      lastError = new Error(`health not ready: status=${health?.status} ready=${health?.mcp_ready}`);
    } catch (error) {
      lastError = error;
    }
    await sleep(delayMs);
  }
  throw lastError || new Error("Runtime health did not become ready.");
}

function remoteRuntimeHint(paths) {
  if (!paths.remoteName) {
    return "";
  }
  return ` Remote window detected (${paths.remoteName}); set anaMax.runtimeRoot to the local Windows ANA_MAX folder if desktop/control tools should run on this PC.`;
}

function addToBuffer(line) {
  logBuffer.push(line);
  if (logBuffer.length > MAX_LOG_LINES) {
    logBuffer.shift();
  }
}

function appendLiveLog(message) {
  const line = `[${new Date().toISOString()}] ${String(message || "").replace(/\r/g, "")}\n`;
  if (logChannel) logChannel.append(line);
  addToBuffer(line);
  if (panel) post(panel, "runtimeLog", line);
  queueImportantVoice(message);
}

function showLiveConsole() {
  if (!logChannel) {
    logChannel = vscode.window.createOutputChannel("ANA MAX MCP");
  }
  logChannel.show(true);
  try {
    const config = getConfig();
    const paths = resolveRuntimePaths(config);
    if (config.voiceReadout) {
      startVoiceBridge(config, paths);
    }
    startVoiceInboxDaemon(config, paths);
    startConversationAuditTail(config, paths);
  } catch {
    // Voice is assistive only; never block the operator console.
  }
}

function workspaceRootPath() {
  return vscode.workspace.workspaceFolders?.[0]?.uri?.fsPath || "";
}

function anaRootPath(paths) {
  const root = workspaceRootPath();
  if (root) {
    const candidate = path.join(root, "ANA_MAX");
    if (fs.existsSync(candidate)) {
      return candidate;
    }
  }
  return paths?.runtimeRoot || root;
}

function voiceQueuePath(config, paths) {
  return path.join(anaRootPath(paths || resolveRuntimePaths(config)), "voice_queue.txt");
}

function voiceTempDir(config, paths) {
  return path.join(anaRootPath(paths || resolveRuntimePaths(config)), "voice_temp");
}

function voiceInboxStatusPath(config, paths) {
  return path.join(anaRootPath(paths || resolveRuntimePaths(config)), "memory", "voice_inbox_status.txt");
}

function writeVoiceInboxStatus(config, paths, status) {
  try {
    const statusPath = voiceInboxStatusPath(config, paths);
    fs.mkdirSync(path.dirname(statusPath), { recursive: true });
    fs.writeFileSync(statusPath, `${new Date().toISOString()} ${status}`, "utf8");
  } catch {
    // Status is diagnostic only; never block voice startup.
  }
}

function sanitizeVoiceText(text, maxChars) {
  const cleaned = String(text || "")
    .replace(/\r/g, "")
    .replace(/\[[0-9TZ:.\-]+\]\s*/g, "")
    .replace(/\b[a-z]:\\users\\[^"'\s]+/gi, "local path")
    .replace(/screenshots\\view_[0-9]+\.png/gi, "screenshot")
    .replace(/\s+/g, " ")
    .trim();
  if (!cleaned) {
    return "";
  }
  const limit = Math.max(80, Number(maxChars) || 260);
  return cleaned.length > limit ? `${cleaned.slice(0, limit - 3)}...` : cleaned;
}

function voiceTextFromLogLine(rawLine, config) {
  const line = String(rawLine || "").trim();
  if (!line) {
    return "";
  }
  if (/\[MIRROR\]/i.test(line)) {
    return mirrorOrientationSummary(line, config);
  }
  if (/\[(VOICE|HEARTBEAT|CONSOLE)\b/i.test(line)) {
    return "";
  }
  if (/\[CONVERSATION-LIVE\]/i.test(line)) {
    return "";
  }
  if (/screenshots\\view_|events=\d+|app=Code title=/i.test(line)) {
    return "";
  }
  if (/\b(api key|password|token|secret|private key)\b/i.test(line)) {
    return "ANA skipped a sensitive log line.";
  }

  if (config.voiceReadoutLogEvents) {
    if (/\[VOICE-INBOX\]/i.test(line)) {
      const inboxSummary = voiceInboxLogSummary(line);
      return inboxSummary || sanitizeVoiceText(line, config.voiceReadoutMaxChars);
    }
    let match = line.match(/\[GOLDEN-RULE\].*ANA Codex Companion:\s+([A-Z]+)/i);
    if (match) {
      return `ANA preflight ${match[1]}.`;
    }
    if (/\[GOLDEN-RULE\].*preflight start/i.test(line)) {
      return "ANA preflight start.";
    }
    match = line.match(/\[LIVE-BEHAVIOR\].*ANA Live Behavior:\s+([A-Z]+)/i);
    if (match) {
      return `Live behavior ${match[1]}.`;
    }
    if (/\[LIVE-BEHAVIOR\].*Check start/i.test(line)) {
      return "Live behavior check start.";
    }
    match = line.match(/\[NUCLEUS\].*ANA Nucleus:\s+([A-Z]+).*?\(([^)]*)\)/i);
    if (match) {
      return sanitizeVoiceText(`Nucleus ${match[1]}. ${match[2]}.`, config.voiceReadoutMaxChars);
    }
    match = line.match(/\[OPERATOR-STATUS\].*ANA Operator Status:.*vsix=([^\s]+).*mcp_ready=([^\s]+).*tools=([0-9]+)/i);
    if (match) {
      return `Operator status. VSIX ${match[1]}. MCP ready ${match[2]}. Tools ${match[3]}.`;
    }
    match = line.match(/\[RELOAD-READINESS\].*ANA Reload Readiness:.*reload_needed=([^\s]+).*behavior=([A-Z]+)/i);
    if (match) {
      return `Reload readiness. Reload needed ${match[1]}. Behavior ${match[2]}.`;
    }
    match = line.match(/\[RELOAD-CONSISTENCY\].*ANA Reload Consistency:\s+([A-Z]+).*aligned=([^\s]+)/i);
    if (match) {
      return `Reload consistency ${match[1]}. Aligned ${match[2]}.`;
    }
    match = line.match(/\[POST-RELOAD\].*ANA Post Reload:\s+([A-Z]+)/i);
    if (match) {
      return `Post reload ${match[1]}.`;
    }
    match = line.match(/\[CONVERSATION-AUDIT\]\s+([A-Z]+).*events=([0-9]+).*spoken=([0-9]+)/i);
    if (match) {
      return `Conversation audit ${match[1]}. ${match[2]} events. ${match[3]} spoken.`;
    }
    match = line.match(/\bTOOL START name=([a-zA-Z0-9_]+)/);
    if (match) {
      return `Tool start ${match[1]}.`;
    }
    match = line.match(/\bTOOL END name=([a-zA-Z0-9_]+) status=([a-zA-Z0-9_]+)/);
    if (match) {
      const message = line.match(/message='([^']+)'/)?.[1] || "";
      return sanitizeVoiceText(`Tool end ${match[1]} ${match[2]}. ${message}`, config.voiceReadoutMaxChars);
    }
    match = line.match(/\btools\/call start name=([a-zA-Z0-9_]+)/);
    if (match) {
      return `MCP call start ${match[1]}.`;
    }
    match = line.match(/\btools\/call end name=([a-zA-Z0-9_]+).*success=([A-Za-z]+)/);
    if (match) {
      return `MCP call end ${match[1]} success ${match[2]}.`;
    }
    match = line.match(/\bOK health=online tools=([0-9]+)/i);
    if (match) {
      return `Watchdog health online. Tools ${match[1]}.`;
    }
    if (/\b(COACH WARN|WARN|ERROR|FAIL)\b/i.test(line)) {
      return sanitizeVoiceText(line, config.voiceReadoutMaxChars);
    }
    if (/\[(START|AUTO-START|ACTION start|ACTION end|ACTION fail|TOOL start|TOOL end|VOICE-INBOX|CONVERSATION-AUDIT|GOLDEN-RULE|AUDIT|NUCLEUS|POST-RELOAD|OPERATOR-STATUS|CONTEXT-MAPS|RELOAD-READINESS|RELOAD-CONSISTENCY|LIVE-BEHAVIOR)\]/i.test(line)) {
      return sanitizeVoiceText(line, config.voiceReadoutMaxChars);
    }
  }

  const important = [
    /\[ANA\]/i,
    /\[ANA challenge\]/i,
    /\[CODEX\]/i,
    /\[NEXT\]/i,
    /\[GOLDEN-RULE/i,
    /\[AUDIT\]/i,
    /\[ACTION fail\]/i,
    /\[CODEX-COMPANION\].*ANA Codex Companion:/i,
    /\[NUCLEUS\].*ANA Nucleus:/i,
    /\[AUTONOMY\].*ANA Autonomy:/i,
    /\[QUALITY\].*ANA Lab Quality Gate:/i,
    /\[NO-RELOAD\].*ANA No-Reload Gate:/i,
    /\[POST-RELOAD\].*ANA Post Reload:/i,
    /\[OPERATOR-STATUS\].*ANA Operator Status:/i,
    /\[REVIEW-BATCH\].*ANA Review Batch:/i,
    /\[LIVE-BEHAVIOR\].*ANA Live Behavior:/i,
    /\[RELOAD-READINESS\].*ANA Reload Readiness:/i,
    /\[RELOAD-CONSISTENCY\].*ANA Reload Consistency:/i,
    /\b(PASS|WARN|FAIL)\b.*\b(ANA|MCP|trust|tools|behavior|identity|maps)\b/i
  ];
  if (!important.some(pattern => pattern.test(line))) {
    return "";
  }
  return sanitizeVoiceText(line, config.voiceReadoutMaxChars);
}

function startVoiceBridge(config = getConfig(), paths = resolveRuntimePaths(config)) {
  if (!config.voiceReadout || voiceBridgeProcess) {
    return !!voiceBridgeProcess;
  }
  const anaRoot = anaRootPath(paths);
  const script = path.join(anaRoot, "chat_voice_bridge.py");
  if (!fs.existsSync(script)) {
    appendLiveLog(`[VOICE fail] Chat voice bridge script not found: ${script}`);
    return false;
  }
  const pythonPath = workspacePythonPath(config, paths);
  appendLiveLog(`[VOICE] Starting filtered voice bridge: ${script} clipboard=${config.voiceReadoutClipboard ? "on" : "off"}`);
  const args = [
    script,
    "--poll",
    "0.7",
    "--max-chars",
    `${Math.max(80, Number(config.voiceReadoutMaxChars) || 260)}`
  ];
  if (config.voiceFullReadout) {
    args.push(
      "--full-readout",
      "--full-max-chars",
      `${Math.max(500, Number(config.voiceFullReadoutMaxChars) || 6000)}`,
      "--chunk-chars",
      `${Math.max(120, Number(config.voiceFullReadoutChunkChars) || 700)}`
    );
  }
  if (!config.voiceReadoutClipboard) {
    args.push("--no-clipboard");
  }
  voiceBridgeProcess = cp.spawn(pythonPath, args, {
    cwd: anaRoot,
    env: { ...process.env, PYTHONUNBUFFERED: "1" },
    windowsHide: true
  });
  voiceBridgeProcess.stdout.on("data", (data) => appendLiveLog(`[VOICE] ${data.toString().trimEnd()}`));
  voiceBridgeProcess.stderr.on("data", (data) => appendLiveLog(`[VOICE error] ${data.toString().trimEnd()}`));
  voiceBridgeProcess.on("close", (code) => {
    appendLiveLog(`[VOICE] stopped code=${code}`);
    voiceBridgeProcess = undefined;
  });
  return true;
}

function startVoiceInboxDaemon(config = getConfig(), paths = resolveRuntimePaths(config)) {
  if (!config.voiceInboxAutoStart || voiceInboxProcess) {
    return !!voiceInboxProcess;
  }
  const script = anaScriptPath(paths, "ana_voice_inbox.py");
  if (!fs.existsSync(script)) {
    appendLiveLog(`[VOICE-INBOX fail] Voice inbox script not found: ${script}`);
    writeVoiceInboxStatus(config, paths, "script_not_found");
    return false;
  }
  const pythonPath = workspacePythonPath(config, paths);
  const seconds = Math.max(2, Math.min(Number(config.voiceInboxDuration) || 8, 30));
  const args = [
    script,
    "--continuous",
    "--duration",
    `${seconds}`,
    "--copy",
    "--pause",
    "0.3"
  ];
  if (config.voiceInboxAutoSubmit) {
    args.push("--auto-submit");
  }
  if (config.voiceInboxPressEnter) {
    args.push("--press-enter");
  }
  for (const prefix of csvSetting(config.voiceInboxSubmitPrefix)) {
    args.push("--submit-prefix", prefix);
  }
  for (const title of csvSetting(config.voiceInboxAllowedTitles)) {
    args.push("--allowed-title", title);
  }
  appendLiveLog(
    `[VOICE-INBOX] Starting microphone daemon: ${script} autoSubmit=${config.voiceInboxAutoSubmit ? "on" : "off"} prefix=${csvSetting(config.voiceInboxSubmitPrefix).join("|")}`
  );
  writeVoiceInboxStatus(config, paths, "spawn_requested");
  voiceInboxProcess = cp.spawn(pythonPath, args, {
    cwd: workspaceRootPath() || anaRootPath(paths),
    env: { ...process.env, PYTHONUNBUFFERED: "1" },
    windowsHide: true
  });
  voiceInboxProcess.stdout.on("data", (data) => {
    const text = data.toString().trimEnd();
    appendLiveLog(`[VOICE-INBOX] ${text}`);
    for (const line of text.split(/\r?\n/)) {
      const summary = voiceInboxLogSummary(line);
      if (/Voice phrase/i.test(summary)) {
        speakAccessibility(summary, "phrase", config, paths);
      }
    }
  });
  voiceInboxProcess.stderr.on("data", (data) => appendLiveLog(`[VOICE-INBOX error] ${data.toString().trimEnd()}`));
  voiceInboxProcess.on("close", (code) => {
    appendLiveLog(`[VOICE-INBOX] stopped code=${code}`);
    writeVoiceInboxStatus(config, paths, `stopped code=${code}`);
    voiceInboxProcess = undefined;
  });
  return true;
}

function startConversationAuditTail(config = getConfig(), paths = resolveRuntimePaths(config), options = {}) {
  if (!config.conversationAuditLiveAutoStart && !options.manual) {
    return false;
  }
  if (conversationAuditTailProcess) {
    appendLiveLog("[CONVERSATION-LIVE] already running.");
    return true;
  }
  const script = anaScriptPath(paths, "ana_conversation_audit_tail.py");
  if (!fs.existsSync(script)) {
    appendLiveLog(`[CONVERSATION-LIVE fail] Script not found: ${script}`);
    return false;
  }
  const pythonPath = workspacePythonPath(config, paths);
  appendLiveLog(`[CONVERSATION-LIVE] Starting real-time conversation audit tail: ${script}`);
  conversationAuditTailProcess = cp.spawn(pythonPath, [
    script,
    "--poll",
    "0.5"
  ], {
    cwd: workspaceRootPath() || anaRootPath(paths),
    env: { ...process.env, PYTHONUNBUFFERED: "1" },
    windowsHide: true
  });
  conversationAuditTailProcess.stdout.on("data", (data) => {
    for (const line of data.toString().replace(/\r/g, "").split(/\n/)) {
      if (line.trim()) {
        appendLiveLog(`[CONVERSATION-LIVE] ${line.trim()}`);
      }
    }
  });
  conversationAuditTailProcess.stderr.on("data", (data) => appendLiveLog(`[CONVERSATION-LIVE error] ${data.toString().trimEnd()}`));
  conversationAuditTailProcess.on("close", (code) => {
    appendLiveLog(`[CONVERSATION-LIVE] stopped code=${code}`);
    conversationAuditTailProcess = undefined;
  });
  return true;
}

function speakDirectVoice(text, config, paths) {
  if (!config.voiceReadoutDirect || !text) {
    return false;
  }
  if (/\b(api key|password|token|secret|private key)\b/i.test(text)) {
    return false;
  }
  try {
    const dir = voiceTempDir(config, paths);
    fs.mkdirSync(dir, { recursive: true });
    const tempPath = path.join(dir, `vscode_voice_${Date.now()}_${Math.random().toString(16).slice(2)}.txt`);
    fs.writeFileSync(tempPath, text, "utf8");
    const psScript = [
      "Add-Type -AssemblyName System.Speech",
      "$p = $args[0]",
      "$t = Get-Content -Raw -LiteralPath $p",
      "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer",
      "$s.Volume = 100",
      "$s.Rate = 0",
      "$s.Speak($t)",
      "$s.Dispose()",
      "Remove-Item -LiteralPath $p -Force -ErrorAction SilentlyContinue"
    ].join("; ");
    const child = cp.spawn("powershell.exe", [
      "-NoProfile",
      "-ExecutionPolicy",
      "Bypass",
      "-Command",
      psScript,
      tempPath
    ], {
      cwd: anaRootPath(paths),
      windowsHide: true,
      stdio: "ignore"
    });
    child.unref();
    return true;
  } catch {
    return false;
  }
}

function playAccessibilityBeep(kind, config) {
  if (!config.voiceAccessibilityCues || !config.voiceCueBeeps) {
    return false;
  }
  const cues = {
    button: [660, 80],
    start: [740, 80],
    success: [880, 100],
    fail: [330, 180],
    phrase: [980, 100],
    ready: [784, 90]
  };
  const [frequency, duration] = cues[kind] || cues.button;
  try {
    const child = cp.spawn("powershell.exe", [
      "-NoProfile",
      "-ExecutionPolicy",
      "Bypass",
      "-Command",
      `[Console]::Beep(${frequency}, ${duration})`
    ], {
      windowsHide: true,
      stdio: "ignore"
    });
    child.unref();
    return true;
  } catch {
    return false;
  }
}

function accessibilityPhrase(label, kind) {
  const cleaned = String(label || "").replace(/\s+/g, " ").trim();
  if (!cleaned) {
    return "";
  }
  if (kind === "button") return `Button ${cleaned}.`;
  if (kind === "start") return `Start ${cleaned}.`;
  if (kind === "success") return `Done ${cleaned}.`;
  if (kind === "fail") return `Failed ${cleaned}.`;
  if (kind === "ready") return `${cleaned} ready.`;
  return `${cleaned}.`;
}

function speakAccessibility(label, kind = "button", config = getConfig(), paths = resolveRuntimePaths(config)) {
  if (!config.voiceAccessibilityCues) {
    return false;
  }
  const phrase = sanitizeVoiceText(accessibilityPhrase(label, kind), config.voiceReadoutMaxChars);
  if (!phrase) {
    return false;
  }
  const now = Date.now();
  if (phrase === lastAccessibilityCue && now - lastAccessibilityCueAt < 700) {
    return false;
  }
  lastAccessibilityCue = phrase;
  lastAccessibilityCueAt = now;
  playAccessibilityBeep(kind, config);
  try {
    fs.appendFileSync(voiceQueuePath(config, paths), `${phrase}\n`, "utf8");
    return true;
  } catch {
    // Direct speech below is the fallback; queue writes are best effort.
  }
  speakDirectVoice(phrase, config, paths);
  return true;
}

function commandLabel(command) {
  const label = String(command || "")
    .replace(/^anaMax\./, "")
    .replace(/^ana\./, "")
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replace(/[-_.]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  return label || "ANA command";
}

function announceCommand(command) {
  const config = getConfig();
  if (!config.voiceButtonAnnouncements) {
    return;
  }
  speakAccessibility(commandLabel(command), "button", config, resolveRuntimePaths(config));
}

function actionLabel(type, errorLabel) {
  return String(errorLabel || type || "ANA action")
    .replace(/\s+failed\.?$/i, "")
    .replace(/^ANA MAX:\s*/i, "")
    .trim();
}

function goldenRuleGoalForCommand(label) {
  return `Activity Bar action "${label}" must consult ANA before Codex/operator proceeds.`;
}

function voiceInboxLogSummary(line) {
  const jsonStart = String(line || "").indexOf("{");
  if (jsonStart === -1) {
    return "";
  }
  try {
    const payload = JSON.parse(String(line).slice(jsonStart));
    if (payload.schema === "ana.voice_inbox.daemon.v1") {
      return `Voice inbox ${payload.status || "daemon"}.`;
    }
    if (payload.schema === "ana.voice_inbox.v1") {
      const record = payload.data?.record || {};
      if (record.submitted_to_focused_window) {
        return "Voice phrase submitted.";
      }
      if (record.copied_to_clipboard) {
        return "Voice phrase captured and copied.";
      }
      if (payload.success) {
        return "Voice phrase captured.";
      }
      return `Voice inbox ${payload.message || payload.error || "did not capture speech"}.`;
    }
  } catch {
    return "";
  }
  return "";
}

function mirrorOrientationSummary(line, config) {
  if (!config.voiceOrientationCues || !/\[MIRROR\]/i.test(line)) {
    return "";
  }
  const match = String(line || "").match(/\bapp=([^ ]*)\s+title=(.*?)\s+events=/i);
  if (!match) {
    return "";
  }
  const app = match[1] && match[1] !== "None" ? match[1] : "unknown";
  const rawTitle = match[2] && match[2] !== "None" ? match[2] : "";
  const title = rawTitle
    .replace(/screenshots\\view_[0-9]+\.png/gi, "")
    .replace(/\s+/g, " ")
    .trim();
  const key = `${app}|${title}`;
  const now = Date.now();
  const interval = Math.max(5000, Number(config.voiceOrientationMinIntervalMs) || 20000);
  if (key === lastOrientationCue && now - lastOrientationCueAt < interval) {
    return "";
  }
  lastOrientationCue = key;
  lastOrientationCueAt = now;
  const text = title ? `Screen ${app}. ${title}.` : `Screen ${app}.`;
  return sanitizeVoiceText(text, Math.min(Number(config.voiceReadoutMaxChars) || 260, 180));
}

function queueImportantVoice(message) {
  let config;
  try {
    config = getConfig();
  } catch {
    return;
  }
  if (!config.voiceReadout) {
    return;
  }
  const paths = resolveRuntimePaths(config);
  const voiceLines = [];
  for (const rawLine of String(message || "").split(/\r?\n/)) {
    const voiceText = voiceTextFromLogLine(rawLine, config);
    if (!voiceText || voiceText === lastVoiceLine) {
      continue;
    }
    if (!voiceLines.includes(voiceText)) {
      voiceLines.push(voiceText);
    }
  }
  if (!voiceLines.length) {
    return;
  }
  const now = Date.now();
  if (now - lastVoiceAt < config.voiceReadoutMinIntervalMs) {
    return;
  }
  const combined = sanitizeVoiceText(
    (config.voiceFullReadout ? voiceLines : voiceLines.slice(0, 4)).join(". "),
    config.voiceFullReadout
      ? Math.max(Number(config.voiceFullReadoutMaxChars) || 6000, Number(config.voiceReadoutMaxChars) || 260)
      : config.voiceReadoutMaxChars
  );
  if (!combined || combined === lastVoiceLine) {
    return;
  }
  try {
    startVoiceBridge(config, paths);
    fs.appendFileSync(voiceQueuePath(config, paths), `${combined}\n`, "utf8");
    lastVoiceLine = combined;
    lastVoiceAt = now;
  } catch (error) {
    speakDirectVoice(combined, config, paths);
    lastVoiceLine = combined;
    lastVoiceAt = now;
  }
}

function startMcpLogTail() {
  if (mcpTailProcess) {
    return;
  }
  const root = workspaceRootPath();
  if (!root) {
    appendLiveLog("[CONSOLE] No workspace root; MCP tail disabled.");
    return;
  }
  const tailScript = path.join(root, "ANA_MAX", "dev_artifacts", "scripts", "tail_mcp_log.ps1");
  if (!fs.existsSync(tailScript)) {
    appendLiveLog(`[CONSOLE] MCP tail script not found: ${tailScript}`);
    return;
  }
  appendLiveLog(`[CONSOLE] Tailing MCP activity via ${tailScript}`);
  mcpTailProcess = cp.spawn("powershell.exe", [
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    tailScript
  ], { cwd: root });
  mcpTailProcess.stdout.on("data", (data) => appendLiveLog(`[MCP] ${data.toString().trimEnd()}`));
  mcpTailProcess.stderr.on("data", (data) => appendLiveLog(`[MCP error] ${data.toString().trimEnd()}`));
  mcpTailProcess.on("close", (code) => {
    appendLiveLog(`[CONSOLE] MCP tail stopped code=${code}`);
    mcpTailProcess = undefined;
  });
}

function workspacePythonPath(config, paths) {
  const root = workspaceRootPath();
  const candidates = [
    config.pythonPath ? path.resolve(config.pythonPath) : "",
    root ? path.join(root, ".venv", "Scripts", "python.exe") : "",
    paths?.runtimeRoot ? path.join(paths.runtimeRoot, "venv", "Scripts", "python.exe") : "",
    "python"
  ].filter(Boolean);
  return candidates.find(candidate => candidate === "python" || fs.existsSync(candidate)) || "python";
}

function startLiveWatchdog() {
  if (liveWatchdogProcess) {
    return true;
  }
  const root = workspaceRootPath();
  if (!root) {
    appendLiveLog("[WATCHDOG] No workspace root; watchdog disabled.");
    return false;
  }
  const watchdogScript = path.join(root, "ANA_MAX_Launcher", "live_watchdog.py");
  if (!fs.existsSync(watchdogScript)) {
    appendLiveLog(`[WATCHDOG] Script not found: ${watchdogScript}`);
    return false;
  }
  const config = getConfig();
  const paths = resolveRuntimePaths(config);
  const pythonPath = workspacePythonPath(config, paths);
  appendLiveLog(`[WATCHDOG] Starting ${watchdogScript}`);
  liveWatchdogProcess = cp.spawn(pythonPath, [watchdogScript], {
    cwd: root,
    env: { ...process.env, PYTHONUNBUFFERED: "1" }
  });
  liveWatchdogProcess.stdout.on("data", (data) => appendLiveLog(`[WATCHDOG] ${data.toString().trimEnd()}`));
  liveWatchdogProcess.stderr.on("data", (data) => appendLiveLog(`[WATCHDOG error] ${data.toString().trimEnd()}`));
  liveWatchdogProcess.on("close", (code) => {
    appendLiveLog(`[WATCHDOG] stopped code=${code}`);
    liveWatchdogProcess = undefined;
  });
  return true;
}

function startMirrorWatch() {
  if (mirrorWatchProcess) {
    return true;
  }
  const root = workspaceRootPath();
  if (!root) {
    appendLiveLog("[MIRROR] No workspace root; mirror disabled.");
    return false;
  }
  const mirrorScript = path.join(root, "ANA_MAX", "dev_artifacts", "scripts", "ana_mirror_watch.py");
  if (!fs.existsSync(mirrorScript)) {
    appendLiveLog(`[MIRROR] Script not found: ${mirrorScript}`);
    return false;
  }
  const config = getConfig();
  const paths = resolveRuntimePaths(config);
  const pythonPath = workspacePythonPath(config, paths);
  appendLiveLog(`[MIRROR] Starting ${mirrorScript}`);
  mirrorWatchProcess = cp.spawn(pythonPath, [
    mirrorScript,
    "--interval",
    "2",
    "--screenshot-every",
    "10"
  ], {
    cwd: root,
    env: { ...process.env, PYTHONUNBUFFERED: "1" }
  });
  mirrorWatchProcess.stdout.on("data", (data) => appendLiveLog(`[MIRROR] ${data.toString().trimEnd()}`));
  mirrorWatchProcess.stderr.on("data", (data) => appendLiveLog(`[MIRROR error] ${data.toString().trimEnd()}`));
  mirrorWatchProcess.on("close", (code) => {
    appendLiveLog(`[MIRROR] stopped code=${code}`);
    mirrorWatchProcess = undefined;
  });
  return true;
}

function runPythonScript(config, paths, scriptPath, args, onData) {
  return new Promise((resolve, reject) => {
    const pythonPath = workspacePythonPath(config, paths);
    const child = cp.spawn(pythonPath, [scriptPath, ...args], {
      cwd: workspaceRootPath() || paths.runtimeRoot,
      env: { ...process.env, PYTHONUNBUFFERED: "1" }
    });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (data) => {
      const text = data.toString().replace(/\r/g, "");
      stdout += text;
      if (onData) onData(text, false);
    });
    child.stderr.on("data", (data) => {
      const text = data.toString().replace(/\r/g, "");
      stderr += text;
      if (onData) onData(text, true);
    });
    child.on("error", reject);
    child.on("close", (code) => {
      if (code === 0) {
        resolve({ stdout, stderr });
      } else {
        reject(new Error(stderr || stdout || `Process exited with code ${code}`));
      }
    });
  });
}

function firstOutputLine(text, prefix, fallback) {
  return String(text || "").split(/\r?\n/).find(line => line.startsWith(prefix)) || fallback;
}

function companionStatus(firstLine) {
  const match = String(firstLine || "").match(/ANA Codex Companion:\s+([A-Z]+)/);
  return match ? match[1] : "UNKNOWN";
}

function anaScriptPath(paths, scriptName) {
  return path.join(anaRootPath(paths), "dev_artifacts", "scripts", scriptName);
}

async function runCodexCompanionPreflight(config, paths, goal, options = {}) {
  const script = anaScriptPath(paths, "ana_codex_companion.py");
  if (!fs.existsSync(script)) {
    throw new Error(`ANA Codex Companion script not found: ${script}`);
  }

  const args = [
    "--mcp-url",
    config.runtimeUrl,
    "--goal",
    goal || "Codex asks ANA to observe, challenge blind work, and choose the next verified lab action.",
    "--no-write"
  ];
  if (options.strict) {
    args.push("--strict");
  }

  appendLiveLog(`[GOLDEN-RULE] ANA preflight start: ${goal}`);
  const result = await runPythonScript(config, paths, script, args, (text, isError) => {
    appendLiveLog(`${isError ? "[GOLDEN-RULE error]" : "[GOLDEN-RULE]"} ${text.trimEnd()}`);
  });
  const firstLine = firstOutputLine(result.stdout, "ANA Codex Companion:", "ANA Codex Companion: completed");
  const status = companionStatus(firstLine);
  appendLiveLog(`[GOLDEN-RULE] ANA preflight ${status}: ${firstLine}`);
  if (status === "FAIL") {
    throw new Error(firstLine);
  }
  return { firstLine, status, stdout: result.stdout, stderr: result.stderr };
}

async function runCodexGuard(reason, config = getConfig(), paths = resolveRuntimePaths(config), options = {}) {
  if (!options.manual && !config.codexGuardAutoStart) {
    appendLiveLog("[ANA-GUARD skip] anaMax.codexGuardAutoStart=false");
    return undefined;
  }
  const now = Date.now();
  const minInterval = Math.max(5000, Number(config.codexGuardMinIntervalMs) || 60000);
  if (!options.manual && now - lastCodexGuardAt < minInterval) {
    appendLiveLog("[ANA-GUARD skip] recent guard already ran.");
    return undefined;
  }
  if (codexGuardInFlight) {
    appendLiveLog("[ANA-GUARD skip] guard already running.");
    return undefined;
  }
  codexGuardInFlight = true;
  lastCodexGuardAt = now;
  const goal = reason || "Codex must consult ANA before meaningful lab action.";
  appendLiveLog(`[ANA-GUARD] Start: ${goal}`);
  speakAccessibility("ANA guard checking Codex", "start", config, paths);
  try {
    const preflight = await runCodexCompanionPreflight(config, paths, goal, {
      strict: !!config.codexGuardStrict
    });
    appendLiveLog(`[ANA-GUARD] ${preflight.status}: ${preflight.firstLine}`);
    if (preflight.status === "WARN") {
      speakAccessibility("ANA guard warning. Check Live Console", "ready", config, paths);
    } else {
      speakAccessibility("ANA guard ready", "ready", config, paths);
    }
    return preflight;
  } catch (error) {
    const message = error.message || String(error);
    appendLiveLog(`[ANA-GUARD fail] ${message}`);
    speakAccessibility("ANA guard failed", "fail", config, paths);
    if (options.throwOnFail) {
      throw error;
    }
    return { status: "FAIL", firstLine: message };
  } finally {
    codexGuardInFlight = false;
  }
}

async function runLocalCheckpoint(config, paths, options) {
  const root = workspaceRootPath();
  const script = path.join(root || paths.runtimeRoot, "ANA_MAX", "dev_artifacts", "scripts", "ana_local_checkpoint.py");
  if (!fs.existsSync(script)) {
    throw new Error(`ANA local checkpoint script not found: ${script}`);
  }
  const args = [
    "--title",
    options.title,
    "--summary",
    options.summary,
    "--current-goal",
    options.currentGoal || "",
    "--next-steps",
    options.nextSteps || "",
    "--files-changed",
    options.filesChanged || "",
    "--validation",
    options.validation || "",
    "--risks",
    options.risks || "",
    "--sync-status",
    options.syncStatus || "",
    "--json"
  ];
  appendLiveLog(`[LOCAL-CHECKPOINT] start: ${script}`);
  const result = await runPythonScript(config, paths, script, args, (text, isError) => {
    appendLiveLog(`${isError ? "[LOCAL-CHECKPOINT error]" : "[LOCAL-CHECKPOINT]"} ${text.trimEnd()}`);
  });
  const payload = JSON.parse(result.stdout);
  if (!payload.success) {
    throw new Error(payload.error || "Local checkpoint failed");
  }
  return payload.data || payload;
}

function startLiveConsoleHeartbeat() {
  if (liveConsoleTimer) {
    return;
  }
  const tick = async () => {
    try {
      const config = getConfig();
      const health = await getHealth(config);
      const line = `[HEARTBEAT] status=${health.status} ready=${health.mcp_ready} tools=${health.tools_count || "?"}`;
      if (line !== lastHeartbeatLine) {
        appendLiveLog(line);
        lastHeartbeatLine = line;
      }
    } catch (e) {
      const line = `[HEARTBEAT fail] ${e.message}`;
      if (line !== lastHeartbeatLine) {
        appendLiveLog(line);
        lastHeartbeatLine = line;
      }
    }
  };
  tick();
  liveConsoleTimer = setInterval(tick, 5000);
}

function openLiveConsole() {
  const config = getConfig();
  const paths = resolveRuntimePaths(config);
  showLiveConsole();
  speakAccessibility("Live Console", "button", config, paths);
  appendLiveLog("[CONSOLE] ANA MAX live console opened. Text log is now the primary control surface.");
  startLiveConsoleHeartbeat();
  startMirrorWatch();
  if (!startLiveWatchdog()) {
    startMcpLogTail();
  }
}

function safeModeMessage(action) {
  const config = getConfig();
  return `ANA MAX ${action}: safe-mode ${config.safeMode ? "active" : "disabled"}.`;
}

function getDangerousActionPrompts(toolName, args) {
  const text = `${toolName || ""} ${JSON.stringify(args || {})}`.toLowerCase();
  const normalizedTool = String(toolName || "").toLowerCase();
  const readOnlyTools = new Set([
    "ana_identity",
    "agent_coach",
    "ana_health_check",
    "ana_runtime_inspector",
    "baseline_update_suggester",
    "codebase_understanding",
    "docs_generator",
    "error_radar",
    "foreground_ui_snapshot",
    "project_navigator",
    "runtime_guard",
    "schema_diff",
    "session_lifecycle",
    "session_rem_sleep",
    "tool_contract_validator",
    "tool_healthcheck",
    "tool_router",
    "workspace_situational_awareness"
  ]);
  const prompts = [];

  if (readOnlyTools.has(normalizedTool)) {
    return prompts;
  }
  if (
    normalizedTool === "session_checkpoint" ||
    (
      normalizedTool === "session_lifecycle" &&
      ["wake", "rest"].includes(String((args || {}).action || "").toLowerCase())
    )
  ) {
    return prompts;
  }

  if (/(write|patch|edit|delete|remove|move|rename|save|commit|push|install|uninstall)/.test(text)) {
    prompts.push("Allow write?");
  }
  if (/(terminal|shell|powershell|cmd|subprocess|process|launch|start_runtime|exec)/.test(text)) {
    prompts.push("Allow subprocess?");
  }
  if (/(http|https|fetch|download|upload|network|browser|web|api|curl)/.test(text)) {
    prompts.push("Allow network call?");
  }

  return [...new Set(prompts)];
}

async function confirmDangerousAction(toolName, args) {
  const config = getConfig();
  if (!config.safeMode) {
    return true;
  }

  const prompts = getDangerousActionPrompts(toolName, args);
  for (const prompt of prompts) {
    const answer = await vscode.window.showWarningMessage(
      `${prompt} safe-mode blocks tool execution unless you approve this action.`,
      { modal: true },
      "Allow once"
    );
    if (answer !== "Allow once") {
      return false;
    }
  }
  return true;
}

function getMcpConfigText(config) {
  return [
    "ANA MAX MCP Config",
    "",
    `Runtime URL: ${config.runtimeUrl}`,
    `Codex server name: ${config.codexServerName}`,
    "",
    "Codex config TOML:",
    `[mcp_servers.${config.codexServerName}]`,
    `url = "${config.runtimeUrl}"`
  ].join("\n");
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function writeLocalDashboard(config, health, tools, healthcheck) {
  const outDir = path.join(os.tmpdir(), "ana-max-dashboard");
  fs.mkdirSync(outDir, { recursive: true });
  const outFile = path.join(outDir, "dashboard.html");
  const toolNames = tools.map(tool => String(tool.name || "")).filter(Boolean).sort();
  const healthcheckData = healthcheck?.data || healthcheck || {};
  const failed = Number(healthcheckData.failed || 0);
  const ok = Number(healthcheckData.ok || 0);
  const status = health?.mcp_ready && failed === 0 ? "READY" : "CHECK";
  const generated = new Date().toISOString();
  const htmlText = `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ANA MAX Lab Dashboard</title>
  <style>
    body { margin: 0; font-family: Segoe UI, Arial, sans-serif; background: #101820; color: #e8eef2; }
    main { max-width: 1180px; margin: 0 auto; padding: 28px; }
    h1 { margin: 0 0 8px; font-size: 28px; }
    .muted { color: #9eb0bf; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin: 18px 0; }
    .card { background: #172430; border: 1px solid #294154; border-radius: 8px; padding: 14px; }
    .metric { font-size: 30px; font-weight: 700; margin-top: 8px; }
    .ready { color: #78df9a; }
    .check { color: #ffd166; }
    pre { white-space: pre-wrap; word-break: break-word; overflow: auto; background: #0b1118; border: 1px solid #24384a; border-radius: 8px; padding: 12px; }
    ul { columns: 3 260px; padding-left: 20px; }
    li { break-inside: avoid; margin: 3px 0; }
  </style>
</head>
<body>
  <main>
    <h1>ANA MAX Lab Dashboard</h1>
    <p class="muted">Generated from the live local MCP runtime. No dashboard server is required.</p>
    <p class="muted">Runtime: ${escapeHtml(config.runtimeUrl)} | Generated: ${escapeHtml(generated)}</p>
    <div class="grid">
      <section class="card"><div>Status</div><div class="metric ${status === "READY" ? "ready" : "check"}">${status}</div></section>
      <section class="card"><div>MCP ready</div><div class="metric">${escapeHtml(health?.mcp_ready)}</div></section>
      <section class="card"><div>Tools</div><div class="metric">${toolNames.length}</div></section>
      <section class="card"><div>Healthcheck</div><div class="metric">${ok} OK / ${failed} FAIL</div></section>
    </div>
    <h2>Health</h2>
    <pre>${escapeHtml(JSON.stringify(health, null, 2))}</pre>
    <h2>Tool Healthcheck</h2>
    <pre>${escapeHtml(JSON.stringify(healthcheckData, null, 2))}</pre>
    <h2>Tools</h2>
    <ul>${toolNames.map(name => `<li>${escapeHtml(name)}</li>`).join("")}</ul>
  </main>
</body>
</html>`;
  fs.writeFileSync(outFile, htmlText, "utf8");
  return outFile;
}

async function openLocalFile(config, filePath) {
  const browserPath = String(config.preferredBrowserPath || "").trim();
  if (browserPath && fs.existsSync(browserPath)) {
    const child = cp.spawn(browserPath, [filePath], {
      detached: true,
      stdio: "ignore"
    });
    child.unref();
    return { method: "preferred_browser", executable: browserPath };
  }
  await vscode.env.openExternal(vscode.Uri.file(filePath));
  return { method: "vscode_open_external" };
}

function requestJson(url, payload) {
  return new Promise((resolve, reject) => {
    try {
      const parsed = new URL(url);
      const body = JSON.stringify(payload || {});
      const req = http.request({
        hostname: parsed.hostname,
        port: parsed.port,
        path: parsed.pathname,
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Content-Length": Buffer.byteLength(body)
        },
        timeout: 10000
      }, (res) => {
        let data = "";
        res.on("data", (chunk) => { data += chunk; });
        res.on("end", () => {
          try {
            resolve(data ? JSON.parse(data) : {});
          } catch (error) {
            reject(new Error(`Failed to parse response: ${error.message}`));
          }
        });
      });
      req.on("timeout", () => {
        req.destroy(new Error("ANA MAX runtime request timed out"));
      });
      req.on("error", reject);
      req.write(body);
      req.end();
    } catch (e) {
      reject(e);
    }
  });
}

async function callTool(config, name, args) {
  if (!(await confirmDangerousAction(name, args))) {
    appendLiveLog(`[TOOL blocked] ${name} safe-mode`);
    return { success: false, error: "safe-mode blocks tool execution" };
  }
  appendLiveLog(`[TOOL start] ${name} ${JSON.stringify(args || {})}`);
  const res = await requestJson(config.runtimeUrl, {
    jsonrpc: "2.0",
    id: Date.now(),
    method: "tools/call",
    params: { name, arguments: args || {} }
  });
  const text = res.result?.content?.[0]?.text;
  if (!text) {
    return { success: false, error: "Missing MCP tool content", raw: res };
  }
  try {
    const parsed = JSON.parse(text);
    appendLiveLog(`[TOOL end] ${name} success=${parsed.success === true} message=${parsed.message || parsed.error || ""}`);
    return parsed;
  } catch (error) {
    appendLiveLog(`[TOOL end] ${name} non-json ${error.message}`);
    return { success: false, error: `Non-JSON MCP tool content: ${error.message}`, raw: text };
  }
}

async function getSmartReadiness(config) {
  const health = await getHealth(config);
  const toolsRes = await requestJson(config.runtimeUrl, {
    jsonrpc: "2.0",
    id: Date.now(),
    method: "tools/list",
    params: {}
  });
  const tools = toolsRes.result?.tools || [];
  const names = tools.map(t => t.name);
  const agentCoach = tools.find(t => t.name === "agent_coach") || {};
  const actions = agentCoach.inputSchema?.properties?.action?.enum || [];
  const router = await callTool(config, "tool_router", {
    task: "MCP tool failed with schema mismatch action versus operation",
    error: "Invalid value for operation",
    max_tools: 4
  });
  const recommend = await callTool(config, "agent_coach", {
    action: "recommend",
    task: "MCP tool failed with schema mismatch action versus operation",
    error: "Invalid value for operation",
    max_tools: 5,
    include_prompt: false
  });
  const checks = [
    { name: "health_online", ok: health.status === "online" && !!health.mcp_ready },
    { name: "tool_router_present", ok: names.includes("tool_router") },
    { name: "agent_coach_present", ok: names.includes("agent_coach") },
    { name: "agent_coach_recommend_schema", ok: actions.includes("recommend") },
    { name: "tool_router_call", ok: !!router.success && !!router.data?.recommended_tools?.length },
    {
      name: "agent_coach_recommend_call",
      ok: !!recommend.success
        && recommend.data?.schema === "ana.agent_coach.recommend.v1"
        && !!recommend.data?.primary_tool
    }
  ];
  return {
    ok: checks.every(c => c.ok),
    health,
    tool_count: tools.length,
    actions,
    checks,
    router: router.data || router,
    recommend: recommend.data || recommend
  };
}

function formatSmartReadiness(report) {
  const status = report.ok ? "SMART READY" : "NOT READY";
  const primary = report.recommend?.primary_tool || "none";
  const stack = (report.recommend?.tool_stack || []).join(", ") || "none";
  const checks = report.checks.map(c => `${c.ok ? "[OK]" : "[FAIL]"} ${c.name}`).join("\n");
  return [
    status,
    `health=${report.health?.status} mcp_ready=${report.health?.mcp_ready} tools=${report.tool_count}`,
    `primary_tool=${primary}`,
    `tool_stack=${stack}`,
    "",
    checks
  ].join("\n");
}

class AnaActionProvider {
  getTreeItem(element) {
    return element;
  }

  getChildren() {
    return [
      actionItem("0 Live Console", "anaMax.openLiveConsole", "terminal", "Open the text-only ANA MAX live log."),
      actionItem("1 Start MCP Server", "anaMax.startRuntime", "play", "Start the local ANA MAX MCP server."),
      actionItem("2 Smart Ready", "anaMax.showHealth", "pulse", "Verify health, router, coach, and tool list."),
      actionItem("Codex Guard", "anaMax.codexGuard", "shield", "Run ANA guard now and speak whether Codex may proceed."),
      actionItem("Codex Companion", "anaMax.codexCompanion", "comment-discussion", "Let ANA observe, challenge Codex, and choose the next verified action."),
      actionItem("Voice Inbox", "anaMax.voiceInbox", "record", "Capture one microphone dictation, copy it to clipboard, and save it for Codex."),
      actionItem("Conversation Audit", "anaMax.conversationAudit", "megaphone", "Show whether ANA captured recent voice, clipboard, and spoken queue evidence."),
      actionItem("Live Conversation Audit", "anaMax.liveConversationAudit", "eye", "Stream conversation audit events in the Live Console as they happen."),
      actionItem("Voice Operator Smoke", "anaMax.voiceOperatorSmoke", "unmute", "Send one voice-operator test phrase and verify conversation audit evidence."),
      actionItem("3 Wake", "anaMax.wakeSession", "debug-restart", "Load the last REM context or first-run manifest."),
      actionItem("Health JSON", "anaMax.showHealthJson", "json", "Show raw ANA MAX health JSON."),
      actionItem("List Tools", "anaMax.listTools", "list-unordered", "List MCP tools exposed by ANA MAX."),
      actionItem("Live Debug", "anaMax.liveDebug", "debug-alt", "Refresh live MCP health and tool count."),
      actionItem("Nucleus Smoke", "anaMax.nucleusSmoke", "beaker", "Run health, router, coach, context, graph, verification, and trust checks."),
      actionItem("Autonomy Pass", "anaMax.autonomyPass", "run-all", "Observe, route, context-pack, verify, audit, and checkpoint safely."),
      actionItem("Lab Quality Gate", "anaMax.labQualityGate", "checklist", "Run compile, focused tests, governance, policy coverage, health, and nucleus smoke."),
      actionItem("No-Reload Gate", "anaMax.noReloadGate", "shield", "Validate and package without installing or reloading the IDE."),
      actionItem("Operator Status", "anaMax.operatorStatus", "info", "Show VSIX version, MCP readiness, reload marker, checkpoint, and next commands."),
      actionItem("Review Batch Plan", "anaMax.reviewBatchPlan", "play-circle", "Preview the first focused Dirty Tree review-batch command without running it."),
      actionItem("Live Behavior", "anaMax.liveBehavior", "debug-coverage", "Check whether live MCP exposes current tool behavior."),
      actionItem("Reload Readiness", "anaMax.reloadReadiness", "sync", "Check whether VS Code reload or MCP restart is useful now."),
      actionItem("Reload Consistency", "anaMax.reloadConsistency", "check-all", "Check whether reload diagnostics agree before action work."),
      actionItem("Post-Reload Verify", "anaMax.postReloadVerify", "pass", "After MCP reload, verify marker, Nucleus Smoke, and compact lab state."),
      actionItem("Recommend", "anaMax.showRouterDecisions", "list-tree", "Ask ANA which tool should be used next."),
      actionItem("Profile Status", "anaMax.profileStatus", "symbol-namespace", "Show active permission profiles and tool policy coverage."),
      actionItem("Checkpoint", "anaMax.checkpoint", "save", "Save a compact handoff checkpoint."),
      actionItem("Rest Preview", "anaMax.previewRest", "preview", "Analyze session lessons without writing memory."),
      actionItem("Save REM", "anaMax.runRemSleep", "repo-push", "Save the session handoff after review."),
      actionItem("Refresh Context Maps", "anaMax.refreshCodeMap", "symbol-structure", "Refresh Code Map and Graph Map for fresh project context."),
      actionItem("Trust Score", "anaMax.showTrustScore", "verified", "Show current session trust score."),
      actionItem("Session Audit", "anaMax.generateSessionAudit", "shield", "Generate public-safe session audit JSON."),
      actionItem("Binary Map", "anaMax.binaryMap", "file-binary", "Analyze an executable/library statically."),
      actionItem("Identity", "anaMax.identity", "account", "Call ANA identity."),
      actionItem("MCP Config", "ana.showCodexMcpConfig", "json", "Show Codex MCP config."),
      actionItem("Call MCP Tool", "anaMax.executeTool", "tools", "Call any MCP tool with JSON arguments."),
      actionItem("Inspect Runtime", "anaMax.inspectRuntime", "search", "Inspect ANA runtime state."),
      actionItem("Open Dashboard", "anaMax.openDashboard", "dashboard", "Open the ANA dashboard URL.")
    ];
  }
}

function actionItem(label, command, icon, tooltip) {
  const item = new vscode.TreeItem(label, vscode.TreeItemCollapsibleState.None);
  item.command = { command, title: label };
  item.iconPath = new vscode.ThemeIcon(icon);
  item.tooltip = tooltip;
  return item;
}

function activate(context) {
  logChannel = vscode.window.createOutputChannel("ANA MAX MCP");
  context.subscriptions.push(logChannel);

  context.subscriptions.push(
    vscode.window.registerTreeDataProvider("anaMax.actions", new AnaActionProvider())
  );

  if (typeof vscode.commands.onDidExecuteCommand === "function") {
    context.subscriptions.push(vscode.commands.onDidExecuteCommand((event) => {
      const command = String(event?.command || "");
      if (command.startsWith("anaMax.") || command.startsWith("ana.")) {
        announceCommand(command);
      }
    }));
  }

  async function startRuntime() {
    const config = getConfig();
    const paths = resolveRuntimePaths(config);
    showLiveConsole();
    speakAccessibility("Start MCP Server", "start", config, paths);
    appendLiveLog("[START] Start MCP Server requested.");
    if (runtimeProcess) {
      vscode.window.showWarningMessage("ANA MAX MCP is already running.");
      appendLiveLog("[START] Runtime process already tracked by extension.");
      speakAccessibility("ANA MCP already running", "ready", config, paths);
      return;
    }
    try {
      const readiness = await getSmartReadiness(config);
      if (readiness.ok) {
        const msg = `[SYSTEM] ANA MAX already smart ready at ${runtimeBaseUrl(config)} with ${readiness.tool_count || "?"} tools.\n`;
        logChannel.append(msg);
        addToBuffer(msg);
        if (panel) post(panel, "runtimeLog", msg);
        appendLiveLog(`[START] Existing MCP is smart ready; tools=${readiness.tool_count || "?"}.`);
        speakAccessibility(`ANA MCP active with ${readiness.tool_count || "unknown"} tools`, "ready", config, paths);
        runCodexGuard("Post-start guard: Codex must use ANA before meaningful action.", config, paths).catch((error) => {
          appendLiveLog(`[ANA-GUARD fail] ${error.message || error}`);
        });
        vscode.window.showInformationMessage(`ANA MAX is already active.`);
        return;
      }
    } catch {
      // Offline is expected here; continue with launch and stream process logs.
    }
    if (!fs.existsSync(paths.mainPy)) {
      vscode.window.showErrorMessage(`ANA MAX main.py not found in ${paths.runtimeRoot}.${remoteRuntimeHint(paths)}`);
      speakAccessibility("ANA main file missing", "fail", config, paths);
      return;
    }

    logChannel.appendLine(`[Extension] Launching ${paths.mainPy}...${remoteRuntimeHint(paths)}`);
    appendLiveLog(`[START] Launching ${paths.mainPy} with ${paths.pythonPath} on port ${config.runtimePort}.`);
    const args = [paths.mainPy, "--host", "127.0.0.1", "--port", `${config.runtimePort}`];

    try {
      runtimeProcess = cp.spawn(paths.pythonPath, args, {
        cwd: paths.runtimeRoot,
        env: { ...process.env, PYTHONUNBUFFERED: "1" }
      });

      const handleData = (data, prefix = "") => {
        const line = data.toString().replace(/\r/g, "");
        const formatted = prefix ? `${prefix}: ${line}` : line;
        logChannel.append(formatted);
        addToBuffer(formatted);
        if (panel) post(panel, "runtimeLog", formatted);
      };

      runtimeProcess.stdout.on("data", (data) => handleData(data));
      runtimeProcess.stderr.on("data", (data) => handleData(data, "!!"));

      runtimeProcess.on("close", (code) => {
        const msg = `[SYSTEM] Runtime stopped (Code ${code})`;
        logChannel.appendLine(msg);
        addToBuffer(msg + "\n");
        runtimeProcess = undefined;
        if (panel) post(panel, "runtimeLog", "\n" + msg);
        if (panel) post(panel, "runtimeState", { active: false });
      });

      if (panel) post(panel, "runtimeState", { active: true });
      appendLiveLog("[START] Runtime process spawned; waiting for MCP discovery.");
      try {
        const health = await waitForRuntimeHealth(config);
        const msg = `[SYSTEM] ANA MAX MCP ready: status=${health.status} tools=${health.tools_count || "?"}`;
        logChannel.appendLine(msg);
        addToBuffer(msg + "\n");
        appendLiveLog(`[START] Health ready; tools=${health.tools_count || "?"}.`);
        speakAccessibility(`ANA MCP ready with ${health.tools_count || "unknown"} tools`, "ready", config, paths);
        runCodexGuard("Post-start guard: Codex must use ANA before meaningful action.", config, paths).catch((error) => {
          appendLiveLog(`[ANA-GUARD fail] ${error.message || error}`);
        });
        if (panel) post(panel, "runtimeState", { active: true });
        if (panel) post(panel, "health", health);
        vscode.window.showInformationMessage(`ANA MAX MCP ready (${health.tools_count || "?"} tools).`);
      } catch (healthError) {
        const msg = `[START fail] Runtime spawned but health did not become ready: ${healthError.message}`;
        appendLiveLog(msg);
        speakAccessibility("ANA MCP health failed", "fail", config, paths);
        vscode.window.showWarningMessage("ANA MAX runtime was started, but /health is not ready yet. Check ANA MAX MCP output.");
      }
    } catch (err) {
      vscode.window.showErrorMessage(`Failed to launch: ${err.message}`);
      appendLiveLog(`[START fail] ${err.message}`);
      speakAccessibility("Start MCP Server failed", "fail", config, paths);
      runtimeProcess = undefined;
    }
  }

  function openOrRevealCockpit() {
    if (panel) {
      panel.reveal(vscode.ViewColumn.Beside);
      return panel;
    }

    panel = vscode.window.createWebviewPanel(
      "anaCodexCockpit",
      "ANA MAX Codex MCP Cockpit",
      vscode.ViewColumn.Beside,
      { enableScripts: true, retainContextWhenHidden: true }
    );

    panel.webview.html = getWebviewContent(panel.webview);
    setTimeout(() => {
      appendLiveLog("[COCKPIT] Webview opened.");
    }, 100);

    // Send history on load
    if (logBuffer.length > 0) {
      setTimeout(() => {
        post(panel, "runtimeLog", logBuffer.join(""));
      }, 500);
    }

    panel.onDidDispose(() => {
      panel = undefined;
    });

    panel.webview.onDidReceiveMessage(async (message) => {
      const config = getConfig();
      const baseUrl = runtimeBaseUrl(config);

      if (message.command === "webviewReady") {
        appendLiveLog(`[UI] Webview ready script=${message.script || "unknown"} buttons=${message.buttons ?? "unknown"}`);
        return;
      }

      if (message.command === "webviewError") {
        appendLiveLog(`[UI ERROR] ${message.message || "Unknown webview error"}`);
        if (message.stack) {
          appendLiveLog(`[UI ERROR stack] ${String(message.stack).slice(0, 1200)}`);
        }
        post(panel, "error", `Cockpit UI error: ${message.message || "Unknown webview error"}`);
        return;
      }

      if (message.command === "health") {
        appendLiveLog("[UI] Health JSON requested.");
        try {
          const data = await requestGetJson(`${baseUrl}/health`);
          appendLiveLog(`[HEALTH] status=${data.status} mcp_ready=${data.mcp_ready} tools=${data.tools_count}`);
          post(panel, "health", data);
        } catch (e) {
          appendLiveLog(`[HEALTH fail] ${e.message}`);
          post(panel, "error", `Backend offline @ ${baseUrl}. Start ANA MAX via main.py.`);
        }
        return;
      }

      if (message.command === "startRuntime") {
        await vscode.commands.executeCommand("anaMax.startRuntime");
        return;
      }

      if (message.command === "smartReady") {
        appendLiveLog("[UI] Smart Ready requested.");
        try {
          const report = await getSmartReadiness(config);
          appendLiveLog(`[SMART] ok=${report.ok} health=${report.health?.status} tools=${report.tool_count} primary=${report.recommend?.primary_tool || "none"}`);
          post(panel, "smartReady", report);
        } catch (e) {
          appendLiveLog(`[SMART fail] ${e.message}`);
          post(panel, "error", `Smart readiness failed @ ${baseUrl}: ${e.message}`);
        }
        return;
      }

      if (message.command === "refreshCodeMap") {
        await vscode.commands.executeCommand("anaMax.refreshCodeMap");
        return;
      }

      if (message.command === "trustScore") {
        await vscode.commands.executeCommand("anaMax.showTrustScore");
        return;
      }

      if (message.command === "sessionAudit") {
        await vscode.commands.executeCommand("anaMax.generateSessionAudit");
        return;
      }

      if (message.command === "binaryMap") {
        await vscode.commands.executeCommand("anaMax.binaryMap");
        return;
      }

      if (message.command === "recommend") {
        appendLiveLog("[UI] Recommend requested.");
        try {
          const payload = await callTool(config, "agent_coach", {
            action: "recommend",
            task: message.task || "Cockpit operator asks for the next best ANA MAX tool",
            max_tools: 5,
            include_prompt: false
          });
          post(panel, "recommend", payload.data || payload);
        } catch (e) {
          post(panel, "error", e.message);
        }
        return;
      }

      if (message.command === "wakeSession") {
        try {
          const payload = await callTool(config, "session_lifecycle", {
            action: "wake"
          });
          post(panel, "lifecycle", payload.data || payload);
        } catch (e) {
          post(panel, "error", e.message);
        }
        return;
      }

      if (message.command === "checkpoint") {
        try {
          const paths = resolveRuntimePaths(config);
          const payload = await runLocalCheckpoint(config, paths, {
            title: "Cockpit quick checkpoint",
            summary: message.summary || "Operator saved a quick checkpoint from the cockpit.",
            currentGoal: "Continue ANA MAX MCP/tool orchestration without losing chat context.",
            nextSteps: "Read docs/NEXT_SESSION_BOOTSTRAP.md; verify MCP smart readiness; continue from ANA_MAX/docs/CURRENT_SESSION_HANDOFF.md",
            filesChanged: "vscode_extension/extension.js; docs/AGENT_MEMORY.md; docs/NEXT_SESSION_BOOTSTRAP.md",
            validation: "MCP smart readiness should report OK before continuing.",
            risks: "Reloading the IDE can close the current chat; defer reload until operator is ready.",
            syncStatus: "Mother lab only; public release sync pending review."
          });
          post(panel, "checkpoint", payload);
        } catch (e) {
          post(panel, "error", e.message);
        }
        return;
      }

      if (message.command === "remSleep") {
        try {
          const payload = await callTool(config, "session_lifecycle", {
            action: "rest",
            consolidate: true,
            save_memory: true
          });
          post(panel, "remSleep", payload.data || payload);
        } catch (e) {
          post(panel, "error", e.message);
        }
        return;
      }

      if (message.command === "previewRest") {
        try {
          const payload = await callTool(config, "session_lifecycle", {
            action: "rest",
            consolidate: false
          });
          post(panel, "lifecycle", payload.data || payload);
        } catch (e) {
          post(panel, "error", e.message);
        }
        return;
      }

      if (message.command === "listTools") {
        appendLiveLog("[UI] List Tools requested.");
        try {
          const res = await requestJson(config.runtimeUrl, {
            jsonrpc: "2.0",
            id: Date.now(),
            method: "tools/list",
            params: {}
          });
          const tools = res.result?.tools || [];
          const names = tools.map(t => t.name).sort().join("\n");
          appendLiveLog(`[TOOLS] listed ${tools.length} tools.`);
          post(panel, "response", names ? `Tools loaded (${tools.length}):\n\n${names}` : "No tools found.");
        } catch (e) {
          appendLiveLog(`[TOOLS fail] ${e.message}`);
          post(panel, "error", e.message);
        }
        return;
      }

      if (message.command === "liveDebug") {
        try {
          const health = await getHealth(config);
          const toolsRes = await requestJson(config.runtimeUrl, {
            jsonrpc: "2.0",
            id: Date.now(),
            method: "tools/list",
            params: {}
          });
          const tools = toolsRes.result?.tools || [];
          appendLiveLog(`[LIVE] status=${health.status} ready=${health.mcp_ready} tools=${tools.length}`);
          post(panel, "liveDebug", {
            runtimeUrl: config.runtimeUrl,
            baseUrl,
            health,
            tool_count: tools.length,
            sample_tools: tools.slice(0, 8).map(t => t.name),
            checked_at: new Date().toISOString()
          });
        } catch (e) {
          appendLiveLog(`[LIVE fail] ${e.message}`);
          post(panel, "liveDebug", {
            runtimeUrl: config.runtimeUrl,
            baseUrl,
            error: e.message,
            checked_at: new Date().toISOString()
          });
        }
        return;
      }

      if (message.command === "codexMcpConfig") {
        post(panel, "response", getMcpConfigText(config));
        return;
      }

      if (message.command === "execute") {
        appendLiveLog(`[UI] Execute requested: ${message.tool || "unknown"}`);
        try {
          if (!(await confirmDangerousAction(message.tool, message.args || {}))) {
            post(panel, "error", "safe-mode blocks tool execution");
            return;
          }
          const res = await requestJson(config.runtimeUrl, {
            jsonrpc: "2.0",
            id: Date.now(),
            method: "tools/call",
            params: { name: message.tool, arguments: message.args || {} }
          });
          const payloadText = res.result?.content?.[0]?.text;
          let payload = undefined;
          if (payloadText) {
            try {
              payload = JSON.parse(payloadText);
            } catch {
              payload = undefined;
            }
          }
          if (payload?.guidance_summary) {
            post(panel, "toolGuidance", {
              tool: message.tool,
              payload,
              guidance_summary: payload.guidance_summary
            });
          } else {
            post(panel, "response", JSON.stringify(res.result || res.error, null, 2));
          }
        } catch (e) {
          post(panel, "error", e.message);
        }
        return;
      }

      if (message.command === "sendMessage") {
        const text = message.text || "";
        if (text.startsWith("/tool ")) {
          const body = text.slice(6).trim();
          const space = body.indexOf(" ");
          const name = space === -1 ? body : body.slice(0, space);
          const argsStr = space === -1 ? "{}" : body.slice(space + 1);
          try {
            const args = JSON.parse(argsStr);
            panel.webview.postMessage({ command: "execute", tool: name, args });
          } catch (e) {
            post(panel, "error", "Invalid JSON arguments.");
          }
          return;
        }
        post(panel, "response", `Message received: ${text}\n\nANA MAX is bridged to your local MCP runtime. Available tools can be tested from the cockpit.`);
      }
    });

    return panel;
  }

  async function runInCockpit(type, operation, errorLabel) {
    const config = getConfig();
    const paths = resolveRuntimePaths(config);
    const label = actionLabel(type, errorLabel);
    try {
      showLiveConsole();
      speakAccessibility(label, "start", config, paths);
      appendLiveLog(`[ACTION start] ${type}`);
      const result = await operation();
      appendLiveLog(`[ACTION end] ${type} ${JSON.stringify(result.data || result)}`);
      if (config.voiceActionCompletion) {
        speakAccessibility(label, "success", config, paths);
      }
      post(panel, type, result.data || result);
    } catch (e) {
      appendLiveLog(`[ACTION fail] ${type} ${errorLabel}: ${e.message}`);
      speakAccessibility(label, "fail", config, paths);
      post(panel, "error", `${errorLabel}: ${e.message}`);
    }
  }

  async function ensureGoldenRulePreflight(label, goal, config, paths, options = {}) {
    if (config.goldenRulePreflight) {
      try {
        const preflight = await runCodexCompanionPreflight(config, paths, goal || label, {
          strict: !!options.strictPreflight
        });
        if (preflight.status === "WARN") {
          appendLiveLog(`[GOLDEN-RULE challenge] ${label}: ANA warned; continuing with caution after logging the challenge.`);
        }
      } catch (error) {
        const message = error.message || String(error);
        appendLiveLog(`[GOLDEN-RULE fail] ${label}: ${message}`);
        vscode.window.showErrorMessage(`ANA Golden Rule blocked ${label}: ${message}`);
        return false;
      }
    } else {
      appendLiveLog(`[GOLDEN-RULE skip] ${label}: anaMax.goldenRulePreflight=false`);
    }
    return true;
  }

  async function runWithGoldenRule(label, goal, operation, options = {}) {
    const config = getConfig();
    const paths = resolveRuntimePaths(config);
    showLiveConsole();
    if (!(await ensureGoldenRulePreflight(label, goal, config, paths, options))) {
      return undefined;
    }
    return operation(config, paths);
  }

  context.subscriptions.push(vscode.commands.registerCommand("anaMax.openLiveConsole", openLiveConsole));

  const openCockpit = vscode.commands.registerCommand("ana.openChat", () => {
    showLiveConsole();
    appendLiveLog("[COCKPIT disabled] Webview cockpit is disabled in this lab build; use ANA MAX Activity Bar controls.");
    vscode.window.showInformationMessage("ANA MAX Cockpit webview is disabled in this lab build. Use Activity Bar controls + Live Console.");
  });

  const callToolExternal = vscode.commands.registerCommand("ana.callTool", async () => {
    const config = getConfig();
    const tool = await vscode.window.showInputBox({ prompt: "Enter MCP Tool Name (from mother-folder)" });
    if (!tool) return;
    const args = await vscode.window.showInputBox({ prompt: "Arguments JSON", value: "{}" });
    if (args === undefined) return;

    try {
      const parsedArgs = JSON.parse(args || "{}");
      if (!(await confirmDangerousAction(tool, parsedArgs))) {
        vscode.window.showWarningMessage("safe-mode blocks tool execution");
        return;
      }
      const paths = resolveRuntimePaths(config);
      if (!(await ensureGoldenRulePreflight("Call MCP Tool", `Manual MCP tool call: ${tool}`, config, paths))) {
        return;
      }
      const response = await requestJson(config.runtimeUrl, {
        jsonrpc: "2.0",
        id: "vscode-tool-call",
        method: "tools/call",
        params: { name: tool, arguments: parsedArgs }
      });
      const doc = await vscode.workspace.openTextDocument({
        content: JSON.stringify(response, null, 2),
        language: "json"
      });
      await vscode.window.showTextDocument(doc, vscode.ViewColumn.Beside);
    } catch (e) {
      vscode.window.showErrorMessage(e.message);
    }
  });

  context.subscriptions.push(openCockpit, callToolExternal);


  context.subscriptions.push(vscode.commands.registerCommand("ana.showCodexMcpConfig", async () => {
    const config = getConfig();
    showLiveConsole();
    appendLiveLog(`[MCP CONFIG]\n${getMcpConfigText(config)}`);
  }));

  context.subscriptions.push(vscode.commands.registerCommand("anaMax.showHealth", async () => {
    await runWithGoldenRule("Smart Ready", goldenRuleGoalForCommand("Smart Ready"), async (config) => {
      await runInCockpit("smartReady", () => getSmartReadiness(config), "ANA MAX smart readiness failed");
    });
  }));

  context.subscriptions.push(vscode.commands.registerCommand("anaMax.codexGuard", async () => {
    const config = getConfig();
    const paths = resolveRuntimePaths(config);
    showLiveConsole();
    await vscode.window.withProgress({
      location: vscode.ProgressLocation.Notification,
      title: "ANA MAX: Codex Guard",
      cancellable: false
    }, async () => {
      const result = await runCodexGuard(
        "Manual guard: Codex must consult ANA before meaningful lab action.",
        config,
        paths,
        { manual: true }
      );
      const status = result?.status || "SKIP";
      vscode.window.showInformationMessage(`ANA Codex Guard: ${status}`);
    });
  }));

  context.subscriptions.push(vscode.commands.registerCommand("anaMax.showHealthJson", async () => {
    await runWithGoldenRule("Health JSON", goldenRuleGoalForCommand("Health JSON"), async (config) => {
      await runInCockpit("health", () => getHealth(config), "ANA MAX health JSON failed");
    });
  }));

  context.subscriptions.push(vscode.commands.registerCommand("anaMax.listTools", async () => {
    await runWithGoldenRule("List Tools", goldenRuleGoalForCommand("List Tools"), async (config) => {
      await runInCockpit("response", async () => {
        const res = await requestJson(config.runtimeUrl, {
          jsonrpc: "2.0",
          id: "list-tools",
          method: "tools/list",
          params: {}
        });
        const tools = res.result?.tools || [];
        const names = tools.map(t => t.name).sort().join("\n");
        return names ? `Tools loaded (${tools.length}):\n\n${names}` : "No tools found.";
      }, "ANA MAX list tools failed");
    });
  }));

  context.subscriptions.push(vscode.commands.registerCommand("anaMax.liveDebug", async () => {
    await runWithGoldenRule("Live Debug", goldenRuleGoalForCommand("Live Debug"), async (config) => {
      await runInCockpit("liveDebug", async () => {
        const health = await getHealth(config);
        const toolsRes = await requestJson(config.runtimeUrl, {
          jsonrpc: "2.0",
          id: "live-debug",
          method: "tools/list",
          params: {}
        });
        const tools = toolsRes.result?.tools || [];
        return {
          runtimeUrl: config.runtimeUrl,
          baseUrl: runtimeBaseUrl(config),
          health,
          tool_count: tools.length,
          sample_tools: tools.slice(0, 8).map(t => t.name),
          checked_at: new Date().toISOString()
        };
      }, "ANA MAX live debug failed");
    });
  }));

  context.subscriptions.push(vscode.commands.registerCommand("anaMax.codexCompanion", async () => {
    const config = getConfig();
    const paths = resolveRuntimePaths(config);
    const root = workspaceRootPath();
    const script = path.join(root || paths.runtimeRoot, "ANA_MAX", "dev_artifacts", "scripts", "ana_codex_companion.py");
    showLiveConsole();
    if (!fs.existsSync(script)) {
      const msg = `ANA Codex Companion script not found: ${script}`;
      appendLiveLog(`[CODEX-COMPANION fail] ${msg}`);
      vscode.window.showErrorMessage(msg);
      return;
    }
    await vscode.window.withProgress({
      location: vscode.ProgressLocation.Notification,
      title: "ANA MAX: Codex Companion",
      cancellable: false
    }, async () => {
      appendLiveLog(`[CODEX-COMPANION] Companion start: ${script}`);
      const preflight = await runCodexCompanionPreflight(
        config,
        paths,
        "Codex asks ANA to observe, challenge blind work, and choose the next verified lab action."
      );
      const firstLine = preflight.firstLine;
      appendLiveLog(`[CODEX-COMPANION] ${firstLine}`);
      vscode.window.showInformationMessage(firstLine);
    });
  }));

  context.subscriptions.push(vscode.commands.registerCommand("anaMax.voiceInbox", async () => {
    const config = getConfig();
    const paths = resolveRuntimePaths(config);
    const script = anaScriptPath(paths, "ana_voice_inbox.py");
    showLiveConsole();
    if (!(await ensureGoldenRulePreflight("Voice Inbox", "Capture microphone dictation into ANA Voice Inbox for Codex.", config, paths))) {
      return;
    }
    if (!fs.existsSync(script)) {
      const msg = `ANA voice inbox script not found: ${script}`;
      appendLiveLog(`[VOICE-INBOX fail] ${msg}`);
      vscode.window.showErrorMessage(msg);
      return;
    }
    const secondsText = await vscode.window.showInputBox({
      prompt: "Seconds to listen",
      value: "8",
      placeHolder: "2-30"
    });
    if (secondsText === undefined) {
      return;
    }
    const seconds = Math.max(2, Math.min(parseInt(secondsText || "8", 10) || 8, 30));
    await vscode.window.withProgress({
      location: vscode.ProgressLocation.Notification,
      title: `ANA MAX: Voice Inbox (${seconds}s)`,
      cancellable: false
    }, async () => {
      speakAccessibility("Voice Inbox listening", "start", config, paths);
      appendLiveLog(`[VOICE-INBOX] Listening for ${seconds}s. Speak now.`);
      try {
        const result = await runPythonScript(config, paths, script, [
          "--duration",
          `${seconds}`,
          "--copy"
        ], (text, isError) => {
          appendLiveLog(`${isError ? "[VOICE-INBOX error]" : "[VOICE-INBOX]"} ${text.trimEnd()}`);
        });
        const payload = JSON.parse(result.stdout);
        const text = payload.data?.record?.text || "";
        appendLiveLog(`[VOICE-INBOX] ${payload.message}${text ? `: ${text}` : ""}`);
        speakAccessibility(payload.success ? "Voice phrase captured" : "Voice inbox did not capture speech", payload.success ? "phrase" : "fail", config, paths);
        vscode.window.showInformationMessage(text ? `ANA Voice Inbox copied: ${text.slice(0, 80)}` : payload.message);
      } catch (error) {
        const message = error.message || String(error);
        appendLiveLog(`[VOICE-INBOX fail] ${message}`);
        speakAccessibility("Voice Inbox failed", "fail", config, paths);
        vscode.window.showWarningMessage(`ANA Voice Inbox did not capture speech: ${message.split(/\r?\n/)[0]}`);
      }
    });
  }));

  context.subscriptions.push(vscode.commands.registerCommand("anaMax.nucleusSmoke", async () => {
    await runWithGoldenRule("Nucleus Smoke", goldenRuleGoalForCommand("Nucleus Smoke"), async (config, paths) => {
    const root = workspaceRootPath();
    const script = path.join(root || paths.runtimeRoot, "ANA_MAX", "dev_artifacts", "scripts", "ana_nucleus_smoke.py");
    showLiveConsole();
    if (!fs.existsSync(script)) {
      const msg = `ANA nucleus smoke script not found: ${script}`;
      appendLiveLog(`[NUCLEUS fail] ${msg}`);
      vscode.window.showErrorMessage(msg);
      return;
    }
    await vscode.window.withProgress({
      location: vscode.ProgressLocation.Notification,
      title: "ANA MAX: Running Nucleus Smoke",
      cancellable: false
    }, async () => {
      appendLiveLog(`[NUCLEUS] Smoke start: ${script}`);
      const result = await runPythonScript(config, paths, script, ["--mcp-url", config.runtimeUrl], (text, isError) => {
        appendLiveLog(`${isError ? "[NUCLEUS error]" : "[NUCLEUS]"} ${text.trimEnd()}`);
      });
      const firstLine = result.stdout.split(/\r?\n/).find(line => line.startsWith("ANA Nucleus:")) || "ANA Nucleus: completed";
      appendLiveLog(`[NUCLEUS] ${firstLine}`);
      vscode.window.showInformationMessage(firstLine);
    });
    });
  }));

  context.subscriptions.push(vscode.commands.registerCommand("anaMax.autonomyPass", async () => {
    const config = getConfig();
    const paths = resolveRuntimePaths(config);
    const root = workspaceRootPath();
    const script = path.join(root || paths.runtimeRoot, "ANA_MAX", "dev_artifacts", "scripts", "ana_autonomy_runner.py");
    showLiveConsole();
    if (!(await ensureGoldenRulePreflight("Autonomy Pass", "Activity Bar Autonomy Pass; ANA should challenge Codex before a multi-step lab action.", config, paths))) {
      return;
    }
    if (!fs.existsSync(script)) {
      const msg = `ANA autonomy runner script not found: ${script}`;
      appendLiveLog(`[AUTONOMY fail] ${msg}`);
      vscode.window.showErrorMessage(msg);
      return;
    }
    await vscode.window.withProgress({
      location: vscode.ProgressLocation.Notification,
      title: "ANA MAX: Running Autonomy Pass",
      cancellable: false
    }, async () => {
      appendLiveLog(`[AUTONOMY] Pass start: ${script}`);
      const result = await runPythonScript(config, paths, script, [
        "--mcp-url",
        config.runtimeUrl,
        "--goal",
        "VS Code Activity Bar Autonomy Pass",
        "--checkpoint"
      ], (text, isError) => {
        appendLiveLog(`${isError ? "[AUTONOMY error]" : "[AUTONOMY]"} ${text.trimEnd()}`);
      });
      const firstLine = result.stdout.split(/\r?\n/).find(line => line.startsWith("ANA Autonomy:")) || "ANA Autonomy: completed";
      appendLiveLog(`[AUTONOMY] ${firstLine}`);
      vscode.window.showInformationMessage(firstLine);
    });
  }));

  context.subscriptions.push(vscode.commands.registerCommand("anaMax.labQualityGate", async () => {
    const config = getConfig();
    const paths = resolveRuntimePaths(config);
    const root = workspaceRootPath();
    const script = path.join(root || paths.runtimeRoot, "ANA_MAX", "dev_artifacts", "scripts", "lab_quality_gate.py");
    showLiveConsole();
    if (!(await ensureGoldenRulePreflight("Lab Quality Gate", "Run the broader lab quality gate after ANA checks context and current risks.", config, paths))) {
      return;
    }
    if (!fs.existsSync(script)) {
      const msg = `ANA lab quality gate script not found: ${script}`;
      appendLiveLog(`[QUALITY fail] ${msg}`);
      vscode.window.showErrorMessage(msg);
      return;
    }
    await vscode.window.withProgress({
      location: vscode.ProgressLocation.Notification,
      title: "ANA MAX: Running Lab Quality Gate",
      cancellable: false
    }, async () => {
      appendLiveLog(`[QUALITY] Gate start: ${script}`);
      const result = await runPythonScript(config, paths, script, [], (text, isError) => {
        appendLiveLog(`${isError ? "[QUALITY error]" : "[QUALITY]"} ${text.trimEnd()}`);
      });
      const firstLine = result.stdout.split(/\r?\n/).find(line => line.startsWith("ANA Lab Quality Gate:")) || "ANA Lab Quality Gate: completed";
      appendLiveLog(`[QUALITY] ${firstLine}`);
      vscode.window.showInformationMessage(firstLine);
    });
  }));

  context.subscriptions.push(vscode.commands.registerCommand("anaMax.noReloadGate", async () => {
    const config = getConfig();
    const paths = resolveRuntimePaths(config);
    const root = workspaceRootPath();
    const script = path.join(root || paths.runtimeRoot, "ANA_MAX", "dev_artifacts", "scripts", "no_reload_quality_gate.py");
    showLiveConsole();
    if (!(await ensureGoldenRulePreflight("No-Reload Gate", "Package/check extension without reload after ANA confirms context and risks.", config, paths))) {
      return;
    }
    if (!fs.existsSync(script)) {
      const msg = `ANA no-reload quality gate script not found: ${script}`;
      appendLiveLog(`[NO-RELOAD fail] ${msg}`);
      vscode.window.showErrorMessage(msg);
      return;
    }
    await vscode.window.withProgress({
      location: vscode.ProgressLocation.Notification,
      title: "ANA MAX: Running No-Reload Gate",
      cancellable: false
    }, async () => {
      appendLiveLog(`[NO-RELOAD] Gate start: ${script}`);
      const result = await runPythonScript(config, paths, script, [], (text, isError) => {
        appendLiveLog(`${isError ? "[NO-RELOAD error]" : "[NO-RELOAD]"} ${text.trimEnd()}`);
      });
      const payload = JSON.parse(result.stdout);
      const passCount = payload.summary?.pass ?? 0;
      const msg = `ANA No-Reload Gate: PASS (${passCount} pass)`;
      appendLiveLog(`[NO-RELOAD] ${msg}`);
      vscode.window.showInformationMessage(msg);
    });
  }));

  context.subscriptions.push(vscode.commands.registerCommand("anaMax.postReloadVerify", async () => {
    await runWithGoldenRule("Post-Reload Verify", goldenRuleGoalForCommand("Post-Reload Verify"), async (config, paths) => {
    const root = workspaceRootPath();
    const script = path.join(root || paths.runtimeRoot, "ANA_MAX", "dev_artifacts", "scripts", "ana_post_reload_verify.py");
    showLiveConsole();
    if (!fs.existsSync(script)) {
      const msg = `ANA post-reload verifier script not found: ${script}`;
      appendLiveLog(`[POST-RELOAD fail] ${msg}`);
      vscode.window.showErrorMessage(msg);
      return;
    }
    await vscode.window.withProgress({
      location: vscode.ProgressLocation.Notification,
      title: "ANA MAX: Running Post-Reload Verify",
      cancellable: false
    }, async () => {
      appendLiveLog(`[POST-RELOAD] Verify start: ${script}`);
      const result = await runPythonScript(config, paths, script, [
        "--mcp-url",
        config.runtimeUrl,
        "--no-write"
      ], (text, isError) => {
        appendLiveLog(`${isError ? "[POST-RELOAD error]" : "[POST-RELOAD]"} ${text.trimEnd()}`);
      });
      const firstLine = result.stdout.split(/\r?\n/).find(line => line.startsWith("ANA Post Reload:")) || "ANA Post Reload: completed";
      appendLiveLog(`[POST-RELOAD] ${firstLine}`);
      vscode.window.showInformationMessage(firstLine);
    });
    });
  }));

  context.subscriptions.push(vscode.commands.registerCommand("anaMax.operatorStatus", async () => {
    await runWithGoldenRule("Operator Status", goldenRuleGoalForCommand("Operator Status"), async (config, paths) => {
    const root = workspaceRootPath();
    const script = path.join(root || paths.runtimeRoot, "ANA_MAX", "dev_artifacts", "scripts", "ana_operator_status.py");
    showLiveConsole();
    if (!fs.existsSync(script)) {
      const msg = `ANA operator status script not found: ${script}`;
      appendLiveLog(`[OPERATOR-STATUS fail] ${msg}`);
      vscode.window.showErrorMessage(msg);
      return;
    }
    await vscode.window.withProgress({
      location: vscode.ProgressLocation.Notification,
      title: "ANA MAX: Operator Status",
      cancellable: false
    }, async () => {
      appendLiveLog(`[OPERATOR-STATUS] Status start: ${script}`);
      const result = await runPythonScript(config, paths, script, [
        "--mcp-url",
        config.runtimeUrl
      ], (text, isError) => {
        appendLiveLog(`${isError ? "[OPERATOR-STATUS error]" : "[OPERATOR-STATUS]"} ${text.trimEnd()}`);
      });
      const firstLine = result.stdout.split(/\r?\n/).find(line => line.startsWith("ANA Operator Status:")) || "ANA Operator Status: completed";
      appendLiveLog(`[OPERATOR-STATUS] ${firstLine}`);
      vscode.window.showInformationMessage(firstLine);
    });
    });
  }));

  context.subscriptions.push(vscode.commands.registerCommand("anaMax.reviewBatchPlan", async () => {
    const config = getConfig();
    const paths = resolveRuntimePaths(config);
    const root = workspaceRootPath();
    const script = path.join(root || paths.runtimeRoot, "ANA_MAX", "dev_artifacts", "scripts", "ana_review_batch_runner.py");
    showLiveConsole();
    if (!(await ensureGoldenRulePreflight("Review Batch Plan", "Preview Dirty Tree review batches after ANA checks current project state.", config, paths))) {
      return;
    }
    if (!fs.existsSync(script)) {
      const msg = `ANA review batch runner script not found: ${script}`;
      appendLiveLog(`[REVIEW-BATCH fail] ${msg}`);
      vscode.window.showErrorMessage(msg);
      return;
    }
    await vscode.window.withProgress({
      location: vscode.ProgressLocation.Notification,
      title: "ANA MAX: Review Batch Plan",
      cancellable: false
    }, async () => {
      appendLiveLog(`[REVIEW-BATCH] Plan start: ${script}`);
      const result = await runPythonScript(config, paths, script, [
        "--all-batches",
        "--no-write"
      ], (text, isError) => {
        appendLiveLog(`${isError ? "[REVIEW-BATCH error]" : "[REVIEW-BATCH]"} ${text.trimEnd()}`);
      });
      const firstLine = result.stdout.split(/\r?\n/).find(line => line.startsWith("ANA Review Batch:")) || "ANA Review Batch: completed";
      appendLiveLog(`[REVIEW-BATCH] ${firstLine}`);
      vscode.window.showInformationMessage(firstLine);
    });
  }));

  context.subscriptions.push(vscode.commands.registerCommand("anaMax.liveBehavior", async () => {
    await runWithGoldenRule("Live Behavior", goldenRuleGoalForCommand("Live Behavior"), async (config, paths) => {
    const root = workspaceRootPath();
    const script = path.join(root || paths.runtimeRoot, "ANA_MAX", "dev_artifacts", "scripts", "ana_live_behavior_check.py");
    showLiveConsole();
    if (!fs.existsSync(script)) {
      const msg = `ANA live behavior checker script not found: ${script}`;
      appendLiveLog(`[LIVE-BEHAVIOR fail] ${msg}`);
      vscode.window.showErrorMessage(msg);
      return;
    }
    await vscode.window.withProgress({
      location: vscode.ProgressLocation.Notification,
      title: "ANA MAX: Live Behavior",
      cancellable: false
    }, async () => {
      appendLiveLog(`[LIVE-BEHAVIOR] Check start: ${script}`);
      try {
        const result = await runPythonScript(config, paths, script, [
          "--mcp-url",
          config.runtimeUrl
        ], (text, isError) => {
          appendLiveLog(`${isError ? "[LIVE-BEHAVIOR error]" : "[LIVE-BEHAVIOR]"} ${text.trimEnd()}`);
        });
        const firstLine = result.stdout.split(/\r?\n/).find(line => line.startsWith("ANA Live Behavior:")) || "ANA Live Behavior: completed";
        appendLiveLog(`[LIVE-BEHAVIOR] ${firstLine}`);
        vscode.window.showInformationMessage(firstLine);
      } catch (error) {
        const message = error.message || String(error);
        appendLiveLog(`[LIVE-BEHAVIOR warn] ${message}`);
        const firstLine = message.split(/\r?\n/).find(line => line.startsWith("ANA Live Behavior:")) || "ANA Live Behavior: WARN";
        vscode.window.showWarningMessage(firstLine);
      }
    });
    });
  }));

  context.subscriptions.push(vscode.commands.registerCommand("anaMax.reloadReadiness", async () => {
    await runWithGoldenRule("Reload Readiness", goldenRuleGoalForCommand("Reload Readiness"), async (config, paths) => {
    const root = workspaceRootPath();
    const script = path.join(root || paths.runtimeRoot, "ANA_MAX", "dev_artifacts", "scripts", "ana_reload_readiness.py");
    showLiveConsole();
    if (!fs.existsSync(script)) {
      const msg = `ANA reload readiness script not found: ${script}`;
      appendLiveLog(`[RELOAD-READINESS fail] ${msg}`);
      vscode.window.showErrorMessage(msg);
      return;
    }
    await vscode.window.withProgress({
      location: vscode.ProgressLocation.Notification,
      title: "ANA MAX: Reload Readiness",
      cancellable: false
    }, async () => {
      appendLiveLog(`[RELOAD-READINESS] Check start: ${script}`);
      const result = await runPythonScript(config, paths, script, [
        "--mcp-url",
        config.runtimeUrl,
        "--no-write"
      ], (text, isError) => {
        appendLiveLog(`${isError ? "[RELOAD-READINESS error]" : "[RELOAD-READINESS]"} ${text.trimEnd()}`);
      });
      const firstLine = result.stdout.split(/\r?\n/).find(line => line.startsWith("ANA Reload Readiness:")) || "ANA Reload Readiness: completed";
      appendLiveLog(`[RELOAD-READINESS] ${firstLine}`);
      vscode.window.showInformationMessage(firstLine);
    });
    });
  }));

  context.subscriptions.push(vscode.commands.registerCommand("anaMax.reloadConsistency", async () => {
    await runWithGoldenRule("Reload Consistency", goldenRuleGoalForCommand("Reload Consistency"), async (config, paths) => {
    const root = workspaceRootPath();
    const script = path.join(root || paths.runtimeRoot, "ANA_MAX", "dev_artifacts", "scripts", "ana_reload_consistency_check.py");
    showLiveConsole();
    if (!fs.existsSync(script)) {
      const msg = `ANA reload consistency script not found: ${script}`;
      appendLiveLog(`[RELOAD-CONSISTENCY fail] ${msg}`);
      vscode.window.showErrorMessage(msg);
      return;
    }
    await vscode.window.withProgress({
      location: vscode.ProgressLocation.Notification,
      title: "ANA MAX: Reload Consistency",
      cancellable: false
    }, async () => {
      appendLiveLog(`[RELOAD-CONSISTENCY] Check start: ${script}`);
      const result = await runPythonScript(config, paths, script, [
        "--mcp-url",
        config.runtimeUrl,
        "--no-write"
      ], (text, isError) => {
        appendLiveLog(`${isError ? "[RELOAD-CONSISTENCY error]" : "[RELOAD-CONSISTENCY]"} ${text.trimEnd()}`);
      });
      const firstLine = result.stdout.split(/\r?\n/).find(line => line.startsWith("ANA Reload Consistency:")) || "ANA Reload Consistency: completed";
      appendLiveLog(`[RELOAD-CONSISTENCY] ${firstLine}`);
      vscode.window.showInformationMessage(firstLine);
    });
    });
  }));

  context.subscriptions.push(vscode.commands.registerCommand("anaMax.showRouterDecisions", async () => {
    await runWithGoldenRule("Recommend", goldenRuleGoalForCommand("Recommend"), async (config) => {
      await runInCockpit("recommend", () => callTool(config, "agent_coach", {
      action: "recommend",
      task: "VS Code command asks for the next best ANA MAX tool",
      max_tools: 5,
      include_prompt: false
      }), "ANA MAX recommendation failed");
    });
  }));

  context.subscriptions.push(vscode.commands.registerCommand("anaMax.profileStatus", async () => {
    await runWithGoldenRule("Profile Status", goldenRuleGoalForCommand("Profile Status"), async (config, paths) => {
    const root = workspaceRootPath();
    const coverageScript = path.join(root || paths.runtimeRoot, "ANA_MAX", "dev_artifacts", "scripts", "ana_permission_manifest_coverage.py");
    await runInCockpit("response", async () => {
      const result = await callTool(config, "tool_router", { mode: "profile_status" });
      if (result.success && result.data?.schema === "ana.tool_router.profile_status.v1") {
        return JSON.stringify(result.data, null, 2);
      }
      appendLiveLog("[PROFILE] MCP profile_status unavailable; falling back to local permission manifest coverage.");
      if (!fs.existsSync(coverageScript)) {
        return JSON.stringify(result.data || result, null, 2);
      }
      const fallback = await runPythonScript(config, paths, coverageScript, ["--json", "--no-write"], (text, isError) => {
        appendLiveLog(`${isError ? "[PROFILE fallback error]" : "[PROFILE fallback]"} ${text.trimEnd()}`);
      });
      return fallback.stdout.trim();
    }, "ANA MAX profile status failed");
    });
  }));

  context.subscriptions.push(vscode.commands.registerCommand("anaMax.wakeSession", async () => {
    const config = getConfig();
    const paths = resolveRuntimePaths(config);
    if (!(await ensureGoldenRulePreflight("Wake Session", "Wake ANA session memory with Codex aware of current context.", config, paths))) {
      return;
    }
    await runInCockpit("lifecycle", () => callTool(config, "session_lifecycle", { action: "wake" }), "ANA MAX wake failed");
  }));

  context.subscriptions.push(vscode.commands.registerCommand("anaMax.checkpoint", async () => {
    const config = getConfig();
    const paths = resolveRuntimePaths(config);
    if (!(await ensureGoldenRulePreflight("Checkpoint", "Save a checkpoint only after ANA observes current lab state.", config, paths))) {
      return;
    }
    await runInCockpit("checkpoint", () => runLocalCheckpoint(config, paths, {
      title: "Activity Bar quick checkpoint",
      summary: "Operator saved a quick checkpoint from the ANA MAX Activity Bar.",
      currentGoal: "Continue ANA MAX MCP/tool orchestration from the stable Activity Bar controls.",
      nextSteps: "Verify MCP smart readiness, use Activity Bar controls for tool workflows, and keep Cockpit as a monitor.",
      filesChanged: "vscode_extension/extension.js; vscode_extension/package.json",
      validation: "MCP health should be online and Activity Bar commands should execute.",
      risks: "Cockpit webview button handling may remain host-dependent; Activity Bar is the stable fallback.",
      syncStatus: "Mother lab only; public release sync pending review."
    }), "ANA MAX checkpoint failed");
  }));

  context.subscriptions.push(vscode.commands.registerCommand("anaMax.previewRest", async () => {
    await runWithGoldenRule("Rest Preview", goldenRuleGoalForCommand("Rest Preview"), async (config) => {
      await runInCockpit("lifecycle", () => callTool(config, "session_lifecycle", {
      action: "rest",
      consolidate: false
      }), "ANA MAX rest preview failed");
    });
  }));

  context.subscriptions.push(vscode.commands.registerCommand("anaMax.runRemSleep", async () => {
    const config = getConfig();
    const paths = resolveRuntimePaths(config);
    if (!(await ensureGoldenRulePreflight("Save REM", "Consolidate REM/session memory after ANA challenges current state.", config, paths))) {
      return;
    }
    await runInCockpit("remSleep", () => callTool(config, "session_lifecycle", {
      action: "rest",
      consolidate: true,
      save_memory: true
    }), "ANA MAX REM sleep failed");
  }));

  context.subscriptions.push(vscode.commands.registerCommand("anaMax.refreshCodeMap", async () => {
    const config = getConfig();
    const paths = resolveRuntimePaths(config);
    const root = workspaceRootPath();
    const script = path.join(root || paths.runtimeRoot, "ANA_MAX", "dev_artifacts", "scripts", "ana_refresh_context_maps.py");
    showLiveConsole();
    if (!(await ensureGoldenRulePreflight("Refresh Context Maps", "Refresh Code Map and Graph Map after ANA checks whether maps are needed.", config, paths))) {
      return;
    }
    if (!fs.existsSync(script)) {
      const msg = `ANA context maps refresh script not found: ${script}`;
      appendLiveLog(`[CONTEXT-MAPS fail] ${msg}`);
      vscode.window.showErrorMessage(msg);
      return;
    }
    await vscode.window.withProgress({
      location: vscode.ProgressLocation.Notification,
      title: "ANA MAX: Refreshing Context Maps",
      cancellable: false
    }, async () => {
      appendLiveLog(`[CONTEXT-MAPS] Refresh start: ${script}`);
      const result = await runPythonScript(config, paths, script, ["--json"], (text, isError) => {
        appendLiveLog(`${isError ? "[CONTEXT-MAPS error]" : "[CONTEXT-MAPS]"} ${text.trimEnd()}`);
      });
      const payload = JSON.parse(result.stdout);
      const code = payload.code_map || {};
      const graph = payload.graph_map || {};
      appendLiveLog(`[CONTEXT-MAPS] Refresh done: code=${code.summaries} graph=${graph.nodes}n/${graph.edges}e maps=${payload.message} elapsed=${payload.elapsed_sec}s`);
      post(panel, "response", `Context Maps refreshed:\n${JSON.stringify(payload, null, 2)}`);
      vscode.window.showInformationMessage(`ANA Context Maps refreshed: ${payload.message}`);
    });
  }));

  context.subscriptions.push(vscode.commands.registerCommand("anaMax.showTrustScore", async () => {
    await runWithGoldenRule("Trust Score", goldenRuleGoalForCommand("Trust Score"), async (config) => {
      await runInCockpit("response", async () => {
      const payload = await callTool(config, "session_audit", {
        action: "trust",
        hours: 1,
        limit: 100
      });
      const trust = payload.data?.trust || {};
      const identity = payload.data?.identity_surface || {};
      const score = trust.score ?? "?";
      appendLiveLog(`[AUDIT] Trust ${score} percent. Identity ${identity.status || "unknown"}. ${trust.message || ""}`);
      return JSON.stringify(payload.data, null, 2);
      }, "ANA MAX trust score failed");
    });
  }));

  context.subscriptions.push(vscode.commands.registerCommand("anaMax.generateSessionAudit", async () => {
    const config = getConfig();
    const paths = resolveRuntimePaths(config);
    if (!(await ensureGoldenRulePreflight("Session Audit", "Generate session audit after ANA verifies current context and trust signals.", config, paths))) {
      return;
    }
    const runId = `vscode-${new Date().toISOString().replace(/[:.]/g, "-")}`;
    await runInCockpit("response", async () => {
      const payload = await callTool(config, "session_audit", {
        action: "generate",
        run_id: runId,
        hours: 1,
        limit: 120
      });
      const data = payload.data || {};
      const trust = data.trust || {};
      const score = trust.score ?? data.trust_score ?? "?";
      const status = data.status || data.integrity?.status || "ready";
      appendLiveLog(`[AUDIT] Session audit ${status}. Trust ${score} percent. Run ${runId}.`);
      return JSON.stringify(data, null, 2);
    }, "ANA MAX session audit failed");
  }));

  context.subscriptions.push(vscode.commands.registerCommand("anaMax.conversationAudit", async () => {
    await runWithGoldenRule("Conversation Audit", goldenRuleGoalForCommand("Conversation Audit"), async (config, paths) => {
      await runInCockpit("response", async () => {
      const script = anaScriptPath(paths, "ana_conversation_audit.py");
      if (!fs.existsSync(script)) {
        throw new Error(`ANA conversation audit script not found: ${script}`);
      }
      const result = await runPythonScript(config, paths, script, [
        "--hours",
        "1",
        "--limit",
        "120",
        "--json"
      ], (text, isError) => {
        appendLiveLog(`${isError ? "[CONVERSATION-AUDIT error]" : "[CONVERSATION-AUDIT]"} ${text.trimEnd()}`);
      });
      const data = JSON.parse(result.stdout);
      const status = data.status || "UNKNOWN";
      const events = data.events ?? 0;
      const spoken = data.spoken_events ?? 0;
      const skipped = data.sensitive_skipped ?? 0;
      appendLiveLog(`[CONVERSATION-AUDIT] ${status} events=${events} spoken=${spoken} skipped=${skipped}.`);
      speakAccessibility(`Conversation audit ${status}. ${events} events. ${spoken} spoken.`, "ready", config, paths);
      return JSON.stringify(data, null, 2);
      }, "ANA MAX conversation audit failed");
    });
  }));

  context.subscriptions.push(vscode.commands.registerCommand("anaMax.liveConversationAudit", async () => {
    const config = getConfig();
    const paths = resolveRuntimePaths(config);
    showLiveConsole();
    const started = startConversationAuditTail(config, paths, { manual: true });
    if (started) {
      appendLiveLog("[CONVERSATION-LIVE] Manual live stream requested.");
      speakAccessibility("Live conversation audit", "ready", config, paths);
    } else {
      appendLiveLog("[CONVERSATION-LIVE fail] Could not start live stream.");
      speakAccessibility("Live conversation audit failed", "fail", config, paths);
    }
  }));

  context.subscriptions.push(vscode.commands.registerCommand("anaMax.voiceOperatorSmoke", async () => {
    await runWithGoldenRule("Voice Operator Smoke", goldenRuleGoalForCommand("Voice Operator Smoke"), async (config, paths) => {
    showLiveConsole();
    await runInCockpit("response", async () => {
      const script = anaScriptPath(paths, "ana_voice_operator_smoke.py");
      if (!fs.existsSync(script)) {
        throw new Error(`ANA voice operator smoke script not found: ${script}`);
      }
      const result = await runPythonScript(config, paths, script, [
        "--label",
        "activity-bar",
        "--timeout",
        "15",
        "--json"
      ], (text, isError) => {
        appendLiveLog(`${isError ? "[VOICE-OPERATOR error]" : "[VOICE-OPERATOR]"} ${text.trimEnd()}`);
      });
      const data = JSON.parse(result.stdout);
      appendLiveLog(`[VOICE-OPERATOR] ${data.status} audit_seen=${data.audit_seen} phrase="${data.phrase}"`);
      speakAccessibility(`Voice operator smoke ${data.status}`, data.success ? "ready" : "fail", config, paths);
      return JSON.stringify(data, null, 2);
    }, "ANA MAX voice operator smoke failed");
    });
  }));

  context.subscriptions.push(vscode.commands.registerCommand("anaMax.binaryMap", async () => {
    const config = getConfig();
    const paths = resolveRuntimePaths(config);
    const binaryPath = await vscode.window.showInputBox({
      prompt: "Binary path inside ANA_MAX workspace",
      value: "archives/security_research/de pe red edit/tproxy-v0.9.2-windows-amd64/tproxy.exe"
    });
    if (!binaryPath) return;
    if (!(await ensureGoldenRulePreflight("Binary Map", `Static binary map for ${binaryPath}`, config, paths))) {
      return;
    }
    await runInCockpit("response", async () => JSON.stringify((await callTool(config, "binary_map", {
      path: binaryPath,
      strings_limit: 20
    })).data, null, 2), "ANA MAX binary map failed");
  }));

  context.subscriptions.push(vscode.commands.registerCommand("anaMax.identity", async () => {
    await runWithGoldenRule("Identity", goldenRuleGoalForCommand("Identity"), async (config) => {
      await runInCockpit("response", async () => JSON.stringify((await callTool(config, "ana_identity", {})).data, null, 2), "ANA MAX identity failed");
    });
  }));

  context.subscriptions.push(vscode.commands.registerCommand("anaMax.startRuntime", startRuntime));

  context.subscriptions.push(vscode.commands.registerCommand("anaMax.executeTool", async () => {
    await vscode.commands.executeCommand("ana.callTool");
  }));

  context.subscriptions.push(vscode.commands.registerCommand("anaMax.inspectRuntime", async () => {
    await runWithGoldenRule("Inspect Runtime", goldenRuleGoalForCommand("Inspect Runtime"), async (config) => {
      await runInCockpit("response", async () => {
      const response = await requestJson(config.runtimeUrl, {
        jsonrpc: "2.0",
        id: "inspect-runtime",
        method: "tools/call",
        params: { name: "ana_runtime_inspector", arguments: { action: "snapshot" } }
      });
      return JSON.stringify(response, null, 2);
      }, "ANA MAX runtime inspection failed");
    });
  }));

  context.subscriptions.push(vscode.commands.registerCommand("anaMax.runScenario", async () => {
    vscode.window.showInformationMessage("ANA MAX scenario runner is not wired in this cockpit build yet.");
  }));

  context.subscriptions.push(vscode.commands.registerCommand("anaMax.showObservability", async () => {
    vscode.window.showInformationMessage("ANA MAX observability view is not wired in this cockpit build yet.");
  }));

  // Legacy commands
  context.subscriptions.push(vscode.commands.registerCommand("anaMax.openDashboard", async () => {
    const config = getConfig();
    const paths = resolveRuntimePaths(config);
    showLiveConsole();
    try {
      if (!(await ensureGoldenRulePreflight("Open Dashboard", "Open generated dashboard after ANA verifies current runtime state.", config, paths))) {
        return;
      }
      appendLiveLog("[DASHBOARD] Generating local dashboard from live MCP runtime.");
      const health = await getHealth(config);
      const toolsRes = await requestJson(config.runtimeUrl, {
        jsonrpc: "2.0",
        id: "dashboard-list-tools",
        method: "tools/list",
        params: {}
      });
      const tools = toolsRes.result?.tools || [];
      const healthcheck = await callTool(config, "tool_healthcheck", { scope: "safe" });
      const filePath = writeLocalDashboard(config, health, tools, healthcheck);
      appendLiveLog(`[DASHBOARD] Open local file: ${filePath}`);
      const opened = await openLocalFile(config, filePath);
      appendLiveLog(`[DASHBOARD] Open method: ${opened.method}${opened.executable ? ` (${opened.executable})` : ""}`);
    } catch (error) {
      appendLiveLog(`[DASHBOARD fail] ${error.message}`);
      vscode.window.showErrorMessage(`ANA MAX dashboard failed: ${error.message}`);
    }
  }));

  if (getConfig().autoStartRuntime) {
    const autoStartTimer = setTimeout(() => {
      showLiveConsole();
      appendLiveLog("[AUTO-START] Extension activated; opening Live Console, voice bridge, and MCP runtime.");
      startRuntime().catch((error) => {
        appendLiveLog(`[AUTO-START fail] ${error.message || error}`);
      });
    }, 900);
    context.subscriptions.push({ dispose: () => clearTimeout(autoStartTimer) });
  } else {
    appendLiveLog("[AUTO-START skip] anaMax.autoStartRuntime=false");
  }
}

function post(panel, type, content) {
  panel?.webview.postMessage({ type, content });
}

function getNonce() {
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  let text = "";
  for (let i = 0; i < 32; i++) {
    text += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return text;
}

function getWebviewContent(webview) {
  const nonce = getNonce();
  const cspSource = webview?.cspSource || "";
  return `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <!-- Local lab build: keep scripts unblocked so the cockpit can show live diagnostics. -->
    <style>
        body { font-family: sans-serif; background: #1e1e1e; color: #ccc; padding: 20px; display: flex; flex-direction: column; height: 100vh; margin: 0; }
        .header { background: #252526; padding: 15px; border-radius: 8px; border: 1px solid #333; margin-bottom: 15px; }
        h1 { font-size: 18px; margin: 0 0 5px 0; color: #007acc; }
        p { font-size: 12px; margin: 0; color: #888; }
        .quickstart { background: #202832; border: 1px solid #33475f; border-radius: 6px; padding: 10px; margin-bottom: 12px; }
        .quickstart h2 { font-size: 13px; margin: 0 0 8px 0; color: #d7e8ff; }
        .quickstart ol { margin: 0; padding-left: 18px; color: #c7d8ea; font-size: 12px; line-height: 1.5; }
        .quickstart code { color: #8fd3ff; }
        .toolbar { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 15px; }
        .group-label { width: 100%; color: #aab6c3; font-size: 11px; text-transform: uppercase; margin-top: 4px; }
        .status { background: #1f2a24; border: 1px solid #315c3f; border-radius: 6px; padding: 10px; margin-bottom: 12px; font-size: 12px; color: #b7e4c7; white-space: pre-wrap; }
        .status.bad { background: #3a2323; border-color: #713333; color: #ffc9c9; }
        .debug { background: #181f27; border: 1px solid #2f4e68; border-radius: 6px; padding: 10px; margin-bottom: 12px; font-size: 12px; color: #d7e8ff; white-space: pre-wrap; min-height: 54px; }
        .debug.bad { background: #3a2323; border-color: #713333; color: #ffc9c9; }
        button { background: #0e639c; color: white; border: none; padding: 8px 12px; border-radius: 4px; cursor: pointer; font-size: 12px; min-height: 32px; }
        button.secondary { background: #3d4c5c; }
        button.safe { background: #1f7a54; }
        button.save { background: #76591f; }
        button:hover { background: #1177bb; }
        #chat { flex: 1; background: #252526; border: 1px solid #333; border-radius: 8px; overflow-y: auto; padding: 15px; margin-bottom: 15px; display: flex; flex-direction: column; gap: 10px; min-height: 200px; }
        .msg { padding: 10px; border-radius: 6px; font-size: 13px; line-height: 1.4; white-space: pre-wrap; }
        .msg.user { background: #37373d; border-left: 4px solid #007acc; align-self: flex-end; max-width: 80%; }
        .msg.ai { background: #2d2d30; border-left: 4px solid #4ec9b0; align-self: flex-start; max-width: 90%; }
        .msg.error { background: #4b1a1a; border-left: 4px solid #f44336; }
        .input-box { display: flex; gap: 10px; }
        input { flex: 1; background: #3c3c3c; color: #eee; border: 1px solid #555; padding: 10px; border-radius: 4px; outline: none; }
        .log-header { font-size: 10px; color: #555; text-transform: uppercase; margin-bottom: 4px; font-weight: bold; margin-top: 10px; display: flex; justify-content: space-between; gap: 8px; }
        .log-follow { color: #77d977; font-weight: normal; text-transform: none; }
        .log-follow.paused { color: #d7b65a; }
        .live-log { background: #000; color: #0f0; font-family: monospace; font-size: 11px; padding: 10px; border-radius: 6px; border: 1px solid #333; height: 120px; overflow-y: auto; margin-bottom: 15px; white-space: pre-wrap; }
    </style>
</head>
<body>
    <div class="header">
        <h1>ANA MAX Codex MCP Cockpit</h1>
        <p>Start ANA, check readiness, wake the last session, then let your AI agent ask ANA which tool to use next.</p>
    </div>
    <div class="quickstart">
        <h2>Beginner Flow</h2>
        <ol>
            <li>Press <code>Start MCP Server</code> once when ANA is offline.</li>
            <li>Press <code>Smart Ready</code>. Green means the agent can use ANA tools.</li>
            <li>Press <code>Wake</code> so the agent loads the last session memory.</li>
            <li>Use <code>Recommend</code> before risky work, then <code>Rest Preview</code> before saving REM Sleep.</li>
        </ol>
    </div>
    <div class="toolbar">
        <div class="group-label">Start here</div>
        <button title="Start the local ANA MAX MCP server if it is offline." data-cmd="startRuntime">1 Start MCP Server</button>
        <button class="safe" title="Verify ANA MAX health, router, coach, and tool list." data-cmd="smartReady">2 Smart Ready</button>
        <button class="safe" title="Load last REM Sleep context or create a first-run manifest." data-action="wakeSession">3 Wake</button>
        <div class="group-label">Daily work</div>
        <button title="Ask ANA which tool should be used next." data-action="recommend">Recommend</button>
        <button class="secondary" title="Save a compact handoff checkpoint." data-action="checkpoint">Checkpoint</button>
        <button class="secondary" title="Analyze the session without writing memory." data-action="previewRest">Rest Preview</button>
        <button class="save" title="Save REM Sleep after reviewing the preview." data-action="remSleep">Save REM</button>
        <div class="group-label">Advanced</div>
        <button class="secondary" title="Refresh Code Map and Graph Map for fresh project context." data-action="refreshCodeMap">Refresh Context Maps</button>
        <button class="secondary" title="Show current audit trust score." data-action="trustScore">Trust Score</button>
        <button class="secondary" title="Generate session audit with hash-chain integrity." data-action="sessionAudit">Session Audit</button>
        <button class="secondary" title="Analyze a binary statically without executing it." data-action="binaryMap">Binary Map</button>
        <button class="secondary" title="Show raw health JSON." data-cmd="health">Health JSON</button>
        <button class="secondary" title="List MCP tools exposed by ANA MAX." data-cmd="listTools">List Tools</button>
        <button class="secondary" title="Refresh live MCP server health and discovered tool count." data-action="liveDebug">Live Debug</button>
        <button class="secondary" title="Show Codex MCP config." data-cmd="codexMcpConfig">MCP Config</button>
        <button class="secondary" title="Call ANA identity." data-action="identity">Identity</button>
    </div>
    <div id="status" class="status">Press Smart Ready. If it is green, press Wake before work.</div>
    <div id="debug" class="debug">Live Debug: waiting for MCP server status...</div>
    <div class="log-header"><span>Live Runtime Log</span><span id="log-follow" class="log-follow">following latest</span></div>
    <div id="live-log" class="live-log">Waiting for runtime output...</div>
    <div id="chat"></div>
    <div class="input-box">
        <input type="text" id="in" placeholder="Optional task for Recommend, or /tool name {}" />
        <button id="sendButton">Send</button>
    </div>
    <script nonce="${nonce}">
        document.documentElement.dataset.anaCockpitScript = 'running';
        const vscode = acquireVsCodeApi();
        const chat = document.getElementById('chat');
        const input = document.getElementById('in');
        const liveLog = document.getElementById('live-log');
        const logFollow = document.getElementById('log-follow');
        let logPinnedToBottom = true;

        function reportUiError(error) {
            const message = error && error.message ? error.message : String(error || 'Unknown cockpit UI error');
            const stack = error && error.stack ? error.stack : '';
            vscode.postMessage({ command: 'webviewError', message, stack });
        }

        window.addEventListener('error', (event) => {
            reportUiError(event.error || event.message);
        });

        window.addEventListener('unhandledrejection', (event) => {
            reportUiError(event.reason || 'Unhandled cockpit promise rejection');
        });

        function isNearBottom(element) {
            return element.scrollHeight - element.scrollTop - element.clientHeight < 24;
        }

        function updateLogFollowState() {
            logPinnedToBottom = isNearBottom(liveLog);
            logFollow.textContent = logPinnedToBottom ? 'following latest' : 'paused while reading';
            logFollow.className = 'log-follow ' + (logPinnedToBottom ? '' : 'paused');
        }

        function scrollLiveLogToBottom() {
            liveLog.scrollTop = liveLog.scrollHeight;
            requestAnimationFrame(() => {
                liveLog.scrollTop = liveLog.scrollHeight;
                updateLogFollowState();
            });
        }

        liveLog.addEventListener('scroll', updateLogFollowState);
        liveLog.addEventListener('dblclick', scrollLiveLogToBottom);

        function cmd(command) {
            addMsg(command.toUpperCase(), 'user');
            vscode.postMessage({ command });
        }

        function identity() {
            addMsg('/tool ana_identity {}', 'user');
            vscode.postMessage({ command: "execute", tool: "ana_identity", args: {} });
        }

        function recommend() {
            const task = input.value.trim() || 'Cockpit operator asks for the next best ANA MAX tool';
            addMsg('RECOMMEND: ' + task, 'user');
            vscode.postMessage({ command: "recommend", task });
        }

        function wakeSession() {
            addMsg('WAKE: load last REM context or first-run manifest', 'user');
            vscode.postMessage({ command: "wakeSession" });
        }

        function checkpoint() {
            const summary = input.value.trim() || 'Operator saved a quick checkpoint before risking chat loss.';
            addMsg('CHECKPOINT: ' + summary, 'user');
            vscode.postMessage({ command: "checkpoint", summary });
        }

        function remSleep() {
            addMsg('REM SLEEP: save recent session lessons', 'user');
            vscode.postMessage({ command: "remSleep" });
        }

        function previewRest() {
            addMsg('REST PREVIEW: analyze recent session lessons without writing', 'user');
            vscode.postMessage({ command: "previewRest" });
        }

        function refreshCodeMap() {
            addMsg('REFRESH CONTEXT MAPS: build code and graph project context', 'user');
            vscode.postMessage({ command: "refreshCodeMap" });
        }

        function trustScore() {
            addMsg('TRUST SCORE: calculate evidence-weighted confidence', 'user');
            vscode.postMessage({ command: "trustScore" });
        }

        function sessionAudit() {
            addMsg('SESSION AUDIT: generate public-safe audit report', 'user');
            vscode.postMessage({ command: "sessionAudit" });
        }

        function binaryMap() {
            addMsg('BINARY MAP: static executable/library analysis', 'user');
            vscode.postMessage({ command: "binaryMap" });
        }

        function liveDebug() {
            vscode.postMessage({ command: "liveDebug" });
        }

        function send() {
            const val = input.value.trim();
            if(!val) return;
            addMsg(val, 'user');
            vscode.postMessage({ command: 'sendMessage', text: val });
            input.value = '';
        }

        function addMsg(text, type) {
            const d = document.createElement('div');
            d.className = 'msg ' + type;
            // Sanitize carriage returns that can corrupt terminal output embedded in tool responses.
            d.textContent = String(text || '').replace(/\r/g, '');
            chat.appendChild(d);
            chat.scrollTop = chat.scrollHeight;
        }

        function formatSmartReadiness(report) {
            const checks = (report.checks || []).map(c => (c.ok ? '[OK] ' : '[FAIL] ') + c.name).join('\\n');
            const stack = ((report.recommend || {}).tool_stack || []).join(', ') || 'none';
            return (report.ok ? 'SMART READY' : 'NOT READY')
                + '\\nhealth=' + ((report.health || {}).status)
                + ' mcp_ready=' + ((report.health || {}).mcp_ready)
                + ' tools=' + report.tool_count
                + '\\nprimary_tool=' + (((report.recommend || {}).primary_tool) || 'none')
                + '\\ntool_stack=' + stack
                + '\\n\\n' + checks;
        }

        function formatToolGuidance(content) {
            const summary = content.guidance_summary || {};
            const stack = (summary.tool_stack || []).join(', ') || 'none';
            return 'Tool failed with guidance: ' + (content.tool || 'unknown')
                + '\\nprimary_tool=' + (summary.primary_tool || 'none')
                + '\\ntool_stack=' + stack
                + '\\nnext_action=' + (summary.next_action || '')
                + '\\nsource=' + (summary.source || '')
                + '\\n\\nFull payload:\\n' + JSON.stringify(content.payload, null, 2);
        }

        function formatLiveDebug(content) {
            if(content.error) {
                return 'MCP LIVE: OFFLINE'
                    + '\\nurl=' + (content.runtimeUrl || '')
                    + '\\nchecked_at=' + (content.checked_at || '')
                    + '\\nerror=' + content.error;
            }
            const health = content.health || {};
            const sample = (content.sample_tools || []).join(', ') || 'none';
            return 'MCP LIVE: ' + (health.status || 'unknown')
                + '\\nurl=' + (content.runtimeUrl || '')
                + '\\nmcp_ready=' + health.mcp_ready
                + ' tools=' + content.tool_count
                + '\\nchecked_at=' + (content.checked_at || '')
                + '\\nsample_tools=' + sample;
        }

        window.addEventListener('message', (e) => {
            const m = e.data || {};
            if(m.type === 'response') addMsg(m.content, 'ai');
            if(m.type === 'health') addMsg('Health Check:\\n' + JSON.stringify(m.content, null, 2), 'ai');
            if(m.type === 'smartReady') {
                const status = document.getElementById('status');
                status.textContent = formatSmartReadiness(m.content);
                status.className = 'status ' + (m.content.ok ? '' : 'bad');
                addMsg('Smart Readiness:\\n' + formatSmartReadiness(m.content), 'ai');
            }
            if(m.type === 'recommend') {
                const stack = (m.content.tool_stack || []).join(', ') || 'none';
                addMsg('Recommendation:\\nprimary_tool=' + (m.content.primary_tool || 'none') + '\\ntool_stack=' + stack + '\\nnext_action=' + (m.content.next_action || ''), 'ai');
            }
            if(m.type === 'checkpoint') {
                addMsg('Checkpoint saved:\\n' + JSON.stringify(m.content, null, 2), 'ai');
            }
            if(m.type === 'remSleep') {
                addMsg('REM sleep saved:\\n' + JSON.stringify(m.content, null, 2), 'ai');
            }
            if(m.type === 'lifecycle') {
                addMsg('Lifecycle:\\n' + JSON.stringify(m.content, null, 2), 'ai');
            }
            if(m.type === 'toolGuidance') {
                addMsg(formatToolGuidance(m.content), 'ai');
            }
            if(m.type === 'liveDebug') {
                const debug = document.getElementById('debug');
                debug.textContent = formatLiveDebug(m.content);
                debug.className = 'debug ' + (m.content.error ? 'bad' : '');
            }
            if(m.type === 'error') {
                const debug = document.getElementById('debug');
                debug.textContent = 'Last error:\\n' + m.content;
                debug.className = 'debug bad';
                addMsg('Error: ' + m.content, 'error');
            }
            if(m.type === 'runtimeLog') {
                const log = liveLog;
                const shouldFollow = logPinnedToBottom || isNearBottom(log);
                if (log.textContent.includes('Waiting for runtime output...')) {
                    log.textContent = '';
                }
                log.textContent += m.content;
                if (shouldFollow) {
                    scrollLiveLogToBottom();
                } else {
                    updateLogFollowState();
                }
            }
            if(m.command === 'execute') vscode.postMessage(m);
        });

        const actions = {
            binaryMap,
            checkpoint,
            identity,
            liveDebug,
            previewRest,
            refreshCodeMap,
            recommend,
            remSleep,
            sessionAudit,
            trustScore,
            wakeSession
        };

        input.addEventListener('keydown', (e) => { if(e.key === 'Enter') send(); });
        document.getElementById('sendButton').addEventListener('click', send);

        document.addEventListener('click', (event) => {
            const button = event.target.closest('button[data-cmd], button[data-action]');
            if (!button) return;
            event.preventDefault();
            try {
                if (button.dataset.cmd) {
                    cmd(button.dataset.cmd);
                    return;
                }
                const actionName = button.dataset.action;
                const action = actions[actionName];
                if (typeof action !== 'function') {
                    throw new Error('Unknown cockpit action: ' + actionName);
                }
                action();
            } catch (error) {
                addMsg('Cockpit button error: ' + (error.message || error), 'error');
                reportUiError(error);
            }
        });

        addMsg('Cockpit ready. Primary path: VS Code + Codex + ANA MAX on 8766.', 'ai');
        vscode.postMessage({
            command: 'webviewReady',
            script: document.documentElement.dataset.anaCockpitScript,
            buttons: document.querySelectorAll('button[data-cmd], button[data-action]').length
        });
        vscode.postMessage({ command: 'smartReady' });
        liveDebug();
        setInterval(liveDebug, 5000);
    </script>
</body>
</html>`;
}

function deactivate() {
  if (voiceBridgeProcess) {
    voiceBridgeProcess.kill();
    voiceBridgeProcess = undefined;
  }
  if (voiceInboxProcess) {
    voiceInboxProcess.kill();
    voiceInboxProcess = undefined;
  }
  if (conversationAuditTailProcess) {
    conversationAuditTailProcess.kill();
    conversationAuditTailProcess = undefined;
  }
}

module.exports = { activate, deactivate };
