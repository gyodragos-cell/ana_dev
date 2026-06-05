# Linux Readiness Summary Example

## Purpose

Show how ANA tracks the future Linux/Mate migration without pretending the
Windows lab is already Linux-ready.

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_linux_readiness.py
```

## Sanitized Result Summary

Latest readiness scan:

```text
schema: ana.linux_readiness.v1
status: WINDOWS_FIRST
score: 0
findings: 642
affected_files: 122
core_blocker_files: 39
by_profile:
  core_candidate: 330
  docs: 102
  extension: 42
  tests: 72
  windows_profile: 96
```

Latest mother-lab scan:

```text
report: ANA_MAX/dev_artifacts/reports/linux_readiness_20260601_150056.json
status: WINDOWS_FIRST
score: 0
findings: 738
affected_files: 174
core_blocker_files: 40
by_profile:
  core_candidate: 333
  docs: 180
  extension: 44
  tests: 85
  windows_profile: 96
```

## What This Proves

- ANA can statically scan for Windows-specific blockers.
- Linux migration is tracked as engineering work, not hope.
- Windows UIA, desktop, input, and voice tools must stay behind a Windows
  profile.
- Code Map, Graph Map, Nucleus Smoke, Autonomy Pass, session audit, and routing
  are the intended Linux-first core.

## Recommended Next Steps

```text
1. Keep using Windows as primary until the Linux core runs cleanly.
2. Move only core/shared logic first.
3. Avoid porting every old PowerShell helper.
4. Add bash equivalents only for stable workflows.
5. Start Linux with MCP core and no desktop-control tools.
```

## Limitation

This is a conservative static scan. It finds likely blockers; it does not prove
runtime behavior on Linux. The real proof starts when the Linux mirror runs the
core MCP smoke tests.

## Share Class

Sanitized. Safe after removing local report paths and private migration package
details.
