@echo off
setlocal
cd /d "%~dp0ANA_MAX"
echo Starting Chat Voice Bridge...
echo Copy text from this chat and the voice bridge will speak it.
echo.
python chat_voice_bridge.py
pause
