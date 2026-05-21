@echo off
echo ============================================================
echo ODBC Driver for SQL Server Installer
echo ============================================================
echo.

echo Downloading ODBC Driver 17...
echo.

:: Download using PowerShell
powershell -Command "& {Invoke-WebRequest -Uri 'https://go.microsoft.com/fwlink/?linkid=2249004' -OutFile '%TEMP%\msodbcsql.msi'}"

if exist "%TEMP%\msodbcsql.msi" (
    echo Download complete!
    echo.
    echo Installing...
    echo.
    
    :: Install silently
    msiexec /i "%TEMP%\msodbcsql.msi" /qn IACCEPTMSODBCSQLLICENSETERMS=YES
    
    echo.
    echo Installation complete!
    echo.
    echo Now run: python read_with_localdb.py
    echo.
) else (
    echo Download failed!
    echo.
    echo Please download manually from:
    echo https://go.microsoft.com/fwlink/?linkid=2249004
    echo.
)

pause
