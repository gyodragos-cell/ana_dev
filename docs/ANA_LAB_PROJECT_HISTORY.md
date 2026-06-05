# ANA Lab Project History

Last updated: 2026-06-01

This file keeps the human/project story in one place: how Billy and Codex moved
ANA MAX from a broad experimental repo toward a focused mother-lab runtime.

## North Star

ANA MAX is not meant to be just another AI IDE extension. The lab direction is:

```text
local-first agent runtime
observe -> route -> act -> verify -> learn
```

The important idea is shared visibility. Billy sees what ANA/Codex is doing,
Codex sees enough local evidence to stop guessing, and ANA becomes the local
runtime that remembers useful lessons.

## Roles

- Billy brings market signals, intuition, real testing, and product direction.
- Codex acts as technical manager and implementation agent inside VS Code.
- ANA is the local lab runtime: tools, memory, observation, verification, and
  learning.

This rhythm is intentional:

```text
Billy brings ideas -> Codex filters/selects -> ANA lab implements/tests -> keep what works
```

The market changes constantly, so the lab must stay adaptive. Nothing is treated
as static.

## Why GitHub Is Pending

GitHub/public release work helped Billy enter the GitHub/open-source world, but
it is not the current priority.

Current rule:

```text
mother lab first
public/GitHub pending
no exposure unless explicitly requested
```

The public repo is low priority because the useful work now is private lab
iteration, testing, learning, and selecting the best ideas safely.

## Control Surface Evolution

Early work tried to use a richer Cockpit/webview interface. It looked good, but
it was fragile in the host and some buttons did not behave reliably.

The stable decision:

```text
ANA MAX Activity Bar + ANA MAX MCP Live Console
```

This made the system usable:

- left-side buttons work reliably
- Live Console shows actions and errors
- webview is out of the critical path
- Nucleus Smoke gives one-button confidence

## Current Stable Stack

```text
VS Code + Codex
ANA MAX Activity Bar
ANA MAX MCP Live Console
MCP server on 127.0.0.1:8766
90 tools
Code Map
Graph Map
Context Pack
Tool Router
Agent Coach
Error Radar
Tool Healthcheck
Session Audit / Trust Score
Checkpoint / REM Sleep
```

Current live lab status after the 90-tool alignment is clean after MCP reload:
`behavior=PASS(checks=3/3)`, with tool surface and identity also PASS.

## Important Lab Decisions

### Observation First

Before acting, ANA should gather evidence:

```text
foreground_ui_snapshot
code_context_pack
graph_context_pack
tool_router / agent_coach
```

### Do Not Use All Tools Blindly

Tool count is less important than choosing the smallest useful tool stack. This
is why `tool_router` and `agent_coach action=recommend` matter.

### Sensitive Keyword Boundary Check

The chat once triggered a cybersecurity warning around sensitive terminology.
That became a useful lab rule: sensitive words are not automatic panic and not
automatic permission.

The correct behavior is:

```text
sensitive keyword -> classify boundary -> continue only if local, authorized, defensive/diagnostic, and lab-only
```

This applies to Codex and any future sub-agent.

### Local Graph Layer

Graphify inspired the graph idea, but the lab did not import the whole repo.
Codex selected the useful concept and implemented it lab-native:

```text
ana_code_map -> ana_graph_map -> graph_context_pack
```

This gives ANA relationships between files, symbols, dependencies, and
keywords.

### Nucleus Smoke

The lab needed one button to answer:

```text
Is ANA whole right now?
```

So `ANA MAX: Nucleus Smoke` now checks:

```text
health
tools/list
tool_router
agent_coach
code_context_pack
graph_context_pack
tool_healthcheck
error_radar
session_audit / trust
```

Latest known result:

```text
PASS 9/9
Trust 92%
```

## Important Recent Additions

- `ana_code_map.py`
- `ana_graph_map.py`
- `code_context_pack`
- `graph_context_pack`
- `session_audit`
- `binary_map`
- `input_api_probe` lab-only
- `ana_nucleus_smoke.py`
- Activity Bar command `Nucleus Smoke`
- local dashboard fallback
- error_radar timestamp/auth false-positive fix

## Workspace Cleanup

Generated packages and build folders were archived instead of deleted:

```text
ANA_MAX/dev_artifacts/archives/workspace_cleanup_20260529/
```

Future generated artifacts should not go in the repo root.

## What To Read First

For future sessions:

```text
AGENTS.md
docs/ANA_LAB_MASTER_CONTEXT.md
docs/ANA_LAB_PROJECT_HISTORY.md
ANA_MAX/docs/CURRENT_SESSION_HANDOFF.md
```

Then run:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_nucleus_smoke.py --mcp-url http://127.0.0.1:8766/mcp
```

## Current Direction

Keep building in dev mode:

```text
test -> learn -> keep useful ideas -> discard hype -> document lessons
```

The next useful work should continue from the stable lab base, not from public
repo pressure.
