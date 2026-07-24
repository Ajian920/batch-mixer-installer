@echo off
cd /d "%~dp0"

python --version >nul 2>&1
if %errorlevel% neq 0 (
    start "" "Åú»ì¼ô¹¤×÷ÊÒ.exe"
    exit /b
)

python app.py
if %errorlevel% neq 0 (
    echo.
    echo Error.
    pause
)
