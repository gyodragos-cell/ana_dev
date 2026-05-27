# ANA MAX Observability Dashboard Spec

## Panels

- Tools: latency, success rate, failure streak, output bytes.
- Router: recent decisions, score components, scenario fit.
- Health: degraded tools, noisy tools, uptime.
- Memory: semantic hits, episodic summaries, decay status.
- Agents: active roles, messages, lifecycle.
- Sessions: active session state and memory counts.

## Metrics

- `tool_latency_ms`
- `tool_success_rate`
- `failure_streak`
- `noisy_tool_score`
- `routing_score`
- `scenario_effectiveness`
- `policy_block_count`

## Integration Points

- VS Code webview panels.
- Future web dashboard.
- Observability and audit trail snapshots.
