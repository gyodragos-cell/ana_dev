# Autonomy Runner WARN Follow-Up Example

## Purpose

Show how ANA treats an Autonomy Runner `WARN` as a diagnostic signal, not as a
silent success or a panic failure.

This is a historical diagnostic example from before the clean live MCP reload.
It intentionally preserves the old `live_behavior` warning pattern. Current
clean operator examples should show `PASS`, not this warning.

## Evidence Source

```text
ANA_MAX/dev_artifacts/reports/autonomy_runner_20260531_215513.json
live no-write run on 2026-05-31 after adding live behavior freshness checks
docs/examples/BUG_REPORT_EXAMPLE_ANA_AUTONOMY_WARN.md
```

Resolution evidence:

```text
ANA_MAX/dev_artifacts/reports/trace_report_20260531_223702.json
ANA Trace Report: PASS steps=16 spans=16 aligned=True
```

Current operator guidance note:

```text
If the only stale signal is live_behavior, ANA should recommend direct MCP
restart, not a full VS Code/VSIX reload.
```

## Sanitized Result Summary

The Autonomy Runner result was:

```text
status: WARN
summary: 15 pass / 1 warn / 0 fail
tools_count: 90
trust_score: 92
warning_steps: live_behavior
warning_message: live MCP has not loaded the latest checked tool behavior yet.
tool_healthcheck: 7 OK / 0 FAIL
error_radar: 1 medium finding
next_action: Restart ANA MCP, then run Live Behavior, Reload Consistency, Post-Reload Verify, and Autonomy Pass.
```

## Interpretation

This is a healthy-with-warning state:

```text
MCP runtime: usable
core routing: usable
code context: usable
graph context: usable
verification: partial, because selected live behavior is stale until MCP restart
UI observation: usable
live behavior: advisory, because the running MCP server has not loaded latest checked tool behavior
```

## Follow-Up Rule

When Autonomy Runner returns `WARN`:

```text
1. Do not rerun blindly.
2. Read the warning step.
3. Check whether the step is optional.
4. Run or inspect `error_radar`.
5. If only `live_behavior` warns, restart ANA MCP directly before relying on
   newly changed tool behavior.
6. If the reload marker is missing, use the operator reload/restart lane.
7. If healthcheck is clean and warning is optional, continue with caution.
8. Save the warning as an example if it teaches a recurring lesson.
```

## What This Proves

- ANA can continue after non-blocking warnings.
- The report separates `PASS`, `WARN`, and `FAIL`.
- Reload freshness is visible inside the same autonomy report.
- Trust score stays evidence-based and decreases when verification is partial.
- Repeated warnings can become documented operating rules instead of chat-only
  memory.

## Limitation

This example preserves the warning pattern for future diagnostics. The specific
`live_behavior` warning shown here is expected while disk-side behavior has been
updated but the live MCP process has not restarted yet.

## Share Class

Sanitized. Safe after removing report filenames, local paths, and private UI
details if used outside the lab.
