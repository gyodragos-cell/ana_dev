# ANA Lab Master Context

Last updated: 2026-06-02

This is the single-file operational context for ANA MAX mother-lab work. New
agents should read this first, then only open deeper docs/checkpoints when they
need detail.

For the human/project story of how Billy + Codex shaped the lab, read:

```text
docs/ANA_LAB_PROJECT_HISTORY.md
```

For the full documentation map, read:

```text
docs/DOCS_INDEX.md
```

For professional lab setup and safety boundaries, read:

```text
docs/LAB_README.md
docs/SAFETY_BOUNDARIES.md
```

For future Linux Mate preparation, read:

```text
docs/LINUX_MATE_MIGRATION_LANE.md
```

For serious-project discipline and profile boundaries, read:

```text
docs/ANA_SERIOUS_PROJECT_RULES.md
docs/ANA_PROFILE_MANIFEST.md
docs/ANA_EXAMPLES_AND_TESTS_CHECKLIST.md
```

For the full Codex operating prompt, read:

```text
docs/CODEX_LAB_MANAGER_PROMPT.md
```

## Priority

Focus on the private mother lab:

```text
C:\Users\billy\Desktop\ana_dev\ANA_MAX
```

Public/GitHub release work is pending and low priority. Do not sync, publish,
or expose lab work unless Billy explicitly asks.

## Current Operating Surface

- Primary pair: Billy + Codex in VS Code.
- Collaboration default: one coherent lead. Codex coordinates engineering and
  lab decisions. Treat external tools/repos only as research input, never as
  project identity or promotion.
- Stable controls: `ANA MAX` Activity Bar + `ANA MAX MCP` Live Console.
- Future Linux Mate migration is a prepared lane, not today's primary move.
- Webview/Cockpit is disabled as the primary lab surface because it was
  host-fragile. New operator controls should be Activity-Bar-first.
- Packaged lab VSIX: `ANA MAX - Codex MCP Cockpit` v1.0.71. Install is done;
  reload VS Code when Billy is ready for the extension host to load 1.0.71.
- The active anti-blind-work button is `ANA MAX: Codex Companion`; it runs
  `ana_codex_companion.py` so ANA observes, routes, coaches, context-packs,
  checks Error Radar, and challenges Codex before scoped work.
- The active accessibility proof button is `ANA MAX: Conversation Audit`; it
  runs `ana_conversation_audit.py` and summarizes recent Voice Inbox,
  copied-chat, voice-queue, and bridge-status evidence from
  `ANA_MAX/memory/conversation_audit.jsonl`.
- The active realtime accessibility stream is `ANA MAX: Live Conversation
  Audit`; it runs `ana_conversation_audit_tail.py` and prints new audit entries
  into the Live Console as `[CONVERSATION-LIVE]` lines.
- The active health button is `ANA MAX: Nucleus Smoke`; clean shape is PASS
  10/10, including a final `context_maps` freshness check after the graph
  context probe.
- The active autonomy button is `ANA MAX: Autonomy Pass`; it treats stale live
  tool surface or stale live behavior as restart blockers before action and
  includes dry-run Review Batch Plan plus read-only Review Batch Run ledger
  evidence after Patch Advisor.
- The active policy buttons are `ANA MAX: Profile Status` and
  `ANA MAX: Lab Quality Gate`.
- The active reload operator buttons are `ANA MAX: Reload Readiness`,
  `ANA MAX: Reload Consistency`, `ANA MAX: Live Behavior`, `ANA MAX: Operator Status`, and
  `ANA MAX: Post-Reload Verify`.

## Current Runtime State

Expected MCP:

```text
URL: http://127.0.0.1:8766/mcp
health: http://127.0.0.1:8766/health
status: online
mcp_ready: true
tools_count: 90 after MCP reload
```

Current important tools:

- `tool_router`
- `agent_coach`
- `code_context_pack`
- `graph_context_pack`
- `tool_healthcheck`
- `error_radar`
- `session_audit`
- `session_checkpoint`
- `session_lifecycle`
- `session_rem_sleep`
- `binary_map`
- `input_api_probe` lab-only

