# ANA MAX — Advanced Neural Architecture

**ANA MAX** este un proiect compus din două componente principale, clar delimitate:

- **ANA MAX OS v2 (engine)** — un OS AI **declarativ** și **determinist**: orchestrator, registry, fallback engine, skill engine, sandbox, config loader, event bus. Conține skill-uri declarative (ex: `self.repair`, `health.check`, `fs.inspect`), test suite și smoke test.
- **ANA MAX Windows MCP Agent (legacy / runtime)** — agent Windows-first cu MCP tools, UI automation și integrare VSCode. Rămâne disponibil ca strat de integrare sau runtime istoric.

---

## Unde găsești ce te interesează

- **Engine (OS v2)**: `ana/`
  - Teste: `ana/tests/`
  - Smoke test: `ana/smoke_test.py`
  - Config: `ana/config/` (incl. `skills.yaml`, `learned_rules.yaml`)
  - Skills declarative: `ana/skills/skills/`
  - Documentație: `ana/README.md`

- **Windows MCP Agent (runtime public)**: `ANA_MAX/` și `ANA_MAX_GitHub_Release/`
  - Entrypoint MCP: `main.py`, `launcher.py`
  - Public site: `ANA_MAX_GitHub_Release/index.html`
  - Public docs: `ANA_MAX_GitHub_Release/README.md`, `SETUP_AND_RUN.md`

---

## Comenzi esențiale

**Rulare test suite OS v2**
```bash
python -m pytest ana/tests -q
```

**Rulare smoke test OS v2**
```bash
python ana/smoke_test.py
```

**Rulare MCP Agent (legacy)**
```bash
python main.py --test
python main.py --list-tools
```

## Ce s-a schimbat / scopul actualizării

- OS v2 este acum documentat și promovat ca **engine principal** (în `ana/`).
- Windows MCP Agent rămâne disponibil, documentat separat.
- Site-ul public și README-urile au fost sincronizate pentru a reflecta această separare.
- Scop: claritate, stabilitate, reproducibilitate. După această actualizare repo + site rămân „freeze" pe versiunea stabilă OS v2, fără schimbări majore fără aprobarea ta.

## Contribuire și workflow

- Pentru modificări majore: deschide PR, rulează testele OS v2, asigură-te că smoke test-ul trece.
- CI recomandat: rulează `pytest` pentru `ana/tests` și smoke test în pipeline.
