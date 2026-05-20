# Engineer Wow Demo

Purpose: give a technical reviewer one clean proof path.

This is not a marketing demo. It is the short engineering check that shows
JokerForge is more than a folder of ideas.

## One Command

Run from the repository root:

```powershell
.\RUN_JOKERFORGE_ENGINEER_PROOF.ps1
```

Or double-click:

```text
RUN_JOKERFORGE_ENGINEER_PROOF.bat
```

## What It Proves

The proof checks five things:

1. Git state is visible.
2. MCP tools are discoverable.
3. Frida can be called through MCP for authorized local diagnostics.
4. Core Python files compile.
5. The full quality gate passes.

The point is not to impress with a long list of tools. The point is to prove
the workflow:

```text
observe -> instrument -> compile -> verify -> report
```

## What A Reviewer Should Notice

An engineer should see that JokerForge is built around evidence:

- the agent does not need to guess what tools exist;
- runtime diagnostics are checked through the same interface an agent can use;
- broken desktop or runtime access should fail visibly;
- release confidence comes from repeatable checks, not optimism.

## Expected Result

At the end, the script should print:

```text
[PASS] JokerForge engineer proof passed.
```

If it fails, the failure is useful. It means the workspace, MCP layer, Frida
path, compile surface, or quality gate needs attention before the project is
presented as stable.

## Why This Matters

This is the difference between an AI coding toy and an operator workflow.

The goal is not that an agent writes more code. The goal is that an agent works
with live facts, uses the smallest relevant tool, and verifies the result.
