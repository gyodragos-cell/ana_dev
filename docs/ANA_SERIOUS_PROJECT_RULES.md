# ANA Serious Project Rules

Last updated: 2026-05-29

Purpose: keep ANA MAX disciplined as it grows from a private experiment into a
serious local agent lab.

## Product Truth

ANA MAX is not "an AI that can do everything."

ANA MAX is a local-first agent runtime and QA lab that helps an operator:

- observe context
- choose tools
- run focused checks
- collect evidence
- verify results
- save memory
- continue work across sessions

The core loop is:

```text
observe -> diagnose -> route -> act once -> verify -> learn
```

## What ANA Can Claim

ANA can claim:

- local MCP tool orchestration
- structured QA workflows
- code map and graph map context
- smoke tests and health gates
- trust/audit reports based on available evidence
- checkpoints and session memory
- Windows lab tools with explicit operator control
- future Linux core profile preparation

## What ANA Must Not Claim

ANA must not claim:

- guaranteed correctness
- autonomous safety without operator oversight
- full operating-system control in public/default mode
- stealth instrumentation
- anti-cheat bypass
- exploit automation
- professional security certification
- production readiness without evidence
- that every tool is stable just because it exists

## No Hype Rule

Do not describe ANA with exaggerated claims such as:

- "god mode" as a public promise
- "unbeatable"
- "guaranteed"
- "controls everything"
- "sees all memory"
- "replaces developers"

Lab nicknames may exist privately, but docs, CV, public material, and serious
handoffs should use precise language.

## Profile Rule

Every tool or workflow should belong to one profile:

- `core`
- `windows`
- `linux`
- `security_lab`
- `public_safe`
- `private_lab`

If a tool is powerful, invasive, or privacy-sensitive, it must not be part of
the default core profile.

## Evidence Rule

Before saying something works, keep evidence:

- test output
- smoke report
- audit report
- checkpoint
- before/after behavior
- known limitation

Preferred gates:

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_nucleus_smoke.py --mcp-url http://127.0.0.1:8766/mcp
python ANA_MAX/dev_artifacts/scripts/ana_autonomy_runner.py --mcp-url http://127.0.0.1:8766/mcp --checkpoint
python ANA_MAX/dev_artifacts/scripts/lab_quality_gate.py
```

## Collaboration Discipline Rule

ANA Lab should optimize for coherent work, not for the number of agents or
tools involved. The active lab identity is Codex-first: Billy + Codex + ANA.

Default collaboration model:

```text
Billy brings material, context, and real-world signals.
Codex filters, designs, implements, verifies, and keeps the project coherent.
ANA observes, reports, audits, remembers, and proposes suggest-only fixes.
```

External tools, agent products, or repos may be researched as market signals,
but they must not become project identity, credits, or promotion in active lab
docs or extension copy. If a useful pattern is found, distill it into
lab-native ANA behavior with neutral wording.

Do not write active docs as competitive comparisons or as advertising for
another tool.
Keep the surface:

```text
Codex-first
ANA-for-Codex
neutral about external tools
evidence over branding
```

Quality order:

```text
organization -> respect for future readers/coworkers -> clarity -> utility -> features
```

If an idea is exciting but not useful, safe, testable, and documentable, park it
or discard it.

## Security Lab Rule

Deep diagnostics such as Frida, process memory, input APIs, MITM analysis, and
pentest tooling stay `security_lab` / `private_lab` by default.

Allowed framing:

- authorized local diagnostics
- defensive learning
- static analysis
- aggregate reporting
- responsible disclosure

Forbidden framing:

- bypassing protections
- credential capture
- persistence
- stealth monitoring
- public exploit steps
- targeting third-party systems without authorization

## Example Rule

ANA should have real examples, not only architecture:

- example health report
- example Autonomy Pass report
- example Code Map query
- example Graph Map query
- example bug report template
- example Linux restore flow
- example CV/job-search support workflow

Examples must be sanitized before public sharing.
