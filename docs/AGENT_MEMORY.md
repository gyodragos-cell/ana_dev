# ANA MAX Agent Memory

Last updated: 2026-06-02

This file is the compact persistent memory for agents working in this workspace.
Use it before deep work, together with `AGENTS.md` and the relevant docs.
For fastest chat recovery, read `docs/ANA_LAB_MASTER_CONTEXT.md` first; it is
the merged one-file lab context.

## Current Operating Context

- Codex is the primary project manager and implementation agent for this workspace.
- VS Code + Codex are the primary operator surface. Use the ANA MAX Activity Bar plus the `ANA MAX MCP` Live Console as the stable control surface.
- Keep one coherent lead by default. Billy brings material and real-world signals; Codex filters, designs, implements, and verifies; ANA observes, reports, audits, remembers, and proposes suggest-only repairs.
- Quality order: organization, respect for future readers/coworkers, clarity, utility, then features.
- The Cockpit webview is disabled as a primary lab surface because it was host-fragile. Keep it out of the critical workflow unless explicitly re-enabled for debugging. New operator controls should be Activity-Bar-first.
- Antigravity is installed but should be treated as an optional sub-agent/helper only, not the primary ANA control surface. Its 2026-05-28 UI update changed MCP/skills behavior enough that ANA UX work should be validated in VS Code first.
- Treat the workspace as multi-agent when other tools are active, but keep implementation priority on the VS Code/Codex workflow unless Billy explicitly redirects.
- MCP should be used first whenever it provides relevant project context, tools, diagnostics, or structured knowledge.
- Golden rule: ANA first for scoped lab work. Use `ana_codex_companion.py`,
  `agent_coach action=recommend`, `tool_router`, or a relevant ANA
  observation/context tool before meaningful Codex action. If ANA returns
  `WARN`, pause mutation and address the challenge; if ANA returns `FAIL`, stop
  action work until readiness/evidence is repaired. Source:
  `docs/ANA_CODEX_GOLDEN_RULE.md`.
