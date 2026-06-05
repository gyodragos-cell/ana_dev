# ANA OS v2 Skills Specification

This document defines how declarative skills are authored for ANA MAX OS v2.

Each skill must be stored under `ana/skills/skills/<skill-name>/SKILL.md`.

Required sections:
- `Context`
- `Scop`
- `Structura directoare`
- `Componente OS v2`
- `Discipline OS v2`
- `Taskuri pentru implementare`
- `Reguli pentru Codex`
- `Output asteptat`

Required metadata:
- `Version` (semantic version of the skill declaration)
- `Capability` mapping declared in `ana/config/skills.yaml`

Skills must also declare task headings A through K in order.

Skill execution is not a live service call. Skills are a declarative bridge between capability intent and the runtime orchestration layer.
