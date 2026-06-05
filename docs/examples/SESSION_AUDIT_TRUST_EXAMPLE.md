# Session Audit Trust Example

## Purpose

Show how ANA reports a trust score from evidence signals instead of claiming
that a task is complete without proof.

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py session_audit action=trust hours=1 limit=100
```

## Sanitized Result Summary

The trust tool returned:

```text
schema: ana.session_trust.v1
score: 66
message: Gata cu 66% incredere.
weights:
  context_found: 0.4
  schema_validated: 0.3
  verification_passed: 0.3
signals:
  context_found: 0.5
  schema_validated: 1.0
  verification_passed: 0.55
  identity_surface_status: PASS
  identity_cap_applied: false
  has_ui_snapshot: true
  has_code_context_pack: false
  has_code_map: false
  has_error_radar: true
  has_tool_healthcheck: true
  schema_errors: 0
trace:
  available: true
  aligned: true
  steps: 12
  spans: 12
identity_surface:
  available: true
  status: PASS
  violations: 0
```

## What This Proves

- ANA can explain why confidence is high, medium, or low.
- The score is evidence-based: context, schema validation, and verification.
- Missing context reduces trust instead of being hidden.
- Error Radar and Tool Healthcheck contribute to verification signals.
- Active identity drift cannot increase trust. If the Codex-first identity
  surface fails, ANA caps the score and reports the issue explicitly.
- If a Trace Report exists, session audit includes only a compact trace summary:
  step/span counts, alignment, operation counts, and status. It does not embed
  raw logs, screenshots, or private payloads.

## Limitation

This score is a local session signal, not a guarantee. If the active task needs
source-code context, run `code_context_pack` or refresh Code Map first, then
check trust again.

## Share Class

Sanitized. Safe after removing local run identifiers and any private task
details.
