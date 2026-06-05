# Binary Map Static Analysis Example

## Purpose

Show how ANA performs static-only binary analysis in the lab without executing
the target file and without attaching to any process.

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py binary_map path="sandbox/binary_map_sample/sample.dll" strings_limit=10
```

## Sanitized Result Summary

The static analyzer returned:

```text
schema: ana.binary_map.v1
path: sandbox/binary_map_sample/sample.dll
size: 2048
format: pe
architecture: x64
entry_point: 0x140001000
imports:
  - KERNEL32.dll
exports: []
sections:
  - .text
strings:
  - .text
  - KERNEL32.dll
  - CreateFileW diagnostics
lab_mode: true
```

## What This Proves

- ANA can inspect PE metadata statically.
- ANA can extract architecture, entry point, sections, imports, exports, hash,
  and printable strings.
- The file is not executed.
- The tool is useful before any deeper runtime diagnostics.

## Path Lesson

`binary_map` resolves paths relative to the ANA workspace root:

```text
correct: sandbox/binary_map_sample/sample.dll
wrong:   ANA_MAX/sandbox/binary_map_sample/sample.dll
```

The wrong form fails because the tool already starts inside `ANA_MAX`.

## Safety Rule

Use `binary_map` for:

```text
static metadata
dependency/import overview
safe binary triage
closed-source file inventory
pre-flight check before deeper lab-only diagnostics
```

Do not use it as permission to execute, hook, patch, or modify binaries.

## Limitation

This example uses a tiny synthetic PE sample created for lab testing. Real
binary triage may require stronger parsers and manual review, especially for
packed or obfuscated files.

## Share Class

Sanitized. Safe after removing local paths and hashes if they identify private
lab files.
