# MCP Tools List Coverage Example

Last updated: 2026-05-31

Purpose: prove that the live MCP server exposes the expected tool surface, not
only a healthy `/health` endpoint.

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_nucleus_smoke.py --mcp-url http://127.0.0.1:8766/mcp
```

## Sanitized Result

Latest observed report:

```json
{
  "schema": "ana.nucleus_smoke.v1",
  "status": "PASS",
  "steps": [
    {
      "name": "health",
      "status": "PASS",
      "data": {
        "status": "online",
        "mcp_ready": true,
        "tools_count": 90
      }
    },
    {
      "name": "tools_list",
      "status": "PASS",
      "data": {
        "count": 90,
        "missing_required": []
      }
    }
  ]
}
```

## Required Nucleus Tools

`tools/list` must include:

```text
tool_router
agent_coach
code_context_pack
graph_context_pack
tool_healthcheck
error_radar
session_audit
```

## What This Proves

ANA's MCP server is not merely online. The nucleus tools are visible through the
actual MCP `tools/list` contract, so Codex/VS Code can route work through the
same interface that the lab verifies.

## Limitation

`tools/list` coverage proves visibility, not behavior. Behavior is verified by
the rest of Nucleus Smoke and the focused runtime tests.

## Share Class

`sanitized`: safe as architecture evidence after removing local report paths and
private machine state.
