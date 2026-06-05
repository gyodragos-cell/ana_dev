# Context Map Refresh Example

## Purpose

Refresh ANA Code Map and Graph Map in the correct order with one command.

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_refresh_context_maps.py
```

## Expected Clean Shape

```text
ANA Context Maps Refresh: PASS mode=force code=<summaries> graph=<nodes>n/<edges>e maps=code:PASS(<summaries>) graph:PASS(<nodes>n/<edges>e) elapsed=<seconds>s
next_action=Rerun Operator Status or Nucleus Smoke; context maps are fresh.
```

## What This Proves

- Code Map was refreshed first.
- Graph Map was rebuilt from the refreshed Code Map.
- The final map freshness check agrees with Operator Status, Lab State,
  Nucleus, and Autonomy.

## When To Run

Run this when any compact status surface prints stale maps:

```text
maps=code:STALE(...)
maps=graph:STALE(...)
context_maps ... STALE
```

## Safety

Writes only derived local memory under `ANA_MAX/memory/code_map` and
`ANA_MAX/memory/graph_map`. It does not edit source code, install VSIX files,
reload VS Code, restart MCP, archive, delete, or publish anything.

## Share Class

`private-lab, sanitizable`: remove local paths before sharing.
