"""VS Code extension scaffold tests."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def extension_source_path() -> Path:
    src_path = ROOT / "vscode_extension" / "src" / "extension.js"
    if src_path.exists():
        return src_path
    return ROOT / "vscode_extension" / "extension.js"


def test_extension_commands_declared():
    """Package manifest should expose v23 commands."""
    package = json.loads((ROOT / "vscode_extension" / "package.json").read_text(encoding="utf-8"))
    commands = {item["command"] for item in package["contributes"]["commands"]}

    assert package["name"] == "ana-codex-cockpit"
    assert package["displayName"] == "ANA MAX - Codex MCP Cockpit"
    assert package["version"] == "1.0.71"
    assert package["extensionKind"][0] == "ui"
    assert "onStartupFinished" in package["activationEvents"]
    assert "onView:anaMax.actions" in package["activationEvents"]
    assert "anaMax.openLiveConsole" in commands
    assert "anaMax.codexCompanion" in commands
    assert "anaMax.codexGuard" in commands
    assert "anaMax.voiceInbox" in commands
    assert "anaMax.conversationAudit" in commands
    assert "anaMax.liveConversationAudit" in commands
    assert "anaMax.voiceOperatorSmoke" in commands
    assert package["contributes"]["configuration"]["properties"]["anaMax.goldenRulePreflight"]["default"] is True
    assert package["contributes"]["configuration"]["properties"]["anaMax.codexGuardAutoStart"]["default"] is True
    assert package["contributes"]["configuration"]["properties"]["anaMax.codexGuardMinIntervalMs"]["default"] == 60000
    assert package["contributes"]["configuration"]["properties"]["anaMax.codexGuardStrict"]["default"] is False
    assert package["contributes"]["configuration"]["properties"]["anaMax.voiceReadout"]["default"] is True
    assert package["contributes"]["configuration"]["properties"]["anaMax.voiceReadoutDirect"]["default"] is False
    assert package["contributes"]["configuration"]["properties"]["anaMax.voiceReadoutClipboard"]["default"] is True
    assert package["contributes"]["configuration"]["properties"]["anaMax.voiceReadoutLogEvents"]["default"] is True
    assert package["contributes"]["configuration"]["properties"]["anaMax.voiceFullReadout"]["default"] is True
    assert package["contributes"]["configuration"]["properties"]["anaMax.voiceFullReadoutMaxChars"]["default"] == 6000
    assert package["contributes"]["configuration"]["properties"]["anaMax.voiceFullReadoutChunkChars"]["default"] == 700
    assert package["contributes"]["configuration"]["properties"]["anaMax.voiceAccessibilityCues"]["default"] is True
    assert package["contributes"]["configuration"]["properties"]["anaMax.voiceButtonAnnouncements"]["default"] is True
    assert package["contributes"]["configuration"]["properties"]["anaMax.voiceActionCompletion"]["default"] is True
    assert package["contributes"]["configuration"]["properties"]["anaMax.voiceOrientationCues"]["default"] is True
    assert package["contributes"]["configuration"]["properties"]["anaMax.voiceOrientationMinIntervalMs"]["default"] == 20000
    assert package["contributes"]["configuration"]["properties"]["anaMax.voiceCueBeeps"]["default"] is True
    assert package["contributes"]["configuration"]["properties"]["anaMax.voiceInboxAutoStart"]["default"] is True
    assert package["contributes"]["configuration"]["properties"]["anaMax.voiceInboxAutoSubmit"]["default"] is True
    assert package["contributes"]["configuration"]["properties"]["anaMax.voiceInboxPressEnter"]["default"] is True
    assert package["contributes"]["configuration"]["properties"]["anaMax.conversationAuditLiveAutoStart"]["default"] is True
    assert package["contributes"]["configuration"]["properties"]["anaMax.autoStartRuntime"]["default"] is True
    assert "anaMax.executeTool" in commands
    assert "anaMax.inspectRuntime" in commands
    assert "anaMax.showRouterDecisions" in commands
    assert "anaMax.profileStatus" in commands
    assert "anaMax.refreshCodeMap" in commands
    assert "anaMax.showTrustScore" in commands
    assert "anaMax.generateSessionAudit" in commands
    assert "anaMax.binaryMap" in commands
    assert "anaMax.autonomyPass" in commands
    assert "anaMax.labQualityGate" in commands
    assert "anaMax.noReloadGate" in commands
    assert "anaMax.postReloadVerify" in commands
    assert "anaMax.operatorStatus" in commands
    assert "anaMax.reviewBatchPlan" in commands
    assert "anaMax.liveBehavior" in commands
    assert "anaMax.reloadReadiness" in commands
    assert "anaMax.reloadConsistency" in commands
    assert "anaMax.wakeSession" in commands
    assert "anaMax.previewRest" in commands
    assert "anaMax.showObservability" in commands


def test_extension_exposes_visible_cockpit_buttons():
    """VS Code-compatible IDEs should expose visible cockpit buttons outside the palette."""
    package = json.loads((ROOT / "vscode_extension" / "package.json").read_text(encoding="utf-8"))
    contributes = package["contributes"]

    assert contributes["viewsContainers"]["activitybar"][0]["id"] == "anaMax"
    assert contributes["views"]["anaMax"][0]["id"] == "anaMax.actions"

    visible_palette_commands = {
        item["command"]
        for item in contributes["menus"]["commandPalette"]
        if item.get("when") == "true"
    }
    hidden_palette_commands = {
        item["command"]
        for item in contributes["menus"]["commandPalette"]
        if item.get("when") == "false"
    }

    assert "anaMax.openLiveConsole" in visible_palette_commands
    assert "ana.openChat" in hidden_palette_commands
    assert "anaMax.startRuntime" in visible_palette_commands
    assert "anaMax.showHealth" in visible_palette_commands
    assert "anaMax.codexCompanion" in visible_palette_commands
    assert "anaMax.codexGuard" in visible_palette_commands
    assert "anaMax.voiceInbox" in visible_palette_commands
    assert "anaMax.conversationAudit" in visible_palette_commands
    assert "anaMax.liveConversationAudit" in visible_palette_commands
    assert "anaMax.voiceOperatorSmoke" in visible_palette_commands
    assert "anaMax.showHealthJson" in visible_palette_commands
    assert "anaMax.listTools" in visible_palette_commands
    assert "anaMax.liveDebug" in visible_palette_commands
    assert "anaMax.nucleusSmoke" in visible_palette_commands
    assert "anaMax.autonomyPass" in visible_palette_commands
    assert "anaMax.labQualityGate" in visible_palette_commands
    assert "anaMax.noReloadGate" in visible_palette_commands
    assert "anaMax.postReloadVerify" in visible_palette_commands
    assert "anaMax.operatorStatus" in visible_palette_commands
    assert "anaMax.reviewBatchPlan" in visible_palette_commands
    assert "anaMax.liveBehavior" in visible_palette_commands
    assert "anaMax.reloadReadiness" in visible_palette_commands
    assert "anaMax.reloadConsistency" in visible_palette_commands
    assert "anaMax.profileStatus" in visible_palette_commands
    assert "anaMax.refreshCodeMap" in visible_palette_commands
    assert "anaMax.showTrustScore" in visible_palette_commands
    assert "anaMax.generateSessionAudit" in visible_palette_commands
    assert "anaMax.binaryMap" in visible_palette_commands
    assert "anaMax.wakeSession" in visible_palette_commands
    assert "anaMax.checkpoint" in visible_palette_commands
    assert "anaMax.identity" in visible_palette_commands


    view_title_commands = {
        item["command"]
        for item in contributes["menus"]["view/title"]
        if item.get("when") == "view == anaMax.actions"
    }
    assert "anaMax.openLiveConsole" in view_title_commands
    assert "ana.openChat" not in view_title_commands
    assert "anaMax.startRuntime" in view_title_commands
    assert "anaMax.showHealth" in view_title_commands


def test_extension_safe_mode_ui_enforcement_present():
    """Extension source should keep safe-mode checks around tool execution."""
    source = extension_source_path().read_text(encoding="utf-8")

    assert "safeMode" in source
    assert "blocks tool execution" in source
    assert "requestJson" in source
    assert "Start MCP Server" in source
    assert "Live Debug" in source
    assert "liveDebug" in source
    assert "Codex Companion" in source
    assert "codexCompanion" in source
    assert "Codex Guard" in source
    assert "codexGuard" in source
    assert "[ANA-GUARD]" in source
    assert "runCodexGuard" in source
    assert "Voice Inbox" in source
    assert "voiceInbox" in source
    assert "Conversation Audit" in source
    assert "conversationAudit" in source
    assert "Live Conversation Audit" in source
    assert "liveConversationAudit" in source
    assert "Voice Operator Smoke" in source
    assert "voiceOperatorSmoke" in source
    assert "ana_conversation_audit.py" in source
    assert "ana_conversation_audit_tail.py" in source
    assert "ana_voice_operator_smoke.py" in source
    assert "[CONVERSATION-AUDIT]" in source
    assert "[CONVERSATION-LIVE]" in source
    assert "[VOICE-OPERATOR]" in source
    assert "autoStartRuntime" in source
    assert "[AUTO-START]" in source
    assert "Nucleus Smoke" in source
    assert "nucleusSmoke" in source
    assert "Autonomy Pass" in source
    assert "autonomyPass" in source
    assert "Lab Quality Gate" in source
    assert "labQualityGate" in source
    assert "No-Reload Gate" in source
    assert "noReloadGate" in source
    assert "Post-Reload Verify" in source
    assert "postReloadVerify" in source
    assert "Operator Status" in source
    assert "operatorStatus" in source
    assert "Review Batch Plan" in source
    assert "reviewBatchPlan" in source
    assert "Live Behavior" in source
    assert "liveBehavior" in source
    assert "Reload Readiness" in source
    assert "reloadReadiness" in source
    assert "Reload Consistency" in source
    assert "reloadConsistency" in source
    assert "Beginner Flow" in source
    assert "Start here" in source
    assert "Daily work" in source
    assert "Rest Preview" in source
    assert "registerTreeDataProvider" in source
    assert "AnaActionProvider" in source
    assert "Refresh Context Maps" in source
    assert "Trust Score" in source
    assert "Session Audit" in source
    assert "[AUDIT]" in source
    assert "Binary Map" in source
    assert "Profile Status" in source
    assert "Health JSON" in source
    assert "List Tools" in source
    assert "Checkpoint" in source
    assert "Identity" in source
    assert "ana_local_checkpoint.py" in source
    assert "[LOCAL-CHECKPOINT]" in source


def test_extension_nucleus_smoke_command_runs_script():
    """Activity Bar should expose one-button nucleus smoke checks."""
    source = extension_source_path().read_text(encoding="utf-8")
    package = json.loads((ROOT / "vscode_extension" / "package.json").read_text(encoding="utf-8"))
    commands = {item["command"] for item in package["contributes"]["commands"]}

    assert "anaMax.nucleusSmoke" in commands
    assert "ana_nucleus_smoke.py" in source
    assert "[NUCLEUS]" in source
    assert "ANA MAX: Running Nucleus Smoke" in source


def test_extension_codex_companion_command_runs_script():
    """Activity Bar should expose ANA's Codex companion challenge loop."""
    source = extension_source_path().read_text(encoding="utf-8")
    package = json.loads((ROOT / "vscode_extension" / "package.json").read_text(encoding="utf-8"))
    commands = {item["command"] for item in package["contributes"]["commands"]}

    assert "anaMax.codexCompanion" in commands
    assert "ana_codex_companion.py" in source
    assert "[CODEX-COMPANION]" in source
    assert "[GOLDEN-RULE]" in source
    assert "goldenRulePreflight" in source
    assert "ANA MAX: Codex Companion" in source
    assert "challenge blind work" in source


