# Tool Router Recommendation Example

## Purpose

Show how ANA chooses a compact tool stack for a task instead of using all tools
blindly.

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py tool_router mode=code_change task="update a runtime tool with tests" max_tools=6
```

## Sanitized Result Summary

The router returned:

```text
schema: ana.tool_router.v1
mode: code_change
headline: Make a scoped code change and verify it.
recommended_tools:
  - code_context_pack
  - graph_context_pack
  - project_navigator
  - code_search
  - file_patch
  - edit
tool_profiles:
  all recommended tools: core
active_profiles:
  - core
  - windows
  - linux
  - security_lab
  - private_lab
filtered_by_profile: []
why_not_all_tools: Use the smallest useful stack; escalate only when evidence requires it.
```

## What This Proves

- ANA routes by task mode.
- Code-change work starts with compact context before patching.
- Graph context is included when code relationships matter.
- Recommended tools include profile metadata.
- No inactive-profile tools were needed for this core task.

## Routing Rule

For code changes:

```text
context first -> inspect target -> patch small -> verify
```

Do not jump directly to deep runtime, desktop control, or security-lab tools
unless evidence requires escalation.

## Limitation

Tool Router recommends a stack; it does not execute the task. The agent still
must inspect files, make scoped edits, run tests, and record results.

## Share Class

Sanitized. Safe after removing private task wording or local report paths.
