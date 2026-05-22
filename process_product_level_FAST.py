# FAST Product-Level Net Sales Calculation
# Uses CSV for speed, then converts to Excel

import pyodbc
import pandas as pd
import os
from datetime import datetime

# Configuration
ALL_DEPOTS_FOLDER = r"C:\Users\Irak\Desktop\Barishal April Data\All_Depots"
SQL_SERVER = r'.\SQLEXPRESS'

def find_all_depots():
    """Find all depot folders"""
    print(f"\nScanning for depots in: {ALL_DEPOTS_FOLDER}")
    
    if not os.path.exists(ALL_DEPOTS_FOLDER):
        print(f"  Error: Folder not found: {ALL_DEPOTS_FOLDER}")
        return []
    
    depots = []
    
    for depot_folder in os.listdir(ALL_DEPOTS_FOLDER):
        depot_path = os.path.join(ALL_DEPOTS_FOLDER, depot_folder)
        
        if os.path.isdir(depot_path):
            data_folder = os.path.join(depot_path, 'Data')
            
            if os.path.exists(data_folder):
                erp_mdf = None
                for file in os.listdir(data_folder):
                    if file.lower() == 'erponthenet_data.mdf':
                        erp_mdf = os.path.join(data_folder, file)
                        break
                
                if erp_mdf:
                    depots.append({
                        'name': depot_folder,
                        'path': depot_path,
                        'data_folder': data_folder,
                        'mdf_file': erp_mdf
                    })
                    print(f"  Found: {depot_folder}")
    
    print(f"\nTotal depots found: {len(depots)}")
    return depots

def attach_database(depot_name, mdf_path):
    """Attach MDF file to SQL Server"""
    try:
        mdf_dir = os.path.dirname(mdf_path)
        
        ldf_path = None
        for file in os.listdir(mdf_dir):
            if file.lower() == 'erponthenet_log.ldf':
                ldf_path = os.path.join(mdf_dir, file)
                break
        
        db_name = f"{depot_name}_DB"
        
        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SQL_SERVER};DATABASE=master;Trusted_Connection=yes;'
        conn = pyodbc.connect(conn_str)
        conn.autocommit = True
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT name FROM sys.databases WHERE name = '{db_name}'")
        if cursor.fetchone():
            conn.close()
            return db_name
        
        if ldf_path and os.path.exists(ldf_path):
            attach_query = f"""
            CREATE DATABASE [{db_name}] ON 
            (FILENAME = N'{mdf_path}'),
            (FILENAME = N'{ldf_path}')
            FOR ATTACH;
            """
        else:
            attach_query = f"""
            CREATE DATABASE [{db_name}] ON 
            (FILENAME = N'{mdf_path}')
            FOR ATTACH_REBUILD_LOG;
            """
        
        cursor.execute(attach_query)
        conn.close()
        return db_name
        
    except Exception as e:
        print(f"    ✗ Error attaching: {e}")
        return None

