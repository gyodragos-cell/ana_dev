# ANA MAX OS v2 Architecture

ANA MAX OS v2 is a deterministic local agent operating layer. The runtime is built around one rule: services do not call each other directly. Every action enters the orchestrator, receives a trace ID, is routed through the tool registry, runs inside the sandbox, emits events, and returns a structured response.

## Runtime Flow

1. A caller submits an `OSRequest` with a capability and payload.
2. The orchestrator validates the request against config and enabled services.
3. The tool router selects the highest-priority registered tool for that capability.
4. The sandbox checks the capability boundary and invokes the handler.
5. The fallback engine retries or degrades through registered fallback handlers.
6. The event bus records state transitions and allows replay.
7. The caller receives an `OSResponse` with output or a structured error packet.

## Components

- `core/orchestrator` owns routing, state transitions, cancellation, timeouts by policy, and strict service boundaries.
- `core/orchestrator/cooperation.py` owns cooperative behavior, OS v2 discipline metadata, self-repair for missing primary tools, and failure explanations.
- `core/event_bus` provides topic publish/subscribe, deterministic sequence numbers, replay, and an in-memory queue.
- `core/scheduler` orders dependent tasks deterministically and fails fast on missing dependencies or cycles.
- `core/sandbox` enforces allowed capabilities and creates an audit record for each execution.
- `core/error_model` standardizes recoverable and fatal errors as serializable packets.
- `core/fallback` runs the primary handler first, then fallback handlers in registry order.
- `services` contains deterministic service adapters for filesystem, HTTP, shell, and LLM work.
- `tools/registry` stores tool specs, fallback specs, and ANA skill validation.
- `tools/router` chooses tools predictably by priority and name.
- `config` is the single source of truth for mode, services, fallback attempts, sandbox limits, and logging level.

## Determinism

The default HTTP, shell, and LLM services are fake-first. They only return registered responses and fail when no deterministic response is available. The filesystem service is bounded by an explicit root. Runtime state transitions use sequence counters rather than wall-clock time.

## Boundaries

Services expose handlers, but they do not call one another. The orchestrator is the only coordination path. Any direct cross-service dependency should be modeled as a new capability and routed through the registry.

## Cooperation

The cooperation module avoids unnecessary blockers without guessing. If a primary tool is missing but a deterministic fallback is registered for the same capability, self-repair promotes that fallback into the sandboxed execution path and records the repair in event/output metadata. If no deterministic path exists, the response explains the blocker, returns the structured error, and gives the next safe action.
