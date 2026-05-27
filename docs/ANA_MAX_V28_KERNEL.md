# ANA MAX v28 Kernel Definition

## Stable Dev Components

- Remote execution with in-process transport, retry, timeout, and local fallback.
- Distributed memory with node-aware reads, writes, replication, and last-write-wins conflict handling.
- Cluster manager with node join, leave, heartbeat, health, and simple routing.
- Distributed runtime that routes tasks through cluster and remote execution.
- Event bus with categories, wildcard fan-out, async publish, and in-memory history.
- Semantic FS with virtual files, tags, metadata, and keyword lookup.
- OS permissions and security model boundaries for tools and nodes.
- Service manager with lifecycle, health checks, and restart counters.

## Experimental Components

- Dashboard API and UI remain dev-only.
- Networked remote execution is not enabled by default.
- Persistent distributed memory is not enabled.
- Policy and audit integration need more hardening before public runtime exposure.

## Deployment Modes

- Dev mode: local in-process distributed simulation and full tests.
- Safe mode: read-only dashboard and no external calls.
- Release mode: docs only until runtime hardening is complete.
