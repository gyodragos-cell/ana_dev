# File Activity Snapshot Example

## Purpose

Show how ANA can notice aggregate file changes between runs without reading
file contents or watching the whole machine.

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_file_activity_snapshot.py --root . --json
```

## Sanitized Result Summary

```text
schema: ana.file_activity_snapshot.v1
baseline_available: true
files_scanned: 1200
diff.created: 2
diff.deleted: 1
diff.modified: 4
privacy.content_read: false
privacy.raw_private_payloads: false
privacy.paths: relative_to_authorized_root
```

## What This Proves

- ANA can detect created, deleted, and modified files after a baseline exists.
- The snapshot stores relative paths, size/mtime metadata, suffixes, and stat
  digests.
- It does not read file contents and does not store raw private payloads.

## Limitation

This is not a continuous watcher. It compares one snapshot to the previous
baseline for an explicitly chosen root. Run it once to initialize a baseline,
then run it later to detect changes.

## Share Class

Private-lab, sanitizable. Remove file samples and local root labels before
sharing outside the lab.
