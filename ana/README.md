# ANA MAX OS v2 — Engine Declarativ

Acest director conține engine-ul ANA MAX OS v2: orchestrator, registry, fallback engine, skill engine, sandbox, servicii deterministe pentru testare și skill-uri declarative.

## Structură principală

- `core/` — orchestrator, registry, fallback, skills engine, sandbox, event bus
- `config/` — `loader.py`, `defaults.yaml`, `skills.yaml`, `learned_rules.yaml`
- `services/` — adaptori deterministi: `http`, `shell`, `llm`, `fs`
- `skills/skills/` — skill-uri declarative: `self-repair`, `health-check`, `fs-inspect`
- `smoke_test.py` — scenariu de verificare end-to-end
- `tests/` — unit & integration tests (16 teste în starea curentă)

## Cum rulezi (developer)

1. Instalează dependențe (dacă există):
   ```bash
   pip install -r requirements.txt
   ```

2. Rulează testele:
   ```bash
   python -m pytest ana/tests -q
   ```

3. Rulează smoke test:
   ```bash
   python ana/smoke_test.py
   ```

## Skills declarative (sumar)

- `self.repair` — detectare probleme, generare și aplicare patch-uri declarative, scriere în `learned_rules.yaml`.
- `health.check` — verifică registry, services, fallback, sandbox.
- `fs.inspect` — inspectare deterministă a filesystem-ului.

## Debug & verificări rapide

- Verifică skill root: `os.skill_engine._skill_root()` (în debug)
- Verifică registry: `registry.tools_for("self.repair")` etc.
- Verifică fallback: `registry.fallbacks_for("llm.complete")`

## Observabilitate

- Event bus loghează: `orchestrator.received`, `orchestrator.routed`, `orchestrator.running`, `orchestrator.completed`.
- Smoke test afișează un sumar final: toate skill-urile executate, fallback configurat, layer deterministic stable.
