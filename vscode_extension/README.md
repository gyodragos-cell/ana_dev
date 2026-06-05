# ANA MAX - Codex MCP Cockpit

ANA MAX is a local-first MCP runtime for Codex coding workflows. This extension
is the VS Code cockpit for that runtime.

It is built for developers who want an AI agent to work from evidence instead
of guessing:

```text
observe -> route -> act -> verify -> remember
```

In simple terms, ANA MAX helps an agent see the project and desktop, choose a
useful tool, run focused actions, check the result, and save context for the
next session.

## Why This Extension Exists

Most AI coding agents can edit text, but they often lose context between chats
or choose tools blindly. ANA MAX gives them a local tool layer:

- workspace and file observation;
- git, terminal, test, log, and health checks;
- Windows desktop, UI Automation, OCR, and screenshot context;
- MCP tool routing through `tool_router`;
- next-action recommendations through `agent_coach action=recommend`;
- session checkpoint and REM Sleep handoff controls.

The extension provides the cockpit for that workflow in VS Code with Codex.

## What You Get

- **Live Console**: the stable text control surface for runtime logs and MCP
  action output.
- **Visible Runtime Controls**: an `ANA MAX` Activity Bar view with `Start
  Runtime`, `Smart Ready`, `Operator Status`, `Nucleus Smoke`, `Autonomy Pass`,
  `Live Behavior`, `Reload Readiness`, `Reload Consistency`,
  `Review Batch Plan`, `Refresh Context Maps`,
  `Post-Reload Verify`, router, REM Sleep, and MCP config actions.
- **Smart Ready**: verifies that the ANA MAX runtime is online and that router,
  coach, and memory tools are callable.
- **Tool Calls**: call MCP tools directly from the cockpit when debugging.
- **Router Decisions**: ask ANA MAX which tool should be used next.
- **Checkpoint**: save compact working context before reloads or handoffs using
  the local-source fallback when MCP reload is pending.
- **REM Sleep**: consolidate recent work into a next-session handoff.
- **Voice Inbox**: in the private lab, the Live Console can start a local
  microphone daemon. Focus the Codex/ChatGPT input and speak `codex ...` or
  `ana ...`; prefix-guarded text is copied, pasted into the focused allowed
  window, and submitted.
- **MCP Config**: copy the Codex MCP configuration.

## Requirements

- Windows recommended.
- Python installed.
- ANA MAX runtime downloaded or cloned from the public repository.
- VS Code with Codex.

Public project:

- Repository: https://github.com/gyodragos-cell/ANA-MAX-v0.1.0-beta---Advanced-Neural-Architecture
- Live site: https://gyodragos-cell.github.io/ANA-MAX-v0.1.0-beta---Advanced-Neural-Architecture/
- Author: Dragos / `gyodragos-cell`, built with Codex as the main engineering copilot
- License: MIT

## Quick Start

1. Download or clone ANA MAX.
2. Start the local MCP runtime:

```powershell
cd ANA_MAX
python main.py --host 127.0.0.1 --port 8766
```

3. Install the VSIX:

```powershell
code --install-extension vscode_extension\ana-codex-cockpit-1.0.71.vsix --force
```

4. Reload the IDE window.
5. Open the `ANA MAX` Activity Bar.
6. Press `Start MCP Server` if the MCP server is offline, then press `Smart Ready`.

## Beginner Button Guide

Use the buttons in this order:

1. **Start MCP Server** starts the local ANA MAX MCP server. Press it once if
   ANA is offline.
2. **Smart Ready** checks that ANA is online and that the router/coach tools
   work. Green means the agent can use ANA safely.
3. **Wake Session** loads the last REM Sleep memory. On a first run, it creates
   a fresh-start manifest so the agent does not start blind.
4. **Operator Status** shows the current VSIX, MCP readiness, reload marker,
   live behavior freshness, checkpoint, and next install/verify commands.
5. **Nucleus Smoke** checks the core health, router, coach, context, graph,
   verification, and trust loop.
6. **Autonomy Pass** runs the safe observe-route-context-verify-audit loop.
7. **Reload Readiness** explains whether VS Code reload or MCP restart is useful
   before you touch the running session.
8. **Reload Consistency** checks whether all reload diagnostics agree before
   action work.
9. **Post-Reload Verify** checks that a restarted MCP server loaded the newest
   live tool behavior.
10. **Review Batch Plan** previews the first focused verification command from
   Dirty Tree review batches without running it.
11. **Refresh Context Maps** rebuilds Code Map and Graph Map together so
   structural context is fresh before deeper work.
12. **Ask Next Tool / Recommend** asks ANA which tool should be used next for the
   current task.
13. **Checkpoint** saves a compact handoff before reloads or risky changes.
14. **Preview REM Sleep** analyzes the session without writing memory.
15. **Save REM Sleep** writes the handoff only after you reviewed the preview.
16. **Live Behavior** checks whether the running MCP process exposes current
   tool behavior, not only `/health`.
17. **Live Debug** shows live MCP health, readiness, and discovered tool count
   inside the cockpit.

Normal read-only buttons should not show confirmation popups. Confirmation is
reserved for writes, terminal/subprocess actions, network calls, and desktop
control.

Expected local lab health after MCP reload:

```text
status=online
mcp_ready=true
tools_count=90
```

Current mother-lab installs expose the active lab tool set. Lean installs may
show fewer tools when optional desktop, vector, or security-lab dependencies are
not installed. The important check is that Smart Ready and Nucleus Smoke pass.

## Default Endpoints

- MCP server: `http://127.0.0.1:8766/mcp`
- Dashboard: `http://127.0.0.1:8787`

## MCP Client Config

Codex:

```toml
[mcp_servers.anamax]
url = "http://127.0.0.1:8766/mcp"
```

## Extension Settings

```json
{
  "anaMax.runtimeUrl": "http://127.0.0.1:8766/mcp",
  "anaMax.runtimeRoot": "",
  "anaMax.runtimePort": 8766,
  "anaMax.dashboardUrl": "http://127.0.0.1:8787"
}
```

`anaMax.runtimeRoot` defaults to the open workspace folder.

Local development on `127.0.0.1` does not require an API key. Non-local or
production deployments should use ANA MAX server-side bearer-token settings.

## Safety Model

ANA MAX is designed for local, authorized work. Keep it pointed at projects and
machines you are allowed to inspect or automate. Desktop actions are controlled
and confirmation-gated where appropriate.

Private memory, local screenshots, logs, tokens, and machine-specific paths
should stay local and should not be published with marketplace packages.

## Marketplace Keywords

`mcp`, `model-context-protocol`, `ai-agent`, `agent-ide`, `codex`,
`codex-tools`, `coding-agent`, `local-ai`,
`windows-automation`, `qa`, `debugging`, `tool-router`, `desktop-ai`,
`ai-coding-assistant`, `local-first`, `agent-tools`, `ana-max`
