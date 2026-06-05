# Local Checkpoint Lane Example

## Purpose

Show how ANA can save a checkpoint through local source for deterministic
handoff continuity. This lane is useful during stale live MCP states, and it is
also safe as the default Activity Bar checkpoint path.

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_local_checkpoint.py --title "Local checkpoint" --summary "Saved through the deterministic local checkpoint lane."
```

## Why This Exists

When live MCP behavior is stale, MCP calls may still use old tool code. In a
previous session, live MCP `session_checkpoint` rewrote
`CURRENT_SESSION_HANDOFF.md` and removed appended operator notes.

The local checkpoint lane imports `tools.session_checkpoint_tool` from the
current source tree and therefore uses the current preservation behavior without
depending on live MCP freshness.

## Expected Shape

```text
ANA Local Checkpoint: PASS Session checkpoint saved: SESSION_CHECKPOINT_<timestamp>.md
path=...\ANA_MAX\docs\SESSION_CHECKPOINT_<timestamp>.md
```

## Safety

- Writes the same checkpoint/memory artifacts as `session_checkpoint`.
- Does not call the live MCP server.
- Good for lab continuity and deterministic handoffs, especially during reload
  diagnostics.

## Share Class

`private-lab, sanitizable`: remove local paths and checkpoint filenames before
sharing outside the lab.