## Default Work Loop

```text
observe -> diagnose -> route -> act once -> verify -> learn
```

Quality order:

```text
organization -> respect for future readers/coworkers -> clarity -> utility -> features
```

Use this stack before code edits:

```text
Nucleus Smoke -> code_context_pack -> graph_context_pack -> tool_router/agent_coach -> patch -> tests -> session_audit/trust -> checkpoint/REM
```

## Start And End Of Session

At start:

```text
Smart Ready -> Wake -> Nucleus Smoke
```

During work:

```text
Recommend -> Code Map/Graph Map/Context Pack -> Autonomy Pass -> Checkpoint
```

At end:

```text
Rest Preview -> Save REM
```

## Health Gate

Run from Activity Bar:

```text
ANA MAX: Nucleus Smoke
```

Or terminal:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_nucleus_smoke.py --mcp-url http://127.0.0.1:8766/mcp
```

For the broader developer gate:

```powershell
python ANA_MAX/dev_artifacts/scripts/lab_quality_gate.py
```

For the lab-safe autonomy pass:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_autonomy_runner.py --mcp-url http://127.0.0.1:8766/mcp --checkpoint
```

This pass observes the current UI, asks router/coach for the next tool stack,
loads code and graph context, verifies tool health and error radar, prepares a
dry-run Review Batch Plan, checks recent Review Batch Run evidence, computes
trust, writes a report, and optionally saves a checkpoint. It does not run deep
instrumentation or arbitrary mutation tools.

After an operator MCP reload/restart:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_post_reload_verify.py --no-write
```

This verifies the live reload marker, tool surface, identity surface, live
behavior freshness, Nucleus Smoke, and compact lab state in one read-only
command.

For future Linux Mate readiness:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_linux_readiness.py
```

For governance/profile discipline:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_governance_check.py
```

Current expectation is `WINDOWS_FIRST`: the lab is still Windows-first, while
portable core pieces are being separated for a later Linux mirror.

Latest known good:

```text
MCP ready: true
MCP tools: 90 after MCP reload
ANA Nucleus: PASS (9 pass / 0 warn / 0 fail)
Autonomy Pass: PASS (19 pass / 0 warn / 0 fail), including context map freshness
Autonomy trace: aligned (18 steps / 18 spans)
Autonomy trust: observed 92% on the latest full pass
Governance: PASS (117 pass / 0 fail)
No-reload quality gate: PASS (8 pass, no advisory after live MCP reload)
Lab quality gate: PASS (10 pass, includes identity_surface_check and trace_report)
Lab state summary should be: reload=PASS, tool_surface=PASS, behavior=PASS(checks=9/9), maps=PASS, identity=PASS, trace_aligned=true, archive_readiness=PASS
```

Fast state command:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_lab_state_summary.py --no-write
```

