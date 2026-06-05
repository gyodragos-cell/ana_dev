# Nucleus Smoke Summary Example

## Purpose

Show the smallest high-signal check ANA should run before serious lab work.

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_nucleus_smoke.py --mcp-url http://127.0.0.1:8766/mcp
```

## Sanitized Result Summary

Latest known smoke report:

```text
schema: ana.nucleus_smoke.v1
status: PASS
summary: 10 pass / 0 warn / 0 fail
tools_count: 90
tool_router: PASS
agent_coach: PASS
code_context_pack: PASS
graph_context_pack: PASS
tool_healthcheck: 7 OK / 0 FAIL
error_radar: PASS, 1 workspace finding surfaced for review
session_audit: trust 100
context_maps: PASS, Code Map and Graph Map are fresh
```

## What This Proves

- MCP health is online.
- Required nucleus tools are present.
- Router and coach can recommend next actions.
- Code Map and Graph Map are available through context packs.
- Code Map and Graph Map freshness is checked after the graph context probe, so
  transient graph refreshes do not create false warnings.
- Healthcheck has no tool failures.
- Error Radar can surface workspace risks without blocking the smoke pass.
- Session Audit can produce a trust score.

## Routing Rule

Run Nucleus Smoke before:

```text
large edits
extension packaging
lab quality gates
autonomy runner sessions
Linux migration checks
handoff to a future session
```

## Limitation

Nucleus Smoke is a readiness check, not a full regression suite. It proves the
core loop is alive; larger changes still need focused tests and the broader lab
quality gate.

## Share Class

Sanitized. Safe after removing local report paths and private workspace details.
