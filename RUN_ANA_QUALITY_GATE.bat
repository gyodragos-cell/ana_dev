@echo off
setlocal

cd /d "%~dp0"

echo ============================================================
echo ANA DEV QUALITY GATE
echo ============================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0RUN_ANA_QUALITY_GATE.ps1"
set EXITCODE=%ERRORLEVEL%

echo.
if "%EXITCODE%"=="0" (
  echo [PASS] ANA quality gate passed.
) else (
  echo [FAIL] ANA quality gate failed.
)

echo.
pause
exit /b %EXITCODE%
