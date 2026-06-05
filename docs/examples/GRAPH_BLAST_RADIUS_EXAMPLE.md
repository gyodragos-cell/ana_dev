# Graph Blast-Radius Example

Purpose: estimate what files, tests, symbols, or docs may be affected when a
file changes, using ANA Graph Map.

Profile: `core/private_lab`

Share class: `private-lab, sanitizable`

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_graph_map.py blast --changed ANA_MAX/tools/tool_healthcheck.py --limit 12
```

Equivalent MCP action after live reload:

```text
graph_context_pack action=blast changed=ANA_MAX/tools/tool_healthcheck.py limit=12
```

## Result Shape

```json
{
  "schema": "ana.graph_blast_radius.v1",
  "changed": ["ANA_MAX/tools/tool_healthcheck.py"],
  "matched_changed": [
    {
      "id": "file:ANA_MAX/tools/tool_healthcheck.py",
      "name": "ANA_MAX/tools/tool_healthcheck.py",
      "kind": "file"
    }
  ],
  "affected": [
    {
      "name": "ANA_MAX/tools/tool_healthcheck.py",
      "score": 100,
      "confidence": "EXACT",
      "reasons": ["changed file: ANA_MAX/tools/tool_healthcheck.py"],
      "low_signal": false
    }
  ]
}
```

## What It Proves

- ANA can map a changed file into graph-aware affected context.
- Common noise such as `time`, `json`, `__future__`, `execute`, and
  `get_definition` is filtered so generic imports/symbols do not dominate.
- Generic file names such as `__init__.py` are not matched by basename alone;
  this prevents paths like `tools/__init__.py` from being confused with
  `plugins/__init__.py` when the exact path is not present in the graph.
- Archive, sandbox, memory, screenshot, checkpoint, REM sleep, and historical
  test-report paths are downranked as `low_signal`.
- Probable tests are prioritized when their filename shares specific tokens with
  the changed file.

## Limitation

The result depends on the freshness and quality of Code Map / Graph Map. If
new files or tests were added after the last graph refresh, run Code Map refresh
and Graph Map refresh first.

## Recommended Use

Before editing:

1. Run blast-radius for the target file.
2. Read high-score active code/test results first.
3. Ignore or defer low-signal historical docs unless the task is documentation.
4. Run targeted tests listed by blast-radius before broad gates.
