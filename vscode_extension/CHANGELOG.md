# Changelog

## 1.0.71 - Voice And Golden Rule Coverage

- Route more Activity Bar status/diagnostic/audit commands through
  `runWithGoldenRule` so ANA observes before the operator/Codex acts.
- Keep bootstrap controls such as Live Console, Start MCP Server, and Codex
  Guard available without preflight loops, while still speaking their cues.
- Preserve command voice coverage through `onDidExecuteCommand`,
  `speakAccessibility`, action start/end speech, and conversation audit.

## 1.0.70 - Bug Bounty Voice Polish

- Redact Windows user paths case-insensitively before spoken Live Console text
  enters the voice queue.
- Redact Windows user paths inside conversation audit entries and compact
  metadata, even when text reaches the queue outside the extension sanitizer.
- Summarize noisy Golden Rule, Live Behavior, Nucleus, Operator Status, reload,
  post-reload, and conversation audit lines before speaking them.

## 1.0.69 - Voice Operator Smoke

- Add `ANA MAX: Voice Operator Smoke` to the Activity Bar and command palette.
- Run `ana_voice_operator_smoke.py` from the Live Console path to verify the
  voice queue -> chat bridge -> conversation audit pipeline.
- Mark the command as audio-interactive in Activity Bar smoke tests so normal
  button checks verify registration without unexpectedly speaking.

## 1.0.68 - Single Voice Channel

- Make the voice queue bridge the default ANA voice channel.
- Disable direct System.Speech readout by default to avoid duplicate or triple
  voices during live operator mode.
- Keep direct voice available as fallback/manual test, but do not speak the
  same Live Console text through queue and direct voice when queue write
  succeeds.

## 1.0.67 - Full Voice Readout

- Add full voice readout mode for ANA queue and copied-chat text.
- Start `chat_voice_bridge.py` with `--full-readout` so long text is spoken in
  chunks instead of skipped or truncated.
- Keep secret-word filtering active while allowing longer operator/Codex
  messages to be heard end to end.

## 1.0.66 - Live Conversation Audit

- Add `ANA MAX: Live Conversation Audit` and auto-start a real-time
  conversation-audit tail when the Live Console opens.
- Stream new Voice Inbox, copied-chat, voice-queue, and bridge-status evidence
  into the `ANA MAX MCP` output as `[CONVERSATION-LIVE]` lines.
- Keep `[CONVERSATION-LIVE]` visual-only to avoid audio feedback loops while
  the existing voice filters continue speaking high-signal ANA events.

## 1.0.65 - Conversation Voice Audit

- Add `ANA MAX: Conversation Audit` to show recent voice, clipboard, and spoken
  queue evidence from the private lab.
- Record compact local conversation audit entries when Chat Voice Bridge speaks
  copied chat text or voice queue lines.
- Record Voice Inbox dictation evidence into the same conversation audit file,
  while skipping sensitive text and avoiding raw audio.

## 1.0.64 - Audible Codex Guard

- Add `ANA MAX: Codex Guard` as a manual Activity Bar/command-palette action.
- Run an automatic post-start ANA Guard check after MCP readiness so Billy hears
  whether ANA has challenged Codex before meaningful lab work.
- Add `[ANA-GUARD]` Live Console markers plus spoken `ready`, `warning`, and
  `failed` cues. This makes the ANA-first rule visible and audible instead of
  only implied by Codex behavior.

## 1.0.63 - Accessibility Audio Cues

- Add private-lab accessibility cues for Activity Bar buttons, action
  start/end, server readiness, failures, and Voice Inbox phrase completion.
- Speak deduplicated orientation cues from mirror/watchdog logs so Billy can
  hear the active app/window context without hearing screenshot spam.
- Add short beep cues for button/start/success/fail/ready/phrase events, with
  settings to disable cues or beeps independently.
- Convert Voice Inbox JSON output into useful spoken summaries such as
  `Voice phrase captured` and `Voice phrase submitted`.

## 1.0.62 - Spoken Live Log Events

- Add `anaMax.voiceReadoutLogEvents`, enabled by default in the lab build.
- Speak useful Live Console log events including MCP tool call start/end,
  `TOOL START/END`, watchdog health, coach warnings, failures, audit, reload,
  and voice-inbox status.
- Keep noisy mirror, heartbeat, screenshot, and raw UI event lines filtered so
  spoken logs help the operator instead of flooding them.

## 1.0.61 - Startup Activation For Voice Inbox

- Add explicit `onStartupFinished` and `onView:anaMax.actions` activation
  events so the extension actually wakes after VS Code reload.
- Keep the automatic Voice Inbox daemon tied to the startup Live Console path
  and write `voice_inbox_status.txt` when daemon spawn is requested or stopped.

## 1.0.60 - Automatic Voice Inbox Daemon

- Start the private-lab microphone Voice Inbox daemon automatically when the
  ANA Live Console opens.
- Auto-submit recognized speech only when it starts with an allowed prefix such
  as `codex` or `ana`, and only into allowed foreground windows.
