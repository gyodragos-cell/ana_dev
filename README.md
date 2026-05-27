# JokerForge

Local-first AI tooling for observation, voice feedback, diagnostics, and assistive workflows.

JokerForge is an engineering workspace for giving AI agents safer, testable access to the parts of a Windows development environment that normal chat-only agents cannot see: local tools, voice feedback, desktop diagnostics, MCP calls, quality gates, and controlled runtime inspection.

The project is not a hosted surveillance tool and not a public hacking service. The public demo is only a thin preview layer. The powerful tools stay local, under the operator's control.

## Why It Exists

Most AI coding agents are strong inside text files and weak once a task needs real environment feedback:

- Did the desktop tool actually see the screen, or did it capture a black frame?
- Did the MCP server expose the expected tools?
- Can the voice layer confirm what the assistant is doing?
- Can runtime diagnostics inspect an authorized local process?
- Can the whole workspace pass a repeatable quality gate before publishing?

JokerForge is built around that gap: make agent work observable, testable, and honest.

## First-Look Demo Path

Start here if you are reviewing the project:

```text
AGENT_START_HERE.md
```

That file gives any AI agent the required reading order before it touches the
workspace.

Then read:

```text
AI_AGENT_OPERATOR_RULES.md
```

That file defines how Codex, Qoder, Cursor, Windsurf, Antigravity, and any
other agent should work with this repository.

Then run:

```powershell
.\RUN_JOKERFORGE_ENGINEER_PROOF.ps1
```

That is the fastest engineer-first proof: git snapshot, MCP tool inventory,
authorized Frida-through-MCP check, compile surface, and full quality gate.

For the detailed proof path, read:

```text
ENGINEER_WOW_DEMO.md
```

For the lower-level gate, run:

```powershell
.\RUN_ANA_QUALITY_GATE.ps1
```

That gate checks the core Python files, MCP tool listing, smoke tests, and Frida-through-MCP availability.

For the local cockpit:

```powershell
.\RUN_JOKERFORGE_COCKPIT.bat
```

Then open:

```text
ANA_SCHOOL_DEMO.html
```

For the public hosted preview layer:

```text
jokerforge_pythonanywhere_demo/
```

That folder is intentionally small and safe for PythonAnywhere. It does not expose local MCP, Frida, desktop control, credentials, private logs, or personal files.

## Architecture

JokerForge is split into four practical layers:

1. Public demo layer
   - A small Flask app for PythonAnywhere.
   - Shows the idea, accepts feedback, and keeps the public surface safe.

2. Local MCP layer
   - Exposes controlled tools to compatible AI clients.
   - Keeps privileged actions on the user's machine.

3. Observation and voice layer
   - Desktop vision diagnostic.
   - Chat voice bridge.
   - Browser demo controls for live feedback.

4. Runtime diagnostics layer
   - Frida-based process inspection for authorized local testing.
   - Designed for debugging, education, and assistive workflows.

## Safety Boundary

The public-facing rule is simple:

- Public demo: explain, preview, collect feedback.
- Local machine: run MCP, voice, desktop diagnostics, and runtime tools.
- GitHub: publish only clean code, docs, and safe demos.
- Never publish credentials, local user paths, private logs, or unrestricted control endpoints.

See `PUBLIC_NAMING_POLICY.md` for the naming and privacy rules.

## Repository Map

```text
ANA_MAX/                         Core tools and MCP server
AGENT_START_HERE.md              First file for any AI agent
ANA_SCHOOL_DEMO.html             Local browser demo
RUN_JOKERFORGE_COCKPIT.bat       Local cockpit launcher
RUN_JOKERFORGE_ENGINEER_PROOF.ps1 One-command engineer proof
RUN_ANA_QUALITY_GATE.ps1         Repeatable verification gate
ENGINEER_WOW_DEMO.md             Reviewer-focused proof path
jokerforge_pythonanywhere_demo/  Safe public Flask demo
PUBLIC_NAMING_POLICY.md          Public/private naming rules
SAFE_AGENT_RULES.md              Operating rules for AI agents
AI_AGENT_OPERATOR_RULES.md       Role map and workflow for AI agents
DESKTOP_PROJECT_MAP.md           Local workspace map
```

## Engineering Goals

- Make AI agent work visible instead of mysterious.
- Prefer local-first tools over public control surfaces.
- Fail honestly when vision, voice, or runtime tools cannot access the environment.
- Keep demos small enough to understand and real enough to verify.
- Build assistive tooling that can help developers, students, and eventually accessibility workflows.

## Current Status

This is the active JokerForge / ANA MAX parent workspace (`ana_dev`). It contains the full history, local configurations, testing tools, and private assets.

> [!NOTE]
> The clean public release of ANA MAX is deployed from the `ANA_MAX_GitHub_Release` repository.
> Do not publish private integrations, DB files, or tokens from this workspace to the public repository.

The current priority is maintaining the ANA MAX v1.0.12 cockpit baseline:
86 tools in the mother-lab runtime, 85 public tools in the clean release, and
clear CI/CD plus release-quality automation.
