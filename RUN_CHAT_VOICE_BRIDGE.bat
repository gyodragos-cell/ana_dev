@echo off
setlocal
cd /d "%~dp0ANA_MAX"
echo Starting ANA MAX Chat Voice Bridge...
echo Copy text from this chat and ANA will speak it.
echo.
python chat_voice_bridge.py
pause
