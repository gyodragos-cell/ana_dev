# Agent Coach Recommendation Example

## Purpose

Show how ANA turns telemetry and router output into a concrete next action for
the agent, especially after failures or repeated loops.

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py agent_coach action=recommend task="runtime failure after tool call" max_tools=6 include_prompt=false
```

## Sanitized Result Summary

The coach returned:

```text
schema: ana.agent_coach.recommend.v1
severity: critical
primary_tool: error_radar
tool_stack:
  - error_radar
  - agent_coach
  - ana_memory
  - debugger
  - tool_healthcheck
  - foreground_ui_snapshot
router:
  mode: failure
  headline: Diagnose the first real failure and avoid retry loops.
next_action: Call error_radar, then read the normalized error and auto_guidance.
```

## What This Proves

- ANA can combine router recommendations with recent telemetry.
- Repeated failures become explicit coaching signals.
- The coach can tell the agent to stop retrying the same failing call.
- The next action is concrete, not a vague suggestion.
- Private memory tools can appear in lab mode, but the result still starts with
  safer diagnostic tools such as `error_radar` and `tool_healthcheck`.

## Operating Rule

After a tool failure:

```text
1. Do not retry blindly.
2. Call error_radar.
3. Read normalized error and auto_guidance.
4. Check known memory/lessons if available.
5. Retry once with changed input.
6. Verify with healthcheck or focused tests.
```

## Limitation

Agent Coach recommendations depend on recent telemetry. If the observability log
contains old repeated failures, severity can be higher than the current task
alone would imply. Treat the recommendation as a diagnostic guide, then verify.

## Share Class

Sanitized. Safe after removing private telemetry details and local report paths.
