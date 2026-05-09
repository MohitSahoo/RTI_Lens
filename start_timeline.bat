@echo off
REM Quick Start Script for Timeline Visualization (Windows)
REM Run this script to set up and launch RTI-Lens with Timeline Visualization

echo.
echo ========================================
echo RTI-Lens Timeline Visualization
echo Quick Start (Windows)
echo ========================================
echo.

REM Check if we're in the right directory
if not exist "streamlit_app.py" (
    echo [ERROR] Please run this script from the IDP directory
    exit /b 1
)

REM Step 1: Install dependencies
echo [1/3] Installing dependencies...
pip install plotly==5.18.0
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install plotly
    exit /b 1
)
echo [OK] Plotly installed
echo.

REM Step 2: Check backend
echo [2/3] Checking backend status...
curl -s http://localhost:8001/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Backend is running on port 8001
) else (
    echo [WARNING] Backend is not running
    echo.
    echo Please start the backend in a separate terminal:
    echo    uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload
    echo.
    pause
)
echo.

REM Step 3: Launch Streamlit
echo [3/3] Launching Streamlit frontend...
echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Quick Guide:
echo   1. Navigate to the Timeline tab
echo   2. Select "Demo: Sample Timeline"
echo   3. Try "Case Timeline" for real data
echo.
echo Opening browser at http://localhost:8501
echo.

streamlit run streamlit_app.py
