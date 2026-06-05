# ANA MAX Linux Lab Start Here

Last updated: 2026-05-29

This folder is a private Linux-prep mirror of the ANA MAX mother lab. It exists
so Billy can move to Linux Mate later without losing today's Windows lab state.

Primary Windows lab stays here until Linux is proven stable:

```text
C:\Users\billy\Desktop\ana_dev
```

## First Boot On Linux

From the Linux copy root:

```bash
chmod +x ANA_MAX/dev_artifacts/scripts/linux_bootstrap.sh
./ANA_MAX/dev_artifacts/scripts/linux_bootstrap.sh
```

Then run the static readiness checker:

```bash
python ANA_MAX/dev_artifacts/scripts/ana_linux_readiness.py
```

Run core tests that do not require Windows desktop APIs:

```bash
python -m pytest \
  tests/runtime/test_ana_linux_readiness.py \
  tests/runtime/test_ana_autonomy_runner.py \
  tests/runtime/test_ana_code_map.py \
  tests/runtime/test_ana_graph_map.py \
  tests/runtime/test_code_context_pack_tool.py \
  tests/runtime/test_graph_context_pack_tool.py \
  tests/runtime/test_session_audit_tool.py \
  tests/runtime/test_tool_router_tool.py \
  -q
```

## Linux Core First

Start with:

- Code Map
- Graph Map
- Tool Router
- Agent Coach
- Session Audit / Trust
- Nucleus Smoke after MCP starts
- Autonomy Pass after MCP starts

Do not start by porting:

- Windows UIA
- desktop_control
- Windows Deep Sight / Insight
- PowerShell helper scripts
- SAPI / Windows voice
- input_api_probe

Those stay in the Windows profile until Linux adapters are intentionally built.

## Expected First Result

The readiness checker may say:

```text
ANA Linux Readiness: WINDOWS_FIRST
```

That is not failure. It means ANA still contains Windows-profile tools. The
goal is to keep the portable core clean and move OS-specific pieces behind
profiles.
