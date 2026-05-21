# Detach all depot databases to start fresh

import pyodbc

SQL_SERVER = r'.\SQLEXPRESS'

# Connect to master
conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SQL_SERVER};DATABASE=master;Trusted_Connection=yes;'
conn = pyodbc.connect(conn_str)
conn.autocommit = True
cursor = conn.cursor()

print("=" * 70)
print("Detaching All Depot Databases")
print("=" * 70)

# Get all databases ending with _DB
cursor.execute("""
    SELECT name FROM sys.databases 
    WHERE name LIKE '%_DB'
    AND name NOT IN ('master', 'tempdb', 'model', 'msdb')
""")

databases = [row[0] for row in cursor.fetchall()]

print(f"\nFound {len(databases)} depot databases to detach:")
for db in databases:
    print(f"  - {db}")

# Detach each database
for db_name in databases:
    try:
        # Kill all connections first
        cursor.execute(f"""
            ALTER DATABASE [{db_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
        """)
        
        # Detach
        cursor.execute(f"EXEC sp_detach_db '{db_name}'")
        print(f"  ✓ Detached: {db_name}")
    except Exception as e:
        print(f"  ✗ Error detaching {db_name}: {e}")

conn.close()

print("\n" + "=" * 70)
print("Done!")
print("=" * 70)