Trace validation command:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_trace_report.py --latest
```

## Code Intelligence

ANA now has two structural layers:

- Code Map: `ANA_MAX/dev_artifacts/scripts/ana_code_map.py`
- Graph Map: `ANA_MAX/dev_artifacts/scripts/ana_graph_map.py`

Graph output:

```text
ANA_MAX/memory/graph_map/graph.json
ANA_MAX/memory/graph_map/GRAPH_REPORT.md
ANA_MAX/memory/graph_map/graph.html
```

Latest graph:

```text
nodes: 7764
edges: 15593
node kinds: file, symbol, dependency, keyword
edge confidence: EXTRACTED, INFERRED
```

`code_context_pack` now combines:

```text
foreground_ui_snapshot + ana_code_map + ana_graph_map
```

`tool_router` recommends `graph_context_pack` for code-change flows.

`graph_context_pack` and the local Graph Map script support blast-radius
queries for changed files. Patch Advisor consumes this graph signal before
recommending repairs, so code edits can be scoped by likely affected files and
tests instead of by guesswork.

## Recent Lab Wins

- Activity Bar became the stable control surface.
- Cockpit webview was removed from the critical path.
- `Open Dashboard` now generates local HTML from live MCP data instead of
  opening a blank legacy port `8787`.
- `error_radar` no longer treats timestamp milliseconds such as `,403` as an
  HTTP 403 auth failure.
- `error_radar` now has a dirty-tree breakdown in code/tests. Live MCP exposes
  it after server reload.
- `error_radar` filters deliberate debugger smoke-test `traceback_text` INFO
  lines so they do not appear as real traceback blockers after MCP reload.
- `Patch Advisor` was added as the safe self-healing bridge: diagnostics become
  suggest-only repair recommendations; it does not apply patches.
- `Patch Advisor` now includes Graph Map blast-radius evidence before risky
  edits, and recommends reviewing impacted files/tests before mutation.
- `Patch Advisor` now prefers local Dirty Tree's full breakdown for
  `large_dirty_tree` evidence instead of relying on stale live Error Radar or a
  sampled git path list. This prevents runtime/script work and checkpoint/REM
  noise from being undercounted before MCP restart.
- `Review Batch Runner` was added as the controlled execution bridge after
  Patch Advisor/Operator Status: it previews by default, runs only Python
  commands that came from Dirty Tree review batches, rejects shell
  metacharacters, and never archives/deletes/commits/reloads.
- `Autonomy Pass` now includes a dry-run Review Batch Plan after Patch Advisor:
  it records all active review batches and first focused commands in compact
  metadata, but does not execute the planned commands from Autonomy.
- `Autonomy Pass` now includes read-only Review Batch Run ledger verification:
  it compares planned batch categories with recent Review Batch Runner reports
  and reports planned/passed/missing/failing counts.
- `error_radar` now classifies runtime paths correctly when git status is run
  from inside `ANA_MAX` and returns paths like `tools/`, `core/`, and
  `dev_artifacts/scripts/`.
- `ana_live_behavior_check.py` now detects stale live `error_radar` behavior by
  comparing live dirty-tree runtime counts with the disk-side classifier.
- `ana_live_behavior_check.py` now also detects stale live `agent_coach`
  monitor-noise filtering, so a live server that still reports read-only
  monitor/demo telemetry as repeated failures shows `behavior=WARN` until ANA
  MCP is restarted.
- `ana_live_behavior_check.py` also guards the Code/Graph Context generated
  memory filter: the `next scoped lab action after green baseline` probe must
  keep active files ahead of `SESSION_CHECKPOINT`, REM, and archive noise.
- Graphify-inspired graph layer was implemented natively without importing the
  external repo.
- `graph_context_pack` and `code_context_pack` now rebuild Graph Map when Code
  Map changed after the graph was built. Live MCP exposes the `data.stale`
  marker after server reload.
- `tool_healthcheck` now reports web-search dependency availability for
  `ddgs` / `duckduckgo-search` so web research failures are visible instead of
  mysterious.
- `Nucleus Smoke` was added as one-button verification.
- `Autonomy Pass` was added as the safe observe-route-verify-audit loop.
- `Autonomy Pass` now emits compact agent trace spans for each major step:
  verification, context pack, tool call, audit, and checkpoint.
- `ana_trace_report.py` validates trace spans against
  `ana.agent_trace_span.v1`, checks step/span alignment, and writes a compact
  local trace report without raw private payloads.
- `Operator Status` and `ana_lab_state_summary.py` now surface live behavior
  freshness, identity status, and trace alignment, including inline validation
  when the latest autonomy report is newer than the saved trace report.
- `ana_file_activity_snapshot.py` was added as a privacy-preserving file
  activity sentinel for authorized roots. It detects created/deleted/modified
  files between snapshots using metadata and relative paths only; it does not
  read file contents.
- `Operator Status` now prints identity status and aggregate file activity counts as
  `files=created=N,deleted=N,modified=N`, so manual workspace changes are
  visible beside MCP readiness, reload, reports, and trace alignment.
- `Operator Status` now prints memory archive candidates and latest dry-run
  readiness. Memory hygiene defaults to keeping the latest 20 checkpoints and
  latest 20 REM reports. `STALE` means the saved dry-run plan is valid but no
  longer covers every current checkpoint/REM candidate.
- `Operator Status` now prints the latest REM Sleep report pointer, so the
  operator can confirm session memory consolidation from the compact status
  output.
- `Operator Status` and `Lab State Summary` now print `maps=code:... graph:...`
  so stale Code Map or Graph Map state is visible before ANA relies on
  structural context. When maps are stale but reload/autonomy evidence is clean,
  the recommended next action is to refresh both maps and rerun the status
  command.
- `Operator Status` now distinguishes code-behavior staleness from extension
  reload work: if only `live_behavior_stale` is present, it recommends
  restarting ANA MCP directly, then running Live Behavior, Reload Consistency,
  and Post-Reload Verify.
- `Operator Status` now prints `review=batch=<category> command=<command>` from
  the latest Autonomy/Patch Advisor signal, so the next focused verification is
  visible without opening JSON reports.
- `Operator Status` also appends the dry-run Review Batch Plan size as
  `plan=dry_run batches=<n> commands=<n>`, so the operator can see both the
  next command and the plan coverage from one line.
- `Operator Status` now prints `review_run=<latest review batch report>` so the
  operator can see which review batch was actually executed and whether all
  commands passed.
- `Operator Status` now also prints `review_runs=<per-category ledger>` so the
  operator can confirm recent PASS evidence for runtime, script, test, config,
  extension, and doc review batches.
- `Operator Status` checks review-batch freshness by comparing each batch
  report mtime with the latest active dirty-tree file mtime for that category.
  Fresh categories count as verified; stale categories print
  `fresh=false stale=<category>`.
- When the fresh review ledger covers the current dry-run plan,
  `Operator Status` appends
  `verified=<passed>/<planned> all_pass=true fresh=true` to the `review=` line.
- `Autonomy Pass` uses the same fresh verified review-batch evidence in
  `next_action`, preferring a new scoped lab action over generic context/review
  reruns when the ledger is fully green and fresh.
- Full `tests/runtime` now runs as one suite. The runtime test harness prefers
  `ANA_MAX/core` while keeping the legacy root `core/` modules as fallback,
  resolving the import collision that appeared during Review Batch Runner
  `category=test`.
- `Reload Readiness` uses the same distinction: a pure `live_behavior_stale`
  signal recommends direct ANA MCP restart instead of the broader VSIX install
  and VS Code reload lane.
- `Autonomy Pass` now includes `file_activity_snapshot` as a local read-only
  verification step, so autonomy reports and trace spans include aggregate
  workspace file activity before recommendations.
- `Autonomy Pass` now includes `memory_archive_readiness` as a local read-only
  verification step, so autonomy reports know whether checkpoint/REM cleanup
  planning is current before recommending the next action.
- `Autonomy Pass` now includes live tool-surface and live behavior freshness
  checks, and gives MCP restart priority over coach-driven action when live MCP
  is stale.
- `Autonomy Pass` now uses the same live-behavior stale follow-up as the other
  reload diagnostics: restart ANA MCP, then run Live Behavior, Reload
  Consistency, Post-Reload Verify, and Autonomy Pass.
- `Autonomy Pass` now also includes `context_maps` as a local read-only
  verification step. It uses the same Code Map/Graph Map freshness evidence as
  Operator Status and recommends refreshing both maps before continuing when
  structural context is stale.
- `ana_live_behavior_check.py` is strict by default and returns non-zero on
  `WARN`. Use `--allow-warn` only for operator log collection wrappers; it
  still prints `WARN` and must not be treated as a successful reload.
- `ana_reload_consistency_check.py` verifies that reload-facing diagnostics
  agree; aligned WARN is acceptable before MCP restart, disagreement is a
  repair signal.
- `adal_integration` was retired from active registration and permission
  profiles. Keep ANA's surface neutral: no external-tool promotion, no
  comparative advertising, and no unnecessary branded dependencies.
- `lab_quality_gate.py` now includes `trace_report`, so the broader developer
  gate validates autonomy trace alignment alongside compile, runtime tests,
  governance, permission manifest coverage, VSIX consistency, MCP health, and
  Nucleus Smoke.
- `session_audit` now includes a compact trace summary in trust/audit/replay
  outputs after MCP reload: availability, status, step/span counts, alignment,
  operation counts, and span-error count. It does not include raw private
  payloads.
- `ANA_LAB_LLM_INDEX.md` was added as a compact machine-oriented lab index for
  Codex, ANA, and future local agents.
- `Linux Mate Migration Lane` was documented so future Linux work can be
  prepared without derailing the Windows mother lab.
- Serious-project rules, profile manifest, and examples/tests checklist were
  added to keep ANA disciplined: no hype, no public god-mode claims, dangerous
  tools behind lab profiles, clear docs, tests, and real examples.
- Permission profiles are now runtime policy: `permission_manifest.json` covers
  90 active tools after MCP reload, `tool_router mode=profile_status` reports coverage, and
  `lab_quality_gate.py` includes permission-manifest coverage drift detection.
- VSIX v1.0.71 keeps the Activity Bar as the stable control surface, adds
  `Codex Companion` as the ANA-to-Codex challenge loop, adds
  `Conversation Audit` as the accessibility proof lane, keeps all-batches
  dry-run `Review Batch Plan` beside `Reload Readiness`, `Live Behavior`,
  `Reload Consistency`, and `Operator Status`, and routes `Checkpoint` through
  the deterministic local checkpoint lane. Do not add new controls to the
  fragile webview unless explicitly debugging it.
- Lab history was updated in `docs/NEXT_SESSION_BOOTSTRAP.md`,
  `docs/AGENT_MEMORY.md`, and session checkpoints.
- Lab state, memory hygiene, and memory archive dry-run scripts were added:
  `ana_lab_state_summary.py`, `ana_memory_hygiene.py`,
  `ana_memory_archive.py`, `ana_file_activity_snapshot.py`.

## Clean Workspace Rules

Active code stays in:

- `ANA_MAX/core/`
- `ANA_MAX/tools/`
- `ANA_MAX/dev_artifacts/scripts/`
- `vscode_extension/`
- `tests/`
- `docs/`

Generated outputs go to:

- `ANA_MAX/dev_artifacts/reports/`
- `ANA_MAX/dev_artifacts/audit/`
- `ANA_MAX/memory/`
- `ANA_MAX/sandbox/`

Old generated packages/builds were archived, not deleted:

```text
ANA_MAX/dev_artifacts/archives/workspace_cleanup_20260529/
```

Do not put `.vsix`, logs, screenshots, temp reports, or one-off experiments in
the repo root.

Not every `.md` should be physically moved into `docs/`: some root/package
markdown files are referenced by scripts, packaging, or legacy README paths.
Use `docs/DOCS_INDEX.md` as the single discovery point instead.

## Current Handoff

Latest handoff file:

```text
ANA_MAX/docs/CURRENT_SESSION_HANDOFF.md
```

Latest checkpoint at the time of this master context:

```text
ANA_MAX/docs/SESSION_CHECKPOINT_2026-06-01T185703Z0000.md
```

Project history:

```text
docs/ANA_LAB_PROJECT_HISTORY.md
```

## Caution

- Worktree is intentionally dirty with lab changes.
- Dirty tree is large partly because checkpoint/REM memory files are numerous.
  Use `ana_memory_hygiene.py --plan --no-write` to inspect archive candidates.
  Do not apply archive without explicit operator intent.
- Preserve unrelated edits from Billy, Codex, extensions, or prior lab sessions.
- Do not commit or public-sync without explicit instruction.
- Frida/input probing remains lab-only and requires explicit operator intent.
- Sensitive keywords such as cyber, Frida, hooking, process memory, input API,
  pentest, malware, anti-cheat, exploit, token, credential, or exfiltration
  trigger a boundary check, not panic and not blind execution. See
  `docs/SAFETY_BOUNDARIES.md`.

