- Keep one-shot `ANA MAX: Voice Inbox` available, while the reload path now
  supports hands-free Codex prompts when the chat input is focused.

## 1.0.59 - Clipboard Chat Voice

- Start the chat voice bridge with clipboard monitoring enabled by default for
  the private lab.
- Let Billy copy real Codex/ChatGPT text and hear it immediately, while keeping
  Live Console filtered voice and direct System.Speech fallback.
- Keep `anaMax.voiceReadoutClipboard` configurable so clipboard speech can be
  disabled when privacy/noise matters.

## 1.0.58 - Direct Voice Fallback

- Add `anaMax.voiceReadoutDirect` so filtered Live Console lines are also
  spoken directly through Windows System.Speech.
- Keep `voice_queue.txt` as backup, but do not depend on the queue bridge alone
  for audit and next-action speech.
- Use a temp-file based PowerShell call to avoid command-line quoting issues.

## 1.0.57 - Spoken Audit Summary

- Make `Trust Score` and `Session Audit` write short `[AUDIT]` Live Console
  summaries with trust score, identity/status, and run id.
- Include `[AUDIT]` lines in the filtered Voice Readout path so Billy hears the
  useful audit verdict instead of raw JSON noise.

## 1.0.56 - Auto Start And Voice Inbox

- Start the stable lab surface automatically on extension activation:
  Live Console, voice bridge, and ANA MCP runtime attach/start.
- Add `ANA MAX: Voice Inbox` as a one-shot microphone dictation bridge for
  Codex: listen, transcribe through local Windows speech, save compact text,
  and copy it to the clipboard.
- Keep Voice Inbox behind Golden Rule preflight and mark it interactive in the
  Activity Bar smoke test.

## 1.0.55 - Golden Rule Voice Readout

- Add `anaMax.goldenRulePreflight` so high-impact Activity Bar actions run the
  ANA Codex Companion preflight before continuing.
- Add `anaMax.voiceReadout`, backed by `chat_voice_bridge.py`, so important
  Live Console decisions can be spoken automatically.
- Filter speech to useful operator lines only: ANA challenges, Codex next
  steps, PASS/WARN/FAIL verdicts, and high-impact command summaries.

## 1.0.53 - Codex Companion

- Add `ANA MAX: Codex Companion` to the Activity Bar and command palette.
- Run `ana_codex_companion.py` from the Live Console path so ANA observes,
  routes, coaches, context-packs, and challenges Codex before scoped work.
- Keep the flow report-oriented: ANA can warn about blind/repeated work and
  Codex must verify before another action.

## 1.0.52 - Context Maps Refresh

- Make the Activity Bar refresh command run `ana_refresh_context_maps.py --json`.
- Refresh Code Map and Graph Map together, then surface the compact freshness
  verdict in the Live Console.
- Keep the existing `anaMax.refreshCodeMap` command id as a stable alias for
  older operator flows.

## 1.0.51 - Review Batch All-Batches Plan

- Make `ANA MAX: Review Batch Plan` call
  `ana_review_batch_runner.py --all-batches --no-write`.
- Show the planned verification commands for all active Dirty Tree review
  batches without executing them.
- Keep execution explicit through terminal-only `--category ... --run`.

## 1.0.50 - Review Batch Plan

- Add `ANA MAX: Review Batch Plan` to the Activity Bar and command palette.
- Run `ana_review_batch_runner.py --no-write` from the Live Console path.
- Preview the first Dirty Tree review-batch verification command without
  executing tests, installing VSIX files, or reloading the IDE.

## 1.0.49 - Reload Consistency

- Add `ANA MAX: Reload Consistency` to the Activity Bar and command palette.
- Run `ana_reload_consistency_check.py --no-write` from the Live Console path.
- Surface whether Reload Readiness, Operator Status, Lab State, and
  Post-Reload Verify agree before action work.

## 1.0.48 - Reload Readiness

- Add `ANA MAX: Reload Readiness` to the Activity Bar and command palette.
- Run `ana_reload_readiness.py --no-write` from the Live Console path.
- Show whether VS Code reload or MCP restart is useful based on reload marker,
  live tool-surface drift, and live behavior freshness.

## 1.0.47 - Live Behavior

- Add `ANA MAX: Live Behavior` to the Activity Bar and command palette.
- Run `ana_live_behavior_check.py` from the Live Console path.
- Surface healthy-but-stale MCP behavior when live tools have not loaded
  disk-side changes yet.

## 1.0.46 - Operator Status

- Add `ANA MAX: Operator Status` to the Activity Bar and command palette.
- Run `ana_operator_status.py` from the Live Console path.
- Show current VSIX version, MCP readiness, reload marker, checkpoint, and next
  install/verify commands without mutating state.

## 1.0.45 - Local Checkpoint Fallback

- Route the Activity Bar `Checkpoint` command through `ana_local_checkpoint.py`
  instead of live MCP `session_checkpoint`.
