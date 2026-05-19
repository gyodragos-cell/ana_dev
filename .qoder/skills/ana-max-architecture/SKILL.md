---
name: ana-max-architecture
description: Arhitectura oficială și Ghidul de Dezvoltare "The ANA MAX Way". Trigger-uiește automat atunci când ești rugat să modifici arhitectura, să adaugi un tool nou sau să depanezi sistemul ANA MAX. Respectă regulile de performanță, zero zgomot și securitate absolută.
---

# ANA MAX - Arhitectura și Regulile de Dezvoltare

Acest skill te ghidează cum să scrii cod pentru proiectul ANA MAX fără să-i distrugi performanța sau "liniștea" (fără zgomot inutil).

## 1. Regulile de Aur (The ANA MAX Way)

1. **🚫 Fără "Zgomot" (Silent System):**
   - NICIODATĂ nu printa sau loga cu `INFO` evenimente care se repetă (ex. verificări la fiecare secundă de loop, fișiere modificate, procese noi). Acestea aparțin nivelului `DEBUG`.
   - `INFO` este DOAR pentru porniri de sistem și acțiuni declanșate direct de utilizator.

2. **⚡ Native Python Libraries > PowerShell:**
   - Când extragi procese, memorie sau detalii sistem, **NU** folosi `subprocess.run(["powershell"...])`. Asta provoacă un overhead masiv și încetinește întregul PC.
   - **SOLUȚIA:** Folosește `import psutil`. Este de 100x mai rapid și nu creează procese în fundal.
   - Pentru interfață (GUI), folosește `pywinauto` (Microsoft UI Automation).
   - Pentru injectare și analiză "Under the Hood", folosește `frida`.

3. **🔒 Conexiuni Persistente și Securitate:**
   - Nu deschide baza de date SQLite (`memory.py`) la fiecare secundă. Folosește conexiuni de tip Singleton protejate cu `threading.Lock()`.
   - Serverul MCP (`mcp_server.py`) trebuie mereu să verifice un API Key (Bearer Token) ca să protejeze sistemul de "God Mode". Orice modificare adusă trebuie să mențină `auth_header != f"Bearer {api_key}"`.

## 2. Harta Proiectului

Când lucrezi la fișiere, iată exact structura:
- `core/`: Logica de bază (`agent.py`, `memory.py`, `mcp_server.py`). Nu adăuga tools aici.
- `tools/`: Aici stau toate capabilitățile. Când adaugi un tool, extinde clasa `Tool` (din `tools.base`) și nu uita să adaugi metoda `get_definition(self)`.
- **Cum înregistrezi un tool:** Întotdeauna importă-l în `tools/__init__.py` și adaugă-l într-una din listele de înregistrare din `main.py` (`desktop_tools`, `new_tools` etc.).

## 3. Workflow-ul Corect pentru tine (Agentul)
Când ți se cere o funcționalitate nouă:
1. Creează fișierul curat în `tools/`.
2. Asigură-te că include `ToolDefinition`.
3. Evită total polling-ul agresiv prin `.bat`/`powershell`.
4. După ce ai scris codul, înregistrează-l în `main.py`.
5. Rulează `python main.py --test` prin terminal înainte să te oprești.
