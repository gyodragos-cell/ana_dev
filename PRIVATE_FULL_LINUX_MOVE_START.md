# ANA MAX Private Full Linux Move Start

This folder is a private full lab clone for Billy's future Linux Mate move.

It intentionally includes private lab state such as local configs, memory,
logs, reports, and session history so the Linux lab can continue from the
Windows mother lab state.

Do not publish, upload, push, share, or public-sync this folder.

## First Steps On Linux

From this folder:

```bash
chmod +x ANA_MAX/dev_artifacts/scripts/linux_bootstrap.sh
./ANA_MAX/dev_artifacts/scripts/linux_bootstrap.sh
```

Then run the core Linux gate:

```bash
./ANA_MAX/dev_artifacts/scripts/linux_core_gate.sh
```

Expected first readiness may still be:

```text
ANA Linux Readiness: WINDOWS_FIRST
```

That is acceptable. It means Windows-profile tools still exist. Start by making
the portable core work first.

## Start With Core

Use these first:

- `ana_linux_readiness.py`
- `ana_code_map.py`
- `ana_graph_map.py`
- `ana_nucleus_smoke.py` after MCP starts
- `ana_autonomy_runner.py` after MCP starts
- `session_audit`
- `tool_router`
- `agent_coach`

Avoid these until Linux adapters are built:

- Windows UIA tools
- PowerShell helpers
- Windows Deep Sight / Insight
- SAPI / Windows voice
- Windows input API probe

## Keep Windows Lab Intact

Do not delete the Windows mother lab until Linux passes the same gates several
times and Billy decides the Linux lab is primary.
