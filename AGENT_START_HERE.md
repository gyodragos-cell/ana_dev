# Agent Start Here

Purpose: first file to give any AI agent before it works on this project.

This file is the safe entry point. It tells the agent what to read, in what
order, before editing code or docs.

## Required Reading Order

0. `docs/NEXT_SESSION_BOOTSTRAP.md`

   This is the current anti-blind-start handoff. It summarizes the latest MCP
   state, the tool-routing work, health checks, and the next best work.

1. `AGENTS.md`

   This is the workspace-level instruction file for Codex and other agents.
   It points agents to durable memory, MCP strategy, diagnostics, and safety
   boundaries.

2. `docs/AGENT_MEMORY.md`

   This is the compact durable project memory across chats. Read it before
   substantial work so the agent does not rely on raw chat history.

3. `ANA_MAX/docs/CURRENT_SESSION_HANDOFF.md`

   This points to the latest checkpoint. Open the checkpoint before continuing
   runtime, MCP, tool, release, dashboard, or architecture work.

4. `AI_AGENT_OPERATOR_RULES.md`

   This is the main operator contract. It defines agent roles, safe workflow,
   tool rules, PowerShell warnings, release rules, and what each agent may do.

5. `SAFE_AGENT_RULES.md`

   This is the short safety checklist. Use it to catch common failures quickly.

6. `DESKTOP_PROJECT_MAP.md`

   This explains which local folder is active development and which folder is
   the public GitHub release.

7. `PUBLIC_NAMING_POLICY.md`

   This keeps public naming professional and separates public names from
   internal codenames.

8. `ANA_MAX/docs/PROJECT_MAP_AI_GUIDE.md`

   This is the deeper technical map of the core project. Read it after the
   operator rules. It contains historical context and tool/module locations.

9. `vscode_extension/README.md` (ANA & Antigravity Cockpit)

   The extension in `vscode_extension/` is the primary bridge between Antigravity
   and ANA's tools. It uses the mother-folder runtime to expose all 84+ tools.

## Warning About PROJECT_MAP_AI_GUIDE.md

`ANA_MAX/docs/PROJECT_MAP_AI_GUIDE.md` is useful, but it is not the first source
of truth for agent behavior.

Reasons:

- it contains old/historical project context;
- some text may show encoding damage from previous tool runs;
- it describes the internal map, not the safety workflow;
- it may mention older public names or older assumptions.

If it conflicts with `AI_AGENT_OPERATOR_RULES.md`, follow
`AI_AGENT_OPERATOR_RULES.md`.

## Agent Prompt Template

Give this to any agent:

```text
Read AGENT_START_HERE.md first.
Then read docs/NEXT_SESSION_BOOTSTRAP.md, docs/AGENT_MEMORY.md, and
ANA_MAX/docs/CURRENT_SESSION_HANDOFF.md before editing.

Task:
[write exact task here]

Rules:
- Run git status first.
- Read files before editing.
- Make one small change.
- Do not delete files.
- Do not push without permission.
- Show the diff.
- Run the relevant test.
- If a tool or command fails, report the failure honestly.
```

## Minimal Command Set

Before editing:

```powershell
git status --short --branch
Invoke-RestMethod -Uri "http://127.0.0.1:8766/health"
```

After editing:

```powershell
git diff
```

Before handoff:

```powershell
.\RUN_ANA_QUALITY_GATE.ps1
```

For engineer proof:

```powershell
.\RUN_JOKERFORGE_ENGINEER_PROOF.ps1
```

## Rule Of Priority

If documents conflict, use this priority:

```text
1. User's current request
2. AGENTS.md
3. docs/NEXT_SESSION_BOOTSTRAP.md
4. docs/AGENT_MEMORY.md
5. ANA_MAX/docs/CURRENT_SESSION_HANDOFF.md and latest checkpoint
6. AI_AGENT_OPERATOR_RULES.md
7. SAFE_AGENT_RULES.md
8. PUBLIC_NAMING_POLICY.md
9. DESKTOP_PROJECT_MAP.md
10. ANA_MAX/docs/PROJECT_MAP_AI_GUIDE.md
```
