# Code Context Pack Example

## Purpose

Show how ANA builds an observation-first context pack by combining current UI
state, Code Map search, Graph Map neighbors, and a compact next-action state.

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py code_context_pack task="tool profile governance example" limit=3 include_graph=true
```

`query="..."` is also accepted as an alias for `task="..."` for compatibility
with agent/search-style tool calls.

## Sanitized Result Summary

The context pack returned:

```text
schema: ana.code_context_pack.v1
snapshot:
  active_app: Code
  title: Visual Studio Code workspace
  detected_errors: []
code_map:
  summaries: 907
  results: 3
  top_candidate: docs/ANA_SERIOUS_PROJECT_RULES.md
graph_map:
  results: 3
compressed_state:
  goal: tool profile governance example
  evidence:
    - foreground_ui_snapshot
    - ana_code_map
    - ana_graph_map
  next_action:
    Open the top candidate only, inspect nearby symbols, then patch or diagnose.
```

When `include_graph=true`, Graph Map can promote a more precise file candidate
above a noisier Code Map text match. This keeps broad text matches, changelog
entries, and old checkpoints from dominating code-change context.

## What This Proves

- ANA can observe the active VS Code context.
- ANA can query Code Map without reading the whole workspace.
- ANA can attach Graph Map relationship context.
- ANA can use Graph Map ranking to reduce noisy Code Map candidates.
- ANA produces a compact state that an agent can use for the next step.
- The workflow supports `observe -> route -> inspect -> act once -> verify`.

## Limitation

Broad queries can return noisy secondary candidates from archives or old lab
material. The agent must inspect the top candidate and filter noise before
editing. Code Context Pack is context selection, not permission to patch.

## Operating Rule

Use `code_context_pack` before code changes when the active file or relevant
module is unclear:

```text
1. Build context pack.
2. Inspect top candidate only.
3. Ignore archive/private-lab noise unless explicitly relevant.
4. Patch the smallest active source surface.
5. Run focused tests.
```

## Share Class

Sanitized. Safe after removing private visible UI text, local paths, and archive
details.
