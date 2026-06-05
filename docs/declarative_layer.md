# ANA MAX Declarative Layer

The declarative layer for ANA MAX OS v2 includes:
- declarative skills under `ana/skills/skills`
- declarative fallback rules under `ana/core/fallback/rules.py`
- declarative disciplines under `ana/disciplines`
- declarative skill-to-capability mappings under `ana/config/skills.yaml`
- learned repair patterns under `ana/learnings/learned_rules.yaml`

This layer separates runtime execution from policy knowledge. It allows ANA MAX to:
- validate skill declarations before runtime
- apply fallback chains based on capability-level rules
- record learned repair behavior over time
- keep deterministic behavior under strict boundaries
