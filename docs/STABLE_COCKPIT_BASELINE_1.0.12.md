# Stable Cockpit Baseline 1.0.12

Last updated: 2026-05-27

## Release Intent

v1.0.12 is the stable beginner-friendly cockpit baseline for ANA MAX.
It keeps the existing runtime architecture stable and adds a clear user flow:

```text
Start Runtime -> Smart Ready -> Wake -> Recommend -> Rest Preview -> Save REM
```

## Marketplace Artifact

Use this VSIX for Marketplace publication:

```text
C:\Users\billy\Desktop\ana_dev\vscode_extension\ana-antigravity-chat-1.0.12.vsix
```

Extension identity:

```text
publisher: d4d8176a-bb85-66ef-93dd-a58bc9ddfdad
name: ana-antigravity-chat
version: 1.0.12
displayName: ANA MAX - Hybrid AI Cockpit
```

## Confirmed Behavior

- ANA MAX exposes 85 tools in the current public runtime.
- `session_lifecycle` is now a real MCP tool.
- `Smart Ready`, `tool_router`, `agent_coach`, `ana_identity`, and read-only
  guidance flows are calm and do not show generic confirmation popups.
- Confirmation remains for real-risk actions such as writes, terminal or
  subprocess work, network calls, and desktop control.
- `Rest Preview` runs `session_lifecycle action=rest consolidate=false`.
- `Save REM` runs `session_lifecycle action=rest consolidate=true`.
- Port `8766` must be free when pressing Start Runtime.

## GitHub Public State

Latest public release commit:

```text
d0deb2c Add beginner lifecycle cockpit release
```

GitHub Actions:

```text
Python CI #53: success
Publish GitHub Pages #53: success
Pages deployment #90: success
```

## Final Publish Checklist

1. Upload `ana-antigravity-chat-1.0.12.vsix` to the Marketplace publisher.
2. Verify the Marketplace page shows version `1.0.12`.
3. Install/update from Marketplace in VS Code and Antigravity.
4. Press `Start Runtime` only if no server is already running on port `8766`.
5. Press `Smart Ready`, then `Wake`.
6. Confirm no generic `Allow tool execution?` popup appears for read-only flows.
7. Ask an agent to call `ana_identity`, `tool_router`, and
   `session_lifecycle action=wake`.

