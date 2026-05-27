# QA Pass 1.0.12 MCP Lifecycle

Date: 2026-05-27

Status: PASS

## Scope

This QA pass validates the v1.0.12 Stable Cockpit Baseline plus the live
mother-lab MCP lifecycle server.

## Confirmed Live State

```text
MCP URL: http://127.0.0.1:8766/mcp
Health: online
mcp_ready: true
Mother-lab tools_count: 86
Clean public release tools_count: 85
```

Required tools are visible:

```text
ana_identity
tool_router
agent_coach
session_rem_sleep
session_lifecycle
workspace_situational_awareness
autonomy_dashboard
```

## Calm Flow Results

Read-only and recommendation flows run without generic confirmation popups:

```text
ana_identity: PASS
tool_router: PASS
agent_coach action=recommend: PASS
session_lifecycle action=wake: PASS
session_lifecycle action=rest consolidate=false: PASS
autonomy_dashboard: PASS
```

`ana_identity` now reports the live mother-lab count correctly:

```text
ANA identity ready (86 active tools).
```

## Security Gate Results

Risky tools remain gated when called without `confirm=True`:

```text
terminal: requires_confirmation
windows_uia_bridge: requires_confirmation
bash_exec: requires_confirmation
edit/write paths: gated or blocked unless schema and confirmation are valid
```

## Extension Audit

The cockpit extension is aligned with v1.0.12:

```text
name: ana-antigravity-chat
displayName: ANA MAX - Hybrid AI Cockpit
publisher: d4d8176a-bb85-66ef-93dd-a58bc9ddfdad
version: 1.0.12
```

Beginner flow is documented:

```text
Start Runtime -> Smart Ready -> Wake -> Recommend -> Rest Preview -> Save REM
```

## Notes

- The lab/public count difference is intentional and documented: the mother lab
  currently exposes 86 tools after `session_lifecycle`; the clean public release
  baseline exposes 85 tools.
- Temporary QA scripts and outputs belong in `ANA_MAX/sandbox/`.
- Keep v2 cleanup separate from the stable v1.0.12 baseline.

