@echo off
title AirADB Studio - Android Wireless Debugging Hub
cd /d "%~dp0"

echo ================================================================
echo    Launching AirADB Studio (Android Wireless Debugging Hub)
echo ================================================================

where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python was not found in PATH!
    echo Please install Python 3 or add it to PATH.
    pause
    exit /b 1
)

python server.py
pause
