# Web Research Tool Smoke Example

Date: 2026-05-31

Profile: `core/private_lab`

Share class: `private-lab, sanitizable`

Purpose: verify that ANA can use web tools for controlled research and turn the
result into project guidance instead of raw browsing noise.

## What Was Tested

Commands were run through ANA MCP using
`ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py`.

| Tool | Target | Result | Notes |
| --- | --- | --- | --- |
| `web_fetch` | `https://modelcontextprotocol.io/docs` | PASS | Fetched MCP docs text. |
| `web_fetch` | `https://modelcontextprotocol.io/llms.txt` | PASS | Fetched MCP LLM-oriented docs index. |
| `web_scraper operation=extract_metadata` | `https://modelcontextprotocol.io/docs` | PASS | Extracted title, canonical URL, and metadata. |
| `web_scraper operation=extract_links` | `https://modelcontextprotocol.io/docs` | PASS | Extracted 41 links including docs, architecture, SDKs, inspector, debugging, and provider integrations. |
| `web_fetch` | `https://opentelemetry.io/docs/` | PASS | Fetched observability docs index. |
| `web_fetch` | `https://opentelemetry.io/docs/what-is-opentelemetry/` | PASS | Fetched OpenTelemetry concept/navigation content. |
| `web_search` | generic search query | FAIL | Missing optional dependency: `duckduckgo-search`. |

## What ANA Learned

Useful patterns for ANA MAX:

1. `llms.txt` style indexes are high value for agent research. ANA should prefer
   exact docs indexes when available before broad search.
2. MCP's docs structure reinforces ANA's own split between tools, resources,
   prompts, local servers, remote servers, debugging, inspector flows, SDKs, and
   authorization.
3. OpenTelemetry's signal model maps cleanly to ANA observability:
   traces become agent step chains, metrics become pass/warn/fail counters, logs
   become event records, and context propagation becomes run/session identity.
4. ANA should keep research outputs compact: source URL, extracted signal,
   local implication, limitation, next action.
5. Failed search is still useful evidence. It shows `web_search` needs either an
   optional dependency install check, a fallback path, or a clearer health report.

## Local Implications

Recommended follow-up work:

- Add a safe web tool health check that reports whether `web_search` dependencies
  are installed. Implemented in `tool_healthcheck.data.dependencies.web_search`.
- Prefer exact official documentation URLs in lab research tasks.
- Add source-aware research notes to docs instead of storing raw downloaded pages.
- Consider an `ana_research_pack` later: fetch exact sources, extract links,
  summarize project implications, write a compact report, and include source URLs.

## Sources Used

- `https://modelcontextprotocol.io/docs`
- `https://modelcontextprotocol.io/llms.txt`
- `https://opentelemetry.io/docs/`
- `https://opentelemetry.io/docs/what-is-opentelemetry/`

## Result

ANA web research is usable today through `web_fetch` and `web_scraper`.
`web_search` is not currently ready in this environment because an optional
dependency is missing. The correct behavior is to record this as a tool-health
finding, not to keep retrying blindly.
