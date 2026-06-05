# Reload Consistency Check Example

Last updated: 2026-05-31

Purpose: verify that ANA's reload-facing diagnostics agree before the operator
continues with action work.

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_reload_consistency_check.py --no-write
```

## Sanitized Result Before MCP Restart

```text
ANA Reload Consistency: PASS aligned=True readiness=WARN operator=WARN lab_state=WARN post_reload=WARN
next_action=Restart ANA MCP, then run Live Behavior, Reload Consistency, and Post-Reload Verify.
```

This means the live server is still stale, but the diagnostics agree. Aligned
`WARN` is acceptable before the operator restarts MCP.

## Expected Result After MCP Restart

```text
ANA Reload Consistency: PASS aligned=True readiness=PASS operator=PASS lab_state=PASS post_reload=PASS
next_action=Reload diagnostics agree. Continue with Autonomy Pass or one scoped lab action.
```

## What It Compares

- `Reload Readiness`
- `Operator Status`
- `Lab State`
- `Post-Reload Verify`

## Why It Exists

Marker-only reload checks can be misleading. The consistency guard requires the
reload marker, live tool surface, and selected live behavior freshness to tell
the same story.

## Safety Boundary

Read-only. It does not install, reload, restart, stop, kill, or mutate
processes.

## Share Class

`private-lab, sanitizable`: safe as workflow evidence after removing local
report paths or machine-specific output.
