# ANA Examples And Tests Checklist

Last updated: 2026-06-01

Purpose: track the real examples and tests ANA needs before it can be called
serious, useful, or ready for broader testing.

## Required Examples

| Example | Status | Evidence |
| --- | --- | --- |
| Nucleus Smoke output | ready | `docs/examples/NUCLEUS_SMOKE_SUMMARY_EXAMPLE.md`, `ANA_MAX/dev_artifacts/reports/nucleus_smoke_*.json` |
| Autonomy Pass output | ready | `ANA_MAX/dev_artifacts/reports/autonomy_runner_*.json` |
| Autonomy Pass contract | ready | `docs/examples/AUTONOMY_RUNNER_PASS_CONTRACT_EXAMPLE.md`, `tests/runtime/test_ana_autonomy_runner.py` |
| Autonomy Pass checkpoint | ready | `docs/examples/AUTONOMY_RUNNER_CHECKPOINT_EXAMPLE.md`, `test_run_autonomy_pass_can_write_optional_checkpoint` |
| Autonomy Pass warning follow-up | ready | `docs/examples/AUTONOMY_RUNNER_WARN_FOLLOWUP_EXAMPLE.md` |
| MCP tools/list coverage | ready | `docs/examples/MCP_TOOLS_LIST_COVERAGE_EXAMPLE.md`, `ana_nucleus_smoke.py` |
| MCP tools/call failure normalization | ready | `docs/examples/MCP_TOOLS_CALL_FAILURE_NORMALIZATION_EXAMPLE.md`, `tests/runtime/test_ana_mcp_call.py` |
| MCP schema lookup | ready | `docs/examples/MCP_SCHEMA_LOOKUP_EXAMPLE.md`, `ana_mcp_call.py --schema input_api_probe` |
| Live MCP reload verification | ready | `docs/examples/LIVE_MCP_RELOAD_VERIFICATION_EXAMPLE.md`, `graph_context_pack action=stats` |
| Live MCP reload checker | ready | `ANA_MAX/dev_artifacts/scripts/ana_live_reload_check.py`, `tests/runtime/test_ana_live_reload_check.py` |
| Live behavior checker | ready | `docs/examples/LIVE_BEHAVIOR_CHECK_EXAMPLE.md`, `tests/runtime/test_ana_live_behavior_check.py` |
| Live behavior collection mode | ready | `ana_live_behavior_check.py --allow-warn`, `tests/runtime/test_ana_live_behavior_check.py::test_live_behavior_allow_warn_returns_success_for_operator_collection` |
| Lab Quality Gate output | ready | `docs/examples/LAB_QUALITY_GATE_SUMMARY_EXAMPLE.md`, `ANA_MAX/dev_artifacts/reports/lab_quality_gate_*.json` |
| No-reload Quality Gate output | ready | `docs/examples/NO_RELOAD_QUALITY_GATE_SUMMARY_EXAMPLE.md`, `ANA_MAX/dev_artifacts/scripts/no_reload_quality_gate.py` |
| No-reload advisory behavior | ready | `tests/runtime/test_no_reload_quality_gate.py` |
| Permission manifest coverage | ready | `docs/examples/PERMISSION_MANIFEST_COVERAGE_EXAMPLE.md`, `ANA_MAX/dev_artifacts/scripts/ana_permission_manifest_coverage.py` |
| Governance check | ready | `docs/examples/GOVERNANCE_CHECK_SUMMARY_EXAMPLE.md`, `ANA_MAX/dev_artifacts/scripts/ana_governance_check.py` |
| Tool Router recommendation | ready | `docs/examples/TOOL_ROUTER_RECOMMENDATION_EXAMPLE.md`, `tool_router mode=code_change` |
| Agent Coach recommendation | ready | `docs/examples/AGENT_COACH_RECOMMENDATION_EXAMPLE.md`, `agent_coach action=recommend` |
| Codex Companion | ready | `docs/examples/CODEX_COMPANION_EXAMPLE.md`, `tests/runtime/test_ana_codex_companion.py` |
| Error Radar finding | ready | `docs/examples/ERROR_RADAR_FINDING_EXAMPLE.md`, `error_radar limit=20` |
| Dirty Tree Report | ready | `ANA_MAX/dev_artifacts/scripts/ana_dirty_tree_report.py`, `tests/runtime/test_ana_dirty_tree_report.py` |
| Patch Advisor suggestion | ready | `docs/examples/PATCH_ADVISOR_EXAMPLE.md`, `ANA_MAX/dev_artifacts/scripts/ana_patch_advisor.py` |
| Web research tool smoke | ready | `docs/examples/WEB_RESEARCH_TOOL_SMOKE_EXAMPLE.md`, `web_fetch`, `web_scraper`, `web_search` dependency finding |
| Code Context Pack | ready | `docs/examples/CODE_CONTEXT_PACK_EXAMPLE.md`, `code_context_pack include_graph=true` |
| Graph Context Pack | ready | `docs/examples/GRAPH_CONTEXT_PACK_EXAMPLE.md`, `graph_context_pack action=query` |
| Code Map query | ready | `docs/examples/CODE_MAP_QUERY_EXAMPLE.md`, `ANA_MAX/dev_artifacts/scripts/ana_code_map.py query ...` |
| Code Map incremental refresh | ready | `docs/examples/CODE_MAP_INCREMENTAL_REFRESH_EXAMPLE.md`, `tests/runtime/test_ana_code_map.py` |
| Graph Map query | ready | `docs/examples/GRAPH_MAP_QUERY_EXAMPLE.md`, `ANA_MAX/dev_artifacts/scripts/ana_graph_map.py query ...` |
| Graph Map refresh | ready | `docs/examples/GRAPH_MAP_REFRESH_EXAMPLE.md`, `tests/runtime/test_ana_graph_map.py` |
| Graph blast-radius | ready | `docs/examples/GRAPH_BLAST_RADIUS_EXAMPLE.md`, `tests/runtime/test_ana_graph_map.py` |
| Code/Graph stale map handling | ready | `docs/examples/CODE_GRAPH_STALE_MAP_HANDLING_EXAMPLE.md`, `tests/runtime/test_graph_context_pack_tool.py` |
| Linux restore flow | ready | `README_RESTORE_ON_LINUX.md`, `LINUX_START_HERE.md` |
| Linux readiness report | ready | `docs/examples/LINUX_READINESS_SUMMARY_EXAMPLE.md`, `ANA_MAX/dev_artifacts/reports/linux_readiness_*.json` |
| Permission manifest reload | ready | `docs/examples/PERMISSION_MANIFEST_RELOAD_EXAMPLE.md`, `test_permission_manifest_reloads_when_file_changes` |
| Permission blocked action | ready | `docs/examples/PERMISSION_BLOCKED_ACTION_EXAMPLE.md`, `input_api_probe operation=list_authorized` without `confirm=true` |
| Permission inactive profile block | ready | `docs/examples/PERMISSION_INACTIVE_PROFILE_BLOCK_EXAMPLE.md`, `test_permission_manifest_profiles_can_block_inactive_profile` |
| Sanitized mobile QA case study | ready | `C:\Users\billy\Desktop\cvnou\CASE_STUDY_Mobile_Game_Integrity_QA_Sanitized.md` |
| Bug report template | ready | `docs/templates/BUG_REPORT_TEMPLATE.md` |
| Sanitized bug report example | ready | `docs/examples/BUG_REPORT_EXAMPLE_ANA_AUTONOMY_WARN.md` |
| Session Audit trust example | ready | `docs/examples/SESSION_AUDIT_TRUST_EXAMPLE.md`, `session_audit action=trust` |
| Trace report example | ready | `docs/examples/TRACE_REPORT_EXAMPLE.md`, `tests/runtime/test_ana_trace_report.py` |
| Session Checkpoint example | ready | `docs/examples/SESSION_CHECKPOINT_EXAMPLE.md`, `session_checkpoint action=save` |
| Session Checkpoint preserves notes | ready | `docs/examples/SESSION_CHECKPOINT_PRESERVES_NOTES_EXAMPLE.md`, `tests/runtime/test_session_checkpoint_tool.py` |
| Local checkpoint lane | ready | `docs/examples/LOCAL_CHECKPOINT_FALLBACK_EXAMPLE.md`, `tests/runtime/test_ana_local_checkpoint.py` |
| Session REM Sleep example | ready | `docs/examples/SESSION_REM_SLEEP_EXAMPLE.md`, `session_rem_sleep action=analyze` |
| Session Lifecycle example | ready | `docs/examples/SESSION_LIFECYCLE_EXAMPLE.md`, `session_lifecycle action=wake/rest` |
| Memory hygiene report | ready | `ANA_MAX/dev_artifacts/scripts/ana_memory_hygiene.py`, `tests/runtime/test_ana_memory_hygiene.py` |
| Memory archive dry-run/apply safety | ready | `ANA_MAX/dev_artifacts/scripts/ana_memory_archive.py`, `tests/runtime/test_ana_memory_archive.py` |
| Lab state summary | ready | `ANA_MAX/dev_artifacts/scripts/ana_lab_state_summary.py`, `tests/runtime/test_ana_lab_state_summary.py` |
| File activity snapshot | ready | `docs/examples/FILE_ACTIVITY_SNAPSHOT_EXAMPLE.md`, `tests/runtime/test_ana_file_activity_snapshot.py` |
| Reload readiness preflight | ready | `ANA_MAX/dev_artifacts/scripts/ana_reload_readiness.py`, `tests/runtime/test_ana_reload_readiness.py` |
| Reload consistency check | ready | `docs/examples/RELOAD_CONSISTENCY_CHECK_EXAMPLE.md`, `tests/runtime/test_ana_reload_consistency_check.py` |
| Post-reload verify | ready | `docs/examples/POST_RELOAD_VERIFY_EXAMPLE.md`, `tests/runtime/test_ana_post_reload_verify.py` |
| Operator status | ready | `docs/examples/OPERATOR_STATUS_EXAMPLE.md`, `tests/runtime/test_ana_operator_status.py` |
| VSIX version consistency | ready | `docs/examples/VSIX_VERSION_CONSISTENCY_EXAMPLE.md`, `tests/runtime/test_ana_vsix_version_check.py` |
| Binary Map static analysis | ready | `docs/examples/BINARY_MAP_STATIC_ANALYSIS_EXAMPLE.md`, `binary_map path=...` |
| Input API Probe spec | ready | `docs/examples/INPUT_API_PROBE_SPEC_EXAMPLE.md`, `input_api_probe operation=spec confirm=true` |
| Runtime deep router escalation | ready | `docs/examples/RUNTIME_DEEP_ROUTER_ESCALATION_EXAMPLE.md`, `tool_router mode=runtime_deep` |
| Tool Healthcheck summary | ready | `docs/examples/TOOL_HEALTHCHECK_SUMMARY_EXAMPLE.md`, `tool_healthcheck scope=safe` |
| Tool profile report | ready | `ANA_MAX/dev_artifacts/scripts/ana_tool_profile_report.py`, `ANA_MAX/memory/tool_profiles/TOOL_PROFILE_REPORT.md` |
| Tool profile summary example | ready | `docs/examples/TOOL_PROFILE_SUMMARY_EXAMPLE.md` |
| Dashboard local HTML example | ready | `docs/examples/DASHBOARD_LOCAL_HTML_EXAMPLE.md`, `tests/runtime/test_vscode_extension.py::test_extension_dashboard_generates_local_html` |
| Examples index | ready | `docs/ANA_EXAMPLES_INDEX.md` |

