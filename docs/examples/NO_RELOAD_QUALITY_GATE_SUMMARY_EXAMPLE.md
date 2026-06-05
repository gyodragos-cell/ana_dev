# No-Reload Quality Gate Summary Example

## Purpose

Show how ANA verifies the current VS Code/MCP milestone without reinstalling a
VSIX package or reloading the IDE.

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/no_reload_quality_gate.py
```

## Sanitized Result Summary

Latest no-reload gate:

```text
schema: ana.no_reload_quality_gate.v1
summary:
  pass: 8
advisory_summary:
  ok: 2
  warn: 1
compile_core_routing: PASS
pytest_routing_guidance: PASS, includes Nucleus Smoke unit coverage
permission_manifest_coverage: PASS
identity_surface_check: PASS
mcp_smart_readiness: PASS
mcp_all_tools_smoke: PASS
vsix_version_consistency: PASS
package_cockpit_vsix_no_install: PASS
live_reload_marker: ADVISORY/OK
live_tool_surface: ADVISORY/OK
live_behavior: ADVISORY/WARN
```

## What This Proves

- Core routing files compile.
- Router, coach, REM/session, governance, local checkpoint, checkpoint
  preservation, trace, file-activity snapshot, Nucleus Smoke, and extension
  tests pass.
- Permission manifest coverage is clean.
- Active lab and extension identity stays Codex-first and neutral.
- MCP readiness is healthy.
- MCP tool smoke checks pass.
- Active VSIX version references match `vscode_extension/package.json`.
- Extension packaging can run without installing/reloading the IDE.
- Advisory checks can report runtime freshness, live tool-surface drift, and
  stale live behavior without failing the gate.

## Advisory Example

When updated Python tool modules are fixed on disk but the live MCP process has
not reloaded them yet, the gate can print:

```text
ADVISORY live_reload_marker
ANA Live Reload: WARN marker=False
next_action=Restart/reload ANA MCP server, then rerun this check.
```

If live MCP still exposes a retired or stale tool after disk cleanup, the gate
can also print:

```text
ADVISORY live_tool_surface
ANA Live Tool Surface: WARN(live=91,manifest=90,extra=1,missing=0)
extra_live=adal_integration
next_action=Restart ANA MCP so live tools/list matches the local permission manifest.
```

If live MCP is online but still running old tool behavior, the gate can also
print:

```text
ADVISORY live_behavior
ANA Live Behavior: WARN session_audit_identity_field=True session_audit_identity_signal=True code_context_query_alias=False code_context_graph_preference=True code_context_graph_limit_one=False error_radar_runtime=True error_radar_summary=False agent_coach_monitor_noise=False context_generated_memory_noise=False
next_action=Restart ANA MCP, then run Live Behavior, Reload Consistency, and Post-Reload Verify.
```

This does not mean the gate failed. It means the live process still needs a
reload before the newest behavior can be verified through MCP.

## When To Use

Run this after:

```text
Activity Bar command changes
tool routing changes
permission manifest edits
extension packaging edits
small MCP/runtime fixes
checkpoint/handoff fallback changes
```

## Limitation

No-reload gate is optimized for fast local confidence. It does not replace the
full Lab Quality Gate after broad runtime, docs, or test changes.

## Share Class

Sanitized. Safe after removing local report paths and raw stdout/stderr tails.
