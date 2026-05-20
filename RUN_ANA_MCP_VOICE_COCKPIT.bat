@echo off
setlocal

set "ROOT=%~dp0"
set "ANA=%ROOT%ANA_MAX"
set "MCP_HOST=127.0.0.1"
set "MCP_PORT=8765"
set "MCP_URL=http://%MCP_HOST%:%MCP_PORT%/mcp"
set "INFO=%ANA%\ANA_MCP_CONNECTION_INFO.txt"

cd /d "%ANA%"

echo ============================================================
echo ARHITECTURA NEURO AVANSATA - MCP + VOICE COCKPIT
echo ============================================================
echo.
echo This starts:
echo   1. Arhitectura Neuro Avansata MCP HTTP server
echo   2. Chat voice bridge
echo   3. Desktop vision diagnostic
echo.
echo MCP URL:
echo   %MCP_URL%
echo.

(
  echo ARHITECTURA NEURO AVANSATA MCP CONNECTION INFO
  echo ===========================
  echo MCP HTTP URL: %MCP_URL%
  echo Health URL:   http://%MCP_HOST%:%MCP_PORT%/health
  echo Tools URL:    http://%MCP_HOST%:%MCP_PORT%/tools
  echo.
  echo For MCP clients that support HTTP/SSE, use:
  echo %MCP_URL%
  echo.
  echo Voice:
  echo Keep RUN_CHAT_VOICE_BRIDGE window open.
  echo Copy text from chat to hear it.
  echo.
  echo Vision:
  echo RUN_DESKTOP_VISION_DIAG checks if this Windows session allows screenshots.
) > "%INFO%"

echo Starting MCP server window...
start "Arhitectura Neuro Avansata MCP Server :8765" cmd /k "cd /d ""%ANA%"" && python main.py --host %MCP_HOST% --port %MCP_PORT%"

timeout /t 3 /nobreak >nul

echo Starting Chat Voice Bridge window...
start "Arhitectura Neuro Avansata Chat Voice Bridge" cmd /k "cd /d ""%ANA%"" && python chat_voice_bridge.py"

timeout /t 2 /nobreak >nul

echo Starting Desktop Vision Diagnostic window...
start "Arhitectura Neuro Avansata Desktop Vision Diagnostic" cmd /k "cd /d ""%ANA%"" && python desktop_vision_diag.py"

echo.
echo ============================================================
echo COCKPIT STARTED
echo ============================================================
echo MCP URL: %MCP_URL%
echo Info file: %INFO%
echo.
echo What to do now:
echo   - Keep the MCP server window open.
echo   - Keep the voice bridge window open.
echo   - Copy text from chat if you want the voice bridge to speak it.
echo   - After the vision diagnostic ends, tell Codex: gata.
echo.
echo Note:
echo Codex itself cannot auto-attach to a new MCP server from this BAT,
echo but any MCP-compatible client can use the URL above.
echo ============================================================
echo.
pause
