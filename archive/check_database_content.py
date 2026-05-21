# Check what's in the Barishal database

import pyodbc
import pandas as pd

SQL_SERVER = r'.\SQLEXPRESS'
DATABASE_NAME = 'Barishal_DB'

conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SQL_SERVER};DATABASE={DATABASE_NAME};Trusted_Connection=yes;'
conn = pyodbc.connect(conn_str)

print("=" * 70)
print(f"Checking Database: {DATABASE_NAME}")
print("=" * 70)

# Check if opord table exists
print("\n1. Checking if 'opord' table exists...")
cursor = conn.cursor()
cursor.execute("""
    SELECT TABLE_NAME 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_TYPE = 'BASE TABLE'
    ORDER BY TABLE_NAME
""")
tables = [row[0] for row in cursor.fetchall()]
print(f"   Found {len(tables)} tables")

if 'opord' in tables:
    print("   ✓ 'opord' table EXISTS")
    
    # Check row count
    cursor.execute("SELECT COUNT(*) FROM opord")
    count = cursor.fetchone()[0]
    print(f"   Total rows in opord: {count:,}")
    
    # Check if xsp column exists and has data
    print("\n2. Checking 'xsp' column (MPO codes)...")
    cursor.execute("""
        SELECT TOP 20 xsp, COUNT(*) as count
        FROM opord
        WHERE xsp IS NOT NULL AND xsp != ''
        GROUP BY xsp
        ORDER BY COUNT(*) DESC
    """)
    
    print("   Top 20 MPO codes in database:")
    for row in cursor.fetchall():
        print(f"     {row[0]}: {row[1]} records")
    
    # Check sample data
    print("\n3. Sample data from opord table:")
    df = pd.read_sql("SELECT TOP 5 * FROM opord", conn)
    print(df.to_string())
    
else:
    print("   ✗ 'opord' table NOT FOUND")
    print(f"\n   Available tables:")
    for table in tables[:20]:
        print(f"     - {table}")

conn.close()

print("\n" + "=" * 70)
print("Done!")
print("=" * 70)
