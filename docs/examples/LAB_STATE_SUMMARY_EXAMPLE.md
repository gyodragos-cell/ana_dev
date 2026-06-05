# Lab State Summary Example

Last updated: 2026-06-01

Purpose: provide one compact command that summarizes the current ANA lab state.

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_lab_state_summary.py --no-write
```

## Sanitized Result

```text
ANA Lab State: mcp_ready=True tools=90 package=PASS(main=True,copy=True) reload=PASS tool_surface=PASS(live=90,manifest=90,extra=0,missing=0) behavior=PASS(checks=9/9) maps=code:PASS(<n>) graph:PASS(<nodes>n/<edges>e) identity=PASS(files=10,violations=0,missing=0) trace_aligned=True file_deleted=0 dirty=<n> archive_candidates=<n> date_basis=utc archive_readiness=PASS
next_action=Run Nucleus Smoke, then continue with one scoped action.
```

## What It Combines

- MCP `/health`
- current VSIX package artifact readiness
- live reload marker status
- live MCP tool-surface drift against the local permission manifest
- selected live behavior freshness checks
- Code Map / Graph Map freshness
- Codex-first active identity surface status
- latest Autonomy trace alignment
- aggregate file activity counts from the authorized workspace snapshot
- memory hygiene counts
- archive date basis (`utc`)
- archive dry-run count
- latest memory archive readiness status
- git dirty-tree count

The default memory hygiene policy keeps the latest 20 checkpoints and latest 20
REM reports. `STALE` means the latest saved dry-run archive report is internally
valid, but new checkpoint/REM files appeared after it was generated.

## What This Proves

ANA can produce a short handoff state without scrolling through several reports.
This is useful before pausing, restarting the server, moving to Linux, or handing
the lab to a future session.

## Limitation

This is a summary, not a full gate. Use Nucleus Smoke or the no-reload quality
gate for verification.

## Share Class

`private-lab, sanitizable`: safe after removing local paths and private report
details.
