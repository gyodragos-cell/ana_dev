# Code Map Incremental Refresh Example

Last updated: 2026-05-31

Purpose: prove that ANA Code Map can skip unchanged files instead of rebuilding
every summary blindly.

## Evidence

Focused test:

```powershell
python -m pytest tests/runtime/test_ana_code_map.py -q
```

Expected:

```text
3 passed
```

## Scenario

The test creates a small project with one source file, then runs:

```python
first = refresh(project, out_dir, force=True)
second = refresh(project, out_dir, force=False)
```

Expected counters:

```json
{
  "first": {
    "updated": 1,
    "skipped": 0
  },
  "second": {
    "updated": 0,
    "skipped": 1,
    "summaries": 1
  }
}
```

## What This Proves

Code Map stores enough index metadata to avoid reprocessing unchanged files.
That matters for large lab projects because ANA can refresh context without
turning every question into a full-project scan.

## Limitation

The current incremental check uses file `mtime` and `size`. It is fast and
deterministic, but a future stronger mode could compare content hashes when
precision matters more than speed.

## Share Class

`sanitized`: safe as architecture evidence. Do not publish private project maps,
local paths, or generated memory contents.
