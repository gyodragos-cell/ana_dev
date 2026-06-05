# Error Radar Finding Example

## Purpose

Show how ANA turns logs, git state, and UI signals into prioritized findings
with a concrete recommended next step.

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py error_radar limit=20
```

## Sanitized Result Summary

Current live MCP after reload returns:

```text
schema: ana.error_radar.v1
scope: quick
count: 1
findings:
  - source: git
    kind: large_dirty_tree
    severity: medium
    summary: <changed path count> changed paths; review before committing
recommended_next_step:
  Separate old dirty work from today's change before editing or committing.
```

The updated `error_radar` includes compact dirty-tree details:

```text
details:
  total: <changed path count>
  tracked: <tracked changed paths>
  untracked: <untracked paths>
  docs: <docs paths>
  examples: <docs/examples paths>
  tests: <tests paths>
  runtime: <ANA_MAX/tools or dev_artifacts/scripts paths>
  checkpoints: <session checkpoint/rem sleep paths>
  sample_paths:
    - <first changed path>
  next_step:
    Group changes by docs/tests/runtime/checkpoints before any commit or archive action.
```

For deeper read-only classification, run:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_dirty_tree_report.py
```

Current report shape:

```text
ANA Dirty Tree: total=<n> tracked=<n> untracked=<n> categories=checkpoint=<n>, config=<n>, doc=<n>, extension=<n>, memory=<n>, other=<n>, rem_sleep=<n>, runtime=<n>, script=<n>, test=<n>
active_work=<n> categories={'config': <n>, 'doc': <n>, 'extension': <n>, 'runtime': <n>, 'script': <n>, 'test': <n>}
generated_or_memory=<n> categories={'checkpoint': <n>, 'memory': <n>, 'other': <n>, 'rem_sleep': <n>}
recommendation=Do not commit blindly. Review active work first, then archive checkpoint/REM noise only with explicit operator approval.
```

The JSON report also includes `active_work.by_category` and
`generated_or_memory.by_category`, with `count`, `tracked`, `untracked`,
`top_folders`, and path samples for each category.

It also includes `active_work.review_batches`, ordered for practical review:

```text
runtime -> script -> test -> config -> extension -> doc
```

Each batch includes counts, path samples, a next step for that category, and
focused `suggested_commands` for the first verification pass.

## What This Proves

- ANA can scan recent logs for likely blockers.
- Findings are sorted by severity.
- Git dirty-tree risk is surfaced without pretending it is a runtime crash.
- Large dirty-tree findings include a grouped breakdown in live MCP after reload.
- Dirty Tree Report provides a deeper local classification without mutating the
  workspace.
- Dirty Tree Report can produce an Active Work Map that separates real work
  from generated checkpoint/REM/memory noise before any archive or commit
  decision.
- The Active Work Map includes review batches, so ANA can recommend which group
  to inspect first instead of dumping hundreds of changed paths.
- Review batches include suggested commands, so ANA can move from diagnosis to
  the smallest useful verification without guessing.
- The tool returns an explicit recommended next step.
- Known monitor noise and successful MCP info lines are filtered.
- Debugger smoke-test lines containing `traceback_text` are filtered when they
  are INFO/tool-start metadata, so Error Radar does not confuse a deliberate
  debugger analysis input with an active traceback.

## Operating Rule

When Error Radar returns findings:

```text
1. Start with the highest severity finding.
2. Avoid broad rewrites.
3. Inspect the owner/source of the finding.
4. Apply the smallest fix.
5. Run compile or the focused test for that area.
6. Re-run Error Radar only after the input changed.
```

## Limitation

Error Radar detects likely blockers. It can report historical log entries from
recent sessions, so the agent must confirm whether the finding is still active
before editing.

Noise-filter or dirty-tree classifier changes may still need an MCP reload
before the live server uses newly edited Python modules.

## Share Class

Sanitized. Safe after removing raw log lines, local paths, and private window
titles.
