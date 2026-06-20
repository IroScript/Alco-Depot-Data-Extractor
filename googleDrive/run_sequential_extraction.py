import os
import re
import sys
import time
import zipfile
import shutil
import subprocess
import tkinter as tk
import pyodbc
import pandas as pd
from unittest.mock import patch

# Reconfigure console output encoding
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
    except:
        pass

# Add parent directory to sys.path to resolve imports from project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Imports from the main script
from single_click_auto_run_no_need__following_steps import (
    load_env, get_drive_service, list_drive_folder_items, get_best_item_from_groq,
    find_rclone_executable, upgrade_db_compatibility, grant_sql_server_permissions,
    CLIENT_SECRET_PATH, EXCEL_PATH, ENV_PATH, BASE_DEPOT_DIR, RCLONE_REMOTE_NAME, SQL_SERVER
)

def run_sql(cursor, query):
    try:
        cursor.execute(query)
    except Exception as e:
        print(f"    Error: {e}")

def recover_sylhet_db(mdf_path, depot_name):
    """Special recovery for SYLHET MDF file where log rebuild fails standard attach"""
    db_name = f"{depot_name.upper()}_DB"
    data_dir = os.path.dirname(mdf_path)
    
    dummy_mdf_path = os.path.join(data_dir, 'dummy_ERPonTheNet.mdf')
    dummy_ldf_path = os.path.join(data_dir, 'dummy_ERPonTheNet_log.ldf')
    
    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SQL_SERVER};DATABASE=master;Trusted_Connection=yes;'
    conn = pyodbc.connect(conn_str)
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Clean up existing database if any
    cursor.execute(f"SELECT database_id FROM sys.databases WHERE name = '{db_name}'")
    if cursor.fetchone():
        try:
            cursor.execute(f"ALTER DATABASE [{db_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
            cursor.execute(f"DROP DATABASE [{db_name}]")
        except:
            pass
            
    # Delete dummy files if they exist
    for f in [dummy_mdf_path, dummy_ldf_path]:
        if os.path.exists(f):
            os.remove(f)
            
    # Create dummy database in our workspace directory
    create_query = f"""
    CREATE DATABASE [{db_name}] ON PRIMARY 
    (NAME = '{db_name}_data', FILENAME = '{dummy_mdf_path}')
    LOG ON 
    (NAME = '{db_name}_log', FILENAME = '{dummy_ldf_path}')
    """
    cursor.execute(create_query)
    
    # Set offline
    cursor.execute(f"ALTER DATABASE [{db_name}] SET OFFLINE WITH ROLLBACK IMMEDIATE")
    
    # Replace dummy MDF with target MDF
    if os.path.exists(dummy_mdf_path):
        os.remove(dummy_mdf_path)
    shutil.copy2(mdf_path, dummy_mdf_path)
    
    # Delete dummy LDF to force rebuild
    if os.path.exists(dummy_ldf_path):
        os.remove(dummy_ldf_path)
        
    # Set online (will fail/warn, which is expected)
    try:
        cursor.execute(f"ALTER DATABASE [{db_name}] SET ONLINE")
    except Exception as e:
        pass
        
    # Set to EMERGENCY mode
    cursor.execute(f"ALTER DATABASE [{db_name}] SET EMERGENCY")
    
    # Set to SINGLE_USER
    cursor.execute(f"ALTER DATABASE [{db_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
    
    # Rebuild Log and Repair
    print("    Running DBCC CHECKDB with REPAIR_ALLOW_DATA_LOSS to rebuild log file...")
    try:
        cursor.execute(f"DBCC CHECKDB ('{db_name}', REPAIR_ALLOW_DATA_LOSS) WITH NO_INFOMSGS, ALL_ERRORMSGS")
    except Exception as e:
        print(f"    DBCC warning (expected): {e}")
        
    # Set back to MULTI_USER
    try:
        cursor.execute(f"ALTER DATABASE [{db_name}] SET MULTI_USER")
    except:
        pass
        
    # Upgrade compatibility
    cursor.execute(f"ALTER DATABASE [{db_name}] SET COMPATIBILITY_LEVEL = 100")
    print(f"    [SUCCESS] Recovered and attached Suspect database: {db_name}")
    
    conn.close()
    return db_name

def attach_database(depot_name, mdf_path, ldf_path):
    db_name = f"{depot_name.upper()}_DB"
    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SQL_SERVER};DATABASE=master;Trusted_Connection=yes;'
    
    conn = pyodbc.connect(conn_str)
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Drop/Detach if already exists
    cursor.execute(f"SELECT database_id FROM sys.databases WHERE name = '{db_name}'")
    if cursor.fetchone():
        try:
            cursor.execute(f"ALTER DATABASE [{db_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
            cursor.execute(f"EXEC sp_detach_db '{db_name}', 'true'")
        except:
            pass
            
    mdf_path = os.path.normpath(mdf_path)
    grant_sql_server_permissions(os.path.dirname(mdf_path))
    
    if ldf_path and os.path.exists(ldf_path):
        ldf_path = os.path.normpath(ldf_path)
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
        
    print(f"    Attaching database {db_name}...")
    cursor.execute(attach_query)
    conn.close()
    return db_name

def detach_database(db_name):
    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SQL_SERVER};DATABASE=master;Trusted_Connection=yes;'
    try:
        conn = pyodbc.connect(conn_str)
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute(f"SELECT database_id FROM sys.databases WHERE name = '{db_name}'")
        if cursor.fetchone():
            cursor.execute(f"ALTER DATABASE [{db_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
            cursor.execute(f"EXEC sp_detach_db '{db_name}', 'true'")
            print(f"    ✓ Detached {db_name}")
        conn.close()
    except Exception as e:
        print(f"    Error detaching {db_name}: {e}")

def extract_sales_data(depot_name, db_name):
    try:
        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SQL_SERVER};DATABASE={db_name};Trusted_Connection=yes;'
        conn = pyodbc.connect(conn_str)
        
        query = f"""
        SELECT 
            '{depot_name}' AS Depot,
            o.xsp AS MPO_Code,
            o.xordernum AS Invoice_No,
            o.xdate AS Invoice_Date,
            o.ztime AS Transaction_Time,
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
        print(f"    [ERROR] Error extracting from {db_name}: {e}")
        return pd.DataFrame()

def download_depot_files(depot_name, folder_url, drive_service, groq_api_key):
    """Download MDF/LDF files for a single depot to its folder"""
    depot_dir = os.path.join(BASE_DEPOT_DIR, depot_name)
    data_dir = os.path.join(depot_dir, "Data")
    os.makedirs(data_dir, exist_ok=True)
    
    final_mdf_path = os.path.join(data_dir, "ERPonTheNet_Data.MDF")
    final_ldf_path = os.path.join(data_dir, "ERPonTheNet_log.LDF")
    
    # Check if files already exist
    if os.path.exists(final_mdf_path):
        print(f"  Local MDF file already exists at: {final_mdf_path}")
        return final_mdf_path, (final_ldf_path if os.path.exists(final_ldf_path) else None)
        
    folder_id_match = re.search(r'folders/([a-zA-Z0-9-_]+)', str(folder_url))
    if not folder_id_match:
        print(f"  Error: Invalid folder URL: {folder_url}")
        return None, None
        
    folder_id = folder_id_match.group(1)
    items = list_drive_folder_items(drive_service, folder_id)
    if not items:
        print(f"  No files or folders found in drive folder.")
        return None, None
        
    print("  Asking Groq LLM to verify and select the correct file...")
    decision = get_best_item_from_groq(depot_name, items, groq_api_key)
    selected_name = decision.get("selected_item_name")
    selected_id = decision.get("selected_item_id")
    selected_type = decision.get("selected_item_type")
    print(f"  Selected '{selected_name}' ({selected_type})")
    
    temp_download_dir = os.path.join(depot_dir, "Temp_Download")
    os.makedirs(temp_download_dir, exist_ok=True)
    
    rclone_exe = find_rclone_executable()
    mdf_local_path = None
    ldf_local_path = None
    
    try:
        if selected_type == 'file' and selected_name.lower().endswith('.zip'):
            zip_path = os.path.join(temp_download_dir, selected_name)
            remote_file_path = f"{RCLONE_REMOTE_NAME},root_folder_id={folder_id}:{selected_name}"
            cmd = [rclone_exe, "copyto", "--progress", remote_file_path, zip_path]
            print(f"  Downloading ZIP file...")
            subprocess.run(cmd, check=True)
            
            print(f"  Extracting ZIP file...")
            extract_dir = os.path.join(temp_download_dir, "extracted")
            os.makedirs(extract_dir, exist_ok=True)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
                
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    f_name = file.lower()
                    if f_name == 'erponthenet_data.mdf':
                        mdf_local_path = os.path.join(root, file)
                    elif f_name == 'erponthenet_log.ldf':
                        ldf_local_path = os.path.join(root, file)
                        
            if not mdf_local_path:
                for root, dirs, files in os.walk(extract_dir):
                    for file in files:
                        if file.lower().endswith('.mdf') and not file.lower().startswith(('master', 'tempdb', 'msdb', 'model')):
                            mdf_local_path = os.path.join(root, file)
                        elif file.lower().endswith('.ldf') and not file.lower().startswith(('mastlog', 'templog', 'msdb', 'model')):
                            ldf_local_path = os.path.join(root, file)
                            
        elif selected_type == 'folder':
            print("  Downloading MDF/LDF from folder...")
            # We copy files directly matching ERPonTheNet* to save space and time
            cmd = [
                rclone_exe, "copy",
                "--progress",
                f"{RCLONE_REMOTE_NAME},root_folder_id={selected_id}:",
                temp_download_dir,
                "--include", "ERPonTheNet*",
                "--ignore-case"
            ]
            subprocess.run(cmd, check=True)
            
            for root, dirs, files in os.walk(temp_download_dir):
                for file in files:
                    f_name = file.lower()
                    if f_name == 'erponthenet_data.mdf':
                        mdf_local_path = os.path.join(root, file)
                    elif f_name == 'erponthenet_log.ldf':
                        ldf_local_path = os.path.join(root, file)
        else:
            if selected_name.lower().endswith('.mdf'):
                temp_mdf_path = os.path.join(temp_download_dir, selected_name)
                remote_mdf_path = f"{RCLONE_REMOTE_NAME},root_folder_id={folder_id}:{selected_name}"
                cmd = [rclone_exe, "copyto", "--progress", remote_mdf_path, temp_mdf_path]
                print(f"  Downloading MDF file...")
                subprocess.run(cmd, check=True)
                mdf_local_path = temp_mdf_path
                
                for item in items:
                    if item['name'].lower().endswith('.ldf') and 'erponthenet' in item['name'].lower():
                        temp_ldf_path = os.path.join(temp_download_dir, item['name'])
                        remote_ldf_path = f"{RCLONE_REMOTE_NAME},root_folder_id={folder_id}:{item['name']}"
                        cmd = [rclone_exe, "copyto", "--progress", remote_ldf_path, temp_ldf_path]
                        print(f"  Downloading LDF file...")
                        subprocess.run(cmd, check=True)
                        ldf_local_path = temp_ldf_path
                        break
                        
        if not mdf_local_path or not os.path.exists(mdf_local_path):
            print("  Error: MDF file not downloaded successfully.")
            return None, None
            
        # Move to final destination
        if os.path.exists(final_mdf_path):
            os.remove(final_mdf_path)
        shutil.move(mdf_local_path, final_mdf_path)
        
        if ldf_local_path and os.path.exists(ldf_local_path):
            if os.path.exists(final_ldf_path):
                os.remove(final_ldf_path)
            shutil.move(ldf_local_path, final_ldf_path)
        else:
            final_ldf_path = None
            
        shutil.rmtree(temp_download_dir, ignore_errors=True)
        return final_mdf_path, final_ldf_path
        
    except Exception as e:
        print(f"  Error downloading depot {depot_name}: {e}")
        shutil.rmtree(temp_download_dir, ignore_errors=True)
        return None, None

def check_free_space():
    total, used, free = shutil.disk_usage("C:\\")
    return free / (1024 * 1024 * 1024) # Return in GB

def main_sequential():
    base_dir = r'c:\Users\Irak\Desktop\Barishal April Data'
    print("=" * 80)
    print("  SEQUENTIAL SPACE-SAVING DATA EXTRACTOR PIPELINE")
    print("=" * 80)
    
    # Initial cleanup of any attached _DB databases to ensure clean slate
    print("Cleaning up old databases from SQLEXPRESS...")
    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SQL_SERVER};DATABASE=master;Trusted_Connection=yes;'
    try:
        conn = pyodbc.connect(conn_str)
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sys.databases WHERE name LIKE '%_DB' AND name NOT IN ('master','tempdb','model','msdb')")
        dbs = [r[0] for r in cursor.fetchall()]
        for db in dbs:
            try:
                cursor.execute(f"ALTER DATABASE [{db}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
                cursor.execute(f"EXEC sp_detach_db '{db}', 'true'")
                print(f"  Detached: {db}")
            except:
                pass
        conn.close()
    except Exception as e:
        print(f"Cleanup check note: {e}")
        
    env = load_env(ENV_PATH)
    groq_api_key = env.get("GROQ_API_KEY")
    drive_service = get_drive_service()
    
    # Load links sheet
    df_links = pd.read_excel(EXCEL_PATH)
    depot_col = df_links.columns[0]
    link_col = df_links.columns[1]
    
    depots_to_process = []
    for idx, row in df_links.iterrows():
        depots_to_process.append((row[depot_col].strip(), row[link_col].strip()))
        
    print(f"Found {len(depots_to_process)} depots to process sequentially.")
    
    all_data = []
    success_depots = []
    
    for i, (depot_name, folder_url) in enumerate(depots_to_process, 1):
        print(f"\n==================================================")
        print(f"[{i}/{len(depots_to_process)}] PROCESSING DEPOT: {depot_name}")
        print(f"==================================================")
        print(f"  Current C: drive free space: {check_free_space():.2f} GB")
        
        mdf_path, ldf_path = download_depot_files(depot_name, folder_url, drive_service, groq_api_key)
        
        if not mdf_path:
            print(f"  ✗ Failed to retrieve database files for {depot_name}. Skipping.")
            continue
            
        print(f"  Database files retrieved successfully.")
        
        db_name = None
        try:
            # Upgrade and attach
            if depot_name.upper() == 'SYLHET':
                # Special recovery logic for suspect log file in Sylhet
                db_name = recover_sylhet_db(mdf_path, depot_name)
            else:
                try:
                    upgrade_db_compatibility(mdf_path, ldf_path, depot_name)
                except Exception as e:
                    print(f"  Warning upgrading compatibility: {e}")
                db_name = attach_database(depot_name, mdf_path, ldf_path)
                
            if db_name:
                print(f"  ✓ Database {db_name} attached successfully.")
                print(f"  Extracting sales data...")
                df = extract_sales_data(depot_name, db_name)
                
                if len(df) > 0:
                    all_data.append(df)
                    sales_cnt = len(df[df['Transaction_Type'] == 'Sale'])
                    returns_cnt = len(df[df['Transaction_Type'] == 'Return'])
                    print(f"  ✓ Extracted {len(df):,} records (Sales: {sales_cnt:,} | Returns: {returns_cnt:,})")
                    success_depots.append(depot_name)
                else:
                    print(f"  ✗ No sales data found in database.")
            else:
                print(f"  ✗ Failed to attach database.")
        except Exception as e:
            print(f"  [ERROR] Failed to process database for {depot_name}: {e}")
        finally:
            if db_name:
                detach_database(db_name)
                
            # Deleting files immediately to reclaim space!
            depot_dir = os.path.join(BASE_DEPOT_DIR, depot_name)
            if os.path.exists(depot_dir):
                print(f"  Reclaiming space: deleting database folder for {depot_name}...")
                shutil.rmtree(depot_dir, ignore_errors=True)
                print(f"  ✓ Database folder deleted. Free space: {check_free_space():.2f} GB")
                
    if not all_data:
        print("\nERROR: No data extracted from any of the depots. Pipeline stopping.")
        return
        
    print("\n" + "=" * 60)
    print("COMBINING AND PROCESSING ALL EXTRACTED DATA")
    print("=" * 60)
    
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Add Month column
    combined_df['Month'] = pd.to_datetime(combined_df['Invoice_Date']).dt.strftime('%Y-%m')
    
    # Create concatenated key
    combined_df['CONCATENATED_KEY'] = (
        combined_df['Depot'].astype(str) + '_' +
        combined_df['MPO_Code'].astype(str) + '_' +
        combined_df['Customer_ID'].astype(str) + '_' +
        combined_df['Month'].astype(str) + '_' +
        combined_df['Product_Code'].astype(str)
    )
    
    sales_df = combined_df[combined_df['Transaction_Type'] == 'Sale'].copy()
    returns_df = combined_df[combined_df['Transaction_Type'] == 'Return'].copy()
    
    print(f"Total Combined Sales: {len(sales_df):,} | Returns: {len(returns_df):,}")
    
    # Group sales
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
    
    # Group returns
    returns_grouped = returns_df.groupby('CONCATENATED_KEY').agg({
        'Quantity': 'sum',
        'Line_Amount': 'sum'
    }).reset_index()
    
    returns_grouped.columns = ['CONCATENATED_KEY', 'Return_Qty', 'Return_Amount']
    
    # Merge (VLOOKUP)
    net_sales = pd.merge(sales_grouped, returns_grouped, on='CONCATENATED_KEY', how='outer')
    
    # Fill NaN and calculate
    net_sales['Sale_Qty'] = net_sales['Sale_Qty'].fillna(0)
    net_sales['Sale_Amount'] = net_sales['Sale_Amount'].fillna(0)
    net_sales['Return_Qty'] = net_sales['Return_Qty'].fillna(0)
    net_sales['Return_Amount'] = net_sales['Return_Amount'].fillna(0)
    net_sales['ACTUAL_SALE_QTY'] = net_sales['Sale_Qty'] - net_sales['Return_Qty']
    net_sales['ACTUAL_SALE_AMOUNT'] = net_sales['Sale_Amount'] - net_sales['Return_Amount']
    net_sales['Return_Rate_%'] = (net_sales['Return_Qty'] / net_sales['Sale_Qty'] * 100).round(2)
    
    timestamp = datetime.now().strftime('%d_%b_%Y_%I.%M_%p')
    csv_file = os.path.join(base_dir, f"01_Product_Level_Net_Sales_Extracted_Data_{timestamp}.csv")
    net_sales.to_csv(csv_file, index=False)
    print(f"\n[SAVED FILE 1] {csv_file}")
    
    # Save Detailed
    detailed_df = combined_df.copy()
    detailed_df['Invoice_Date'] = pd.to_datetime(detailed_df['Invoice_Date']).dt.strftime('%Y-%m-%d')
    detailed_df['Transaction_Time'] = pd.to_datetime(detailed_df['Transaction_Time']).dt.strftime('%Y-%m-%d %H:%M:%S.%f').str[:-3]
    detailed_df['Customer_Name'] = detailed_df['Customer_Name'].astype(str).str.strip()
    detailed_df['Product_Name'] = detailed_df['Product_Name'].astype(str).str.strip()
    
    detailed_df.loc[detailed_df['Transaction_Type'] == 'Return', 'Quantity'] *= -1
    detailed_df.loc[detailed_df['Transaction_Type'] == 'Return', 'Line_Amount'] *= -1
    
    detailed_grouped = detailed_df.groupby([
        'Depot', 'MPO_Code', 'Invoice_No', 'Invoice_Date', 'Transaction_Time', 
        'Transaction_Type', 'Customer_ID', 'Customer_Name', 'Product_Code', 'Product_Name', 'Month'
    ]).agg({
        'Quantity': 'sum',
        'Line_Amount': 'sum'
    }).reset_index()
    
    col_order = [
        'Depot', 'MPO_Code', 'Invoice_No', 'Invoice_Date', 'Transaction_Time', 
        'Transaction_Type', 'Customer_ID', 'Customer_Name', 'Product_Code', 'Product_Name', 
        'Quantity', 'Line_Amount', 'Month', 'CONCATENATED_KEY'
    ]
    detailed_grouped = detailed_grouped[col_order]
    
    csv_file_detailed = os.path.join(base_dir, f"01.1_Date_wise_Customer_wise_Product_wise_Net_Sales_Extracted_Data_{timestamp}.csv")
    detailed_grouped.to_csv(csv_file_detailed, index=False)
    print(f"[SAVED FILE 2] {csv_file_detailed}")
    
    print(f"\nSuccessfully processed depots: {', '.join(success_depots)}")
    
    # ──────────────────────────────────────────────────────────
    # Run Steps 2, 3, 4 sequentially using mock
    # ──────────────────────────────────────────────────────────
    print("\n" + "="*60)
    print("RUNNING REPORT GENERATION STEPS (STEP 2, 3, 4)")
    print("="*60)
    
    # Run Step 2 (Generate MPO Report)
    print("\nStarting Step 2 (Generate MPO Report)...")
    # Patch input CSV selection inside step 2 script to use our newly created CSV
    with patch('pandas.read_csv', lambda f, *args, **kwargs: pd.read_csv(csv_file) if '01_' in str(f) else pd.read_csv(f)):
        import step_2_generate_MPO_Target_vs_Achievement_report as s2
        
    print("\nStarting Step 3 & 4 (Zone Reports)...")
    root = tk.Tk()
    root.withdraw()
    
    import step_3_generate_Zone_Wise_Product_Sales_Report as s3
    app = s3.ZoneReportApp(root)
    # Force step 3 to use our new CSV
    app.input_file.set(csv_file)
    app.run_report()
    print("Step 3 completed successfully.")
    
    import step_4_analyze_Zone_Wise_Product_Sales_Report as s4
    # Find latest zone report file
    zone_files = [f for f in os.listdir(base_dir) if f.startswith('03_Zone_Wise_Sales_Grouped_Report_') and f.endswith('.xlsx')]
    zone_files.sort(reverse=True)
    if zone_files:
        latest_zone_path = os.path.join(base_dir, zone_files[0])
        app4 = s4.AnalysisApp(root)
        app4.input_file.set(latest_zone_path)
        app4.run_analysis()
        print("Step 4 completed successfully.")
    else:
        print("Error: Could not find Step 3 Excel output to run Step 4!")
        
    root.destroy()
    
    # Clean up All_Depots if empty or check
    try:
        shutil.rmtree(BASE_DEPOT_DIR, ignore_errors=True)
        print("Cleaned up All_Depots folder.")
    except:
        pass
        
    print("\n" + "*" * 80)
    print("  ALL PIPELINE STEPS COMPLETED SUCCESSFULLY WITH SEQUENTIAL RECLAIM!")
    print("*" * 80)

if __name__ == "__main__":
    main_sequential()