- Disk-side active ANA surface is 90 tools after retiring `adal_integration`, and current live MCP also reports 90 tools. Live Behavior now has 9 selected probes, including the `agent_coach` monitor-noise filter and the context generated-memory noise filter. Current expected clean shape is `reload=PASS`, `tool_surface=PASS(live=90,manifest=90)`, `behavior=PASS(checks=9/9)`, and `identity=PASS`. Current extension source/package is v1.0.71 after the voice + Golden Rule coverage lane; install/reload evidence should be refreshed after packaging.
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
- In docs/examples, use placeholders such as `<n>` or `<timestamp>` for volatile
  counters and report filenames that change after every checkpoint/gate. Keep
  stable verdicts and output shapes exact.
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
- `graph_context_pack` is ANA's lab-native Graphify-inspired graph layer over `ana_code_map`. It builds `ANA_MAX/memory/graph_map/graph.json`, `GRAPH_REPORT.md`, and `graph.html`, with file/symbol/dependency/keyword nodes and `EXTRACTED`/`INFERRED` relation confidence.
- `code_context_pack` now combines foreground UI snapshot, ANA Code Map, and optional Graph Map results. It accepts both `task="..."` and `query="..."`; `query` is an alias for agent/search-style calls and is covered by Live Behavior checks. When `include_text=false`, Code Context keeps the query precise and does not mix in foreground window title/text. For code work, prefer `code_context_pack` first, then `graph_context_pack query/path` when relationships matter. Latest Code Map refresh in this lane has 958 summaries.
- `ana_code_map.query` demotes generated memory and archive paths for general project-state questions: `ANA_MAX/docs/SESSION_CHECKPOINT_*`, `ANA_MAX/docs/rem_sleep/`, `ANA_MAX/dev_artifacts/archives/`, and `ANA_MAX/archives/` no longer outrank active scripts/docs unless the query explicitly asks for checkpoint, REM, archive, or security-research material. This keeps `code_context_pack` from opening stale generated history when the operator asks for the next scoped lab action.
- `ana_graph_map.query_graph` follows the same intent: keyword hubs and generated-memory/archive file nodes are demoted for general project-state questions, and low-signal checkpoint/archive neighbors are hidden unless the query explicitly asks for that material. This keeps Graph Map useful as a relationship lens instead of amplifying old session history.
- `ANA MAX: Nucleus Smoke` is the one-button Activity Bar health gate. It runs health, tools/list, router, coach, code context, graph context, tool healthcheck, error radar, trust score, and a final `context_maps` freshness check. The map check runs after `graph_context_pack`, so graph auto-refresh can settle before Nucleus decides PASS/WARN. Script: `ANA_MAX/dev_artifacts/scripts/ana_nucleus_smoke.py`. Latest PASS report in this lane is `ANA_MAX/dev_artifacts/reports/nucleus_smoke_20260601_234253.json`: PASS 10/0/0 with maps code 960 and graph 10635/29288.
- `ANA MAX: Autonomy Pass` is the lab-safe pre-work confidence loop. It runs health, UI observe, live reload marker, live tool-surface freshness, live behavior freshness, context map freshness, file activity, memory archive readiness, code context, graph context, router, coach, tool healthcheck, error radar, Patch Advisor, dry-run Review Batch Plan, recent Review Batch Run ledger, trust score, report writing, and optional checkpoint. Script: `ANA_MAX/dev_artifacts/scripts/ana_autonomy_runner.py`. Autonomy now prioritizes MCP restart when `live_tool_surface` or `live_behavior` is stale, and prioritizes Code Map/Graph Map refresh when `context_maps` is stale, even if coach recommends an action.
- `Autonomy Pass` now prints and stores the selected Live Behavior check count, for example `[PASS] live_behavior live_behavior 9/9 checks`, and preserves `failed_checks` in the compact signal when any marker fails. This keeps the autonomy audit aligned with Operator Status `behavior=PASS(checks=9/9)`.
- `Autonomy Pass` also prints/stores `context_maps`, for example `[PASS] context_maps code:PASS(958) graph:PASS(10623n/29217e)`. If Code Map or Graph Map is stale against active dirty-tree mtimes, the expected next action is to run `python ANA_MAX/dev_artifacts/scripts/ana_refresh_context_maps.py`, then rerun Autonomy Pass.
- When Autonomy warns only on `live_behavior`, the expected next action is: restart ANA MCP, then run Live Behavior, Reload Consistency, Post-Reload Verify, and Autonomy Pass.
- `ANA MAX: Codex Companion`, `ANA MAX: Conversation Audit`, `ANA MAX: Voice Operator Smoke`, `ANA MAX: Profile Status`, `ANA MAX: Lab Quality Gate`, `ANA MAX: Reload Readiness`, `ANA MAX: Reload Consistency`, `ANA MAX: Live Behavior`, `ANA MAX: Post-Reload Verify`, `ANA MAX: Operator Status`, `ANA MAX: Review Batch Plan`, and `ANA MAX: Refresh Context Maps` are packaged in VSIX v1.0.71 as Activity-Bar-only controls. Codex Companion runs `ana_codex_companion.py`; Conversation Audit runs `ana_conversation_audit.py`; Voice Operator Smoke runs `ana_voice_operator_smoke.py --json` to verify voice queue -> bridge -> conversation audit; Profile Status calls `tool_router mode=profile_status` with local coverage fallback; Lab Quality Gate runs `ANA_MAX/dev_artifacts/scripts/lab_quality_gate.py`; Reload Readiness runs `ana_reload_readiness.py --no-write`; Reload Consistency runs `ana_reload_consistency_check.py --no-write`; Live Behavior runs `ana_live_behavior_check.py`; Operator Status runs `ana_operator_status.py`; Review Batch Plan runs `ana_review_batch_runner.py --all-batches --no-write`; Refresh Context Maps runs `ana_refresh_context_maps.py --json`; Checkpoint uses the deterministic local checkpoint lane. Packaged artifacts: `vscode_extension/ana-codex-cockpit-1.0.71.vsix` and `ANA_MAX/ana-max-codex-cockpit-1.0.71.vsix`.
- Permission profiles are now runtime policy. `permission_manifest.json` covers the 90 active disk-side MCP tools, `safe_execute` blocks inactive profiles, `tool_router` filters by active profiles, and `ana_permission_manifest_coverage.py` is included in the lab quality gate. Latest profile/coverage evidence: `permission_manifest_coverage_20260601_145648.json` PASS runtime=90 manifest=90 missing=0 extra=0, and `tool_profile_report_20260601_145615.json` with unprofiled=0 inactive=0 confirmation-required=12.
- `agent_coach action=recommend` combines recent telemetry with `tool_router` and returns `schema=ana.agent_coach.recommend.v1`, `primary_tool`, `tool_stack`, `router`, `coach`, and `next_action`.
- `agent_coach` intentionally filters successful read-only monitor probes from loop detection, including `graph_context_pack action=stats`, the Live Behavior `code_context_pack query="operator status reload behavior"` probe, `session_audit action=trust`, `error_radar scope=quick/git`, and the intentional `router_failure_demo` auto-guidance demo. This prevents Autonomy from reporting false `critical` coach severity while keeping real repeated failures visible.
- `ana_codex_companion.py` is the Codex-first anti-blind-work bridge. It runs health, foreground UI snapshot, `tool_router`, `agent_coach`, `code_context_pack` with Graph Map, `error_radar`, and `tool_healthcheck` when coach warns, then prints an `[ANA]` / `[ANA challenge]` / `[CODEX]` / `[NEXT]` report. Use it before scoped Codex work when Billy asks whether ANA is really helping Codex. Activity Bar command: `ANA MAX: Codex Companion`.
- `session_rem_sleep` is ANA's deterministic between-session recalibration tool. It reads recent checkpoints, observability telemetry, and conversation lessons, then reports what worked, mistakes/friction, patterns, recommendations, and a next-session prompt. `action=consolidate` writes `ANA_MAX/docs/rem_sleep/REM_SLEEP_REPORT_*.md` and saves compact lessons into `conversation_learning` and `ana_memory`.
- When using `session_rem_sleep action=consolidate`, call `action=latest` only after consolidate finishes. Do not run consolidate and latest in parallel, because latest may race and return the previous report.
- Latest REM consolidation/report: `ANA_MAX/docs/rem_sleep/REM_SLEEP_REPORT_2026-06-01T173531+0000.md`; it summarizes the current reload/version/review-batch planning lane and next-session rules.
- Historical full MCP smoke was clean as of `ANA_MAX/dev_artifacts/reports/mcp_smoke_report_20260528_042102.json`: 65 pass, 21 skipped unsafe, 0 fail on the older live 86-tool server. Previous clean run: `mcp_smoke_report_20260527_071334.json` with 65 pass, 20 skipped, 0 fail. Current fast confidence should use the 90-tool Nucleus Smoke and no-reload quality gate.
- No-reload quality gate was clean as of `ANA_MAX/dev_artifacts/reports/no_reload_quality_gate_20260602_100724.json`: compileall, focused pytest, permission-manifest coverage, identity surface check, VSIX version consistency, MCP readiness, MCP smoke/live behavior, and VSIX packaging all passed (8/8) after the v1.0.71 voice + Golden Rule coverage work.
- Full lab quality gate is clean as of `ANA_MAX/dev_artifacts/reports/lab_quality_gate_20260601_151812.json`: compile, focused runtime tests including Nucleus Smoke coverage, governance, permission-manifest coverage, extension syntax, VSIX version consistency, identity surface, trace report, MCP health, and live Nucleus Smoke all passed (10/10; focused pytest 154 passed).
- Linux readiness remains `WINDOWS_FIRST` as of `ANA_MAX/dev_artifacts/reports/linux_readiness_20260601_150056.json`: score 0, 738 findings, 174 affected files, 40 core blocker files. This is expected; keep Linux as a prepared mirror lane and keep the portable core focused on MCP, tool_router, agent_coach, Code/Graph Context, Nucleus, Autonomy, Session Audit, and REM.
- Post-Reload Verify now prints identity status beside live reload, live tool-surface, and Nucleus Smoke. Current clean live result after MCP reload is `PASS` with marker, tool surface, identity, live behavior, and Nucleus Smoke aligned.
- `session_audit` trust now includes compact identity-surface evidence and caps trust at 70% if the active Codex-first identity surface fails.
- `ana_live_behavior_check.py` verifies that live MCP exposes selected current behavior, not only `/health` or `tools/list`. Current probes check whether `session_audit action=trust` includes identity-surface fields, whether `code_context_pack query=...` is honored precisely as an alias for `task=...` when `include_text=false`, whether Graph Map can promote the more precise code candidate above a noisy Code Map text match, whether Graph Map can still promote the precise file when `limit=1`, whether live `error_radar` dirty-tree runtime counts match disk-side behavior, whether `error_radar` returns its compact summary breakdown, whether live `agent_coach` already filters known read-only monitor/demo telemetry, and whether Code/Graph Context avoid generated checkpoint/archive noise for the `next scoped lab action after green baseline` probe. It warns until MCP reloads stale tool code. The default CLI returns non-zero on `WARN`; `--allow-warn` is only for log collection wrappers and must not be treated as a successful reload.
- `ana_operator_status.py` and `ana_lab_state_summary.py` now print `behavior=STATUS(checks=P/T)` beside tool surface and identity. Current live status is expected to show `behavior=PASS(checks=9/9)` when the selected behavior probes are fresh.
- `ana_reload_readiness.py` now decides reload usefulness from three signals: missing reload marker, live tool-surface drift, and live behavior staleness. It no longer says reload is unnecessary just because the old marker is present.
- Reload diagnostics are intentionally aligned: `Reload Readiness`, `Operator Status`, `Lab State`, `Post-Reload Verify`, and `Autonomy Pass` should all report WARN while live MCP has stale selected behavior, and all converge to PASS only after MCP restart loads disk-side code. If tool-surface drift returns, it should also be reported explicitly.
- `Lab State` now distinguishes pure stale live behavior from VS Code/VSIX reload needs. If only `live_behavior_stale` is present, it recommends `Restart ANA MCP, then run Live Behavior, Reload Consistency, and Post-Reload Verify.`
- `ana_reload_consistency_check.py` is the read-only guard for that alignment. It compares `Reload Readiness`, `Operator Status`, `Lab State`, and `Post-Reload Verify`; current live expected shape after MCP reload is `PASS aligned=True readiness=PASS operator=PASS lab_state=PASS post_reload=PASS`.
- Latest Lab State report is `ANA_MAX/dev_artifacts/reports/lab_state_summary_20260601_170740.json`: reload/tool-surface/behavior/identity PASS, trace aligned, dirty tree counted, archive readiness PASS.
- `ana_dirty_tree_report.py` classifies the large lab dirty tree without mutating files. Current report is `ANA_MAX/dev_artifacts/reports/dirty_tree_report_20260601_170417.json`: 463 changed paths, split into 145 active work paths and 318 generated/memory paths. Active categories are config=2, doc=31, extension=4, runtime=23, script=42, test=43; generated/memory categories are checkpoint=268, rem_sleep=46, memory=1, other=3. `ANA_MAX/docs/CURRENT_SESSION_HANDOFF.md` is treated as generated checkpoint memory, not active product docs, so saving a checkpoint does not stale the doc review batch by itself. The report includes `active_work.by_category`, `generated_or_memory.by_category`, and ordered `active_work.review_batches` (`runtime -> script -> test -> config -> extension -> doc`) with count/tracked/untracked/top folders/path samples, next steps, and focused `suggested_commands`. Use it before any archive/commit decision, and do not archive without the exact operator confirmation rule.
- `ana_patch_advisor.py` embeds local Dirty Tree evidence for `large_dirty_tree` recommendations, so it does not undercount runtime/script work when live MCP `error_radar` behavior is stale before restart. Error Radar remains an input signal, but local dirty-tree classification is preferred for dirty-tree evidence.
- `ana_patch_advisor.py` also includes Dirty Tree `active_work.review_batches` in its suggest-only report and adds a "Review active work batches before choosing a patch" recommendation. Current first batch is `runtime`, followed by `script`, `test`, `config`, `extension`, and `doc`; compact batches preserve focused `suggested_commands` for the next verification step.
- `ana_review_batch_runner.py` is the dry-run-first execution bridge for those focused review commands. It defaults to planned/dry-run, can run a selected batch with `--run`, rejects shell metacharacters, allows only Python commands sourced from `ana_dirty_tree_report.active_work.review_batches.suggested_commands`, and never archives/deletes/commits/reloads. Latest runtime batch run report is `ANA_MAX/dev_artifacts/reports/review_batch_runner_20260601_171644.json`: PASS for runtime compileall plus focused router/coach/error_radar/tool_healthcheck pytest.
- `Autonomy Pass` compacts Patch Advisor's local Dirty Tree signals as `dirty_tree_available` and `dirty_tree_total`, so the autonomy report can prove self-healing used local dirty-tree evidence even while live MCP `error_radar` is stale.
- `Autonomy Pass` now preserves Patch Advisor review batches in `signals.patch_advisor`, including `first_review_batch`, `first_review_next_step`, `first_review_commands`, and compact per-batch counts. Current first review batch is `runtime`.
- `Autonomy Pass` now includes a local dry-run `review_batch_plan` after Patch Advisor. It calls Review Batch Runner in all-batches plan mode, preserves compact category/command metadata in `signals.review_batch_plan`, and does not execute those commands from Autonomy.
- `Autonomy Pass` now includes local read-only `review_batch_runs` after the plan. It reads recent Review Batch Runner reports, compares them to current planned categories, checks whether each report is fresh against the latest active dirty-tree file mtime for that category, and preserves compact counts in `signals.review_batch_runs`; current evidence is planned=6, passed=6, missing=0, failing=0, stale=0.
- Latest persisted Autonomy report is `ANA_MAX/dev_artifacts/reports/autonomy_runner_20260601_233005.json`: `PASS` with 19 pass, 0 warn, 0 fail, trust 92%, trace 19/19 aligned, `context_maps` PASS, Patch Advisor review batches, dry-run Review Batch Plan, fresh Review Batch Run ledger signals, and next_action `Continue with one new scoped lab action; review batches verified 6/6. Do not rerun them unless new changes land.`
- Latest standalone Trace report is `ANA_MAX/dev_artifacts/reports/trace_report_20260601_191044.json`: `PASS`, 18 steps, 18 spans, aligned, sourced from `autonomy_runner_20260601_191040.json`.
- Governance check is clean as of `ANA_MAX/dev_artifacts/reports/governance_check_20260601_185437.json`: 117 pass, 0 fail.
- `ana_memory_hygiene.py` and `ana_memory_archive.py` are the dry-run-first cleanup path for old checkpoints and REM reports. Latest dry-run archive readiness is `ANA_MAX/dev_artifacts/reports/memory_archive_20260601_185704.json`: 313 planned moves, `date_basis=utc`, no files moved. Use `--no-write` to plan, `--readiness-report <report> --no-write` to prove a plan is still safe, and only run archive apply with the exact operator confirmation phrase `ARCHIVE_OLD_MEMORY`. Archive folders use UTC dates and both CLIs print `date_basis=utc` to avoid local/UTC rollover confusion during late lab sessions.
- `ana_local_checkpoint.py` refreshes the memory archive dry-run report after a successful checkpoint by default, so `Operator Status` should not become stale just because a checkpoint was saved. Use `--no-refresh-memory-archive` only for focused tests or when intentionally avoiding report writes.
- Disk-side and live `session_checkpoint_tool.py` refresh the memory archive dry-run report after successful checkpoints. If Operator Status ever shows memory readiness STALE, run `ana_memory_archive.py` locally to refresh the plan.
- `Operator Status` and `Lab State` also surface memory `date_basis=utc`, so the compact operator surfaces match the raw memory hygiene/archive tools.
- `Operator Status` also prints the latest REM Sleep report pointer, so the operator can see whether session memory was consolidated without opening `docs/rem_sleep/`.
- `Operator Status` and `Lab State Summary` now print VSIX artifact readiness as `package=PASS(main=True,copy=True)`, proving both local lab VSIX artifacts exist before an operator install.
- `Operator Status` now prints context map freshness as `maps=code:PASS(<summaries>) graph:PASS(<nodes>n/<edges>e)`. It compares Code Map and Graph Map mtimes with the latest active dirty-tree file; if either map is stale and reload diagnostics plus Autonomy are clean, `next_action` recommends `python ANA_MAX/dev_artifacts/scripts/ana_refresh_context_maps.py`.
- `Lab State Summary` now surfaces the same context map freshness as `maps=...` and recommends `python ANA_MAX/dev_artifacts/scripts/ana_refresh_context_maps.py` when structural context is stale while reload signals are clean.
- `ana_refresh_context_maps.py` is the one-command map refresh lane. It runs Code Map first, Graph Map second, then verifies final map freshness with the same status logic. Use it instead of manually running `ana_code_map.py refresh --force` and `ana_graph_map.py refresh`.
- `Operator Status` now recommends `Continue with one scoped lab action.` when reload diagnostics are PASS and the latest Autonomy report is PASS; it recommends Autonomy Pass only when no clean latest Autonomy evidence exists. It also prints `review=batch=<category> command=<first suggested command> plan=dry_run batches=<n> commands=<n>` from the latest Autonomy Patch Advisor and Review Batch Plan signals, plus `review_run=<report>:PASS(mode=run,category=<category>,commands=<n>,pass=<n>,fail=<n>,timeout=<n>,planned=<n>)` from the latest Review Batch Runner report. This lets the operator see both the next focused verification and what was actually run.
- `Operator Status` also prints `review_runs=runtime:PASS(...),script:PASS(...),test:PASS(...),config:PASS(...),extension:PASS(...),doc:PASS(...)` by reading recent Review Batch Runner reports. Current evidence shows all six active review batches passed and fresh: runtime, script, test, config, extension, and doc.
- When the dry-run review plan is fully covered by the recent fresh run ledger, `Operator Status` appends `verified=<passed>/<planned> all_pass=true fresh=true` to the `review=` line. If a category changed after its latest report, it prints `fresh=false stale=<category>` and does not count that category as verified.
- `Review Batch Runner` report filenames now include microseconds, PID/time-ns entropy, mode, and category, for example `review_batch_runner_<stamp>_<pid>_<ns>_run_script.json`. This avoids report overwrites when script/test/doc batches run in parallel during lab verification.
- `Autonomy Pass` uses the same fresh verified review-batch evidence when choosing `next_action`: if all planned review batches are already passed and fresh, it prefers one new scoped lab action over a generic coach recommendation to rerun context tools.
- Full runtime test batch caught an import-path collision between `ANA_MAX/core` and the legacy root `core/` package. `tests/runtime/conftest.py` now puts `ANA_MAX` first and extends `core.__path__` with the legacy root `core/` fallback, so both modern ANA_MAX tests and older runtime tests can run together. Evidence: `python -m pytest tests/runtime -q` passed with 359 tests, and Review Batch Runner `category=test` passed in `review_batch_runner_20260601_180250.json`.
- `session_rem_sleep` is MCP-visible after restart. `mcp_readiness_check.py --expect-tool session_rem_sleep` passes, and direct MCP `session_rem_sleep action=latest` returns the latest REM report.
- MCP readiness is now contract-based: see `docs/MCP_AGENT_READINESS_CONTRACT.md` and `ANA_MAX_Launcher/mcp_readiness_check.py`. Readiness means health is online, `tool_router` is callable, and `agent_coach action=recommend` returns a `primary_tool`.
- MCP readiness now also proves a controlled failed tool result includes top-level `guidance_summary` plus nested `data.guidance_summary` with `primary_tool` and `next_action`.
- MCP readiness now also verifies `resources/templates/list`; HTTP `/mcp` and stdio both return empty `resourceTemplates`, `resources`, and `prompts` lists for optional MCP discovery methods so agent IDEs do not mark the connection unhealthy after `tools/list`.
- Launcher scripts now call smart readiness checks so stale MCP servers without `tool_router`/`agent_coach recommend` fail early instead of looking healthy by tool count.
- VS Code/Codex cockpit now exposes smart readiness and next-tool recommendations in the webview and command palette. It validates `tool_router` and `agent_coach action=recommend` instead of showing only raw health.

