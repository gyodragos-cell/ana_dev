# AI Agent Operator Rules

Purpose: protect Billy's work while using multiple AI agents and local tools.

This file is the operating manual. Give it to any AI agent before letting it
touch the project.

## Core Principle

The human is the operator.

AI agents can help with research, code, tests, docs, and diagnostics, but they
must work inside clear limits:

- observe before acting;
- make small changes;
- show the diff;
- run the relevant test;
- never publish or delete without permission.

## Agent Roles

### Codex

Use for high-trust engineering work:

- repo repair;
- git hygiene;
- release preparation;
- quality gates;
- MCP/tool integration;
- documentation that must stay accurate;
- safety and privacy checks;
- small targeted code changes.

Codex may edit the main workspace when the task is clear and the diff can be
verified.

### Cursor, Windsurf, Antigravity

Use for normal coding assistance when the task is bounded:

- feature edits;
- refactors with clear scope;
- tests;
- IDE-assisted navigation;
- UI improvements.

They should still follow the same workflow: status, read, patch, diff, test.

### Qoder

Use Qoder as a lab assistant, not as the release engineer.

Good Qoder tasks:

- explain a file;
- summarize logs;
- brainstorm ideas;
- write draft text;
- create experiments in a temporary folder;
- read public websites;
- voice companion work;
- suggest fixes without editing.

Avoid Qoder tasks:

- auto-fix the main repo;
- broad refactors;
- dependency changes;
- deleting files;
- pushing to GitHub;
- editing public release docs without review.

If Qoder produces useful code, move it through a review path before it reaches
the main project.

## Workspace Rules

### Active Workspace

```text
C:\Users\billy\Desktop\ana_dev
```

Use for:

- experiments;
- tool testing;
- Codex repair work;
- voice and desktop diagnostics;
- local development.

Do not publish directly from here unless the diff is intentionally prepared.

### Public Release Workspace

```text
C:\Users\billy\Desktop\ANA_MAX_GitHub_Release
```

Use for:

- public README;
- website;
- GitHub Pages;
- release docs;
- clean publishable files.

Before push:

```powershell
git status --short --branch
git diff
```

Never publish local paths, credentials, private logs, memory databases,
screenshots, or temporary test output.

## Tool Connection Rules

Use tools through their declared interface whenever possible.

Preferred flow:

1. Start the local cockpit:

```powershell
.\RUN_JOKERFORGE_COCKPIT.bat
```

2. Confirm MCP/tool availability:

```powershell
python ANA_MAX\test_mcp_tools.py
```

3. Confirm Frida through MCP only for authorized local testing:

```powershell
python ANA_MAX\test_mcp_frida_call.py
```

4. Run the full quality gate before handoff:

```powershell
.\RUN_ANA_QUALITY_GATE.ps1
```

## MCP Tool Rules

Agents should not guess tool parameters.

Before calling a tool:

- list the tool definition;
- check required parameters;
- call the smallest useful operation;
- treat errors as evidence.

Recommended tool usage:

- `file_operations`: inspect or edit files through schema;
- `git_operations`: inspect git state when available;
- `desktop_capture`: check whether desktop vision actually sees pixels;
- `foreground_ui_snapshot`: inspect focused UI state;
- `windows_uia_bridge`: use native Windows UI structure when possible;
- `edge_tts_voice`: speak short progress messages;
- `frida_instrument`: authorized runtime diagnostics only;
- `tool_healthcheck`: verify tool availability.

Do not expose MCP ports publicly.

## PowerShell Non-ASCII Scan Rule

Warning for all agents: do not use inline regex tricks to scan non-ASCII text in
PowerShell.

This kind of command is fragile because shell quoting, ranges, and control
characters can be parsed incorrectly before the regex ever runs.

Avoid:

```powershell
rg -n "[^\u0000-\u007F]" file.md
```

Use a byte scan instead:

```powershell
$files=@('README.md','SAFE_AGENT_RULES.md')
foreach($f in $files){
  $bytes=[System.IO.File]::ReadAllBytes((Join-Path (Get-Location) $f))
  $bad=$bytes | Where-Object { $_ -gt 127 } | Select-Object -First 1
  if($null -ne $bad){ Write-Host "BAD $f" } else { Write-Host "OK $f" }
}
```

For permanent checks, prefer the ASCII guard inside
`RUN_ANA_QUALITY_GATE.ps1`. If a quick regex command fails with a parser error,
do not treat that as proof that the file is clean.

## Prompt Template For Any Agent

Use this before asking another agent to work:

```text
You are working in Billy's project. Follow AI_AGENT_OPERATOR_RULES.md.

Task:
[write the exact task]

Rules:
- Run git status first.
- Read the target files before editing.
- Make the smallest useful change.
- Do not delete files.
- Do not change dependencies unless the task requires it.
- Do not push without permission.
- Show the diff.
- Run the relevant test.
- If you are not sure, stop and explain.
```

## Safe Experiment Template

For risky ideas, tell the agent:

```text
Create the experiment in experiments/[short-name]/ only.
Do not edit production files.
Do not change requirements.
Include a README explaining what the experiment proves.
```

## Release Checklist

Before publishing to GitHub:

1. Confirm the correct folder.
2. Run `git status --short --branch`.
3. Review `git diff`.
4. Scan public docs for private data.
5. Run the relevant tests.
6. Commit one logical change.
7. Push only after permission.

Public scan terms:

```text
C:\Users\
file:///
credentials
private log
memory.db
.sqlite
.env
```

Some terms may appear in warnings or policy docs. Review context before
changing them.

## When Money Or Credit Is Low

Use AI time only on high-leverage work:

- one clean README section;
- one working demo path;
- one failing test fixed;
- one release hygiene improvement;
- one operator rule added;
- one bug reproduced and documented.

Do not spend scarce credit on arguments, giant rewrites, or cosmetic churn.

## Long-Term Direction

The goal is to move toward private local testing with stronger offline models
when hardware allows it.

Until then:

- keep public demos thin and safe;
- keep powerful tools local;
- document what is real;
- verify before claiming success;
- use each AI agent for the role where it is strongest.
