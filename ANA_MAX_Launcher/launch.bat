@echo off
SETLOCAL EnableExtensions EnableDelayedExpansion

set "ANA_DIR=C:\Users\billy\Desktop\ana_dev\ANA_MAX"
set "PY=%ANA_DIR%\venv\Scripts\python.exe"
set "PORT=8766"
set "HOST=127.0.0.1"
set "MCP_URL=http://%HOST%:%PORT%/mcp"
set "HEALTH_URL=http://%HOST%:%PORT%/health"
set "QODER_MCP=%APPDATA%\Qoder\SharedClientCache\mcp.json"
set "WATCHDOG=%~dp0live_watchdog.py"
set "READINESS=%~dp0mcp_readiness_check.py"

echo.
echo ========================================
echo   ANA MAX JARVIS - UNIFIED LAUNCHER
echo ========================================
echo.

if not exist "%ANA_DIR%\main.py" (
    echo [ERROR] ANA MAX main.py not found:
    echo         %ANA_DIR%\main.py
    pause
    exit /b 1
)

if not exist "%PY%" (
    echo [ERROR] Python venv not found:
    echo         %PY%
    pause
    exit /b 1
)

echo [0/7] Configuring Qoder MCP on port %PORT%...
if not exist "%APPDATA%\Qoder\SharedClientCache" mkdir "%APPDATA%\Qoder\SharedClientCache" >NUL 2>&1
>"%QODER_MCP%" echo {"$schema":"https://opencode.ai/config.json","mcp":{"ana-max":{"type":"remote","url":"%MCP_URL%","enabled":true}}}
if errorlevel 1 (
    echo [ERROR] Could not write Qoder MCP config:
    echo         %QODER_MCP%
    pause
    exit /b 1
)
echo [OK] Qoder MCP config: %MCP_URL%

echo.
echo [1/7] Checking existing MCP server...
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $h = Invoke-RestMethod -Uri '%HEALTH_URL%' -TimeoutSec 2; if ($h.status -eq 'online') { exit 0 } else { exit 2 } } catch { exit 1 }"
if "%ERRORLEVEL%"=="0" (
    echo [OK] MCP server already online on port %PORT%
) else (
    echo [INFO] Starting MCP Server on port %PORT%...
    start "MCP Server" /MIN cmd /k "pushd ""%ANA_DIR%"" && venv\Scripts\python.exe main.py --port %PORT%"
    call :WAIT_HEALTH
    if errorlevel 1 (
        echo [ERROR] MCP server did not become healthy.
        echo         Check the MCP Server window and %ANA_DIR%\logs\ana_max.log
        pause
        exit /b 1
    )
)

echo.
echo [2/7] Verifying loaded tools and smart routing...
for /f "usebackq delims=" %%A in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "$body=@{jsonrpc='2.0';id=1;method='tools/list';params=@{}} | ConvertTo-Json -Depth 5; $r=Invoke-RestMethod -Uri '%MCP_URL%' -Method Post -Body $body -ContentType 'application/json' -TimeoutSec 10; $r.result.tools.Count"`) do set "TOOLS_COUNT=%%A"
if not defined TOOLS_COUNT (
    echo [ERROR] Could not read MCP tools/list.
    pause
    exit /b 1
)
echo [OK] MCP tools loaded: !TOOLS_COUNT!
if exist "%READINESS%" (
    "%PY%" "%READINESS%" --mcp-url "%MCP_URL%" --timeout 20
    if errorlevel 1 (
        echo [ERROR] MCP smart readiness failed.
        echo         Expected tool_router and agent_coach action=recommend to work.
        pause
        exit /b 1
    )
) else (
    echo [WARN] Smart readiness checker missing: %READINESS%
)

echo.
echo [3/7] Checking desktop eyes...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$body=@{jsonrpc='2.0';id=2;method='tools/call';params=@{name='desktop_capture';arguments=@{operation='capture'}}} | ConvertTo-Json -Depth 8; $r=Invoke-RestMethod -Uri '%MCP_URL%' -Method Post -Body $body -ContentType 'application/json' -TimeoutSec 15; $t=$r.result.content[0].text | ConvertFrom-Json; if ($t.success) { Write-Host '[OK] desktop_capture works:' $t.data.file; exit 0 } else { Write-Host '[ERROR] desktop_capture failed:' $t.error; exit 1 }"
if errorlevel 1 (
    pause
    exit /b 1
)

echo.
echo [4/7] Checking Frida...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$body=@{jsonrpc='2.0';id=3;method='tools/call';params=@{name='frida_instrument';arguments=@{operation='version';confirm=$true}}} | ConvertTo-Json -Depth 8; $r=Invoke-RestMethod -Uri '%MCP_URL%' -Method Post -Body $body -ContentType 'application/json' -TimeoutSec 15; $t=$r.result.content[0].text | ConvertFrom-Json; if ($t.success) { Write-Host '[OK] Frida works:' $t.data.version; exit 0 } else { Write-Host '[WARN] Frida not ready:' $t.message $t.error; exit 2 }"
if errorlevel 2 (
    echo [WARN] Continuing without Frida. Install/fix frida-tools if needed.
)

echo.
echo [5/7] Starting live debug console...
start "DEBUG CONSOLE" cmd /k "pushd ""%ANA_DIR%"" && venv\Scripts\python.exe tools\live_debug_console.py"
echo [OK] Debug console opened

echo.
echo [6/7] Starting watchdog and Frida monitor...
if exist "%WATCHDOG%" (
    start "WATCHDOG FRIDA" cmd /k "title WATCHDOG FRIDA && pushd ""%ANA_DIR%"" && venv\Scripts\python.exe ""%WATCHDOG%"""
    echo [OK] Watchdog/Frida monitor opened
) else if exist "%ANA_DIR%\frida_monitor_live.py" (
    start "FRIDA LIVE MONITOR" /MIN cmd /k "pushd ""%ANA_DIR%"" && venv\Scripts\python.exe frida_monitor_live.py"
    echo [OK] Fallback Frida live monitor opened
) else (
    echo [WARN] No watchdog or Frida monitor found, skipped
)

echo.
echo [7/7] Starting chat voice bridge and Qoder...
start "CHAT VOICE BRIDGE" /MIN cmd /k "pushd ""%ANA_DIR%"" && python.exe chat_voice_bridge.py --poll 0.7"

tasklist /FI "IMAGENAME eq Qoder.exe" 2>NUL | find /I "Qoder.exe" >NUL
if "%ERRORLEVEL%"=="0" (
    echo [OK] Qoder is already running
) else (
    start "" "C:\Program Files\Qoder\Qoder.exe"
    echo [OK] Qoder launched
)

echo.
echo ========================================
echo   ANA MAX JARVIS - READY
echo ========================================
echo MCP:       %MCP_URL%
echo Health:    %HEALTH_URL%
echo Tools:     !TOOLS_COUNT!
echo Logs:      %ANA_DIR%\logs\ana_max.log
echo.
echo Live windows:
echo   - MCP Server
echo   - DEBUG CONSOLE
echo   - WATCHDOG FRIDA
echo   - CHAT VOICE BRIDGE
echo   - Qoder
echo.
pause
exit /b 0

:WAIT_HEALTH
for /L %%I in (1,1,30) do (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $h = Invoke-RestMethod -Uri '%HEALTH_URL%' -TimeoutSec 2; if ($h.status -eq 'online') { exit 0 } else { exit 2 } } catch { exit 1 }"
    if "!ERRORLEVEL!"=="0" (
        echo [OK] MCP health check passed
        exit /b 0
    )
    timeout /t 1 /nobreak >NUL
)
exit /b 1
