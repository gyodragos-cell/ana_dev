# ANA Operator Reload Runbook

Last updated: 2026-05-31

Purpose: one short operator flow for deciding whether the current lab needs only
an ANA MCP restart or the broader VSIX / VS Code reload lane, then verifying
that the live server loaded the new tool behavior.

This is mother-lab only. Do not publish or sync unless Billy explicitly asks.

## When To Use

Use this when:

```text
reload_needed = True
Nucleus Smoke = PASS or core MCP health is online
```

That means ANA is healthy enough to inspect, but the running MCP process or IDE
surface has not loaded the latest lab changes yet.

Reload readiness now checks three signals:

```text
reload marker
live tool surface versus permission manifest
selected live behavior freshness
```

Example:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_reload_readiness.py --no-write
```

Expected shape for Python-only stale behavior:

```text
ANA Reload Readiness: mcp_ready=True reload_needed=True marker=True tool_surface=PASS(live=90,manifest=90,extra=0,missing=0) behavior=WARN(checks=2/3)
reasons=live_behavior_stale
next_action=Restart ANA MCP, then run Live Behavior, Reload Consistency, and Post-Reload Verify.
```

## Lane A. Python Tool Behavior Stale

Use this lane when:

```text
marker=True
tool_surface=PASS(...)
reasons=live_behavior_stale
```

This means the VS Code extension and tool list are fine, but the running MCP
server has old Python tool code loaded.

### A1. Restart ANA MCP

Use the ANA MAX Activity Bar:

```text
Start MCP Server
```

If the old server is still attached, use the existing operator/server flow to
stop and start it. Do not kill processes blindly from scripts.

### A2. Verify Python Behavior

Run these in order:

```text
Live Behavior
Reload Consistency
Post-Reload Verify
```

Or terminal:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_live_behavior_check.py
python ANA_MAX/dev_artifacts/scripts/ana_reload_consistency_check.py --no-write
python ANA_MAX/dev_artifacts/scripts/ana_post_reload_verify.py --no-write
```

Run these as separate commands, not chained with `&&`: `ana_live_behavior_check.py`
returns a non-zero exit code while the live behavior is still `WARN`, and that
is useful evidence rather than a shell-script failure.

For log collection only, use:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_live_behavior_check.py --allow-warn
```

This keeps the printed status as `WARN` but returns exit code 0 so an operator
wrapper can continue collecting the remaining diagnostics. Do not treat
`--allow-warn` as a successful reload.

## Lane B. VSIX / VS Code Surface Reload

Use this lane when:

```text
marker=False
tool_surface=WARN(...)
new Activity Bar command is missing
VSIX package changed
```

## B1. Confirm Current VSIX

Dry-run first:

```powershell
.\ANA_MAX\dev_artifacts\scripts\install_latest_lab_vsix.ps1
```

If the path and version look right, install:

```powershell
.\ANA_MAX\dev_artifacts\scripts\install_latest_lab_vsix.ps1 -Apply
```

The helper does not reload VS Code automatically.

Current lab package:

```text
vscode_extension/ana-codex-cockpit-1.0.71.vsix
ANA_MAX/ana-max-codex-cockpit-1.0.71.vsix
```

Current note: v1.0.71 includes the Activity Bar `Codex Companion` command on
top of the reload/readiness/context-map controls. It lets ANA observe, route,
coach, and challenge Codex before scoped work, and still needs
`Developer: Reload Window` before the new command appears in the active IDE
window.

## B2. Reload VS Code Window

Run from Command Palette:

```text
Developer: Reload Window
```

## B3. Restart ANA MCP

Use the ANA MAX Activity Bar:

```text
Start MCP Server
```

If the old server is still attached, use the existing operator/server flow to
stop and start it. Do not kill processes blindly from scripts.

## 4. Verify

Use the new Activity Bar command:

```text
Post-Reload Verify
```

Before reloading, use:

```text
Reload Readiness
```

To verify the reload diagnostics agree before action work, use:

```text
Reload Consistency
```

Or terminal:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_post_reload_verify.py --no-write
```

Healthy shape:

```text
ANA Post Reload: PASS marker=True tool_surface=PASS(live=90,manifest=90,extra=0,missing=0) identity=PASS(files=10,violations=0,missing=0) behavior=PASS nucleus=PASS (9 pass / 0 warn / 0 fail)
```

If it still says any of:

```text
marker=False
tool_surface=WARN
behavior=WARN
```

then the MCP server or IDE window is still running old loaded code. Reload the
IDE window and/or restart MCP again according to Lane A or Lane B, then rerun
the verification commands.

## 5. Continue Work

After Post-Reload Verify passes:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_autonomy_runner.py --mcp-url http://127.0.0.1:8766/mcp --checkpoint
```

Then continue with one scoped action.

## Safety Notes

- Do not publish this lab VSIX unless explicitly requested.
- Do not run memory archive apply during reload verification.
- Do not clean the dirty tree during reload verification.
- Use the deterministic local checkpoint lane for handoff continuity.
- Keep the Live Console open so both Billy and Codex can see the result.


















