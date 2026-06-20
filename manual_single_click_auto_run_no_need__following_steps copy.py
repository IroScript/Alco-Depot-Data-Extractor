import os
import io
import re
import sys
import time
import json
import zipfile
import shutil
import requests
import pyodbc
import pandas as pd
import subprocess
import tkinter as tk
from datetime import datetime
from unittest.mock import patch
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Reconfigure console output encoding to prevent Windows crash on non-ASCII characters
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
    except:
        pass

# ══════════════════════════════════════════════════════════════════
#  Google Drive & Upgrade Configuration
# ══════════════════════════════════════════════════════════════════
CLIENT_SECRET_PATH = r'c:\Users\Irak\Desktop\Barishal April Data\googleDrive\client_secret_1076305260584-t28u3map5uuuqvdk28mrqjk0oigbadh4.apps.googleusercontent.com.json'
TOKEN_PICKLE_PATH = r'c:\Users\Irak\Desktop\Barishal April Data\googleDrive\token.pickle'
EXCEL_PATH = r'c:\Users\Irak\Desktop\Barishal April Data\googleDrive\gDriveDepotLinks.xlsx'
ENV_PATH = r'c:\Users\Irak\Desktop\Barishal April Data\googleDrive\env'
BASE_DEPOT_DIR = r'c:\Users\Irak\Desktop\Barishal April Data\googleDrive\All_Depots'
RCLONE_REMOTE_NAME = 'grive_new'
SQL_SERVER = r'.\SQLEXPRESS'

def find_rclone_executable():
    if shutil.which("rclone"):
        return "rclone"
    common_paths = [r"C:\rclone\rclone.exe"]
    try:
        for item in os.listdir("C:\\"):
            if "rclone" in item.lower():
                full_path = os.path.join("C:\\", item, "rclone.exe")
                if os.path.exists(full_path):
                    common_paths.append(full_path)
    except:
        pass
    for path in common_paths:
        if os.path.exists(path):
            return path
    return "rclone"

def load_env(env_path):
    env = {}
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        env[parts[0].strip()] = parts[1].strip()
    return env

def get_drive_service():
    creds_path = r'c:\Users\Irak\Desktop\Barishal April Data\FieldEdit\alco-pharma-cf4b49e394bb.json'
    scopes = ['https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
    return build('drive', 'v3', credentials=creds)

def list_drive_folder_items(drive_service, folder_id):
    query = f"'{folder_id}' in parents and trashed = false"
    for attempt in range(1, 4):
        try:
            results = drive_service.files().list(
                q=query,
                pageSize=100,
                fields="files(id, name, mimeType, createdTime, modifiedTime, size)"
            ).execute()
            return results.get('files', [])
        except Exception as e:
            print(f"  [Warning] Google Drive API list failed (Attempt {attempt}/3): {e}")
            if attempt < 3:
                time.sleep(5)
            else:
                raise e

def get_best_item_from_groq(depot_name, items, groq_api_key):
    items_summary = []
    for item in items:
        size_mb = f"{float(item.get('size', 0))/(1024*1024):.2f} MB" if 'size' in item else "DIR"
        items_summary.append(
            f"Name: {item['name']}, ID: {item['id']}, Type: {item['mimeType']}, Size: {size_mb}, Modified: {item.get('modifiedTime', 'N/A')}"
        )
    
    items_str = "\n".join(items_summary)
    
    prompt = f"""
You are an expert AI agent. We are automating the process of downloading the latest database backup files for a specific depot.
Target Depot Name: {depot_name}

Here is a list of available files and folders in the Google Drive parent folder for this depot:
{items_str}

Please analyze the list of items and identify which item we should download or enter to retrieve the database files.
Guidelines:
1. We want the database backup file. This can be inside a subfolder (like 'Data') or it could be a zip file (like '03.06.2026(Sylhet).zip').
2. DHAKA-1 and DHAKA-2 share the same folder URL.
   - For DHAKA-1: Select the item/folder representing Dhaka 1 (e.g. name contains 'DK 1', 'DK1', 'Dhaka 1').
   - For DHAKA-2: Select the item/folder representing Dhaka 2 (e.g. name contains 'DK-2', 'DK2', 'Dhaka 2').
3. For other depots (e.g. JASHORE, FARIDPUR, SYLHET, etc.), pick the folder or archive file that matches the depot and is the latest upload.
   - If there is a direct 'Data' folder and no other folders, select it.
   - If there is a zip file containing the depot's database, select it.
   - If there is a folder with a name like 'Data-03.06.26' or 'Closing Data May-26', select it.

Return a JSON object with the following fields:
- "selected_item_name": The exact name of the selected file or folder.
- "selected_item_id": The ID of the selected file or folder.
- "selected_item_type": Either "folder" or "file".
- "reasoning": A brief explanation of why you selected this item.
"""
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "openai/gpt-oss-120b",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "response_format": {"type": "json_object"}
    }
    
    for attempt in range(1, 4):
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            content = result['choices'][0]['message']['content']
            return json.loads(content)
        except Exception as e:
            print(f"  [Warning] Groq API call failed (Attempt {attempt}/3): {e}")
            if attempt < 3:
                time.sleep(5)
            else:
                raise e

