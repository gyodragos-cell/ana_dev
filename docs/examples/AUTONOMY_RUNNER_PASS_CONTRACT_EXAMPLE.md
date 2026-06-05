# Autonomy Runner Pass Contract Example

Last updated: 2026-05-31

Purpose: document the exact safe read-only stack that must pass for ANA's
autonomy runner contract.

## Evidence

Focused test:

```powershell
python -m pytest tests/runtime/test_ana_autonomy_runner.py tests/runtime/test_ana_review_batch_runner.py -q
```

Result:

```text
19 passed
```

## PASS Contract

The pass-path test proves that `ana_autonomy_runner.py` uses this safe stack:

```text
foreground_ui_snapshot
live_reload_marker
live_tool_surface
live_behavior
file_activity_snapshot
memory_archive_readiness
code_context_pack
graph_context_pack
tool_router
agent_coach
tool_healthcheck
error_radar
patch_advisor
review_batch_plan
review_batch_runs
session_audit
```

The test also verifies that the autonomy runner does not call:

```text
desktop_control
frida_instrument
```

## Live Reality Check

A live run on 2026-05-31 returned:

```text
ANA Autonomy: PASS (12 pass / 0 warn / 0 fail) trust=100% trace=12/12 aligned=True
[PASS] foreground_ui_snapshot UI snapshot captured for: Code
```

The earlier warnings came from optional `live_reload_marker` and
`foreground_ui_snapshot` steps. After operator reload and the
`foreground_ui_snapshot` argument fix, the live contract now passes with zero
warnings. The runner sends `max_elements` as the string required by the MCP
schema and retries one transient empty foreground snapshot before warning.

Current live evidence also includes metadata-only file activity, memory archive
readiness, Patch Advisor review batches, Review Batch Plan dry-run coverage,
and trace alignment:

```text
ANA Autonomy: PASS (18 pass / 0 warn / 0 fail) trust=92% trace=18/18 aligned=True
[PASS] file_activity_snapshot
[PASS] memory_archive_readiness
[PASS] patch_advisor dirty_tree_available=true dirty_tree_total=<current_dirty_tree_total>
[PASS] review_batch_plan
[PASS] review_batch_runs
patch_advisor.first_review_batch=runtime
patch_advisor.review_batches=runtime, script, test, config, extension, doc
patch_advisor.first_review_commands=<focused compile/test commands>
review_batch_plan.mode=dry_run
review_batch_plan.command_count=<current_planned_command_count>
review_batch_plan.batches=runtime, script, test, config, extension, doc
review_batch_plan.first_command=python -m compileall -q ANA_MAX/core ANA_MAX/tools ANA_MAX/main.py ANA_MAX/mcp_stdio.py
review_batch_runs.planned_count=6
review_batch_runs.passed_count=6
review_batch_runs.fresh_count=6
review_batch_runs.missing_categories=[]
review_batch_runs.failing_categories=[]
review_batch_runs.stale_categories=[]
next_action=Continue with one new scoped lab action; review batches verified 6/6. Do not rerun them unless new changes land.
```

## What This Proves

ANA's autonomy runner is an observation/readiness loop, not an uncontrolled
executor. It gathers context, routes, verifies, audits, and then recommends one
scoped next action.

`patch_advisor` is local and suggest-only. It may include local Dirty Tree
evidence plus Graph Map blast-radius signals so ANA can warn about likely
affected files/tests before a patch is made.

`patch_advisor` review batches are preserved in `signals.patch_advisor`, so
Autonomy can recommend the first active-work group to review instead of losing
that information after compaction.

The first review batch also preserves compact `first_review_commands`, allowing
the operator or Codex to run the smallest useful compile/test check next.

`review_batch_plan` is local and dry-run-only inside Autonomy. It calls the
Review Batch Runner in all-batches plan mode, keeps shell execution disabled,
and records only compact batch/category/command metadata. It does not execute
the planned commands from Autonomy.

`review_batch_runs` is local and read-only. It reads recent Review Batch Runner
reports, compares them with the current planned categories, checks whether each
report is fresh against the latest active dirty-tree file mtime for that
category, and records compact planned/passed/fresh/missing/failing/stale
counts. It does not execute commands.

`file_activity_snapshot` is local and metadata-only. It compares the authorized
workspace root against the previous baseline and reports aggregate
created/deleted/modified counts without reading file contents.

`memory_archive_readiness` is local and metadata-only. It reads the current lab
memory hygiene summary plus the latest dry-run archive readiness, then reports
whether cleanup planning is `PASS`, `STALE`, or unavailable. It does not move
checkpoint or REM files.

The report also includes `trace_spans` using `ana.agent_trace_span.v1`. These
spans record run/trace/span identity, step operation, status, timing, and
digests. They do not store raw private payloads.

## Limitation

The runner is still allowed to return `WARN` when optional observation is
degraded. That is the correct behavior: continue only after reviewing the
warning or using a smaller diagnostic tool.

When the only warning is stale live behavior, the correct follow-up is to
restart ANA MCP, then run Live Behavior, Reload Consistency, Post-Reload Verify,
and Autonomy Pass.

## Share Class

`sanitized`: safe as architecture/test evidence. Do not publish raw UI
snapshots, local reports, private paths, or session telemetry.
