# Cluster Membership - Transport Protocol

Envelope:
- version: 1
- type: "cluster.join" | "cluster.leave" | "cluster.heartbeat"
- source_node: node_id of sender
- target_node: "*" for broadcast, or specific node_id
- timestamp: ISO8601 string
- payload: type-specific

Join:
- type: "cluster.join"
- payload: { node_id, address, port, capabilities }
- effect: receiver creates/updates ClusterNode, sets state=ACTIVE.

Leave:
- type: "cluster.leave"
- payload: { node_id, reason }
- effect: receiver marks node as DEAD via evict().

Heartbeat:
- type: "cluster.heartbeat"
- payload: { node_id }
- effect: receiver calls heartbeat(node_id).

Failure detection:
- check_heartbeats(max_missed=N):
  - ACTIVE + N misses -> SUSPECT
  - SUSPECT + N misses -> DEAD

Compatibility:
- If no transport is configured, cluster_manager continues to work in local mode.
- Existing behavior of heartbeat() is preserved and extended, not replaced.

# Distributed Memory - Sync Protocol

Message types:
- "memory.write"
  payload: { key, value, version, node_id, timestamp }

- "memory.replicate"
  payload: { key, value, version, source_node }

- "memory.pull_request"
  payload: { node_id, keys?: [] }

- "memory.pull_response"
  payload: { entries: [{ key, value, version }] }

- "memory.conflict"
  payload: { key, versions: [{ node_id, value, version }] }

Decisions:
- Conflict resolution: last-write-wins by timestamp, existing resolve_conflict() preserved.
- Replication is fire-and-forget over transport, no ACK in phase 131-134.
- pull_request/pull_response used for full sync on node join.

# Distributed Memory - Sync Protocol (Phase 131-134)

Messages:
- "memory.write": broadcast on local write, best-effort replication.
- "memory.pull_request": used by a node to request full or partial sync.
- "memory.pull_response": used to send back key/value/version entries.

Conflict resolution:
- resolve_conflict(local_value, remote_value) is the single source of truth.
- Default policy: last-write-wins by timestamp if implemented, but this phase only wires the hook.

Replication semantics:
- Fire-and-forget over transport, no ACK in this phase.
- Full sync on join is done via pull_request/pull_response.

Compatibility:
- If transport is None, DistributedMemory behaves exactly as before.
- Existing write() semantics are preserved; network sync is additive.

# Distributed Event Bus - Protocol

Message type:
- "event.publish"
  payload:
  - topic: str
  - data: any JSON-serializable
  - origin_node: str
  - local_only: optional bool, default false

Decisions:
- Event bus is topic-based, string topics such as "node.suspect" and "memory.write".
- Wildcards such as "node.*" are local-only for now; not expanded over network in this phase.
- Replication is best-effort, fire-and-forget over transport.
- No delivery guarantees, ACK, or retries in PHASE 135-137.
- Local subscribers always see events even if transport is None or failing.

# Distributed Event Bus - Protocol (Phase 135-137)

Message:
- type: "event.publish"
- payload:
  - topic: string
  - data: JSON-serializable
  - origin_node: node_id of original publisher
  - local_only: not propagated over network, used only locally

Semantics:
- Local publish:
  - Always delivers to local subscribers.
  - If local_only=False and transport is configured, broadcast over network.
- Remote event:
  - Received via handle_event_message().
  - Delivered only to local subscribers, no re-broadcast.
- Delivery guarantees:
  - Best-effort, fire-and-forget.
  - No ACK, no retries in this phase.

Compatibility:
- If transport is None, EventBus behaves exactly as before.
- Existing subscribe/publish APIs are preserved.

# Distributed FS Sync - Protocol

Message types:
- "fs.update"
  payload:
  - path: str
  - content: str or bytes encoded as transport-safe text
  - mtime: ISO8601 or numeric timestamp
  - node_id: str

