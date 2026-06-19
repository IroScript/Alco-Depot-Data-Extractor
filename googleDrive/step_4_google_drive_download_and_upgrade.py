import os
import io
import re
import json
import zipfile
import shutil
import requests
import pyodbc
import pandas as pd
import pickle
import subprocess
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload


# Configuration paths
CLIENT_SECRET_PATH = r'c:\Users\Irak\Desktop\Barishal April Data\googleDrive\client_secret_1076305260584-t28u3map5uuuqvdk28mrqjk0oigbadh4.apps.googleusercontent.com.json'
TOKEN_PICKLE_PATH = r'c:\Users\Irak\Desktop\Barishal April Data\googleDrive\token.pickle'
EXCEL_PATH = r'c:\Users\Irak\Desktop\Barishal April Data\googleDrive\gDriveDepotLinks.xlsx'
ENV_PATH = r'c:\Users\Irak\Desktop\Barishal April Data\googleDrive\env'
BASE_DEPOT_DIR = r'c:\Users\Irak\Desktop\Barishal April Data\googleDrive\All_Depots'
TARGET_UPLOAD_PARENT_ID = '17vBESDDaZL-Gf-0h4MzKZYrVRUxQD_2W'
RCLONE_REMOTE_NAME = 'grive_new'

def find_rclone_executable():
    """Dynamically search for rclone executable in system PATH and common directory locations."""
    if shutil.which("rclone"):
        return "rclone"
    
    # Check common paths on Windows
    common_paths = [
        r"C:\rclone\rclone.exe",
    ]
    # Check root C:\ for any folders containing 'rclone' and check for rclone.exe inside
    try:
        for item in os.listdir("C:\\"):
            if "rclone" in item.lower():
                full_path = os.path.join("C:\\", item, "rclone.exe")
                if os.path.exists(full_path):
                    common_paths.append(full_path)
    except Exception:
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
3. For other depots (e.g. JASHORE, FARIDPUR, SYLHET, etc.), pick the folder or archive file that matches the depot and is the latest upload (by verifying the date/time or folder name dates if available).
   - If there is a direct 'Data' folder and no other folders, select it.
   - If there is a zip file containing the depot's database, select it (e.g. for SYLHET, '03.06.2026(Sylhet).zip' is correct).
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
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0,
        "response_format": {"type": "json_object"}
    }
    
    response = requests.post(url, headers=headers, json=data, timeout=30)
    response.raise_for_status()
    result = response.json()
    content = result['choices'][0]['message']['content']
    return json.loads(content)

def find_db_files_in_drive_folder(drive_service, folder_id):
    """Recursively search for ERPonTheNet_Data.MDF and ERPonTheNet_log.LDF inside a drive folder"""
    found = {}
    query = f"'{folder_id}' in parents and trashed = false"
    results = drive_service.files().list(
        q=query,
        pageSize=100,
        fields="files(id, name, mimeType)"
    ).execute()
    
    files = results.get('files', [])
    for f in files:
        name = f['name'].lower()
        if f['mimeType'] == 'application/vnd.google-apps.folder':
            sub_found = find_db_files_in_drive_folder(drive_service, f['id'])
            if 'mdf' in sub_found and 'mdf' not in found:
                found['mdf'] = sub_found['mdf']
            if 'ldf' in sub_found and 'ldf' not in found:
                found['ldf'] = sub_found['ldf']
        else:
            if name == 'erponthenet_data.mdf':
                found['mdf'] = (f['id'], f['name'])
            elif name == 'erponthenet_log.ldf':
                found['ldf'] = (f['id'], f['name'])
                
    return found

def download_file(drive_service, file_id, dest_path):
    print(f"Downloading file ID: {file_id} to {dest_path}...")
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.FileIO(dest_path, 'wb')
    downloader = MediaIoBaseDownload(fh, request, chunksize=1024*1024*10) # 10MB chunk
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        if status:
            print(f"  Download progress: {int(status.progress() * 100)}%")
    fh.close()
    print("Download complete!")

