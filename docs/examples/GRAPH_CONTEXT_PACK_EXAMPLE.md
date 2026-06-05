# Graph Context Pack Example

## Purpose

Show how ANA uses Graph Map through MCP to expand context by relationships:
files, symbols, dependencies, keywords, and neighbors.

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py graph_context_pack action=query query="tool_router code_context_pack graph_context_pack" limit=3
```

## Sanitized Result Summary

The graph context pack returned:

```text
schema: ana.graph_query.v1
results_count: 3
top_result:
  id: file:ANA_MAX/tools/code_context_pack_tool.py
  kind: file
  score: 56
  degree: 41
  matched_terms:
    - code
    - context
    - pack
    - tool
  purpose: Compact UI + code-map context pack for agent routing.
  neighbor examples:
    - defines _load_code_map_module
    - defines _candidate_terms
    - defines _compact_snapshot
    - defines CodeContextPackTool
    - defines execute
other_results:
  - tests/runtime/test_code_context_pack_tool.py
  - symbol:tool_router
next_step:
  Use top node neighbors to choose the smallest context pack.
```

## What This Proves

- ANA can query relationship-aware graph context over the code map.
- Results include file nodes, symbol nodes, degrees, matched terms, and
  neighbor relationships.
- Graph context helps identify related tests and important symbols.
- Graph Map is useful after Code Map identifies the likely area.

## Limitation

Graph search can prefer high-degree relationship nodes. For exact file lookup,
use Code Map first; then use Graph Context Pack to expand around the selected
file or symbol.

## Operating Rule

Use Graph Context Pack when:

```text
you know the target area but need related symbols
you need to find tests around a module
you need dependencies or neighbor files
you want to avoid reading unrelated project sections
```

## Share Class

Sanitized. Safe after removing private paths and archive/lab-only graph nodes.
