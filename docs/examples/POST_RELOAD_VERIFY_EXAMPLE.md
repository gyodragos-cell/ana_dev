# Post-Reload Verify Example

## Purpose

Show the single command ANA uses after an operator reload/restart to verify
that live MCP loaded the latest tool behavior and that the core nucleus still
passes.

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_post_reload_verify.py --no-write
```

## Expected Healthy Shape

```text
ANA Post Reload: PASS marker=True tool_surface=PASS(live=90,manifest=90,extra=0,missing=0) identity=PASS(files=10,violations=0,missing=0) behavior=PASS nucleus=PASS (9 pass / 0 warn / 0 fail)
next_action=Continue with Autonomy Pass or one scoped lab action.
```

## If Reload Did Not Land

```text
ANA Post Reload: WARN marker=False tool_surface=PASS(live=90,manifest=90,extra=0,missing=0) identity=PASS(files=10,violations=0,missing=0) behavior=PASS nucleus=PASS (9 pass / 0 warn / 0 fail)
next_action=Reload/restart ANA MCP server, then rerun post-reload verify.
```

## If Live Tool Surface Is Stale

```text
ANA Post Reload: WARN marker=True tool_surface=WARN(live=91,manifest=90,extra=1,missing=0) identity=PASS(files=10,violations=0,missing=0) behavior=WARN nucleus=PASS (9 pass / 0 warn / 0 fail)
next_action=Restart ANA MCP so live tools/list matches the local permission manifest, then rerun post-reload verify.
```

## If Identity Surface Drift Appears

```text
ANA Post Reload: WARN marker=True tool_surface=PASS(live=90,manifest=90,extra=0,missing=0) identity=FAIL(files=10,violations=1,missing=0) behavior=PASS nucleus=PASS (9 pass / 0 warn / 0 fail)
next_action=Fix active identity surface, then rerun post-reload verify.
```

## If Live Behavior Is Stale

```text
ANA Post Reload: WARN marker=True tool_surface=PASS(live=90,manifest=90,extra=0,missing=0) identity=PASS(files=10,violations=0,missing=0) behavior=WARN nucleus=PASS (9 pass / 0 warn / 0 fail)
next_action=Restart ANA MCP, then run Live Behavior, Reload Consistency, and Post-Reload Verify.
```

This is the current expected pending shape while disk-side behavior has changed
but ANA MCP has not restarted yet. It is different from tool-surface drift:
`tools/list` already matches the permission manifest, but one selected behavior
probe is still stale.

## What This Proves

- The live MCP server exposes the expected reload freshness marker.
- The live `tools/list` surface matches the local permission manifest.
- The active lab/extension identity surface remains Codex-first and neutral.
- Selected live tool behavior exposes current disk-side fields.
- Nucleus Smoke still passes after reload.
- Lab state summary can still read MCP health, memory hygiene, and dirty-tree
  counts.
- The verifier is read-only except optional report writing.

## Share Class

`private-lab, sanitizable`: keep local report files private. A sanitized summary
can be shared without raw paths, logs, screenshots, or private machine state.
