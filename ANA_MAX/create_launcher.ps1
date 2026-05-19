$batPath = "C:\Users\billy\Desktop\ANA_MAX_Launcher\launch.bat"

$batContent = @'
@echo off
echo ========================================
echo   Qoder + ANA MAX JARVIS Setup
echo ========================================
echo.

echo [1/4] Starting ANA MAX MCP Server...
cd /d "c:\Users\billy\Desktop\ana_dev\ANA_MAX"
start "ANA MAX MCP Server" /MIN cmd /c "cd /d c:\Users\billy\Desktop\ana_dev\ANA_MAX && venv\Scripts\python.exe main.py --port 8765"
timeout /t 3 /nobreak >NUL
echo [OK] MCP Server started (port 8765)

echo.
echo [2/4] Configuring MCP for Qoder...
set QODER_MCP=%APPDATA%\Qoder\SharedClientCache\mcp.json
echo {"$schema": "https://opencode.ai/config.json", "mcp": {"ana-max": {"type": "remote", "url": "http://127.0.0.1:8765/mcp", "enabled": true}}} > "%QODER_MCP%"
if exist "%QODER_MCP%" (
    echo [OK] MCP configuration installed
) else (
    echo [ERROR] Failed to create MCP configuration
    pause
    exit /b 1
)

echo.
echo [3/4] Starting ANA Voice...
start "ANA MAX JARVIS Voice" /MIN cmd /c "cd /d c:\Users\billy\Desktop\ana_dev\ANA_MAX && venv\Scripts\pythonw.exe voice_toggle.py"
timeout /t 2 /nobreak >NUL
echo [OK] ANA Voice started

echo.
echo [4/4] Launching Qoder...
echo ========================================
echo   Qoder with ANA Voice + MCP
echo   All Tools: ENABLED
echo ========================================
echo.
start "" "C:\Program Files\Qoder\Qoder.exe"

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo AI has EYES and HANDS now!
echo Background: MCP Server + Voice (minimized)
echo.
pause
'@

if (Test-Path $batPath) {
    Remove-Item $batPath -Force
}

$batContent | Out-File -FilePath $batPath -Encoding ASCII
Write-Host "[OK] Script created: $batPath" -ForegroundColor Green
