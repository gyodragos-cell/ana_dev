# MCP Tool Orchestration Plan

Last updated: 2026-05-27

Goal: make every ANA MAX tool either useful through MCP, useful internally, or
clearly marked as lab-only/experimental. Tool count is not the goal. Agent
reliability is the goal.

## Principle

Every tool needs a job in the loop:

```text
observe -> decide -> act -> verify -> learn
```

If a tool does not help that loop, it should be fixed, wrapped, hidden, or
removed from the default agent surface.

## Tool Roles

| Role | Purpose | Example tools |
| --- | --- | --- |
| `observe` | Read state without changing it | `workspace_situational_awareness`, `foreground_ui_snapshot`, `desktop_capture`, `windows_uia_bridge`, `git_operations` |
| `diagnose` | Explain errors and blockers | `error_radar`, `debugger`, `tool_healthcheck`, `tool_contract_validator`, `agent_coach` |
| `act` | Change files, UI, browser, system, or runtime | `file_patch`, `edit`, `browser_control`, `uia_click`, `uia_type`, `terminal` |
| `verify` | Prove behavior after changes | `qa_testing`, `tool_healthcheck`, compile/test commands through controlled tools |
| `learn` | Save lessons, handoffs, and between-session retrospectives | `session_checkpoint`, `session_rem_sleep`, `conversation_learning`, `ana_memory`, `session_log_miner` |
| `coach` | Stop loops and recommend next action | `agent_coach`, `live_tool_healer` |
| `release` | Keep lab/public sync clean | `privacy_shield`, release hygiene checks, project maps |
| `experimental` | Lab-only until stable | swarm, remote, provider/network/security tools that need explicit targets |

## Invocation Modes

| Mode | Meaning | Good for |
| --- | --- | --- |
| `agent-first` | Codex or another agent chooses the tool intentionally | observe, diagnose, verify, safe read tools |
| `runtime-auto` | ANA attaches guidance or checks automatically | memory/coach after failures, policy blocks, repeated errors |
| `coach-recommended` | `agent_coach` suggests the next best tool | repeated failures, UI loops, wrong params |
| `user-confirmed` | Requires explicit operator intent | desktop control, Frida, pentest, network, shell mutation |
| `hidden-lab` | Registered but not recommended by default | experimental or noisy tools |

## Default Agent Playbooks

### Unknown Project State

1. `workspace_situational_awareness`
2. `project_navigator`
3. `git_operations status`
4. Read relevant docs

### Command Or Tool Failure

1. Read the normalized error.
2. Check `data.auto_guidance` if present.
3. Search `ana_memory` / `conversation_learning` for a known fix.
4. Call `agent_coach` after repeated failures.
5. Retry with a smaller, changed input.

### UI Or Desktop Task

1. `foreground_ui_snapshot`
2. `windows_uia_bridge action=list_windows`
3. `desktop_capture` or targeted vision capture when needed
4. Act once with `uia_click` / `uia_type` only after confirmation
5. Verify with another snapshot

### Code Change

1. Observe files and docs.
2. Patch with the smallest scoped change.
3. Run compile/test/list-tools depending on blast radius.
4. Save checkpoint or memory lesson if the fix is recurring.

### Between Sessions

1. Save a `session_checkpoint` for concrete handoff.
2. Run `session_rem_sleep action=consolidate` to analyze what worked, what failed, and which rules should carry forward.
3. Start the next session from `docs/NEXT_SESSION_BOOTSTRAP.md`, `ANA_MAX/docs/CURRENT_SESSION_HANDOFF.md`, and the latest REM sleep report.

### Release Or Public Sync

1. Decide `ship-safe` or `lab-only`.
2. Run privacy/release hygiene checks.
3. Update README/setup/changelog/project map when public behavior changes.
4. Keep local secrets, memory, logs, screenshots, and local paths out of public.

## Tool Audit Criteria

Each tool should be scored on:

- `registered`: appears in MCP tool list.
- `safe_case`: has a non-mutating smoke-test call when possible.
- `contract`: clear parameters, choices, and normalized `ToolResult`.
- `output`: compact, JSON-friendly, no noisy dumps by default.
- `risk`: low, medium, high, premium/internal, or lab-only.
- `policy`: confirmation/permission manifest matches risk.
- `verification`: compile, unit test, MCP smoke, or controlled live test.
- `agent_value`: clear use case in observe/diagnose/act/verify/learn.

## Status Decisions

| Decision | Meaning |
| --- | --- |
| `keep` | Stable and useful through MCP. |
| `fix` | Useful but currently broken or noisy. |
| `wrap` | Powerful or messy tool should be exposed through a safer wrapper. |
| `hide` | Keep registered internally but stop recommending to agents by default. |
| `lab-only` | Useful only in controlled local lab scenarios. |
| `remove` | Duplicate, obsolete, or not worth maintaining. |

## Immediate Next Implementation

1. Extend `ANA_MAX/TOOL_STATUS.md` or generate `docs/TOOL_MATRIX.md` with:
   `tool`, `role`, `invocation_mode`, `risk`, `status`, `safe_case`, `next_action`.
2. Update `dev_artifacts/tests/smoke_mcp_all_tools.py` so every stable tool has
   either a safe case or a documented skip reason.
3. Add a recommendation layer, likely `tool_router` or an `agent_coach` action,
   that maps task/failure context to the next best MCP tools.
4. Keep runtime auto-guidance in `tools/base.py` lightweight: attach guidance on
   failures, but do not auto-run high-risk actions.

## Non-Goals

- Do not auto-run desktop control, Frida, network, pentest, or shell mutation.
- Do not expose private memory/log/screenshot data in public reports.
- Do not optimize for a larger tool count.
