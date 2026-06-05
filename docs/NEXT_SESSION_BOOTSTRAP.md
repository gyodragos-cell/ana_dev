# ANA MAX Next Session Bootstrap

Purpose: prevent a new agent/chat from starting blind.

Read `docs/ANA_LAB_MASTER_CONTEXT.md` first when a new chat starts. This file
is the expanded bootstrap checklist for agents that need deeper detail.

## First 5 Minutes

1. Read `AGENTS.md`.
2. Read `docs/ANA_LAB_MASTER_CONTEXT.md`.
3. Read `docs/CODEX_LAB_MANAGER_PROMPT.md` when starting a fresh Codex/agent session.
4. Read `docs/DOCS_INDEX.md` when looking for any project documentation.
5. Read `docs/ANA_LAB_PROJECT_HISTORY.md` if the human/project story matters.
6. Read `ANA_MAX/docs/CURRENT_SESSION_HANDOFF.md`.
7. Open the checkpoint named in that handoff.
8. Run:

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
- Expected MCP health after MCP reload: `status=online`, `mcp_ready=True`, `tools_count=90`.
- Current live MCP reports `tools_count=90`. Live Behavior now has 9 selected probes, including the `agent_coach` monitor-noise filter and the Code/Graph Context generated-memory noise filter. The expected clean shape is tool surface, selected live behavior `9/9`, identity, and Post-Reload Verify PASS.
- `tool_router` is visible in `tools/list`.
- `graph_context_pack` is visible in `tools/list`.
- `agent_coach` supports `action=coach`, `action=recommend`, `action=lessons`, and `action=reset`.
- `agent_coach action=recommend` returns `schema=ana.agent_coach.recommend.v1`, `primary_tool`, `tool_stack`, `router`, `coach`, and `next_action`.
- `session_rem_sleep` is MCP-visible. It analyzes recent checkpoints, telemetry, and lessons, then writes a REM-style retrospective report plus memory lessons.
- `session_lifecycle` is MCP-visible after server restart. `action=wake` resumes from the latest REM report or performs first-run situational awareness; `action=rest consolidate=false` previews REM without writing; `consolidate=true` saves REM.
- Optional MCP discovery methods are handled: `resources/list`, `resources/templates/list`, and `prompts/list` return empty lists instead of HTTP 404.
- Historical full MCP smoke artifact from the older 86-tool server:
  `ANA_MAX/dev_artifacts/reports/mcp_smoke_report_20260528_042102.json`
  with 65 pass, 21 skipped_unsafe, 0 fail. Current fast confidence comes from
  the 90-tool Nucleus Smoke and no-reload quality gate below.
- Last clean no-reload quality gate before the 8th Live Behavior probe: `ANA_MAX/dev_artifacts/reports/no_reload_quality_gate_20260601_215634.json` with 8 pass, 0 fail, and no advisory. It includes permission-manifest coverage, identity surface, VSIX version consistency, MCP readiness, MCP smoke, live behavior 7/7, Nucleus Smoke unit coverage, autonomy/operator-status/review-batch-runner tests, and extension command tests before VSIX packaging. Rerun after MCP restart to capture the newer `agent_coach` monitor-noise probe.
- Latest Autonomy Pass report: `ANA_MAX/dev_artifacts/reports/autonomy_runner_20260601_191040.json` with `PASS (18 pass / 0 warn / 0 fail)`, trust 100%, trace 18/18 aligned, Patch Advisor review batches, first review commands, dry-run Review Batch Plan, read-only fresh Review Batch Run ledger signals, and next_action to continue with one new scoped lab action because review batches are verified 6/6.
- Latest REM sleep report: `ANA_MAX/docs/rem_sleep/REM_SLEEP_REPORT_2026-06-01T173531+0000.md`. Run `session_rem_sleep action=consolidate` and then `action=latest` sequentially, not in parallel.
- Current stable VS Code operator surface is the ANA MAX Activity Bar plus `ANA MAX MCP` Live Console. The old Cockpit webview is disabled as a primary surface because it was host-fragile; keep new operator controls on the left Activity Bar unless explicitly debugging webview.
- Packaged lab VSIX: `ANA MAX - Codex MCP Cockpit` v1.0.64. It can be installed locally; run `Developer: Reload Window` when Billy is ready.
- Anti-blind-work control: `ANA MAX: Codex Companion`, backed by `ana_codex_companion.py`, should be used when Billy asks Codex to prove it is listening to ANA before acting.
- One-button nucleus check: `ANA MAX: Nucleus Smoke` in the Activity Bar, backed by `ANA_MAX/dev_artifacts/scripts/ana_nucleus_smoke.py`.
- Lab-safe autonomy check: `ANA MAX: Autonomy Pass` in the Activity Bar, backed by `ANA_MAX/dev_artifacts/scripts/ana_autonomy_runner.py`. It includes a dry-run Review Batch Plan and a read-only Review Batch Run ledger after Patch Advisor, and should not proceed to coach-driven action while live tool-surface or live behavior is stale.
- Policy/status controls: `ANA MAX: Profile Status` calls `tool_router mode=profile_status` with local coverage fallback; `ANA MAX: Lab Quality Gate` runs `ANA_MAX/dev_artifacts/scripts/lab_quality_gate.py`; `ANA MAX: Reload Readiness` runs `ana_reload_readiness.py --no-write`; `ANA MAX: Reload Consistency` runs `ana_reload_consistency_check.py --no-write`; `ANA MAX: Live Behavior` runs `ana_live_behavior_check.py`; `ANA MAX: Operator Status` runs `ana_operator_status.py` and prints latest REM Sleep plus Code Map/Graph Map freshness; `ANA MAX: Post-Reload Verify` runs `ana_post_reload_verify.py`.
- If `Reload Readiness` later shows only `reasons=live_behavior_stale` with
  marker and tool surface PASS, use the Python-only lane: restart ANA MCP, then
  run Live Behavior, Reload Consistency, Post-Reload Verify, and Autonomy Pass.
  Do not install VSIX or reload VS Code for that case unless another signal
  asks for it.
