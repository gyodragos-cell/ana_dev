# Patch Advisor Example

## Purpose

Show ANA's safe self-healing lane: diagnostics can propose a repair direction,
but they do not write code automatically.

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_patch_advisor.py --write-report
```

## Sanitized Result Summary

```text
ANA Patch Advisor: Do not patch blindly while the lab tree is large confidence=92%
next_action=Keep current work scoped; archive checkpoint/REM noise only after explicit operator approval.
schema: ana.patch_advisor.v1
mode: suggest_only
inputs:
  finding_count: 1
  raw_finding_count: 1
  noise_filtered: 0
  dirty_tree_available: true
  dirty_tree_total: <n>
  blast_radius_available: true
  blast_radius_candidates: 5
  blast_radius_affected: <n>
recommendation_evidence:
  <n> changed paths (<n> tracked, <n> untracked);
  <n> checkpoints, <n> rem_sleep reports, <n> docs, <n> tests,
  <n> runtime, <n> scripts from local Dirty Tree.
recommendations:
  - Do not patch blindly while the lab tree is large
  - Review active work batches before choosing a patch
  - Review graph blast-radius before editing
active_work_batches:
  runtime=<n>; script=<n>; test=<n>; config=<n>; extension=<n>; doc=<n>
first_batch_suggested_commands:
  - python -m compileall -q <area>
  - python -m pytest <focused tests> -q
policy:
  read_only: true
  writes_files: false
  requires_operator_for_apply: true
```

## What This Proves

- ANA can turn `error_radar`, local dirty-tree classification, git state, and
  graph context into a patch recommendation.
- For `large_dirty_tree`, ANA prefers the local full Dirty Tree classification
  over stale or compact live Error Radar details, so runtime/script work is not
  undercounted.
- ANA can filter known diagnostic noise inherited from a stale live MCP tool
  while still reporting how many raw findings were filtered.
- ANA can include Graph Map blast-radius context for changed runtime/test files
  before recommending what to inspect.
- ANA can include Dirty Tree review batches, so large-change self-healing can
  start with the right active-work group instead of only warning about size.
- ANA preserves suggested commands from the first review batch, so the next
  verification step is concrete and scoped.
- The recommendation includes evidence, confidence, suggested files, and a next
  step.
- The tool is read-only and does not apply patches.
- This is the correct bridge between self-healing signals and Codex/operator
  review.

## Operating Rule

Use Patch Advisor after a warning or failure when the next code change is not
obvious:

```text
observe -> error_radar -> patch_advisor -> Codex/operator review -> patch -> tests
```

When `blast_radius_available=true`, read the high-score affected files/tests
before patching. The advisor remains suggest-only.

When `dirty_tree.review_batches` is present, start with the first active-work
batch unless a higher-severity runtime finding points elsewhere. Run one of
that batch's `suggested_commands` before broadening the investigation.

## Share Class

`private-lab, sanitizable`: remove report paths and local git samples before
sharing outside the lab.
