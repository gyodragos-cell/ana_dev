# Permission Blocked Action Example

Last updated: 2026-05-31

Purpose: prove that ANA blocks confirmation-gated tools when explicit operator
confirmation is missing.

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py input_api_probe operation=list_authorized
```

## Sanitized Result

```json
{
  "success": false,
  "message": "Tool requires confirmation: call input_api_probe with confirm=True",
  "guidance_summary": {
    "primary_tool": "error_radar",
    "headline": "Use error_radar next for failure; coach severity is warn.",
    "source": "agent_coach_recommend"
  },
  "signals": [
    {
      "type": "missing_confirm",
      "tool": "input_api_probe"
    }
  ]
}
```

## What This Proves

The permission manifest is active. `input_api_probe` belongs to the
`security_lab` profile and requires confirmation, so ANA blocks the call before
the tool body runs.

This matters because sensitive tools should fail closed:

- no silent execution
- no accidental probing
- no retry loop without changed input
- auto-guidance explains the next safe step

## Correct Follow-Up

If the operator intentionally wants the safe metadata/spec path, retry with
explicit confirmation:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py input_api_probe operation=list_authorized confirm=true
```

For actual execution, the bar is higher: authorized target, short duration,
aggregate-only result, and clear local diagnostic purpose.

## Limitation

This example proves policy blocking, not runtime diagnostics. It does not attach
to a process and does not collect any input.

## Share Class

`sanitized`: safe as a policy example. Do not publish private authorization
lists, local targets, raw auto-guidance logs, or operational instrumentation
templates.