- Keep checkpoint saves safe while the live MCP server is stale and has not
  loaded the latest handoff-note preservation behavior.
- Log local checkpoint activity under `[LOCAL-CHECKPOINT]`.

## 1.0.44 - Post-Reload Verify

- Add `ANA MAX: Post-Reload Verify` to the Activity Bar and command palette.
- Run `ana_post_reload_verify.py --no-write` from the stable Live Console path.
- Verify the live reload marker, Nucleus Smoke, and compact lab state after an
  operator MCP restart/reload.
- Package lab VSIX artifacts for manual install; no marketplace publish implied.

## 1.0.43 - No-Reload Gate

- Add `ANA MAX: No-Reload Gate` to the Activity Bar and command palette.
- Run `no_reload_quality_gate.py` from the stable Live Console path without
  installing the VSIX or reloading the IDE.
- Keep the control out of the fragile Cockpit webview.

## 1.0.42 - Activity Bar Policy Controls

- Add `ANA MAX: Profile Status` to the Activity Bar and command palette.
- Add `ANA MAX: Lab Quality Gate` to run the full local lab gate from the
  stable left-side control surface.
- Keep these controls out of the fragile Cockpit webview; they use the Live
  Console/Activity Bar path only.
- Profile Status falls back to local permission-manifest coverage when the live
  MCP server has not yet picked up the newest router code.

## 1.0.41 - Autonomy Pass

- Add `ANA MAX: Autonomy Pass` to the Activity Bar.
- Run a lab-safe observe, route, context-pack, verify, audit, and checkpoint
  pass without invoking deep instrumentation or arbitrary tools.
- Stream compact status lines into the Live Console and write a JSON report
  under `ANA_MAX/dev_artifacts/reports/`.

## 1.0.40 - Nucleus Smoke

- Add `ANA MAX: Nucleus Smoke` to the Activity Bar.
- Run the live MCP nucleus chain: health, tools/list, router, coach,
  code context, graph context, tool healthcheck, error radar, and trust score.
- Write a compact JSON report under `ANA_MAX/dev_artifacts/reports/`.

## 1.0.39 - Local Dashboard Fallback

- Fix `Open Dashboard` opening a blank page when no legacy dashboard server is
  listening on port 8787.
- Generate a local HTML dashboard from live MCP health, tools/list, and
  `tool_healthcheck` data, then open that file in the browser.

## 1.0.38 - Activity Bar Control Surface

- Disable the Cockpit webview as a primary operator surface in the lab build.
- Promote missing Cockpit actions into the ANA MAX Activity Bar: Health JSON,
  List Tools, Live Debug, Checkpoint, Identity, and existing audit/code-map
  actions.
- Start/runtime actions now prefer the text Live Console instead of opening the
  webview automatically.

## 1.0.37 - Cockpit Button Bridge Diagnostics

- Add a webview-ready handshake so the ANA MAX MCP output confirms the cockpit
  script loaded and counted the visible buttons.
- Route toolbar clicks through one guarded dispatcher and report webview
  JavaScript errors back to the live MCP output.
- Keep Activity Bar commands unchanged; this patch targets selective cockpit
  button failures after reload/install.

## 1.0.27 - Webview CSP Hardening

- Pass `panel.webview` into the webview HTML builder and include
  `webview.cspSource` in the CSP.
- Guard the message listener against null/non-object messages.
- Register button event listeners after all webview functions are declared.

## 1.0.26 - Webview Button Binding Fix

- Replace inline webview `onclick` handlers with event listeners.
- Add a nonce-based script CSP so newer VS Code/Codex webview hosts can run
  the cockpit script reliably.
- This targets the symptom where only sidebar Start MCP Server works while
  cockpit buttons, Live Debug, and Live Runtime Log stay at their initial text.

## 1.0.25 - Codex-Only Cleanup

- Package the extension only as `ANA MAX - Codex MCP Cockpit`.
- Remove non-Codex client positioning from the manifest, README, settings,
  cockpit copy, keywords, and MCP config helper.
- Replace the old config command with `ana.showCodexMcpConfig`.
- Keep the runtime protocol unchanged: ANA MAX serves MCP on localhost for
  Codex through VS Code.

## 1.0.24 - Direction Reset

- Make VS Code + Codex the primary operator surface.
- Keep Start MCP Server auto-reveal and visible Live Runtime Log feedback.

## 1.0.23 - Live Runtime Feedback

- Auto-reveal the cockpit when Start MCP Server runs.
- Move Live Runtime Log above chat so startup feedback is immediately visible.
- Log the already-running smart-ready state instead of relying only on a toast.

## 1.0.22 - Codex Extension Identity

- Rename the package to `ana-codex-cockpit`.
- Keep the visible product name `ANA MAX - Codex MCP Cockpit`.

## Earlier

- Added Smart Ready, router recommendations, Wake, Checkpoint, REM Sleep,
  Live Debug, safe-mode confirmations, and MCP runtime controls.
