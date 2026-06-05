# Lab VSIX Install Helper Example

## Purpose

Show the safe operator flow for installing the latest packaged ANA MAX lab VSIX
without accidentally reloading the active IDE session.

## Dry Run

```powershell
.\ANA_MAX\dev_artifacts\scripts\install_latest_lab_vsix.ps1
```

Expected shape:

```text
ANA MAX lab VSIX: ...\vscode_extension\ana-codex-cockpit-1.0.71.vsix
Dry run only. To install:
  code --install-extension ...\ana-codex-cockpit-1.0.71.vsix --force
After install: Developer: Reload Window, restart ANA MCP, then run Post-Reload Verify, Reload Consistency, and Autonomy Pass.
```

## Apply

```powershell
.\ANA_MAX\dev_artifacts\scripts\install_latest_lab_vsix.ps1 -Apply
```

## Safety

- Dry-run by default.
- Does not reload VS Code automatically.
- Does not start or stop MCP.
- Uses the version from `vscode_extension/package.json`.
- Requires the VSIX to exist before install.

## Share Class

`private-lab, sanitizable`: safe to share as a workflow after removing private
paths and version-specific local artifact names.


















