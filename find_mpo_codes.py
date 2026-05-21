# MPO Codes Finder - Search all tables for MPO codes like B045, B046, etc.

import pyodbc
import pandas as pd
from datetime import datetime
import re

def create_connection():
    """Database connection"""
    server_name = r'.\SQLEXPRESS'
    db_name = 'ERPonTheNet'
    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server_name};DATABASE={db_name};Trusted_Connection=yes;'
    return pyodbc.connect(conn_str)

def search_mpo_in_all_tables(conn):
    """Search for MPO codes in all tables"""
    
    print("\n" + "=" * 70)
    print("Searching for MPO Codes (B001, B002, B045, etc.) in all tables...")
    print("=" * 70)
    
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("""
        SELECT TABLE_SCHEMA, TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
    """)
    
    tables = cursor.fetchall()
    
    mpo_pattern = r'B\d{3}'  # Pattern: B followed by 3 digits
    
    results = []
    
    for schema, table in tables:
        try:
            # Get all columns for this table
            cursor.execute(f"""
                SELECT COLUMN_NAME, DATA_TYPE 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = '{schema}' AND TABLE_NAME = '{table}'
                AND DATA_TYPE IN ('varchar', 'char', 'nvarchar', 'nchar', 'text')
            """)
            
            columns = cursor.fetchall()
            
            for column, data_type in columns:
                try:
                    # Search for MPO pattern in this column
                    query = f"""
                        SELECT TOP 10 [{column}], COUNT(*) as Count
                        FROM [{schema}].[{table}]
                        WHERE [{column}] LIKE 'B[0-9][0-9][0-9]'
                        GROUP BY [{column}]
                        ORDER BY COUNT(*) DESC
                    """
                    
                    cursor.execute(query)
                    rows = cursor.fetchall()
                    
                    if rows:
                        for row in rows:
                            mpo_code = row[0]
                            count = row[1]
                            
                            results.append({
                                'Table': f"{schema}.{table}",
                                'Column': column,
                                'MPO_Code': mpo_code,
                                'Count': count
                            })
                            
                            print(f"   Found: {mpo_code} in {table}.{column} ({count} times)")
                
                except Exception as e:
                    continue
        
        except Exception as e:
            continue
    
    return results

def analyze_mpo_tables(conn):
    """Analyze specific tables that likely contain MPO data"""
    
    print("\n" + "=" * 70)
    print("Analyzing MPO-related tables...")
    print("=" * 70)
    
    # Check xcodes table (codes master)
    print("\n[1] Checking xcodes table...")
    try:
        query = """
            SELECT xcode, xlong, xtype, xsort 
            FROM xcodes 
            WHERE xcode LIKE 'B[0-9][0-9][0-9]'
            ORDER BY xcode
        """
        df_codes = pd.read_sql(query, conn)
        
        if len(df_codes) > 0:
            print(f"   Found {len(df_codes)} MPO codes in xcodes table!")
            output_file = f"MPO_Codes_Master_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df_codes.to_excel(output_file, index=False)
            print(f"   Saved: {output_file}")
            print(f"\n   Sample MPO Codes:")
            print(df_codes.head(10).to_string(index=False))
            return df_codes
        else:
            print("   No MPO codes found in xcodes")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Check cacus table (customers with MPO assignment)
    print("\n[2] Checking cacus table (Customer-MPO mapping)...")
    try:
        query = """
            SELECT DISTINCT xsm, xasm, xsp, xagent, xzone, xblock, COUNT(*) as CustomerCount
            FROM cacus
            WHERE xsm LIKE 'B[0-9][0-9][0-9]' 
               OR xasm LIKE 'B[0-9][0-9][0-9]'
               OR xsp LIKE 'B[0-9][0-9][0-9]'
               OR xagent LIKE 'B[0-9][0-9][0-9]'
            GROUP BY xsm, xasm, xsp, xagent, xzone, xblock
            ORDER BY CustomerCount DESC
        """
        df_customer_mpo = pd.read_sql(query, conn)
        
        if len(df_customer_mpo) > 0:
            print(f"   Found {len(df_customer_mpo)} MPO assignments in customers!")
            print(f"\n   Sample:")
            print(df_customer_mpo.head(10).to_string(index=False))
    except Exception as e:
        print(f"   Error: {e}")
    
    # Check opord table (orders with MPO)
    print("\n[3] Checking opord table (Orders with MPO)...")
    try:
        query = """
            SELECT DISTINCT xsm, xasm, xsp, xagent, xzone, COUNT(*) as OrderCount
            FROM opord
            WHERE xsm LIKE 'B[0-9][0-9][0-9]'
               OR xasm LIKE 'B[0-9][0-9][0-9]'
               OR xsp LIKE 'B[0-9][0-9][0-9]'
               OR xagent LIKE 'B[0-9][0-9][0-9]'
            GROUP BY xsm, xasm, xsp, xagent, xzone
            ORDER BY OrderCount DESC
        """
        df_order_mpo = pd.read_sql(query, conn)
        
        if len(df_order_mpo) > 0:
            print(f"   Found {len(df_order_mpo)} MPO codes in orders!")
            print(f"\n   Sample:")
            print(df_order_mpo.head(10).to_string(index=False))
    except Exception as e:
        print(f"   Error: {e}")
    
    return None

