@echo off
cd /d "%~dp0"
python german_daily.py
if %errorlevel% neq 0 (
    echo.
    echo Script failed. Press any key to exit...
    pause >nul
)
