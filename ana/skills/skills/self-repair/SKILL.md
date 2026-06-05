# Skill: self-repair

## Version
1.0.0

type: system
status: stable

## Capability
self.repair

## Context
Skill declarativ care descrie modul în care ANA MAX OS v2 detectează și remediază problemele
runtime prin ajustări de configurare, fallback și reguli declarative.

## Scop
Permite OS v2 să recunoască degradări, să aplice patch-uri sigure și să învețe din
execuții anterioare pentru a evita aceleași erori.

## Structura directoare
- Diagnostics: evenimente și erori colectate
- Repair plan: propuneri de patch-uri
- Learned rules: actualizări persistente
- Execution: aplicarea și verificarea patch-urilor

## Componente OS v2
1. EventBus - colectare de erori și telemetrie
2. CooperationEngine - orchestrare self-repair
3. Registry - verificare tool-uri și capabilități
4. Fallback - reutilizare de canale de backup
5. ConfigLoader - aplicare patch-uri

## Discipline OS v2
- Determinism: patch-urile trebuie să fie sigure și reproductibile
- Observability: trebuie să fie jurnalizate toate deciziile
- Single source of truth: learned_rules.yaml este sursa adevărului pentru reguli
- Strict boundaries: nu se modifică date externe direct
- Fail fast: dacă reparația e imposibilă, se oprește și raportează
- Zero guessing: nu se face ghicire fără date certe

## Taskuri pentru implementare
### A. Colectează diagnostice
### B. Analizează tiparele de eroare
### C. Identifică reguli și skill-uri relevante
### D. Propune patch-uri declarative
### E. Aplică patch-urile sigure
### F. Verifică efectul modificărilor
### G. Scrie learnings în learned_rules.yaml
### H. Raportează status
### I. Trigger self-repair dacă este necesar
### J. Documentează deciziile
### K. Închide procesul

## Reguli pentru Codex
- Output trebuie să fie clar, structurat și corect pentru diagnostice
- Nu se pot aplica modificări fără un plan validat
- Trebuie să includă steps, status și learnings

## Output asteptat
```json
{
  "status": "patched",
  "details": "Applied self-repair patch based on diagnostic analysis.",
  "learnings": [
    {
      "rule": "llm.complete.retry=2",
      "reason": "recoverable failure pattern"
    }
  ]
}
```

## Summary
Skill declarativ care descrie modul în care ANA MAX OS v2 detectează probleme,
analizează cauze, aplică patch-uri, actualizează configurări și învață din
execuțiile anterioare folosind CooperationEngine și SelfRepairEngine.

## Intent
Acest skill este folosit automat de CooperationEngine atunci când:
- apare o eroare repetitivă
- fallback-urile sunt declanșate prea des
- un tool sau un serviciu devine inconsistent
- configurarea nu mai reflectă realitatea runtime
- lipsesc skill-uri declarative sau reguli declarative

## Preconditions
- CooperationEngine este activ
- SelfRepairEngine este disponibil în cooperation.py
- learned_rules.yaml este accesibil pentru citire/scriere
- fallback engine este funcțional
- event bus publică evenimentele de tip error/failure

## Steps
1. **Collect Diagnostics**
   - citește evenimentele recente din EventBus
   - extrage erorile din ErrorPacket
   - identifică pattern-uri (repetiții, degradări, timeouts)

2. **Analyze**
   - clasifică problemele: recoverable / non-recoverable / transient / structural
   - verifică dacă există reguli declarative pentru aceste cazuri
   - verifică dacă există skill-uri declarative relevante
   - verifică dacă fallback-urile sunt configurate corect

3. **Generate Patch**
   - propune ajustări pentru:
     - fallback rules
     - skills.yaml
     - discipline enforcement
     - config (services active, limits, boundaries)
   - generează patch-uri în format declarativ

4. **Apply Patch**
   - scrie patch-urile în learned_rules.yaml
   - notifică CooperationEngine că patch-ul a fost aplicat
   - actualizează runtime-ul dacă patch-ul este safe

5. **Verify**
   - rulează un health-check intern
   - verifică dacă problema a dispărut
   - dacă nu, marchează patch-ul ca „ineficient”

## Fallbacks
- dacă SelfRepairEngine nu poate aplica patch-ul → returnează status=deferred
- dacă learned_rules.yaml nu poate fi scris → returnează status=blocked
- dacă analiza nu găsește nimic → returnează status=noop

## Output
- status: ok | noop | patched | deferred | blocked
- details: descrierea acțiunilor efectuate
- learnings: lista regulilor noi salvate

## Example Output
status: patched
details: "Updated fallback rules for llm.complete after repeated recoverable failures."
learnings:
  - rule: "llm.complete.retry=2"
    reason: "pattern: recoverable failure x3"
