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
    results = drive_service.files().list(
        q=query,
        pageSize=100,
        fields="files(id, name, mimeType, createdTime, modifiedTime, size)"
    ).execute()
    return results.get('files', [])

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
    
    response = requests.post(url, headers=headers, json=data, timeout=30)
    response.raise_for_status()
    result = response.json()
    content = result['choices'][0]['message']['content']
    return json.loads(content)

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

def download_and_upgrade_depot(depot_name, folder_url, drive_service, groq_api_key):
    print(f"\n" + "="*50)
    print(f"Downloading & Upgrading Depot: {depot_name}")
    print("="*50)
    
    depot_dir = os.path.join(BASE_DEPOT_DIR, depot_name)
    data_dir = os.path.join(depot_dir, "Data")
    final_mdf_path = os.path.join(data_dir, "ERPonTheNet_Data.MDF")
    final_ldf_path = os.path.join(data_dir, "ERPonTheNet_log.LDF")
    
    if os.path.exists(final_mdf_path):
        print(f"  Local MDF file already exists at: {final_mdf_path}. Skipping download.")
        if not os.path.exists(final_ldf_path):
            final_ldf_path = None
        # Make sure compatibility is upgraded just in case
        try:
            upgrade_db_compatibility(final_mdf_path, final_ldf_path, depot_name)
        except Exception as e:
            print(f"  Warning: Compatibility upgrade failed (might already be upgraded): {e}")
        return True

    folder_id_match = re.search(r'folders/([a-zA-Z0-9-_]+)', str(folder_url))
    if not folder_id_match:
        print(f"  Error: Invalid folder URL: {folder_url}")
        return False
        
    folder_id = folder_id_match.group(1)
    items = list_drive_folder_items(drive_service, folder_id)
    if not items:
        print(f"  No files or folders found in drive folder.")
        return False
        
    print("  Asking Groq LLM to verify and select the correct file...")
    decision = get_best_item_from_groq(depot_name, items, groq_api_key)
    print(f"  Groq Decision: Selected '{decision.get('selected_item_name')}' ({decision.get('selected_item_type')})")
    
    selected_name = decision.get("selected_item_name")
    selected_id = decision.get("selected_item_id")
    selected_type = decision.get("selected_item_type")
    
    if not selected_id:
        print(f"  Error: Groq failed to select a valid ID.")
        return False
        
    os.makedirs(data_dir, exist_ok=True)
    temp_download_dir = os.path.join(depot_dir, "Temp_Download")
    os.makedirs(temp_download_dir, exist_ok=True)
    
    rclone_exe = find_rclone_executable()
    mdf_local_path = None
    ldf_local_path = None
    
    if selected_type == 'file' and selected_name.lower().endswith('.zip'):
        zip_path = os.path.join(temp_download_dir, selected_name)
        remote_file_path = f"{RCLONE_REMOTE_NAME},root_folder_id={folder_id}:{selected_name}"
        cmd = [rclone_exe, "copyto", remote_file_path, zip_path]
        print(f"  Running rclone to download ZIP...")
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
        cmd = [
            rclone_exe, "copy",
            f"{RCLONE_REMOTE_NAME},root_folder_id={selected_id}:",
            temp_download_dir,
            "--include", "*.{mdf,ldf,MDF,LDF}",
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
            cmd = [rclone_exe, "copyto", remote_mdf_path, temp_mdf_path]
            print(f"  Downloading MDF file directly...")
            subprocess.run(cmd, check=True)
            mdf_local_path = temp_mdf_path
            
            for item in items:
                if item['name'].lower().endswith('.ldf') and 'erponthenet' in item['name'].lower():
                    temp_ldf_path = os.path.join(temp_download_dir, item['name'])
                    remote_ldf_path = f"{RCLONE_REMOTE_NAME},root_folder_id={folder_id}:{item['name']}"
                    cmd = [rclone_exe, "copyto", remote_ldf_path, temp_ldf_path]
                    print(f"  Downloading LDF file directly...")
                    subprocess.run(cmd, check=True)
                    ldf_local_path = temp_ldf_path
                    break
        else:
            print(f"  Error: Unsupported file/folder selection: {selected_name}")
            return False

    if not mdf_local_path or not os.path.exists(mdf_local_path):
        print("  Error: MDF file was not successfully downloaded or extracted.")
        return False
        
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
    
    upgrade_db_compatibility(final_mdf_path, final_ldf_path, depot_name)
    return True

# ══════════════════════════════════════════════════════════════════
#  Pipeline Execution Steps
# ══════════════════════════════════════════════════════════════════

def run_step_1(base_dir):
    print("\n" + "="*60)
    print("STEP 1: Extract Product Level Net Sales from Database")
    print("="*60)
    import step_1_extract_Product_Level_Net_Sales_csv as s1
    
    class MockGUI:
        def __init__(self):
            # Point directory to googleDrive/All_Depots where database files were downloaded
            self.all_depots_folder = os.path.join(base_dir, "googleDrive", "All_Depots")
            self.output_dir = base_dir
            self.depot_folders = []
            if os.path.exists(self.all_depots_folder):
                for d in os.listdir(self.all_depots_folder):
                    dpath = os.path.join(self.all_depots_folder, d)
                    if os.path.isdir(dpath):
                        self.depot_folders.append(dpath)
            
            class DummyBtn:
                def config(self, **kwargs): pass
            self.start_btn = DummyBtn()
            
            class DummyRoot:
                def destroy(self): pass
                def mainloop(self):
                    if hasattr(self.parent, 'run_processing'):
                        self.parent.run_processing()
            
            self.root = DummyRoot()
            self.root.parent = self
            
        def log(self, msg): 
            print(f"  [LOG] {msg}")
            
        def update_progress(self, val, msg): 
            print(f"  [{val}%] {msg}")

    mock_gui = MockGUI()
    if not mock_gui.depot_folders:
        print("  [ERROR] No valid depots found in 'googleDrive/All_Depots' folder.")
        return False

    def mock_select_folders():
        return mock_gui

    # Patch the GUI creation and messageboxes to execute headlessly
    with patch('step_1_extract_Product_Level_Net_Sales_csv.select_folders_gui', side_effect=mock_select_folders), \
         patch('tkinter.messagebox.showinfo', lambda t, m: print(f"\n  [SUCCESS] {m.split(chr(10))[0]}")), \
         patch('tkinter.messagebox.showerror', lambda t, m: print(f"\n  [ERROR] {m}")):
         
         s1.process_all_depots()
         
    return True

def run_step_2():
    print("\n" + "="*60)
    print("STEP 2: Generate MPO Target vs Achievement")
    print("="*60)
    import step_2_generate_MPO_Target_vs_Achievement_report as s2
    return True

def run_step_3(root):
    print("\n" + "="*60)
    print("STEP 3: Generate Zone Wise Product Sales Report")
    print("="*60)
    import step_3_generate_Zone_Wise_Product_Sales_Report as s3
    
    app = s3.ZoneReportApp(root)
    
    if not app.input_file.get():
        print("  [ERROR] Could not auto-detect input file (CSV) from Step 1!")
        return False

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

def run_step_4(root):
    print("\n" + "="*60)
    print("STEP 4: Analyze Zone Wise Report (10 Parameters)")
    print("="*60)
    import step_4_analyze_Zone_Wise_Product_Sales_Report as s4
    
    app = s4.ZoneDataAnalyzerApp(root)
    
    if not app.input_file.get():
        print("  [ERROR] Could not auto-detect input file (Excel) from Step 3!")
        return False

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
    
    # ──────────────────────────────────────────────────────────
    # Phase 0: Download and Upgrade Depots from Google Drive
    # ──────────────────────────────────────────────────────────
    print("\n" + "="*60)
    print("PHASE 0: Download and Upgrade Depots from Google Drive")
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
    
    # Download and upgrade all depots
    success_count = 0
    fail_count = 0
    
    for depot_name, folder_url in depots_to_process:
        try:
            success = download_and_upgrade_depot(depot_name, folder_url, drive_service, groq_api_key)
            if success:
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            print(f"Error processing {depot_name}: {e}")
            fail_count += 1
            
    print(f"\n==================================================")
    print(f"Download & Upgrade Phase Summary:")
    print(f"Successfully downloaded/upgraded: {success_count}")
    print(f"Failed: {fail_count}")
    print(f"==================================================")
    
    if fail_count > 0:
        print("WARNING: Some depots failed to download or upgrade. Proceeding with successfully retrieved depots.")
    if success_count == 0:
        print("ERROR: No depots were successfully downloaded/upgraded. Pipeline stopping.")
        return
        
    # ──────────────────────────────────────────────────────────
    # Run Steps 1-4
    # ──────────────────────────────────────────────────────────
    
    # Run Step 1 (Extract Sales CSV)
    if not run_step_1(base_dir):
        print("\nPipeline stopped at Step 1.")
        return
        
    print("\nWaiting 5 seconds before next step...")
    time.sleep(5)
    
    # Run Step 2 (Generate MPO Report)
    if not run_step_2():
        print("\nPipeline stopped at Step 2.")
        return
        
    print("\nWaiting 5 seconds before next step...")
    time.sleep(5)
    
    # Create hidden TKinter root window for Step 3 & 4 GUI apps
    root = tk.Tk()
    root.withdraw()
    
    # Run Step 3 (Zone Wise Sales Report)
    if not run_step_3(root):
        print("\nPipeline stopped at Step 3.")
        root.destroy()
        return
        
    print("\nWaiting 5 seconds before next step...")
    time.sleep(5)
    
    # Run Step 4 (10 Parameter Analyzed Report)
    if not run_step_4(root):
        print("\nPipeline stopped at Step 4.")
        root.destroy()
        return
        
    root.destroy()
    
    # ──────────────────────────────────────────────────────────
    # Cleanup local SQLEXPRESS and free up disk space
    # ──────────────────────────────────────────────────────────
    print("\n" + "="*60)
    print("CLEANUP PHASE: Detaching databases and releasing disk space")
    print("="*60)
    
    # Re-call Step 1 cleanup method to detach all attached *_DB databases
    try:
        import step_1_extract_Product_Level_Net_Sales_csv as s1
        s1.cleanup_existing_databases()
    except Exception as e:
        print(f"Warning detaching databases: {e}")
        
    # Delete All_Depots directory completely to reclaim disk space
    if os.path.exists(BASE_DEPOT_DIR):
        print(f"Deleting downloaded database files folder to free space: {BASE_DEPOT_DIR}...")
        try:
            shutil.rmtree(BASE_DEPOT_DIR, ignore_errors=True)
            print("✓ Local database files deleted successfully.")
        except Exception as e:
            print(f"Warning deleting directory: {e}")
            
    print("\n" + "*" * 80)
    print("  ALL STEPS COMPLETED SUCCESSFULLY!")
    print("*" * 80)
    print("\nAll output report files have been successfully generated in the workspace.")

if __name__ == "__main__":
    main()
