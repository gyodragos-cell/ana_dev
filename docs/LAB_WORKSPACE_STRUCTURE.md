# ANA MAX Lab Workspace Structure

Last updated: 2026-06-01

Purpose: keep the mother-lab workspace clean while public/GitHub work stays
pending. This is a lab operating guide, not a public release plan.

## Current Priority

Work from the mother lab first:

```text
C:\Users\billy\Desktop\ana_dev\ANA_MAX
```

Public/GitHub release work is low priority and should stay pending unless Billy
explicitly asks to sync or publish.

## Active Surfaces

- `ANA_MAX/` is the active local runtime and lab.
- `vscode_extension/` is the active VS Code/Codex Activity Bar extension source.
- `ANA_MAX_Launcher/` contains launcher and readiness helpers.
- `docs/` contains durable agent memory and lab planning.
- `tests/` contains focused runtime/extension tests.

## Active ANA MAX Folders

- `ANA_MAX/core/`: runtime core.
- `ANA_MAX/tools/`: MCP tools.
- `ANA_MAX/dev_artifacts/scripts/`: lab helper scripts used by Codex/ANA.
- `ANA_MAX/dev_artifacts/reports/`: generated smoke/quality reports.
- `ANA_MAX/dev_artifacts/audit/`: generated session audit JSON.
- `ANA_MAX/docs/`: session checkpoints, handoffs, and lab docs.
- `ANA_MAX/memory/`: private lab memory, code map, and graph map. Do not public-sync.
- `ANA_MAX/config/`: lab config, including local authorization lists.

## Artifact Archive

Old generated packages and build folders were moved here instead of deleted:

```text
ANA_MAX/dev_artifacts/archives/workspace_cleanup_20260529/
```

Contents include:

- old `.vsix` packages from `ANA_MAX/`
- old `.vsix` packages from `vscode_extension/`
- old `vsix_build_*` directories
- old `vsix_verify_*` directories
- old ignored root artifacts such as `debug.log`, `extension.vsixmanifest`, and demo queues
- legacy ignored demo/source snippets
- old zipped dev artifacts

Keep this archive ignored by Git. It is only for rollback/reference.

## Clean Workspace Rules

- Do not put generated `.vsix` packages, reports, screenshots, logs, or temporary
  files in the repo root.
- Put new one-off scripts and experiments in `ANA_MAX/sandbox/` or
  `ANA_MAX/dev_artifacts/scripts/`.
- Put generated reports under `ANA_MAX/dev_artifacts/reports/`.
- Put local proof/audit JSON under `ANA_MAX/dev_artifacts/audit/`.
- Keep public release sync paused unless explicitly requested.
- Before any broad move/delete, run `git status --short` and preserve unrelated
  user or agent changes.

## Current Health Gate

Use the Activity Bar command:

```text
ANA MAX: Nucleus Smoke
```

Or run:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_nucleus_smoke.py --mcp-url http://127.0.0.1:8766/mcp
```

Expected current lab result:

```text
ANA Nucleus: PASS
MCP tools: 90
tool_surface: PASS
behavior: PASS(checks=3/3)
```

If a future update leaves live MCP with stale selected behavior, disk-side tests
and manifests may still be aligned while `behavior=WARN` appears. Restart ANA
MCP, then run Live Behavior, Reload Consistency, and Post-Reload Verify.

Memory archive cleanup remains dry-run-first. Apply archive moves only with the
explicit operator phrase `ARCHIVE_OLD_MEMORY`; counters in reports are dynamic
and should be treated as current evidence, not permanent documentation values.
