# ANA Agent Trace Schema

Purpose: define ANA's local-first trace vocabulary for agent runs, tool calls,
verification, audit, and checkpoints.

This is inspired by OpenTelemetry-style spans, but ANA stores compact local JSON
records with digests instead of raw private payloads.

## Schema

Runtime helper:

```text
ANA_MAX/core/agent_trace_schema.py
```

Schema name:

```text
ana.agent_trace_span.v1
```

## Span Fields

| Field | Meaning |
| --- | --- |
| `run_id` | Session/run identity. |
| `trace_id` | Trace identity, defaults to `run_id`. |
| `span_id` | Unique local span id. |
| `parent_span_id` | Optional parent span id for step hierarchy. |
| `operation` | One of `agent_run`, `workflow`, `tool_call`, `context_pack`, `verification`, `audit`, `checkpoint`. |
| `tool_name` | Tool name when operation is `tool_call`. |
| `status` | `ok`, `warn`, `error`, `blocked`, or `skipped`. |
| `risk_level` | `low`, `medium`, or `high`. |
| `started_at` / `ended_at` | UTC timestamps. |
| `duration_ms` | Non-negative duration. |
| `input_digest` | SHA-256 digest of redacted input payload. |
| `result_digest` | SHA-256 digest of redacted result payload. |
| `evidence` | Sanitized compact evidence, never raw logs/screenshots. |
| `raw_private_payloads` | Always `false`. |
| `span_digest` | SHA-256 digest of the span minus `span_digest`. |

## Rules

- Do not store raw private payloads in trace spans.
- Redact secret-like keys before digesting or exposing evidence.
- Redact local user paths.
- Use hierarchy: `agent_run` -> `workflow` -> `tool_call` / `context_pack` /
  `verification` -> `audit` / `checkpoint`.
- Keep this local until public-sync review.

## Near-Term Integration Points

- `session_audit`: include or derive spans from existing audit events.
- `ana_autonomy_runner.py`: emit a span per major step.
- Implemented: `ana_autonomy_runner.py` now writes `trace_spans` in each
  autonomy report.
- `ana_patch_advisor.py`: emit suggest-only analysis span.
- Future Graph Map blast-radius query: emit `context_pack` or `verification`
  spans when selecting impacted files/tests.

## Why This Matters

ANA should help Codex understand not only what happened, but which step happened
under which run, what evidence existed, whether verification passed, and what
changed between attempts. This reduces blind retries and makes self-healing
auditable.
