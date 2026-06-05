# ANA Profile Manifest

Last updated: 2026-05-29

Purpose: define the default operating profiles for ANA MAX so tool routing,
docs, tests, and future Linux migration stay disciplined.

Runtime note: `ANA_MAX/config/permission_manifest.json` can declare
`global_settings.active_profiles` plus per-tool `profile` or `profiles`.
`tools.base.safe_execute` blocks tools whose profile is not active, and
`tool_router` filters recommendations through the same profile metadata.
`ana_governance_check.py` verifies the representative core/windows/security
lab tools, confirmation gates, and that every permission-manifest tool has a
valid profile. Current manifest coverage: 90 active tools after MCP reload.
`ana_permission_manifest_coverage.py` compares runtime-registered tools against
the manifest, and `lab_quality_gate.py` runs that check so new tools cannot
quietly bypass explicit profile classification.
The runtime reloads the permission manifest when the file timestamp changes.
For isolated tests or lab experiments, set `ANA_PERMISSION_MANIFEST` to point at
a temporary manifest file.
Call `tool_router` with `mode=profile_status` for a compact read-only profile
summary that includes active profiles, tool counts, inactive tools, and
unprofiled tools.

## Profiles

### `core`

Default portable lab profile.

Use for:

- project understanding
- code and graph context
- routing and coaching
- health checks
- audit/trust
- checkpoints
- tests
- docs

Representative tools/scripts:

- `tool_router`
- `agent_coach`
- `code_context_pack`
- `graph_context_pack`
- `tool_healthcheck`
- `error_radar`
- `session_audit`
- `session_checkpoint`
- `session_lifecycle`
- `session_rem_sleep`
- `ana_code_map.py`
- `ana_graph_map.py`
- `ana_nucleus_smoke.py`
- `ana_autonomy_runner.py`
- `lab_quality_gate.py`

### `windows`

Windows workstation profile.

Use for:

- Windows UI observation
- Activity Bar workflows
- desktop/user interface diagnostics
- PowerShell helpers
- Windows-only voice/UI automation

Representative tools/scripts:

- `foreground_ui_snapshot`
- `desktop_capture`
- `desktop_control`
- `windows_uia_bridge`
- `uia_click`
- `uia_type`
- `window_manager`
- `windows_insight`
- `windows_deep_sight`
- `ana_mcp.ps1`
- `tail_mcp_log.ps1`

Default rule: observe first, mutation only with operator intent.

### `linux`

Future Linux Mate core mirror profile.

Use for:

- MCP core runtime
- bash helpers
- Linux readiness checks
- portable tests
- code/graph context

Representative tools/scripts:

- `ana_linux_readiness.py`
- `linux_bootstrap.sh`
- `linux_core_gate.sh`
- `ana_code_map.py`
- `ana_graph_map.py`
- `ana_nucleus_smoke.py`
- `ana_autonomy_runner.py`

Default rule: start with core; port desktop/UI tools later.

### `security_lab`

Private authorized diagnostics profile.

Use for:

- static APK/binary inspection
- authorized local runtime diagnostics
- mobile QA/integrity research
- defensive learning
- responsible disclosure preparation

Representative tools/scripts:

- `binary_map`
- `apk_analyzer`
- `input_api_probe`
- `frida_instrument`
- `mitm_analyzer`
- `network_diag`
- `security_audit`
- `ana_binary_map.py`
- `ana_input_probe_spec.py`

Default rule: lab-only, explicit operator intent, sanitized/aggregate output.

### `public_safe`

Sanitized educational/release profile.

Use for:

- architecture docs
- setup docs
- sanitized examples
- smoke tests with no private data
- policy docs

Must not include:

- memory databases
- `.env`
- logs
- screenshots
- local machine paths
- session histories
- private configs
- raw dynamic instrumentation evidence

### `private_lab`

Full Billy mother-lab profile.

Use for:

- private local continuity
- memory
- logs
- session reports
- full Linux migration archive
- experiments not ready for public or team sharing

Default rule: never publish or sync externally.

## Routing Priority

Default routing order:

```text
core -> windows/linux profile if needed -> security_lab only with explicit intent
```

For code work:

```text
code_context_pack -> graph_context_pack -> tool_router -> patch -> tests -> audit -> checkpoint
```

For uncertainty:

```text
error_radar -> agent_coach -> tool_router -> smallest retry
```