def grant_sql_server_permissions(folder_path):
    """Grant SQL Server service account read/write permissions to folder"""
    try:
        import subprocess
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
    server = r'.\SQLEXPRESS'
    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE=master;Trusted_Connection=yes;'
    
    conn = pyodbc.connect(conn_str)
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Drop/Detach if already exists
    cursor.execute(f"SELECT database_id FROM sys.databases WHERE name = '{db_name}'")
    if cursor.fetchone():
        print(f"Database {db_name} already exists. Detaching first...")
        try:
            cursor.execute(f"ALTER DATABASE [{db_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
            cursor.execute(f"EXEC sp_detach_db '{db_name}', 'true'")
        except Exception as e:
            print(f"Error detaching existing DB {db_name}: {e}")
            
    # Attach database
    mdf_path = os.path.normpath(mdf_path)
    # Grant permissions to the directory
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
        
    print(f"Attaching {db_name} using query...")
    cursor.execute(attach_query)
    
    # Check current level
    cursor.execute(f"SELECT name, compatibility_level FROM sys.databases WHERE name = '{db_name}'")
    row = cursor.fetchone()
    current_level = row[1] if row else None
    print(f"Attached database: {db_name}. Current compatibility level: {current_level}")
    
    # Set to 100
    print(f"Setting compatibility level of {db_name} to 100...")
    cursor.execute(f"ALTER DATABASE [{db_name}] SET COMPATIBILITY_LEVEL = 100")
    
    # Verify new level
    cursor.execute(f"SELECT compatibility_level FROM sys.databases WHERE name = '{db_name}'")
    new_level = cursor.fetchone()[0]
    print(f"Verified compatibility level: {new_level}")
    
    # Detach database
    print(f"Detaching database {db_name}...")
    cursor.execute(f"ALTER DATABASE [{db_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
    cursor.execute(f"EXEC sp_detach_db '{db_name}', 'true'")
    print(f"Detached successfully!")
    
    conn.close()

def get_or_create_drive_folder(drive_service, folder_name, parent_id):
    query = f"'{parent_id}' in parents and name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = drive_service.files().list(q=query, fields="files(id)").execute()
    files = results.get('files', [])
    if files:
        return files[0]['id']
    else:
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id]
        }
        folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
        return folder.get('id')

def upload_or_replace_file(drive_service, file_path, folder_id, mimetype):
    file_name = os.path.basename(file_path)
    
    query = f"'{folder_id}' in parents and name = '{file_name}' and trashed = false"
    results = drive_service.files().list(q=query, fields="files(id)").execute()
    files = results.get('files', [])
    
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }
    media = MediaFileUpload(file_path, mimetype=mimetype, resumable=True)
    
    if files:
        file_id = files[0]['id']
        print(f"Replacing existing file {file_name} in Google Drive (ID: {file_id})...")
        drive_service.files().update(
            fileId=file_id,
            media_body=media
        ).execute()
    else:
        print(f"Uploading new file {file_name} to Google Drive...")
        drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

def check_if_already_uploaded(drive_service, depot_name, parent_id):
    try:
        # 1. Find the depot folder under parent_id
        query = f"'{parent_id}' in parents and name = '{depot_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        results = drive_service.files().list(q=query, fields="files(id)").execute()
        files = results.get('files', [])
        if not files:
            return False
        depot_folder_id = files[0]['id']
        
        # 2. Find the 'Data' folder under depot_folder_id
        query = f"'{depot_folder_id}' in parents and name = 'Data' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        results = drive_service.files().list(q=query, fields="files(id)").execute()
        files = results.get('files', [])
        if not files:
            return False
        data_folder_id = files[0]['id']
        
        # 3. Check if 'ERPonTheNet_Data.MDF' exists under data_folder_id
        query = f"'{data_folder_id}' in parents and name = 'ERPonTheNet_Data.MDF' and trashed = false"
        results = drive_service.files().list(q=query, fields="files(id, size)").execute()
        files = results.get('files', [])
        if files:
            size = int(files[0].get('size', 0))
            # If the file size is greater than 100MB, it means it is fully uploaded
            if size > 100 * 1024 * 1024:
                return True
        return False
    except Exception as e:
        print(f"Warning checking Drive status for {depot_name}: {e}")
        return False

