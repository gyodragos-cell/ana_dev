@echo off
setlocal

cd /d "%~dp0"

echo ============================================================
echo PROJECT QUALITY GATE
echo ============================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0RUN_ANA_QUALITY_GATE.ps1"
set EXITCODE=%ERRORLEVEL%

echo.
if "%EXITCODE%"=="0" (
  echo [PASS] Project quality gate passed.
) else (
  echo [FAIL] Project quality gate failed.
)

echo.
pause
exit /b %EXITCODE%
