# Graph Map Refresh Example

Last updated: 2026-05-31

Purpose: prove that ANA can build a relationship graph from Code Map summaries
and read graph stats back from disk.

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_graph_map.py refresh
python ANA_MAX/dev_artifacts/scripts/ana_graph_map.py stats
```

## Focused Test

```powershell
python -m pytest tests/runtime/test_ana_graph_map.py -q
```

Expected:

```text
2 passed
```

## Outputs

Graph Map writes:

```text
graph.json
GRAPH_REPORT.md
graph.html
```

The graph contains:

- file nodes
- symbol nodes
- dependency nodes
- keyword nodes
- `defines`, `imports`, and `mentions` edges
- confidence labels such as `EXTRACTED` and `INFERRED`

## What This Proves

ANA can move from flat code summaries to relationship-aware project context.
That helps Codex ask "what is near this file?" instead of scanning the whole
workspace.

## Limitation

Graph Map depends on Code Map freshness. Prefer `Refresh Context Maps` when source
files changed significantly.

## Share Class

`sanitized`: safe as architecture evidence. Do not publish private graph files
or local machine paths without review.
