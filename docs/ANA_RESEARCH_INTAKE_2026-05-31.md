# ANA Research Intake - 2026-05-31

Purpose: record useful external material found during ANA web/GitHub research
and decide what is worth adapting into the mother lab.

Mode: mother-lab first, no repo sync, no vendor copying.

## Tool Evidence

ANA web tools used:

- `web_fetch`: PASS on MCP docs, MCP `llms.txt`, OpenTelemetry docs, MCP
  Inspector README, code-review-graph README, and OpenTelemetry GenAI agent
  semantic conventions.
- `web_scraper`: PASS for MCP metadata and link extraction.
- `web_search`: currently blocked by missing optional dependency
  `duckduckgo-search`.

External web search was used as a fallback to discover candidate projects.

## Best Materials Found

| Material | Source | Keep? | Why It Helps ANA |
| --- | --- | --- | --- |
| MCP Inspector | `https://github.com/modelcontextprotocol/inspector` | Yes | Official visual/CLI debugging pattern for MCP servers. Useful for ANA health, schema, transport, and tool-call diagnostics. |
| MCP docs and `llms.txt` | `https://modelcontextprotocol.io/docs`, `https://modelcontextprotocol.io/llms.txt` | Yes | Shows a clean docs-index pattern for agents. ANA can copy the pattern, not the content: compact index, exact source URLs, docs grouped for agent consumption. |
| OpenTelemetry GenAI agent spans | `https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-agent-spans/` | Yes | Strong model for ANA audit/event_stream: root agent run, workflow span, tool execution span, errors, attributes, and context propagation. |
| OpenTelemetry GenAI observability blog | `https://opentelemetry.io/blog/2026/genai-observability/` | Yes | Confirms the direction: tool calls and agent steps need explicit traces, not just terminal logs. |
| code-review-graph | `https://github.com/tirth8205/code-review-graph` | Study | Similar to ANA Code Map + Graph Map: Tree-sitter, incremental graph, blast-radius analysis, minimal context. Useful validation, but do not vendor it into ANA. |
| CodeGraph | `https://github.com/Phoenixrr2113/codebase-graph` | Study | MCP code knowledge graph with AST, vector/reranker retrieval, bitemporal facts. Good inspiration for future graph queries and time-aware facts. |
| traceAI | `https://github.com/future-agi/traceai` | Study | OpenTelemetry-based tracing for LLM/tool/retrieval/agent decisions. Useful for ANA trace vocabulary. |
| OpenLIT | `https://github.com/openlit/openlit` | Defer | Big platform. Useful as market signal for observability/eval/guardrails, but too broad for ANA lab right now. |
| Phoenix | `https://github.com/Arize-ai/phoenix` | Defer | Strong observability/evaluation platform. Keep as reference, not a dependency. |
| Uptrace | `https://github.com/uptrace/uptrace` | Defer | Good self-hosted OTel backend, but ANA should first emit compact local traces before adding backend complexity. |

## What ANA Should Adapt

### 1. MCP Inspector-Like Diagnostics

Do not replace ANA Activity Bar. Add a small local diagnostic mode that proves:

- server health
- `tools/list`
- schema lookup for selected tools
- one safe `tools/call`
- transport URL and error message
- optional export of a minimal MCP client config

ANA already has pieces of this through Nucleus Smoke, Operator Status, and
Post-Reload Verify. The improvement is a more inspector-like report organized
by transport/schema/tool call.

### 2. `llms.txt`-Style Lab Docs Index

ANA already has `DOCS_INDEX.md`, but a machine-oriented `ANA_LAB_LLM_INDEX.md`
would help agents quickly load the right context.

Shape:

```text
# ANA MAX Lab

## Read First
- docs/ANA_LAB_MASTER_CONTEXT.md
- docs/AGENT_MEMORY.md
- docs/SAFETY_BOUNDARIES.md

## Tools
- code_context_pack: ...
- graph_context_pack: ...

## Workflows
- health -> observe -> route -> act -> verify -> learn
```

This should contain no private logs or screenshots.

### 3. OTel-Inspired Agent Trace Vocabulary

ANA should keep local JSONL, but use better field names:

- `run_id`
- `trace_id`
- `span_id`
- `parent_span_id`
- `operation`: `agent_run`, `workflow`, `tool_call`, `context_pack`,
  `verification`, `audit`, `checkpoint`
- `tool_name`
- `input_digest`
- `result_digest`
- `status`
- `duration_ms`
- `evidence`
- `risk_level`

This fits current `session_audit`, `event_stream`, `autonomy_runner`, and
`patch_advisor` without requiring a full OTel backend.

### 4. Graph Blast-Radius Query

ANA Graph Map exists. Next useful feature is not a new graph product; it is a
small query:

```text
given changed files -> affected files/tests/symbols -> confidence -> why
```

This directly helps Codex before editing and before declaring a fix done.

### 5. Web Research Pack

Later, create `ana_research_pack`:

1. take exact URLs or a query
2. fetch/scrape
3. keep source URLs
4. summarize only project-relevant signals
5. record failures like missing dependencies
6. write a compact report under `docs/`

Do not store raw downloaded pages by default.

## What Not To Do

- Do not import big observability platforms into ANA right now.
- Do not add another dashboard before core reports are clean.
- Do not clone and blend external repos into the lab.
- Do not chase benchmark claims without reproducing them locally.
- Do not expose lab-only telemetry or private traces publicly.

## Immediate Tasks

1. Add a web-tool dependency check for `web_search`.
2. Add `ANA_LAB_LLM_INDEX.md` for agent-friendly context loading. Implemented
   as `docs/ANA_LAB_LLM_INDEX.md`.
3. Add a future task for Graph Map blast-radius query.
4. Consider an OTel-inspired `agent_trace_schema` doc before changing
   runtime event formats. Implemented as `docs/ANA_AGENT_TRACE_SCHEMA.md` and
   `ANA_MAX/core/agent_trace_schema.py`.

## Sources

- `https://modelcontextprotocol.io/docs`
- `https://modelcontextprotocol.io/llms.txt`
- `https://github.com/modelcontextprotocol/inspector`
- `https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-agent-spans/`
- `https://opentelemetry.io/blog/2026/genai-observability/`
- `https://github.com/tirth8205/code-review-graph`
- `https://github.com/Phoenixrr2113/codebase-graph`
- `https://github.com/future-agi/traceai`
- `https://github.com/openlit/openlit`
- `https://github.com/Arize-ai/phoenix`
- `https://github.com/uptrace/uptrace`
