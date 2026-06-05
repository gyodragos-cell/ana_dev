# Session REM Sleep Example

## Purpose

Show how ANA analyzes recent checkpoints, telemetry, and learned lessons to
produce a compact retrospective for the next session.

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py session_rem_sleep action=analyze checkpoint_limit=5 telemetry_limit=20 lesson_limit=5
```

## Sanitized Result Summary

The REM sleep analysis returned:

```text
schema: ana.session_rem_sleep.v1
headline: REM sleep analyzed 7 success signals, 4 friction signals, and 4 next-session rules.
inspected:
  checkpoints: 5
  telemetry_entries: 20
  lessons: 5
patterns:
  - Validation-first work is paying off.
  - Friction should become small durable rules.
  - Checkpoint memory is already useful.
recommendations:
  - Start by reading durable memory and current handoff.
  - Run no-reload gate before packaging/reloading.
  - Convert recurring warnings into lessons.
  - Use tool_router so the agent does not scan all tools blindly.
```

## What This Proves

- ANA can inspect recent checkpoint history.
- ANA can summarize what worked and what caused friction.
- ANA can produce next-session rules from durable lab evidence.
- REM Sleep turns repeated patterns into guidance instead of relying on chat
  memory.

## Schema Lesson

Valid actions are:

```text
analyze
consolidate
latest
```

An attempted `preview` action is invalid and should be corrected to `analyze`.

## Operating Rule

Use `session_rem_sleep`:

```text
after many checkpoints
before ending a long workday
before changing machines or moving to Linux
when recurring warnings keep appearing
when future agents need compact session wisdom
```

When saving durable REM lessons, run the write and read steps sequentially:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py session_rem_sleep action=consolidate checkpoint_limit=10 telemetry_limit=200 lesson_limit=20 save_memory=true
python ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py session_rem_sleep action=latest
```

Do not run `consolidate` and `latest` in parallel. `latest` can race and return
the previous report if it reads before the new report is fully written.

## Limitation

REM Sleep may include noisy signals from dirty git state or old checkpoints.
Treat its output as retrospective guidance, then verify with current gates.

## Share Class

Private-lab by default. Sanitized summaries can be shared only after removing
local paths, raw checkpoint excerpts, telemetry, and memory details.
