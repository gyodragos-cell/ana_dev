# V2 Product Cleanup Backlog

Last updated: 2026-05-27

Purpose: keep v2 product cleanup separate from the stable v1.0.12 release.
Do not interrupt v1.0.12 Marketplace publication for these changes.

## Product Direction

Position ANA MAX as a local-first agent runtime and hybrid cockpit:

```text
observe -> route -> act -> verify -> remember
```

Use `Agent Runtime`, `Kernel`, or `Cockpit` language before `OS` language.
When old docs mention ANA MAX OS, bridge it clearly:

```text
ANA MAX OS means Agent Runtime Layer, not a computer operating system.
```

## V2 Priorities

| Priority | Item | Why | Risk |
| --- | --- | --- | --- |
| P0 | Update GitHub repo description | First impression is still stale. | Low |
| P1 | Rename repo to `ANA-MAX` or `ana-max-runtime` | Shorter, easier to share, more professional. | Medium: links/docs need review |
| P1 | Terminology cleanup: OS -> Agent Runtime / Kernel / Cockpit | Avoids unnecessary technical criticism. | Medium: many docs mention OS |
| P2 | Split public architecture into runtime package + extension | Cleaner install story and future distribution. | High: package paths/imports |
| P2 | Public install simplification | Help beginners avoid Git/Python confusion. | Medium |
| P3 | Marketplace screenshots and beginner GIF/video | Better conversion after stable release. | Low |

## Immediate Metadata Fix

Recommended GitHub repository description:

```text
Local-first MCP runtime and hybrid cockpit for AI coding agents: observe, route, act, verify, remember.
```

## Repo Rename Options

Preferred:

```text
ANA-MAX
```

Alternative:

```text
ana-max-runtime
```

Keep the current long repository name until v1.0.12 Marketplace publication is
confirmed. GitHub redirects old links after rename, but docs, Marketplace
metadata, and badges should still be reviewed in one dedicated pass.

## Architecture Split Sketch

Future public structure:

```text
ana-max-runtime/      Python MCP runtime, tools, lifecycle, tests
ana-max-cockpit/      VS Code-compatible extension
ana-max-docs/         Site and public guides
```

Do not do this during the v1.0.12 stabilization window.

## Acceptance Criteria For V2 Cleanup

- New users understand the product in 30 seconds.
- README starts with Runtime/Cockpit value, not raw tool count.
- GitHub description, Marketplace description, site hero, and extension README
  use the same language.
- Old OS wording is either removed or clearly explained as Agent Runtime Layer.
- Public tests pass after any path/package split.

