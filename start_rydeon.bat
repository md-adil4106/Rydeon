@echo off
title Rydeon - Vehicle Rental System
color 0B

cd /d "%~dp0"

echo ======================================================================
echo           RYDEON - PREMIUM VEHICLE RENTAL PLATFORM
echo ======================================================================
echo.

:: 1. Detect Python virtual environment
if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
) else if exist "%~dp0venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo [1/3] Using Python: %PYTHON_EXE%

:: 2. Ensure environment configuration exists
if not exist "%~dp0.env" (
    echo [!] Warning: .env file not found. Copying from .env.example...
    if exist "%~dp0.env.example" (
        copy "%~dp0.env.example" "%~dp0.env" >nul
        echo [OK] Created .env with default local settings.
    )
)

:: 3. Launch the web browser after a 2-second delay
echo [2/3] Launching web browser at http://127.0.0.1:5000/ ...
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:5000/"

:: 4. Information Banner
echo [3/3] Starting Rydeon Web Application Server...
echo.
echo ======================================================================
echo   APPLICATION URL:  http://127.0.0.1:5000/
echo.
echo   DEMO CREDENTIALS:
echo   ------------------------------------------------------------------
echo   [Admin]     Email: admin@rydeon-rentals.com
echo               Pass:  AdminSecret2026!
echo.
echo   [Customer]  Email: alexander.wright@example.com
echo               Pass:  CustomerSecret2026!
echo ======================================================================
echo.
echo Press [Ctrl + C] anytime to shut down the server.
echo.

"%PYTHON_EXE%" run.py

if errorlevel 1 (
    echo.
    echo ======================================================================
    echo [ERROR] The server exited with an error code.
    echo Please verify that MySQL service is running on port 3306.
    echo ======================================================================
    pause
)
