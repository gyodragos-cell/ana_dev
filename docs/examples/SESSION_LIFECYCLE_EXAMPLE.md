# Session Lifecycle Example

## Purpose

Show how ANA coordinates session wake, recommendations, and rest without
forcing writes or noisy reloads.

## Commands

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py session_lifecycle action=wake
python ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py session_lifecycle action=rest consolidate=false save_memory=false
```

## Sanitized Result Summary

Wake returned:

```text
schema: ana.session_lifecycle.v1
phase: wake
status: resumed
source: last_rem
current_handoff: ANA_MAX/docs/CURRENT_SESSION_HANDOFF.md
success: true
```

Rest preview returned:

```text
schema: ana.session_lifecycle.v1
phase: rest
action: analyze
write_status: preview_only
operator_prompt: Save it with rest(consolidate=True)?
success: true
```

## What This Proves

- ANA can resume from the latest REM Sleep report.
- ANA can point the agent to the current handoff.
- Rest mode defaults to preview/analyze unless consolidation is explicit.
- The lifecycle layer keeps wake/rest/recommend behavior consistent for VS Code
  buttons and MCP calls.

## Schema Lesson

Valid lifecycle actions are:

```text
start
wake
recommend
rest
```

An attempted `status` action is invalid and should be corrected to `wake` or
`recommend`, depending on intent.

## Operating Rule

Use:

```text
wake: at session start or after restart
recommend: when choosing the next tool stack
rest consolidate=false: preview end-of-session REM
rest consolidate=true: explicitly save REM Sleep
```

## Limitation

Lifecycle is an orchestrator. It delegates to REM Sleep, Agent Coach, and
workspace awareness; those underlying tools still need their own validation.

## Share Class

Private-lab by default. Sanitized summaries can be shared after removing local
paths and REM excerpts.