def process_depot(depot_name, folder_url, drive_service, groq_api_key):
    print(f"\n==================================================")
    print(f"Processing depot: {depot_name}")
    print(f"==================================================")
    
    # Check Google Drive to see if this depot was already successfully uploaded
    if check_if_already_uploaded(drive_service, depot_name, TARGET_UPLOAD_PARENT_ID):
        print(f"Depot {depot_name} is already successfully upgraded and uploaded in Google Drive. Skipping entirely!")
        return True
    
    # Local setup directory
    depot_dir = os.path.join(BASE_DEPOT_DIR, depot_name)
    data_dir = os.path.join(depot_dir, "Data")
    
    final_mdf_path = os.path.join(data_dir, "ERPonTheNet_Data.MDF")
    final_ldf_path = os.path.join(data_dir, "ERPonTheNet_log.LDF")
    
    rclone_exe = find_rclone_executable()
    
    skip_download = False
    if os.path.exists(final_mdf_path):
        print(f"Local MDF file already exists at: {final_mdf_path}")
        print("Skipping Google Drive download for this depot. Using existing local files.")
        skip_download = True
        if not os.path.exists(final_ldf_path):
            final_ldf_path = None
            
    if not skip_download:
        # Extract folder ID from URL
        folder_id_match = re.search(r'folders/([a-zA-Z0-9-_]+)', str(folder_url))
        if not folder_id_match:
            print(f"Error: Invalid folder URL: {folder_url}")
            return False
            
        folder_id = folder_id_match.group(1)
        
        # List folder items
        items = list_drive_folder_items(drive_service, folder_id)
        if not items:
            print(f"No files or folders found in the folder for {depot_name}")
            return False
            
        # Ask Groq to select the best item
        print("Asking Groq LLM to determine the correct database item...")
        decision = get_best_item_from_groq(depot_name, items, groq_api_key)
        print(f"Groq Decision: {json.dumps(decision, indent=2)}")
        
        selected_name = decision.get("selected_item_name")
        selected_id = decision.get("selected_item_id")
        selected_type = decision.get("selected_item_type")
        
        if not selected_id:
            print(f"Error: Groq could not select a valid item ID.")
            return False
            
        os.makedirs(data_dir, exist_ok=True)
        
        temp_download_dir = os.path.join(depot_dir, "Temp_Download")
        os.makedirs(temp_download_dir, exist_ok=True)
        
        mdf_local_path = None
        ldf_local_path = None
        
        if selected_type == 'file' and selected_name.lower().endswith('.zip'):
            # Download ZIP file
            zip_path = os.path.join(temp_download_dir, selected_name)
            remote_file_path = f"{RCLONE_REMOTE_NAME},root_folder_id={folder_id}:{selected_name}"
            cmd = [rclone_exe, "copyto", remote_file_path, zip_path, "--progress"]
            print(f"Running: {' '.join(cmd)}")
            subprocess.run(cmd, check=True)
            
            # Extract ZIP
            print(f"Extracting zip file {zip_path}...")
            extract_dir = os.path.join(temp_download_dir, "extracted")
            os.makedirs(extract_dir, exist_ok=True)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
                
            # Look recursively inside extracted folder for MDF and LDF
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    f_name = file.lower()
                    if f_name == 'erponthenet_data.mdf':
                        mdf_local_path = os.path.join(root, file)
                    elif f_name == 'erponthenet_log.ldf':
                        ldf_local_path = os.path.join(root, file)
                        
            if not mdf_local_path:
                # Fallback search if files are named differently inside zip
                for root, dirs, files in os.walk(extract_dir):
                    for file in files:
                        if file.lower().endswith('.mdf') and not file.lower().startswith('master') and not file.lower().startswith('tempdb') and not file.lower().startswith('msdb') and not file.lower().startswith('model') and not file.lower().startswith('pubs') and not file.lower().startswith('northwnd'):
                            mdf_local_path = os.path.join(root, file)
                        elif file.lower().endswith('.ldf') and not file.lower().startswith('mastlog') and not file.lower().startswith('templog') and not file.lower().startswith('msdb') and not file.lower().startswith('model') and not file.lower().startswith('pubs') and not file.lower().startswith('northwnd'):
                            ldf_local_path = os.path.join(root, file)
                            
        elif selected_type == 'folder':
            # Selected a folder. Recursively download database files via rclone
            print("Folder selected. Downloading MDF and LDF files recursively from Google Drive via rclone...")
            cmd = [
                rclone_exe, "copy",
                f"{RCLONE_REMOTE_NAME},root_folder_id={selected_id}:",
                temp_download_dir,
                "--include", "*.{mdf,ldf,MDF,LDF}",
                "--ignore-case",
                "--progress"
            ]
            print(f"Running: {' '.join(cmd)}")
            subprocess.run(cmd, check=True)
            
            # Look recursively inside downloaded folder for MDF and LDF
            for root, dirs, files in os.walk(temp_download_dir):
                for file in files:
                    f_name = file.lower()
                    if f_name == 'erponthenet_data.mdf':
                        mdf_local_path = os.path.join(root, file)
                    elif f_name == 'erponthenet_log.ldf':
                        ldf_local_path = os.path.join(root, file)
                        
            if not mdf_local_path:
                # Fallback search if files are named differently
                for root, dirs, files in os.walk(temp_download_dir):
                    for file in files:
                        if file.lower().endswith('.mdf') and not file.lower().startswith('master') and not file.lower().startswith('tempdb') and not file.lower().startswith('msdb') and not file.lower().startswith('model') and not file.lower().startswith('pubs') and not file.lower().startswith('northwnd'):
                            mdf_local_path = os.path.join(root, file)
                        elif file.lower().endswith('.ldf') and not file.lower().startswith('mastlog') and not file.lower().startswith('templog') and not file.lower().startswith('msdb') and not file.lower().startswith('model') and not file.lower().startswith('pubs') and not file.lower().startswith('northwnd'):
                            ldf_local_path = os.path.join(root, file)
                            
        else:
            # File that is not a zip (could be MDF directly)
            if selected_name.lower().endswith('.mdf'):
                temp_mdf_path = os.path.join(temp_download_dir, selected_name)
                remote_mdf_path = f"{RCLONE_REMOTE_NAME},root_folder_id={folder_id}:{selected_name}"
                cmd = [rclone_exe, "copyto", remote_mdf_path, temp_mdf_path, "--progress"]
                print(f"Running: {' '.join(cmd)}")
                subprocess.run(cmd, check=True)
                mdf_local_path = temp_mdf_path
                
                # Check if there is an LDF file in the same folder in Drive
                for item in items:
                    if item['name'].lower().endswith('.ldf') and 'erponthenet' in item['name'].lower():
                        temp_ldf_path = os.path.join(temp_download_dir, item['name'])
                        remote_ldf_path = f"{RCLONE_REMOTE_NAME},root_folder_id={folder_id}:{item['name']}"
                        cmd = [rclone_exe, "copyto", remote_ldf_path, temp_ldf_path, "--progress"]
                        print(f"Running: {' '.join(cmd)}")
                        subprocess.run(cmd, check=True)
                        ldf_local_path = temp_ldf_path
                        break
            else:
                print(f"Error: Unknown item type or file format selected: {selected_name}")
                return False

        if not mdf_local_path or not os.path.exists(mdf_local_path):
            print("Error: Database MDF file was not downloaded/extracted successfully.")
            return False
            
        # Overwrite if exists
        if os.path.exists(final_mdf_path):
            os.remove(final_mdf_path)
        shutil.move(mdf_local_path, final_mdf_path)
        print(f"Moved MDF to: {final_mdf_path}")
        
        if ldf_local_path and os.path.exists(ldf_local_path):
            if os.path.exists(final_ldf_path):
                os.remove(final_ldf_path)
            shutil.move(ldf_local_path, final_ldf_path)
            print(f"Moved LDF to: {final_ldf_path}")
            
        # Clean up Temp directory
        shutil.rmtree(temp_download_dir, ignore_errors=True)
        
        if not ldf_local_path:
            final_ldf_path = None
    
    # Upgrade Compatibility Level
    print("Upgrading database compatibility level using local SQLEXPRESS...")
    upgrade_db_compatibility(final_mdf_path, final_ldf_path, depot_name)
    
    # Re-upload upgraded files
    print("Uploading upgraded database files back to Google Drive using rclone...")
    remote_path = f"{RCLONE_REMOTE_NAME},root_folder_id={TARGET_UPLOAD_PARENT_ID}:{depot_name}/Data"
    cmd = [rclone_exe, "copy", data_dir, remote_path, "--progress"]
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
        
    # Reclaim disk space by deleting local depot directory
    print(f"Reclaiming disk space: deleting local folder {depot_dir}...")
    shutil.rmtree(depot_dir, ignore_errors=True)
        
    print(f"Success: Depot {depot_name} processed, upgraded, and uploaded successfully!")
    return True

