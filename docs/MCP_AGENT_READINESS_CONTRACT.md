# MCP Agent Readiness Contract

Last updated: 2026-05-27

Purpose: define what "ANA MAX MCP is ready for agents" means. Tool count alone
is not enough.

## Required Endpoint State

Health must succeed:

```text
GET http://127.0.0.1:8766/health
```

Expected fields:

```json
{
  "status": "online",
  "mcp_ready": true,
  "tools_count": 86
}
```

`tools_count` may differ between clean public releases and mother-lab builds,
but readiness should fail if the core routing tools are missing or broken.

## Required Tools

`tools/list` must include:

```text
tool_router
agent_coach
```

`tools/list` must also include the REM/recalibration tool:

```text
session_rem_sleep
session_lifecycle
```

`agent_coach` input schema must include:

```text
action = recommend
```

## Required Calls

### tool_router

Request:

```json
{
  "name": "tool_router",
  "arguments": {
    "task": "MCP tool failed with schema mismatch action versus operation",
    "error": "Invalid value for operation",
    "max_tools": 4
  }
}
```

Expected response shape:

```json
{
  "success": true,
  "data": {
    "schema": "ana.tool_router.v1",
    "mode": "failure",
    "recommended_tools": ["error_radar", "agent_coach"]
  }
}
```

### agent_coach recommend

Request:

```json
{
  "name": "agent_coach",
  "arguments": {
    "action": "recommend",
    "task": "MCP tool failed with schema mismatch action versus operation",
    "error": "Invalid value for operation",
    "max_tools": 5,
    "include_prompt": false
  }
}
```

Expected response shape:

```json
{
  "success": true,
  "data": {
    "schema": "ana.agent_coach.recommend.v1",
    "primary_tool": "error_radar",
    "tool_stack": ["error_radar", "agent_coach", "ana_memory"],
    "next_action": "Call error_radar..."
  }
}
```

The exact stack may evolve, but `primary_tool` must be present and useful.

### session_rem_sleep latest

Safe read-only check after the REM tool is MCP-visible:

```json
{
  "name": "session_rem_sleep",
  "arguments": {
    "action": "latest"
  }
}
```

Expected response shape:

```json
{
  "success": true,
  "data": {
    "found": true,
    "path": "ANA_MAX/docs/rem_sleep/REM_SLEEP_REPORT_..."
  }
}
```

### failed tool guidance summary

Request:

```json
{
  "name": "tool_contract_validator",
  "arguments": {
    "action": "validate_tool",
    "tool_name": "definitely_missing_tool_for_guidance"
  }
}
```

Expected response shape:

```json
{
  "success": false,
  "guidance_summary": {
    "primary_tool": "error_radar",
    "tool_stack": ["error_radar", "agent_coach", "ana_memory"],
    "next_action": "Call error_radar...",
    "source": "agent_coach_recommend"
  },
  "data": {
    "guidance_summary": {
      "primary_tool": "error_radar",
      "tool_stack": ["error_radar", "agent_coach", "ana_memory"],
      "next_action": "Call error_radar...",
      "source": "agent_coach_recommend"
    }
  }
}
```

The top-level `guidance_summary` is required so MCP clients can display the next
action without digging into `data`. The nested copy remains for backward
compatibility. This proves the runtime helps agents recover from actual tool
failures.

## Readiness Tooling

Use:

```powershell
python ANA_MAX_Launcher/mcp_readiness_check.py --mcp-url http://127.0.0.1:8766/mcp
```

After adding a new MCP tool and restarting the server, require it explicitly:

```powershell
python ANA_MAX_Launcher/mcp_readiness_check.py --mcp-url http://127.0.0.1:8766/mcp --expect-tool session_rem_sleep
```

This check is used by launcher scripts and should stay stdlib-only.

## Failure Meaning

- `fetch failed` or connection refused: MCP server is not reachable. Restart it.
- `tool_router` missing: server is old or failed to import the new tool.
- `agent_coach recommend` missing: server is old or schema was not updated.
- `agent_coach recommend` returns no `primary_tool`: recommendation layer is not usable enough for agents.
- `failed_tool_guidance_summary` fails: auto-guidance is not attached to failed tool results, or the server has stale `tools/base.py`.

## Current Clean Smoke

Latest known clean smoke:

```text
ANA_MAX/dev_artifacts/reports/mcp_smoke_report_20260527_071334.json
65 pass, 20 skipped_unsafe, 0 fail
```
