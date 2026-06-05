# ANA MAX Lab LLM Index

Purpose: compact machine-oriented index for Codex, ANA, and future local agents.
Use this before broad file scanning.

Mode: private mother-lab first. Do not public-sync without review.

## Read First

- `AGENTS.md` - workspace operating rules.
- `docs/ANA_LAB_MASTER_CONTEXT.md` - current merged lab context.
- `docs/ANA_CODEX_GOLDEN_RULE.md` - ANA-first rule: Codex must not work blind.
- `docs/AGENT_MEMORY.md` - durable agent memory.
- `docs/SAFETY_BOUNDARIES.md` - local/authorized/defensive boundary rules.
- `docs/DOCS_INDEX.md` - human docs map.
- `ANA_MAX/docs/CURRENT_SESSION_HANDOFF.md` - runtime handoff if present.

## Core Loop

```text
Billy intent -> ANA observe/coach/route -> Codex decides -> act once -> verify -> learn
```

For scoped ANA work, run `ana_codex_companion.py`, `agent_coach`, `tool_router`,
or a relevant ANA context/observation tool before mutating files.

## Current Stable Surfaces

- VS Code Activity Bar controls.
- `ANA MAX MCP` Live Console.
- MCP server: `http://127.0.0.1:8766/mcp`.
- Health endpoint: `http://127.0.0.1:8766/health`.
- Chrome preferred for generated local HTML:
  `C:\Program Files\Google\Chrome\Application\chrome.exe`.

## High-Signal Tools

| Need | Prefer |
| --- | --- |
| Codex anti-blind-work preflight | `ana_codex_companion.py` |
| Fast readiness | `ana_nucleus_smoke.py` |
| Broader gate | `lab_quality_gate.py` or `no_reload_quality_gate.py` |
| Current operator status | `ana_operator_status.py` |
| Live behavior freshness | `ana_live_behavior_check.py` |
| Tool routing | `tool_router` |
| Failure coaching | `agent_coach action=recommend` |
| Code context | `code_context_pack` |
| Relationship context | `graph_context_pack` |
| Changed-file impact | `graph_context_pack action=blast` |
| Health signals | `tool_healthcheck` |
| Log/error signals | `error_radar` |
| Suggest-only repair planning | `ana_patch_advisor.py` with local Dirty Tree evidence |
| Trust summary | `session_audit action=trust` |
| Checkpoint | `ana_local_checkpoint.py` |
| REM/session analysis | `session_lifecycle` / `session_rem_sleep` |

## Code Intelligence

- Code Map: `ANA_MAX/dev_artifacts/scripts/ana_code_map.py`.
- Graph Map: `ANA_MAX/dev_artifacts/scripts/ana_graph_map.py`.
- Code context tool: `ANA_MAX/tools/code_context_pack_tool.py`.
- Graph context tool: `ANA_MAX/tools/graph_context_pack_tool.py`.

Use Code Map for compact file summaries. Use Graph Map when relationships,
neighbors, symbols, or blast-radius analysis matter.

## Current Known Friction

- `web_search` needs `ddgs` or `duckduckgo-search` installed. `web_fetch` and
  `web_scraper` work for exact URLs and should be preferred for controlled
  research.
- Live MCP can keep old Python code loaded until server restart/reload. Current
  tool-surface is PASS at 90 tools; the remaining expected stale signal is
  selected live behavior. If a local test passes but MCP output is stale,
  run/recommend Live Behavior, Reload Consistency, and Post-Reload Verify.
  `ana_live_behavior_check.py` is strict by default; `--allow-warn` is only for
  diagnostic collection wrappers and is not reload success.
- Large dirty lab tree is normal right now. Do not blindly clean/archive without
  explicit operator intent.
- Cockpit webview is not the primary surface. Prefer Activity Bar + Live
  Console.

## Research Pattern

For external material:

1. Prefer exact official docs URLs or GitHub README raw URLs.
2. Fetch/scrape compactly.
3. Keep source URLs.
4. Extract only ANA-relevant design patterns.
5. Write a research intake doc.
6. Do not clone or vendor external repos unless explicitly approved.

Recent research intake:

- `docs/ANA_RESEARCH_INTAKE_2026-05-31.md`
- `docs/examples/WEB_RESEARCH_TOOL_SMOKE_EXAMPLE.md`

## Safety Profiles

- `core`: normal local runtime and docs work.
- `windows`: local Windows observation/control with care.
- `linux`: future portability lane.
- `security_lab`: authorized defensive diagnostics only.
- `private_lab`: local/private evidence and memory.
- `public_safe`: sanitized docs/policy examples only.

Sensitive terms trigger a boundary check, not panic and not permission.

## Verification Defaults

Before serious changes:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_nucleus_smoke.py --mcp-url http://127.0.0.1:8766/mcp
```

After docs/policy changes:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_governance_check.py
```

After extension/runtime changes without reload:

```powershell
python ANA_MAX/dev_artifacts/scripts/no_reload_quality_gate.py
```

## Do Not

- Do not push/sync/publish public release unless Billy explicitly asks.
- Do not move broad docs/files just to make folders pretty.
- Do not use deep instrumentation by default.
- Do not repeat a failing tool blindly after two similar failures.
- Do not store raw private pages/logs/screenshots in public-safe docs.
