# ANA MAX Governance

## Policy Layers

- Safe-mode: read-only by default; blocks writes, subprocess, and network.
- Dev-mode: local lab execution with explicit operator responsibility.
- Write-mode: controlled release or workspace writes only.

## Approval Flow

High-risk actions require human approval before execution. Approval decisions
should be recorded in the audit trail.

## Audit Flow

Audit records cover tool calls, routing decisions, repairs, optimization
changes, workspace switches, and human approval decisions. Secret-like fields
are redacted.

## Deployment Considerations

Deployment exports must exclude secrets, private memory, logs, screenshots, and
local machine paths. Memory export remains blocked in safe-mode.
