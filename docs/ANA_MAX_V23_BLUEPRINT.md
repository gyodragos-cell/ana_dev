# ANA MAX v23 Blueprint

Status: development blueprint
Scope: `ana_dev` only until the implementation is verified

## Router v23

- Use health monitor feedback for reliability, failure streak, output size,
  noise, and recent latency.
- Keep safety gates before mutating tools.
- Add multi-step fallback chains with explicit stop reasons.

## Observability v23

- Promote correlation IDs from placeholders to runtime-generated IDs.
- Track rolling latency percentiles and bounded event history.
- Export a compact health snapshot for VS Code and future dashboards.

## Scenario v23

- Convert fake scenarios into deterministic replay bundles.
- Add coverage metrics for router, execution, safety, and fallback paths.
- Keep scenarios fake-only unless explicitly marked as lab integration.

## Execution v23

- Support injected registries, mappings, and callable tool adapters.
- Normalize all results into one compact schema.
- Record latency, output bytes, success, fallback attempts, and truncation.

## Registry v23

- Keep the MCP registry as the execution authority for real tools.
- Add schema-aware argument building before live tool calls.
- Preserve premium/internal gates and confirmation boundaries.

## Runtime v23

- Move from single-step runtime to bounded multi-step orchestration.
- Keep safe-mode default-on.
- Expose a demo command for local validation without live tool execution.

## MCP Integration v23

- Add `MCPClient` as the disabled-by-default bridge for MCP tool execution.
- Describe each tool with a `ToolEndpoint`: local, MCP, or remote.
- Normalize MCP success, timeout, disabled-server, and invalid-response cases.
- Keep auth as references only; no secrets in code or config.

## Local Model v23

- Support cloud, local, and hybrid AI backends.
- Let tests inject fake model backends through `generate(prompt, context)`.
- Keep real local model calls off unless explicitly configured.
- Fall back from local to cloud-compatible deterministic output on failure.

## Auto-Repair v23

- Convert failures into text-only repair plans.
- Supported strategies: retry, switch tool, suggest patch, diagnose, stop.
- Never apply patches automatically.
- Attach repair suggestions to execution failures and scenario failure flows.

## Self-Optimization v23

- Compute in-memory routing adjustments from success rate, latency, noise, and
  scenario feedback.
- Feed reliability and noisy-tool scores into router scoring.
- Export text reports only; no persistent config writes in safe-mode.

## Roadmap

1. Stabilize runtime activation with fake registry tests.
2. Wire health monitor into router scoring everywhere.
3. Add VS Code HTTP/MCP client calls behind safe-mode.
4. Add scenario bundles for CI.
5. Add real MCP execution tests behind explicit lab markers.
6. Add auto-repair dashboards and approval workflows.
7. Persist optimization snapshots only after policy review.
