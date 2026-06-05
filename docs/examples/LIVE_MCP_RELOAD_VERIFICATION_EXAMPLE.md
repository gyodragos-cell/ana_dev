# Live MCP Reload Verification Example

Last updated: 2026-05-31

Purpose: show how ANA distinguishes between code that is fixed on disk and code
that the live MCP server has actually loaded.

## Why This Matters

Python MCP tools can stay loaded in the running server process. After editing a
tool module, focused tests may pass because they import the updated file, while
the live MCP server may still be using an older in-memory module until restart
or reload.

## Verification Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py graph_context_pack action=stats
```

## Expected After Reload

After the updated `graph_context_pack_tool.py` is loaded, the response includes
the stale-map signal:

```json
{
  "success": true,
  "data": {
    "schema": "ana.graph_map.v1",
    "stale": false
  }
}
```

`stale=true` is also valid when Code Map changed after Graph Map was built. The
important reload marker is that the `stale` field exists.

## Observed Before Reload

Before MCP reload, the live server can return graph stats without the new field:

```json
{
  "success": true,
  "data": {
    "schema": "ana.graph_map.v1",
    "stats": {
      "nodes": 7764,
      "edges": 15593
    }
  }
}
```

This means the fix is present on disk and in tests, but not yet active in the
running MCP process.

## Correct Follow-Up

1. Restart or reload the ANA MCP server.
2. Run the verification command again.
3. Confirm the `stale` field exists.
4. Run Nucleus Smoke.

## What This Proves

ANA can avoid a common lab mistake: assuming live runtime behavior changed just
because local tests passed.

## Limitation

This is a runtime freshness check for one tool behavior. It does not replace
focused tests, governance, or Nucleus Smoke.

## Share Class

`private-lab, sanitizable`: the method is safe to describe, but raw live MCP
payloads and local paths should stay private unless sanitized.
