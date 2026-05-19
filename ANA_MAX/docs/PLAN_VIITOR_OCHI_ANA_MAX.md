# Plan de Viitor: "Ochi" Sistematici pentru ANA MAX

## Obiectiv Principal
Înlocuirea sistemului vizual bazat pe OCR (Tesseract) cu **Microsoft UI Automation (UIA)** prin intermediul librăriei `pywinauto`. Această schimbare îi va oferi lui ANA o înțelegere nativă, semantică și perfectă a întregului mediu desktop Windows (similar modului în care un browser procesează DOM-ul HTML), reducând erorile vizuale la zero.

## 1. Limitări ale Soluției Actuale (OCR + Screenshots)
- **Viteză scăzută:** Generarea de capturi de ecran și trecerea lor prin Tesseract durează mult și pune presiune pe I/O.
- **Fiabilitate redusă:** Rezoluția ecranului, culorile fondului sau anti-aliasing-ul pot face textele indescifrabile pentru OCR ("I" vs "1", "O" vs "0").
- **Lipsă de Context Structural:** OCR-ul știe *unde* e textul, dar nu știe ce *rol* are acel text (dacă e un buton, o bară de titlu, o listă derulantă etc.).

## 2. Abordarea Viitoare: Microsoft UI Automation (UIA)
Microsoft UIA expune o hartă completă a absolut tuturor elementelor grafice desenate pe ecran.
Pentru ANA MAX, vom crea un bridge special (ex: `windows_uia_bridge.py`):
1. **Citire Nativă:** ANA va interoga direct API-ul sistemului pentru a citi interfața:
   - Ex: *Aplicația "Chrome" -> Fereastra Principală -> Meniul "File" -> Butonul "Save"*
2. **Interacțiune ("Mâini" Precise):** În loc să emită click-uri "oarbe" pe coordonate (X,Y) estimate de OCR, ANA va cere direct OS-ului: *"Apasă elementul `submit_btn`"*.
3. **Imunitate Vizuală:** Dacă un element își schimbă poziția pe ecran, fereastra este mutată sau tema (Dark/Light Mode) este schimbată, ANA îl va găsi instant pe baza ID-ului și numelui său structural.

## 3. Status Actual (v0.2.0 - 2026-05-15)

### ✅ Ce s-a realizat deja:
- **pywinauto** este deja instalat și funcțional
- **windows_uia_bridge.py** a fost creat și este FREE
- **UI Automation** funcționează pentru aplicații Windows (Calculator, Notepad, etc.)
- **desktop_capture** este FREE (Vision AI activat)
- **OCR cu PaddleOCR** este activat și funcțional
- **56 MCP Tools** sunt disponibile (43 Free + 4 Premium + 9 AI Core)

### 🔧 Ce mai trebuie făcut (Next Tasks):
- [ ] **Etapa 2:** Îmbunătățirea `windows_uia_bridge.py` pentru a genera rapid arborele UIA al aplicației din foreground
- [ ] **Etapa 3:** Crearea de "Acțiuni Nemaivăzute" (Click pe nume, Selectare meniu, Introducere text exact) apelabile direct din interfața MCP / `execute_task`
- [ ] **Etapa 4:** Integrarea completă cu `windows_deep_sight.py` pentru o vedere completă "Deasupra și Sub Capotă"

## 4. Roadmap Viitor (v0.3.0+)

### 🎯 Obiective pe termen lung:
1. **UIA Avansat:**
   - Scanare UIA în timp real pentru toate aplicațiile deschise
   - Arbore UIA complet exportat ca JSON pentru AI
   - Acțiuni precise bazate pe nume/rol, nu pe coordonate

2. **Vision AI Îmbunătățit:**
   - OCR mai rapid cu PaddleOCR optimizat
   - Detecție automată a tipului de element (buton, text, imagine)
   - Înțelegere semantică a interfeței

3. **Automatizare Completă:**
   - AI-ul să poată executa task-uri complexe pe orice aplicație Windows
   - Fără intervenție umană pentru click-uri sau tastare
   - Rezistență la schimbări de UI (teme, rezoluții, poziții)

Acest sistem combinat va da agentului ANA capacitatea de a executa task-uri desktop de o complexitate masivă, cu viteza la care execută astăzi scripturi de consolă.
