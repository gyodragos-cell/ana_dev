# ANA MAX Agent Memory

Last updated: 2026-05-27

This file is the compact persistent memory for agents working in this workspace.
Use it before deep work, together with `AGENTS.md` and the relevant docs.
For fastest chat recovery, read `docs/NEXT_SESSION_BOOTSTRAP.md` first, then this file.

## Current Operating Context

- Codex is the primary project manager and implementation agent for this workspace.
- Antigravity is also installed and may work in parallel. Treat the workspace as multi-agent.
- MCP should be used first whenever it provides relevant project context, tools, diagnostics, or structured knowledge.
- After the latest MCP restart, the server recovered and discovered 85 tools, including `tool_router` and `session_rem_sleep`.
- Do not rely on raw chat history being available. Use this file, handoff docs, session history, and checkpoints as durable memory.

## Project Vision

ANA MAX is a Windows-first, privacy-first local agent runtime for private workstations, QA labs, offline model workflows, and agent IDEs that need real computer context.

The core loop is:

```text
observe -> decide -> act -> verify -> learn
```

The product message should stay practical and white-hat: ANA MAX is not magic. It observes the real workspace, uses the right tools, verifies with tests/logs/runtime evidence, and keeps the user informed.

## Workspace Discipline

The private mother lab is:

```text
C:\Users\billy\Desktop\ana_dev\ANA_MAX
```

The clean public release workspace is:

```text
C:\Users\billy\Desktop\ANA_MAX_GitHub_Release
```

Every meaningful mother-lab change needs an explicit decision:

```text
ship-safe -> sync to public release
lab-only -> document as private/internal and do not copy
```

Public release surfaces must not contain secrets, memory databases, private logs, screenshots with private content, local videos, local machine paths, tokens, `.env`, private endpoints, or private model/provider experiments.

## Agent Collaboration Rules

- Respect existing changes from the user, Codex, Antigravity, Qoder, extensions, and other agents.
- Do not revert unrelated edits.
- Before architecture, runtime, protocol, security, dashboard, or release work, read the relevant docs in `docs/` and `ANA_MAX/docs/`.
- Prefer compact JSON-oriented outputs for agent IDE workflows.
- After repeated failures or two similar failed attempts, stop repeating the same action and consult diagnostics or `agent_coach` when available.
- If a shell/tool error repeats, search `ana_memory` or `conversation_learning` for a known fix before another retry. Save the final fix back into memory when it is likely to recur.
- For UI/desktop work, follow: observe, act once, verify.

## Important Architecture Memory

- ANA MAX is a safe local runtime for agent work: observe, plan, route, execute, verify, learn.
- The active kernel/runtime work is dev/lab-oriented, deterministic, local-first, and fake-transport based unless the user explicitly approves real integrations.
- Distributed behavior should remain additive and backward compatible. When transport is absent, subsystems should keep working in local-only mode.
- Current documented stable dev components include remote execution with in-process transport, distributed memory, cluster join/leave/heartbeat/health/routing, distributed runtime task routing, event bus, semantic FS, permissions/security boundaries, and service lifecycle.
- Experimental or dev-only areas include dashboard API/UI, networked remote execution, persistent distributed memory, policy/audit hardening, and public runtime exposure.

## Safety And Public Hygiene

- Safe-mode is read-only by default.
- Dev-mode is local lab execution.
- Write-mode is controlled workspace or release writing.
- High-risk actions need explicit operator intent or approval: subprocess escalation, network access, desktop control, public release writes, private/external system access, and broad file mutation.
- Redact token, secret, password, and API key fields before logs, dashboards, docs, exports, or public sync.
- Public-safe material is limited to architecture docs, policy descriptions, test matrices, high-level roadmaps, and reviewed release plans.

## Tool And Runtime Memory

