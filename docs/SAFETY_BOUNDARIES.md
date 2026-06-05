# ANA MAX Lab Safety Boundaries

Last updated: 2026-05-29

This lab is for authorized local development, QA, and agent-runtime research.
These rules are part of the engineering contract for anyone working in the
workspace.

## Default Posture

```text
local-first
operator-visible
explicit confirmation for risky actions
no public sync by default
no private data export
```

## Sensitive Keyword Trigger

Certain words should trigger a short boundary check, not panic and not blind
execution.

Examples:

```text
cyber
Frida
hooking
process memory
input API
Raw Input
DirectInput
GetAsyncKeyState
pentest
malware
anti-cheat
exploit
token
credential
exfiltration
```

When a sensitive keyword appears, the agent must pause and classify the request:

```text
Is it local?
Is it authorized?
Is it defensive, diagnostic, or educational?
Is it lab-only?
Can output be aggregated/sanitized?
Does it need explicit operator confirmation?
```

If the answer is safe, continue with the smallest useful diagnostic path. If
not, park the idea in docs/backlog or refuse the unsafe part. This rule applies
to Codex and any sub-agent working under this lab.

## Allowed By Default

- Read local source files in the active workspace.
- Run focused tests and compile checks.
- Call read-only MCP diagnostics.
- Generate local reports under `ANA_MAX/dev_artifacts/reports/`.
- Build Code Map and Graph Map from local files.
- Save checkpoints and REM summaries for lab continuity.

## Requires Explicit Operator Intent

- Desktop control and UI mutation.
- Subprocess actions that affect the host.
- Network access beyond local health checks.
- Public release sync, Git push, marketplace update, or external publishing.
- Dynamic runtime instrumentation.
- Input API probing.
- Any action against private/external systems.

## Lab-Only Areas

The following are lab-only unless reviewed and sanitized:

- `input_api_probe`
- Frida/runtime instrumentation wrappers
- desktop screenshots and visual evidence
- local process diagnostics
- memory databases
- session archives
- audit JSON generated from private runs
- private config and authorization lists

## Frida And Input Diagnostics

Use only for authorized local diagnostics. Do not use for stealth, persistence,
credential capture, bypassing anti-cheat, or monitoring people. Prefer static
or aggregate diagnostics first:

```text
foreground_ui_snapshot
event_stream
binary_map
input_api_probe spec/list_authorized
```

Active instrumentation requires explicit operator intent and should return
aggregated, non-sensitive output whenever possible.

## Public Release Boundary

Public-safe content may include:

- architecture summaries
- high-level policies
- sanitized tests
- setup docs
- reviewed tool contracts

Public release must not include:

- private memory databases
- logs
- screenshots
- local paths and machine state
- API keys/tokens/secrets
- private endpoint configs
- raw session histories
- dynamic instrumentation demos with private process data

## Failure Rule

After two similar failures, stop repeating the same action. Use:

```text
error_radar -> agent_coach -> tool_router -> smaller verified retry
```

## Verification Rule

Before claiming the lab is healthy, run:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_nucleus_smoke.py --mcp-url http://127.0.0.1:8766/mcp
```

For broader checks:

```powershell
python ANA_MAX/dev_artifacts/scripts/lab_quality_gate.py
```
