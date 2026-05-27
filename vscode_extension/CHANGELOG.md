# Changelog

## 1.0.11 - Quieter Safe Mode For Read-Only Agent Tools

- Stopped asking for `Allow tool execution?` on known read-only guidance tools
  such as `tool_router`, `agent_coach`, `ana_identity`, health checks, and
  workspace observation.
- Kept confirmation prompts for writes, subprocess/runtime starts, network,
  terminal, and unknown tool calls.
- Reduced prompt noise in Antigravity/Qoder/Windsurf while preserving safe-mode
  boundaries for real actions.

## 1.0.10 - Antigravity Visible Runtime Controls

- Added an `ANA MAX` Activity Bar view with visible runtime actions for
  VS Code-compatible IDEs that do not expose command palette entries the same
  way.
- Added explicit `Start Runtime` buttons in the view title, editor title, and
  cockpit toolbar.
- Kept the MCP backend unchanged: this release improves discoverability for
  Antigravity/Qoder/Windsurf-style hosts.

## 1.0.9 - Marketplace Readiness Pass

- Clarified the public product message around `observe -> route -> act -> verify -> remember`.
- Expanded the marketplace README for beginner installation and agent workflows.
- Added marketplace metadata polish: preview flag, banner color, Testing category, activation events, and stronger keywords.
- Documented Smart Ready, router decisions, checkpoint, and REM Sleep as the main cockpit workflow.

## 1.0.8 - Hybrid MCP Cockpit

- Added Smart Ready checks for ANA MAX MCP readiness.
- Added router and coach actions for next-tool recommendations.
- Added checkpoint and REM Sleep controls for handoff continuity.
- Added icon, public repository metadata, and author credit.
