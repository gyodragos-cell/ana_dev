# ANA Lab Docs Index

Last updated: 2026-06-01

Purpose: keep all important documentation discoverable from `docs/` without
physically moving active root files that old scripts, READMEs, or agent rules
still reference.

## Read First

1. `AGENTS.md`
2. `docs/ANA_LAB_MASTER_CONTEXT.md`
3. `docs/ANA_CODEX_GOLDEN_RULE.md`
4. `docs/CODEX_LAB_MANAGER_PROMPT.md`
5. `docs/ANA_LAB_LLM_INDEX.md`
6. `docs/AGENT_MEMORY.md`
7. `ANA_MAX/docs/CURRENT_SESSION_HANDOFF.md`
8. `docs/ANA_LAB_PROJECT_HISTORY.md`

## Core Lab Docs In `docs/`

- `docs/LAB_README.md` - professional overview and current lab verification.
- `docs/ANA_CODEX_GOLDEN_RULE.md` - ANA-first rule so Codex does not work blind.
- `docs/SAFETY_BOUNDARIES.md` - safety, public/private boundaries, and sensitive keyword trigger handling.
- `docs/CODEX_LAB_MANAGER_PROMPT.md` - full operating prompt for Codex/agent sessions.
- `docs/ANA_LAB_MASTER_CONTEXT.md` - single-file current lab context.
- `docs/ANA_LAB_LLM_INDEX.md` - compact machine-oriented index for Codex, ANA, and future local agents.
- `docs/ANA_LAB_PROJECT_HISTORY.md` - Billy + Codex + ANA project story.
- `docs/LAB_WORKSPACE_STRUCTURE.md` - clean workspace rules.
- `docs/LINUX_MATE_MIGRATION_LANE.md` - future Linux Mate mirror plan and portability rules.
- `docs/ANA_SERIOUS_PROJECT_RULES.md` - no-hype rules, claims boundary, evidence rule, and serious lab discipline.
- `docs/ANA_RESEARCH_INTAKE_2026-05-31.md` - filtered web/GitHub research intake and lab-native follow-up decisions.
- `docs/ANA_AGENT_TRACE_SCHEMA.md` - local-first trace span vocabulary for agent runs, tool calls, verification, audit, and checkpoints.
- `docs/ANA_PROFILE_MANIFEST.md` - core/windows/linux/security_lab/public_safe/private_lab profile definitions.
- `docs/ANA_EXAMPLES_AND_TESTS_CHECKLIST.md` - real examples and tests required before broader claims.
- `docs/ANA_EXAMPLES_INDEX.md` - catalog of real examples, evidence, profiles, and share classes.
- `docs/examples/WEB_RESEARCH_TOOL_SMOKE_EXAMPLE.md` - controlled web fetch/scrape tool smoke and research-note pattern.
- `docs/examples/GRAPH_BLAST_RADIUS_EXAMPLE.md` - graph-based changed-file blast-radius example.
- `docs/examples/CONTEXT_MAP_REFRESH_EXAMPLE.md` - one-command Code Map and Graph Map refresh lane.
- `docs/examples/TRACE_REPORT_EXAMPLE.md` - Autonomy Runner trace span validation example.
- `docs/examples/ERROR_RADAR_FINDING_EXAMPLE.md` - Error Radar large dirty-tree
  finding and Dirty Tree Report follow-up flow.
- `docs/examples/PATCH_ADVISOR_EXAMPLE.md` - suggest-only repair advice with local Dirty Tree and graph blast-radius context.
- `docs/examples/REVIEW_BATCH_RUNNER_EXAMPLE.md` - dry-run-first runner for
  focused Dirty Tree review-batch verification commands.
- `docs/examples/AUTONOMY_RUNNER_PASS_CONTRACT_EXAMPLE.md` - autonomy pass contract, Patch Advisor dirty-tree signal, and aligned trace example.
- `docs/examples/LAB_STATE_SUMMARY_EXAMPLE.md` - compact lab status example with reload and trace alignment.
- `docs/examples/FILE_ACTIVITY_SNAPSHOT_EXAMPLE.md` - aggregate created/deleted/modified file detection for an authorized root.
- `docs/examples/IDENTITY_SURFACE_CHECK_EXAMPLE.md` - Codex-first active identity surface check.
- `docs/examples/LIVE_BEHAVIOR_CHECK_EXAMPLE.md` - detects a healthy but stale
  live MCP process by checking selected tool behavior fields; includes strict
  exit behavior and collection-only `--allow-warn`.