def test_extension_codex_guard_auto_start_is_audible():
    """Codex Guard should make ANA-first work visible and audible after startup."""
    source = extension_source_path().read_text(encoding="utf-8")
    package = json.loads((ROOT / "vscode_extension" / "package.json").read_text(encoding="utf-8"))
    properties = package["contributes"]["configuration"]["properties"]

    assert properties["anaMax.codexGuardAutoStart"]["default"] is True
    assert "runCodexGuard(\"Post-start guard" in source
    assert "ANA guard checking Codex" in source
    assert "ANA guard ready" in source
    assert "ANA guard warning" in source
    assert "ANA guard failed" in source


def test_extension_activity_commands_have_voice_and_golden_rule_coverage():
    """Activity Bar commands should be audible and ANA-first by default."""
    source = extension_source_path().read_text(encoding="utf-8")

    assert "function goldenRuleGoalForCommand" in source
    assert "onDidExecuteCommand" in source
    assert "announceCommand(command)" in source
    assert "speakAccessibility(label, \"start\"" in source
    assert "speakAccessibility(label, \"success\"" in source
    assert "speakAccessibility(label, \"fail\"" in source

    run_with_golden = [
        "Smart Ready",
        "Health JSON",
        "List Tools",
        "Live Debug",
        "Nucleus Smoke",
        "Post-Reload Verify",
        "Operator Status",
        "Live Behavior",
        "Reload Readiness",
        "Reload Consistency",
        "Recommend",
        "Profile Status",
        "Rest Preview",
        "Trust Score",
        "Conversation Audit",
        "Voice Operator Smoke",
        "Identity",
        "Inspect Runtime",
    ]
    for label in run_with_golden:
        assert f'runWithGoldenRule("{label}"' in source

    explicit_preflight = [
        "Voice Inbox",
        "Autonomy Pass",
        "Lab Quality Gate",
        "No-Reload Gate",
        "Review Batch Plan",
        "Wake Session",
        "Checkpoint",
        "Save REM",
        "Refresh Context Maps",
        "Session Audit",
        "Binary Map",
        "Open Dashboard",
        "Call MCP Tool",
    ]
    for label in explicit_preflight:
        assert f'ensureGoldenRulePreflight("{label}"' in source

    # Bootstrap/ANA-maintenance commands intentionally avoid preflight loops but
    # remain audible through command announcements and direct speech cues.
    assert 'registerCommand("anaMax.openLiveConsole"' in source
    assert 'registerCommand("anaMax.startRuntime"' in source
    assert 'registerCommand("anaMax.codexGuard"' in source
    assert 'registerCommand("anaMax.liveConversationAudit"' in source


