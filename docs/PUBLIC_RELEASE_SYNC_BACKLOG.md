# Public Release Sync Backlog

Last updated: 2026-05-27

Purpose: track good mother-lab improvements that should eventually be copied or
adapted into the clean GitHub release folder, without mixing them with lab-only
data. This is not a command to sync today. It is the parking lot so Billy and
future agents do not lose what is worth shipping.

Public release folder:

```text
C:\Users\billy\Desktop\ANA_MAX_GitHub_Release
```

Mother lab:

```text
C:\Users\billy\Desktop\ana_dev\ANA_MAX
```

## Rules

- Every item must be marked `ship-safe`, `needs-review`, or `lab-only`.
- Do not copy memory databases, logs, screenshots, local paths, private configs,
  API keys, tokens, `.env`, `.license`, session archives, or private runtime
  evidence into the public release.
- Public docs should describe architecture and behavior without leaking private
  lab state.
- Before syncing code, update public docs/tests in the same work cycle.
- Before public push, run release hygiene checks.

## Status Values

| Status | Meaning |
| --- | --- |
| `candidate` | Looks useful, not reviewed for public release yet. |
| `needs-review` | Requires privacy/security/API/docs review. |
| `ready-later` | Public-safe in principle, but not syncing today. |
| `synced` | Already copied/adapted into the public release. |
| `lab-only` | Keep private; do not copy. |

## Backlog

| Item | Type | Source | Public status | Notes |
| --- | --- | --- | --- | --- |
| Root `AGENTS.md` multi-agent rules | docs | `AGENTS.md` | ready-later | Public-safe after removing local/private wording if needed. |
| Persistent agent memory concept | docs/process | `docs/AGENT_MEMORY.md` | needs-review | Useful pattern, but current file contains local paths and lab state; publish only sanitized summary. |
| MCP-first operating rule | docs/process | `AGENTS.md`, `docs/MCP_TOOL_ORCHESTRATION_PLAN.md` | ready-later | Good public guidance for agent workflows. |
| Auto-guidance on failed tool execution | code/runtime | `ANA_MAX/tools/base.py` | needs-review | Strong candidate; verify tests and avoid private memory leakage in public outputs. |
| Tool orchestration plan | docs | `docs/MCP_TOOL_ORCHESTRATION_PLAN.md` | ready-later | Public-safe after trimming private lab references. |
| Tool matrix methodology | docs | `docs/TOOL_MATRIX.md` | ready-later | Publish sanitized template, not private tool state if sensitive. |
| Agent steroid tools concept | docs/process | `docs/AGENT_STEROID_TOOLS.md` | ready-later | Public-safe after trimming local/private examples; useful positioning for hybrid local AI. |
| Public release sync backlog workflow | docs/process | this file | ready-later | Useful discipline for lab/public split. |
| Core agent nucleus definition | docs/process | `docs/TOOL_MATRIX.md` | ready-later | Good for README/project map after review. |
| Runtime `data.auto_guidance` result field | API behavior | `ANA_MAX/tools/base.py` | needs-review | Includes memory, coach, and tool-router guidance; needs contract docs and smoke tests before public sync. |
| `tool_router` recommendation tool | code/runtime | `ANA_MAX/tools/tool_router_tool.py` | needs-review | Public candidate after MCP smoke tests and docs; helps agents avoid blind all-tool usage. |
| `agent_coach action=recommend` | code/runtime | `ANA_MAX/tools/agent_coach_tool.py` | needs-review | Public candidate after contract docs; combines telemetry and `tool_router` into `primary_tool`, `tool_stack`, and `next_action`. |

## Lab-Only By Default

These categories should not be copied unless explicitly sanitized:

- private memory and conversation databases
- observability logs and session histories
- local screenshots, videos, clipboard content, and UI captures
- provider/API keys and local model experiments
- desktop-control evidence from private machine state
- Frida/runtime instrumentation demos with private process data

## Next Review Checklist

Before moving any `ready-later` or `needs-review` item to the public release:

1. Decide whether the item is code, docs, tests, config, or behavior.
2. Remove local machine paths and private lab details.
3. Check if public README/setup/changelog/project map need updates.
4. Add or update tests when behavior changed.
5. Run public release hygiene tests.
6. Mark the item `synced` only after the public folder is updated.
