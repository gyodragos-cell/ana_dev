# ANA MAX Dashboard UI

## Purpose

The ANA MAX Control Center is a dev-only dashboard shell for inspecting the AI OS runtime without executing tools.

## Panels

- Cluster: nodes, health, load, heartbeat.
- Agents: future process table.
- Sessions: future session list.
- Services: lifecycle and restart state.
- Events: safe observability stream.

## Safe-Mode Rules

- The UI is read-only.
- It does not call tools.
- It does not expose private memory values.
- It refreshes compact snapshots only.

## Current Location

- Backend provider: `core/dashboard_api.py`
- UI shell: `dashboard/index.html`
- VS Code hook: `ANA MAX: Open Dashboard`
