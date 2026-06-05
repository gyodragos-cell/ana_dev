# Tool Profile Summary Example

## Purpose

Show how ANA classifies tools by runtime profile, risk tier, read-only status,
and confirmation requirement before an agent decides what to use.

## Evidence Source

```text
ANA_MAX/memory/tool_profiles/TOOL_PROFILE_REPORT.md
```

## Sanitized Result Summary

Latest lab profile report:

```text
tools_total: 90
active_profiles:
  - core
  - linux
  - private_lab
  - security_lab
  - windows
read_only_tools: 42
confirmation_required_tools: 12
inactive_tools: 0
unprofiled_tools: 0
profile_counts:
  core: 45
  linux: 1
  private_lab: 20
  public_safe: 5
  security_lab: 11
  windows: 19
tier_counts:
  stable: 26
  internal: 32
  experimental: 20
  dangerous: 12
```

## What This Proves

- ANA does not treat all tools as equal.
- Risky tools can require explicit confirmation.
- Security-lab and private-lab tools are separated from core/public-safe tools.
- The permission manifest and report can detect drift: unprofiled tools should
  stay at zero.

## Routing Rule

Use this summary before broad tool execution:

```text
core/public_safe: safe default candidates
windows: local Windows observation/control only
linux: Linux lane preparation
security_lab: authorized defensive diagnostics only
private_lab: Billy + Codex lab continuity only
dangerous tier: never automatic without clear intent and policy
```

## Limitation

This summary intentionally omits the full tool table. The full report is
private-lab material because it can expose internal capability layout and local
development state.

## Share Class

Sanitized. Safe after reviewing counts and removing private timing or internal
tool names if needed.
