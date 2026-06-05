# Code/Graph Stale Map Handling Example

Last updated: 2026-05-31

Purpose: prove that ANA refreshes Graph Map when Code Map changes after the
graph was built.

## Evidence

Focused test:

```powershell
python -m pytest tests/runtime/test_graph_context_pack_tool.py tests/runtime/test_code_context_pack_tool.py -q
```

Expected:

```text
3 passed
```

## Scenario

1. Build Code Map from a project containing `ToolRouter`.
2. Build Graph Map from that Code Map.
3. Modify the source and refresh Code Map so it now contains `FreshGraphSignal`.
4. Query `graph_context_pack` for `FreshGraphSignal`.
5. ANA detects that `graph.code_map_updated_at` differs from the current Code
   Map `updated_at`, rebuilds Graph Map, then returns the fresh symbol.

## What Changed

`graph_context_pack` now checks whether the graph is stale before query/path
actions.

`code_context_pack` also checks staleness before embedding graph results in a
context pack.

## What This Proves

ANA does not have to trust an old graph after Code Map changes. This reduces
wrong-file routing and stale context during long lab sessions.

## Runtime Note

The focused tests import the updated code directly. The live MCP server sees
this behavior after the server/extension reloads the updated Python modules.

## Limitation

The stale check compares Code Map `updated_at` with Graph Map
`code_map_updated_at`. It does not inspect every source file directly; Code Map
must still be refreshed when source files change.

## Share Class

`sanitized`: safe as architecture evidence. Do not publish private graph/index
files or local paths.
