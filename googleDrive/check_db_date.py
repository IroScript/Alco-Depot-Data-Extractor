import os
import pyodbc
import pandas as pd
import subprocess

def grant_sql_server_permissions(folder_path):
    try:
        accounts = [
            'NT SERVICE\\MSSQL$SQLEXPRESS',
            'NT SERVICE\\MSSQLSERVER',
            'NT AUTHORITY\\NETWORK SERVICE',
            'NT AUTHORITY\\SYSTEM'
        ]
        for account in accounts:
            try:
                cmd = f'icacls "{folder_path}" /grant "{account}:(OI)(CI)F" /T /Q'
                subprocess.run(cmd, shell=True, capture_output=True, timeout=10)
            except:
                pass
    except Exception as e:
        print(f"Warning: Permissions check failed: {e}")

def main():
    server = r'.\SQLEXPRESS'
    db_name = 'TEMP_TEST_DATE_DB'
    mdf_path = r'c:\Users\Irak\Desktop\Barishal April Data\Barishal_Temp\Data\ERPonTheNet_Data.MDF'
    ldf_path = r'c:\Users\Irak\Desktop\Barishal April Data\Barishal_Temp\Data\ERPonTheNet_log.LDF'
    
    if not os.path.exists(mdf_path):
        print(f"File not found: {mdf_path}")
        return
        
    mdf_path = os.path.normpath(mdf_path)
    ldf_path = os.path.normpath(ldf_path)
    
    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE=master;Trusted_Connection=yes;'
    try:
        conn = pyodbc.connect(conn_str)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database already exists, if so drop/detach it
        cursor.execute(f"SELECT database_id FROM sys.databases WHERE name = '{db_name}'")
        row = cursor.fetchone()
        if row:
            print("Database already exists, detaching...")
            try:
                cursor.execute(f"ALTER DATABASE [{db_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
                cursor.execute(f"EXEC sp_detach_db '{db_name}', 'true'")
            except Exception as e:
                print(f"Error detaching: {e}")
                
        # Grant permissions to SQL Server service account
        grant_sql_server_permissions(os.path.dirname(mdf_path))
        
        # Attach database
        print(f"Attaching {db_name}...")
        attach_query = f"""
        CREATE DATABASE [{db_name}] ON 
        (FILENAME = N'{mdf_path}'),
        (FILENAME = N'{ldf_path}')
        FOR ATTACH;
        """
        cursor.execute(attach_query)
        print("Attached successfully!")
        
        # Query columns from opord
        print("\nColumns in opord:")
        cursor.execute(f"SELECT COLUMN_NAME, DATA_TYPE FROM [{db_name}].INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'opord'")
        for col in cursor.fetchall():
            if 'date' in col[0].lower() or 'time' in col[0].lower():
                print(f"  * {col[0]} ({col[1]})")
            else:
                print(f"    {col[0]} ({col[1]})")
                
        # Get sample date values
        print("\nSample records from opord (first 5 rows with date columns):")
        query = f"SELECT TOP 5 xordernum, xdate, xsaledate FROM [{db_name}].dbo.opord"
        df = pd.read_sql(query, conn)
        print(df.to_string())
        
        # Detach
        print("\nDetaching database...")
        cursor.execute(f"ALTER DATABASE [{db_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
        cursor.execute(f"EXEC sp_detach_db '{db_name}', 'true'")
        print("Detached successfully!")
        
        conn.close()
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    main()