## Historical Public/Marketplace Memory

The notes below are retained for project history only. Current mother-lab work
is v1.0.71, Activity-Bar-first, private-lab-first, and public/GitHub work is
low priority unless Billy explicitly asks.

- Marketplace extension is live as `d4d8176a-bb85-66ef-93dd-a58bc9ddfdad.ana-antigravity-chat` at `https://marketplace.visualstudio.com/items?itemName=d4d8176a-bb85-66ef-93dd-a58bc9ddfdad.ana-antigravity-chat`. Keep the package `name`/extension id stable for Marketplace updates unless intentionally creating a separate new listing; public display/copy is now Codex-first (`ANA MAX - Codex MCP Cockpit`).
- **Cockpit v1.0.19** is a historical stable build, not the current lab target: `ANA MAX Codex MCP Cockpit` remains the single visible command-palette entrypoint, the `ANA MAX` Activity Bar runtime view is restored so buttons are visible in VS Code-compatible hosts, the first guided button is `1 Start MCP Server`, `Live Debug` polls MCP health/tools every 5 seconds, guided command results stay inside the cockpit instead of opening `Untitled` JSON tabs, and explicit lifecycle buttons no longer show the `Save REM` safe-mode write popup. Fixed `callTool` shadowing and stripped carriage returns from output.
- No-reload quality gate 2026-05-28: 5/5 PASS (`compile_core_routing`, `pytest_routing_guidance`, `mcp_smart_readiness`, `mcp_all_tools_smoke`, `package_cockpit_vsix_no_install`).
- Extension Conflict resolved: Old `ana-ai.ana-antigravity-chat` uninstalled; only `d4d8176a...` remains active.
- **Cockpit v1.0.25 Codex-only cleanup**: the VSIX is now intentionally for VS Code + Codex only. Remove non-Codex client positioning from extension manifest, README, settings, keywords, and cockpit copy. A 2026-05-28 live check showed `fetch failed` when no process was listening on `127.0.0.1:8766`; manual `python ANA_MAX\main.py --host 127.0.0.1 --port 8766` restored `/health` with `mcp_ready=true`, 86 tools, and full readiness PASS.

