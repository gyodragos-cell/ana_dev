---
name: 🚀 Pull Request
about: Template pentru Pull Request-uri
title: ''
labels: ''
assignees: ''
---

## Descriere
Ce modificari ai facut si de ce?

## Tipul Modificarii
- [ ] Bug fix (non-breaking)
- [ ] New feature (non-breaking)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Code refactoring
- [ ] Performance improvement

## Tool-uri Afectate
Listeaza tool-urile modificate:
- [ ] `tools/` 
- [ ] `core/`
- [ ] `main.py`
- [ ] Altele: _____

## Testare
- [ ] Am rulat `python main.py --test` si testele trec
- [ ] Am rulat `python main.py --list-tools` si tool-ul se incarca
- [ ] Am testat manual functionalitatea
- [ ] Am adaugat teste unitare (daca e relevant)

## Checklist
- [ ] Codul urmeaza "The ANA MAX Way" (PROJECT_MAP_AI_GUIDE.md)
- [ ] Fara "zgomot" (log-level DEBUG pentru evenimente recurente)
- [ ] API-uri Native > Subprocesses
- [ ] Nu am spart securitatea (MCP endpoints protejate)
- [ ] Tool-ul e inregistrat in `tools/__init__.py` si `main.py`
- [ ] Am actualizat documentatia (daca e necesar)

## Screenshots (daca e relevant)

## Additional Notes
