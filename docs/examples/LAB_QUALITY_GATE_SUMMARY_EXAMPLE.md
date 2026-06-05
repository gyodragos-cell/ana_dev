# Lab Quality Gate Summary Example

## Purpose

Show the broader mother-lab verification gate ANA should run after larger
runtime, extension, governance, or test changes.

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/lab_quality_gate.py
```

## Sanitized Result Summary

Latest known quality gate report:

```text
schema: ana.lab_quality_gate.v1
status: PASS
compile_core_tools_scripts: PASS
pytest_focused_runtime: PASS, 145 passed
governance_check: PASS
permission_manifest_coverage: PASS
extension_js_syntax: PASS
vsix_version_consistency: PASS
identity_surface_check: PASS
trace_report: PASS
mcp_health: PASS
nucleus_smoke: PASS
```

## What This Proves

- Python runtime files compile.
- Focused runtime tests pass, including the Nucleus Smoke unit contract.
- Local checkpoint lane and checkpoint handoff preservation tests pass.
- Governance docs and profile rules are enforced.
- Runtime tools and permission manifest match.
- VS Code extension JavaScript parses.
- Active VSIX version references match `vscode_extension/package.json`.
- Active lab and extension identity stays Codex-first and neutral.
- Autonomy trace spans validate and align with recorded autonomy steps.
- MCP health is online.
- Nucleus Smoke passes after the broader checks.

## When To Use

Run this after:

```text
adding or removing MCP tools
changing permission/profile policy
changing Activity Bar commands
editing context pack or routing behavior
editing governance docs/tests
editing checkpoint or handoff behavior
preparing a lab handoff
```

## Limitation

Lab Quality Gate is heavier than Nucleus Smoke. Use Nucleus Smoke for quick
readiness and this gate when the change affects multiple layers.

## Share Class

Sanitized. Safe after removing full local command paths, raw MCP tool lists, and
private report paths.
