@echo off
REM Quick cleanup script for Windows
REM Cleans MongoDB and PageIndex trees

echo.
echo ========================================
echo RTI-Lens Data Cleanup
echo ========================================
echo.
echo This will delete:
echo   - All MongoDB documents
echo   - All PageIndex tree files
echo   - BM25 index file
echo.
echo Schema and structure will be kept intact.
echo.

pause

python cleanup_data.py

pause
