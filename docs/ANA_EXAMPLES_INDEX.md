# ANA Examples Index

Last updated: 2026-05-31

Purpose: list real ANA examples, what they prove, and whether they are private
lab material or safe to sanitize later.

## Rules

- Examples must prove behavior with evidence, not hype.
- Private reports stay private unless sanitized.
- Security-lab examples must remove operational details before sharing.
- Local paths, screenshots, logs, memory, `.env`, and session history are
  private by default.
- Public-safe examples should show structure and outcomes, not private machine
  state.
- Use placeholders such as `<n>` or `<timestamp>` for volatile counters and
  filenames that change after every checkpoint, gate, or memory dry-run. Keep
  stable verdicts and shapes exact.

## Example Catalog

| Example | File / Source | Profile | Share class | Proves | Notes |
| --- | --- | --- | --- | --- | --- |
| Bug report template | `docs/templates/BUG_REPORT_TEMPLATE.md` | `core` | public-safe | ANA has a clear QA reporting format. | Safe to share. |
| Autonomy warning bug example | `docs/examples/BUG_REPORT_EXAMPLE_ANA_AUTONOMY_WARN.md` | `windows` | sanitized | ANA records limitations instead of hiding warnings. | Review local paths before sharing. |
| Autonomy warning follow-up example | `docs/examples/AUTONOMY_RUNNER_WARN_FOLLOWUP_EXAMPLE.md` | `core/windows` | sanitized | ANA interprets `WARN` as a diagnostic state with next actions. | Documents response, not a runtime fix. |
| Autonomy runner pass contract example | `docs/examples/AUTONOMY_RUNNER_PASS_CONTRACT_EXAMPLE.md` | `core/windows` | sanitized | ANA's autonomy loop uses a safe read-only stack, avoids desktop control/Frida, and carries Patch Advisor dirty-tree evidence. | Current clean run is PASS; stale live behavior remains a documented diagnostic scenario. |
| Autonomy runner checkpoint example | `docs/examples/AUTONOMY_RUNNER_CHECKPOINT_EXAMPLE.md` | `core/private_lab` | private-lab, sanitizable | ANA can optionally save a compact session checkpoint after an autonomy pass. | Actual checkpoint files stay private. |
| Nucleus Smoke summary example | `docs/examples/NUCLEUS_SMOKE_SUMMARY_EXAMPLE.md` | `core` | sanitized | ANA proves the core observe-route-context-verify-audit loop is alive. | Readiness check, not full regression. |
| MCP tools/list coverage example | `docs/examples/MCP_TOOLS_LIST_COVERAGE_EXAMPLE.md` | `core` | sanitized | The live MCP server exposes 90 active tools after reload and all required nucleus tools through `tools/list`. | Visibility, not behavior. |
| MCP tools/call failure normalization example | `docs/examples/MCP_TOOLS_CALL_FAILURE_NORMALIZATION_EXAMPLE.md` | `core` | sanitized | ANA returns compact JSON and non-zero exit for a missing tool call. | Protocol wrapper behavior, not tool semantics. |
| MCP schema lookup example | `docs/examples/MCP_SCHEMA_LOOKUP_EXAMPLE.md` | `core/security_lab` | sanitized | ANA inspects a tool contract before execution and reports missing tools cleanly. | Schema visibility, not runtime behavior. |
| Live MCP reload verification example | `docs/examples/LIVE_MCP_RELOAD_VERIFICATION_EXAMPLE.md` | `core/private_lab` | private-lab, sanitizable | ANA checks whether live MCP has loaded updated tool code after file edits. | Presence of `stale` proves new graph stats code is active. |
| Live MCP reload checker | `ANA_MAX/dev_artifacts/scripts/ana_live_reload_check.py` | `core/private_lab` | private-lab, sanitizable | ANA emits PASS/WARN depending on whether live MCP exposes the expected reload marker. | Use after server restart/reload. |
| Live behavior checker | `docs/examples/LIVE_BEHAVIOR_CHECK_EXAMPLE.md` | `core/private_lab` | private-lab, sanitizable | ANA detects when MCP is online but selected live tool behavior is stale. | Current probe checks `session_audit` identity fields and `error_radar` runtime behavior; `--allow-warn` is collection-only. |
| Reload readiness preflight example | `docs/examples/RELOAD_READINESS_PREFLIGHT_EXAMPLE.md` | `core/private_lab` | private-lab, sanitizable | ANA checks whether reload is useful and inspects port/process context without stopping anything. | Read-only; operator performs restart. |
| Reload consistency check example | `docs/examples/RELOAD_CONSISTENCY_CHECK_EXAMPLE.md` | `core/private_lab` | private-lab, sanitizable | ANA verifies reload diagnostics agree before action work. | Aligned WARN before restart is acceptable; disagreement is a repair signal. |
| Post-reload verify example | `docs/examples/POST_RELOAD_VERIFY_EXAMPLE.md` | `core/private_lab` | private-lab, sanitizable | ANA verifies live reload marker, tool surface, identity surface, live behavior, Nucleus Smoke, and lab state summary after an operator restart. | Read-only; use immediately after reload. |
| Operator status example | `docs/examples/OPERATOR_STATUS_EXAMPLE.md` | `core/private_lab` | private-lab, sanitizable | ANA prints current VSIX, MCP readiness, reload marker, tool surface, live behavior, identity surface, checkpoint, latest REM report, and next commands. | Current clean example ends with one scoped lab action. |
| VSIX version consistency example | `docs/examples/VSIX_VERSION_CONSISTENCY_EXAMPLE.md` | `core/private_lab` | private-lab, sanitizable | ANA checks active install/operator docs match `vscode_extension/package.json`. | Historical changelog/checkpoints are excluded. |
| Lab VSIX install helper example | `docs/examples/LAB_VSIX_INSTALL_HELPER_EXAMPLE.md` | `windows/private_lab` | private-lab, sanitizable | ANA provides a dry-run-first helper for installing the latest packaged lab VSIX. | Does not reload VS Code automatically. |
| Lab Quality Gate summary example | `docs/examples/LAB_QUALITY_GATE_SUMMARY_EXAMPLE.md` | `core` | sanitized | ANA verifies compile, focused tests, governance, manifest coverage, extension syntax, MCP health, and smoke. | Heavier than Nucleus Smoke. |
| No-reload Quality Gate summary example | `docs/examples/NO_RELOAD_QUALITY_GATE_SUMMARY_EXAMPLE.md` | `core/windows` | sanitized | ANA verifies extension/runtime health without reinstalling VSIX or reloading the IDE. | Fast confidence, not full regression. |
| Lab state summary example | `docs/examples/LAB_STATE_SUMMARY_EXAMPLE.md` | `core/private_lab` | private-lab, sanitizable | ANA summarizes MCP readiness, live reload status, tool surface, live behavior, identity surface, memory hygiene, archive plan count, and dirty tree. | Current clean example shows reload/behavior PASS; summary only, not full gate. |
| File activity snapshot example | `docs/examples/FILE_ACTIVITY_SNAPSHOT_EXAMPLE.md` | `private_lab` | private-lab, sanitizable | ANA detects created/deleted/modified files under an authorized root using metadata-only snapshots. | Not continuous; baseline must exist first. |
| Linux readiness summary example | `docs/examples/LINUX_READINESS_SUMMARY_EXAMPLE.md` | `linux` | sanitized | ANA tracks Windows-first blockers before Linux/Mate migration. | Static scan, not runtime proof. |
| Permission manifest coverage example | `docs/examples/PERMISSION_MANIFEST_COVERAGE_EXAMPLE.md` | `core` | sanitized | Runtime tools and permission manifest match exactly. | Coverage, not full policy correctness. |
| Permission manifest reload example | `docs/examples/PERMISSION_MANIFEST_RELOAD_EXAMPLE.md` | `core` | sanitized | ANA reloads permission policy when the manifest file changes. | Uses temporary test manifest. |
| Permission blocked action example | `docs/examples/PERMISSION_BLOCKED_ACTION_EXAMPLE.md` | `security_lab` | sanitized | ANA blocks a confirmation-gated tool when `confirm=true` is missing. | Policy block, not runtime diagnostics. |
| Permission inactive profile block example | `docs/examples/PERMISSION_INACTIVE_PROFILE_BLOCK_EXAMPLE.md` | `core/security_lab` | sanitized | ANA blocks a tool when its profile is inactive, even if the individual tool is allowed. | Uses temporary test manifest. |
| Governance check summary example | `docs/examples/GOVERNANCE_CHECK_SUMMARY_EXAMPLE.md` | `core` | sanitized | ANA enforces docs, profiles, no-hype rules, manifest structure, and confirmation boundaries. | Policy consistency, not runtime proof. |
| Tool Router recommendation example | `docs/examples/TOOL_ROUTER_RECOMMENDATION_EXAMPLE.md` | `core` | sanitized | ANA chooses a compact task-specific tool stack instead of using all tools blindly. | Recommendation only, not execution. |
| Agent Coach recommendation example | `docs/examples/AGENT_COACH_RECOMMENDATION_EXAMPLE.md` | `core/private_lab` | sanitized | ANA turns telemetry and router output into a concrete next action after failures. | Severity depends on recent telemetry. |
| Codex Companion example | `docs/examples/CODEX_COMPANION_EXAMPLE.md` | `core/private_lab` | private-lab, sanitizable | ANA observes, routes, coaches, context-packs, and challenges Codex before scoped work. | This is the Codex-first anti-blind-work bridge. |
| Error Radar finding example | `docs/examples/ERROR_RADAR_FINDING_EXAMPLE.md` | `core` | sanitized | ANA turns logs and git state into prioritized findings with a next step. | Confirm whether log findings are still active. |
| Dirty Tree Report | `ANA_MAX/dev_artifacts/scripts/ana_dirty_tree_report.py` | `core/private_lab` | private-lab, sanitizable | ANA classifies large dirty trees into active work and generated/memory noise without mutating files. | Use before commit/archive decisions. |
| Patch Advisor example | `docs/examples/PATCH_ADVISOR_EXAMPLE.md` | `core/private_lab` | private-lab, sanitizable | ANA converts diagnostics into suggest-only patch advice with confidence and policy. | Does not apply code; Codex/operator reviews. |
| Review Batch Runner example | `docs/examples/REVIEW_BATCH_RUNNER_EXAMPLE.md` | `core/private_lab` | private-lab, sanitizable | ANA previews or runs the focused verification commands from Dirty Tree review batches. | Dry-run by default; no shell; Python review commands only. |
| Web research tool smoke example | `docs/examples/WEB_RESEARCH_TOOL_SMOKE_EXAMPLE.md` | `core/private_lab` | private-lab, sanitizable | ANA verifies controlled web fetch/scrape research and records missing search dependency as a tool-health finding. | Prefer exact official docs URLs over broad search. |
| Code Context Pack example | `docs/examples/CODE_CONTEXT_PACK_EXAMPLE.md` | `core/windows` | sanitized | ANA combines UI snapshot, Code Map, Graph Map, and compressed state before editing. | Context selection, not permission to patch. |
| Graph Context Pack example | `docs/examples/GRAPH_CONTEXT_PACK_EXAMPLE.md` | `core` | sanitized | ANA expands context by graph relationships around files, tests, symbols, and neighbors. | Use after Code Map for expansion. |
| Code Map query example | `docs/examples/CODE_MAP_QUERY_EXAMPLE.md` | `core` | sanitized | ANA finds exact source context from compact summaries. | Refresh map after adding new scripts. |
| Code Map incremental refresh example | `docs/examples/CODE_MAP_INCREMENTAL_REFRESH_EXAMPLE.md` | `core` | sanitized | ANA skips unchanged files on refresh using index metadata. | Uses mtime and size. |
| Graph Map query example | `docs/examples/GRAPH_MAP_QUERY_EXAMPLE.md` | `core` | sanitized | ANA retrieves relationship-aware graph context and records routing limits. | Use after Code Map for expansion. |
| Graph Map refresh example | `docs/examples/GRAPH_MAP_REFRESH_EXAMPLE.md` | `core` | sanitized | ANA builds graph.json, GRAPH_REPORT.md, and graph.html from Code Map summaries. | Prefer Refresh Context Maps for both maps. |
| Graph blast-radius example | `docs/examples/GRAPH_BLAST_RADIUS_EXAMPLE.md` | `core/private_lab` | private-lab, sanitizable | ANA estimates affected files/tests/docs from changed files and downranks graph noise. | Depends on fresh Code Map / Graph Map. |
| Code/Graph stale map handling example | `docs/examples/CODE_GRAPH_STALE_MAP_HANDLING_EXAMPLE.md` | `core` | sanitized | ANA rebuilds Graph Map when Code Map has changed since the graph was built. | Live MCP sees it after reload. |
| Session Audit trust example | `docs/examples/SESSION_AUDIT_TRUST_EXAMPLE.md` | `core` | sanitized | ANA explains confidence from context, schema, and verification signals. | Score is evidence, not guarantee. |
| Trace report example | `docs/examples/TRACE_REPORT_EXAMPLE.md` | `core/private_lab` | private-lab, sanitizable | ANA validates Autonomy Runner trace spans and confirms steps/spans alignment. | Report-local traces only for now. |
| Session Checkpoint example | `docs/examples/SESSION_CHECKPOINT_EXAMPLE.md` | `core/private_lab` | private-lab, sanitizable | ANA saves compact handoff state for future sessions and memory retrieval. | Keep compact; avoid raw private data. |
| Session Checkpoint preserves notes example | `docs/examples/SESSION_CHECKPOINT_PRESERVES_NOTES_EXAMPLE.md` | `core/private_lab` | private-lab, sanitizable | ANA updates latest checkpoint pointer without deleting appended operator notes. | Live MCP and local lanes should preserve notes after clean reload. |
| Local checkpoint lane example | `docs/examples/LOCAL_CHECKPOINT_FALLBACK_EXAMPLE.md` | `core/private_lab` | private-lab, sanitizable | ANA can save checkpoint through local source for deterministic handoff continuity. | Useful during reload diagnostics; safe as Activity Bar checkpoint path. |
| Session REM Sleep example | `docs/examples/SESSION_REM_SLEEP_EXAMPLE.md` | `core/private_lab` | private-lab, sanitizable | ANA summarizes recent checkpoints, telemetry, friction, and next-session rules. | Retrospective guidance, not live proof. |
| Session Lifecycle example | `docs/examples/SESSION_LIFECYCLE_EXAMPLE.md` | `core/private_lab` | private-lab, sanitizable | ANA coordinates wake, recommend, and rest preview/consolidation flows. | Orchestrator; validates underlying tools separately. |
| Memory hygiene report example | `docs/examples/MEMORY_HYGIENE_REPORT_EXAMPLE.md` | `private_lab` | private-lab, sanitizable | ANA reports checkpoint/REM volume and archive candidates without modifying files. | Read-only cleanup planning. |
| Memory archive dry-run example | `docs/examples/MEMORY_ARCHIVE_DRY_RUN_EXAMPLE.md` | `private_lab` | private-lab, sanitizable | ANA creates a guarded archive plan with hashes and explicit apply confirmation. | Dry-run by default; no delete. |
| Binary Map static analysis example | `docs/examples/BINARY_MAP_STATIC_ANALYSIS_EXAMPLE.md` | `security_lab` | sanitized | ANA extracts static PE metadata, imports, sections, strings, and hash without executing the file. | Static-only; no process attach. |
| Input API Probe spec example | `docs/examples/INPUT_API_PROBE_SPEC_EXAMPLE.md` | `security_lab` | lab-only, sanitizable | ANA generates a confirmation-gated aggregate-only Windows input API probe spec without execution. | No raw key storage or character decoding. |
| Runtime deep router escalation example | `docs/examples/RUNTIME_DEEP_ROUTER_ESCALATION_EXAMPLE.md` | `security_lab/windows` | sanitized | ANA routes under-the-hood diagnostics through health, events, static binary analysis, and guarded specs before invasive tools. | Recommendation only; no process attach. |
| Tool Healthcheck summary example | `docs/examples/TOOL_HEALTHCHECK_SUMMARY_EXAMPLE.md` | `core` | sanitized | ANA verifies a compact safe stack before deeper diagnostics. | Quick health, not full regression. |
| Tool profile summary example | `docs/examples/TOOL_PROFILE_SUMMARY_EXAMPLE.md` | `core` | sanitized | ANA classifies tools by profile, tier, confirmation, and lab boundary. | Summary only, full table stays private-lab. |
| Dashboard local HTML example | `docs/examples/DASHBOARD_LOCAL_HTML_EXAMPLE.md` | `windows` | sanitized | Open Dashboard generates local HTML from live MCP data instead of relying on port `8787`. | Visual rendering depends on local browser. |
| Tool profile report | `ANA_MAX/memory/tool_profiles/TOOL_PROFILE_REPORT.md` | `core` | private-lab, sanitizable | All tools are classified by profile/tier/confirmation. | Sanitize tool list if needed. |
| Nucleus Smoke report | `ANA_MAX/dev_artifacts/reports/nucleus_smoke_*.json` | `core` | private-lab, sanitizable | Health, routing, context, verification, trust checks run. | Use latest summary only for public. |
| Autonomy Pass report | `ANA_MAX/dev_artifacts/reports/autonomy_runner_*.json` | `core/windows` | private-lab, sanitizable | Observe-route-context-verify-audit loop works. | Do not share UI details/screenshots. |
| Lab Quality Gate report | `ANA_MAX/dev_artifacts/reports/lab_quality_gate_*.json` | `core` | private-lab, sanitizable | Compile/tests/MCP/gates pass together. | Share summary, not full local paths. |
| No-reload Quality Gate report | `ANA_MAX/dev_artifacts/reports/no_reload_quality_gate_*.json` | `core/windows` | private-lab | Extension/runtime checks pass without reinstall/reload. | Useful internally before package work. |
| Permission manifest coverage | `ANA_MAX/dev_artifacts/reports/permission_manifest_coverage_*.json` | `core` | sanitizable | Runtime tools and policy manifest match. | Good serious-project evidence. |
| Governance check report | `ANA_MAX/dev_artifacts/reports/governance_check_*.json` | `core` | sanitizable | Docs/profile/no-hype rules are enforced. | Good public-safe summary candidate. |
| Linux readiness report | `ANA_MAX/dev_artifacts/reports/linux_readiness_*.json` | `linux` | private-lab, sanitizable | Windows-first blockers are tracked for Linux move. | Share only aggregate counts. |
| Linux restore flow | `README_RESTORE_ON_LINUX.md`, `LINUX_START_HERE.md` | `linux/private_lab` | private-lab | Full migration path exists. | Contains private migration context. |
| Mobile integrity QA case study | `C:\Users\billy\Desktop\cvnou\CASE_STUDY_Mobile_Game_Integrity_QA_Sanitized.md` | `security_lab` | sanitized | Whitehat mobile QA thinking. | Keep exploit details removed. |

## Share Classes

### `public-safe`

Can be shared after a quick review. Should not contain secrets, local user
paths, raw logs, screenshots, memory, or private session details.

### `sanitized`

Safe only after redaction/rewrite. Keep the method and outcome, remove private
machine state and operational security details.

### `private-lab`

Do not share. Use internally for Billy + Codex + ANA continuity.

## Public-Safe Summary Pattern

When an example needs to be shown outside the lab, prefer this shape:

```text
What was tested:
Evidence used:
Result:
Limitation:
Next step:
```

Avoid:

```text
raw logs
screenshots
private local paths
tokens/secrets
exploit steps
personal machine state
```

## Next Examples To Add

- Real post-reload PASS evidence after the next operator MCP restart.
