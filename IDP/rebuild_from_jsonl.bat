@echo off
REM Complete Rebuild Script for Windows
REM Rebuilds everything from clean_cases_final_balanced.jsonl

echo.
echo ========================================
echo RTI-Lens Complete Rebuild
echo ========================================
echo.
echo This will:
echo   1. Process JSONL file (900 cases)
echo   2. Create markdown files
echo   3. Populate MongoDB
echo   4. Build PageIndex trees
echo   5. Build BM25 index
echo   6. Build vector embeddings
echo.
echo Estimated time: 30-60 minutes
echo.

pause

cd "C:\Users\WIN11\Downloads\IDP 2\IDP"
python rebuild_from_jsonl.py

echo.
echo ========================================
echo Rebuild Complete
echo ========================================
echo.

pause