def extract_sales_data(depot_name, db_name):
    """Extract sales and returns data"""
    try:
        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SQL_SERVER};DATABASE={db_name};Trusted_Connection=yes;'
        conn = pyodbc.connect(conn_str)
        
        query = f"""
        SELECT 
            '{depot_name}' AS Depot,
            o.xsp AS MPO_Code,
            o.xordernum AS Invoice_No,
            o.xdate AS Invoice_Date,
            CASE 
                WHEN o.xordernum LIKE 'IN-%' OR o.xordernum LIKE 'IN--%' THEN 'Sale'
                WHEN o.xordernum LIKE 'SR-%' OR o.xordernum LIKE 'SR--%' THEN 'Return'
                ELSE 'Other'
            END AS Transaction_Type,
            o.xcus AS Customer_ID,
            LTRIM(RTRIM(c.xorg)) AS Customer_Name,
            od.xitem AS Product_Code,
            i.xdesc AS Product_Name,
            od.xqtyord AS Quantity,
            od.xlineamt AS Line_Amount
        FROM opord o
        LEFT JOIN opodt od ON o.xordernum = od.xordernum
        LEFT JOIN cacus c ON o.xcus = c.xcus
        LEFT JOIN caitem i ON od.xitem = i.xitem
        WHERE o.xsp IS NOT NULL 
          AND o.xsp != ''
          AND (o.xordernum LIKE 'IN-%' OR o.xordernum LIKE 'IN--%' 
               OR o.xordernum LIKE 'SR-%' OR o.xordernum LIKE 'SR--%')
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        return df
        
    except Exception as e:
        print(f"    ✗ Error extracting data: {e}")
        return pd.DataFrame()

def process_all_depots():
    """Main function"""
    print("=" * 80)
    print("FAST Product-Level Net Sales Calculator")
    print("=" * 80)
    
    depots = find_all_depots()
    if not depots:
        print("\nNo depots found. Exiting.")
        return
    
    all_data = []
    
    for i, depot in enumerate(depots, 1):
        print(f"\n[{i}/{len(depots)}] {depot['name']}", end=" ", flush=True)
        
        db_name = attach_database(depot['name'], depot['mdf_file'])
        
        if db_name:
            df = extract_sales_data(depot['name'], db_name)
            
            if len(df) > 0:
                all_data.append(df)
                sales_count = len(df[df['Transaction_Type'] == 'Sale'])
                returns_count = len(df[df['Transaction_Type'] == 'Return'])
                print(f"✓ Sales: {sales_count:,} | Returns: {returns_count:,}")
            else:
                print(f"✗ No data")
        else:
            print(f"✗ Failed")
    
    if not all_data:
        print("\nNo data extracted.")
        return
    
    print("\n" + "=" * 80)
    print("Processing...")
    print("=" * 80)
    
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Add Month column
    print("  [1/6] Adding Month column...")
    combined_df['Month'] = pd.to_datetime(combined_df['Invoice_Date']).dt.strftime('%Y-%m')
    
    # Create concatenated key
    print("  [2/6] Creating concatenated keys...")
    combined_df['CONCATENATED_KEY'] = (
        combined_df['Depot'].astype(str) + '_' +
        combined_df['MPO_Code'].astype(str) + '_' +
        combined_df['Customer_ID'].astype(str) + '_' +
        combined_df['Month'].astype(str) + '_' +
        combined_df['Product_Code'].astype(str)
    )
    
    # Separate sales and returns
    sales_df = combined_df[combined_df['Transaction_Type'] == 'Sale'].copy()
    returns_df = combined_df[combined_df['Transaction_Type'] == 'Return'].copy()
    
    print(f"      Sales: {len(sales_df):,} | Returns: {len(returns_df):,}")
    
    # Group sales
    print("  [3/6] Grouping sales...")
    sales_grouped = sales_df.groupby('CONCATENATED_KEY').agg({
        'Depot': 'first',
        'MPO_Code': 'first',
        'Customer_ID': 'first',
        'Customer_Name': 'first',
        'Month': 'first',
        'Product_Code': 'first',
        'Product_Name': 'first',
        'Quantity': 'sum',
        'Line_Amount': 'sum'
    }).reset_index()
    
    sales_grouped.columns = [
        'CONCATENATED_KEY', 'Depot', 'MPO_Code', 'Customer_ID', 'Customer_Name',
        'Month', 'Product_Code', 'Product_Name', 'Sale_Qty', 'Sale_Amount'
    ]
    
    print(f"      Unique keys: {len(sales_grouped):,}")
    
    # Group returns
    print("  [4/6] Grouping returns...")
    returns_grouped = returns_df.groupby('CONCATENATED_KEY').agg({
        'Quantity': 'sum',
        'Line_Amount': 'sum'
    }).reset_index()
    
    returns_grouped.columns = ['CONCATENATED_KEY', 'Return_Qty', 'Return_Amount']
    
    print(f"      Unique keys: {len(returns_grouped):,}")
    
    # Merge (VLOOKUP)
    print("  [5/6] Matching returns to sales (VLOOKUP)...")
    net_sales = pd.merge(
        sales_grouped,
        returns_grouped,
        on='CONCATENATED_KEY',
        how='left'
    )
    
    # Fill NaN and calculate
    net_sales['Return_Qty'] = net_sales['Return_Qty'].fillna(0)
    net_sales['Return_Amount'] = net_sales['Return_Amount'].fillna(0)
    net_sales['ACTUAL_SALE_QTY'] = net_sales['Sale_Qty'] - net_sales['Return_Qty']
    net_sales['ACTUAL_SALE_AMOUNT'] = net_sales['Sale_Amount'] - net_sales['Return_Amount']
    net_sales['Return_Rate_%'] = (net_sales['Return_Qty'] / net_sales['Sale_Qty'] * 100).round(2)
    
    # Save to CSV first (FAST!)
    print("  [6/6] Saving to CSV...")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_file = f"Product_Level_Net_Sales_{timestamp}.csv"
    
    net_sales.to_csv(csv_file, index=False)
    
    file_size_mb = os.path.getsize(csv_file) / (1024 * 1024)
    print(f"\n✓ Saved: {csv_file} ({file_size_mb:.2f} MB)")
    
    # Statistics
    total_sale_qty = net_sales['Sale_Qty'].sum()
    total_return_qty = net_sales['Return_Qty'].sum()
    total_actual_qty = net_sales['ACTUAL_SALE_QTY'].sum()
    
    total_sale_amt = net_sales['Sale_Amount'].sum()
    total_return_amt = net_sales['Return_Amount'].sum()
    total_actual_amt = net_sales['ACTUAL_SALE_AMOUNT'].sum()
    
    print(f"\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Unique Product-Level Combinations: {len(net_sales):,}")
    print(f"\nQuantity:")
    print(f"  Sale Qty:       {total_sale_qty:>15,.2f}")
    print(f"  Return Qty:     {total_return_qty:>15,.2f}")
    print(f"  ────────────────────────────────")
    print(f"  ACTUAL SALE:    {total_actual_qty:>15,.2f}")
    print(f"\nAmount (BDT):")
    print(f"  Sale Amount:    {total_sale_amt:>15,.2f}")
    print(f"  Return Amount:  {total_return_amt:>15,.2f}")
    print(f"  ────────────────────────────────")
    print(f"  ACTUAL SALE:    {total_actual_amt:>15,.2f}")
    print(f"  Return Rate:    {total_return_amt/total_sale_amt*100:>14.2f}%")
    
    # Depot summary
    depot_summary = net_sales.groupby('Depot').agg({
        'Sale_Amount': 'sum',
        'Return_Amount': 'sum',
        'ACTUAL_SALE_AMOUNT': 'sum'
    }).reset_index()
    depot_summary['Return_Rate_%'] = (depot_summary['Return_Amount'] / depot_summary['Sale_Amount'] * 100).round(2)
    depot_summary = depot_summary.sort_values('ACTUAL_SALE_AMOUNT', ascending=False)
    
    print(f"\n" + "=" * 80)
    print("Depot Summary:")
    print("=" * 80)
    print(depot_summary[['Depot', 'Sale_Amount', 'Return_Amount', 'ACTUAL_SALE_AMOUNT', 'Return_Rate_%']].to_string(index=False))
    
    print("\n" + "=" * 80)
    print("✓ Complete! Open CSV in Excel to analyze.")
    print("=" * 80)

if __name__ == "__main__":
    try:
        process_all_depots()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
