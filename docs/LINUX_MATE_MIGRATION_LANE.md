# Linux Mate Migration Lane

Last updated: 2026-05-29

Purpose: prepare ANA MAX Lab for a future Linux Mate workspace without
breaking the current Windows mother lab.

This is not a command to migrate today. The current primary lab remains:

```text
C:\Users\billy\Desktop\ana_dev\ANA_MAX
```

## Decision

Do not block current ANA Lab progress on a full Linux migration.

Do prepare every new stable feature so it can run later in a Linux core profile.
The future Linux Mate move should be a controlled mirror, not a risky rewrite.

## Target Shape

```text
ANA Core Profile
  - MCP server
  - tool_router
  - agent_coach
  - code_context_pack
  - graph_context_pack
  - code map / graph map
  - session_audit / trust
  - session_checkpoint / REM
  - Autonomy Pass
  - Nucleus Smoke

Windows Profile
  - desktop_control
  - foreground UI details backed by Windows APIs
  - windows_uia_bridge
  - window_manager
  - Windows Deep Sight / Insight
  - PowerShell helper scripts
  - SAPI / Windows voice
  - input_api_probe

Future Linux Profile
  - bash helpers
  - Linux process/system observation
  - xdotool/wmctrl or accessibility bridge if needed
  - Linux screenshot/clipboard adapters
  - Linux static/security lab adapters
```

## Readiness Check

Run from the mother lab:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_linux_readiness.py
```

The checker is static and conservative. It scans for Windows-only paths, shells,
Win32/UIA/registry/TTS dependencies, and records a JSON report under:

```text
ANA_MAX/dev_artifacts/reports/linux_readiness_*.json
```

Expected current result: `WINDOWS_FIRST`. That is acceptable. The goal now is
not zero Windows code; the goal is clear separation between portable core and
OS-specific profiles.

## Rules For New Work

- Use `pathlib.Path` and relative project roots.
- Use `sys.executable` instead of hard-coded Python paths.
- Keep PowerShell-only code inside `.ps1` helpers or Windows-profile modules.
- Do not add new `C:\...` paths to core scripts or docs unless explicitly
  describing the current Windows mother lab.
- Put Linux preparation into docs, tests, and adapters; do not rewrite stable
  Windows tools until the Linux mirror exists.
- Nucleus Smoke, Autonomy Pass, Code Map, Graph Map, and Session Audit should
  remain the portability baseline.

## Migration Steps Later

1. Create a separate Linux Mate workspace mirror.
2. Install Python, Node, ripgrep, git, and optional static-analysis packages.
3. Start only MCP core tools first.
4. Run `ana_nucleus_smoke.py`.
5. Run `ana_autonomy_runner.py`.
6. Run `ana_linux_readiness.py`.
7. Add Linux adapters only where the core proves stable.
8. Keep Windows lab intact until Linux passes the same gates repeatedly.

## Prepared Linux Entry Files

The Windows mother lab now carries Linux-prep files that should travel with the
snapshot:

```text
LINUX_START_HERE.md
ANA_MAX/dev_artifacts/scripts/linux_bootstrap.sh
ANA_MAX/dev_artifacts/scripts/linux_core_gate.sh
ANA_MAX/dev_artifacts/scripts/ana_linux_readiness.py
```

On Linux, start with:

```bash
chmod +x ANA_MAX/dev_artifacts/scripts/linux_bootstrap.sh
./ANA_MAX/dev_artifacts/scripts/linux_bootstrap.sh
```

Then use:

```bash
./ANA_MAX/dev_artifacts/scripts/linux_core_gate.sh
```

## What Not To Do

- Do not move the live mother lab abruptly.
- Do not use Kali as the primary dev base before the normal Linux profile is
  stable.
- Do not port fragile desktop/UI tools first.
- Do not public-sync this lane; it is mother-lab planning.
