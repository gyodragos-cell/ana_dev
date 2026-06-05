# ANA MAX OS v2 Specification

## Goals

ANA MAX OS v2 provides a compact, deterministic agent runtime with observable execution, structured failures, strict service boundaries, and a predictable tool routing model.

## Disciplines

- Determinism: identical registered inputs produce identical outputs.
- Single source of truth: config, registry, state transitions, and event replay are centralized.
- Zero guessing: missing routes, unknown commands, unregistered HTTP responses, and unknown prompts fail with structured errors.
- Strict boundaries: services are invoked through orchestrator capabilities only.
- Fail fast: validation, routing, sandbox, and dependency errors stop the current request immediately.
- Observability: each request publishes traceable state events and returns audit metadata.

## Directory Contract

The OS v2 implementation lives only inside the blueprint directories:

- `ana/core/orchestrator`
- `ana/core/event_bus`
- `ana/core/scheduler`
- `ana/core/sandbox`
- `ana/core/error_model`
- `ana/core/fallback`
- `ana/services/fs`
- `ana/services/http`
- `ana/services/shell`
- `ana/services/llm`
- `ana/tools/registry`
- `ana/tools/router`
- `ana/config`
- `ana/logs`
- `ana/tests/unit`
- `ana/tests/integration`
- `ana/docs`

## A to Z Implementation Order

A. Create the exact directory structure.
B. Create the orchestrator state machine and routing path.
C. Create the event bus with topics, queue, and replay.
D. Create the sandbox with capability isolation and audit metadata.
E. Create the error model with recoverable and fatal packets.
F. Create fallback chains and retry policy.
G. Create the tool manager with registry, validation, capability mapping, and routing.
H. Create the config system with defaults and schema.
I. Create structured logging semantics through traceable events and response audit data.
J. Create unit and integration tests.
K. Create architecture, OS, and tool contract documentation.

## Skill Format

An ANA skill must include a title, numbered sections for context, scope, directory structure, OS components, disciplines, implementation tasks, Codex rules, and expected output. OS v2 skills must declare task headings A through K in order.
