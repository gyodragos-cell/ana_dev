# Tool Healthcheck Summary Example

Last updated: 2026-05-31

Purpose: show how ANA quickly checks the basic tool surface before deeper work.

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py tool_healthcheck
```

## Sanitized Result

```json
{
  "scope": "safe",
  "ok": 7,
  "failed": 0,
  "results": [
    {"tool": "file_operations", "success": true},
    {"tool": "system_control", "success": true},
    {"tool": "smart_search", "success": true},
    {"tool": "workspace_situational_awareness", "success": true},
    {"tool": "project_navigator", "success": true},
    {"tool": "error_radar", "success": true},
    {"tool": "tool_router", "success": true}
  ]
}
```

## What This Proves

`tool_healthcheck` is the quick "is the lab breathing?" check. It verifies a
small safe stack before ANA spends time on deeper diagnostics:

- filesystem visibility
- system vitals
- search/index surface
- workspace awareness
- project navigation
- error radar
- router recommendation

## What It Does Not Prove

This is not a full regression test and it does not prove every tool works. It
also does not fix failures by itself. A failure should be routed into
`error_radar`, `agent_coach`, focused tests, or a specific repair step.

## Operating Rule

Use `tool_healthcheck` after repeated tool failures, before runtime-deep
diagnostics, and after important repairs. Prefer `scope=safe` unless the task
explicitly needs lab-only Windows checks.

## Share Class

`sanitized`: safe as a high-level operational example. Do not publish raw
terminal logs, local paths, private machine state, or historical telemetry.
