# ANA MAX OS v2 Tool Contracts

## Tool Spec

A tool is registered with:

- `name`: stable unique label inside a capability group.
- `capability`: route key such as `fs.read`, `http.request`, `shell.run`, or `llm.complete`.
- `handler`: callable that accepts a mapping and returns a mapping.
- `priority`: lower values win deterministic routing.
- `requirements`: optional structured metadata for policy checks.

## Handler Contract

Handlers must:

- Accept a dictionary-like payload.
- Return a dictionary-like result.
- Avoid direct calls to other services.
- Raise `ValidationError` for bad inputs.
- Raise `RoutingFailure` when deterministic data is missing.
- Let fatal sandbox or boundary errors propagate.

## Response Contract

Every orchestrated execution returns:

- `ok`: boolean success flag.
- `state`: final state, usually `completed` or `failed`.
- `trace_id`: caller-provided trace identifier.
- `output`: result payload when successful.
- `error`: structured error packet when failed.

## Fallback Contract

Fallback handlers are registered for the same capability as the primary tool. The fallback engine runs the primary handler first, then fallback handlers in registration order. Recoverable errors are captured in the final successful output. Fatal errors stop execution.

## Cooperation Contract

ANA cooperation is active at the orchestrator boundary. When routing cannot find a primary tool, the self-repair engine checks the registry for a deterministic fallback for the same capability. If one exists, the fallback is executed through the same sandbox path and the response includes `output.cooperation.self_repair`. If none exists, the failure response includes a cooperative explanation and next action instead of a silent refusal.

## Skill Contract

The skill engine validates the ANA skill format before a skill becomes authoritative implementation guidance. OS v2 skills must contain the A through K task sequence exactly once and in order.
