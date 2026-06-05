# Reload Readiness Preflight Example

Last updated: 2026-05-31

Purpose: check whether ANA MCP should be restarted/reloaded without stopping or
mutating any process.

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_reload_readiness.py --no-write
```

## Sanitized Result

```text
ANA Reload Readiness: mcp_ready=True reload_needed=True marker=True tool_surface=PASS(live=90,manifest=90,extra=0,missing=0) behavior=WARN(checks=2/3)
reasons=live_behavior_stale
next_action=Restart ANA MCP, then run Live Behavior, Reload Consistency, and Post-Reload Verify.
```

## What It Checks

- MCP health
- live reload marker (`data.stale`)
- live tool-surface drift against the local permission manifest
- selected live behavior freshness
- port `8766` listener information
- Python process information

## Safety Boundary

This is read-only. It does not stop, kill, restart, reload, or mutate processes.

## Correct Follow-Up

When `reload_needed=True`:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_live_behavior_check.py
python ANA_MAX/dev_artifacts/scripts/ana_reload_consistency_check.py --no-write
python ANA_MAX/dev_artifacts/scripts/ana_post_reload_verify.py --no-write
```

Run these as separate commands. While the live behavior is still stale,
`ana_live_behavior_check.py` reports `WARN` and returns non-zero by design. For
operator log collection only, use:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_live_behavior_check.py --allow-warn
```

This does not mean reload passed; it only lets a wrapper continue collecting
diagnostics.

After operator restart/reload, the expected live reload marker is:

```text
ANA Live Reload: PASS marker=True
ANA Post Reload: PASS ... tool_surface=PASS(...) ... behavior=PASS ...
```

## Share Class

`private-lab, sanitizable`: safe as workflow evidence after removing local
process details.
