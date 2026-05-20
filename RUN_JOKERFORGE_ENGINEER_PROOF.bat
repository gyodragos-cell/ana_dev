@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0RUN_JOKERFORGE_ENGINEER_PROOF.ps1"
echo.
pause
