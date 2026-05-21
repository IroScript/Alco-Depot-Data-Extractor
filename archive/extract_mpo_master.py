# Extract MPO Master List and Sales Data

import pyodbc
import pandas as pd
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def create_connection():
    server_name = r'.\SQLEXPRESS'
    db_name = 'ERPonTheNet'
    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server_name};DATABASE={db_name};Trusted_Connection=yes;'
    return pyodbc.connect(conn_str)

def extract_mpo_master(conn):
    """Extract MPO master list from xcodes"""
    
    query = """
    SELECT 
        xcode AS MPO_Code,
        xlong AS MPO_Name,
        xshort AS Short_Name,
        xtype AS Type,
        xparent AS Parent,
        xseq AS Sequence
    FROM xcodes
    WHERE xcode LIKE 'B0%' OR xcode LIKE 'B[0-9]%'
    ORDER BY xcode
    """
    
    print("Extracting MPO Master List from xcodes...")
    df = pd.read_sql(query, conn)
    
    if len(df) > 0:
        output_file = f"MPO_Master_List_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(output_file, index=False)
        print(f"   Saved: {output_file}")
        print(f"   Total MPOs: {len(df)}")
        print(f"\n   Sample MPO Codes:")
        for code in df['MPO_Code'].head(10):
            print(f"      - {code}")
        return output_file
    else:
        print("   No MPO codes found in xcodes!")
        return None

