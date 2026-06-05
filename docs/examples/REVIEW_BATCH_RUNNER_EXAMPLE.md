# Review Batch Runner Example

## Purpose

Show how ANA turns a Dirty Tree review batch into a concrete, controlled
verification command.

## Commands

Dry-run preview, safe by default:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_review_batch_runner.py
```

Preview every active review batch, still without running commands:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_review_batch_runner.py --all-batches
```

Run the first command from the first active review batch:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_review_batch_runner.py --run
```

Run all suggested commands for the script batch:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_review_batch_runner.py --category script --all --run
```

## Expected Shape

```text
ANA Review Batch: status=DRY_RUN mode=dry_run category=runtime commands=1
[0] planned python -m compileall -q ANA_MAX/core ANA_MAX/tools ANA_MAX/main.py ANA_MAX/mcp_stdio.py
```

Run mode changes planned commands into pass/fail/timeout results and stores
stdout/stderr tails in a JSON report.

## What This Proves

- ANA can move from diagnosis to a focused verification command.
- The command source is constrained to
  `ana_dirty_tree_report.active_work.review_batches.suggested_commands`.
- Dry-run is the default.
- `--all-batches` is plan-only and cannot be combined with `--run`.
- Commands run without a shell and reject shell metacharacters.
- Only Python review commands are accepted.
- The tool does not archive, delete, commit, install VSIX files, or reload the
  IDE.

## Operating Rule

Use Review Batch Runner after `Operator Status` or `Patch Advisor` points to a
first review batch:

```text
operator_status -> review=batch command=... -> review_batch_runner --run -> next scoped action
```

For broad checks, prefer a category-specific batch before running the full
`tests/runtime` suite.

## Share Class

`private-lab, sanitizable`: remove local report paths and private file samples
before sharing.
