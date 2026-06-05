# ANA_SKILL.md
# ANA MAX OS v2 — Skill Specification

## 1. Context
ANA MAX este un Operating System pentru agenți AI, construit pe principii de:
- control total
- reproducibilitate
- verificabilitate
- disciplină strictă
- execuție deterministă
- tool routing predictibil
- fallback logic
- single-source-of-truth

Acest skill definește blueprint-ul complet pentru implementarea OS v2.

---

## 2. Scop
Implementarea completă a ANA MAX OS v2, incluzând:
- arhitectura de servicii
- orchestratorul central
- event bus
- discipline
- fallback-uri
- tool manager
- sandbox
- error model
- logging
- config system
- test suite

---

## 3. Structură directoare (obligatorie)

ana/
  core/
    orchestrator/
    event_bus/
    scheduler/
    sandbox/
    error_model/
    fallback/
  services/
    fs/
    http/
    shell/
    llm/
  tools/
    registry/
    router/
  config/
    defaults.yaml
    schema.json
  logs/
  tests/
    unit/
    integration/
  docs/
    architecture.md
    os_v2_spec.md
    tool_contracts.md

---

## 4. Componente OS v2

### 4.1 Orchestrator
Responsabil de:
- routing între servicii
- execuție deterministă
- timeouts
- cancellation
- dependency graph
- state machine

### 4.2 Event Bus
- publish/subscribe
- topic-based routing
- queue + replay
- persistence optională

### 4.3 Sandbox
- izolarea toolurilor
- limitare resurse
- execuție sigură
- audit trail

### 4.4 Error Model
- error classes
- recoverable vs fatal
- propagation rules
- structured error packets

### 4.5 Fallback System
- fallback chain
- retry logic
- degrade gracefully
- safe-mode execution

### 4.6 Tool Manager
- registry
- validation
- capability mapping
- routing logic

---

## 5. Discipline OS v2

### 5.1 Determinism
Nicio execuție nu poate produce rezultate diferite cu aceleași inputuri.

### 5.2 Single Source of Truth
Config, state, logs, tool registry — toate centralizate.

### 5.3 Zero Guessing
Nicio decizie nu se ia fără date.

### 5.4 Strict Boundaries
Serviciile nu comunică direct, doar prin orchestrator.

### 5.5 Fail Fast
Erorile se propagă imediat.

### 5.6 Observability
Totul este logat, trasabil, auditat.

---

## 6. Taskuri pentru implementare (A → Z)

### A. Creează structura de directoare
Conform secțiunii 3.

### B. Creează orchestratorul
- state machine
- routing
- timeouts
- cancellation

### C. Creează event bus-ul
- topics
- queue
- replay

### D. Creează sandbox-ul
- execuție izolată
- limitare resurse

### E. Creează error model-ul
- error classes
- propagation rules

### F. Creează fallback system
- fallback chain
- retry logic

### G. Creează tool manager-ul
- registry
- validation
- routing

### H. Creează config system
- defaults.yaml
- schema.json

### I. Creează logging system
- structured logs
- trace IDs

### J. Creează test suite
- unit tests
- integration tests

### K. Creează documentația
- architecture.md
- os_v2_spec.md
- tool_contracts.md

---

## 7. Reguli pentru Codex (obligatorii)

- Nu inventa directoare.
- Nu inventa servicii.
- Nu modifica structura.
- Nu crea fișiere în afara blueprint-ului.
- Nu folosi tooluri nevalidate.
- Respectă ordinea A → Z.
- Fiecare pas trebuie să fie atomic.
- Fiecare fișier trebuie să fie complet funcțional.
- Fiecare componentă trebuie să aibă teste.

---

## 8. Output așteptat
- directoare create
- fișiere generate
- cod complet
- teste
- documentație
- raport final cu tot ce a fost creat
