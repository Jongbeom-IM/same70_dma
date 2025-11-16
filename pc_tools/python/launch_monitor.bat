@echo off
echo ============================================
echo SAME70-XPLD Communication Monitor Launcher
echo ============================================
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
echo Starting SAME70-XPLD Communication Monitor...
echo ============================================
echo.

REM Launch the GUI application
python same70_gui_monitor.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo Application exited with error code %errorlevel%
    pause
)