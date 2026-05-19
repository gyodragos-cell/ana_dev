@echo off
echo ========================================
echo   Qoder + ANA MAX JARVIS Setup
echo ========================================
echo.

echo [1/4] Starting ANA MAX MCP Server...
cd /d "c:\Users\billy\Desktop\ana_dev\ANA_MAX"
start "ANA MAX MCP Server" /MIN cmd /c "cd /d c:\Users\billy\Desktop\ana_dev\ANA_MAX && venv\Scripts\python.exe main.py --port 8766"
timeout /t 3 /nobreak >NUL
echo [OK] MCP Server started (port 8766)

echo.
echo [2/4] Configuring MCP for Qoder...
set QODER_MCP=%APPDATA%\Qoder\SharedClientCache\mcp.json
echo {"$schema": "https://opencode.ai/config.json", "mcp": {"ana-max": {"type": "remote", "url": "http://127.0.0.1:8766/mcp", "enabled": true}}} > "%QODER_MCP%"
if exist "%QODER_MCP%" (
    echo [OK] MCP configuration installed
) else (
    echo [ERROR] Failed to create MCP configuration
    pause
    exit /b 1
)

echo.
echo [3/4] Starting ANA Voice...
start "ANA MAX JARVIS Voice" /MIN cmd /c "cd /d c:\Users\billy\Desktop\ana_dev\ANA_MAX && venv\Scripts\python.exe voice_toggle.py"
timeout /t 2 /nobreak >NUL
echo [OK] ANA Voice started

echo.
echo [4/4] Launching Qoder...
tasklist /FI "IMAGENAME eq Qoder.exe" 2>NUL | find /I /N "Qoder.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [INFO] Qoder is already running, skipping launch
) else (
    echo [OK] Starting Qoder...
    start "" "C:\Program Files\Qoder\Qoder.exe"
)

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo AI has EYES and HANDS now!
echo Background: MCP Server + Voice (minimized)
echo.
pause