def test_extension_voice_readout_uses_filtered_chat_bridge():
    """Live Console voice should use the existing low-noise ANA chat bridge."""
    source = extension_source_path().read_text(encoding="utf-8")
    package = json.loads((ROOT / "vscode_extension" / "package.json").read_text(encoding="utf-8"))
    properties = package["contributes"]["configuration"]["properties"]

    assert properties["anaMax.voiceReadout"]["default"] is True
    assert "chat_voice_bridge.py" in source
    assert "voice_queue.txt" in source
    assert "voiceReadoutClipboard" in source
    assert "voiceReadoutLogEvents" in source
    assert "voiceFullReadout" in source
    assert "--full-readout" in source
    assert "--full-max-chars" in source
    assert "--chunk-chars" in source
    assert "CONVERSATION-AUDIT" in source
    assert "CONVERSATION-LIVE" in source
    assert "voiceAccessibilityCues" in source
    assert "voiceButtonAnnouncements" in source
    assert "voiceOrientationCues" in source
    assert "mirrorOrientationSummary" in source
    assert "Screen ${app}" in source
    assert "playAccessibilityBeep" in source
    assert "speakAccessibility" in source
    assert "onDidExecuteCommand" in source
    assert "Voice phrase submitted" in source
    assert "TOOL START name=" in source
    assert "TOOL END name=" in source
    assert "Watchdog health online" in source
    assert "clipboard=" in source
    assert "--no-clipboard" in source
    assert "speakDirectVoice" in source
    assert "System.Speech" in source
    assert "queueImportantVoice" in source
    assert "voiceTextFromLogLine" in source
    assert "\\b[a-z]:\\\\users\\\\[^\"'\\s]+" in source
    assert "ANA preflight ${match[1]}" in source
    assert "Live behavior ${match[1]}" in source
    assert "Nucleus ${match[1]}" in source
    assert "Operator status. VSIX" in source
    assert "Reload readiness. Reload needed" in source
    assert "Reload consistency ${match[1]}" in source
    assert "Post reload ${match[1]}" in source
    assert "Conversation audit ${match[1]}" in source
    assert "screenshots\\\\view_" in source
    assert "ANA challenge" in source
    assert "[AUDIT]" in source


