# Agent Start Here

Purpose: first file to give any AI agent before it works on this project.

This file is the safe entry point. It tells the agent what to read, in what
order, before editing code or docs.

## Required Reading Order

1. `AI_AGENT_OPERATOR_RULES.md`

   This is the main operator contract. It defines agent roles, safe workflow,
   tool rules, PowerShell warnings, release rules, and what each agent may do.

2. `SAFE_AGENT_RULES.md`

   This is the short safety checklist. Use it to catch common failures quickly.

3. `DESKTOP_PROJECT_MAP.md`

   This explains which local folder is active development and which folder is
   the public GitHub release.

4. `PUBLIC_NAMING_POLICY.md`

   This keeps public naming professional and separates public names from
   internal codenames.

5. `ANA_MAX/docs/PROJECT_MAP_AI_GUIDE.md`

   This is the deeper technical map of the core project. Read it after the
   operator rules. It contains historical context and tool/module locations.

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
Then follow AI_AGENT_OPERATOR_RULES.md and SAFE_AGENT_RULES.md.

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
2. AI_AGENT_OPERATOR_RULES.md
3. SAFE_AGENT_RULES.md
4. PUBLIC_NAMING_POLICY.md
5. DESKTOP_PROJECT_MAP.md
6. ANA_MAX/docs/PROJECT_MAP_AI_GUIDE.md
```

