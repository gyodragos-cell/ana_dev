# Live Behavior Check Example

## Purpose

Show how ANA detects a healthy-but-stale MCP server after source edits.

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_live_behavior_check.py
```

Strict mode returns a non-zero exit code while status is `WARN`. For operator
log collection only, use:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_live_behavior_check.py --allow-warn
```

`--allow-warn` keeps the printed status as `WARN` but returns exit code 0 so a
wrapper can continue collecting reload diagnostics. It is not a reload PASS.

## Expected Shape While MCP Is Stale

```text
ANA Live Behavior: WARN session_audit_identity_field=True session_audit_identity_signal=True code_context_query_alias=False code_context_graph_preference=False code_context_graph_limit_one=False error_radar_runtime=False error_radar_summary=False agent_coach_monitor_noise=False context_generated_memory_noise=False
next_action=Restart ANA MCP, then run Live Behavior, Reload Consistency, and Post-Reload Verify.
```

## Expected Shape After Reload

```text
ANA Live Behavior: PASS session_audit_identity_field=True session_audit_identity_signal=True code_context_query_alias=True code_context_graph_preference=True code_context_graph_limit_one=True error_radar_runtime=True error_radar_summary=True agent_coach_monitor_noise=True context_generated_memory_noise=True
next_action=Live MCP exposes current checked behavior.
```

## What This Proves

- MCP can be online but still running old tool code.
- ANA checks behavior, not only `/health` and `tools/list`.
- The current probe verifies that live `session_audit action=trust` exposes the
  identity-surface fields added on disk.
- The current probe also compares live `error_radar` dirty-tree runtime counts
  against disk-side behavior, so a stale server is detected after diagnostic
  classifier fixes.
- The current probe verifies that `error_radar` returns its compact summary
  breakdown, so self-healing can rank findings by severity/kind/source.
- The current probe verifies that `code_context_pack query=...` is accepted as
  a precise alias for `task=...` when `include_text=false`, so agent-style
  calls do not silently fall back to UI text.
- The current probe verifies that Graph Map can promote the more precise file
  candidate above a noisier Code Map text match.
- The current probe verifies the same Graph Map promotion when `limit=1`, so
  compact agent calls still receive the precise top file.
- The current probe verifies that live `agent_coach` filters known read-only
  monitor/demo telemetry, so Autonomy does not chase false critical loops after
  diagnostics have already been fixed on disk.
- The current probe verifies that Code/Graph Context keep active files ahead of
  generated checkpoint, REM, and archive noise for the representative next
  scoped lab action query.

## Limitation

This is a small freshness probe, not a full regression suite. Extend it only
with high-signal behavior markers.

## Share Class

`private-lab, sanitizable`: safe after removing local report paths and run ids.
