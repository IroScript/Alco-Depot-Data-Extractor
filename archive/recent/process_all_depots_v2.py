# Process All Depots - Version 2 with Returns Handling

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
                # Find ONLY ERPonTheNet_Data.MDF file
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
        
        # Find LDF file
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
        
        # Check if already attached
        cursor.execute(f"SELECT name FROM sys.databases WHERE name = '{db_name}'")
        if cursor.fetchone():
            print(f"    ✓ Database '{db_name}' already attached")
            conn.close()
            return db_name
        
        # Attach
        if ldf_path and os.path.exists(ldf_path):
            attach_query = f"""
            CREATE DATABASE [{db_name}] ON 
            (FILENAME = N'{mdf_path}'),
            (FILENAME = N'{ldf_path}')
            FOR ATTACH;
            """
            print(f"    Attaching with log file...")
        else:
            attach_query = f"""
            CREATE DATABASE [{db_name}] ON 
            (FILENAME = N'{mdf_path}')
            FOR ATTACH_REBUILD_LOG;
            """
            print(f"    Attaching and rebuilding log...")
        
        cursor.execute(attach_query)
        print(f"    ✓ Attached: {db_name}")
        
        conn.close()
        return db_name
        
    except Exception as e:
        print(f"    ✗ Error attaching: {e}")
        return None

