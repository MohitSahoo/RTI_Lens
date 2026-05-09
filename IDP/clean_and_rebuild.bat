@echo off
REM Complete cleanup and rebuild script
REM Step 1: Clean all databases
REM Step 2: Rebuild from JSONL

echo.
echo ========================================
echo RTI-Lens: Clean and Rebuild
echo ========================================
echo.
echo This will:
echo   1. Clean PostgreSQL database
echo   2. Clean MongoDB collections
echo   3. Delete all files (markdown, trees, indexes)
echo   4. Rebuild everything from JSONL
echo.
echo Total time: 30-60 minutes
echo.

pause

cd "C:\Users\WIN11\Downloads\IDP 2\IDP"

echo.
echo ========================================
echo STEP 1: Cleaning Databases
echo ========================================
echo.

python cleanup_all_databases.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Cleanup failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo STEP 2: Rebuilding from JSONL
echo ========================================
echo.

python rebuild_from_jsonl.py

echo.
echo ========================================
echo Complete!
echo ========================================
echo.

pause