def test_extension_voice_inbox_command_runs_script():
    """Activity Bar should expose microphone dictation and the auto-start daemon for Codex."""
    source = extension_source_path().read_text(encoding="utf-8")
    package = json.loads((ROOT / "vscode_extension" / "package.json").read_text(encoding="utf-8"))
    commands = {item["command"] for item in package["contributes"]["commands"]}
    properties = package["contributes"]["configuration"]["properties"]

    assert "anaMax.voiceInbox" in commands
    assert "ana_voice_inbox.py" in source
    assert "[VOICE-INBOX]" in source
    assert "--copy" in source
    assert "startVoiceInboxDaemon" in source
    assert "--continuous" in source
    assert "--auto-submit" in source
    assert "--press-enter" in source
    assert "voiceInboxAutoStart" in source
    assert properties["anaMax.voiceInboxSubmitPrefix"]["default"] == "codex,ana"
    assert "Visual Studio Code" in properties["anaMax.voiceInboxAllowedTitles"]["default"]


def test_extension_autonomy_pass_command_runs_script():
    """Activity Bar should expose the lab-safe autonomy pass."""
    source = extension_source_path().read_text(encoding="utf-8")
    package = json.loads((ROOT / "vscode_extension" / "package.json").read_text(encoding="utf-8"))
    commands = {item["command"] for item in package["contributes"]["commands"]}

    assert "anaMax.autonomyPass" in commands
    assert "ana_autonomy_runner.py" in source
    assert "[AUTONOMY]" in source
    assert "ANA MAX: Running Autonomy Pass" in source
    assert "--checkpoint" in source


