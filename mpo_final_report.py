# Final MPO-wise Complete Sales Report

import pyodbc
import pandas as pd
from datetime import datetime
import os

# Configuration
MPO_CODES_FILE = r"C:\Users\Irak\Desktop\Barishal April Data\mpo_code.xlsx"
SQL_SERVER = r'.\SQLEXPRESS'
DATABASE_NAME = 'ERPonTheNet'

def load_mpo_codes():
    """Load MPO codes from Excel file if exists"""
    if os.path.exists(MPO_CODES_FILE):
        try:
            df = pd.read_excel(MPO_CODES_FILE)
            mpo_codes = df.iloc[:, 0].dropna().astype(str).tolist()
            print(f"Loaded {len(mpo_codes)} MPO codes from Excel file")
            return mpo_codes
        except:
            pass
    return None

conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SQL_SERVER};DATABASE={DATABASE_NAME};Trusted_Connection=yes;'
conn = pyodbc.connect(conn_str)

print("=" * 70)
print("Creating Final MPO-wise Sales Report...")
print("=" * 70)

# Load MPO codes if available
mpo_codes = load_mpo_codes()

# Query for complete MPO sales data
if mpo_codes:
    # Use specific MPO codes
    mpo_filter = "', '".join(mpo_codes[:100])  # First 100 codes
    where_clause = f"WHERE o.xsp IN ('{mpo_filter}')"
    print(f"\nFiltering by {len(mpo_codes)} MPO codes from Excel file...")
else:
    # Use pattern matching
    where_clause = "WHERE o.xsp LIKE 'B%' AND LEN(o.xsp) = 4"
    print("\nUsing pattern matching for MPO codes (B***)...")

query = f"""
SELECT 
    o.xsp AS MPO_Code,
    o.xordernum AS Invoice_No,
    o.xdate AS Invoice_Date,
    o.xcus AS Customer_ID,
    c.xorg AS Customer_Name,
    c.xoffadd AS Customer_Address,
    c.xphone AS Customer_Phone,
    od.xitem AS Product_Code,
    i.xdesc AS Product_Name,
    od.xqtyord AS Quantity,
    od.xprice AS Unit_Price,
    od.xlineamt AS Line_Amount,
    o.xtotamt AS Total_Amount
FROM opord o
LEFT JOIN opodt od ON o.xordernum = od.xordernum
LEFT JOIN cacus c ON o.xcus = c.xcus
LEFT JOIN caitem i ON od.xitem = i.xitem
{where_clause}
ORDER BY o.xsp, o.xdate DESC
"""

print("\nFetching data...")
df = pd.read_sql(query, conn)

print(f"Found {len(df):,} records!")

# Create Excel with multiple sheets
output_file = f"MPO_Complete_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    # Sheet 1: All Details
    df.to_excel(writer, sheet_name='All Sales Details', index=False)
    
    # Sheet 2: MPO Summary
    mpo_summary = df.groupby('MPO_Code').agg({
        'Invoice_No': 'nunique',
        'Customer_ID': 'nunique',
        'Quantity': 'sum',
        'Line_Amount': 'sum'
    }).reset_index()
    mpo_summary.columns = ['MPO Code', 'Total Invoices', 'Total Customers', 'Total Quantity', 'Total Sales Amount']
    mpo_summary = mpo_summary.sort_values('Total Sales Amount', ascending=False)
    mpo_summary.to_excel(writer, sheet_name='MPO Summary', index=False)
    
    # Sheet 3: Top 20 MPOs
    top20 = mpo_summary.head(20)
    top20.to_excel(writer, sheet_name='Top 20 MPOs', index=False)

print(f"\nSaved: {output_file}")
print(f"\nReport contains:")
print(f"- All Sales Details: {len(df):,} records")
print(f"- MPO Summary: {len(mpo_summary)} MPOs")
print(f"- Top 20 MPOs")

print("\nTop 10 MPOs by Sales:")
print(mpo_summary.head(10).to_string(index=False))

conn.close()
print("\n" + "=" * 70)
print("Done!")
print("=" * 70)
