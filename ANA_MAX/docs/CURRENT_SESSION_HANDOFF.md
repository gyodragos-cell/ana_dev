# Current Session Handoff

Latest checkpoint: `SESSION_CHECKPOINT_2026-05-27T080700Z0000.md`
Timestamp: 2026-05-27T08:07:00+03:00
Memory topic: `session_checkpoint_2026_05_27T080700Z0000`

Open the checkpoint file for the full handoff.

## Fast Resume

Read these first:

```text
docs/NEXT_SESSION_BOOTSTRAP.md
docs/AGENT_MEMORY.md
ANA_MAX/docs/SESSION_CHECKPOINT_2026-05-27T080700Z0000.md
```

Current known-good runtime:

```text
MCP: http://127.0.0.1:8766/mcp
Health: http://127.0.0.1:8766/health
Expected health: online, mcp_ready=True, tools_count=85
```

What is now valuable:

- `tool_router` is MCP-visible and recommends compact tool stacks.
- failed tool results may include `data.auto_guidance.tool_router`.
- `agent_coach action=recommend` combines telemetry + `tool_router` and returns `primary_tool`, `tool_stack`, and `next_action`.
- failed tool results now include `data.auto_guidance.agent_coach_recommend` with `primary_tool`, `tool_stack`, and `next_action`.
- failed tool results also include compact `data.guidance_summary` for easy UI/agent display.
- smart readiness now verifies a controlled failed tool returns `guidance_summary`.
- smart readiness now verifies `resources/templates/list` returns an empty `resourceTemplates` list instead of HTTP 404.
- MCP `tools/call` failed payloads now expose top-level `guidance_summary` as well as nested `data.guidance_summary`.
- cockpit VSIX `ana-ai.ana-antigravity-chat@1.0.8` is packaged as `ANA MAX Hybrid AI Cockpit`. It renders top-level `guidance_summary`, includes `Checkpoint` plus `REM Sleep`, carries public repo/author-with-Codex/license/homepage/keywords metadata, includes the marketplace icon at `assets/ana-max-icon.png`, and defaults `runtimeRoot` to the open workspace folder for public safety. Public GitHub release commit: `7f91659`.
- Windsurf CLI was not found in PATH, but the extension docs and `ANA_MAX/HYBRID_MCP_CONFIG.md` document the manual Windsurf/Cursor-style MCP config: name `anamax`, type HTTP/remote MCP, URL `http://127.0.0.1:8766/mcp`.
- cockpit VSIX packaging is repeatable with `python ANA_MAX/dev_artifacts/scripts/package_cockpit_vsix.py`; it builds/verifies artifacts without install/reload.
- no-reload quality gate is repeatable with `python ANA_MAX/dev_artifacts/scripts/no_reload_quality_gate.py`; it validates compileall, focused pytest, MCP readiness, MCP smoke, and VSIX packaging without forcing an IDE reload.
- launcher shortcut exists at `ANA_MAX_Launcher/quality_gate_no_reload.bat` for the same no-reload gate.
- `session_rem_sleep` is MCP-visible as the between-session REM/recalibration tool. It writes retrospective reports under `ANA_MAX/docs/rem_sleep/` and compact lessons into memory.
- latest REM consolidation report: `ANA_MAX/docs/rem_sleep/REM_SLEEP_REPORT_2026-05-27T040435+0000.md`.
- MCP smoke has a safe `session_rem_sleep action=latest` case and passes on the live 85-tool server.
- `mcp_readiness_check.py --expect-tool session_rem_sleep` passes on the live MCP server.
- launchers now use smart readiness checks, not only tool count.
- cockpit UI now has Smart Ready and Recommend flows backed by `tool_router` + `agent_coach action=recommend`.
- cockpit VSIX `ana-ai.ana-antigravity-chat@1.0.8` is packaged and installed in VS Code/Qoder; reload IDEs manually only when the current chat context is safe.
- current chat should not be forced to reload.
- latest clean MCP smoke: `ANA_MAX/dev_artifacts/reports/mcp_smoke_report_20260527_071334.json` with 65 pass, 20 skipped unsafe, 0 fail on the live 85-tool server.
- latest clean no-reload quality gate: `ANA_MAX/dev_artifacts/reports/no_reload_quality_gate_20260527_080630.json` with summary `{ "pass": 5 }`.
- latest REM consolidation report: `ANA_MAX/docs/rem_sleep/REM_SLEEP_REPORT_2026-05-27T043327+0000.md`.
- cockpit JS syntax: `node --check vscode_extension/extension.js` and `node --check ANA_MAX/extension/_vsix_unpack_103/extension/extension.js` -> OK.
- latest focused local pytest after REM tool: `tests/runtime/test_tool_router_tool.py tests/runtime/test_agent_coach_recommend.py tests/runtime/test_session_rem_sleep_tool.py` -> 9 passed.

If the IDE says `fetch failed`, the MCP server is not reachable. Restart it from
`ANA_MAX` on port `8766`, then verify `/health` before debugging tool code.
