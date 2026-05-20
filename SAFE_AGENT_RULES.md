# SAFE AGENT RULES

Purpose: keep ANA MAX clean, quiet, and repairable when multiple AI tools are used.

## Allowed Agents For Code Changes

Use only these agents for repo edits:

- Codex
- Antigravity
- Windsurf
- Cursor

Use Qoder only for:

- voice companion experiments
- demos
- read-only observation
- conversation and brainstorming

Qoder must not auto-fix, rewrite, delete, or refactor repo files unless Billy explicitly asks and a trusted agent reviews the diff first.

## Required Workflow

Before editing:

1. Run `git status --short`.
2. Read the target file and nearby code.
3. Use ANA tools through their real interface, usually MCP/tool registry.
4. Verify the tool schema before calling a tool.
5. Treat terminal errors as evidence, not as noise.

When editing:

1. Make the smallest useful change.
2. Avoid broad rewrites for warnings or cosmetic issues.
3. Keep ASCII-only text in source files, scripts, and public docs unless a file already requires Unicode.
4. Do not add emoji, decorative symbols, or noisy banners to code.
5. Do not enable global DEBUG logging unless the task is specifically debug tracing.

After editing:

1. Show or inspect the diff.
2. Run the narrowest relevant test.
3. If a command prints an error, do not report success until the error is explained or fixed.
4. Leave unrelated dirty files alone.
5. Run `RUN_ANA_QUALITY_GATE.bat` before calling the workspace clean.

## ANA Tool Rules

ANA tools are not random Python imports. Prefer MCP/tool registry calls.

Examples:

- Use tool name `frida_instrument` through MCP/registry.
- Use `desktop_capture` before desktop actions.
- Use `windows_uia_bridge` for native Windows UI when possible.
- Use `file_operations`, `smart_search`, `edit`, and `terminal` through their declared schemas.

Always check required parameters first. If a tool says `action` is required, pass `action`.

## Red Flags

Stop and review if an agent:

- says "everything works" while terminal output shows `Traceback`, `ModuleNotFoundError`, `[BAD]`, or exit code 1
- uses a fragile PowerShell regex for non-ASCII scanning instead of a byte scan
- changes dependencies without proving the exact compatibility issue
- edits many files for a small warning
- adds global `logging.basicConfig(level=logging.DEBUG)`
- introduces Unicode/emoji into Windows console scripts or core source
- deletes files without a direct request
- ignores `git status`

## PowerShell Text Scan Rule

For non-ASCII checks on Windows, use byte scanning or the ASCII guard in
`RUN_ANA_QUALITY_GATE.ps1`.

Do not trust a failed inline regex command as a clean scan. PowerShell can break
quoted regex ranges before the search tool runs.

Safe byte-scan pattern:

```powershell
$bytes=[System.IO.File]::ReadAllBytes($path)
$bad=$bytes | Where-Object { $_ -gt 127 } | Select-Object -First 1
```

## Dependency Rule

Warnings from installed packages must be diagnosed against the actual installed versions.

For the current requests warning, check:

- `requests`
- `urllib3`
- `chardet`
- `charset-normalizer`

Do not assume changing only `requests` fixes it. Verify by rerunning the command that produced the warning.

## Billy Preference

Billy wants a clean project with low noise.

Default behavior:

- observe first
- verify before editing
- edit small
- test after
- explain honestly

## Quality Gate

Use this before commits, handoffs, or long breaks:

```text
RUN_ANA_QUALITY_GATE.bat
```

It checks:

- clean git status
- ASCII-only guard for critical scripts
- compile of core ANA files
- `python main.py --test`
- MCP stdio tool listing
- Frida through MCP
