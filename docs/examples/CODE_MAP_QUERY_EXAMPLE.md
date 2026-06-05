# Code Map Query Example

## Purpose

Show how ANA uses Code Map to search compact project summaries instead of
reading the full repository blindly.

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_code_map.py refresh --force
python ANA_MAX/dev_artifacts/scripts/ana_code_map.py query --query "ana_tool_profile_report permission_manifest" --limit 5
```

## Sanitized Result Summary

The refreshed query returned five compact matches from summary files. The top
match was:

```text
file: ANA_MAX/dev_artifacts/scripts/ana_tool_profile_report.py
score: 4
purpose: Generate a readable ANA tool profile report from permission_manifest.
matched_terms: ana_tool_profile_report, permission_manifest, profile, report
symbols:
  - load_manifest
  - tool_profiles
  - build_report
  - markdown_report
  - write_outputs
dependencies:
  - argparse
  - collections
  - datetime
  - json
  - pathlib
next_step: Open the top file only, then inspect nearby symbols.
```

Other matches included session checkpoints that mention the same tool profile
work. Those are useful for history, but the top source file is the actionable
context.

## What This Proves

- ANA can query a prebuilt code map instead of scanning every source file.
- Results include file path, purpose, symbols, dependencies, matched terms, and
  a recommended next step.
- Code Map is useful for narrowing context before opening files.
- A refresh matters after adding new scripts; stale maps can return older
  related files.

## Limitation

The broad query below matched generic terms such as `report` and `profile`, so
it returned a related runtime report before the exact tool profile script:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_code_map.py query --query "tool profile report" --limit 5
```

Use specific symbol/file terms when precision matters.

## Share Class

Sanitized. Safe after reviewing paths and removing private report references if
used outside the lab.
