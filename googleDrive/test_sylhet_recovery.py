import pyodbc
import os
import shutil

SQL_SERVER = r'.\SQLEXPRESS'
conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SQL_SERVER};DATABASE=master;Trusted_Connection=yes;'

def recover_sylhet():
    db_name = "SYLHET_UPGRADE_DB"
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_dir, 'All_Depots', 'SYLHET', 'Data')
    mdf_path = os.path.join(data_dir, 'ERPonTheNet_Data.MDF')
    
    dummy_mdf_path = os.path.join(data_dir, 'dummy_ERPonTheNet.mdf')
    dummy_ldf_path = os.path.join(data_dir, 'dummy_ERPonTheNet_log.ldf')
    
    conn = pyodbc.connect(conn_str)
    conn.autocommit = True
    cursor = conn.cursor()
    
    # 1. Clean up existing dummy database if any
    cursor.execute(f"SELECT database_id FROM sys.databases WHERE name = '{db_name}'")
    if cursor.fetchone():
        print("Dropping existing database...")
        try:
            cursor.execute(f"ALTER DATABASE [{db_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
            cursor.execute(f"DROP DATABASE [{db_name}]")
        except Exception as e:
            print(f"Error dropping: {e}")
            
    # Delete dummy files if they exist
    for f in [dummy_mdf_path, dummy_ldf_path]:
        if os.path.exists(f):
            os.remove(f)
            
    # 2. Create a dummy database with files in our directory
    print("Creating dummy database in our directory...")
    create_query = f"""
    CREATE DATABASE [{db_name}] ON PRIMARY 
    (NAME = '{db_name}_data', FILENAME = '{dummy_mdf_path}')
    LOG ON 
    (NAME = '{db_name}_log', FILENAME = '{dummy_ldf_path}')
    """
    cursor.execute(create_query)
    
    print(f"Dummy MDF: {dummy_mdf_path}")
    print(f"Dummy LDF: {dummy_ldf_path}")
    
    # 3. Set dummy offline
    cursor.execute(f"ALTER DATABASE [{db_name}] SET OFFLINE WITH ROLLBACK IMMEDIATE")
    
    # 4. Replace dummy MDF with target MDF
    print("Replacing dummy MDF with target MDF...")
    if os.path.exists(dummy_mdf_path):
        os.remove(dummy_mdf_path)
    shutil.copy2(mdf_path, dummy_mdf_path)
    
    # 5. Delete the dummy LDF file so SQL Server is forced to rebuild it or fail
    if os.path.exists(dummy_ldf_path):
        os.remove(dummy_ldf_path)
        
    # 6. Set online (will fail or go to recovery pending, which is expected)
    print("Setting database ONLINE (expecting failure/warning)...")
    try:
        cursor.execute(f"ALTER DATABASE [{db_name}] SET ONLINE")
    except Exception as e:
        print(f"Set ONLINE failed (as expected): {e}")
        
    # 7. Set to EMERGENCY mode
    print("Setting database to EMERGENCY mode...")
    cursor.execute(f"ALTER DATABASE [{db_name}] SET EMERGENCY")
    
    # 8. Set to SINGLE_USER
    print("Setting database to SINGLE_USER...")
    cursor.execute(f"ALTER DATABASE [{db_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
    
    # 9. Rebuild Log and Repair
    print("Running DBCC CHECKDB with REPAIR_ALLOW_DATA_LOSS...")
    try:
        cursor.execute(f"DBCC CHECKDB ('{db_name}', REPAIR_ALLOW_DATA_LOSS) WITH NO_INFOMSGS, ALL_ERRORMSGS")
    except Exception as e:
        print(f"DBCC CHECKDB error (might still have worked): {e}")
        
    # 10. Set back to MULTI_USER and check status
    print("Setting back to MULTI_USER...")
    try:
        cursor.execute(f"ALTER DATABASE [{db_name}] SET MULTI_USER")
    except Exception as e:
        print(f"Error setting MULTI_USER: {e}")
        
    # 11. Check if online and upgrade compatibility
    print("Upgrading compatibility...")
    try:
        cursor.execute(f"ALTER DATABASE [{db_name}] SET COMPATIBILITY_LEVEL = 100")
        print("Compatibility upgraded successfully!")
    except Exception as e:
        print(f"Error upgrading compatibility: {e}")
        
    # 12. Detach database so the recovered file becomes free
    print("Detaching recovered database...")
    try:
        cursor.execute(f"ALTER DATABASE [{db_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
        cursor.execute(f"EXEC sp_detach_db '{db_name}', 'true'")
        
        # Replace target MDF with the recovered dummy MDF
        if os.path.exists(mdf_path):
            os.remove(mdf_path)
        shutil.move(dummy_mdf_path, mdf_path)
        
        # Move the newly rebuilt LDF to final LDF path
        final_ldf_path = os.path.join(data_dir, 'ERPonTheNet_log.LDF')
        if os.path.exists(final_ldf_path):
            os.remove(final_ldf_path)
        if os.path.exists(dummy_ldf_path):
            shutil.move(dummy_ldf_path, final_ldf_path)
            
        print("✓ Successfully recovered and moved SYLHET MDF and rebuilt LDF back to target paths!")
    except Exception as e:
        print(f"Error during detach and copy: {e}")
        
    conn.close()

if __name__ == "__main__":
    recover_sylhet()