- Tool quality beats tool count.
- New tools should define capabilities, policy requirements, normalized result shape, and tests.
- ANA tool execution now attaches automatic failure guidance in `tools/base.py`: failed tool results may include `data.auto_guidance` from `ana_memory` known fixes, `agent_coach_recommend` primary next tool/stack/action, `agent_coach` telemetry analysis, and `tool_router` next-tool recommendations. Failed results also include compact `data.guidance_summary` when guidance is available.
- `tool_router` recommends a compact MCP tool stack for a task/error so agents do not blindly consider every available tool.
- `agent_coach action=recommend` combines recent telemetry with `tool_router` and returns `schema=ana.agent_coach.recommend.v1`, `primary_tool`, `tool_stack`, `router`, `coach`, and `next_action`.
- `session_rem_sleep` is ANA's deterministic between-session recalibration tool. It reads recent checkpoints, observability telemetry, and conversation lessons, then reports what worked, mistakes/friction, patterns, recommendations, and a next-session prompt. `action=consolidate` writes `ANA_MAX/docs/rem_sleep/REM_SLEEP_REPORT_*.md` and saves compact lessons into `conversation_learning` and `ana_memory`.
- Latest REM report: `ANA_MAX/docs/rem_sleep/REM_SLEEP_REPORT_2026-05-27T043327+0000.md`.
- MCP smoke is clean as of `ANA_MAX/dev_artifacts/reports/mcp_smoke_report_20260527_071334.json`: 65 pass, 20 skipped unsafe, 0 fail on the live 85-tool server.
- No-reload quality gate is clean as of `ANA_MAX/dev_artifacts/reports/no_reload_quality_gate_20260527_080630.json`: compileall, focused pytest including `session_rem_sleep`, MCP readiness, MCP smoke, and cockpit VSIX packaging all passed.
- `session_rem_sleep` is MCP-visible after restart. `mcp_readiness_check.py --expect-tool session_rem_sleep` passes, and direct MCP `session_rem_sleep action=latest` returns the latest REM report.
- MCP readiness is now contract-based: see `docs/MCP_AGENT_READINESS_CONTRACT.md` and `ANA_MAX_Launcher/mcp_readiness_check.py`. Readiness means health is online, `tool_router` is callable, and `agent_coach action=recommend` returns a `primary_tool`.
- MCP readiness now also proves a controlled failed tool result includes top-level `guidance_summary` plus nested `data.guidance_summary` with `primary_tool` and `next_action`.
- MCP readiness now also verifies `resources/templates/list`; HTTP `/mcp` and stdio both return empty `resourceTemplates`, `resources`, and `prompts` lists for optional MCP discovery methods so agent IDEs do not mark the connection unhealthy after `tools/list`.
- Launcher scripts now call smart readiness checks so stale MCP servers without `tool_router`/`agent_coach recommend` fail early instead of looking healthy by tool count.
- VS Code/Qoder cockpit now exposes smart readiness and next-tool recommendations in the webview and command palette. It validates `tool_router` and `agent_coach action=recommend` instead of showing only raw health.
- Marketplace extension is live as `d4d8176a-bb85-66ef-93dd-a58bc9ddfdad.ana-antigravity-chat` at `https://marketplace.visualstudio.com/items?itemName=d4d8176a-bb85-66ef-93dd-a58bc9ddfdad.ana-antigravity-chat`.
- Cockpit VSIX `d4d8176a-bb85-66ef-93dd-a58bc9ddfdad.ana-antigravity-chat@1.0.12` is the stable beginner-friendly cockpit baseline. It includes the marketplace icon at `assets/ana-max-icon.png`, author credit `Dragos / gyodragos-cell with Codex`, public repo/homepage/license metadata, marketplace keywords, workspace-relative `runtimeRoot` defaults, Smart Ready, Wake, Recommend, Checkpoint, Rest Preview, Save REM, `session_lifecycle`, `tool_router`, and `agent_coach action=recommend` flows. Marketplace artifact: `vscode_extension/ana-antigravity-chat-1.0.12.vsix`. Lab packaging also produced `ANA_MAX/ana-antigravity-hybrid-1.0.12.vsix`.
- Stable v1.0.12 release memory lives in `docs/STABLE_COCKPIT_BASELINE_1.0.12.md`; v2 product cleanup is intentionally deferred in `docs/V2_PRODUCT_CLEANUP_BACKLOG.md`.
- Public GitHub release/site were updated after the Marketplace publish: commit `57d2330` explains the agent workflow and "Agent OS layer"; commit `829fe1b` adds one-click Marketplace install links; commit `87eaa09` fixes the top-left site logo alignment. GitHub Pages #49 and Python CI #49 passed for `87eaa09`.
- The public GitHub repo description is still stale in GitHub metadata (`Windows AI Agent with 85 MCP Tools Features:`). Suggested replacement: `Local-first MCP runtime and hybrid cockpit for AI coding agents: observe, route, act, verify, remember.`
- The extension is positioned as a hybrid MCP cockpit for Codex, Antigravity/Qoder, Windsurf, Cursor, and VS Code-compatible agent IDEs. Windsurf CLI was not found in PATH, so Windsurf install/config is documented for manual setup through MCP settings.
- Do not force IDE reload while the operator wants to preserve the current chat. Cockpit `Checkpoint` and `REM Sleep` controls are packaged/installed in 1.0.8, but the active IDE window may need a manual reload before showing them.
- Cockpit source/unpacked code now formats top-level MCP `guidance_summary` for failed tool calls as a readable "Tool failed with guidance" block. This source change also awaits a later package/reinstall/reload.
- Cockpit VSIX packaging is now repeatable with `python ANA_MAX/dev_artifacts/scripts/package_cockpit_vsix.py`; it builds and verifies local VSIX artifacts without installing/reloading.
- Full local validation without IDE reload is now repeatable with `python ANA_MAX/dev_artifacts/scripts/no_reload_quality_gate.py`; it writes a JSON report under `ANA_MAX/dev_artifacts/reports/` and does not install/reload the extension.
- The same no-reload validation can be launched with `ANA_MAX_Launcher/quality_gate_no_reload.bat` for operator-friendly use.
- Prefer fake-only scenarios first. Mark lab-only tests explicitly before real tool execution.
- Use Frida only when runtime instrumentation is actually needed. MCP Frida operations may require `confirm=True`.
- Known practical tools and concepts from prior sessions include desktop vision, foreground/UI observation, Frida instrumentation, live debug console, watchdog, `agent_coach`, `workspace_situational_awareness`, `error_radar`, `file_patch`, `project_navigator`, `uia_click`, `uia_type`, `vision_region_capture`, and `vision_find_element`.
- If a tool schema mismatch appears, check whether the tool expects `action` or `operation` before retrying.

