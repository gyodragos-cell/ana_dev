# Dashboard Local HTML Example

## Purpose

Show how ANA opens a dashboard without depending on the old legacy dashboard
server at port `8787`.

## Operator Action

In VS Code:

```text
ANA MAX: Open Dashboard
```

## What The Command Does

The Activity Bar command:

```text
1. Opens the ANA MAX Live Console.
2. Reads live MCP health from the configured runtime URL.
3. Calls MCP `tools/list`.
4. Calls `tool_healthcheck` with safe scope.
5. Writes a local HTML file under the OS temp folder:
   ana-max-dashboard/dashboard.html
6. Opens that local file in the preferred browser. In the Windows lab this is
   Chrome by default: `C:\Program Files\Google\Chrome\Application\chrome.exe`.
   If that executable is unavailable, the extension falls back to VS Code
   `openExternal`.
```

## Evidence Source

```text
vscode_extension/extension.js
tests/runtime/test_vscode_extension.py
vscode_extension/CHANGELOG.md
```

## Sanitized Result Summary

The extension test verifies that the dashboard command:

```text
contains writeLocalDashboard
uses ana-max-dashboard/dashboard.html
calls tools/list with id dashboard-list-tools
calls tool_healthcheck with scope safe
opens vscode.Uri.file(filePath)
```

## What This Proves

- `Open Dashboard` no longer opens a blank legacy `8787` page when no dashboard
  server is running.
- The dashboard is generated from live MCP data.
- The dashboard path is local and temporary.
- The dashboard opens through `anaMax.preferredBrowserPath` first, with a safe
  fallback to the system/VS Code external opener.
- The command is read-only from the runtime perspective.

## Limitation

This proves the extension wiring and local HTML fallback. Visual rendering still
depends on VS Code opening the generated file in the local browser.

## Share Class

Sanitized. Safe after removing local temp paths and any private MCP response
payloads.
