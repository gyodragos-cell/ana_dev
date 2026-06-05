# ANA MAX Self-Repair Specification

Self-repair in ANA MAX OS v2 is centralized in `ana/core/orchestrator/cooperation.py` and supported by:
- declarative skills for repair guidance
- fallback rules for deterministic degradation
- learned rule persistence for repeat patterns
- structured diagnostics and patch suggestion

The self-repair workflow is:
1. detect a recoverable routing or validation failure
2. consult registered fallback handlers and declarative fallback rules
3. consult skill metadata and learned rules
4. choose a deterministic repair path or explain the blocker
5. record the decision in `ana/learnings/learned_rules.yaml`
