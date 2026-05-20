# JokerForge PythonAnywhere Demo

Public demo layer for JokerForge.

This folder is safe to upload to PythonAnywhere. It does not contain the local
MCP server, Frida tooling, desktop control, private logs, keys, screenshots, or
workspace files.

## What This Demo Does

- Presents JokerForge as a local-first AI tooling project.
- Explains that the real cockpit runs locally on the Windows machine.
- Provides a small feedback form for teachers, users, and friends.
- Stores feedback in a local SQLite file on PythonAnywhere.

## What This Demo Does Not Do

- It does not run Frida.
- It does not control a desktop.
- It does not access the local PC.
- It does not expose MCP tools publicly.
- It does not collect secrets or API keys.

## PythonAnywhere Setup

1. Upload this folder to PythonAnywhere.
2. Open a Bash console.
3. Go into the folder:

```bash
cd jokerforge_pythonanywhere_demo
```

4. Install requirements if needed:

```bash
pip install --user -r requirements.txt
```

5. In the PythonAnywhere Web tab, create a Flask web app.
6. Set the WSGI file to import `app` from `app.py`.
7. Reload the web app.

## WSGI Example

In the PythonAnywhere WSGI file, use:

```python
import sys
path = "/home/YOUR_USERNAME/jokerforge_pythonanywhere_demo"
if path not in sys.path:
    sys.path.insert(0, path)

from app import app as application
```

Replace `YOUR_USERNAME` with the PythonAnywhere username.

## Privacy Rule

Keep public demo data public-safe. Do not paste passwords, API keys, private
logs, local paths, or personal documents into the feedback form.
