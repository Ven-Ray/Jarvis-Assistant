@echo off
echo Starting Jarvis Voice Assistant...
echo.

REM Check if Python is available
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not found in PATH.
    echo Please install Python and add it to your PATH environment variable.
    pause
    exit /b 1
)

REM Check if LM Studio is running
echo Checking if LM Studio API is available...
curl -s http://localhost:1234/v1 >nul 2>&1
if %errorlevel% neq 0 (
    echo Warning: LM Studio API not found at http://localhost:1234/v1
    echo Make sure LM Studio is running with a model loaded.
    echo.
)

echo Starting Jarvis frontend...
python run_frontend.py

echo.
echo Jarvis assistant has stopped.
pause