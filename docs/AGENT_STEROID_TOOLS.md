# Agent Steroid Tools

Last updated: 2026-05-27

Purpose: define the ANA MAX tools that give local/hybrid agents a real
advantage, and when to use them. These are not all default tools. They are the
high-leverage tools that help an agent stop guessing.

## Principle

The strongest ANA MAX workflow is:

```text
observe -> diagnose -> act once -> verify -> learn
```

The "steroid" effect comes from giving the agent real machine context:
workspace state, UI state, logs, tool telemetry, runtime health, and known
lessons. High-risk tools stay behind confirmation.

## Tier 1: Daily Driver Tools

Use these first in normal coding/project work.

| Tool | Why it gives leverage | Default use |
| --- | --- | --- |
| `workspace_situational_awareness` | Gives compact project/UI/git/error context in one pass. | First read when state is unclear. |
| `project_navigator` | Helps find files and understand project structure. | Before editing unfamiliar areas. |
| `error_radar` | Finds likely blockers from logs, git, and visible error signals. | After errors or before verification. |
| `tool_router` | Chooses the smallest useful MCP stack for the current task. | Before reaching for many tools. |
| `agent_coach` | Detects repeated failures and bad loops from observability. | After repeated attempts or high failure rate. |
| `ana_memory` | Searches known fixes and saved lessons. | Before retrying a repeated error. |
| `tool_healthcheck` | Quickly checks whether the local tool layer is healthy. | Before/after MCP or runtime changes. |
| `file_patch` / `edit` | Controlled file mutation. | Small scoped code edits. |
| `qa_testing` | Verification support. | After code changes or bug fixes. |

## Tier 2: Eyes And UI Tools

Use these when the real screen or app state matters.

| Tool | Why it gives leverage | Guardrail |
| --- | --- | --- |
| `foreground_ui_snapshot` | Reads active UI state without relying on user description. | Read-only first. |
| `windows_uia_bridge` | Lists/inspects Windows UI elements. | Mutation needs confirmation. |
| `desktop_capture` | Captures screen/window context. | Watch privacy and screenshots. |
| `ocr_tool` | Extracts text when UIA cannot see it. | Prefer targeted use. |
| `window_manager` | Lists and manages windows. | Mutating actions need care. |
| `uia_click` / `uia_type` | Lets ANA act on UI. | Confirm, act once, then verify. |
| `vision_region_capture` / `vision_find_element` | Useful for visual targets/templates. | Needs controlled scenario. |

These are gold for local AI because they remove blindness. They should not
click/type repeatedly. The rule is observe first, one action, verify.

## Tier 3: Under-The-Hood Tools

Use these when normal observation is not enough.

| Tool | Best use | Guardrail |
| --- | --- | --- |
| `live_watchdog.py` | Operator dashboard: MCP health, tool count, Frida version, window sanity, log tail, coach warnings. | Runs as a monitor; not a decision-maker. |
| `frida_instrument` | Runtime instrumentation, process/module/function inspection, white-hat diagnostics. | Authorized use only; `confirm=True`; not default for normal coding. |
| `ana_input_probe_spec.py` | Lab-only spec for short, aggregate-only Windows input API probes such as Raw Input registration or keyboard state API calls. | Authorized targets only; no raw key storage, no character decoding, no continuous monitoring, no anti-cheat bypass. |
| `windows_insight` / `windows_deep_sight` | Deep local diagnostics and process/system view. | Premium/internal; controlled lab use. |
| `event_stream` | Runtime event/debug stream. | Needs concise safe views before default use. |
| `live_tool_healer` | Failure pattern and repair guidance. | Needs more real failure validation. |

Watchdog and Frida are useful, especially for Qoder-like agents that need more
external supervision. For Codex-style work, they are still valuable as
diagnostic accelerators, but only when the problem is below normal source-level
visibility.

## Tier 4: Power Tools

These can be valuable, but should not be default automatic tools.

| Tool family | Use | Default stance |
| --- | --- | --- |
| terminal/shell tools | Verification, controlled commands, diagnostics. | Confirm risky commands; avoid destructive actions. |
| browser/web tools | Browser state and web workflows. | Network/user intent required. |
| security/network/mobile tools | White-hat diagnostics, authorized targets. | Lab-only unless explicitly approved. |
| autonomous/swarm/remote tools | Experiments and orchestration. | Hidden/lab-only until hardened. |
| self-evolving tools | Suggested improvements and evolution. | No uncontrolled auto-change. |

## Codex Usage Preference

Codex does not need every tool all the time. The strongest default stack is:

```text
workspace_situational_awareness
project_navigator
error_radar
tool_router
agent_coach
ana_memory
tool_healthcheck
file_patch/edit
qa_testing
session_checkpoint
```

For UI work, add:

```text
foreground_ui_snapshot
windows_uia_bridge
desktop_capture
ocr_tool
uia_click/uia_type with confirmation
```

For under-the-hood debugging, add:

```text
live_watchdog.py
frida_instrument
windows_deep_sight
event_stream
```

## When Frida Is Worth It

Use Frida when the question is about runtime behavior that source files, logs,
tests, or UI snapshots cannot answer:

- Is a function/module loaded at runtime?
- Is a process actually receiving or changing data?
- Does a hook prove the live behavior?
- Is a mobile/app process doing something different than the code suggests?

Do not use Frida for ordinary file edits, docs, project navigation, simple test
failures, or guesses. It is a microscope, not a hammer.

Input API probes are even narrower: use them only to confirm whether an
authorized local test process calls Windows input APIs such as
`RegisterRawInputDevices`, `GetAsyncKeyState`, or `GetKeyboardState`. They must
be short-lived, aggregate-only, and lab-only. Do not decode characters, store raw
keys, monitor continuously, or use them for anti-cheat bypass.

## When Watchdog Is Worth It

Use watchdog when a long local session is running and the operator needs one
place to see:

- MCP health
- loaded tool count
- recent tool calls
- warnings/errors
- Frida availability
- visible window sanity
- agent coach warnings

It is especially useful for external agents and launch workflows. It also helps
Codex indirectly because it keeps the lab observable and catches repeated tool
failure patterns.

## Promotion Rule

If a steroid tool repeatedly helps real work, add it to:

- `docs/TOOL_MATRIX.md` with `keep` or `fix`
- `docs/PUBLIC_RELEASE_SYNC_BACKLOG.md` if the idea is public-safe later
- `docs/AGENT_MEMORY.md` if it changes durable agent behavior