def test_extension_lab_quality_gate_command_runs_script():
    """Activity Bar should expose the full local lab quality gate."""
    source = extension_source_path().read_text(encoding="utf-8")
    package = json.loads((ROOT / "vscode_extension" / "package.json").read_text(encoding="utf-8"))
    commands = {item["command"] for item in package["contributes"]["commands"]}

    assert "anaMax.labQualityGate" in commands
    assert "lab_quality_gate.py" in source
    assert "[QUALITY]" in source
    assert "ANA MAX: Running Lab Quality Gate" in source
    assert 'data-action="labQualityGate"' not in source


def test_extension_no_reload_gate_command_runs_script():
    """Activity Bar should expose packaging validation without IDE reload."""
    source = extension_source_path().read_text(encoding="utf-8")
    package = json.loads((ROOT / "vscode_extension" / "package.json").read_text(encoding="utf-8"))
    commands = {item["command"] for item in package["contributes"]["commands"]}

    assert "anaMax.noReloadGate" in commands
    assert "no_reload_quality_gate.py" in source
    assert "[NO-RELOAD]" in source
    assert "ANA MAX: Running No-Reload Gate" in source
    assert 'data-action="noReloadGate"' not in source


def test_extension_post_reload_verify_command_runs_script():
    """Activity Bar should expose post-reload verification without writing reports."""
    source = extension_source_path().read_text(encoding="utf-8")
    package = json.loads((ROOT / "vscode_extension" / "package.json").read_text(encoding="utf-8"))
    commands = {item["command"] for item in package["contributes"]["commands"]}

    assert "anaMax.postReloadVerify" in commands
    assert "ana_post_reload_verify.py" in source
    assert "[POST-RELOAD]" in source
    assert "ANA MAX: Running Post-Reload Verify" in source
    assert "--no-write" in source


def test_extension_operator_status_command_runs_script():
    """Activity Bar should expose compact operator status."""
    source = extension_source_path().read_text(encoding="utf-8")
    package = json.loads((ROOT / "vscode_extension" / "package.json").read_text(encoding="utf-8"))
    commands = {item["command"] for item in package["contributes"]["commands"]}

    assert "anaMax.operatorStatus" in commands
    assert "ana_operator_status.py" in source
    assert "[OPERATOR-STATUS]" in source
    assert "ANA MAX: Operator Status" in source


def test_extension_review_batch_plan_command_runs_script_without_execution():
    """Activity Bar should expose dry-run review-batch planning only."""
    source = extension_source_path().read_text(encoding="utf-8")
    package = json.loads((ROOT / "vscode_extension" / "package.json").read_text(encoding="utf-8"))
    commands = {item["command"] for item in package["contributes"]["commands"]}

    assert "anaMax.reviewBatchPlan" in commands
    assert "ana_review_batch_runner.py" in source
    assert "[REVIEW-BATCH]" in source
    assert "ANA MAX: Review Batch Plan" in source
    assert "--all-batches" in source
    assert "--no-write" in source
    assert '"--run"' not in source