def create_mpo_sales_report(conn, mpo_codes_df):
    """Create detailed MPO-wise sales report"""
    
    print("\n" + "=" * 70)
    print("Creating MPO-wise Sales Report...")
    print("=" * 70)
    
    query = """
    SELECT 
        o.xsm AS MPO_Code,
        sm.xlong AS MPO_Name,
        o.xordernum AS InvoiceNo,
        o.xdate AS InvoiceDate,
        o.xcus AS CustomerID,
        c.xorg AS CustomerName,
        c.xoffadd AS CustomerAddress,
        o.xzone AS ZoneCode,
        zone.xlong AS ZoneName,
        od.xitem AS ProductCode,
        i.xdesc AS ProductName,
        od.xqtyord AS Quantity,
        od.xprice AS UnitPrice,
        od.xlineamt AS LineAmount,
        o.xtotamt AS TotalAmount,
        o.xstatusord AS Status
    FROM opord o
    LEFT JOIN opodt od ON o.xordernum = od.xordernum
    LEFT JOIN cacus c ON o.xcus = c.xcus
    LEFT JOIN caitem i ON od.xitem = i.xitem
    LEFT JOIN xcodes sm ON o.xsm = sm.xcode
    LEFT JOIN xcodes zone ON o.xzone = zone.xcode
    WHERE o.xsm LIKE 'B[0-9][0-9][0-9]'
    ORDER BY o.xsm, o.xdate DESC
    """
    
    print("   Fetching data...")
    df = pd.read_sql(query, conn)
    
    if len(df) > 0:
        print(f"   Found {len(df):,} sales records with MPO codes!")
        
        # Add date columns
        df['Year'] = pd.to_datetime(df['InvoiceDate'], errors='coerce').dt.year
        df['Month'] = pd.to_datetime(df['InvoiceDate'], errors='coerce').dt.month
        df['MonthName'] = pd.to_datetime(df['InvoiceDate'], errors='coerce').dt.strftime('%B')
        
        output_file = f"MPO_Sales_Report_Complete_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Sheet 1: Detailed Sales
            df.to_excel(writer, sheet_name='Detailed Sales', index=False)
            
            # Sheet 2: MPO Summary
            mpo_summary = df.groupby(['MPO_Code', 'MPO_Name']).agg({
                'InvoiceNo': 'nunique',
                'CustomerID': 'nunique',
                'Quantity': 'sum',
                'LineAmount': 'sum',
                'TotalAmount': 'sum'
            }).reset_index()
            mpo_summary.columns = ['MPO Code', 'MPO Name', 'Total Invoices', 'Total Customers', 'Total Quantity', 'Total Line Amount', 'Total Amount']
            mpo_summary = mpo_summary.sort_values('Total Amount', ascending=False)
            mpo_summary.to_excel(writer, sheet_name='MPO Summary', index=False)
            
            # Sheet 3: MPO-Customer Matrix
            mpo_customer = df.groupby(['MPO_Code', 'MPO_Name', 'CustomerID', 'CustomerName']).agg({
                'InvoiceNo': 'nunique',
                'LineAmount': 'sum'
            }).reset_index()
            mpo_customer.columns = ['MPO Code', 'MPO Name', 'Customer ID', 'Customer Name', 'Total Invoices', 'Total Amount']
            mpo_customer.to_excel(writer, sheet_name='MPO-Customer Matrix', index=False)
            
            # Sheet 4: MPO-Product Matrix
            mpo_product = df.groupby(['MPO_Code', 'MPO_Name', 'ProductCode', 'ProductName']).agg({
                'Quantity': 'sum',
                'LineAmount': 'sum'
            }).reset_index()
            mpo_product.columns = ['MPO Code', 'MPO Name', 'Product Code', 'Product Name', 'Total Quantity', 'Total Amount']
            mpo_product.to_excel(writer, sheet_name='MPO-Product Matrix', index=False)
            
            # Sheet 5: MPO Monthly Performance
            mpo_monthly = df.groupby(['MPO_Code', 'MPO_Name', 'Year', 'Month', 'MonthName']).agg({
                'InvoiceNo': 'nunique',
                'LineAmount': 'sum'
            }).reset_index()
            mpo_monthly.columns = ['MPO Code', 'MPO Name', 'Year', 'Month', 'Month Name', 'Total Invoices', 'Total Amount']
            mpo_monthly.to_excel(writer, sheet_name='MPO Monthly Performance', index=False)
        
        print(f"\n   Saved: {output_file}")
        print(f"\n   Report contains:")
        print(f"   - Detailed Sales: {len(df):,} records")
        print(f"   - MPO Summary: {len(mpo_summary)} MPOs")
        print(f"   - MPO-Customer Matrix: {len(mpo_customer)} combinations")
        print(f"   - MPO-Product Matrix: {len(mpo_product)} combinations")
        print(f"   - MPO Monthly Performance: {len(mpo_monthly)} records")
        
        return output_file
    else:
        print("   No sales data found with MPO codes!")
        return None

