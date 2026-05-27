# ANA MAX AI OS Snapshot

## Kernel

ANA MAX acts as a local AI OS kernel: scheduler, policy boundary, event hub,
memory coordinator, and execution router.

## Processes

Agents behave like processes with lifecycle state and roles.

## Semantic FS

Semantic FS maps virtual paths to memory-backed content and semantic lookup.

## Permissions

OS permissions define inheritance and enforcement for tools, memory, and nodes.

## Event Bus

Unified event bus routes categorized events to dashboard and runtime consumers.

## Services

Service manager tracks long-running services and health checks.

## Distributed Runtime

Distributed runtime introduces nodes, messages, remote execution, cluster
health, and failover concepts.

## Real vs Stub Status

Real in dev:

- remote execution retry, timeout, and local fallback
- distributed memory node stores and simulated replication
- cluster join, leave, heartbeat, health, and routing
- distributed runtime task routing
- event bus categories, wildcard fan-out, async publish, and history
- semantic FS virtual files, tags, metadata, and keyword lookup
- OS permissions inheritance and enforcement
- service lifecycle, health, and restart counters
- security model node/tool allow-deny checks

Still dev-only:

- real networked node transport
- persistent distributed storage
- production dashboard serving
- public runtime sync
