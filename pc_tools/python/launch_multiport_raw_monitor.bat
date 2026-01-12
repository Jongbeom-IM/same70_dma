@echo off
echo ================================================
echo SAME70-XPLD Multi-Port Raw Data Monitor
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
python -c "import serial, tkinter" >nul 2>&1
if errorlevel 1 (
    echo WARNING: Some required packages are missing
    echo Installing required packages...
    echo.
    pip install pyserial
    if errorlevel 1 (
        echo ERROR: Failed to install packages
        pause
        exit /b 1
    )
)

echo.
echo Dependencies OK!
echo.
echo Starting Multi-Port Raw Data Monitor...
echo Features:
echo - 6 independent COM port connections
echo - Real-time RAW data logging (no packet parsing)
echo - Receives ALL bytes without filtering
echo - Per-port filtering in log view
echo - Hex display for all data
echo - Log export functionality
echo ================================================
echo.

REM Launch the multi-port raw monitor GUI application
python same70_multiport_raw_monitor.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo Application exited with error code %errorlevel%
    pause
)
