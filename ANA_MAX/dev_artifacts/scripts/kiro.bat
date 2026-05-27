@echo off
title ANA MAX - MCP Server
color 0A

echo.
echo ====================================================================
echo      A.N.A. MAX - Pornire MCP Server
echo      Tool-uri: 63 ^| Port: 8765 ^| Host: 127.0.0.1
echo ====================================================================
echo.

:: Mergi in folderul proiectului
cd /d "C:\Users\billy\Desktop\ana_dev\ANA_MAX"

:: Verifica daca venv exista
if not exist "venv\Scripts\python.exe" (
    echo [EROARE] Virtual environment nu exista.
    echo Ruleaza: python -m venv venv
    pause
    exit /b 1
)

echo [OK] Proiect gasit
echo [OK] Virtual environment gasit
echo.
echo  Pornesc ANA MAX MCP Server pe http://127.0.0.1:8765
echo  Apasa Ctrl+C pentru a opri serverul.
echo.
echo ====================================================================
echo.

venv\Scripts\python.exe main.py --port 8765

echo.
echo [ANA MAX] Server oprit.
pause
