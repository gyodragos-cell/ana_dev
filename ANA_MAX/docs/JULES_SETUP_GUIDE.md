# 🚀 ANA MAX + Jules MCP - Setup Quick Guide

## 📋 Ce s-a configurat:

✅ **Jules MCP Server** - `C:\Users\billy\Desktop\jules\jules-mcp-server-main`
✅ **ANA MAX Jules Bridge Tool** - `tools/jules_mcp_bridge.py`
✅ **Startup Script** - `Start_ANA_Jules_System.bat`

## 🔧 Configurare Rapidă:

### 1. Obține Jules API Key:
1. Mergi la: https://jules.google/settings/api
2. Generează o cheie API nouă
3. Copiază cheia

### 2. Configurează Jules MCP:
1. Deschide: `C:\Users\billy\Desktop\jules\jules-mcp-server-main\.env`
2. Înlocuiește linia:
   ```
   JULES_API_KEY=your_jules_api_key_here
   ```
   cu:
   ```
   JULES_API_KEY=cheia_ta_aici
   ```
3. Salvează fișierul

### 3. Conectează Repository-ul GitHub:
1. Mergi la: https://jules.google.com
2. Conectează repository-ul tău (ex: `gyodragos-cell/ANA-MAX`)
3. Instalează GitHub App pe repository

## ▶️ Pornire Sistem:

### Opțiunea 1 - Dublu-click (Recomandat):
```
Double-click: C:\Users\billy\Desktop\ana_dev\ANA_MAX\Start_ANA_Jules_System.bat
```

### Opțiunea 2 - Manual:
```powershell
# Terminal 1 - Jules MCP
cd C:\Users\billy\Desktop\jules\jules-mcp-server-main
node dist\index.js

# Terminal 2 - ANA MAX (alt terminal)
cd C:\Users\billy\Desktop\ana_dev\ANA_MAX
venv\Scripts\python.exe main.py --port 8765
```

## 🎯 Cum Funcționează:

### ANA poate acum să:
1. **Delege task-uri de coding către Jules**
   - "Jules, scrie teste unitare pentru modulul de autentificare"
   - "Jules, fixează bug-ul din funcția X"
   - "Jules, adaugă documentație pentru API"

2. **Monitorizeze progresul**
   - "Care e statusul sesiunii Jules abc123?"
   - "A terminat Jules task-ul?"

3. **Aprobe planuri**
   - "Arată-mi planul lui Jules și aprobă-l"

4. **Programeze task-uri recurente**
   - "Programează Jules să facă update la dependențe fiecare Luni"

## 📝 Exemple de Utilizare:

### Exemplu 1 - Creează Task:
```
User: "ANA, roagă-l pe Jules să scrie teste pentru files.py"

ANA va folosi tool-ul: jules_mcp_bridge
  action: create_task
  prompt: "Write comprehensive unit tests for files.py module"
  source: sources/github/gyodragos-cell/ANA-MAX
```

### Exemplu 2 - Verifică Status:
```
User: "Ce face Jules?"

ANA va folosi tool-ul: jules_mcp_bridge
  action: get_status
  session_id: <session_id>
```

### Exemplu 3 - Aprobă Plan:
```
User: "Arată-mi ce vrea să facă Jules"

ANA va folosi tool-ul: jules_mcp_bridge
  action: manage_session
  session_id: <session_id>
  action_type: approve_plan
```

## 🔍 Tool-uri Jules Disponibile:

| Tool | Descriere |
|------|-----------|
| `create_task` | Creează task de coding nou |
| `manage_session` | Aprobă/respinge planuri, trimite mesaje |
| `get_status` | Verifică status sesiune |
| `schedule_task` | Programează task recurent |
| `list_schedules` | Listează schedule-uri |
| `wait_for_session` | Așteaptă finalizare sesiune |
| `get_activities` | Obține activități sesiune |
| `delete_session` | Șterge sesiune |
| `get_source_details` | Detalii repository |
| `list_sources` | Listează repository-uri conectate |

## ⚙️ Jules MCP Tools Disponibile:

Jules MCP Server expune următoarele tool-uri către ANA:

1. **create_coding_task** - Creează task-uri de coding
2. **create_repoless_task** - Task-uri fără repository
3. **manage_session** - Gestionează sesiuni (approve/reject/message)
4. **get_session_status** - Status sesiune
5. **wait_for_session** - Polling până la finalizare
6. **get_activities_since** - Istoric activități
7. **schedule_recurring_task** - Schedule cu cron
8. **list_schedules** - Listează schedule-uri
9. **delete_schedule** - Șterge schedule
10. **delete_session** - Șterge sesiune
11. **get_source_details** - Detalii repository

## 🎨 Arhitectură:

```
┌─────────────────┐
│   OpenCode AI   │  (Creierul LLM)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    ANA MAX      │  (Body + 57 Tools)
│  MCP Server     │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐  ┌──────────────┐
│  ANA   │  │ Jules MCP    │
│ Tools  │  │ Bridge Tool  │
└────────┘  └──────┬───────┘
                   │
                   ▼
          ┌─────────────────┐
          │ Jules MCP       │
          │ Server (Node.js)│
          └────────┬────────┘
                   │
                   ▼
          ┌─────────────────┐
          │ Jules API       │
          │ (Google Cloud)  │
          └────────┬────────┘
                   │
                   ▼
          ┌─────────────────┐
          │ GitHub PRs      │
          │ Code Changes    │
          └─────────────────┘
```

## 🔒 Securitate:

- ✅ Jules API Key stocat în `.env` (nu în cod)
- ✅ Repository allowlist configurabil
- ✅ Plan approval workflow (human-in-the-loop)
- ✅ Auto-create PR pentru review

## 🐛 Troubleshooting:

### "JULES_API_KEY environment variable is required"
→ Editează `.env` și adaugă cheia ta API

### "Repository not found"
→ Verifică că repository-ul e conectat la Jules pe https://jules.google.com

### Jules MCP nu pornește
→ Rulează `npm run build` în `C:\Users\billy\Desktop\jules\jules-mcp-server-main`

### ANA nu vede tool-ul Jules
→ Verifică că `tools/jules_mcp_bridge.py` există și rulează `python main.py --list-tools`

## 📚 Resurse:

- Jules Docs: https://jules.google/docs/
- Jules MCP Server: https://github.com/savethepolarbears/jules-mcp-server
- ANA MAX Docs: `docs/PROJECT_MAP_AI_GUIDE.md`

---

**Created:** 2026-05-19
**Status:** ✅ Ready to use (configure API key first)