- Review Batch Runner is available after Operator Status/Patch Advisor:
  `python ANA_MAX/dev_artifacts/scripts/ana_review_batch_runner.py --run`
  runs the first focused command from the first active Dirty Tree review batch;
  use `--category script --all --run` for a specific batch.
- Operator Status now shows both the first review command and the current
  dry-run Review Batch Plan size: `plan=dry_run batches=<n> commands=<n>`.
- Operator Status also shows the latest Review Batch Runner execution report as
  `review_run=...`, so a new session can see which batch was actually run.
- Operator Status also shows `review_runs=...`, a per-category ledger from
  recent Review Batch Runner reports. Current expected shape shows PASS for
  runtime, script, test, config, extension, and doc.
- When that ledger covers the dry-run plan and the reports are newer than the
  active dirty-tree files they verify, Operator Status adds
  `verified=6/6 all_pass=true fresh=true` to the `review=` line. Treat that as
  evidence that review batches are already green unless new changes land.
- If a category changed after its latest report, Operator Status marks
  `fresh=false stale=<category>` and Autonomy should not use the verified-batch
  shortcut.
- Autonomy Pass also uses that evidence in `next_action`, so a clean run should
  not ask for generic reruns of context/review tools when all review batches are
  already verified.
- Full `tests/runtime` now uses `tests/runtime/conftest.py` to prefer
  `ANA_MAX/core` while keeping the legacy root `core/` fallback available.
  Latest evidence: `python -m pytest tests/runtime -q` passed with 359 tests
  and Review Batch Runner `category=test` passed.
- Latest nucleus smoke report: `ANA_MAX/dev_artifacts/reports/nucleus_smoke_20260601_151812.json` with `PASS (9 pass / 0 warn / 0 fail)`.
- Graph context layer is active: `ANA_MAX/dev_artifacts/scripts/ana_graph_map.py` builds `ANA_MAX/memory/graph_map/graph.json`, `GRAPH_REPORT.md`, and `graph.html`. Latest live graph had 7,764 nodes and 15,593 edges.

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
code_context_pack
graph_context_pack
ana_memory
session_rem_sleep
tool_healthcheck
file_patch/edit
qa_testing
```

If ANA MCP tools are not attached directly to the current chat, use the local
wrapper:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py --health
python ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py --schema desktop_control
python ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py desktop_control operation=view confirm=true
python ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py desktop_control operation=move_mouse target=10,10 confirm=true
python ANA_MAX/dev_artifacts/scripts/ana_nucleus_smoke.py --mcp-url http://127.0.0.1:8766/mcp
python ANA_MAX/dev_artifacts/scripts/ana_autonomy_runner.py --mcp-url http://127.0.0.1:8766/mcp --checkpoint
python ANA_MAX/dev_artifacts/scripts/lab_quality_gate.py
```

For a more natural PowerShell bridge:

```powershell
. .\ANA_MAX\dev_artifacts\scripts\ana_mcp.ps1
ana-health
ana-under-hood
ana-frida
ana-step desktop_capture operation=get_windows --no-screenshot
ana-smoke "ANA MAX smoke"
```

## What Was Just Finished

- 2026-05-29 lab update: added a Graphify-inspired, lab-native graph layer without external repo dependency.
- Added `ANA_MAX/dev_artifacts/scripts/ana_graph_map.py` with `refresh`, `query`, `path`, and `stats`.
- Added MCP tool `graph_context_pack`, registered in `ANA_MAX/main.py` and `ANA_MAX/tools/__init__.py`.
- `code_context_pack` now includes optional `graph_map` results and marks `ana_graph_map` as evidence.
- `tool_router` now recommends `graph_context_pack` for code-change flows.
- Added `ANA_MAX/dev_artifacts/scripts/ana_nucleus_smoke.py` and Activity Bar command `ANA MAX: Nucleus Smoke`.
- Added `ANA_MAX/dev_artifacts/scripts/ana_autonomy_runner.py` and Activity Bar command `ANA MAX: Autonomy Pass`.
- Autonomy Pass now checks live tool-surface and live behavior freshness and
  prioritizes MCP restart over action when live MCP is stale.
