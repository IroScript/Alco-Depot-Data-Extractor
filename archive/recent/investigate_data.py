# Investigate database for returns, cancellations, and data quality issues

import pyodbc
import pandas as pd

SQL_SERVER = r'.\SQLEXPRESS'
DATABASE_NAME = 'Barishal_DB'

conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SQL_SERVER};DATABASE={DATABASE_NAME};Trusted_Connection=yes;'
conn = pyodbc.connect(conn_str)

print("=" * 80)
print("DATABASE INVESTIGATION - Returns, Cancellations, and Data Quality")
print("=" * 80)

# 1. Check opord table structure
print("\n1. OPORD TABLE STRUCTURE")
print("-" * 80)
cursor = conn.cursor()
cursor.execute("""
    SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'opord'
    ORDER BY ORDINAL_POSITION
""")
print("Columns in opord table:")
for row in cursor.fetchall():
    print(f"  {row[0]:20} {row[1]:15} {str(row[2]) if row[2] else ''}")

# 2. Check for status/cancelled/return indicators
print("\n2. ORDER STATUS ANALYSIS")
print("-" * 80)
cursor.execute("""
    SELECT 
        xstatusord AS Status,
        COUNT(*) AS Count,
        SUM(xtotamt) AS Total_Amount
    FROM opord
    GROUP BY xstatusord
    ORDER BY COUNT(*) DESC
""")
print("Order Status Distribution:")
for row in cursor.fetchall():
    print(f"  {str(row[0]):20} Count: {row[1]:6,}  Amount: {row[2]:15,.2f}")

# 3. Check for negative quantities (returns)
print("\n3. NEGATIVE QUANTITIES (RETURNS)")
print("-" * 80)
cursor.execute("""
    SELECT 
        COUNT(*) AS Negative_Qty_Records,
        SUM(CASE WHEN xqtyord < 0 THEN 1 ELSE 0 END) AS Negative_Count,
        MIN(xqtyord) AS Min_Qty,
        MAX(xqtyord) AS Max_Qty
    FROM opodt
""")
row = cursor.fetchone()
print(f"  Total records in opodt: {row[0]:,}")
print(f"  Records with negative qty: {row[1]:,}")
print(f"  Min quantity: {row[2]}")
print(f"  Max quantity: {row[3]}")

# 4. Check for negative amounts (returns/credits)
print("\n4. NEGATIVE AMOUNTS (RETURNS/CREDITS)")
print("-" * 80)
cursor.execute("""
    SELECT 
        COUNT(*) AS Total_Records,
        SUM(CASE WHEN xlineamt < 0 THEN 1 ELSE 0 END) AS Negative_Amount_Count,
        SUM(CASE WHEN xlineamt < 0 THEN xlineamt ELSE 0 END) AS Total_Negative_Amount,
        MIN(xlineamt) AS Min_Amount,
        MAX(xlineamt) AS Max_Amount
    FROM opodt
""")
row = cursor.fetchone()
print(f"  Total records: {row[0]:,}")
print(f"  Records with negative amount: {row[1]:,}")
print(f"  Total negative amount: {row[2]:,.2f}")
print(f"  Min amount: {row[3]:,.2f}")
print(f"  Max amount: {row[4]:,.2f}")

# 5. Sample negative quantity records
print("\n5. SAMPLE NEGATIVE QUANTITY RECORDS (RETURNS)")
print("-" * 80)
df_negative = pd.read_sql("""
    SELECT TOP 10
        o.xordernum AS Invoice_No,
        o.xdate AS Invoice_Date,
        o.xstatusord AS Status,
        od.xitem AS Product_Code,
        od.xqtyord AS Quantity,
        od.xprice AS Unit_Price,
        od.xlineamt AS Line_Amount,
        o.xtotamt AS Total_Amount
    FROM opord o
    JOIN opodt od ON o.xordernum = od.xordernum
    WHERE od.xqtyord < 0
    ORDER BY od.xqtyord ASC
""", conn)

if len(df_negative) > 0:
    print(df_negative.to_string(index=False))
else:
    print("  No negative quantity records found")

# 6. Check for cancelled orders
print("\n6. CANCELLED/REJECTED ORDERS")
print("-" * 80)
cursor.execute("""
    SELECT 
        xstatusord AS Status,
        COUNT(*) AS Count
    FROM opord
    WHERE xstatusord LIKE '%cancel%' 
       OR xstatusord LIKE '%reject%'
       OR xstatusord LIKE '%void%'
    GROUP BY xstatusord
""")
cancelled = cursor.fetchall()
if cancelled:
    for row in cancelled:
        print(f"  {row[0]:20} Count: {row[1]:,}")
else:
    print("  No explicitly cancelled orders found")

# 7. Check opodt table structure
print("\n7. OPODT TABLE STRUCTURE")
print("-" * 80)
cursor.execute("""
    SELECT COLUMN_NAME, DATA_TYPE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'opodt'
    ORDER BY ORDINAL_POSITION
""")
print("Columns in opodt table:")
for row in cursor.fetchall():
    print(f"  {row[0]:20} {row[1]}")

# 8. Check for return-related tables
print("\n8. CHECKING FOR RETURN-RELATED TABLES")
print("-" * 80)
cursor.execute("""
    SELECT TABLE_NAME
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_TYPE = 'BASE TABLE'
    AND (TABLE_NAME LIKE '%return%' 
         OR TABLE_NAME LIKE '%credit%'
         OR TABLE_NAME LIKE '%refund%')
    ORDER BY TABLE_NAME
""")
return_tables = cursor.fetchall()
if return_tables:
    print("Found return-related tables:")
    for row in return_tables:
        print(f"  - {row[0]}")
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {row[0]}")
        count = cursor.fetchone()[0]
        print(f"    Records: {count:,}")
else:
    print("  No return-related tables found")

# 9. Check invoice number patterns (returns might have different prefixes)
print("\n9. INVOICE NUMBER PATTERNS")
print("-" * 80)
cursor.execute("""
    SELECT 
        LEFT(xordernum, 3) AS Prefix,
        COUNT(*) AS Count,
        MIN(xdate) AS First_Date,
        MAX(xdate) AS Last_Date
    FROM opord
    GROUP BY LEFT(xordernum, 3)
    ORDER BY COUNT(*) DESC
""")
print("Invoice prefixes:")
for row in cursor.fetchall():
    print(f"  {row[0]:10} Count: {row[1]:6,}  From: {row[2]}  To: {row[3]}")

# 10. Check for zero or null amounts
print("\n10. ZERO OR NULL AMOUNTS")
print("-" * 80)
cursor.execute("""
    SELECT 
        COUNT(*) AS Total_Records,
        SUM(CASE WHEN xlineamt = 0 THEN 1 ELSE 0 END) AS Zero_Amount,
        SUM(CASE WHEN xlineamt IS NULL THEN 1 ELSE 0 END) AS Null_Amount
    FROM opodt
""")
row = cursor.fetchone()
print(f"  Total records: {row[0]:,}")
print(f"  Zero amount records: {row[1]:,}")
print(f"  Null amount records: {row[2]:,}")

conn.close()

print("\n" + "=" * 80)
print("INVESTIGATION COMPLETE")
print("=" * 80)
