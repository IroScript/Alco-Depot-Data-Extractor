import os
import pyodbc

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main():
    server = r'.\SQLEXPRESS'
    db_name = 'TEST_BARISHAL_COMPAT_DB'
    barishal_data = os.path.join(PROJECT_DIR, 'All_Depots', 'BARISHAL', 'Data')
    mdf_path = os.path.join(barishal_data, 'ERPonTheNet_Data.MDF')
    ldf_path = os.path.join(barishal_data, 'ERPonTheNet_log.LDF')
    
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
        
        # Check compatibility level
        cursor.execute(f"SELECT name, compatibility_level FROM sys.databases WHERE name = '{db_name}'")
        row = cursor.fetchone()
        if row:
            print(f"Database: {row[0]}, Compatibility Level: {row[1]}")
            
        # Detach
        print("Detaching...")
        cursor.execute(f"ALTER DATABASE [{db_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
        cursor.execute(f"EXEC sp_detach_db '{db_name}', 'true'")
        print("Detached successfully!")
        
        conn.close()
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    main()
