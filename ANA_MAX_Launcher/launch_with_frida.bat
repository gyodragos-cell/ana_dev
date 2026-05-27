@echo off
echo ========================================
echo   ANA MAX JARVIS - FRIDA MONITORING
echo ========================================
echo.
set ANA_DIR=c:\Users\billy\Desktop\ana_dev\ANA_MAX
set MCP_URL=http://127.0.0.1:8766/mcp
set READINESS=%~dp0mcp_readiness_check.py

REM === STEP 0: FRIDA Process Snapshot BEFORE launch ===
echo [FRIDA] Taking process snapshot BEFORE launch...
cd /d "%ANA_DIR%"
start "FRIDA Process Monitor" /MIN cmd /c "echo FRIDA LIVE MONITOR - Watching for new processes... && venv\Scripts\python.exe dev_artifacts\diagnostics\frida_monitor_live.py"
timeout /t 2 /nobreak >NUL
echo [OK] FRIDA Monitor started

echo.
echo [1/4] Starting ANA MAX MCP Server...
start "ANA MAX MCP Server" /MIN cmd /k "cd /d ""%ANA_DIR%"" && venv\Scripts\python.exe -u main.py --host 127.0.0.1 --port 8766"
timeout /t 8 /nobreak >NUL
echo [OK] MCP Server started (port 8766)
if exist "%READINESS%" (
    "%ANA_DIR%\venv\Scripts\python.exe" "%READINESS%" --mcp-url "%MCP_URL%" --timeout 20
    if errorlevel 1 (
        echo [ERROR] MCP smart readiness failed.
        pause
        exit /b 1
    )
)

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
echo [4/4] Taking AFTER launch screenshot with Desktop Vision...
start "Vision Check" /MIN cmd /c "cd /d c:\Users\billy\Desktop\ana_dev\ANA_MAX && venv\Scripts\python.exe dev_artifacts\diagnostics\vision_check_launch.py"
timeout /t 3 /nobreak >NUL
echo [OK] Vision check started

echo.
echo [5/5] Launching Qoder...
tasklist /FI "IMAGENAME eq Qoder.exe" 2>NUL | find /I /N "Qoder.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [INFO] Qoder is already running, skipping launch
) else (
    echo [OK] Starting Qoder...
    start "" "C:\Program Files\Qoder\Qoder.exe"
)

echo.
echo ========================================
echo   Setup Complete with FRIDA Monitoring!
echo ========================================
echo.
echo AI has EYES (Desktop Vision) and HANDS (FRIDA) now!
echo Background processes:
echo   1. MCP Server (port 8766)
echo      Smart readiness: tool_router + agent_coach recommend checked
echo   2. Voice Toggle (Microsoft Zira)
echo   3. FRIDA Process Monitor (LIVE)
echo   4. Vision Check (Screenshot analysis)
echo.
pause
