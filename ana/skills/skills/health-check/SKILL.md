# Skill: health-check

## Version
1.0.0

## Context
Skill declarativ care verifică starea serviciilor active, a tool-urilor înregistrate,
a fallback-urilor declarative și a disciplinei OS v2.

## Scop
Verifică disponibilitatea și stabilitatea infrastructurii OS v2.

## Structura directoare
- Registry: tool-uri active
- Services: config active
- Event Bus: intrări în journal
- Sandbox: politici active

## Componente OS v2
1. Registry - tool storage
2. EventBus - event streaming
3. Sandbox - execution policy
4. Fallback - recovery mechanism

## Discipline OS v2
- Determinism: verifică că responses sunt deterministe
- Observability: verifică că event-uri sunt publicate
- Single source of truth: verifică că registry e consistent
- Strict boundaries: verifică că sandbox policy e activ
- Fail fast: verifică ca fallbacks sunt registered
- Zero guessing: verifică că nu avem missing tools

## Taskuri pentru implementare
### A. Verifică registry
### B. Verifică services
### C. Verifică fallbacks
### D. Verifică event bus
### E. Verifică sandbox
### F. Colectează stats
### G. Evaluează health
### H. Returnează report
### I. Logează diagnostics
### J. Actualizeaza timestamp
### K. Finalizează

## Reguli pentru Codex
- Report trebuie să includă: ok | degraded | failed
- Details trebuie să listeze fiecare component
- Errors trebuie să fie specifice și actionable

## Output asteptat
```json
{
  "status": "ok",
  "details": {
    "registry": "active",
    "services": ["http", "shell", "llm"],
    "fallbacks": 3,
    "event_bus": "active",
    "sandbox": "active",
    "timestamp": "2026-06-05T..."
  }
}
```