- Cockpit VSIX `d4d8176a-bb85-66ef-93dd-a58bc9ddfdad.ana-antigravity-chat@1.0.12` is a historical beginner-friendly cockpit baseline. Patch `1.0.13` fixes real button friction found by Antigravity QA: `Start Runtime` auto-detects `ANA_MAX/main.py` from a parent workspace, falls back to `python` from PATH when no runtime venv exists, and strips carriage returns from Cockpit output. Marketplace-ready artifact: `vscode_extension/ana-antigravity-chat-1.0.13.vsix`; lab artifact: `ANA_MAX/ana-antigravity-hybrid-1.0.13.vsix`.
- Stable v1.0.12 release memory lives in `docs/STABLE_COCKPIT_BASELINE_1.0.12.md`; v2 product cleanup is intentionally deferred in `docs/V2_PRODUCT_CLEANUP_BACKLOG.md`.
- Historical early REM sleep reports included `ANA_MAX/docs/rem_sleep/REM_SLEEP_REPORT_2026-05-28T005425+0000.md` and `REM_SLEEP_REPORT_2026-05-28T005329+0000.md`; current latest REM is tracked in the active section above.
- v1.0.12 MCP lifecycle QA PASS is recorded in `docs/QA_PASS_1.0.12_MCP_LIFECYCLE.md`: live mother-lab MCP has 86 tools, `session_lifecycle wake/rest preview` passes, calm flows do not show generic confirmation, and risky tools remain gated.
- Visual release screenshots should be captured only into `ANA_MAX/sandbox/screenshots/` and reviewed with `docs/VISUAL_RELEASE_ASSETS_GUIDE.md` before anything is copied to public README/site/Marketplace assets.
- Public messaging cleanup commit `93d23cb` was pushed to the GitHub release repo on 2026-05-27. It aligns README/site/extension README wording around `Stable Baseline v1.0.12`, `85 public tools / 86 mother-lab tools`, and "Agent Runtime Layer" instead of confusing raw OS/version labels. GitHub Python CI #54, Publish GitHub Pages #54, and Pages deployment #91 all completed successfully.
- Antigravity/Qoder should be credited as an AI-assisted release QA and runtime consistency collaborator. It helped with MCP live checks, screenshot/visual QA, Marketplace/GitHub/site consistency audits, and post-restart validation while Codex coordinated architecture and implementation.
- Public GitHub release/site were updated after the Marketplace publish: commit `57d2330` explains the agent workflow and "Agent OS layer"; commit `829fe1b` adds one-click Marketplace install links; commit `87eaa09` fixes the top-left site logo alignment. GitHub Pages #49 and Python CI #49 passed for `87eaa09`.
- The public GitHub repo description is still stale in GitHub metadata (`Windows AI Agent with 85 MCP Tools Features:`). Suggested replacement: `Local-first MCP runtime and hybrid cockpit for AI coding agents: observe, route, act, verify, remember.`
- The extension is positioned only as the ANA MAX Codex MCP Cockpit for VS Code. Non-Codex IDE integrations are out of scope for the current extension cleanup.
- Do not force IDE reload while the operator wants to preserve the current chat. Cockpit `Checkpoint` and `REM Sleep` controls are packaged/installed in 1.0.8, but the active IDE window may need a manual reload before showing them.
- Cockpit source/unpacked code now formats top-level MCP `guidance_summary` for failed tool calls as a readable "Tool failed with guidance" block. This source change also awaits a later package/reinstall/reload.
- Cockpit VSIX packaging is now repeatable with `python ANA_MAX/dev_artifacts/scripts/package_cockpit_vsix.py`; it builds and verifies local VSIX artifacts without installing/reloading.
- Full local validation without IDE reload is now repeatable with `python ANA_MAX/dev_artifacts/scripts/no_reload_quality_gate.py`; it writes a JSON report under `ANA_MAX/dev_artifacts/reports/`, checks policy coverage, packages the VSIX, and does not install/reload the extension.
- The same no-reload validation can be launched with `ANA_MAX_Launcher/quality_gate_no_reload.bat` for operator-friendly use.
- Prefer fake-only scenarios first. Mark lab-only tests explicitly before real tool execution.
- Use Frida only when runtime instrumentation is actually needed. MCP Frida operations may require `confirm=True`.
- Known practical tools and concepts from prior sessions include desktop vision, foreground/UI observation, Frida instrumentation, live debug console, watchdog, `agent_coach`, `workspace_situational_awareness`, `error_radar`, `file_patch`, `project_navigator`, `uia_click`, `uia_type`, `vision_region_capture`, and `vision_find_element`.
- If a tool schema mismatch appears, check whether the tool expects `action` or `operation` before retrying.
- For quick Codex-to-ANA MCP access when tools are not attached natively in chat, use `python ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py` or `ANA_MAX/dev_artifacts/scripts/ana_mcp_call.ps1`. It supports `--health`, `--list`, `--schema TOOL`, JSON args, `@json-file`, and easy `key=value` args, for example `desktop_control operation=view confirm=true` or `desktop_control operation=move_mouse target=10,10 confirm=true`.
- PowerShell MCP helpers live at `ANA_MAX/dev_artifacts/scripts/ana_mcp.ps1`. Dot-source with `. .\ANA_MAX\dev_artifacts\scripts\ana_mcp.ps1`, then use `ana-health`, `ana-windows`, `ana-view`, `ana-move 300 300`, `ana-under-hood`, `ana-frida`, `ana-step TOOL ...`, and `ana-smoke "text"`. Prefer `ana-step` for agent work because it performs health -> observe -> act -> verify -> diagnose-on-fail and writes `ANA_MAX/dev_artifacts/reports/agent_step_*.json`.
- Local shared visibility uses `ANA_MAX/dev_artifacts/scripts/ana_mirror_watch.py`, which writes `ANA_MAX/logs/ana_mirror.jsonl` with foreground UI snapshot summaries, event_stream stats, and periodic screenshots. PowerShell helper: `ana-mirror`; VS Code live console builds from 1.0.32 start the mirror alongside the watchdog.
- Mother-lab control room is `ANA_MAX/dev_artifacts/scripts/ana_lab_hub.py`, exposed through PowerShell helper `ana-lab`. It combines MCP health, `event_stream` stats, mirror feed, watchdog output, and optional god-mode read-only checks into one live terminal stream. Modes: `ana-lab dev`, `ana-lab lab`, `ana-lab god`.
- Frida diagnostics are available through `ANA_MAX/dev_artifacts/scripts/ana_frida.py` and `ana-frida`. Read-only summary/version/devices/list_processes are allowed with MCP confirmation; active attach/spawn/inject/hook/terminate require `--allow-active` and explicit operator intent.

