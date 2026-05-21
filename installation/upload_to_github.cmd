@echo off
echo ============================================================
echo GitHub Upload Script
echo ============================================================
echo.

echo Checking if Git is installed...
git --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo Git is not installed!
    echo.
    echo Please install Git from: https://git-scm.com/download/win
    echo.
    echo Or use GitHub Desktop: https://desktop.github.com/
    echo.
    pause
    exit /b 1
)

echo Git is installed!
echo.

echo Initializing repository...
git init

echo.
echo Adding files...
git add .

echo.
echo Committing...
git commit -m "Initial commit - Data extraction tools for legacy ERP"

echo.
echo Adding remote...
git remote add origin https://github.com/IroScript/Alco-Depot-Data-Extractor.git

echo.
echo Setting branch to main...
git branch -M main

echo.
echo Pushing to GitHub...
git push -u origin main

echo.
echo ============================================================
echo Upload Complete!
echo ============================================================
echo.
echo Your repository is now live at:
echo https://github.com/IroScript/Alco-Depot-Data-Extractor
echo.

pause
