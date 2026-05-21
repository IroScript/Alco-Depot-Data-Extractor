@echo off
echo ============================================================
echo SQL Server 2008 R2 Express Downloader
echo ============================================================
echo.

echo SQL Server 2008 R2 Express হলো:
echo - Free এবং lightweight
echo - Windows 10/11 supported
echo - SQL Server 2000 database পড়তে পারে
echo - Management Studio included
echo.

echo ============================================================
echo Download Options:
echo ============================================================
echo.
echo 1. SQL Server 2008 R2 Express with Tools (Recommended)
echo    Size: ~250 MB
echo    Includes: Database Engine + Management Studio
echo.
echo 2. SQL Server 2008 R2 Express with Advanced Services
echo    Size: ~600 MB
echo    Includes: Everything + Full-Text Search + Reporting
echo.

set /p choice="আপনার পছন্দ (1 or 2): "

if "%choice%"=="1" (
    echo.
    echo Downloading SQL Server 2008 R2 Express with Tools...
    echo.
    
    set URL=https://download.microsoft.com/download/0/4/B/04BE03CD-EAF3-4797-9D8D-2E08E316C998/SQLEXPRWT_x64_ENU.exe
    set OUTPUT=%TEMP%\SQLEXPRWT_x64_ENU.exe
    
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%URL%' -OutFile '%OUTPUT%'}"
    
    if exist "%OUTPUT%" (
        echo.
        echo Download complete!
        echo.
        echo Starting installer...
        echo.
        start "" "%OUTPUT%"
        
        echo.
        echo ============================================================
        echo Installation Tips:
        echo ============================================================
        echo 1. Select "New installation"
        echo 2. Accept license terms
        echo 3. Install all features (Database Engine + Management Tools)
        echo 4. Instance name: SQLEXPRESS (default)
        echo 5. Authentication: Windows Authentication
        echo 6. Wait 15-20 minutes for installation
        echo.
        echo After installation, run: python read_with_sql2005.py
        echo ============================================================
    ) else (
        echo.
        echo Download failed!
        echo.
        echo Please download manually from:
        echo https://www.microsoft.com/en-us/download/details.aspx?id=30438
    )
    
) else if "%choice%"=="2" (
    echo.
    echo Downloading SQL Server 2008 R2 Express with Advanced Services...
    echo.
    
    set URL=https://download.microsoft.com/download/0/4/B/04BE03CD-EAF3-4797-9D8D-2E08E316C998/SQLEXPRADV_x64_ENU.exe
    set OUTPUT=%TEMP%\SQLEXPRADV_x64_ENU.exe
    
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%URL%' -OutFile '%OUTPUT%'}"
    
    if exist "%OUTPUT%" (
        echo.
        echo Download complete!
        echo.
        echo Starting installer...
        echo.
        start "" "%OUTPUT%"
        
        echo.
        echo ============================================================
        echo Installation Tips:
        echo ============================================================
        echo 1. Select "New installation"
        echo 2. Accept license terms
        echo 3. Install all features
        echo 4. Instance name: SQLEXPRESS (default)
        echo 5. Authentication: Windows Authentication
        echo 6. Wait 20-30 minutes for installation
        echo.
        echo After installation, run: python read_with_sql2005.py
        echo ============================================================
    ) else (
        echo.
        echo Download failed!
        echo.
        echo Please download manually from:
        echo https://www.microsoft.com/en-us/download/details.aspx?id=30438
    )
    
) else (
    echo.
    echo Invalid choice!
)

echo.
pause