- Autonomy Pass now includes local all-batches dry-run Review Batch Plan
  evidence after Patch Advisor, without executing the planned commands.
- Autonomy Pass now also includes read-only Review Batch Run ledger evidence:
  planned categories are compared with recent Review Batch Runner reports.
- Added `ana_reload_consistency_check.py` so future sessions can verify that
  Reload Readiness, Operator Status, Lab State, and Post-Reload Verify agree.
- Packaged VSIX v1.0.64 with Activity-Bar-only `Codex Companion`, `Refresh Context Maps`, all-batches `Review Batch Plan`, `Nucleus Smoke`,
  `Autonomy Pass`, `Profile Status`, `Lab Quality Gate`, `Live Behavior`,
  `Reload Readiness`, `Reload Consistency`, `Post-Reload Verify`, and
  `Operator Status`. Checkpoint routes through the deterministic local
  checkpoint lane. Install/reload remains operator-controlled.
- Added permission profile runtime policy: `permission_manifest.json` covers
  the 90 active disk-side tools after `adal_integration` retirement,
  `tool_router mode=profile_status` reports active profiles, and
  `ana_permission_manifest_coverage.py` is part of `lab_quality_gate.py`.
- Fixed `Open Dashboard`: it now generates a local HTML dashboard from live MCP data instead of opening a blank legacy `8787` page.
- Fixed `error_radar` false auth positives caused by timestamp milliseconds such as `,403`.
- `tool_router` became an MCP-visible recommendation router.
- Failed tool results can include `data.auto_guidance.tool_router`.
- `agent_coach action=recommend` now combines telemetry with `tool_router`.
- `tools/base.py` no longer uses deprecated `datetime.utcnow`.
- MCP real smoke is clean.
- No-reload quality gate is clean and repeatable, including VSIX version
  consistency.
- `session_rem_sleep` was added as ANA's between-session recalibration tool.
- Historical public/Marketplace note: Cockpit v1.0.19 was a previous stable
  Marketplace-era build for `ANA MAX - Codex MCP Cockpit`. It is not the
  current lab target; current lab work is v1.0.64, Activity-Bar-first, and
  private-lab-first.
- Cockpit VSIX 1.0.19 historical shape: single command-palette entrypoint,
  restored `ANA MAX` Activity Bar runtime buttons, `1 Start MCP Server` button,
  Live Debug polling every 5s, guided results stay in cockpit, lifecycle
  buttons are calm (no write popup). Historical local artifact:
  `vscode_extension/ana-antigravity-chat-1.0.19.vsix`.
- Historical public GitHub and GitHub Pages were updated after Marketplace publish:
  - `57d2330` explains the agent workflow and clarifies "Agent OS layer".
  - `829fe1b` adds one-click Marketplace install links to README and site.
  - `87eaa09` fixes the top-left site logo alignment.
  - GitHub Pages #49 and Python CI #49 passed for `87eaa09`.
- Fixed the post-discovery MCP client error `Method not found: resources/templates/list` by adding empty optional discovery responses to HTTP `/mcp` and stdio.

## Next Good Work

1. Use `agent_coach action=recommend` automatically in more runtime paths.
2. `session_rem_sleep` and `session_lifecycle` are now MCP-visible; keep them in smoke/readiness checks when changing MCP registration.

```powershell
python ANA_MAX_Launcher/mcp_readiness_check.py --mcp-url http://127.0.0.1:8766/mcp --expect-tool session_rem_sleep --expect-tool session_lifecycle
```

1. Do not force IDE reload if preserving the active chat matters. The current
   lab VSIX is v1.0.64; reload manually only after important chat context is
   safe.
2. Use `docs/MCP_AGENT_READINESS_CONTRACT.md` when changing MCP launcher, IDE, or smoke behavior.
3. Keep lab-only/private memory out of public release sync.

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
.\ANA_MAX\dev_artifacts\scripts\install_latest_lab_vsix.ps1 -Apply
```

Do this only after saving/exporting important chat context. Do not reinstall
Marketplace-era VSIX files for normal mother-lab work.

## Do Not Forget

- The worktree is dirty from broader lab work. Do not revert unrelated edits.
- Mother lab: `C:\Users\billy\Desktop\ana_dev\ANA_MAX`
- Public release workspace: `C:\Users\billy\Desktop\ANA_MAX_GitHub_Release`
- Public/GitHub work is pending and low priority. Focus on the mother lab unless Billy explicitly asks to sync.
- Generated packages/builds/logs should stay out of the root. Use `ANA_MAX/dev_artifacts/archives/workspace_cleanup_20260529/` for archived generated artifacts.
- Treat new runtime/tool behavior as mother-lab until explicitly reviewed for public sync.
