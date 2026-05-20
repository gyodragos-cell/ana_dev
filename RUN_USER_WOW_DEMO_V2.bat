@echo off
setlocal
title ANA MAX - User Wow Demo V2 (Improved)
mode con: cols=118 lines=34
color 0B
cd /d "%~dp0"

echo ================================================================
echo ANA MAX - USER WOW DEMO (IMPROVED VERSION)
echo ================================================================
echo.
echo What this proves:
echo A text-only AI can talk about a window.
echo ANA MAX with tools can change authorized live runtime behavior.
echo.
echo INSTRUCTIONS FOR RECORDING:
echo 1. Start your screen recording NOW
echo 2. Position this terminal on the LEFT side of screen
echo 3. Leave RIGHT side empty for the MessageBox window
echo 4. Press any key to start the demo
echo.
echo This is a local white-hat demo target.
echo No third-party app is touched.
echo.
pause >nul

python user_wow_frida_demo_v2.py

echo.
echo ================================================================
echo END OF ANA MAX USER WOW DEMO
echo ================================================================
echo.
echo If you saw a window that said:
echo   "AFTER: ANA MAX Runtime Control"
echo Then the demo worked perfectly!
echo.
echo This proves ANA MAX can intercept and modify live Windows processes.
echo.
pause
endlocal
