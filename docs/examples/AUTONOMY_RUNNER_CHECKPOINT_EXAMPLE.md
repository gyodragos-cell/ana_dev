# Autonomy Runner Checkpoint Example

Last updated: 2026-05-31

Purpose: show that ANA's autonomy runner can optionally save a compact session
checkpoint after the observe-route-context-verify-audit loop.

## Evidence

Focused test:

```powershell
python -m pytest tests/runtime/test_ana_autonomy_runner.py -q
```

Result:

```text
4 passed
```

## Contract

When `checkpoint=True`, the autonomy runner first verifies the normal safe
stack, then calls:

```text
session_checkpoint
```

The checkpoint includes:

- title
- summary
- current goal
- next steps
- changed-files summary
- validation summary
- risks
- sync status
- optional git state

## What This Proves

ANA can leave a compact handoff after an autonomy pass. That is useful when the
human switches tasks or Codex resumes later.

## Safety Boundary

The checkpoint is a compact lab memory artifact. It should not contain raw
screenshots, full logs, secrets, private payloads, or long terminal dumps.

## Limitation

The checkpoint write is optional. Normal autonomy passes can run read-only with
`checkpoint=False`.

## Share Class

`private-lab, sanitizable`: keep actual checkpoint files private. Share only the
shape of the workflow after review.
