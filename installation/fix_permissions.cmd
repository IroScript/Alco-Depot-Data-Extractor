@echo off
echo ============================================================
echo SQL Server File Permissions Fixer
echo ============================================================
echo.

echo Granting SQL Server access to MDF files...
echo.

:: Grant full control to SQL Server service account
icacls "c:\Users\Irak\Desktop\Barishal April Data\Data" /grant "NT SERVICE\MSSQL$SQLEXPRESS:(OI)(CI)F" /T

:: Also grant to current user
icacls "c:\Users\Irak\Desktop\Barishal April Data\Data" /grant "%USERNAME%:(OI)(CI)F" /T

:: Grant to NETWORK SERVICE (backup)
icacls "c:\Users\Irak\Desktop\Barishal April Data\Data" /grant "NETWORK SERVICE:(OI)(CI)F" /T

echo.
echo ============================================================
echo Permissions updated!
echo ============================================================
echo.
echo Now run: python read_with_sql2005.py
echo.

pause
