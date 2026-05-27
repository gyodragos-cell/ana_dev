# ANA MAX v26 Release Plan

## Sync Rules

- Sync public-safe docs only unless code is explicitly approved.
- Do not sync memory stores, optimization snapshots, logs, screenshots, local
  configs, or private workspace paths.

## Test Matrix

```powershell
python -m compileall -q core tests\runtime tests\integration
python -m pytest tests\runtime tests\integration -q
node --check vscode_extension\extension.js
```

## Site Update Plan

- Add a v26 runtime section.
- Link governance and observability dashboard specs.
- Keep tool count unchanged unless tool registry changes.

## Suggested Public Surface

- `docs/ANA_MAX_GOVERNANCE.md`
- `docs/ANA_MAX_OBSERVABILITY_DASHBOARD.md`
- `docs/ANA_MAX_V26_RUNTIME.md`
- `docs/ANA_MAX_V26_ROADMAP.md`
- `docs/ANA_MAX_V26_RELEASE_PLAN.md`
