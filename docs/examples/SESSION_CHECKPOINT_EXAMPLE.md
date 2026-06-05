# Session Checkpoint Example

## Purpose

Show how ANA saves compact continuity state so a future session or agent can
continue without reconstructing the whole chat.

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py session_checkpoint action=save title="Session checkpoint example probe" summary="Probe checkpoint for sanitized documentation example." include_git=false
```

## Sanitized Result Summary

The checkpoint tool returned:

```text
success: true
saved: true
path: ANA_MAX/docs/SESSION_CHECKPOINT_<timestamp>.md
topic: session_checkpoint_<timestamp>
timestamp: <utc timestamp>
message: Session checkpoint saved
```

## What This Proves

- ANA can write a compact markdown handoff.
- ANA can save a memory topic for future retrieval.
- ANA updates the current handoff pointer.
- ANA preserves operator notes appended after the standard latest-handoff
  pointer once the live MCP server has loaded the current source.
- The checkpoint can include title, summary, current goal, next steps, changed
  files, validation, risks, sync status, and optional git snapshot.

## Operating Rule

Use `session_checkpoint`:

```text
after meaningful architecture decisions
after successful gate/test runs
before ending a long session
before Linux migration or handoff
after adding a recurring lesson
```

Avoid:

```text
raw private logs
screenshots
tokens/secrets
full chat dumps
unreviewed exploit details
```

## Limitation

Checkpoints are durable lab memory. They should be compact and intentional; too
many noisy checkpoints make future retrieval harder.

When `live_reload_marker` is still `WARN`, the running MCP server may not yet
include the latest checkpoint-preservation behavior. Reload MCP before relying
on newly changed checkpoint semantics.

## Share Class

Private-lab by default. Sanitized summaries can be shared only after removing
local paths, memory topics, git status, and private context.
