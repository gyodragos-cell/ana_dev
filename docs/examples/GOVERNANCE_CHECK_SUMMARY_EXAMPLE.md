# Governance Check Summary Example

## Purpose

Show how ANA verifies project discipline: required docs, profile terms, no-hype
rules, permission manifest structure, important tool profiles, and confirmation
requirements for risky tools.

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_governance_check.py
```

## Sanitized Result Summary

Latest governance run:

```text
schema: ana.governance_check.v1
status: PASS
summary: 74 pass / 0 fail
tools_total: 90
profile_counts:
  core: 45
  linux: 1
  private_lab: 20
  public_safe: 5
  security_lab: 11
  windows: 19
```

## What This Proves

- Required lab docs and examples exist.
- Profile vocabulary is present: `core`, `windows`, `linux`,
  `security_lab`, `public_safe`, `private_lab`.
- Serious-project rules explicitly reject unsafe hype such as guaranteed
  correctness, replacing developers, or claiming to be unbeatable.
- The permission manifest has active profiles and every tool is profiled.
- Important tools are assigned to expected profiles.
- Risky tools such as desktop control, UIA actions, Frida, input probing, MITM,
  and network pentest require confirmation.

## Failure Meaning

If this check fails, treat the lab as not ready for broad automation until the
failed discipline item is fixed. Examples:

```text
missing doc: project memory or proof is incomplete
missing profile term: routing vocabulary drifted
unprofiled tool: tool may bypass policy review
risky tool without confirmation: unsafe automation boundary
```

## Limitation

Governance checks project structure and policy consistency. It does not replace
runtime smoke tests, tool health checks, or manual review for risky lab work.

## Share Class

Sanitized. Safe after removing local report paths and private tool details if
needed.
