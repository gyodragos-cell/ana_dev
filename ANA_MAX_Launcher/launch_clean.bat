@echo off
echo ========================================
echo   ANA MAX JARVIS - CLEAN LAUNCH
echo ========================================
echo.

set "ANA_DIR=C:\Users\billy\Desktop\ana_dev\ANA_MAX"
set "PY=%ANA_DIR%\venv\Scripts\python.exe"
set "PORT=8766"
set "MCP_URL=http://127.0.0.1:%PORT%/mcp"
set "READINESS=%~dp0mcp_readiness_check.py"

REM Stop only processes listening on the MCP port to avoid duplicate servers.
echo [CLEANUP] Stopping existing MCP listener on port %PORT%...
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":%PORT% .*LISTENING"') do taskkill /F /PID %%P >NUL 2>&1
timeout /t 2 /nobreak >NUL
echo [OK] Clean slate ready

echo.
echo [1/3] Starting ANA MAX MCP Server (minimized)...
start "MCP" /MIN cmd /k "cd /d ""%ANA_DIR%"" && venv\Scripts\python.exe -u main.py --host 127.0.0.1 --port %PORT%"
timeout /t 8 /nobreak >NUL
echo [OK] MCP Server started (port 8766)
if exist "%READINESS%" (
    "%PY%" "%READINESS%" --mcp-url "%MCP_URL%" --timeout 20
    if errorlevel 1 (
        echo [ERROR] MCP smart readiness failed.
        pause
        exit /b 1
    )
)

echo.
echo [2/3] Starting ANA Voice (minimized)...
start "Voice" /MIN cmd /c "cd /d c:\Users\billy\Desktop\ana_dev\ANA_MAX && venv\Scripts\python.exe voice_toggle.py"
timeout /t 2 /nobreak >NUL
echo [OK] ANA Voice started

echo.
echo [3/3] Launching Qoder...
tasklist /FI "IMAGENAME eq Qoder.exe" 2>NUL | find /I /N "Qoder.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [INFO] Qoder is already running
) else (
    echo [OK] Starting Qoder...
    start "" "C:\Program Files\Qoder\Qoder.exe"
)

echo.
echo ========================================
echo   LAUNCH COMPLETE!
echo ========================================
echo.
echo Background processes (minimized):
echo   1. MCP Server (port 8766) - 84 tools expected, smart readiness checked
echo   2. Voice Toggle (Microsoft Zira)
echo.
echo Use Qoder to interact with ANA MAX tools!
echo.
pause
