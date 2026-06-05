# Graph Map Query Example

## Purpose

Show how ANA uses Graph Map to retrieve relationship-aware context from files,
symbols, dependencies, and keywords.

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_graph_map.py refresh
python ANA_MAX/dev_artifacts/scripts/ana_graph_map.py query --query "tool_profile_report" --limit 5
```

## Sanitized Result Summary

The query returned graph nodes with scores, node kinds, neighbors, and relation
confidence.

Top result example:

```text
node: file:ANA_MAX/tools/session_audit_tool.py
kind: file
score: 36
degree: 48
matched_terms: report, tool
purpose: Session audit and trust-score report tool.
neighbor relation examples:
  - defines _now_iso
  - defines _sha256
  - defines _redact
  - defines _score
confidence: EXTRACTED
```

Other results included:

- existing bug report template file
- `ANA_MAX/TOOL_STATUS.md`
- archived tool-calling example

## What This Proves

- ANA can search across graph nodes, not only text files.
- Results include degree, matched terms, purpose, and neighbors.
- Graph edges have confidence labels such as `EXTRACTED` and `INFERRED`.
- Graph Map is useful when relationships matter, such as which symbols a file
  defines or which files mention a keyword.
- Graph Map is a relationship-discovery layer, not the first choice for exact
  file lookup when Code Map already has a specific source summary.

## Limitation

The query was broad, and Graph Map currently scores high-degree reporting/tool
nodes ahead of the exact newly-added tool profile script. This is useful for
discovery but not ideal for exact file lookup.

When precision is needed, route like this:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_code_map.py query --query "ana_tool_profile_report permission_manifest" --limit 5
```

Then use Graph Map on the selected file or related symbols to inspect
relationships. This gives ANA a better policy: Code Map first for exact
location, Graph Map next for dependency/context expansion.

## Share Class

Sanitized. Safe after reviewing paths and removing private/lab-only nodes if
used outside the lab.
