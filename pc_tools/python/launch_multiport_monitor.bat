@echo off
echo ================================================
echo SAME70-XPLD Multi-Port Communication Monitor
echo ================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo Python found: 
python --version

REM Check if required packages are installed
echo.
echo Checking dependencies...
python -c "import serial, matplotlib, numpy" >nul 2>&1
if errorlevel 1 (
    echo WARNING: Some required packages are missing
    echo Installing required packages...
    echo.
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install packages
        pause
        exit /b 1
    )
)

echo.
echo Dependencies OK!
echo.
echo Starting Multi-Port SAME70-XPLD Communication Monitor...
echo Features:
echo - 6 independent COM port connections
echo - Individual real-time status monitoring
echo - Comparative latency and packet loss charts
echo - Centralized logging with port filtering
echo ================================================
echo.

REM Launch the multi-port GUI application
python same70_multiport_monitor.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo Application exited with error code %errorlevel%
    pause
)