- "fs.delete"
  payload:
  - path: str
  - mtime: ISO8601 or numeric timestamp
  - node_id: str

- "fs.pull_request"
  payload:
  - node_id: str
  - paths: optional list of paths; null means full tree

- "fs.pull_response"
  payload:
  - entries: list of { path, content, mtime, deleted? }

Decisions:
- Conflict resolution: last-write-wins by mtime.
- Replication is fire-and-forget over transport, no ACK in phase 138-139.
- pull_request/pull_response used for full sync on node join or manual resync.
- Binary content is deferred; this phase uses UTF-8 text-safe content.

# Distributed FS Sync - Protocol (Phase 138-139)

Messages:
- "fs.update": file content update, includes path, content, mtime, node_id.
- "fs.delete": file deletion, includes path, mtime, node_id.
- "fs.pull_request": request for full or partial FS tree.
- "fs.pull_response": response with entries {path, content, mtime, deleted?}.

Conflict resolution:
- Last-write-wins by mtime.
- Remote update/delete applied only if remote mtime is newer than local.

Replication semantics:
- Fire-and-forget over transport, no ACK in this phase.
- Full sync on join via fs.pull_request/fs.pull_response.

Compatibility:
- If transport is None, FS sync behaves exactly as before: local-only.
- Existing write/delete APIs are preserved; network sync is additive.

# Full Integration Scenario - Phase 140

- All distributed subsystems must interoperate: cluster, memory, event bus, and fs sync.
- FakeTransportMulti simulates a multi-node network.
- No real network, no threads, no async loops are used.
- Message routing is deterministic and synchronous.
- Heartbeat -> suspect -> dead -> recovery flows are validated.
- Memory and FS pull sync are validated on join/manual sync.
- Event bus fan-out is validated.
- LWW semantics are validated for memory and FS at subsystem level.

# Distributed Kernel v23 - Phases 141-200

Self-healing:
- Node health monitor is tick-based and synchronous.
- Unhealthy nodes move to SUSPECT; recovered nodes move to ACTIVE.
- Events: "node.unhealthy", "node.recovered".

Adaptive routing:
- Routing skips SUSPECT and DEAD nodes.
- ACTIVE nodes are preferred; JOINING nodes are fallback candidates.
- Capability routing uses per-capability round-robin.
- Event: "routing.changed".

Distributed services:
- Service registry is replicated into distributed memory under "service:<name>".
- Service failover reassigns services from dead nodes to the best available node.
- Events: "service.start", "service.stop", "service.crash".

Ephemeral locks:
- Locks are in-memory with TTL checks driven by explicit ticks.
- Lock state is replicated into distributed memory under "lock:<key>".
- Events: "lock.acquired", "lock.released".

Distributed tasks:
- Tasks are routed through cluster_manager.get_best_node().
- Task state is replicated into distributed memory under "task:<task_id>".
- Events: "task.submitted", "task.started", "task.completed", "task.failed".

Sync, partitions, and consistency:
- Join sync is modeled through existing memory/fs pull requests.
- Leave cleanup removes node-specific memory and exposes FS cleanup hooks.
- Network partitions are simulated by FakeTransportMulti disconnect/reconnect.
- Consistency modes: eventual, strong_local, hybrid.
- strong_local suppresses remote broadcasts.

Observability, logs, debug, recovery:
- MetricsManager tracks counters and emits "metrics.update".
- Distributed logs use "log.entry".
- Debug hooks use "debug.breakpoint" and "debug.inspect".
- RecoveryManager restores memory, services, and locks from snapshots.

Future phases:
- Phases 155-200 remain incremental hardening targets: unified handlers,
  pipelines, distributed agents, adaptive AI routing, chaos tests, and kernel
  consistency validation.

# ANA MAX AI Kernel v1 Naming

- "ANA MAX AI Kernel v1" is the dev/lab name for the first integrated
  simulated distributed kernel.