def test_extension_live_behavior_command_runs_script():
    """Activity Bar should expose live behavior freshness checks."""
    source = extension_source_path().read_text(encoding="utf-8")
    package = json.loads((ROOT / "vscode_extension" / "package.json").read_text(encoding="utf-8"))
    commands = {item["command"] for item in package["contributes"]["commands"]}

    assert "anaMax.liveBehavior" in commands
    assert "ana_live_behavior_check.py" in source
    assert "[LIVE-BEHAVIOR]" in source
    assert "ANA MAX: Live Behavior" in source


def test_extension_reload_readiness_command_runs_script():
    """Activity Bar should expose the reload decision check."""
    source = extension_source_path().read_text(encoding="utf-8")
    package = json.loads((ROOT / "vscode_extension" / "package.json").read_text(encoding="utf-8"))
    commands = {item["command"] for item in package["contributes"]["commands"]}

    assert "anaMax.reloadReadiness" in commands
    assert "ana_reload_readiness.py" in source
    assert "[RELOAD-READINESS]" in source
    assert "ANA MAX: Reload Readiness" in source
    assert "--no-write" in source


def test_extension_reload_consistency_command_runs_script():
    """Activity Bar should expose reload diagnostic agreement checks."""
    source = extension_source_path().read_text(encoding="utf-8")
    package = json.loads((ROOT / "vscode_extension" / "package.json").read_text(encoding="utf-8"))
    commands = {item["command"] for item in package["contributes"]["commands"]}

    assert "anaMax.reloadConsistency" in commands
    assert "ana_reload_consistency_check.py" in source
    assert "[RELOAD-CONSISTENCY]" in source
    assert "ANA MAX: Reload Consistency" in source
    assert "--no-write" in source


def test_extension_confirmation_dialogs_present():
    """Extension should include explicit dangerous-action confirmations."""
    source = extension_source_path().read_text(encoding="utf-8")

    assert "Allow write?" in source
    assert "Allow subprocess?" in source
    assert "Allow network call?" in source
    assert "Allow tool execution?" not in source
    assert "confirmDangerousAction" in source
    assert "readOnlyTools" in source
    assert '"tool_router"' in source
    assert '"agent_coach"' in source
    assert '"session_lifecycle"' in source


def test_extension_uses_lifecycle_for_wake_and_rest():
    """Cockpit should use session_lifecycle for wake/rest flows."""
    source = extension_source_path().read_text(encoding="utf-8")

    assert "session_lifecycle" in source
    assert 'action: "wake"' in source
    assert 'consolidate: false' in source
    assert 'consolidate: true' in source


def test_extension_checkpoint_uses_local_source_fallback():
    """Checkpoint should not depend on stale live MCP session_checkpoint code."""
    source = extension_source_path().read_text(encoding="utf-8")

    assert "async function runLocalCheckpoint" in source
    assert "ana_local_checkpoint.py" in source
    assert 'registerCommand("anaMax.checkpoint"' in source
    assert 'callTool(config, "session_checkpoint"' not in source


def test_extension_start_runtime_handles_missing_main():
    """Start runtime should report failure if main.py is missing."""
    source = extension_source_path().read_text(encoding="utf-8")
    assert "ANA MAX main.py not found" in source


def test_extension_start_runtime_waits_for_health_and_prefers_workspace_venv():
    """Start runtime should use the mother workspace venv and wait for /health."""
    source = extension_source_path().read_text(encoding="utf-8")

    assert "workspaceVenvPython" in source
    assert "waitForRuntimeHealth" in source
    assert "Runtime spawned but health did not become ready" in source
    assert "ANA MAX MCP ready" in source


def test_extension_implements_live_log_buffer():
    """Extension must have a bounded log buffer and an OutputChannel for v1.0.23."""
    source = extension_source_path().read_text(encoding="utf-8")

    assert "let logBuffer = [];" in source
    assert 'vscode.window.createOutputChannel("ANA MAX MCP")' in source
    assert 'post(panel, "runtimeLog"' in source
    assert "function appendLiveLog(message)" in source
    assert "[LIVE] status=" in source
    assert "[TOOL start]" in source
    assert 'runtimeProcess = cp.spawn' in source
    assert "showLiveConsole();" in source


def test_extension_live_log_follows_latest_without_fighting_reader():
    """Live log should auto-follow bottom while allowing manual scrollback."""
    source = extension_source_path().read_text(encoding="utf-8")

    assert "logPinnedToBottom" in source
    assert "following latest" in source
    assert "paused while reading" in source
    assert "scrollLiveLogToBottom" in source
    assert "liveLog.addEventListener('scroll'" in source


