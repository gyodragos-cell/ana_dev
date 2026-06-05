# Memory Archive Dry-Run Example

Last updated: 2026-05-31

Purpose: show how ANA can prepare a safe archive operation for old checkpoint
and REM files without moving anything by default.

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_memory_archive.py --no-write
```

## Sanitized Result

```text
ANA Memory Archive: mode=dry_run moves=<n> archive_root=dev_artifacts/archives/memory_hygiene_<yyyymmdd> date_basis=utc kinds=checkpoints=<n>, rem_sleep_reports=<n> bytes=<n>
apply_requires=--apply --confirm ARCHIVE_OLD_MEMORY
```

## What This Proves

ANA can produce a concrete archive plan with:

- source path
- target path
- file size
- SHA256 digest
- source/target existence checks
- archive root
- archive date basis (`utc`)
- compact counts by kind
- total bytes planned

## Readiness Check

Before applying a dry-run plan, validate the saved report:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_memory_archive.py --readiness-report ANA_MAX/dev_artifacts/reports/memory_archive_<timestamp>.json --no-write
```

Expected shape:

```text
ANA Memory Archive Readiness: PASS moves=<n> kinds=checkpoints=<n>, rem_sleep_reports=<n> failures=0
```

The default mode is dry-run. No files are moved unless the operator explicitly
runs:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_memory_archive.py --apply --confirm ARCHIVE_OLD_MEMORY
```

## Safety Boundary

The archive apply path is guarded by:

- explicit `--apply`
- exact confirmation phrase
- path containment under `ANA_MAX`
- target-exists skip
- no deletion
- report output

Do not run apply during normal feature work. Run it only after reviewing the
dry-run plan and after a final REM/session consolidation.

## Verification

```powershell
python -m pytest tests/runtime/test_ana_memory_archive.py tests/runtime/test_ana_memory_hygiene.py -q
```

Expected:

```text
12 passed
```

## Post-Apply Verification

If an archive is ever applied, verify the applied report:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_memory_archive.py --verify-report ANA_MAX/dev_artifacts/reports/memory_archive_<timestamp>.json
```

Verification checks:

- original source is gone
- archive target exists
- target SHA256 matches the dry-run/apply hash

This mode is also report-only.

## Share Class

`private-lab, sanitizable`: workflow shape can be shared after review, but
actual checkpoint names, hashes, and paths stay private.
