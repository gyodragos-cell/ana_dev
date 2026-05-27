# ANA MAX MCP Tool Matrix

Last updated: 2026-05-27

Purpose: track which ANA MAX tools are useful through MCP, which are internal,
which need fixes, and which should stay lab-only. This matrix is derived from
`ANA_MAX/TOOL_STATUS.md` and should be updated after every MCP smoke pass.

Decision values:

- `keep`: stable and useful through MCP.
- `fix`: useful, but needs repair, output cleanup, tests, or schema hardening.
- `wrap`: expose through a safer wrapper before default agent use.
- `hide`: keep available internally, but do not recommend by default.
- `lab-only`: use only in controlled private lab scenarios.
- `remove`: duplicate, obsolete, or not worth maintaining.

## Core Agent Nucleus

These are the default tools agents should prefer first.

| Tool | Role | Invocation | Risk | Decision | Next action |
| --- | --- | --- | --- | --- | --- |
| `workspace_situational_awareness` | observe | agent-first | low | keep | Keep compact; use as first project-state read. |
| `project_navigator` | observe | agent-first | low | keep | Keep as file/project map helper. |
| `git_operations` | observe/verify | agent-first | medium | keep | Use status/log safely; gate mutating ops. |
| `error_radar` | diagnose | agent-first | low | keep | Expand terminal/log/test error sources. |
| `agent_coach` | coach/decide | runtime-auto/coach-recommended | low | keep | `action=recommend` now returns primary next tool plus a compact stack from telemetry + `tool_router`. |
| `tool_router` | decide/coach | agent-first/runtime-helper | low | keep | Recommend the smallest useful MCP tool stack for a task or error. |
| `ana_memory` | learn/diagnose | runtime-auto/agent-first | medium | keep | Use for known fixes; avoid dumping private memory. |
| `conversation_learning` | learn | agent-first | medium | keep | Use for compact lessons only. |
| `session_checkpoint` | learn | agent-first | medium | keep | Use before handoff or major context loss. |
| `session_rem_sleep` | learn/coach | between-session/agent-first | medium | keep | Consolidates checkpoints, telemetry, and lessons into a REM-style retrospective report and memory rules. |
| `tool_healthcheck` | verify/diagnose | agent-first | low | keep | Expand safe scopes. |
| `file_patch` | act | user-confirmed/agent-first preview | medium | keep | Prefer preview/dry-run before writes. |
| `edit` | act | agent-first | medium | keep | Use scoped exact edits only. |
| `qa_testing` | verify | agent-first | low | keep | Add repeatable self-QA suites. |

## Observability And Diagnostics

| Tool | Role | Invocation | Risk | Decision | Next action |
| --- | --- | --- | --- | --- | --- |
| `ana_identity` | observe | agent-first | low | keep | Safe baseline identity/status. |
| `debugger` | diagnose | agent-first | low | keep | Keep traceback-focused. |
| `code_search` | observe | agent-first | low | keep | Keep compact result limits. |
| `code_tools` | diagnose | agent-first | low | keep | Keep analysis read-only by default. |
| `smart_search` | observe | agent-first | low | keep | Avoid heavy model loading in safe healthchecks. |
| `codebase_understanding` | observe | agent-first | medium | fix | Add output limits and safe lightweight mode. |
| `tool_contract_validator` | verify | agent-first | low | keep | Use in MCP audit passes. |
| `ana_runtime_inspector` | diagnose | agent-first | low | keep | Use for read-only runtime snapshots. |
| `schema_diff` | diagnose | agent-first | low | keep | Use when tool output contracts drift. |
| `live_tool_healer` | coach/diagnose | coach-recommended | medium | fix | Needs real failure scenarios and concise output. |
| `session_log_miner` | learn/diagnose | user-confirmed | medium | fix | Keep private-log aware; avoid public export. |
| `event_stream` | observe/diagnose | hidden-lab | medium | fix | Define safe stats/status usage. |

## Files, Search, And Local System

| Tool | Role | Invocation | Risk | Decision | Next action |
| --- | --- | --- | --- | --- | --- |
| `file_operations` | observe/act | agent-first | medium | keep | Keep path safety and compact listings. |
| `glob_search` | observe | agent-first | low | keep | Keep result limits. |
| `grep_content` | observe | agent-first | low | keep | Keep result limits. |
| `grep_file` | observe | agent-first | low | keep | Keep result limits. |
| `todowrite` | learn/plan | agent-first | low | keep | Useful for long work loops. |
| `system_control` | observe/act | user-confirmed | high | wrap | Split safe vitals from mutating operations. |
| `system_optimization` | diagnose/act | user-confirmed | high | wrap | Default to analyze-only. |
| `terminal` | act/verify | user-confirmed | high | wrap | Needs destructive-command policy and dry-run guidance. |
| `bash_exec` | act | user-confirmed | high | hide | Prefer safer terminal/tool wrappers. |

## Desktop, UI, Vision, And Voice

