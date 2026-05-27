# ANA MAX v23 Runtime Architecture

Status: dev blueprint and release-prep document
Scope: `ana_dev` first; public sync requires an explicit phase

## Runtime v23 Architecture

```text
Input Layer
  -> Context Builder
  -> Hybrid AI Engine
  -> Adaptive Tool Router
  -> Execution Layer
  -> Observability + Health Monitor
  -> Auto-Repair + Self-Optimization
```

The runtime remains safe-mode first. Live execution exists, but subprocess,
network, and file writes are blocked unless the runtime is explicitly moved out
of safe-mode with controlled policy.

## Live Tool Execution

Execution supports:

- Python-callable tools through injected registries or mappings.
- Built-in `file_read` and controlled `file_write`.
- Built-in `subprocess_exec` when subprocess capability is allowed.
- Built-in `network_get` through an injectable transport or configured network
  permission.
- MCP and remote endpoints through `ToolEndpoint`.

Capability flags:

```text
safe_read
safe_write
network_allowed
subprocess_allowed
```

## Adaptive Router v23

Router score shape:

```text
score = base_score
      + reliability_boost
      - noise_penalty
      - latency_penalty
      + scenario_fit
      + optimization_feedback
```

The router keeps the last 50 decisions in memory and records scenario
effectiveness. It consumes health monitor and self-optimization feedback.

## Hybrid AI Engine

Supported modes:

- `cloud`
- `local`
- `hybrid`

Hybrid mode tries a local backend first and falls back to a cloud-compatible
backend when local generation fails. Real local model calls remain opt-in.

## Self-Healing Runtime

Auto-repair converts failures into safe repair plans:

- retry with adjusted parameters
- switch to backup tool
- suggest code patch as text only
- log diagnostic hints
- temporarily disable broken tools after repeated failures

No repair plan applies code automatically.

## VS Code Integration

The dev extension exposes:

- `ANA MAX: Execute Tool`
- `ANA MAX: Inspect Runtime`
- `ANA MAX: Show Router Decisions`
- `ANA MAX: Show Observability`
- scenario and health panels

Safe-mode blocks tool execution until a confirmation flow is implemented.

## Roadmap

### v23-alpha

- Keep all live execution behind safe-mode policies.
- Expand fake MCP and local model tests.
- Stabilize router memory and health feedback.

### v23-beta

- Add explicit lab-only MCP integration tests.
- Add VS Code webview data refresh.
- Add scenario effectiveness dashboards.

### v23-rc

- Freeze capability flags and sandbox rules.
- Review public-safe docs and release surfaces.
- Run full runtime, extension, and release hygiene matrix.

### v23 Public Release

- Sync only ship-safe code, tests, docs, and extension scaffolding.
- Keep secrets, logs, memories, screenshots, and private lab state out.
- Tag and push only after explicit release confirmation.

## Release Plan

Sync rules:

- Public sync requires explicit phase approval.
- No private runtime data leaves `ana_dev`.
- MCP and local model integrations must document disabled-by-default behavior.

Safe-mode rules:

- Read-only by default.
- No subprocess.
- No network.
- No file writes.

Write-mode rules:

- Controlled writes only.
- No public release writes unless a phase explicitly says so.
- Destructive operations require confirmation.

Extension packaging:

```powershell
node --check vscode_extension\extension.js
```

Test matrix:

```powershell
python -m compileall -q core tests\runtime
python -m pytest tests\runtime -q
node --check vscode_extension\extension.js
```
