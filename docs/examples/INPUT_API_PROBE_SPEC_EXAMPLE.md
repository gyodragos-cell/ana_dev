# Input API Probe Spec Example

## Purpose

Show how ANA prepares a lab-only Windows input API probe specification without
executing instrumentation or recording raw input.

## Commands

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py input_api_probe operation=list_authorized confirm=true
python ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py input_api_probe operation=spec target_process="ana_lab_demo.exe" api_name=RegisterRawInputDevices duration=5 sample_limit=100 confirm=true
```

## Sanitized Result Summary

Authorized targets:

```text
schema: ana.input_api_probe.authorized.v1
authorized_targets: []
lab_only: true
```

Generated spec:

```text
schema: ana.input_api_probe.spec_result.v1
authorized: false
target: ana_lab_demo.exe
api: RegisterRawInputDevices
module: user32.dll
export: RegisterRawInputDevices
duration_sec_max: 5
sample_limit_max: 100
policy:
  requires_operator_confirmation: true
  authorized_targets_only: true
  no_anti_cheat_bypass: true
  no_continuous_monitoring: true
  no_raw_key_storage: true
  no_character_decoding: true
  aggregate_counts_only: true
  public_release: forbidden
allowed_output:
  aggregate counts only
```

## What This Proves

- ANA can generate a diagnostic probe spec without execution.
- Input probing is lab-only and confirmation-gated.
- Unauthorized targets do not execute.
- Output is restricted to aggregate counts.
- The policy forbids raw key storage, character decoding, continuous monitoring,
  and public release.

## Manifest Lesson

The permission manifest requires `confirm=true` even for spec/list operations.
This is intentionally stricter than the inner tool logic because
`input_api_probe` is a security-lab capability.

## Safety Rule

Use `input_api_probe` only for authorized local diagnostics:

```text
prefer list_authorized and spec first
execute only with explicit operator intent
execute only on an authorized target
keep duration short
return aggregate-only output
never use for monitoring people or capturing typed content
```

## Limitation

This example does not attach to a process. It proves policy, spec generation,
and guardrails, not runtime instrumentation.

## Share Class

Lab-only by default. Sanitized architecture summaries can be shared, but do not
share operational Frida templates or private target lists outside the lab.
