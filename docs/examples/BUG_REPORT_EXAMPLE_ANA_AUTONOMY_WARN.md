# Bug Report Example - Autonomy Pass UI Snapshot Warning

## Title

Resolved: Autonomy Pass returned non-blocking warning on foreground UI snapshot.

## Summary

After running ANA Autonomy Pass, the workflow completes successfully but reports
a warning for `foreground_ui_snapshot`. The warning does not block the pass, but
it lowers confidence and should be tracked.

## Environment

- Date: 2026-05-31
- Status: historical resolved regression example; current lab state is tracked
  by Operator Status and the latest Autonomy Pass report.
- OS: Windows lab
- App/build/version: ANA MAX MCP 18.0-MAX, extension v1.0.46
- Device/browser/emulator: VS Code local workspace
- Account/test profile: private mother lab
- Network/setup: local MCP at `http://127.0.0.1:8766/mcp`
- Related tool/profile: `foreground_ui_snapshot`, `windows` profile

## Preconditions

ANA MCP server is running and extension has been restarted.

## Steps To Reproduce

1. Start or verify ANA MCP server.
2. Run:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_autonomy_runner.py --mcp-url http://127.0.0.1:8766/mcp --goal "Post extension restart verification"
```

3. Review Autonomy Pass output.

## Expected Result

Autonomy Pass should complete with all steps passing, or the UI snapshot warning
should include a precise reason and remediation.

## Actual Result

Autonomy Pass returns `WARN` because `foreground_ui_snapshot` attaches auto
guidance from ANA memory/coach. Other checks pass.

## Resolution

Fixed on 2026-05-31.

Root cause:

```text
ana_autonomy_runner.py sent max_elements as an integer, while the
foreground_ui_snapshot MCP schema expects a string.
```

Fix:

```text
Send max_elements as "20".
Retry one transient empty/failed foreground snapshot.
Compact the real snapshot shape: active_app, title, buttons, inputs,
visible_text, detected_errors.
```

Verified result:

```text
ANA Autonomy: PASS (11 pass / 0 warn / 0 fail) trust=86%
[PASS] foreground_ui_snapshot UI snapshot captured for: Code
```

## Frequency

Resolved in the Windows lab. Keep this as a regression example.

## Severity

Low to Medium.

Reason: core workflow still succeeds, but UI observation is part of the
confidence signal.

## Evidence

Example output:

```text
ANA Autonomy: WARN (9 pass / 1 warn / 0 fail) trust=86%
[WARN] foreground_ui_snapshot Auto guidance attached from ANA memory/coach.
```

Report path example:

```text
ANA_MAX/dev_artifacts/reports/autonomy_runner_20260530_220739.json
```

## Impact

Historical impact:

ANA remains usable, but live UI observation is not fully trusted in the current
pass. Operators should treat Autonomy Pass as healthy-with-warning rather than
perfect.

## Suspected Area

Windows UI observation profile or result classification from
`foreground_ui_snapshot`.

## Workaround

Historical workaround:

Use Nucleus Smoke, tool healthcheck, and code/graph context as the primary
signals. Treat UI snapshot as advisory until stabilized.

## Recommended Next Step

Keep the regression test in `tests/runtime/test_ana_autonomy_runner.py` and
rerun Autonomy Pass after changing UI-observation arguments.

## Privacy / Safety Notes

This example is sanitized. Do not include screenshots or private UI text in
public examples.