- `docs/examples/RELOAD_READINESS_PREFLIGHT_EXAMPLE.md` - read-only preflight
  for deciding whether VS Code/MCP reload or restart is useful.
- `docs/examples/RELOAD_CONSISTENCY_CHECK_EXAMPLE.md` - verifies reload-facing
  diagnostics agree before action work.
- `docs/examples/POST_RELOAD_VERIFY_EXAMPLE.md` - verifies the live server
  after operator reload/restart.
- `docs/examples/MEMORY_ARCHIVE_DRY_RUN_EXAMPLE.md` - safe dry-run and
  readiness workflow for archiving old checkpoints/REM reports without moving
  files by default.
- `docs/ANA_OPERATOR_RELOAD_RUNBOOK.md` - operator flow for VSIX install,
  VS Code reload, MCP restart, and Post-Reload Verify.
- `docs/templates/BUG_REPORT_TEMPLATE.md` - generic QA/ANA bug report template.
- `docs/examples/BUG_REPORT_EXAMPLE_ANA_AUTONOMY_WARN.md` - sanitized example bug report from current ANA lab behavior.
- `docs/NEXT_SESSION_BOOTSTRAP.md` - detailed next-session checklist.
- `docs/AGENT_MEMORY.md` - durable agent memory.
- `docs/PUBLIC_RELEASE_SYNC_BACKLOG.md` - parking lot for possible future public sync.
- `docs/MCP_AGENT_READINESS_CONTRACT.md` - MCP readiness expectations.
- `docs/MCP_TOOL_ORCHESTRATION_PLAN.md` - tool routing/orchestration plan.
- `docs/TOOL_MATRIX.md` - tool status/methodology.
- `docs/AGENT_STEROID_TOOLS.md` - high-leverage lab tools and boundaries.

## Current Lab Scripts

- `ANA_MAX/dev_artifacts/scripts/ana_codex_companion.py` - anti-blind-work
  bridge where ANA observes, routes, coaches, context-packs, checks Error
  Radar, and challenges Codex before scoped work.
- `ANA_MAX/dev_artifacts/scripts/ana_nucleus_smoke.py` - one-button nucleus
  health and context smoke check.
- `ANA_MAX/dev_artifacts/scripts/ana_refresh_context_maps.py` - one-command
  Code Map then Graph Map refresh with final freshness verification.
- `ANA_MAX/dev_artifacts/scripts/ana_autonomy_runner.py` - lab-safe autonomy
  pass: observe, route, context-pack, verify, audit, and optional checkpoint.
- `ANA_MAX/dev_artifacts/scripts/ana_trace_report.py` - validates compact
  Autonomy Runner trace spans and writes a local alignment report.
- `ANA_MAX/dev_artifacts/scripts/ana_patch_advisor.py` - suggest-only repair
  advisor that combines diagnostics with local Dirty Tree and Graph Map
  blast-radius evidence.
- `ANA_MAX/dev_artifacts/scripts/ana_lab_state_summary.py` - compact operator
  state summary with MCP readiness, reload status, trace alignment, dirty tree,
  and memory hygiene counts.
- `ANA_MAX/dev_artifacts/scripts/ana_reload_readiness.py` - read-only preflight
  that decides reload usefulness from marker, tool surface, and live behavior.
- `ANA_MAX/dev_artifacts/scripts/ana_live_behavior_check.py` - selected
  behavior freshness check; strict by default, `--allow-warn` only for
  diagnostic collection.
- `ANA_MAX/dev_artifacts/scripts/ana_reload_consistency_check.py` - read-only
  guard that compares Reload Readiness, Operator Status, Lab State, and
  Post-Reload Verify.
- `ANA_MAX/dev_artifacts/scripts/ana_post_reload_verify.py` - read-only
  verification bundle for after operator reload/restart.
- `ANA_MAX/dev_artifacts/scripts/ana_file_activity_snapshot.py` - privacy
  preserving snapshot diff for created/deleted/modified files under an
  authorized root.
- `ANA_MAX/dev_artifacts/scripts/ana_dirty_tree_report.py` - read-only git
  dirty tree classifier for separating active work from checkpoints, REM
  reports, memory, and generated lab artifacts.