## Required Tests

| Area | Status | Notes |
| --- | --- | --- |
| Extension command declarations | ready | `tests/runtime/test_vscode_extension.py` |
| Code Map | ready | `tests/runtime/test_ana_code_map.py` |
| Graph Map | ready | `tests/runtime/test_ana_graph_map.py` |
| Code Context Pack | ready | `tests/runtime/test_code_context_pack_tool.py` |
| Graph Context Pack | ready | `tests/runtime/test_graph_context_pack_tool.py` |
| Tool Router | ready | `tests/runtime/test_tool_router_tool.py` |
| Codex Companion | ready | `tests/runtime/test_ana_codex_companion.py` |
| Tool Healthcheck | ready | `tests/runtime/test_tool_healthcheck_tool.py` |
| MCP CLI wrapper | ready | `tests/runtime/test_ana_mcp_call.py` |
| Nucleus Smoke | ready | `tests/runtime/test_ana_nucleus_smoke.py` |
| No-reload gate advisory | ready | `tests/runtime/test_no_reload_quality_gate.py` |
| Lab quality gate contract | ready | `tests/runtime/test_lab_quality_gate_contract.py` |
| VSIX version consistency | ready | `tests/runtime/test_ana_vsix_version_check.py` |
| Local checkpoint lane | ready | `tests/runtime/test_ana_local_checkpoint.py` |
| Session checkpoint handoff preservation | ready | `tests/runtime/test_session_checkpoint_tool.py` |
| Session Audit | ready | `tests/runtime/test_session_audit_tool.py` |
| Memory hygiene | ready | `tests/runtime/test_ana_memory_hygiene.py` |
| Memory archive safety | ready | `tests/runtime/test_ana_memory_archive.py` |
| Lab state summary | ready | `tests/runtime/test_ana_lab_state_summary.py` |
| File activity snapshot | ready | `tests/runtime/test_ana_file_activity_snapshot.py` |
| Live behavior checker | ready | `tests/runtime/test_ana_live_behavior_check.py` |
| Reload readiness | ready | `tests/runtime/test_ana_reload_readiness.py` |
| Reload consistency | ready | `tests/runtime/test_ana_reload_consistency_check.py` |
| Post-reload verify | ready | `tests/runtime/test_ana_post_reload_verify.py` |
| Error Radar | ready | `tests/runtime/test_error_radar_tool.py` |
| Dirty Tree Report | ready | `tests/runtime/test_ana_dirty_tree_report.py` |
| Patch Advisor | ready | `tests/runtime/test_ana_patch_advisor.py` |
| Autonomy Runner | ready | `tests/runtime/test_ana_autonomy_runner.py` |
| Linux Readiness | ready | `tests/runtime/test_ana_linux_readiness.py` |
| Profile Manifest | ready | `ana_governance_check.py` verifies required profile terms and permission manifest coverage. |
| Serious Project Rules | ready | `ana_governance_check.py` verifies required docs and no-hype rule terms. |
| Tool Profile Report | ready | `tests/runtime/test_ana_tool_profile_report.py` |

## Before Claiming A Feature Works

1. Identify profile: `core`, `windows`, `linux`, `security_lab`, `public_safe`,
   or `private_lab`.
2. Run the smallest focused test.
3. Run Nucleus Smoke or Autonomy Pass if MCP behavior changed.
4. Save a checkpoint if the feature affects future sessions.
5. Record the limitation.

## Before Sharing Anything Outside The Lab

1. Remove secrets and local paths.
2. Remove screenshots/logs/session memory.
3. Replace private examples with sanitized examples.
4. Remove security-lab operational details.
5. Avoid hype language.
6. Say what was verified and what remains experimental.
