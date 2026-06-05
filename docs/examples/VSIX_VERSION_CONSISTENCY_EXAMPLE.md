# VSIX Version Consistency Example

## Purpose

Show how ANA checks that active operator docs point to the same VSIX version as
`vscode_extension/package.json`.

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_vsix_version_check.py
```

## Expected Shape

```text
ANA VSIX Version: PASS expected=1.0.64 mismatches=0
```

## What This Proves

- The latest package version is read from `vscode_extension/package.json`.
- Active install/reload/operator docs do not point to stale VSIX artifacts.
- Historical changelog and checkpoint files are not treated as active install
  instructions.

## Safety

Read-only. Does not package, install, reload, or mutate files.

## Share Class

`private-lab, sanitizable`: safe to describe after removing local paths and
private checkpoint names.











