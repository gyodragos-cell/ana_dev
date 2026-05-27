# ANA MAX Tool Catalog And Capability Map

## Capabilities

- `safe_read`: read-only operations.
- `safe_write`: file or state mutation.
- `network_allowed`: network access.
- `subprocess_allowed`: process execution.

## Risk Levels

- Low: read-only inspection.
- Medium: local writes with confirmation.
- High: subprocess, network, desktop control, public release writes.

## Policies

Safe-mode blocks high-risk operations by default. Dev-mode and write-mode need
explicit operator intent.
