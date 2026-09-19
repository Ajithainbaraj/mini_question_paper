@echo off
echo ========================================
echo Restarting Flask App with Fresh Code
echo ========================================

REM Kill all Python processes
echo Stopping any running Python processes...
taskkill /F /IM python.exe /T 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✓ Stopped running Python processes
) else (
    echo ✓ No Python processes were running
)

REM Wait a moment
timeout /t 2 /nobreak >nul

REM Clear Python cache
echo Clearing Python cache...
if exist __pycache__ (
    rmdir /s /q __pycache__
    echo ✓ Cleared __pycache__
)
if exist question_generator.pyc (
    del /f /q question_generator.pyc
    echo ✓ Cleared .pyc files
)

echo.
echo ========================================
echo Starting Flask App...
echo ========================================
echo.

REM Start the app without bytecode caching
python -B app.py

pause