- It covers transport envelopes, cluster membership, health monitoring,
  adaptive routing, distributed memory, FS sync, event bus, services, locks,
  tasks, metrics, debug hooks, and recovery scaffolding.
- It remains safe-mode and dev-only until a separate public sync decision.
- The canonical dev snapshot document is docs/ANA_MAX_AI_KERNEL_V1.md.

# ANA MAX AI Kernel v1 - Phases 201-500

Distributed model runtime:
- Model registry stores metadata under "model:<name>:<version>".
- Placement stores records under "placement:<name>:<version>".
- Inference protocol uses "model.infer.request" and "model.infer.response".
- Inference is simulated only: no real model execution.
- Metrics use per-model counters and "model.metrics.update".

Agent runtime:
- Agent registry stores state under "agent:<name>".
- Agent messaging uses "agent.message" semantics with local inbox delivery.
- Lifecycle events: "agent.started", "agent.stopped", "agent.crashed".
- Agents can write through distributed memory, fs_sync, and task_manager.

DevTools:
- Debug events: "debug.breakpoint.set", "debug.breakpoint.hit", "debug.inspect.response".
- Logs UI protocol: "ui.logs.subscribe", "ui.logs.event".
- FS viewer protocol: "ui.fs.list", "ui.fs.read", "ui.fs.write".
- Memory viewer protocol: "ui.memory.list", "ui.memory.get", "ui.memory.set".

Cloud mode:
- Federation protocol: "federation.heartbeat", "federation.state", "federation.route".
- Cross-cluster routing is simulated through local federation state.

AI-native kernel:
- Vector memory stores small vectors and uses cosine search, no ANN service.
- Model-aware routing can use placement, cluster capabilities, and future vector locality.
- Pipelines are synchronous chains of fake model/agent steps.
- Adaptive policies are represented as routing inputs and remain simulated.

Compatibility:
- All new systems are additive.
- No real network, threads, async loops, or model calls are introduced.
- Public release remains untouched until an explicit sync phase.

# Model Runtime - Registry, Placement, Routing, Inference (PHASE 201-210)

model_registry:
- keys: "model:{name}:{version}"
- values: metadata dict with name, version, capabilities, tags, path, node_id
- events: "model.registered", "model.unregistered"

placement_manager:
- keys: "placement:{model}:{version}"
- values: { model, version, nodes, policy }
- events: "model.placement.changed"

routing:
- verifies model existence through model_registry
- prefers nodes listed in placement
- skips SUSPECT and DEAD nodes by only considering ACTIVE healthy nodes
- uses round-robin per (model, version)
- falls back to cluster_manager.get_best_node()

inference protocol:
- "model.infer.request"
  payload: { model, version, input, request_id, origin_node }
- "model.infer.response"
  payload: { request_id, output, error }
- inference is simulated only using deterministic echo responses
- best-effort, no strong delivery guarantees in this phase

Compatibility:
- Transport is optional.
- If no transport exists, only local routing can complete.
- No real ML or real network behavior is introduced.

# Public Release Build - Phases 501-1000

Runtime stabilization:
- Kernel summaries expose health, debug, metrics, recovery, consistency,
  routing, model, agent, pipeline, vector, and federation views.
- Cluster state includes kernel_version, cluster_id, domain, labels, and
  annotations.

Services:
- Service runtime v2 adds dependencies, priorities, annotations, scaling
  metadata, summaries, and existing lifecycle events.

DevTools:
- Debugger, profiler, logs, FS viewer, memory viewer, and kernel inspector
  remain simulated and synchronous.

Cloud mode:
- Federation domains/regions/zones are represented as local state.
- Cross-cluster routing is deterministic and simulated.

AI Kernel v2:
- Cognitive runtime adds episodic memory, semantic memory, consolidation,
  pruning, planning, and workflow simulation.

Packaging and docs:
- PackagingManager generates dev-only manifests, validators, release notes, and
  changelog previews.
- No PHASE 1000 public copy, tag, push, or release action is performed here.