## Voice And Launcher Memory

- The unified launcher is under `ANA_MAX_Launcher`.
- Past launcher issues involved duplicate Python processes and fragile Windows quoting. Prefer verified launcher paths and health checks over assumptions.
- Voice history: `pyttsx3`/SAPI had `Class not registered`; fallback through Windows `.NET System.Speech` was added in prior work.
- For continuous chat voice, `chat_voice_bridge.py` is the practical bridge; `tools/live_voice_bridge.py` is the voice engine/test surface. VSIX v1.0.71 auto-starts the stable lab surface on extension activation, starts the bridge with clipboard monitoring enabled by default, writes filtered high-signal lines to `ANA_MAX/voice_queue.txt`, starts the private-lab `ana_voice_inbox.py --continuous` microphone daemon, and starts `ana_conversation_audit_tail.py` so new evidence appears in the Live Console as `[CONVERSATION-LIVE]` lines. Full Voice Readout is enabled by default: long queue/copied-chat text is spoken in chunks with `--full-readout` instead of being skipped at `voiceReadoutMaxChars`, while secret-word filtering stays active. Single Voice Channel is now the default: `anaMax.voiceReadoutDirect=false`, so the queue bridge is the main voice and direct System.Speech is reserved for fallback/manual tests to avoid duplicate or triple voices. `ANA MAX: Voice Operator Smoke` runs `ana_voice_operator_smoke.py` to prove the local voice queue -> bridge -> conversation audit path is alive before Billy relies on it; real evidence `ANA Voice Operator Smoke: PASS audit_seen=True` was produced for label `v1.0.71-final`. v1.0.71 links command voice and ANA-first coverage: command triggers are announced through `onDidExecuteCommand`, action start/success/fail are spoken through `runInCockpit`, and normal status/diagnostic/audit commands route through `runWithGoldenRule` before executing. Bootstrap controls such as Live Console, Start MCP Server, Codex Guard, and Live Conversation Audit stay loop-safe exceptions but still speak cues. Bug bounty polish in v1.0.71 redacts Windows user paths case-insensitively in spoken text and conversation audit, and summarizes noisy Golden Rule / Live Behavior / Nucleus / Operator Status / reload / audit lines before speech. Voice Inbox copies recognized speech to `ANA_MAX/memory/voice_inbox_latest.txt`; when the focused window title is allowed and the text starts with `codex` or `ana`, it can paste into the focused chat input and press Enter. Conversation evidence now writes to `ANA_MAX/memory/conversation_audit.jsonl` from Voice Inbox, copied chat text, voice queue lines, and bridge status events; `ANA MAX: Conversation Audit` summarizes the latest evidence, and `ANA MAX: Live Conversation Audit` starts the realtime tail manually. Real Codex/ChatGPT chat speech still cannot be read directly by the VS Code extension; copied chat text remains the honest fallback for hearing Codex output.

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
