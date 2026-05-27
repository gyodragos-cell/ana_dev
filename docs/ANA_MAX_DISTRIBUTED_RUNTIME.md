# ANA MAX Distributed Runtime

## Node Roles

- Coordinator: owns planning and policy.
- Worker: executes assigned safe tasks.
- Memory node: stores distributed memory.
- Observer: reports health and telemetry.

## Distributed Orchestrator

The orchestrator schedules across nodes, tracks dependencies, and isolates
failure domains. Current implementation is a no-network stub.

## Distributed Memory

Distributed memory exposes read/write operations with failure-aware responses.
Private memories remain lab-only.

## Remote Agents

Remote agents use a transport interface. Tests use fake transports only.

## Failure Domains

Each node should fail independently without corrupting policy, audit, or memory
state for other nodes.