def main():
    print("=" * 70)
    print("MPO Codes Finder & Sales Report Generator")
    print("=" * 70)
    print("\nSearching for MPO codes like: B001, B002, B045, B046, B054, etc.")
    print("=" * 70)
    
    try:
        conn = create_connection()
        print("\nConnected to database successfully!")
        
        # Step 1: Analyze MPO tables
        mpo_codes_df = analyze_mpo_tables(conn)
        
        # Step 2: Search in all tables
        search_results = search_mpo_in_all_tables(conn)
        
        if search_results:
            print(f"\n\nTotal MPO code occurrences found: {len(search_results)}")
            
            # Save search results
            df_search = pd.DataFrame(search_results)
            search_file = f"MPO_Search_Results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df_search.to_excel(search_file, index=False)
            print(f"Search results saved: {search_file}")
        
        # Step 3: Create comprehensive MPO sales report
        if mpo_codes_df is not None:
            report_file = create_mpo_sales_report(conn, mpo_codes_df)
        
        conn.close()
        
        print("\n" + "=" * 70)
        print("MPO Analysis Complete!")
        print("=" * 70)
        print("\nGenerated files:")
        print("1. MPO_Codes_Master_*.xlsx - All MPO codes from master table")
        print("2. MPO_Search_Results_*.xlsx - Where MPO codes are used")
        print("3. MPO_Sales_Report_Complete_*.xlsx - Complete MPO-wise sales analysis")
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
