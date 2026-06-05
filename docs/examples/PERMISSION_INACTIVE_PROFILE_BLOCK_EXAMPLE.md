# Permission Inactive Profile Block Example

Last updated: 2026-05-31

Purpose: prove that ANA can disable whole tool classes by profile, not only by
individual confirmation prompts.

## Evidence

Focused test:

```powershell
python -m pytest tests/runtime/test_ana_governance_check.py::test_permission_manifest_profiles_can_block_inactive_profile -q
```

Result:

```text
1 passed
```

## Scenario

A temporary permission manifest activates only the `core` profile:

```json
{
  "global_settings": {
    "active_profiles": ["core"]
  },
  "tools": {
    "demo_probe": {
      "profile": "security_lab",
      "readonly": true,
      "requires_confirmation": false,
      "allowed": true
    }
  }
}
```

Even though the tool is individually allowed and read-only, ANA blocks it
because its profile is inactive.

## What This Proves

Profiles are real runtime boundaries:

- `core` can remain enabled for normal work
- `windows` can be disabled on Linux
- `security_lab` can be disabled for safe sessions
- `private_lab` can stay local-only

This gives ANA a clean way to run different lab modes without deleting tools.

## Correct Follow-Up

If a blocked tool is needed, do not bypass the check. Switch to the correct
profile intentionally, then rerun the smallest focused command.

## Limitation

This example uses a test/demo tool and a temporary manifest. It proves the policy
mechanism, not any specific production tool behavior.

## Share Class

`sanitized`: safe as a policy architecture example. Do not share private
manifest values, local authorization lists, or lab-only tool targets.
