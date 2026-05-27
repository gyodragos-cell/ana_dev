# ANA MAX Dev Artifacts

Acest folder tine fisierele de test, demo, diagnostic si media generate in
timpul lucrului. Ele au fost mutate aici ca radacina proiectului sa ramana
curata si usor de inteles.

## Foldere

- `tests/` - teste manuale, smoke checks si experimente `test_*.py`.
- `demos/` - demo-uri si prototipuri de interactiune.
- `diagnostics/` - scripturi manuale pentru verificari, Frida, voice, vision,
  procese si debugging.
- `media/` - imagini generate/capturate in demo-uri.
- `reports/` - rezervat pentru artefacte de raportare locale.

## Regula

Fisierele din acest folder sunt utile ca istoric, dar nu sunt parte din calea
principala de rulare. Nu le importa din `main.py` si nu baza launcher-ul
principal pe ele decat daca le promovezi inapoi in codul principal.
