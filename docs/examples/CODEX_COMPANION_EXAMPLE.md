# Codex Companion Example

## Purpose

Show the ANA-first bridge for Codex work: ANA observes the UI/workspace, routes
the task, checks coach telemetry, builds compact code/graph context, checks
Error Radar, and challenges Codex before a scoped action.

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_codex_companion.py --mcp-url http://127.0.0.1:8766/mcp --goal "Codex asks ANA to observe challenge blind work and choose the next verified lab action" --no-write
```

## Expected Shape

```text
ANA Codex Companion: WARN goal=<goal>
[ANA] Use code_context_pack next for project_state; coach severity is ok.
[ANA challenge] Error Radar has <n> finding(s): <next step>.
[CODEX] I will address ANA's challenge before any mutation.
[NEXT] Call code_context_pack, then Capture compact workspace/git/error context. Verify before another action.
context=<file candidates>
```

## What This Proves

- ANA is not just a passive tool list; it can challenge Codex before work.
- The bridge follows `observe -> route -> coach -> context -> radar -> next`.
- `WARN` is useful when evidence says Codex should slow down or verify first.
- The default command is report-only; it does not patch, package, reload, or
  write reports when `--no-write` is used.

## Safety

Read-only by default when `--no-write` is passed. It uses MCP observation and
diagnostic tools, then returns a compact recommendation.

## Share Class

`private-lab, sanitizable`: safe to describe after removing local paths,
runtime logs, and private session details.
