# MCP Schema Lookup Example

Last updated: 2026-05-31

Purpose: show how ANA checks a tool schema before calling it.

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py --schema input_api_probe
```

## Sanitized Result

```json
{
  "name": "input_api_probe",
  "description": "Lab-only authorized probe for Windows input API usage.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "operation": {
        "enum": ["list_authorized", "spec", "execute"],
        "type": "string"
      },
      "api_name": {
        "enum": ["RegisterRawInputDevices", "GetAsyncKeyState", "GetKeyboardState"],
        "type": "string"
      },
      "confirm": {
        "type": "boolean"
      }
    }
  }
}
```

Missing tool lookup returns a compact failure:

```json
{
  "success": false,
  "error": "tool not found: definitely_missing_tool"
}
```

## Focused Test

```powershell
python -m pytest tests/runtime/test_ana_mcp_call.py -q
```

Expected:

```text
5 passed
```

## What This Proves

ANA can inspect tool contracts before execution:

- accepted operation names
- enum values
- parameter types
- missing-tool errors

This reduces blind calls and helps Codex choose the smallest valid request.

## Limitation

Schema lookup proves the advertised contract, not the runtime behavior. Behavior
still needs a focused tool test or MCP call.

## Share Class

`sanitized`: safe as protocol evidence. Do not publish private endpoints or
lab-only authorization data.
