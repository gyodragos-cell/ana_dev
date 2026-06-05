# Permission Manifest Reload Example

Last updated: 2026-05-31

Purpose: prove that ANA reloads permission policy when the manifest file
changes.

## Evidence

Focused test:

```powershell
python -m pytest tests/runtime/test_ana_governance_check.py::test_permission_manifest_reloads_when_file_changes -q
```

Result:

```text
1 passed
```

## Scenario

The test points ANA at a temporary permission manifest through
`ANA_PERMISSION_MANIFEST`.

First manifest:

```json
{
  "global_settings": {
    "active_profiles": ["core"]
  },
  "tools": {}
}
```

Second manifest:

```json
{
  "global_settings": {
    "active_profiles": ["windows"]
  },
  "tools": {}
}
```

After the file timestamp changes, ANA reloads the manifest and observes the new
active profile.

## What This Proves

Permission policy can change during lab work without changing code:

- switch between `core`, `windows`, `linux`, and `security_lab` profiles
- test safer profiles first
- avoid stale permission decisions
- support future Linux/Mate migration lanes

## Limitation

This proves reload behavior for the manifest loader. It does not decide which
profiles should be active for a specific session; that remains an operator/lab
policy choice.

## Share Class

`sanitized`: safe as architecture evidence. Do not publish private manifest
contents, local authorization targets, or lab-only paths.