def main():
    print("Starting Depot Database Upgrade Pipeline...")
    env = load_env(ENV_PATH)
    groq_api_key = env.get("GROQ_API_KEY")
    if not groq_api_key:
        print("Error: GROQ_API_KEY not found in env file.")
        return
        
    if not os.path.exists(CLIENT_SECRET_PATH):
        print(f"Error: Client secret file not found at {CLIENT_SECRET_PATH}")
        return
        
    drive_service = get_drive_service()
    
    df = pd.read_excel(EXCEL_PATH)
    depot_col = df.columns[0]
    link_col = df.columns[1]
    
    # We will process BARISHAL first to verify the pipeline
    # Then we will loop and process all depots.
    depots_to_process = []
    for idx, row in df.iterrows():
        depots_to_process.append((row[depot_col].strip(), row[link_col].strip()))
    
    print(f"Found {len(depots_to_process)} depots to process in Excel sheet.")
    
    success_count = 0
    fail_count = 0
    
    for depot_name, folder_url in depots_to_process:
        try:
            success = process_depot(depot_name, folder_url, drive_service, groq_api_key)
            if success:
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            print(f"Error processing {depot_name}: {e}")
            fail_count += 1
            
    print(f"\n==================================================")
    print(f"Pipeline Execution Summary:")
    print(f"Successfully processed: {success_count}")
    print(f"Failed to process: {fail_count}")
    print(f"==================================================")

if __name__ == '__main__':
    main()
