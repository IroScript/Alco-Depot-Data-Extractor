# Process All Depots - Extract MPO-wise data from multiple depot databases

import pyodbc
import pandas as pd
import os
from datetime import datetime
import glob

# Configuration
MPO_CODES_FILE = r"C:\Users\Irak\Desktop\Barishal April Data\mpo_code.xlsx"
ALL_DEPOTS_FOLDER = r"C:\Users\Irak\Desktop\Barishal April Data\All_Depots"
SQL_SERVER = r'.\SQLEXPRESS'

def load_mpo_codes():
    """Load MPO codes from Excel file"""
    print("Loading MPO codes from Excel...")
    
    if not os.path.exists(MPO_CODES_FILE):
        print(f"  Error: MPO codes file not found: {MPO_CODES_FILE}")
        return []
    
    try:
        df = pd.read_excel(MPO_CODES_FILE)
        # Get first column (MPO codes)
        mpo_codes = df.iloc[:, 0].dropna().astype(str).tolist()
        print(f"  Loaded {len(mpo_codes)} MPO codes")
        return mpo_codes
    except Exception as e:
        print(f"  Error loading MPO codes: {e}")
        return []

def find_all_depots():
    """Find all depot folders"""
    print(f"\nScanning for depots in: {ALL_DEPOTS_FOLDER}")
    
    if not os.path.exists(ALL_DEPOTS_FOLDER):
        print(f"  Error: Folder not found: {ALL_DEPOTS_FOLDER}")
        return []
    
    depots = []
    
    # Find all folders that contain a "Data" subfolder
    for depot_folder in os.listdir(ALL_DEPOTS_FOLDER):
        depot_path = os.path.join(ALL_DEPOTS_FOLDER, depot_folder)
        
        if os.path.isdir(depot_path):
            data_folder = os.path.join(depot_path, 'Data')
            
            if os.path.exists(data_folder):
                # Find ONLY ERPonTheNet_Data.MDF file (case insensitive)
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
        # Find LDF file in the same directory
        mdf_dir = os.path.dirname(mdf_path)
        mdf_basename = os.path.basename(mdf_path)
        
        # Try to find matching LDF file (case insensitive)
        ldf_path = None
        for file in os.listdir(mdf_dir):
            if file.lower() == 'erponthenet_log.ldf':
                ldf_path = os.path.join(mdf_dir, file)
                break
        
        # Database name
        db_name = f"{depot_name}_DB"
        
        # Connect to master
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
            # Attach without LDF - rebuild log
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
    """Extract MPO-wise sales data from depot database"""
    try:
        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SQL_SERVER};DATABASE={db_name};Trusted_Connection=yes;'
        conn = pyodbc.connect(conn_str)
        
        # Extract ALL MPO data (no filtering)
        query = f"""
        SELECT 
            '{depot_name}' AS Depot,
            o.xsp AS MPO_Code,
            o.xordernum AS Invoice_No,
            o.xdate AS Invoice_Date,
            o.xcus AS Customer_ID,
            c.xorg AS Customer_Name,
            od.xitem AS Product_Code,
            i.xdesc AS Product_Name,
            od.xqtyord AS Quantity,
            od.xprice AS Unit_Price,
            od.xlineamt AS Line_Amount
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
    print("Multi-Depot MPO Data Extractor")
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
        
        # Create output file with unique name (never overwrite)
        base_name = "All_Depots_MPO_Report"
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"{base_name}_{timestamp}.xlsx"
        
        # Ensure unique filename
        counter = 1
        while os.path.exists(output_file):
            output_file = f"{base_name}_{timestamp}_{counter}.xlsx"
            counter += 1
        
        # Add Month column to data
        combined_df['Month'] = pd.to_datetime(combined_df['Invoice_Date']).dt.strftime('%Y-%m')
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # All data
            combined_df.to_excel(writer, sheet_name='All Data', index=False)
            
            # Depot summary
            depot_summary = combined_df.groupby('Depot').agg({
                'Invoice_No': 'nunique',
                'Customer_ID': 'nunique',
                'Line_Amount': 'sum'
            }).reset_index()
            depot_summary.columns = ['Depot', 'Total Invoices', 'Total Customers', 'Total Sales']
            depot_summary.to_excel(writer, sheet_name='Depot Summary', index=False)
            
            # MPO summary
            mpo_summary = combined_df.groupby(['Depot', 'MPO_Code']).agg({
                'Invoice_No': 'nunique',
                'Line_Amount': 'sum'
            }).reset_index()
            mpo_summary.columns = ['Depot', 'MPO Code', 'Total Invoices', 'Total Sales']
            mpo_summary.to_excel(writer, sheet_name='MPO Summary', index=False)
        
        print(f"\nSaved: {output_file}")
        print(f"Total Records: {len(combined_df):,}")
        print(f"Total Depots: {len(depot_summary)}")
        print(f"\nDepot Summary:")
        print(depot_summary.to_string(index=False))
        
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