def test_extension_reports_webview_button_bridge_health():
    """Cockpit should report webview script readiness and button bridge failures."""
    source = extension_source_path().read_text(encoding="utf-8")

    assert "webviewReady" in source
    assert "webviewError" in source
    assert "Cockpit button error" in source
    assert "document.addEventListener('click'" in source
    assert "button[data-cmd], button[data-action]" in source


def test_extension_refresh_code_map_command_runs_python_script():
    """Activity Bar should expose the deterministic context maps refresh."""
    source = extension_source_path().read_text(encoding="utf-8")

    assert "anaMax.refreshCodeMap" in source
    assert "ana_refresh_context_maps.py" in source
    assert "[CONTEXT-MAPS]" in source
    assert "Refresh Code Map and Graph Map" in source


def test_extension_exposes_lab_audit_and_binary_commands():
    """Cockpit should expose lab trust, audit, and static binary helpers."""
    source = extension_source_path().read_text(encoding="utf-8")

    assert "anaMax.showTrustScore" in source
    assert "anaMax.generateSessionAudit" in source
    assert "anaMax.conversationAudit" in source
    assert "anaMax.liveConversationAudit" in source
    assert "anaMax.binaryMap" in source
    assert '"session_audit"' in source
    assert "ana_conversation_audit.py" in source
    assert "ana_conversation_audit_tail.py" in source
    assert '"binary_map"' in source
    assert "trustScore" in source
    assert "sessionAudit" in source
    assert "conversationAudit" in source
    assert "liveConversationAudit" in source
    assert "binaryMap" in source


def test_extension_cockpit_layout_order():
    """Live Log must be above Chat for visibility in v1.0.23."""
    source = extension_source_path().read_text(encoding="utf-8")

    log_pos = source.find('id="live-log"')
    chat_pos = source.find('id="chat"')

    assert log_pos != -1
    assert chat_pos != -1
    assert log_pos < chat_pos, "Live Log should be defined before Chat in HTML for layout order"
    assert 'Waiting for runtime output...' in source


def test_extension_avoids_global_fetch_for_older_hosts():
    """The ^1.75.0 engine target should not depend on extension-host global fetch."""
    source = extension_source_path().read_text(encoding="utf-8")

    assert '"vscode": "^1.75.0"' in (ROOT / "vscode_extension" / "package.json").read_text(encoding="utf-8")
    assert "function requestGetJson(url)" in source
    assert "await fetch(" not in source


def test_extension_prefers_local_ui_host_for_remote_desktop_control():
    """Remote/WSL windows should prefer local UI extension host for Windows desktop tools."""
    package = json.loads((ROOT / "vscode_extension" / "package.json").read_text(encoding="utf-8"))
    source = extension_source_path().read_text(encoding="utf-8")

    assert package["extensionKind"][:2] == ["ui", "workspace"]
    assert "vscode.env.remoteName" in source
    assert "remoteRuntimeHint" in source
    assert "ANA_MAX_RUNTIME_ROOT" in source
    assert "Remote/WSL/SSH windows" in json.dumps(package)


def test_extension_sanitizes_cockpit_carriage_returns():
    """Cockpit output should strip carriage returns from logs/tool responses."""
    source = extension_source_path().read_text(encoding="utf-8")

    assert "Sanitize carriage returns" in source
    assert ".replace(/\\r/g, '')" in source


def test_extension_does_not_shadow_call_tool_helper():
    """Command disposable names must not shadow the callTool helper used by buttons."""
    source = extension_source_path().read_text(encoding="utf-8")

    assert "async function callTool(config, name, args)" in source
    assert "const callTool = vscode.commands.registerCommand" not in source
    # v1.0.17 used callToolCommand; v1.0.19 uses callToolExternal to be safe
    assert "const callToolExternal = vscode.commands.registerCommand" in source
    assert "context.subscriptions.push(openCockpit, callToolExternal)" in source


