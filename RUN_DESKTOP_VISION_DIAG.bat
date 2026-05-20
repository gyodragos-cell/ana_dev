@echo off
setlocal
cd /d "%~dp0ANA_MAX"
echo Starting Desktop Vision Diagnostic...
echo Run this by double-clicking from your normal Windows desktop session.
echo.
python desktop_vision_diag.py
pause
