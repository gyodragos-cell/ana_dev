# ANA MAX v26 Runtime Blueprint

## Focus

v26 focuses on multi-agent orchestration, task graph planning, long-running
sessions, governance integration, and deployment readiness.

## Architecture

```text
User task
  -> Task Planner
  -> Agent Manager
  -> Policy Engine
  -> Orchestrator
  -> Execution + Observability
  -> Session + Memory
  -> Audit Trail
```

## Multi-Agent Orchestration

Roles include planner, executor, critic, repair, and observer. Agents exchange
in-memory messages and remain under one orchestrator.

## Task Graph Planner

The planner decomposes tasks into observe, execute, and verify nodes, then
assigns nodes to agents or tools.

## Long-Running Sessions

Sessions carry IDs, state, and session-bound memory. Session isolation prevents
memory from leaking across unrelated work.

## Governance Integration

Policy checks and human approval gates are evaluated before high-risk actions.
Audit records preserve decisions and outcomes.

## Deployment Model

Deployment prep exports config, runtime snapshots, registry summaries, and
policy data while keeping memory export blocked in safe-mode.
