# ANA Codex Golden Rule

Last updated: 2026-06-02

Purpose: make the ANA-first workflow explicit so Codex does not work blind in
the mother lab.

## Rule

For ANA lab work, Codex must use ANA before meaningful action:

```text
Billy intent -> ANA observe/coach/route -> Codex decides -> act once -> verify -> learn
```

Codex is still the lead engineer and project manager, but ANA is the local
observer, coach, and challenge layer. If ANA has evidence, Codex must listen to
it before editing, testing broadly, packaging, reloading, or diagnosing by
guesswork.

In the accessibility lab workflow, this must also be visible and audible for
Billy:

```text
[ANA-GUARD] start -> ANA Companion PASS/WARN/FAIL -> spoken guard cue -> action
```

If Codex used ANA but Billy cannot see or hear the evidence, the workflow is not
good enough. The Live Console should show `[ANA-GUARD]`, `[GOLDEN-RULE]`,
`[TOOL start]`, `[TOOL end]`, or a named ANA tool result before action work.

## Required Preflight

Before scoped ANA work, use at least one of:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_codex_companion.py --mcp-url http://127.0.0.1:8766/mcp --goal "<goal>" --no-write
python ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py agent_coach action=recommend task="<goal>" max_tools=6 include_prompt=false
python ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py tool_router task="<goal>" max_tools=6
```

For UI/desktop-facing work, include an observation tool:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py foreground_ui_snapshot include_text=false max_elements=20
```

For code/context work, include:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py code_context_pack query="<goal>" include_graph=true include_text=false limit=5
```

## What ANA Is Allowed To Do

ANA should:

- show what it sees in VS Code, logs, watchdog, mirror, health, and Error Radar
- recommend the smallest useful tool stack
- warn about repeated calls, stale maps, stale MCP behavior, dirty-tree risk, or missing verification
- tell Codex to stop when it is looping or acting without evidence
- produce compact evidence that Billy can also read in the Live Console

## What Codex Must Do

Codex must:

- state the ANA signal when it matters
- make the ANA signal visible/audible when Billy asks for non-blind work
- obey `WARN` as a pause-and-verify signal, not as failure theater
- avoid using all tools blindly
- prefer focused ANA tools over broad shell guessing
- patch only after ANA context identifies the target
- verify with Nucleus Smoke, Operator Status, focused tests, or a relevant gate
- save memory/checkpoint after meaningful session changes

## Current Companion

The main anti-blind-work bridge is:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_codex_companion.py --mcp-url http://127.0.0.1:8766/mcp --goal "<goal>" --no-write
```

Activity Bar:

```text
ANA MAX: Codex Guard
ANA MAX: Codex Companion
```

`ANA MAX: Codex Guard` is the operator-facing proof button. It runs the
companion, writes `[ANA-GUARD]` lines to the Live Console, and speaks ready,
warning, or failed cues so Billy is not left guessing whether Codex consulted
ANA.

Expected output shape:

```text
ANA Codex Companion: PASS|WARN|FAIL goal=<goal>
[ANA] ...
[ANA challenge] ...
[CODEX] ...
[NEXT] ...
```

## If ANA Challenges Codex

If ANA returns `WARN`:

1. Read the challenge.
2. Do not mutate unrelated files.
3. Run the recommended next tool if it is safe and scoped.
4. Continue only after the evidence explains the next action.

If ANA returns `FAIL`:

1. Stop action work.
2. Restore MCP/readiness or collect the failure evidence.
3. Ask Billy only if operator action is required.

## Why This Exists

ANA was built so Codex and Billy do not work blind. Watchdog, Live Console,
mirror, Code Map, Graph Map, Error Radar, tool_router, agent_coach, and trust
score are not decoration. They are the shared visibility layer for the lab.
