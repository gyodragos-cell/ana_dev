# Runtime Deep Router Escalation Example

Last updated: 2026-05-31

Purpose: show how ANA routes an under-the-hood diagnostic request without
jumping straight to invasive instrumentation.

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py tool_router mode=runtime_deep task="authorized local binary and input architecture diagnostics" max_tools=6
```

## Sanitized Result

```json
{
  "schema": "ana.tool_router.v1",
  "mode": "runtime_deep",
  "headline": "Use under-the-hood diagnostics only when normal evidence is not enough.",
  "recommended_tools": [
    "tool_healthcheck",
    "event_stream",
    "binary_map",
    "input_api_probe",
    "windows_deep_sight",
    "windows_insight"
  ],
  "tool_profiles": {
    "tool_healthcheck": ["core"],
    "event_stream": ["core"],
    "binary_map": ["security_lab"],
    "input_api_probe": ["security_lab"],
    "windows_deep_sight": ["windows"],
    "windows_insight": ["windows"]
  },
  "guardrail": "Frida and deep diagnostics are controlled lab tools."
}
```

## What This Proves

ANA can escalate from normal diagnostics to deeper runtime evidence in a
controlled order:

1. Check tool health and recent events first.
2. Use static `binary_map` before any dynamic instrumentation.
3. Generate an `input_api_probe` spec before any execution.
4. Keep Frida and other deep instrumentation as explicit lab-only tools.

## Safety Boundary

This example is a router recommendation only. It does not attach to a process,
hook APIs, read memory, capture input, or execute Frida.

Deep diagnostics remain valid only when all of these are true:

- target is local and authorized
- purpose is defensive, diagnostic, or educational
- operator intent is explicit
- output is short, aggregated, and sanitized
- the smallest useful tool stack is enough

## Limitation

The recommendation is not proof that the target process is safe or that dynamic
instrumentation is allowed. It only proves that ANA chooses a disciplined route
before taking action.

## Share Class

`sanitized`: safe as a high-level architecture example. Do not publish private
targets, raw logs, memory values, input traces, Frida templates, or session
history.