## Voice And Launcher Memory

- The unified launcher is under `ANA_MAX_Launcher`.
- Past launcher issues involved duplicate Python processes and fragile Windows quoting. Prefer verified launcher paths and health checks over assumptions.
- Voice history: `pyttsx3`/SAPI had `Class not registered`; fallback through Windows `.NET System.Speech` was added in prior work.
- For continuous chat voice, `chat_voice_bridge.py` is the practical bridge; `tools/live_voice_bridge.py` is the voice engine/test surface.

## Verification Commands

Mother lab checks:

```powershell
cd C:\Users\billy\Desktop\ana_dev\ANA_MAX
python -m compileall -q main.py core tools
python main.py --test
python main.py --list-tools
```

Public release checks:

```powershell
cd C:\Users\billy\Desktop\ANA_MAX_GitHub_Release
python -m compileall -q main.py core tools vscode_extension
python main.py --test
python main.py --list-tools
python -m unittest discover -s tests -v
```

MCP health checks from prior sessions used:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8766/health"
```

## Current Priorities

- Keep `AGENTS.md` and this memory file current as project-level guidance changes.
- Use `docs/MCP_TOOL_ORCHESTRATION_PLAN.md` as the working plan for making all tools useful through MCP, internally useful, or clearly marked lab-only/experimental.
- Use `docs/MCP_AGENT_READINESS_CONTRACT.md` when touching launchers, IDE MCP health, or readiness smoke checks.
- Use `docs/TOOL_MATRIX.md` for current tool role/status decisions.
- Use `docs/AGENT_STEROID_TOOLS.md` to decide which local/hybrid tools give the agent meaningful extra context and when Frida/watchdog/UI tools are worth using.
- Use `docs/PUBLIC_RELEASE_SYNC_BACKLOG.md` to park good mother-lab improvements that should be reviewed for the clean GitHub release later.
- Keep roadmap, project map, README, setup, changelog, `.env.example`, and tests aligned whenever behavior changes.
- Maintain the lab/public split and make sync decisions explicit.
- Stabilize agent reliability tools and self-QA checks.
- Keep observation-first workflows compact and useful for agent IDEs.
- Audit and consolidate tools toward a smaller reliable core when needed.
- Clarify public versioning whenever repo, docs, dashboard, or release labels diverge.

## Source Memory Files

Agents should consult these when deeper history is needed:

- `ANA_MAX_CHAT_HISTORY_RECOVERY.txt`
- `ANA_MAX_COMPLETE_HISTORY_AND_ROADMAP.txt`
- `ANA_MAX/docs/CURRENT_SESSION_HANDOFF.md`
- `ANA_MAX/docs/CURRENT_SESSION_HANDOFF_2026-05-22.md`
- `ANA_MAX/docs/SESSION_HISTORY_2026-05-22.md`
- `ANA_MAX/docs/SESSION_CHECKPOINT_*.md`
- `ANA_MAX/docs/ROADMAP.md`
- `docs/PROTOCOL_DECISIONS.md`
- `docs/ANA_MAX_*`
