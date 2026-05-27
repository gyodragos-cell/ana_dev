# ANA MAX - Hybrid AI Cockpit

ANA MAX is a local-first MCP runtime for AI coding agents. This extension is the
VS Code-compatible cockpit for that runtime.

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

The extension provides a cockpit for that workflow from VS Code-compatible
agent IDEs such as VS Code, Codex environments, Antigravity/Qoder, Windsurf, and
Cursor.

## What You Get

- **Open Cockpit**: a local panel for runtime status and MCP tool actions.
- **Visible Runtime Controls**: an `ANA MAX` Activity Bar view with `Start
  Runtime`, `Smart Ready`, cockpit, router, REM Sleep, and MCP config actions
  for VS Code-compatible IDEs that do not surface every command the same way.
- **Smart Ready**: verifies that the ANA MAX runtime is online and that router,
  coach, and memory tools are callable.
- **Tool Calls**: call MCP tools directly from the cockpit when debugging.
- **Router Decisions**: ask ANA MAX which tool should be used next.
- **Checkpoint**: save compact working context before reloads or handoffs.
- **REM Sleep**: consolidate recent work into a next-session handoff.
- **Hybrid Config**: copy MCP configuration for Codex, Qoder, Windsurf, Cursor,
  and VS Code-compatible clients.

## Requirements

- Windows recommended.
- Python installed.
- ANA MAX runtime downloaded or cloned from the public repository.
- A VS Code-compatible IDE that can install `.vsix` extensions.

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
code --install-extension ANA_MAX\ana-antigravity-hybrid-1.0.10.vsix --force
```

For Qoder, if its CLI is available:

```powershell
qoder --install-extension ANA_MAX\ana-antigravity-hybrid-1.0.10.vsix --force
```

4. Reload the IDE window.
5. Open the `ANA MAX` Activity Bar view or run `ANA & Antigravity: Open Cockpit`.
6. Press `Start Runtime` if the MCP server is offline, then press `Smart Ready`.

Expected local lab health:

```text
status=online
mcp_ready=true
tools_count=85
```

Lean public installs may show fewer tools when optional desktop or vector
dependencies are not installed. The important check is that Smart Ready passes.

## Default Endpoints

- MCP server: `http://127.0.0.1:8766/mcp`
- Dashboard: `http://127.0.0.1:8787`

## MCP Client Config

Codex:

```toml
[mcp_servers.anamax]
url = "http://127.0.0.1:8766/mcp"
```

Antigravity / Qoder / Windsurf / Cursor:

```json
{
  "mcpServers": {
    "anamax": {
      "type": "http",
      "url": "http://127.0.0.1:8766/mcp"
    }
  }
}
```

If your IDE asks for fields instead of JSON:

```text
Name: anamax
Type: HTTP / remote MCP
URL: http://127.0.0.1:8766/mcp
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
`antigravity`, `qoder`, `windsurf`, `cursor`, `local-ai`,
`windows-automation`, `qa`, `debugging`, `tool-router`, `desktop-ai`,
`ai-coding-assistant`, `local-first`, `agent-tools`, `ana-max`