def test_extension_exposes_activity_bar_and_cockpit():
    """Extension should expose both the single cockpit and the Activity Bar for VS Code stability."""
    package_path = ROOT / "vscode_extension" / "package.json"
    package = json.loads(package_path.read_text(encoding="utf-8"))
    contributes = package["contributes"]

    # Verify Activity Bar in package.json
    assert "anaMax" in contributes["viewsContainers"]["activitybar"][0]["id"]
    assert "anaMax.actions" in contributes["views"]["anaMax"][0]["id"]

    # Verify registration in extension.js
    source = extension_source_path().read_text(encoding="utf-8")
    assert "registerTreeDataProvider(\"anaMax.actions\"" in source
    assert "async function runInCockpit" in source
    assert "openLiveConsole" in source
    assert "startLiveConsoleHeartbeat" in source
    assert "startMirrorWatch" in source
    assert "ana_mirror_watch.py" in source
    assert "tail_mcp_log.ps1" in source
    # Ensure guided commands in extension use runInCockpit, not openTextDocument directly
    assert 'runInCockpit("smartReady"' in source
    assert 'runInCockpit("recommend"' in source
    assert "anaMax.profileStatus" in source
    assert "anaMax.reviewBatchPlan" in source
    assert 'runInCockpit("lifecycle"' in source


def test_extension_exposes_profile_status_in_activity_bar_only():
    """Profile status should use stable Activity Bar commands, not cockpit buttons."""
    source = extension_source_path().read_text(encoding="utf-8")
    package = json.loads((ROOT / "vscode_extension" / "package.json").read_text(encoding="utf-8"))
    commands = {item["command"] for item in package["contributes"]["commands"]}

    assert "anaMax.profileStatus" in commands
    assert 'actionItem("Profile Status", "anaMax.profileStatus"' in source
    assert 'callTool(config, "tool_router", { mode: "profile_status" })' in source
    assert "ana_permission_manifest_coverage.py" in source
    assert "MCP profile_status unavailable" in source
    assert 'data-action="profileStatus"' not in source


def test_extension_dashboard_generates_local_html():
    """Dashboard command should not depend on the legacy 8787 web server."""
    source = extension_source_path().read_text(encoding="utf-8")

    assert "function writeLocalDashboard" in source
    assert "ana-max-dashboard" in source
    assert "dashboard.html" in source
    assert "dashboard-list-tools" in source
    assert 'callTool(config, "tool_healthcheck", { scope: "safe" })' in source
    assert "function openLocalFile" in source
    assert "preferredBrowserPath" in source
    assert "C:\\\\Program Files\\\\Google\\\\Chrome\\\\Application\\\\chrome.exe" in source
    assert "vscode.Uri.file(filePath)" in source


def test_extension_codex_only_wording():
    """Cockpit should be packaged for VS Code/Codex without non-Codex client positioning."""
    package = json.loads((ROOT / "vscode_extension" / "package.json").read_text(encoding="utf-8"))
    source = extension_source_path().read_text(encoding="utf-8")
    package_text = json.dumps(package).lower()

    assert "anaMax.compatibleClientServerName" not in package["contributes"]["configuration"]["properties"]
    assert "anaMax.antigravityServerName" not in package["contributes"]["configuration"]["properties"]
    assert "ana.showCodexMcpConfig" in {item["command"] for item in package["contributes"]["commands"]}
    assert "qoder" not in package_text
    assert "windsurf" not in package_text
    assert "antigravity" not in package_text
    assert "adal" not in package_text
    assert "Primary path: VS Code + Codex + ANA MAX" in source
    assert "ANA MAX MCP Config" in source
    assert "compatible-client" not in source
    assert "hybrid build" not in source
    assert "antigravity" not in source.lower()
    assert "qoder" not in source.lower()
    assert "windsurf" not in source.lower()
    assert "adal" not in source.lower()


def test_extension_webview_uses_nonce_and_bound_buttons():
    """Cockpit buttons should be bound by script listeners, not inline handlers."""
    source = extension_source_path().read_text(encoding="utf-8")

    assert "Local lab build: keep scripts unblocked" in source
    assert "getWebviewContent(panel.webview)" in source
    assert "function getWebviewContent(webview)" in source
    assert "webview?.cspSource" in source
    assert "document.documentElement.dataset.anaCockpitScript = 'running';" in source
    assert "const m = e.data || {};" in source
    assert '<script nonce="${nonce}">' in source
    assert "data-cmd=\"smartReady\"" in source
    assert "data-action=\"liveDebug\"" in source
    assert "document.addEventListener('click'" in source
    assert "button[data-cmd], button[data-action]" in source
    assert "onclick=" not in source
