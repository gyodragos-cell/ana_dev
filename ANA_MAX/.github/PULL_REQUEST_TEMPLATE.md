---
name: 🚀 Pull Request
about: Template pentru Pull Request-uri
title: ''
labels: ''
assignees: ''
---

## Descriere
Ce modificări ai făcut și de ce?

## Tipul Modificării
- [ ] Bug fix (non-breaking)
- [ ] New feature (non-breaking)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Code refactoring
- [ ] Performance improvement

## Tool-uri Afectate
Listează tool-urile modificate:
- [ ] `tools/` 
- [ ] `core/`
- [ ] `main.py`
- [ ] Altele: _____

## Testare
- [ ] Am rulat `python main.py --test` și testele trec
- [ ] Am rulat `python main.py --list-tools` și tool-ul se încarcă
- [ ] Am testat manual funcționalitatea
- [ ] Am adăugat teste unitare (dacă e relevant)

## Checklist
- [ ] Codul urmează "The ANA MAX Way" (PROJECT_MAP_AI_GUIDE.md)
- [ ] Fără "zgomot" (log-level DEBUG pentru evenimente recurente)
- [ ] API-uri Native > Subprocesses
- [ ] Nu am spart securitatea (MCP endpoints protejate)
- [ ] Tool-ul e înregistrat în `tools/__init__.py` și `main.py`
- [ ] Am actualizat documentația (dacă e necesar)

## Screenshots (dacă e relevant)

## Additional Notes
