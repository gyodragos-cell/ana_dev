@echo off
SETLOCAL EnableExtensions

set "REPO_DIR=C:\Users\billy\Desktop\ana_dev"
set "ANA_DIR=%REPO_DIR%\ANA_MAX"
set "PY=%ANA_DIR%\venv\Scripts\python.exe"
set "GATE=%ANA_DIR%\dev_artifacts\scripts\no_reload_quality_gate.py"

echo.
echo ========================================
echo   ANA MAX - NO-RELOAD QUALITY GATE
echo ========================================
echo.
echo This check does not install extensions, reload IDEs, or close chat windows.
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

if not exist "%GATE%" (
    echo [ERROR] No-reload quality gate script not found:
    echo         %GATE%
    pause
    exit /b 1
)

echo [RUN] %GATE%
pushd "%REPO_DIR%"
"%PY%" "%GATE%"
set "GATE_EXIT=%ERRORLEVEL%"
popd

echo.
if "%GATE_EXIT%"=="0" (
    echo [OK] No-reload quality gate passed.
) else (
    echo [ERROR] No-reload quality gate failed with exit code %GATE_EXIT%.
)
echo.
pause
exit /b %GATE_EXIT%
