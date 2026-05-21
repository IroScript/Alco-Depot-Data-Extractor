# Compare MPO codes in Excel vs Database

import pandas as pd
import pyodbc

# Load MPO codes from Excel
MPO_CODES_FILE = r"C:\Users\Irak\Desktop\Barishal April Data\mpo_code.xlsx"
df_excel = pd.read_excel(MPO_CODES_FILE)
excel_codes = set(df_excel.iloc[:, 0].dropna().astype(str).tolist())

print("=" * 70)
print("MPO Code Comparison")
print("=" * 70)

print(f"\nMPO codes in Excel file: {len(excel_codes)}")
print("Sample Excel codes:", list(excel_codes)[:20])

# Get MPO codes from Barishal database
SQL_SERVER = r'.\SQLEXPRESS'
DATABASE_NAME = 'Barishal_DB'

conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SQL_SERVER};DATABASE={DATABASE_NAME};Trusted_Connection=yes;'
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

cursor.execute("""
    SELECT DISTINCT xsp
    FROM opord
    WHERE xsp IS NOT NULL AND xsp != ''
""")

db_codes = set([row[0].strip() for row in cursor.fetchall()])
conn.close()

print(f"\nMPO codes in Barishal database: {len(db_codes)}")
print("Sample DB codes:", list(db_codes)[:20])

# Find matches
matches = excel_codes.intersection(db_codes)
print(f"\n✓ Matching codes: {len(matches)}")
if matches:
    print("  Matches:", list(matches)[:20])

# Find Excel codes not in DB
not_in_db = excel_codes - db_codes
print(f"\n✗ Excel codes NOT in Barishal DB: {len(not_in_db)}")
print("  Sample:", list(not_in_db)[:20])

# Find DB codes not in Excel
not_in_excel = db_codes - excel_codes
print(f"\n✗ DB codes NOT in Excel: {len(not_in_excel)}")
print("  Sample:", list(not_in_excel)[:20])

print("\n" + "=" * 70)
print("Conclusion:")
print("=" * 70)

if len(matches) > 0:
    print(f"✓ Found {len(matches)} matching MPO codes")
    print("  The script should work with these codes")
else:
    print("✗ NO matching MPO codes found!")
    print("  The Excel file might contain codes for different depots")
    print("  Suggestion: Use ALL MPO codes from all databases instead of Excel file")

print("=" * 70)