def grant_sql_server_permissions(folder_path):
    try:
        accounts = [
            'NT SERVICE\\MSSQL$SQLEXPRESS',
            'NT SERVICE\\MSSQLSERVER',
            'NT AUTHORITY\\NETWORK SERVICE',
            'NT AUTHORITY\\SYSTEM'
        ]
        for account in accounts:
            try:
                cmd = f'icacls "{folder_path}" /grant "{account}:(OI)(CI)F" /T /Q'
                subprocess.run(cmd, shell=True, capture_output=True, timeout=10)
            except:
                pass
    except Exception as e:
        print(f"Warning: Permissions check failed: {e}")

def upgrade_db_compatibility(mdf_path, ldf_path, depot_name):
    db_name = f"{depot_name.upper().replace('-', '_')}_UPGRADE_DB"
    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SQL_SERVER};DATABASE=master;Trusted_Connection=yes;'
    
    conn = pyodbc.connect(conn_str)
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Drop/Detach if already exists
    cursor.execute(f"SELECT database_id FROM sys.databases WHERE name = '{db_name}'")
    if cursor.fetchone():
        print(f"  Database {db_name} already exists. Detaching first...")
        try:
            cursor.execute(f"ALTER DATABASE [{db_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
            cursor.execute(f"EXEC sp_detach_db '{db_name}', 'true'")
        except Exception as e:
            print(f"  Error detaching: {e}")
            
    # Attach database
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
        
    print(f"  Attaching {db_name} to SQLEXPRESS...")
    cursor.execute(attach_query)
    
    # Set compatibility level to 100
    print(f"  Upgrading compatibility level of {db_name} to 100...")
    cursor.execute(f"ALTER DATABASE [{db_name}] SET COMPATIBILITY_LEVEL = 100")
    
    # Detach database
    print(f"  Detaching database {db_name}...")
    cursor.execute(f"ALTER DATABASE [{db_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
    cursor.execute(f"EXEC sp_detach_db '{db_name}', 'true'")
    print(f"  [SUCCESS] {depot_name} compatibility upgraded successfully!")
    
    conn.close()

def recover_sylhet_db(mdf_path, depot_name):
    """Special recovery for SYLHET MDF file where log rebuild fails standard attach"""
    db_name = f"{depot_name.upper().replace('-', '_')}_DB"
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
    except:
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
    print(f"    [SUCCESS] Recovered and attached suspect database: {db_name}")
    
    conn.close()
    return db_name

def attach_database(depot_name, mdf_path, ldf_path):
    db_name = f"{depot_name.upper().replace('-', '_')}_DB"
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
    
    # ── CLEANUP LEFTOVER TEMP DOWNLOAD ON RERUN ──
    if os.path.exists(temp_download_dir):
        print(f"  Cleaning leftover Temp_Download directory: {temp_download_dir}...")
        shutil.rmtree(temp_download_dir, ignore_errors=True)
        
    os.makedirs(temp_download_dir, exist_ok=True)
    
    rclone_exe = find_rclone_executable()
    mdf_local_path = None
    ldf_local_path = None
    
    try:
        # Download ZIP file type
        if selected_type == 'file' and selected_name.lower().endswith('.zip'):
            zip_path = os.path.join(temp_download_dir, selected_name)
            remote_file_path = f"{RCLONE_REMOTE_NAME},root_folder_id={folder_id}:{selected_name}"
            # Added --progress flag for speed display
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
                            
        # Download folder type
        elif selected_type == 'folder':
            print("  Downloading MDF/LDF from folder...")
            cmd = [
                rclone_exe, "copy",
                "--progress",
                f"{RCLONE_REMOTE_NAME},root_folder_id={selected_id}:",
                temp_download_dir,
                "--include", "*erponthenet*",
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
        
        # Download single file type (direct MDF/LDF download)
        else:
            if selected_name.lower().endswith('.mdf'):
                temp_mdf_path = os.path.join(temp_download_dir, selected_name)
                remote_mdf_path = f"{RCLONE_REMOTE_NAME},root_folder_id={folder_id}:{selected_name}"
                # Added --progress flag for speed display
                cmd = [rclone_exe, "copyto", "--progress", remote_mdf_path, temp_mdf_path]
                print(f"  Downloading MDF file...")
                subprocess.run(cmd, check=True)
                mdf_local_path = temp_mdf_path
                
                for item in items:
                    if item['name'].lower().endswith('.ldf') and 'erponthenet' in item['name'].lower():
                        temp_ldf_path = os.path.join(temp_download_dir, item['name'])
                        remote_ldf_path = f"{RCLONE_REMOTE_NAME},root_folder_id={folder_id}:{item['name']}"
                        # Added --progress flag for speed display
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

def cleanup_all_attached_dbs():
    """Initial cleanup of any attached _DB databases to ensure clean slate"""
    print("Checking and cleaning up old databases from SQLEXPRESS...")
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
                print(f"  Detached legacy db: {db}")
            except:
                pass
        conn.close()
    except Exception as e:
        print(f"Cleanup check warning: {e}")

# ══════════════════════════════════════════════════════════════════
#  Pipeline Execution Steps
# ══════════════════════════════════════════════════════════════════

def run_step_2():
    print("\n" + "="*60)
    print("STEP 2: Generate MPO Target vs Achievement")
    print("="*60)
    import step_2_generate_MPO_Target_vs_Achievement_report as s2
    return True

def run_step_3(root, csv_file):
    print("\n" + "="*60)
    print("STEP 3: Generate Zone Wise Product Sales Report")
    print("="*60)
    import step_3_generate_Zone_Wise_Product_Sales_Report as s3
    
    app = s3.ZoneReportApp(root)
    
    # Force step 3 to use our new CSV
    app.input_file.set(csv_file)
    
    def on_success(title, msg):
        print(f"\n  [SUCCESS] {msg.split(chr(10))[0]}")
        
    def on_error(title, msg):
        print(f"\n  [ERROR] {msg}")

    def mock_show_success_dialog(out_path):
        print(f"\n  [SUCCESS] Zone Wise Sales Report saved to: {out_path}")

    class SyncThread:
        def __init__(self, target, *args, **kwargs):
            self.target = target
        def start(self):
            self.target()

    with patch('tkinter.messagebox.showinfo', side_effect=on_success), \
         patch('tkinter.messagebox.showerror', side_effect=on_error), \
         patch('threading.Thread', SyncThread), \
         patch.object(s3.ZoneReportApp, 'show_success_dialog', mock_show_success_dialog):
         
         app.run_process()
         
    # Clean up Step 3 widgets
    for widget in root.winfo_children():
        try:
            widget.destroy()
        except:
            pass
            
    return True

def run_step_4(root, excel_file):
    print("\n" + "="*60)
    print("STEP 4: Analyze Zone Wise Report (10 Parameters)")
    print("="*60)
    import step_4_analyze_Zone_Wise_Product_Sales_Report as s4
    
    app = s4.ZoneDataAnalyzerApp(root)
    
    # Force step 4 to use the specified Excel file from Step 3
    app.input_file.set(excel_file)

    def on_success(title, msg):
        print(f"\n  [SUCCESS] {msg.split(chr(10))[0]}")
        
    def on_error(title, msg):
        print(f"\n  [ERROR] {msg}")

    def mock_show_success_dialog(out_path):
        print(f"\n  [SUCCESS] 10 Parameter Analysis saved to: {out_path}")

    class SyncThread:
        def __init__(self, target, *args, **kwargs):
            self.target = target
        def start(self):
            self.target()

    with patch('tkinter.messagebox.showinfo', side_effect=on_success), \
         patch('tkinter.messagebox.showerror', side_effect=on_error), \
         patch('threading.Thread', SyncThread), \
         patch.object(s4.ZoneDataAnalyzerApp, 'show_success_dialog', mock_show_success_dialog):
         
         app.run_process()
         
    # Clean up Step 4 widgets
    for widget in root.winfo_children():
        try:
            widget.destroy()
        except:
            pass
            
    return True

# ══════════════════════════════════════════════════════════════════
#  Main Orchestrator
# ══════════════════════════════════════════════════════════════════

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    print("*" * 80)
    print("  FAST SALES DATA EXTRACTOR & ANALYZER - FULL AUTO RUN")
    print("*" * 80)
    
    # Detach old databases to clear locks
    cleanup_all_attached_dbs()
    
    # ──────────────────────────────────────────────────────────
    # Phase 0 & 1: Sequential space-saving extraction with Resume checkpointing
    # ──────────────────────────────────────────────────────────
    print("\n" + "="*60)
    print("PHASE 0 & 1: Sequential Database Downloads & Extraction")
    print("="*60)
    
    env = load_env(ENV_PATH)
    groq_api_key = env.get("GROQ_API_KEY")
    if not groq_api_key:
        print("ERROR: GROQ_API_KEY not found in env file.")
        return
        
    if not os.path.exists(CLIENT_SECRET_PATH):
        print(f"ERROR: Client secret file not found at {CLIENT_SECRET_PATH}")
        return
        
    drive_service = get_drive_service()
    
    # Load Excel Links
    df_links = pd.read_excel(EXCEL_PATH)
    depot_col = df_links.columns[0]
    link_col = df_links.columns[1]
    
    depots_to_process = []
    for idx, row in df_links.iterrows():
        depots_to_process.append((row[depot_col].strip(), row[link_col].strip()))
        
    print(f"Found {len(depots_to_process)} depots in links Excel.")
    
    # Create checkpoint directory for sequential resume
    checkpoint_dir = os.path.join(BASE_DEPOT_DIR, "extracted_temp")
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    all_data = []
    success_depots = []
    
    for i, (depot_name, folder_url) in enumerate(depots_to_process, 1):
        print(f"\n" + "-"*50)
        print(f"[{i}/{len(depots_to_process)}] DEPOT: {depot_name}")
        print(f"-"*50)
        
        checkpoint_file = os.path.join(checkpoint_dir, f"{depot_name}.csv")
        
        # ── CHECKPOINT RESUME CHECK ──
        if os.path.exists(checkpoint_file):
            print(f"  [RESUME Checkpoint] Extracted data CSV already exists at: {checkpoint_file}. Loading cache...")
            try:
                df = pd.read_csv(checkpoint_file)
                if len(df) > 0:
                    all_data.append(df)
                    success_depots.append(depot_name)
                    print(f"  ✓ Loaded {len(df):,} cached records from checkpoint.")
                    continue
            except Exception as e:
                print(f"  Warning reading checkpoint CSV: {e}. Re-extracting...")
        
        # Check free disk space before processing next database
        free_space = check_free_space()
        print(f"  C: Drive Free Space: {free_space:.2f} GB")
        if free_space < 1.0:
            print("  [WARNING] C: Drive is extremely low on space (< 1.0 GB). Proceeding carefully.")
            
        mdf_path, ldf_path = download_depot_files(depot_name, folder_url, drive_service, groq_api_key)
        
        if not mdf_path or not os.path.exists(mdf_path):
            print(f"  ✗ Failed to retrieve database files for {depot_name}. Skipping.")
            continue
            
        print(f"  Database files retrieved successfully.")
        
        db_name = None
        try:
            # Upgrade compatibility and attach
            if depot_name.upper() == 'SYLHET':
                # Special recovery for suspect database missing transaction logs in Sylhet
                db_name = recover_sylhet_db(mdf_path, depot_name)
            else:
                try:
                    upgrade_db_compatibility(mdf_path, ldf_path, depot_name)
                except Exception as e:
                    print(f"  Warning upgrading compatibility: {e}")
                db_name = attach_database(depot_name, mdf_path, ldf_path)
                
            if db_name:
                print(f"  ✓ Attached database {db_name} successfully.")
                print(f"  Extracting sales & returns data...")
                df = extract_sales_data(depot_name, db_name)
                
                if len(df) > 0:
                    # Save checkpoint CSV
                    df.to_csv(checkpoint_file, index=False)
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
                
            # ── RECLAIM DISK SPACE IMMEDIATELY ──
            depot_folder = os.path.join(BASE_DEPOT_DIR, depot_name)
            if os.path.exists(depot_folder):
                print(f"  Reclaiming space: deleting local MDF/LDF files for {depot_name}...")
                try:
                    shutil.rmtree(depot_folder, ignore_errors=True)
                    print(f"  ✓ Deleted. Current Free Space: {check_free_space():.2f} GB")
                except Exception as e:
                    print(f"  Warning deleting folder: {e}")
                    
    if not all_data:
        print("\nERROR: No data extracted from any of the depots. Pipeline stopping.")
        return
        
    # ──────────────────────────────────────────────────────────
    # Combine and perform exact OUTER merge (avoiding returns loss)
    # ──────────────────────────────────────────────────────────
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
    
    # Group returns keeping metadata to reconstruct missing fields for returns-only records
    returns_grouped = returns_df.groupby('CONCATENATED_KEY').agg({
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
    
    returns_grouped.columns = [
        'CONCATENATED_KEY', 'Depot_ret', 'MPO_Code_ret', 'Customer_ID_ret', 'Customer_Name_ret',
        'Month_ret', 'Product_Code_ret', 'Product_Name_ret', 'Return_Qty', 'Return_Amount'
    ]
    
    # Merge using how='outer' to prevent return loss
    net_sales = pd.merge(sales_grouped, returns_grouped, on='CONCATENATED_KEY', how='outer')
    
    # Fill NaN and calculate
    net_sales['Sale_Qty'] = net_sales['Sale_Qty'].fillna(0)
    net_sales['Sale_Amount'] = net_sales['Sale_Amount'].fillna(0)
    net_sales['Return_Qty'] = net_sales['Return_Qty'].fillna(0)
    net_sales['Return_Amount'] = net_sales['Return_Amount'].fillna(0)
    
    # Reconstruct metadata columns from returns if sales were empty
    for col in ['Depot', 'MPO_Code', 'Customer_ID', 'Customer_Name', 'Month', 'Product_Code', 'Product_Name']:
        net_sales[col] = net_sales[col].fillna(net_sales[col + '_ret'])
        
    # Drop helper columns
    net_sales.drop(columns=[col + '_ret' for col in ['Depot', 'MPO_Code', 'Customer_ID', 'Customer_Name', 'Month', 'Product_Code', 'Product_Name']], inplace=True)
    
    net_sales['ACTUAL_SALE_QTY'] = net_sales['Sale_Qty'] - net_sales['Return_Qty']
    net_sales['ACTUAL_SALE_AMOUNT'] = net_sales['Sale_Amount'] - net_sales['Return_Amount']
    net_sales['Return_Rate_%'] = (net_sales['Return_Qty'] / net_sales['Sale_Qty'] * 100).round(2).fillna(0)
    net_sales['Return_Rate_%'] = net_sales['Return_Rate_%'].replace([float('inf'), float('-inf')], 0)
    
    timestamp = datetime.now().strftime('%d_%b_%Y_%I.%M_%p')
    csv_file = os.path.join(base_dir, f"01_Product_Level_Net_Sales_Extracted_Data_{timestamp}.csv")
    net_sales.to_csv(csv_file, index=False)
    print(f"\n[SAVED FILE 1] {csv_file}")
    
    # Save Detailed (Detailed Raw Transactions)
    detailed_df = combined_df.copy()
    detailed_df['Invoice_Date'] = pd.to_datetime(detailed_df['Invoice_Date']).dt.strftime('%Y-%m-%d')
    detailed_df['Transaction_Time'] = pd.to_datetime(detailed_df['Transaction_Time']).dt.strftime('%Y-%m-%d %H:%M:%S.%f').str[:-3]
    detailed_df['Customer_Name'] = detailed_df['Customer_Name'].astype(str).str.strip()
    detailed_df['Product_Name'] = detailed_df['Product_Name'].astype(str).str.strip()
    
    # Format returns with negative quantities/amounts for invoice view
    detailed_df.loc[detailed_df['Transaction_Type'] == 'Return', 'Quantity'] *= -1
    detailed_df.loc[detailed_df['Transaction_Type'] == 'Return', 'Line_Amount'] *= -1
    
    detailed_grouped = detailed_df.groupby([
        'Depot', 'MPO_Code', 'Invoice_No', 'Invoice_Date', 'Transaction_Time', 
        'Transaction_Type', 'Customer_ID', 'Customer_Name', 'Product_Code', 'Product_Name', 'Month', 'CONCATENATED_KEY'
    ]).agg({
        'Quantity': 'sum',
        'Line_Amount': 'sum'
    }).reset_index()
    
    # Place CONCATENATED_KEY as the very first column
    col_order = [
        'CONCATENATED_KEY', 'Depot', 'MPO_Code', 'Invoice_No', 'Invoice_Date', 'Transaction_Time', 
        'Transaction_Type', 'Customer_ID', 'Customer_Name', 'Product_Code', 'Product_Name', 
        'Quantity', 'Line_Amount', 'Month'
    ]
    detailed_grouped = detailed_grouped[col_order]
    
    csv_file_detailed = os.path.join(base_dir, f"01.1_Date_wise_Customer_wise_Product_wise_Net_Sales_Extracted_Data_{timestamp}.csv")
    detailed_grouped.to_csv(csv_file_detailed, index=False)
    print(f"[SAVED FILE 2] {csv_file_detailed}")
    
    print(f"\nSuccessfully processed depots: {', '.join(success_depots)}")
    
    # Clean up checkpoint folder
    if os.path.exists(checkpoint_dir):
        shutil.rmtree(checkpoint_dir, ignore_errors=True)
        print("Cleaned up checkpoint temporary CSV files.")
        
    print("\nWaiting 5 seconds before next step...")
    time.sleep(5)
    
    # ──────────────────────────────────────────────────────────
    # Run Steps 2, 3, and 4
    # ──────────────────────────────────────────────────────────
    
    # Run Step 2 (Generate MPO Report)
    # Patch glob.glob inside step 2 script to return our newly created CSV instead of globbing
    with patch('glob.glob', return_value=[csv_file]):
        run_step_2()
        
    print("\nWaiting 5 seconds before next step...")
    time.sleep(5)
    
    # Create hidden TKinter root window for Step 3 & 4 GUI apps
    root = tk.Tk()
    root.withdraw()
    
    # Run Step 3 (Zone Wise Sales Report)
    if not run_step_3(root, csv_file):
        print("\nPipeline stopped at Step 3.")
        root.destroy()
        return
        
    print("\nWaiting 5 seconds before next step...")
    time.sleep(5)
    
    # Find latest zone report file from Step 3
    zone_files = [f for f in os.listdir(base_dir) if f.startswith('03_Zone_Wise_Sales_Grouped_Report_') and f.endswith('.xlsx')]
    zone_files.sort(reverse=True)
    if zone_files:
        latest_zone_path = os.path.join(base_dir, zone_files[0])
        # Run Step 4 (10 Parameter Analyzed Report)
        if not run_step_4(root, latest_zone_path):
            print("\nPipeline stopped at Step 4.")
            root.destroy()
            return
    else:
        print("Error: Could not find Step 3 Excel output to run Step 4!")
        
    root.destroy()
    
    # ── FINAL CLEANUP ──
    cleanup_all_attached_dbs()
    if os.path.exists(BASE_DEPOT_DIR):
        print(f"Deleting downloaded database folder to reclaim disk space: {BASE_DEPOT_DIR}...")
        try:
            shutil.rmtree(BASE_DEPOT_DIR, ignore_errors=True)
            print("✓ Local database files deleted successfully.")
        except Exception as e:
            print(f"Warning deleting directory: {e}")
            
    print("\n" + "*" * 80)
    print("  ALL PIPELINE STEPS COMPLETED SUCCESSFULLY!")
    print("*" * 80)

if __name__ == "__main__":
    main()
