# ANA MAX Lab README

Last updated: 2026-06-01

ANA MAX Lab is a private, local-first agent runtime used with VS Code + Codex.
The goal is not to expose a polished public product today. The goal is to build
and test a reliable local agent workflow:

```text
Billy intent -> ANA observe/coach/route -> Codex decides -> act once -> verify -> learn
```

## What This Lab Contains

- MCP runtime on localhost.
- VS Code Activity Bar controls for stable operator actions.
- Local code intelligence through Code Map and Graph Map.
- Tool routing and coaching for choosing the smallest useful tool stack.
- Session audit, trust score, checkpoints, and REM sleep memory flows.
- A lab-safe Autonomy Pass that observes, routes, context-packs, verifies,
  audits, and checkpoints before larger work.
- A Codex Companion preflight that lets ANA challenge Codex before scoped work
  so the lab does not proceed blind.
- A Linux Mate migration lane for future portability work without disrupting
  the current Windows lab.
- Lab-only diagnostics for authorized local testing.

## Current Stable Surface

Use:

```text
ANA MAX Activity Bar
ANA MAX MCP Live Console
```

Avoid using the old Cockpit webview as the primary control surface. It remains
out of the critical path because host webview behavior was unreliable.

## Codex Companion

Run before scoped ANA work when Codex needs ANA's eyes, logs, router, coach, and
context:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_codex_companion.py --mcp-url http://127.0.0.1:8766/mcp --goal "<goal>" --no-write
```

Or use:

```text
ANA MAX Activity Bar -> Codex Companion
```

If it returns `WARN`, read ANA's challenge before mutating files.

## Current Health Gate

Run:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_nucleus_smoke.py --mcp-url http://127.0.0.1:8766/mcp
```

Expected:

```text
ANA Nucleus: PASS
MCP tools: 90
```

## Autonomy Pass

Run:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_autonomy_runner.py --mcp-url http://127.0.0.1:8766/mcp --checkpoint
```

Or use:

```text
ANA MAX Activity Bar -> Autonomy Pass
```

This is the default pre-work confidence pass. It is read-only except for the
optional checkpoint write.

## Quality Gate

Run:

```powershell
python ANA_MAX/dev_artifacts/scripts/lab_quality_gate.py
```

This checks:

- compile of core lab modules
- focused pytest runtime/extension tests
- VS Code extension JavaScript syntax
- governance and permission-manifest coverage
- identity surface and trace alignment
- MCP health
- Nucleus Smoke

## Reload / Install Flow

When reload diagnostics warn but Nucleus Smoke passes, first check whether the
warning is only selected live behavior. Current clean post-reload shape is:

```text
marker=True
tool_surface=PASS
behavior=PASS(checks=9/9)
```

If a future run shows only `behavior=WARN`, restart ANA MCP and then run Live
Behavior, Reload Consistency, and Post-Reload Verify. Use the full runbook for
broader VSIX/IDE reload work:

`Live Behavior` is strict by default: it returns non-zero while status is
`WARN`. Use `--allow-warn` only for diagnostic collection wrappers, not as a
successful reload signal.

```text
docs/ANA_OPERATOR_RELOAD_RUNBOOK.md
```

The short version is:

```powershell
.\ANA_MAX\dev_artifacts\scripts\install_latest_lab_vsix.ps1
.\ANA_MAX\dev_artifacts\scripts\install_latest_lab_vsix.ps1 -Apply
python ANA_MAX/dev_artifacts/scripts/ana_post_reload_verify.py --no-write
```

Reload VS Code and restart ANA MCP between install and verify.

## Future Linux Mate Lane

The lab remains Windows-first today, but new stable work should avoid needless
Windows lock-in. See:

```text
docs/LINUX_MATE_MIGRATION_LANE.md
```

Run the static readiness check:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_linux_readiness.py
```

## Important Docs

- `docs/ANA_LAB_MASTER_CONTEXT.md`
- `docs/ANA_LAB_PROJECT_HISTORY.md`
- `docs/DOCS_INDEX.md`
- `docs/SAFETY_BOUNDARIES.md`
- `ANA_MAX/docs/CURRENT_SESSION_HANDOFF.md`

## Public/GitHub Status

Public/GitHub work is pending. Do not sync or publish lab work unless Billy
explicitly requests it.

## Data Boundary

Do not public-sync:

- `ANA_MAX/memory/`
- `ANA_MAX/logs/`
- `ANA_MAX/screenshots/`
- `ANA_MAX/dev_artifacts/audit/`
- `ANA_MAX/dev_artifacts/reports/`
- local `.env`, keys, tokens, screenshots, videos, private configs, or session
  histories