def extract_mpo_data(depot_name, db_name):
    """Extract MPO-wise sales data with Invoice Type classification"""
    try:
        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SQL_SERVER};DATABASE={db_name};Trusted_Connection=yes;'
        conn = pyodbc.connect(conn_str)
        
        # Extract ALL data with Invoice Type classification
        query = f"""
        SELECT 
            '{depot_name}' AS Depot,
            o.xsp AS MPO_Code,
            o.xordernum AS Invoice_No,
            o.xdate AS Invoice_Date,
            CASE 
                WHEN o.xordernum LIKE 'IN-%' OR o.xordernum LIKE 'IN--%' THEN 'Sale'
                WHEN o.xordernum LIKE 'MR-%' OR o.xordernum LIKE 'MR--%' THEN 'Material Return'
                WHEN o.xordernum LIKE 'SR-%' OR o.xordernum LIKE 'SR--%' THEN 'Sales Return'
                WHEN o.xordernum LIKE 'CR-%' OR o.xordernum LIKE 'CR--%' THEN 'Credit Note'
                ELSE 'Other'
            END AS Invoice_Type,
            o.xstatusord AS Status,
            o.xcus AS Customer_ID,
            c.xorg AS Customer_Name,
            od.xitem AS Product_Code,
            i.xdesc AS Product_Name,
            od.xqtyord AS Quantity,
            od.xprice AS Unit_Price,
            od.xlineamt AS Line_Amount,
            o.xtotamt AS Invoice_Total
        FROM opord o
        LEFT JOIN opodt od ON o.xordernum = od.xordernum
        LEFT JOIN cacus c ON o.xcus = c.xcus
        LEFT JOIN caitem i ON od.xitem = i.xitem
        WHERE o.xsp IS NOT NULL AND o.xsp != ''
        ORDER BY o.xsp, o.xdate DESC
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        return df
        
    except Exception as e:
        print(f"    ✗ Error extracting data: {e}")
        return pd.DataFrame()

def process_all_depots():
    """Main function to process all depots"""
    print("=" * 70)
    print("Multi-Depot MPO Data Extractor - Version 2 (with Returns)")
    print("=" * 70)
    
    # Find depots
    depots = find_all_depots()
    if not depots:
        print("\nNo depots found. Exiting.")
        return
    
    # Process each depot
    all_data = []
    
    for i, depot in enumerate(depots, 1):
        print(f"\n[{i}/{len(depots)}] Processing: {depot['name']}")
        print("-" * 70)
        
        # Attach database
        db_name = attach_database(depot['name'], depot['mdf_file'])
        
        if db_name:
            # Extract data
            print(f"  Extracting MPO data...")
            df = extract_mpo_data(depot['name'], db_name)
            
            if len(df) > 0:
                all_data.append(df)
                print(f"  ✓ Found: {len(df):,} records")
            else:
                print(f"  ✗ No MPO data found")
        else:
            print(f"  ✗ Failed to attach database")
    
    # Combine all data
    if all_data:
        print("\n" + "=" * 70)
        print("Combining Data from All Depots")
        print("=" * 70)
        
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Add Month column based on Invoice_Date
        combined_df['Month'] = pd.to_datetime(combined_df['Invoice_Date']).dt.strftime('%Y-%m')
        
        # Create unique output filename
        base_name = "All_Depots_MPO_Report_V2"
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"{base_name}_{timestamp}.xlsx"
        
        counter = 1
        while os.path.exists(output_file):
            output_file = f"{base_name}_{timestamp}_{counter}.xlsx"
            counter += 1
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Sheet 1: All data
            combined_df.to_excel(writer, sheet_name='All Data', index=False)
            
            # Sheet 2: Sales Only (excluding returns)
            sales_only = combined_df[combined_df['Invoice_Type'] == 'Sale'].copy()
            sales_only.to_excel(writer, sheet_name='Sales Only', index=False)
            
            # Sheet 3: Returns Only
            returns_only = combined_df[combined_df['Invoice_Type'].isin(['Material Return', 'Sales Return'])].copy()
            returns_only.to_excel(writer, sheet_name='Returns Only', index=False)
            
            # Sheet 4: Depot Summary (All)
            depot_summary_all = combined_df.groupby('Depot').agg({
                'Invoice_No': 'nunique',
                'Customer_ID': 'nunique',
                'Line_Amount': 'sum'
            }).reset_index()
            depot_summary_all.columns = ['Depot', 'Total Invoices', 'Total Customers', 'Total Amount']
            depot_summary_all.to_excel(writer, sheet_name='Depot Summary (All)', index=False)
            
            # Sheet 5: Depot Summary (Sales Only)
            depot_summary_sales = sales_only.groupby('Depot').agg({
                'Invoice_No': 'nunique',
                'Customer_ID': 'nunique',
                'Line_Amount': 'sum'
            }).reset_index()
            depot_summary_sales.columns = ['Depot', 'Total Invoices', 'Total Customers', 'Net Sales']
            depot_summary_sales.to_excel(writer, sheet_name='Depot Summary (Sales)', index=False)
            
            # Sheet 6: Invoice Type Summary
            type_summary = combined_df.groupby(['Depot', 'Invoice_Type']).agg({
                'Invoice_No': 'nunique',
                'Line_Amount': 'sum'
            }).reset_index()
            type_summary.columns = ['Depot', 'Invoice Type', 'Count', 'Total Amount']
            type_summary.to_excel(writer, sheet_name='Invoice Type Summary', index=False)
            
            # Sheet 7: MPO Summary (Sales Only)
            mpo_summary = sales_only.groupby(['Depot', 'MPO_Code']).agg({
                'Invoice_No': 'nunique',
                'Line_Amount': 'sum'
            }).reset_index()
            mpo_summary.columns = ['Depot', 'MPO Code', 'Total Invoices', 'Total Sales']
            mpo_summary.to_excel(writer, sheet_name='MPO Summary', index=False)
            
            # Sheet 8: Monthly Summary
            monthly_summary = sales_only.groupby(['Depot', 'Month']).agg({
                'Invoice_No': 'nunique',
                'Line_Amount': 'sum'
            }).reset_index()
            monthly_summary.columns = ['Depot', 'Month', 'Total Invoices', 'Total Sales']
            monthly_summary.to_excel(writer, sheet_name='Monthly Summary', index=False)
        
        print(f"\nSaved: {output_file}")
        print(f"Total Records: {len(combined_df):,}")
        print(f"Total Depots: {len(depot_summary_all)}")
        
        # Calculate statistics
        total_all = combined_df['Line_Amount'].sum()
        total_sales = sales_only['Line_Amount'].sum()
        total_returns = returns_only['Line_Amount'].sum()
        
        print(f"\n" + "=" * 70)
        print("SUMMARY STATISTICS")
        print("=" * 70)
        print(f"Total Records: {len(combined_df):,}")
        print(f"  - Sales: {len(sales_only):,} ({len(sales_only)/len(combined_df)*100:.1f}%)")
        print(f"  - Returns: {len(returns_only):,} ({len(returns_only)/len(combined_df)*100:.1f}%)")
        print(f"\nTotal Amount (All): {total_all:,.2f} BDT")
        print(f"  - Sales: {total_sales:,.2f} BDT")
        print(f"  - Returns: {total_returns:,.2f} BDT")
        print(f"  - Net Sales: {total_sales - total_returns:,.2f} BDT")
        
        print(f"\nDepot Summary (Sales Only):")
        print(depot_summary_sales.to_string(index=False))
        
    else:
        print("\nNo data extracted from any depot.")
    
    print("\n" + "=" * 70)
    print("Processing Complete!")
    print("=" * 70)

if __name__ == "__main__":
    try:
        process_all_depots()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
