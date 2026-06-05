# Permission Manifest Coverage Example

## Purpose

Show how ANA verifies that every runtime MCP tool is represented in the
permission manifest, and that the manifest does not contain stale tool entries.

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_permission_manifest_coverage.py
```

## Sanitized Result Summary

Latest coverage run:

```text
schema: ana.permission_manifest.coverage.v1
status: PASS
runtime_tools: 90
manifest_tools: 90
missing_in_manifest: 0
extra_in_manifest: 0
```

## What This Proves

- Runtime tool registration and policy manifest are synchronized.
- New tools cannot silently bypass profile/policy review.
- Removed tools do not stay in the manifest as stale policy entries.
- This supports profile-based routing and inactive-profile blocking.

## Failure Meaning

If this check fails:

```text
missing_in_manifest: runtime has a tool with no policy entry
extra_in_manifest: manifest references a tool not currently registered
```

Treat either case as a governance issue before trusting broad automation.

## Limitation

Coverage proves presence, not correctness of every policy value. Governance and
focused tests still need to verify profile names, confirmation flags, and risky
tool boundaries.

## Share Class

Sanitized. Safe after removing local report paths.
