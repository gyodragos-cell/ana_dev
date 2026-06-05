# MCP Tools Call Failure Normalization Example

Last updated: 2026-05-31

Purpose: prove that a failed MCP tool call returns a compact JSON failure
instead of an ambiguous terminal crash.

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py definitely_missing_tool
```

## Sanitized Result

```json
{
  "success": false,
  "data": null,
  "message": "",
  "error": "Unknown tool: definitely_missing_tool"
}
```

The CLI exits non-zero for normalized tool failure, so scripts and gates can
detect the failure without scraping free-form text.

## Focused Test

```powershell
python -m pytest tests/runtime/test_ana_mcp_call.py -q
```

Expected:

```text
3 passed
```

## What This Proves

ANA's MCP wrapper preserves the important failure fields:

- `success=false`
- short `error`
- no traceback required for normal unknown-tool failures
- stable non-zero exit code for automation

## Correct Follow-Up

Do not retry the same missing tool blindly. Use:

```text
tools/list -> tool_router -> agent_coach -> smaller verified retry
```

## Limitation

This example proves wrapper normalization for a known missing-tool failure. It
does not prove that every downstream tool error is semantically correct.

## Share Class

`sanitized`: safe as protocol evidence. Do not publish raw private MCP logs,
local endpoints from non-lab systems, or session telemetry.