- `ANA_MAX/dev_artifacts/scripts/ana_review_batch_runner.py` - dry-run-first
  runner for the Python verification commands suggested by Dirty Tree review
  batches.
- `ANA_MAX/dev_artifacts/scripts/ana_memory_archive.py` - dry-run-first memory
  hygiene planner with readiness and post-apply verification; apply requires
  explicit `ARCHIVE_OLD_MEMORY` confirmation.
- `ANA_MAX/dev_artifacts/scripts/ana_identity_surface_check.py` - scans active
  identity files for Codex-first neutral wording and external-tool promotion
  drift.
- `ANA_MAX/dev_artifacts/scripts/ana_linux_readiness.py` - static checker for
  future Linux Mate readiness and Windows-profile separation.
- `ANA_MAX/dev_artifacts/scripts/ana_governance_check.py` - checks serious
  project docs and profile manifest terms.
- `ANA_MAX/dev_artifacts/scripts/ana_permission_manifest_coverage.py` - compares
  runtime-registered tools against `permission_manifest.json` so every live tool
  has an explicit policy/profile entry.
- `ANA_MAX/dev_artifacts/scripts/ana_tool_profile_report.py` - generates JSON
  and Markdown reports from `permission_manifest.json`.
- `ANA_MAX/dev_artifacts/scripts/lab_quality_gate.py` - broader developer
  quality gate before/after larger changes.
- `ANA_MAX/dev_artifacts/scripts/install_latest_lab_vsix.ps1` - dry-run-first
  operator helper for installing the latest packaged lab VSIX.

## Root Docs Kept In Place On Purpose

These are still at repo root because existing docs/scripts refer to those exact
paths. Do not move them until references are updated deliberately.

- `AGENTS.md`
- `README.md`
- `AGENT_START_HERE.md`
- `AI_AGENT_OPERATOR_RULES.md`
- `SAFE_AGENT_RULES.md`
- `PUBLIC_NAMING_POLICY.md`
- `DESKTOP_PROJECT_MAP.md`
- `ANA_MAX_V22_ARCHITECTURE.md`
- `ENGINEER_WOW_DEMO.md`
- `INDEX.md`
- `START_HERE_VOICE_SYSTEM.md`
- `TASK_7_COMPLETION_CHECKLIST.md`
- `VOICE_FIX_SUMMARY_FOR_BILLY.md`

## ANA_MAX Package Docs Kept In Place

These belong to the ANA runtime package area and should stay there unless the
package layout is intentionally changed.

- `ANA_MAX/AGENTS.md`
- `ANA_MAX/README.md`
- `ANA_MAX/CHANGELOG.md`
- `ANA_MAX/HYBRID_MCP_CONFIG.md`
- `ANA_MAX/LAB_MANAGER.md`
- `ANA_MAX/LOG.md`
- `ANA_MAX/TOOL_STATUS.md`

## VS Code Extension Docs Kept In Place

These are used by extension packaging and marketplace/readme context.

- `vscode_extension/README.md`
- `vscode_extension/CHANGELOG.md`
- `vscode_extension/LICENSE.md`
- `vscode_extension/MARKETPLACE.md`

## Generated/Private Docs And Memory

Do not public-sync these without review:

- `ANA_MAX/docs/SESSION_CHECKPOINT_*.md`
- `ANA_MAX/docs/rem_sleep/REM_SLEEP_REPORT_*.md`
- `ANA_MAX/memory/code_map/*.summary.md`
- `ANA_MAX/memory/graph_map/GRAPH_REPORT.md`
- `ANA_MAX/memory/tool_profiles/TOOL_PROFILE_REPORT.md`
- `ANA_MAX/dev_artifacts/reports/*.json`
- `ANA_MAX/dev_artifacts/audit/*.json`

## Archived Artifacts

Generated packages, old VSIX build folders, old root artifacts, and root media
were archived here instead of deleted:

```text
ANA_MAX/dev_artifacts/archives/workspace_cleanup_20260529/
```

This archive is ignored by Git and exists only for rollback/reference.

## Cleanup Rule

If a document is actively referenced by scripts, root README, extension
packaging, or agent instructions, keep it where it is and list it here. If it is
new durable lab guidance, put it directly under `docs/`.
