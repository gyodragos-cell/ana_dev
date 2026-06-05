# Memory Hygiene Report Example

Last updated: 2026-05-31

Purpose: show how ANA reports checkpoint/REM volume without moving or deleting
lab memory files.

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_memory_hygiene.py --no-write
python ANA_MAX/dev_artifacts/scripts/ana_memory_hygiene.py --plan --no-write
```

## Sanitized Result

```text
ANA Memory Hygiene: checkpoints=<n> rem=<n> archive_candidates=<n>
next_action=Archive older checkpoint/REM files into a dated lab archive after a final REM consolidation.
archive_plan=<n> moves -> dev_artifacts/archives/memory_hygiene_<yyyymmdd> date_basis=utc
```

## What This Proves

ANA can quantify memory/checkpoint noise before cleanup:

- session checkpoint count
- REM sleep report count
- latest files to keep
- older files that could be archived later
- dry-run archive target paths
- archive date basis (`utc`)
- read-only safety statement
- default policy: keep the latest 20 checkpoints and latest 20 REM reports

This helps explain large dirty-tree findings without treating them as runtime
crashes.

## Safety Boundary

The script is report-only. It does not move, delete, rename, archive, or modify
files.

`--plan` is still dry-run only. It produces proposed source/target paths and
sets `apply_supported=false`.

## Recommended Workflow

1. Run `session_rem_sleep action=analyze`.
2. Run `ana_memory_hygiene.py --no-write`.
3. Review whether the latest checkpoints are enough.
4. Archive older files only with explicit operator intent.

## Share Class

`private-lab, sanitizable`: counts can be shared after review, but actual
checkpoint and REM files stay private.
