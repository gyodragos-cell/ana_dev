# Trace Report Example

Purpose: validate and summarize `ana.agent_trace_span.v1` spans emitted by an
Autonomy Runner report.

Profile: `core/private_lab`

Share class: `private-lab, sanitizable`

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_trace_report.py
```

By default this reads the latest `autonomy_runner_*.json` report.

## Expected Shape

```text
ANA Trace Report: PASS steps=13 spans=13 aligned=True ops={'audit': 1, 'context_pack': 4, 'tool_call': 2, 'verification': 6}
```

The JSON report uses:

```text
schema: ana.trace_report.v1
```

## What It Proves

- Autonomy steps and trace spans are aligned.
- Every span validates against `ana.agent_trace_span.v1`.
- The report summarizes operations/statuses without exposing raw private
  payloads.

## Limitation

This validates report-local traces. `session_audit` can include a compact trace
summary after MCP reload, but raw trace spans are still not merged into
`event_stream`.
