# ANA MAX Next Session Bootstrap

Purpose: prevent a new agent/chat from starting blind.

Read this file first when a new chat starts, then read the linked memory files.
This is a compact operational map, not a replacement for the full docs.

## First 5 Minutes

1. Read `AGENTS.md`.
2. Read `docs/AGENT_MEMORY.md`.
3. Read `ANA_MAX/docs/CURRENT_SESSION_HANDOFF.md`.
4. Open the checkpoint named in that handoff.
5. Run:

```powershell
git status --short
Invoke-RestMethod -Uri "http://127.0.0.1:8766/health"
```

If `/health` fails with connection refused or the IDE reports `fetch failed`,
restart the MCP server from `C:\Users\billy\Desktop\ana_dev\ANA_MAX`:

```powershell
venv\Scripts\python.exe -u main.py --host 127.0.0.1 --port 8766
```

For persistent launch from Codex, use `Start-Process` outside the sandbox. The
server must remain live after the command returns.

## Current Known Good State

- MCP URL: `http://127.0.0.1:8766/mcp`
- Health URL: `http://127.0.0.1:8766/health`
- Expected MCP health: `status=online`, `mcp_ready=True`, `tools_count=85`
- `tool_router` is visible in `tools/list`.
- `agent_coach` supports `action=coach`, `action=recommend`, `action=lessons`, and `action=reset`.
- `agent_coach action=recommend` returns `schema=ana.agent_coach.recommend.v1`, `primary_tool`, `tool_stack`, `router`, `coach`, and `next_action`.
- `session_rem_sleep` is MCP-visible. It analyzes recent checkpoints, telemetry, and lessons, then writes a REM-style retrospective report plus memory lessons.
- Optional MCP discovery methods are handled: `resources/list`, `resources/templates/list`, and `prompts/list` return empty lists instead of HTTP 404.
- Last clean MCP smoke: `ANA_MAX/dev_artifacts/reports/mcp_smoke_report_20260527_071334.json` with 65 pass, 20 skipped unsafe, 0 fail on the live 85-tool server.
- Last clean no-reload quality gate: `ANA_MAX/dev_artifacts/reports/no_reload_quality_gate_20260527_080630.json` with 5 pass, 0 fail.
- Latest REM sleep report: `ANA_MAX/docs/rem_sleep/REM_SLEEP_REPORT_2026-05-27T043327+0000.md`.

## Working Principle

The project value is shifting from "many tools exist" to "the right tool is
recommended at the right time." Do not make agents consider all tools blindly.

Default flow:

```text
observe -> diagnose -> route -> act once -> verify -> learn
```

Use this nucleus first:

```text
workspace_situational_awareness
project_navigator
error_radar
agent_coach action=recommend
tool_router
ana_memory
session_rem_sleep
tool_healthcheck
file_patch/edit
qa_testing
```

## What Was Just Finished

- `tool_router` became an MCP-visible recommendation router.
- Failed tool results can include `data.auto_guidance.tool_router`.
- `agent_coach action=recommend` now combines telemetry with `tool_router`.
- `tools/base.py` no longer uses deprecated `datetime.utcnow`.
- MCP real smoke is clean.
- No-reload quality gate is clean and repeatable.
- `session_rem_sleep` was added as ANA's between-session recalibration tool.
- Marketplace extension 1.0.9 is live as `ANA MAX - Hybrid AI Cockpit`: `https://marketplace.visualstudio.com/items?itemName=d4d8176a-bb85-66ef-93dd-a58bc9ddfdad.ana-antigravity-chat`.
- Cockpit VSIX 1.0.9 uses publisher `d4d8176a-bb85-66ef-93dd-a58bc9ddfdad`, includes the marketplace icon, repo/author-with-Codex credit/license/homepage/keywords, workspace-relative runtime defaults, `Checkpoint`, `REM Sleep`, Smart Ready, and hybrid Codex/Qoder/Windsurf config helpers. Local artifact: `vscode_extension/ana-antigravity-chat-1.0.9.vsix`.
- Public GitHub and GitHub Pages were updated after Marketplace publish:
  - `57d2330` explains the agent workflow and clarifies "Agent OS layer".
  - `829fe1b` adds one-click Marketplace install links to README and site.
  - `87eaa09` fixes the top-left site logo alignment.
  - GitHub Pages #49 and Python CI #49 passed for `87eaa09`.
- Fixed the post-discovery MCP client error `Method not found: resources/templates/list` by adding empty optional discovery responses to HTTP `/mcp` and stdio.

## Next Good Work

1. Use `agent_coach action=recommend` automatically in more runtime paths.
2. `session_rem_sleep` is now MCP-visible; keep it in smoke/readiness checks when changing MCP registration.

```powershell
python ANA_MAX_Launcher/mcp_readiness_check.py --mcp-url http://127.0.0.1:8766/mcp --expect-tool session_rem_sleep
```
3. Do not force IDE reload if preserving the active chat matters. Version `d4d8176a-bb85-66ef-93dd-a58bc9ddfdad.ana-antigravity-chat@1.0.9` is packaged and published; reload manually only after important chat context is safe.
4. Use `docs/MCP_AGENT_READINESS_CONTRACT.md` when changing MCP launcher, IDE, or smoke behavior.
5. Keep lab-only/private memory out of public release sync.

Before any optional IDE reload/install, run the no-reload gate:

```powershell
python ANA_MAX/dev_artifacts/scripts/no_reload_quality_gate.py
```

Or from Explorer/terminal:

```powershell
ANA_MAX_Launcher\quality_gate_no_reload.bat
```

## Later Cockpit Package

When the operator is ready to reload the IDE, package the current cockpit source:

```powershell
python ANA_MAX/dev_artifacts/scripts/package_cockpit_vsix.py
```

Then install the generated VSIX if desired:

```powershell
code --install-extension vscode_extension/ana-antigravity-chat-1.0.9.vsix --force
qoder --install-extension vscode_extension/ana-antigravity-chat-1.0.9.vsix --force
```

Do this only after saving/exporting important chat context.

## Do Not Forget

- The worktree is dirty from broader lab work. Do not revert unrelated edits.
- Mother lab: `C:\Users\billy\Desktop\ana_dev\ANA_MAX`
- Public release workspace: `C:\Users\billy\Desktop\ANA_MAX_GitHub_Release`
- Treat new runtime/tool behavior as mother-lab until explicitly reviewed for public sync.