| Tool | Role | Invocation | Risk | Decision | Next action |
| --- | --- | --- | --- | --- | --- |
| `foreground_ui_snapshot` | observe | agent-first | low | fix | Stabilize live UI output and limits. |
| `desktop_capture` | observe | agent-first | medium | fix | Stabilize native/window capture. |
| `windows_uia_bridge` | observe/act | user-confirmed for mutation | high | fix | Add output limits, selector hardening, safe observe mode. |
| `window_manager` | observe/act | user-confirmed for mutation | medium | keep | Keep list/status safe. |
| `ocr_tool` | observe | agent-first | low | keep | Keep `check` safe; add targeted OCR cases. |
| `uia_click` | act | user-confirmed | high | wrap | Confirmation only; verify after one action. |
| `uia_type` | act | user-confirmed | high | wrap | Confirmation only; verify after one action. |
| `vision_region_capture` | observe | user-confirmed | medium | fix | Needs live capture scenario and privacy guard. |
| `vision_find_element` | observe | agent-first | low | fix | Needs real template scenario. |
| `vision_fallback` | observe/act | hidden-lab | medium | hide | Provider/live-screen dependent. |
| `desktop_control` | act | user-confirmed | high/premium | wrap | Harden validation and confirmation boundaries. |
| `live_desktop_viewer` | observe | user-confirmed | high/premium | lab-only | Controlled live streaming only. |
| `windows_insight` | diagnose | user-confirmed | high/premium | lab-only | Controlled diagnostics only. |
| `windows_deep_sight` | diagnose | user-confirmed | high/premium | lab-only | Controlled diagnostics only. |
| `clipboard_manager` | observe/act | user-confirmed | medium | fix | Clarify privacy and safe history mode. |
| `edge_tts_voice` | act | agent-first | low | fix | Machine dependency; keep graceful fallback. |

## Browser, Web, Network, Security, And Mobile

| Tool | Role | Invocation | Risk | Decision | Next action |
| --- | --- | --- | --- | --- | --- |
| `browser_control` | observe/act | user-confirmed for mutation | high | fix | Stabilize session persistence and safe status mode. |
| `web_scraper` | observe | user-confirmed/network | medium | fix | Keep offline parse safe; gate network. |
| `web_fetch` | observe | user-confirmed/network | medium | hide | Network-dependent. |
| `web_search` | observe | user-confirmed/network | medium | hide | Network-dependent. |
| `web_ai_bridge` | diagnose/AI | user-confirmed/network | high | hide | Provider-key dependent. |
| `network_diag` | diagnose | user-confirmed | medium | keep | Safe local/IP checks only by default. |
| `security_audit` | diagnose | user-confirmed | medium | keep | Keep hash/static checks safe. |
| `advanced_scanner` | diagnose | user-confirmed | high | lab-only | Authorized security use only. |
| `network_pentest` | diagnose/act | user-confirmed | high | lab-only | Authorized targets only. |
| `mitm_analyzer` | diagnose | user-confirmed | high | lab-only | Capture/target required. |
| `hardware_scanner` | diagnose | user-confirmed | high | lab-only | Authorized hardware/security use only. |
| `adb_operations` | observe/act | user-confirmed | high | lab-only | Device-dependent. |
| `apk_analyzer` | diagnose | user-confirmed | medium | fix | Needs APK fixture or safe sample path. |
| `frida_instrument` | diagnose/act | user-confirmed | high/internal | lab-only | Requires `confirm=True`; authorized runtime use only. |

## AI Core, Memory, And Orchestration

| Tool | Role | Invocation | Risk | Decision | Next action |
| --- | --- | --- | --- | --- | --- |
| `context_engine` | observe/decide | hidden-lab | medium | fix | Exercise status/get_context paths. |
| `context_bridge` | learn | hidden-lab | medium | fix | Wire startup/shutdown only after tests. |
| `memory_cortex` | learn/decide | hidden-lab | medium | fix | Keep memory-sensitive; avoid default dumps. |
| `vector_memory` | learn/observe | hidden-lab | medium | fix | Verify stats/search without private data leaks. |
| `ana_orchestrator` | decide/act | hidden-lab | high | fix | Needs controlled scenarios before default use. |
| `autonomous_engine` | decide/act | hidden-lab | high | lab-only | Controlled scenarios only. |
| `task` | decide/act | hidden-lab | high | lab-only | Can invoke autonomous engine/model. |
| `swarm_orchestrator` | decide/act | hidden-lab | high | lab-only | Keep experimental. |
| `remote_control` | act | user-confirmed | high | lab-only | Remote targets not tested. |
| `self_evolving_tool` | act/learn | user-confirmed | high | lab-only | High-risk auto-change behavior. |
| `proactive_interrupt` | coach | hidden-lab | medium | fix | Define safe status and routing behavior. |

## Miscellaneous Or Unclassified

| Tool | Role | Invocation | Risk | Decision | Next action |
| --- | --- | --- | --- | --- | --- |
| `adal_integration` | experimental | hidden-lab | medium | hide | Clarify current value and safe status operation. |
| `science_research` | experimental | user-confirmed | medium | hide | Needs dataset/simulation use case. |
| `privacy_shield` | release | agent-first/user-confirmed | low | keep | Use for release hygiene and redaction checks. |

## Current Priorities

1. Stabilize the core agent nucleus and use it by default.
2. Add/update safe smoke cases for every `keep` and `fix` tool.
3. Wrap high-risk tools so agents see safe observe/status actions first.
4. Keep lab-only tools registered but out of default recommendations.
5. Generate a fresh MCP smoke report before promoting anything to public release.

## Steroid Tool Note

See `docs/AGENT_STEROID_TOOLS.md` for the high-leverage local/hybrid stack.
Frida and watchdog are valuable under-the-hood accelerators, especially for
long-running local sessions and agents that need extra supervision, but they
should not become default automatic actions. Use them when normal code/log/UI
observation is not enough.
