# ANA Dev Agent Instructions

This repository treats Codex as the primary project manager and implementation agent, while these instructions apply to every agent, extension, or assistant that works in this workspace.

## Operating Rules

- Golden rule for this lab: use ANA before meaningful action. Run
  `ana_codex_companion.py`, `agent_coach action=recommend`, `tool_router`, or a
  relevant ANA observation/context tool before scoped ANA work. If ANA returns
  `WARN`, pause mutation and address the challenge; if ANA returns `FAIL`, stop
  action work until readiness/evidence is repaired. See
  `docs/ANA_CODEX_GOLDEN_RULE.md`.
- Prefer MCP resources and MCP tools first whenever they provide relevant project context, tool access, diagnostics, or structured knowledge.
- Fall back to local shell, file inspection, or web search only when MCP does not cover the task or when direct verification is needed.
- Read `docs/AGENT_MEMORY.md` before substantial work so durable project context survives across chat sessions and agents.
- Keep edits scoped and preserve existing work from the user, Codex, extensions, or prior lab sessions.
- Before changing shared behavior, inspect the surrounding code and follow the established project patterns.
- When multiple agents or tools are active, avoid reverting or overwriting unrelated changes; integrate carefully with the current workspace state.
- Record durable project guidance here when it should affect future sessions.
- Put ad-hoc experiments, one-off scripts, temporary prompts, and scratch outputs in `ANA_MAX/sandbox/`, not the repository root. Promote only cleaned logic and focused tests into `ANA_MAX/core/`, `ANA_MAX/tools/`, or `tests/`.
- To watch live MCP activity for Codex/ANA, run `ANA_MAX/dev_artifacts/scripts/tail_mcp_log.ps1`. Avoid adding desktop notification dependencies unless explicitly requested.

## Project Context

- Treat `docs/` as the durable project memory. Before architecture, runtime, protocol, security, release, or dashboard changes, read the relevant docs first.
- For MCP/tool strategy, audit, routing, or default agent behavior, read `docs/MCP_TOOL_ORCHESTRATION_PLAN.md`.
- For tool keep/fix/wrap/hide decisions, update `docs/TOOL_MATRIX.md`.
- For high-leverage local/hybrid tools and when to use Frida/watchdog/UI vision, read `docs/AGENT_STEROID_TOOLS.md`.
- When a mother-lab improvement is good but should be synced to the GitHub release later, add it to `docs/PUBLIC_RELEASE_SYNC_BACKLOG.md` instead of relying on chat memory.
- Treat `ANA_MAX/sandbox/`, `ANA_MAX/logs/`, `ANA_MAX/memory/`, local VSIX files, and root `test_*.py`/`test_results*.txt` as lab-only noise unless a human explicitly promotes them.
- ANA MAX is a safe local agent runtime: observe, plan, route, execute, verify, learn.
- Current runtime/kernel work is dev/lab-oriented. Distributed behavior is primarily simulated, deterministic, local-first, and fake-transport based unless the user explicitly approves real integrations.
- Preserve backward compatibility for existing subsystem APIs. Network/distributed features should be additive and continue to work in local-only mode when transport is absent.

## Safety And Release Boundaries

- Respect the project modes from the docs: safe-mode is read-only by default, dev-mode is local lab execution, and write-mode is controlled workspace or release writing.
- High-risk actions need explicit operator intent or approval: subprocess escalation, network access, desktop control, public release writes, private/external system access, and broad file mutation.
- Keep lab-only data out of public exports: private memory, logs, screenshots, local configs, local machine paths, endpoints, session archives, optimization snapshots, private datasets, and secrets.
- Redact token, secret, password, and API key fields before logs, dashboards, docs, exports, or public sync.
- Public-safe material is limited to architecture docs, policy descriptions, test matrices, high-level roadmaps, and reviewed release plans.

## Implementation Guidance

- New tools should define capabilities, policy requirements, normalized result shape, and tests.
- Prefer fake-only scenarios first. Mark lab-only tests explicitly before real tool execution.
- For distributed runtime work, keep message envelopes/versioning compatible with `docs/PROTOCOL_DECISIONS.md`.
- Preserve documented semantics where present: best-effort fire-and-forget replication, last-write-wins conflict handling, local subscriber delivery, local fallback, and deterministic synchronous fake transports.
- Dashboard/API/runtime exposure remains dev-only unless the user explicitly asks for release hardening.

## Diagnostics

- On failures, read the normalized error, check policy decisions, inspect health/profiling metrics, review audit metadata, then use auto-repair suggestions when available.
- After two similar failures or repeated command/tool attempts, stop and consult ANA memory/coach before trying again: use `agent_coach` for telemetry loops and `ana_memory`/`conversation_learning` for known fixes or saved lessons when available.
- When a new recurring fix is discovered, save a compact lesson through the project memory path (`session_checkpoint`, `ana_memory`, or `conversation_learning`) so future agents do not rediscover it.
- Prefer smaller retries, backup tools, suggested patch text, or temporarily disabling a broken tool over broad rewrites.
