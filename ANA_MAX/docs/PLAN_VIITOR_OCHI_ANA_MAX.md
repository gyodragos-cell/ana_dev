# Plan de Viitor: "Ochi" Sistematici pentru ANA MAX

## Obiectiv Principal
Inlocuirea sistemului vizual bazat pe OCR (Tesseract) cu **Microsoft UI Automation (UIA)** prin intermediul librariei `pywinauto`. Aceasta schimbare ii va oferi lui ANA o intelegere nativa, semantica si perfecta a intregului mediu desktop Windows (similar modului in care un browser proceseaza DOM-ul HTML), reducand erorile vizuale la zero.

## 1. Limitari ale Solutiei Actuale (OCR + Screenshots)
- **Viteza scazuta:** Generarea de capturi de ecran si trecerea lor prin Tesseract dureaza mult si pune presiune pe I/O.
- **Fiabilitate redusa:** Rezolutia ecranului, culorile fondului sau anti-aliasing-ul pot face textele indescifrabile pentru OCR ("I" vs "1", "O" vs "0").
- **Lipsa de Context Structural:** OCR-ul stie *unde* e textul, dar nu stie ce *rol* are acel text (daca e un buton, o bara de titlu, o lista derulanta etc.).

## 2. Abordarea Viitoare: Microsoft UI Automation (UIA)
Microsoft UIA expune o harta completa a absolut tuturor elementelor grafice desenate pe ecran.
Pentru ANA MAX, vom crea un bridge special (ex: `windows_uia_bridge.py`):
1. **Citire Nativa:** ANA va interoga direct API-ul sistemului pentru a citi interfata:
   - Ex: *Aplicatia "Chrome" -> Fereastra Principala -> Meniul "File" -> Butonul "Save"*
2. **Interactiune ("Maini" Precise):** In loc sa emita click-uri "oarbe" pe coordonate (X,Y) estimate de OCR, ANA va cere direct OS-ului: *"Apasa elementul `submit_btn`"*.
3. **Imunitate Vizuala:** Daca un element isi schimba pozitia pe ecran, fereastra este mutata sau tema (Dark/Light Mode) este schimbata, ANA il va gasi instant pe baza ID-ului si numelui sau structural.

## 3. Status Actual (v0.2.0 - 2026-05-15)

### ✅ Ce s-a realizat deja:
- **pywinauto** este deja instalat si functional
- **windows_uia_bridge.py** a fost creat si este FREE
- **UI Automation** functioneaza pentru aplicatii Windows (Calculator, Notepad, etc.)
- **desktop_capture** este FREE (Vision AI activat)
- **OCR cu PaddleOCR** este activat si functional
- **56 MCP Tools** sunt disponibile (43 Free + 4 Premium + 9 AI Core)

### 🔧 Ce mai trebuie facut (Next Tasks):
- [ ] **Etapa 2:** Imbunatatirea `windows_uia_bridge.py` pentru a genera rapid arborele UIA al aplicatiei din foreground
- [ ] **Etapa 3:** Crearea de "Actiuni Nemaivazute" (Click pe nume, Selectare meniu, Introducere text exact) apelabile direct din interfata MCP / `execute_task`
- [ ] **Etapa 4:** Integrarea completa cu `windows_deep_sight.py` pentru o vedere completa "Deasupra si Sub Capota"

## 4. Roadmap Viitor (v0.3.0+)

### 🎯 Obiective pe termen lung:
1. **UIA Avansat:**
   - Scanare UIA in timp real pentru toate aplicatiile deschise
   - Arbore UIA complet exportat ca JSON pentru AI
   - Actiuni precise bazate pe nume/rol, nu pe coordonate

2. **Vision AI Imbunatatit:**
   - OCR mai rapid cu PaddleOCR optimizat
   - Detectie automata a tipului de element (buton, text, imagine)
   - Intelegere semantica a interfetei

3. **Automatizare Completa:**
   - AI-ul sa poata executa task-uri complexe pe orice aplicatie Windows
   - Fara interventie umana pentru click-uri sau tastare
   - Rezistenta la schimbari de UI (teme, rezolutii, pozitii)

Acest sistem combinat va da agentului ANA capacitatea de a executa task-uri desktop de o complexitate masiva, cu viteza la care executa astazi scripturi de consola.