def extract_mpo_sales_complete(conn):
    """Complete MPO wise sales report"""
    
    query = """
    SELECT 
        -- Order Info
        o.xordernum AS Invoice_No,
        o.xdate AS Invoice_Date,
        o.xstatusord AS Order_Status,
        
        -- MPO/Sales Person Info
        o.xsp AS MPO_Code,
        mpo.xlong AS MPO_Name,
        
        -- Customer Info
        o.xcus AS Customer_ID,
        c.xorg AS Customer_Name,
        c.xoffadd AS Customer_Address,
        c.xphone AS Customer_Phone,
        c.xzone AS Customer_Zone,
        c.xblock AS Customer_Block,
        
        -- Product Info
        od.xitem AS Product_Code,
        i.xdesc AS Product_Name,
        i.xgitem AS Product_Group,
        
        -- Sales Details
        od.xqtyord AS Quantity,
        od.xprice AS Unit_Price,
        od.xlineamt AS Line_Amount,
        od.xdisc AS Discount,
        od.xdiscf AS Discount_Percent,
        
        -- Order Totals
        o.xtotamt AS Total_Amount,
        o.xdiscamt AS Total_Discount,
        
        -- Additional Info
        o.xzone AS Zone_Code,
        zone.xlong AS Zone_Name,
        o.xwh AS Warehouse,
        o.xyear AS Year,
        o.xper AS Period
        
    FROM opord o
    LEFT JOIN opodt od ON o.xordernum = od.xordernum
    LEFT JOIN cacus c ON o.xcus = c.xcus
    LEFT JOIN caitem i ON od.xitem = i.xitem
    LEFT JOIN xcodes mpo ON o.xsp = mpo.xcode
    LEFT JOIN xcodes zone ON o.xzone = zone.xcode
    
    WHERE o.xsp IS NOT NULL 
      AND o.xsp LIKE 'B%'
      AND o.xordernum IS NOT NULL
    
    ORDER BY o.xsp, o.xdate DESC, o.xordernum
    """
    
    print("\nExtracting Complete MPO Sales Data...")
    df = pd.read_sql(query, conn)
    
    if len(df) > 0:
        # Add date columns
        df['Invoice_Date'] = pd.to_datetime(df['Invoice_Date'], errors='coerce')
        df['Year'] = df['Invoice_Date'].dt.year
        df['Month'] = df['Invoice_Date'].dt.month
        df['Month_Name'] = df['Invoice_Date'].dt.strftime('%B')
        df['Date'] = df['Invoice_Date'].dt.date
        
        output_file = f"MPO_Sales_Complete_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Main detailed data
            df.to_excel(writer, sheet_name='All Sales Data', index=False)
            
            # MPO Summary
            mpo_summary = df.groupby(['MPO_Code', 'MPO_Name']).agg({
                'Invoice_No': 'nunique',
                'Customer_ID': 'nunique',
                'Quantity': 'sum',
                'Line_Amount': 'sum',
                'Total_Amount': 'sum'
            }).reset_index()
            mpo_summary.columns = ['MPO Code', 'MPO Name', 'Total Invoices', 'Unique Customers', 'Total Quantity', 'Total Line Amount', 'Total Amount']
            mpo_summary = mpo_summary.sort_values('Total Amount', ascending=False)
            mpo_summary.to_excel(writer, sheet_name='MPO Summary', index=False)
            
            # MPO + Customer Summary
            mpo_customer = df.groupby(['MPO_Code', 'MPO_Name', 'Customer_ID', 'Customer_Name']).agg({
                'Invoice_No': 'nunique',
                'Quantity': 'sum',
                'Line_Amount': 'sum'
            }).reset_index()
            mpo_customer.columns = ['MPO Code', 'MPO Name', 'Customer ID', 'Customer Name', 'Total Invoices', 'Total Quantity', 'Total Amount']
            mpo_customer.to_excel(writer, sheet_name='MPO-Customer', index=False)
            
            # MPO + Product Summary
            mpo_product = df.groupby(['MPO_Code', 'MPO_Name', 'Product_Code', 'Product_Name']).agg({
                'Invoice_No': 'nunique',
                'Quantity': 'sum',
                'Line_Amount': 'sum'
            }).reset_index()
            mpo_product.columns = ['MPO Code', 'MPO Name', 'Product Code', 'Product Name', 'Total Invoices', 'Total Quantity', 'Total Amount']
            mpo_product.to_excel(writer, sheet_name='MPO-Product', index=False)
            
            # MPO + Month Summary
            mpo_month = df.groupby(['MPO_Code', 'MPO_Name', 'Year', 'Month', 'Month_Name']).agg({
                'Invoice_No': 'nunique',
                'Quantity': 'sum',
                'Line_Amount': 'sum'
            }).reset_index()
            mpo_month.columns = ['MPO Code', 'MPO Name', 'Year', 'Month', 'Month Name', 'Total Invoices', 'Total Quantity', 'Total Amount']
            mpo_month.to_excel(writer, sheet_name='MPO-Monthly', index=False)
        
        print(f"   Saved: {output_file}")
        print(f"   Total Records: {len(df):,}")
        print(f"   Unique MPOs: {df['MPO_Code'].nunique()}")
        print(f"   Unique Customers: {df['Customer_ID'].nunique()}")
        print(f"   Unique Products: {df['Product_Code'].nunique()}")
        print(f"\n   Sheets created:")
        print(f"      1. All Sales Data (detailed)")
        print(f"      2. MPO Summary")
        print(f"      3. MPO-Customer")
        print(f"      4. MPO-Product")
        print(f"      5. MPO-Monthly")
        
        return output_file
    else:
        print("   No sales data found for MPOs!")
        return None

def main():
    print("=" * 80)
    print("MPO DATA EXTRACTOR")
    print("=" * 80)
    
    try:
        conn = create_connection()
        print("\nConnected to database!\n")
        
        # Extract MPO Master List
        print("[1/2] MPO Master List")
        print("-" * 80)
        mpo_master = extract_mpo_master(conn)
        
        # Extract Complete Sales Data
        print("\n[2/2] Complete MPO Sales Data")
        print("-" * 80)
        sales_report = extract_mpo_sales_complete(conn)
        
        conn.close()
        
        print("\n" + "=" * 80)
        print("EXTRACTION COMPLETE!")
        print("=" * 80)
        
        if mpo_master:
            print(f"\n1. MPO Master List: {mpo_master}")
        if sales_report:
            print(f"2. Complete Sales Report: {sales_report}")
        
        print("\nNow you have:")
        print("- MPO codes and names")
        print("- Complete sales data by MPO")
        print("- MPO wise summaries (Customer, Product, Monthly)")
        print("- All data properly related!")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
