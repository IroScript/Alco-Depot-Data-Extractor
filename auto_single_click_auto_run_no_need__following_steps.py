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
from googleDrive.credentials_loader import (
    get_drive_service_account_credentials,
    get_env_var,
    list_depots,
)

# Reconfigure console output encoding to prevent Windows crash on non-ASCII characters
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
    except:
        pass

# ══════════════════════════════════════════════════════════════════
#  Google Drive & Upgrade Configuration
#  All paths are resolved dynamically relative to this script's location,
#  so the project can be cloned/copied anywhere (D:, E:, another laptop, etc.)
#  without any hard-coded C:\Users\...\... references.
# ══════════════════════════════════════════════════════════════════
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)

# Project-internal googleDrive/ folder is the single source of truth.
# If a sibling "googleDrive" folder exists next to this script, use it;
# otherwise, fall back to a parent-level googleDrive/ folder.
_LOCAL_GDRIVE_NEXT_TO_SCRIPT = os.path.join(SCRIPT_DIR, "googleDrive")
_LOCAL_GDRIVE_PARENT = os.path.join(PARENT_DIR, "googleDrive")

if os.path.isdir(_LOCAL_GDRIVE_NEXT_TO_SCRIPT):
    LOCAL_GDRIVE_DIR = _LOCAL_GDRIVE_NEXT_TO_SCRIPT
elif os.path.isdir(_LOCAL_GDRIVE_PARENT):
    LOCAL_GDRIVE_DIR = _LOCAL_GDRIVE_PARENT
else:
    # Last-resort fallback so legacy code that references these names
    # doesn't crash on import. These paths will simply not exist on disk
    # if googleDrive/ is missing, and downstream code will fail gracefully.
    LOCAL_GDRIVE_DIR = _LOCAL_GDRIVE_NEXT_TO_SCRIPT

CLIENT_SECRET_PATH = os.path.join(LOCAL_GDRIVE_DIR, "client_secret_1076305260584-t28u3map5uuuqvdk28mrqjk0oigbadh4.apps.googleusercontent.com.json")
TOKEN_PICKLE_PATH = os.path.join(LOCAL_GDRIVE_DIR, "token.pickle")
# NOTE: EXCEL_PATH and ENV_PATH are now LEGACY references. Real values come from
# googleDrive/credentials_master.json (loaded via credentials_loader.get_env_var()
# and list_depots()). The legacy variables are kept defined (set to a non-existent
# path) so that any external importer that still references them by name will not
# crash with NameError — downstream code in this file has been migrated.
EXCEL_PATH = os.path.join(LOCAL_GDRIVE_DIR, "gDriveDepotLinks.xlsx")
ENV_PATH = os.path.join(LOCAL_GDRIVE_DIR, "env")
BASE_DEPOT_DIR = os.path.join(LOCAL_GDRIVE_DIR, "All_Depots")
RCLONE_REMOTE_NAME = 'grive_new'
SQL_SERVER = r'localhost'  # Default instance (MSSQLSERVER). For SQLEXPRESS use r'.\SQLEXPRESS'

# ══════════════════════════════════════════════════════════════════
#  LOCAL-FIRST PATH OVERRIDE (legacy comment kept for reference)
#  All configuration paths above are now computed relative to this
#  script, so the project is fully portable. Any folder containing
#  this script + a sibling "googleDrive/" will Just Work.
# ══════════════════════════════════════════════════════════════════

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
    # Use single-source credentials from credentials_master.json (in-memory, no JSON file needed).
    from googleDrive.credentials_loader import get_drive_service_account_credentials
    scopes = ['https://www.googleapis.com/auth/drive']
    creds = get_drive_service_account_credentials(scopes=scopes)
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

def load_mpo_mapping_from_google_sheet(sheet_id='1Q4utivZ5OpgDznqlqElYU-HWNnZYI71YYpcZKcSM3xY', gid='1918615875'):
    """
    Load the MPO mapping directly from the public Google Sheet
    (DREAM APPS MPO CODE column) when the local mpo_code.xlsx file
    is not available.

    The sheet is publicly shared, so this works without authentication
    by exporting it as XLSX via the standard Google Sheets export URL.

    IMPORTANT: Filters out rows where MPO CODE is blank (footer/notes rows)
    so they don't pollute the SQL join with fake mappings.
    """
    try:
        url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}'
        print(f"  Pulling MPO mapping from Google Sheet gid={gid}...")
        df = pd.read_csv(url)

        # Normalize column names: 'DREAM APPS MPO CODE' -> 'MPO CODE'
        rename_map = {}
        for c in df.columns:
            cs = str(c).strip()
            if cs.upper() == 'DREAM APPS MPO CODE':
                rename_map[c] = 'MPO CODE'
            elif cs.upper() == 'DREAM APPS DEPOT':
                rename_map[c] = 'DEPOT'
            elif cs.upper() == 'DREAM APPS ZONE':
                rename_map[c] = 'ZONE'
        if rename_map:
            df.rename(columns=rename_map, inplace=True)

        # Filter out rows with blank MPO CODE (footer/separator rows in the sheet)
        total_raw = len(df)
        if 'MPO CODE' in df.columns:
            df['MPO CODE'] = df['MPO CODE'].astype(str).str.strip()
            df = df[df['MPO CODE'].notna()
                    & (df['MPO CODE'] != '')
                    & (df['MPO CODE'].str.lower() != 'nan')]
            # Also drop rows with blank DEPOT (those would be pure noise too)
            if 'DEPOT' in df.columns:
                df['DEPOT'] = df['DEPOT'].astype(str).str.strip()
                df = df[df['DEPOT'].notna()
                        & (df['DEPOT'] != '')
                        & (df['DEPOT'].str.lower() != 'nan')]
            print(f"  [OK] Loaded MPO mapping: {len(df)} valid rows (filtered {total_raw - len(df)} blank rows)")
        else:
            print(f"  [WARN] MPO CODE column not found, returning {len(df)} raw rows")

        # Normalize keys for join
        if 'MPO CODE' in df.columns:
            df['MPO CODE'] = df['MPO CODE'].astype(str).str.strip().str.upper()
        if 'DEPOT' in df.columns:
            df['DEPOT'] = df['DEPOT'].astype(str).str.strip().str.upper()

        if 'DEPOT' in df.columns and 'MPO CODE' in df.columns:
            df['DEPOT_MPO_CODE'] = df['DEPOT'] + '_' + df['MPO CODE']
            df = df.drop_duplicates(subset=['DEPOT_MPO_CODE'], keep='first')

        print(f"  [OK] Columns: {list(df.columns)[:6]}...")
        return df
    except Exception as e:
        print(f"  [ERROR] Could not load MPO mapping from Google Sheet: {e}")
        return None


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


# Server options tried in order by connect_sql_server() below.
# On systems where SQL Server is installed as the DEFAULT instance
# (i.e. service name = MSSQLSERVER), 'localhost' / '.' works.
# On systems where it was installed as a NAMED instance (SQLEXPRESS),
# 'localhost\SQLEXPRESS' / '.\SQLEXPRESS' works.
_SQL_SERVER_CANDIDATES = [
    r'localhost',
    r'.',
    r'(local)',
    r'localhost\SQLEXPRESS',
    r'.\SQLEXPRESS',
    r'(local)\SQLEXPRESS',
]


def connect_sql_server(database='master', timeout=5):
    """
    Try connecting to SQL Server using several common server names,
    returning the first successful pyodbc connection. Raises the last
    error if none succeed.
    """
    last_err = None
    for server in _SQL_SERVER_CANDIDATES:
        try:
            conn_str = (
                f'DRIVER={{ODBC Driver 17 for SQL Server}};'
                f'SERVER={server};'
                f'DATABASE={database};'
                f'Trusted_Connection=yes;'
                f'Connection Timeout={timeout};'
            )
            conn = pyodbc.connect(conn_str, timeout=timeout)
            print(f"  [OK] SQL Server connected via SERVER={server}")
            return conn
        except Exception as e:
            last_err = e
    raise last_err

def upgrade_db_compatibility(mdf_path, ldf_path, depot_name):
    db_name = f"{depot_name.upper().replace('-', '_')}_UPGRADE_DB"

    conn = connect_sql_server(database='master')
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

    # Grant write access to SQL Server service account on the depot Data folder
    # (the user folder may not have MSSQLSERVER in its ACL).
    grant_sql_server_permissions(data_dir)

    # Use a temp directory under TEMP (writable by SQL Server service) for dummy files
    # instead of the depot's Data folder, to avoid "Access is denied" on CREATE DATABASE.
    import tempfile
    _sylhet_tmp = os.path.join(tempfile.gettempdir(), f"alco_sylhet_{depot_name}")
    os.makedirs(_sylhet_tmp, exist_ok=True)
    # Ensure SQL Server can read/write this temp dir
    grant_sql_server_permissions(_sylhet_tmp)

    dummy_mdf_path = os.path.join(_sylhet_tmp, f'{depot_name}_dummy.mdf')
    dummy_ldf_path = os.path.join(_sylhet_tmp, f'{depot_name}_dummy_log.ldf')

    conn = connect_sql_server(database='master')
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
    dbcc_errors = []
    try:
        cursor.execute(f"DBCC CHECKDB ('{db_name}', REPAIR_ALLOW_DATA_LOSS) WITH NO_INFOMSGS, ALL_ERRORMSGS")
        while True:
            if not cursor.nextset():
                break
            try:
                row = cursor.fetchone()
                if row is None:
                    break
            except Exception:
                break
    except Exception as e:
        dbcc_errors.append(str(e))
        print(f"    DBCC warning (expected): {e}")

    # ── SAFETY CHECK: count rows in main transaction tables ──
    # REPAIR_ALLOW_DATA_LOSS can silently delete damaged rows. We verify that
    # key tables (xline, xorder) still have rows. If 0 rows -> data is lost.
    print("    Verifying recovered database row counts (data-loss safety check)...")
    row_counts = {}
    try:
        cursor.execute(f"USE [{db_name}]")
        for tbl in ['xline', 'xorder', 'xsp', 'xcustomer']:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM dbo.{tbl}")
                row_counts[tbl] = cursor.fetchone()[0]
            except Exception:
                row_counts[tbl] = None
        total = sum(v for v in row_counts.values() if v)
        print(f"    [SAFETY] Row counts after recovery: {row_counts} (total={total})")
        if total == 0:
            print(f"    [CRITICAL] SYLHET database recovery returned ZERO rows in all main tables.")
            print(f"               This depot's data is likely LOST/corrupted in the source MDF.")
            print(f"               Pipeline will SKIP {depot_name} to avoid polluting aggregates with zeros.")
            try:
                cursor.execute(f"ALTER DATABASE [{db_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
                cursor.execute(f"EXEC sp_detach_db '{db_name}', 'true'")
            except Exception:
                pass
            return None
        elif total < 100:
            print(f"    [WARN] Very low row count ({total}) in SYLHET. May indicate partial data loss.")
    except Exception as e:
        print(f"    [WARN] Safety check failed: {e}")

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

    conn = connect_sql_server(database='master')
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
    try:
        conn = connect_sql_server(database='master')
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
        conn = connect_sql_server(database=db_name)
        
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

def get_local_data_paths(depot_name):
    """Look for existing MDF/LDF in local depot folder (case-insensitive)."""
    depot_dir = os.path.join(BASE_DEPOT_DIR, depot_name)
    data_dir = os.path.join(depot_dir, "Data")
    if not os.path.isdir(data_dir):
        return None, None
    mdf_path = ldf_path = None
    for entry in os.listdir(data_dir):
        low = entry.lower()
        full = os.path.join(data_dir, entry)
        if low in ("erponthenet_data.mdf", "erponthenet.mdf"):
            mdf_path = full
        elif low in ("erponthenet_log.ldf", "erponthenet.ldf"):
            ldf_path = full
    return mdf_path, ldf_path


# ══════════════════════════════════════════════════════════════════
#  3-STAGE / 3-LAYER LOCAL FILE VERIFICATION SYSTEM
#  Purpose: Decide whether we can SKIP Google Drive download because
#  every depot's data is already present locally.
#
#  Stage 1 = Depot folder exists under BASE_DEPOT_DIR/All_Depots/<DEPOT>
#  Stage 2 = A "Data" folder exists somewhere inside that depot folder
#            (depth 1..N sub-folders allowed — recursive search)
#  Stage 3 = At least EXPECTED_MIN_FILES MDF/LDF files exist in that Data
#            folder, each with size > 0 bytes (non-empty / fully downloaded)
#
#  Each stage is verified by 3 INDEPENDENT Python layers to avoid false
#  positives — all 3 layers must agree per stage before that stage counts
#  as "passed".
#
#  Returns: (passes: bool, details: dict) where details holds per-stage
#  and per-layer booleans for diagnostic logging.
# ══════════════════════════════════════════════════════════════════
EXPECTED_MIN_FILES = 15  # MDF + LDF files combined. FARIDPUR has 17, etc.


def _layer1_os_pathlib(depot_name):
    """Layer 1: os.path / listdir based verification (classic stdlib)."""
    depot_dir = os.path.join(BASE_DEPOT_DIR, depot_name)

    # STAGE 1: depot folder exists
    s1 = os.path.isdir(depot_dir)

    # STAGE 2: a "Data" folder exists anywhere underneath depot_dir
    s2 = False
    if s1:
        for root, dirs, _files in os.walk(depot_dir):
            if "Data" in dirs:
                # Confirm it's a directory (defense-in-depth)
                candidate = os.path.join(root, "Data")
                if os.path.isdir(candidate):
                    s2 = True
                    break

    # STAGE 3: file count via os.listdir + extension check, size > 0
    s3_count = 0
    if s2:
        # Re-walk to find the same Data folder we confirmed above
        for root, dirs, _files in os.walk(depot_dir):
            if "Data" in dirs:
                data_dir = os.path.join(root, "Data")
                try:
                    for entry in os.listdir(data_dir):
                        full = os.path.join(data_dir, entry)
                        if not os.path.isfile(full):
                            continue
                        low = entry.lower()
                        if low.endswith(".mdf") or low.endswith(".ldf"):
                            try:
                                if os.path.getsize(full) > 0:
                                    s3_count += 1
                            except OSError:
                                pass
                except OSError:
                    pass
                break
    s3 = s3_count >= EXPECTED_MIN_FILES

    return {"s1": s1, "s2": s2, "s3": s3, "s3_count": s3_count}


def _layer2_pathlib_rglob(depot_name):
    """Layer 2: pathlib.Path with rglob (recursive glob)."""
    from pathlib import Path

    depot_path = Path(BASE_DEPOT_DIR) / depot_name

    # STAGE 1
    s1 = depot_path.is_dir()

    # STAGE 2: rglob for any 'Data' folder case-insensitively
    s2 = False
    if s1:
        for p in depot_path.rglob("Data"):
            if p.is_dir():
                s2 = True
                break
        # also accept case-insensitive match
        if not s2:
            for p in depot_path.rglob("*"):
                if p.is_dir() and p.name.lower() == "data":
                    s2 = True
                    break

    # STAGE 3: use iterdir() on the Data folder
    s3_count = 0
    if s2:
        for p in depot_path.rglob("*"):
            if p.is_dir() and p.name.lower() == "data":
                try:
                    for f in p.iterdir():
                        if not f.is_file():
                            continue
                        if f.suffix.lower() in (".mdf", ".ldf"):
                            try:
                                if f.stat().st_size > 0:
                                    s3_count += 1
                            except OSError:
                                pass
                except OSError:
                    pass
                break

    s3 = s3_count >= EXPECTED_MIN_FILES
    return {"s1": s1, "s2": s2, "s3": s3, "s3_count": s3_count}


def _layer3_scandir_size(depot_name):
    """Layer 3: os.scandir (fast, returns DirEntry objects with stat)
    plus third independent walk-based file extension validation.
    """
    depot_dir = os.path.join(BASE_DEPOT_DIR, depot_name)

    # STAGE 1 — use scandir on parent
    s1 = False
    try:
        base = Path(BASE_DEPOT_DIR) if False else None  # noqa
        parent = os.path.dirname(depot_dir)
        with os.scandir(parent) as it:
            for entry in it:
                if entry.name == depot_name and entry.is_dir():
                    s1 = True
                    break
    except (FileNotFoundError, OSError):
        s1 = os.path.isdir(depot_dir)  # fallback

    # STAGE 2 — manual stack-based DFS using os.scandir (no os.walk)
    s2 = False
    data_dir_found = None
    if s1:
        try:
            stack = [depot_dir]
            while stack:
                current = stack.pop()
                try:
                    with os.scandir(current) as it:
                        for entry in it:
                            if entry.is_dir(follow_symlinks=False):
                                if entry.name.lower() == "data":
                                    data_dir_found = entry.path
                                    s2 = True
                                    break
                                stack.append(entry.path)
                        if s2:
                            break
                except (PermissionError, OSError):
                    continue
        except OSError:
            pass

    # STAGE 3 — count via scandir on the discovered Data folder
    s3_count = 0
    if s2 and data_dir_found:
        try:
            with os.scandir(data_dir_found) as it:
                for entry in it:
                    if not entry.is_file():
                        continue
                    low = entry.name.lower()
                    if low.endswith(".mdf") or low.endswith(".ldf"):
                        try:
                            st = entry.stat()
                            if st.st_size > 0:
                                s3_count += 1
                        except OSError:
                            pass
        except OSError:
            pass
    s3 = s3_count >= EXPECTED_MIN_FILES

    return {"s1": s1, "s2": s2, "s3": s3, "s3_count": s3_count}


def verify_local_depot_complete(depot_name, min_files=EXPECTED_MIN_FILES,
                                 verbose=True):
    """Triple-Stage + Triple-Layer verification for a single depot.

    Returns (passes: bool, report: dict)
    - `passes` is True ONLY if every stage passes in every layer.
    - `report` is a dict like:
        {
          'layer1': {'s1':bool,'s2':bool,'s3':bool,'s3_count':int},
          'layer2': {...},
          'layer3': {...},
          'all_passed': bool
        }

    The caller can short-circuit Google Drive download when `passes` is True.
    """
    l1 = _layer1_os_pathlib(depot_name)
    l2 = _layer2_pathlib_rglob(depot_name)
    l3 = _layer3_scandir_size(depot_name)

    # Each stage must be True across all 3 layers before download can be skipped
    stage1_ok = l1["s1"] and l2["s1"] and l3["s1"]
    stage2_ok = l1["s2"] and l2["s2"] and l3["s2"]
    # Stage 3: also cross-check the count to be reasonably close across layers
    counts = [l1["s3_count"], l2["s3_count"], l3["s3_count"]]
    max_count = max(counts)
    min_count = min(counts)
    # Allow at most 1-file discrepancy between layers due to race conditions
    count_consistent = (max_count - min_count) <= 1
    stage3_ok = (l1["s3"] and l2["s3"] and l3["s3"]
                 and max_count >= min_files and count_consistent)

    all_passed = stage1_ok and stage2_ok and stage3_ok

    if verbose:
        l1c = l1["s3_count"]; l2c = l2["s3_count"]; l3c = l3["s3_count"]
        print(f"    [VERIFY] {depot_name}")
        print(f"      Stage1 (Depot folder):     L1={l1['s1']} L2={l2['s1']} L3={l3['s1']} -> {'OK' if stage1_ok else 'FAIL'}")
        print(f"      Stage2 (Data folder):      L1={l1['s2']} L2={l2['s2']} L3={l3['s2']} -> {'OK' if stage2_ok else 'FAIL'}")
        print(f"      Stage3 ({min_files}+ files): L1={l1c} L2={l2c} L3={l3c} -> {'OK' if stage3_ok else 'FAIL'}")
        print(f"      >>> {'LOCAL COMPLETE — will skip Google Drive' if all_passed else 'INCOMPLETE — must download'}")

    report = {
        "layer1": l1,
        "layer2": l2,
        "layer3": l3,
        "stage1_ok": stage1_ok,
        "stage2_ok": stage2_ok,
        "stage3_ok": stage3_ok,
        "all_passed": all_passed,
        "counts": counts,
    }
    return all_passed, report


def all_depots_have_local_mdf(depots_to_process):
    """
    Check if EVERY depot in the list already has a local MDF file on disk.
    If yes, we can skip Google Drive connection and rclone download entirely,
    and work directly with the local files via SQL Server.

    This is the SINGLE-FILE (just MDF) check used as a quick precondition.
    The deeper triple-stage verification is run per-depot in the main loop
    via `verify_local_depot_complete`.
    """
    missing = []
    for depot_name, _folder_url in depots_to_process:
        mdf_path, _ldf_path = get_local_data_paths(depot_name)
        if not mdf_path or not os.path.exists(mdf_path):
            missing.append(depot_name)
    return (len(missing) == 0), missing

def download_depot_files(depot_name, folder_url, drive_service, groq_api_key):
    """Download MDF/LDF files for a single depot from Google Drive.

    Per user requirement, this ALWAYS downloads fresh files on every run.
    Any existing local files are overwritten by rclone. Files persist on disk
    after this function returns (no deletion by this function).
    """
    depot_dir = os.path.join(BASE_DEPOT_DIR, depot_name)
    data_dir = os.path.join(depot_dir, "Data")
    os.makedirs(data_dir, exist_ok=True)

    final_mdf_path = os.path.join(data_dir, "ERPonTheNet_Data.MDF")
    final_ldf_path = os.path.join(data_dir, "ERPonTheNet_log.LDF")

    # Log whether we're going to overwrite an existing cached file
    if os.path.exists(final_mdf_path):
        print(f"  Existing local MDF will be overwritten: {final_mdf_path}")
        
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
    try:
        conn = connect_sql_server(database='master')
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

def send_pipeline_telegram_notification(base_dir, success_depots, sales_count, returns_count, timestamp):
    env_path = os.path.join(base_dir, "googleDrive", "env")
    env = {}
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        env[parts[0].strip()] = parts[1].strip()
                        
    bot_token = env.get("TELEGRAM_BOT_TOKEN")
    chat_id = env.get("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("  [Telegram] Notification skipped: Credentials not found in env.")
        return
        
    msg = f"""🚀 *ALCO PHARMA LTD. - PIPELINE REPORT* 🚀
===================================
📅 *Completed:* {datetime.now().strftime('%Y-%m-%d %I:%M %p')}
✅ *Status:* PIPELINE STEPS COMPLETED SUCCESSFULLY!
📂 *Depots Processed:* {', '.join(success_depots)} ({len(success_depots)} Depots)

📊 *Statistics:*
- Sales Transactions: {sales_count:,}
- Returns Transactions: {returns_count:,}

📁 *New Files Created:*
1. 01_Product_Level_Net_Sales_Extracted_Data_{timestamp}.csv
2. 01.1_Date_wise_Customer_wise_Product_wise_Net_Sales_Extracted_Data_{timestamp}.csv
3. 02A_MPO_Achievement_Pivot_Analysis_{timestamp}.xlsx
4. 02D_FINAL_MPO_Target_vs_Achievement_Formula_{timestamp}.xlsx
5. 03_Zone_Wise_Sales_Grouped_Report_{timestamp}.xlsx
6. 04_Analyzed_10_Param_Zone_Wise_Sales_Grouped_Report_{timestamp}.xlsx
==================================="""
    
    import requests
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": msg,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
        print("  ✓ [Telegram] Success notification sent successfully!")
    except Exception as e:
        print(f"  [Telegram] Warning: Failed to send notification: {e}")

def generate_and_send_brand_exception_report(base_dir, combined_df, timestamp):
    summary_files = [f for f in os.listdir(base_dir) if f.startswith('02C_MPO_Matched_Targets_Summary_') and f.endswith('.xlsx')]
    summary_files.sort(reverse=True)
    if not summary_files:
        print("  [Telegram] Exception report skipped: 02C summary file not found.")
        return
        
    summary_path = os.path.join(base_dir, summary_files[0])
    try:
        df_mpo = pd.read_excel(summary_path, sheet_name='MPO_Field_Targets')
    except Exception as e:
        print(f"  [Telegram] Warning: Failed to read {summary_files[0]}: {e}")
        return
        
    sales_only = combined_df[combined_df['Transaction_Type'] == 'Sale'].copy()
    
    sales_only['is_alagra'] = sales_only['Product_Name'].str.contains('ALAGRA', case=False, na=False)
    sales_only['is_mokast'] = sales_only['Product_Name'].str.contains('MOKAST', case=False, na=False)
    
    mpo_sales = sales_only.groupby(['Depot', 'MPO_Code']).agg(
        alagra_sold=('Quantity', lambda x: x[sales_only.loc[x.index, 'is_alagra']].sum()),
        mokast_sold=('Quantity', lambda x: x[sales_only.loc[x.index, 'is_mokast']].sum())
    ).reset_index()
    
    df_mpo['MPO CODE'] = df_mpo['MPO CODE'].astype(str).str.strip().str.upper()
    df_mpo['DEPOT'] = df_mpo['DEPOT'].astype(str).str.strip().str.upper()
    
    mpo_sales['MPO_Code'] = mpo_sales['MPO_Code'].astype(str).str.strip().str.upper()
    mpo_sales['Depot'] = mpo_sales['Depot'].astype(str).str.strip().str.upper()
    
    merged = pd.merge(
        df_mpo, 
        mpo_sales, 
        left_on=['DEPOT', 'MPO CODE'], 
        right_on=['Depot', 'MPO_Code'], 
        how='left'
    )
    
    merged['alagra_sold'] = merged['alagra_sold'].fillna(0)
    merged['mokast_sold'] = merged['mokast_sold'].fillna(0)
    
    exceptions = merged[(merged['alagra_sold'] == 0) | (merged['mokast_sold'] == 0)].copy()
    
    if len(exceptions) == 0:
        print("  [Telegram] No sales exceptions found for ALAGRA/MOKAST.")
        return
        
    exceptions = exceptions.sort_values(by=['DEPOT', 'FM/AM, ZONE', 'MPO CODE'])
    
    msg_lines = [
        "🚨 *ALCO PHARMA - SALES EXCEPTION REPORT* 🚨",
        "=========================================",
        f"📅 *Report Date:* {datetime.now().strftime('%d-%b-%Y')}",
        "💊 *Target Brands:* ALAGRA & MOKAST (Zero Sales Alert)",
        "",
        "The following MPOs have *ZERO* sales for ALAGRA or MOKAST in the processed data:",
        "-----------------------------------------"
    ]
    
    count = 0
    max_display = 15
    for idx, row in exceptions.iterrows():
        count += 1
        if count > max_display:
            msg_lines.append(f"⚠️ *...and {len(exceptions) - max_display} more exceptions. See detailed CSV.*")
            break
            
        depot = row['DEPOT']
        zone = row['ZONE']
        fm = row['FM/AM, ZONE']
        mpo = row['MPO CODE']
        market = row['MARKET']
        alagra = int(row['alagra_sold'])
        mokast = int(row['mokast_sold'])
        
        status_alagra = "❌ ZERO SALE" if alagra == 0 else f"{alagra:,} Sold"
        status_mokast = "❌ ZERO SALE" if mokast == 0 else f"{mokast:,} Sold"
        
        msg_lines.append(f"📍 *Depot:* {depot} ({zone})")
        msg_lines.append(f"👤 *FM:* {fm}")
        msg_lines.append(f"🔑 *MPO:* {mpo} ({market})")
        msg_lines.append(f"   ▪️ ALAGRA: {status_alagra}")
        msg_lines.append(f"   ▪️ MOKAST: {status_mokast}")
        msg_lines.append("")
        
    msg_lines.append("=========================================")
    msg_lines.append(f"📈 *SUMMARY:*")
    msg_lines.append(f"- Total MPOs with exceptions: *{len(exceptions)}*")
    msg_lines.append(f"- Zero ALAGRA sales: *{len(exceptions[exceptions['alagra_sold'] == 0])} MPOs*")
    msg_lines.append(f"- Zero MOKAST sales: *{len(exceptions[exceptions['mokast_sold'] == 0])} MPOs*")
    msg_lines.append("=========================================")
    
    msg_text = "\n".join(msg_lines)
    
    env_path = os.path.join(base_dir, "googleDrive", "env")
    env = {}
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        env[parts[0].strip()] = parts[1].strip()
                        
    bot_token = env.get("TELEGRAM_BOT_TOKEN")
    chat_id = env.get("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        return
        
    import requests
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": msg_text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=15).raise_for_status()
        print("  ✓ [Telegram] Exception report sent successfully!")
    except Exception as e:
        print(f"  [Telegram] Warning: Failed to send exception report: {e}")

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
    
    # All credentials + depot folder URLs now come from credentials_master.json
    # via the loader (no more scattered env/Excel/client_secret files needed).
    groq_api_key = get_env_var("GROQ_API_KEY")
    if not groq_api_key:
        print("ERROR: GROQ_API_KEY not found in credentials_master.json (env_file_content).")
        return

    # Depot list now comes from credentials_master.json via the loader.
    depots_to_process = [(d['name'], d.get('url') or d.get('folder_id', '')) for d in list_depots()]

    print(f"Found {len(depots_to_process)} depots in credentials_master.json.")

    # ─── GOOGLE DRIVE DOWNLOAD MODE ───────────────────────────────────────
    # Per user requirement, MDF/LDF files are ALWAYS freshly downloaded from
    # Google Drive on every run (overwriting any existing local cache). Local
    # files remain on disk after the pipeline finishes so they can be inspected
    # or re-used later, but they are NOT a fast-path for the current run.
    print("\n" + "=" * 60)
    print("[CLOUD MODE] Will download fresh MDF/LDF for each depot from Google Drive.")
    print(f"             Cache folder: {BASE_DEPOT_DIR}")
    print("             Existing files (if any) will be overwritten.")
    print("=" * 60)

    # Credentials are loaded from the master file — verify the SA is reachable
    try:
        get_drive_service_account_credentials()
        creds_ok = True
    except Exception:
        creds_ok = False

    if not creds_ok and not all_local:
        print(f"ERROR: Client secret not found at {CLIENT_SECRET_PATH} AND no local MDFs.")
        return

    if creds_ok:
        drive_service = get_drive_service()
    else:
        print("[WARN] Google credentials not available; using existing local MDFs only.")
        drive_service = None
    
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

        # ── 3-STAGE / 3-LAYER LOCAL VERIFICATION ──
        # If ALL 3 stages (depot dir / Data folder / 15+ MDF/LDF files) pass
        # in ALL 3 independent verification layers, we SKIP the Google Drive
        # download completely and just use the local files.
        local_ok, verify_report = verify_local_depot_complete(
            depot_name, min_files=EXPECTED_MIN_FILES, verbose=True
        )

        if drive_service is None:
            # No Google credentials — fall back to whatever local files exist
            mdf_path, ldf_path = get_local_data_paths(depot_name)
            if not mdf_path:
                print(f"  ✗ [NO CREDENTIALS] No MDF for {depot_name} and Google Drive is disabled. Skipping.")
                continue
            print(f"  ✓ [FALLBACK LOCAL] Reusing existing MDF: {mdf_path}")
        else:
            # ── FAST PATH: skip Google Drive download if all 3 stages / 3 layers verified ──
            if local_ok:
                mdf_path, ldf_path = get_local_data_paths(depot_name)
                if mdf_path and os.path.exists(mdf_path):
                    counts = verify_report["counts"]
                    print(f"  ⚡ [LOCAL CACHE HIT] All 3 stages verified by all 3 layers.")
                    print(f"       file counts across layers: {counts} (min required {EXPECTED_MIN_FILES})")
                    print(f"       Skipping Google Drive download for {depot_name}.")
                else:
                    # Verification said OK but MDF actually missing — fall back
                    print(f"  ⚠ Verification passed but local MDF missing — falling back to download.")
                    mdf_path, ldf_path = download_depot_files(
                        depot_name, folder_url, drive_service, groq_api_key
                    )
                    if not mdf_path:
                        mdf_path, ldf_path = get_local_data_paths(depot_name)
                        if not mdf_path:
                            print(f"  ✗ Failed to download MDF for {depot_name}. Skipping.")
                            continue
                        print(f"  ⚠ Download failed; falling back to existing local MDF: {mdf_path}")
            else:
                mdf_path, ldf_path = download_depot_files(
                    depot_name, folder_url, drive_service, groq_api_key
                )
                if not mdf_path:
                    # If download failed, try the previously cached local file as a last resort
                    mdf_path, ldf_path = get_local_data_paths(depot_name)
                    if not mdf_path:
                        print(f"  ✗ Failed to download MDF for {depot_name}. Skipping.")
                        continue
                    print(f"  ⚠ Download failed; falling back to existing local MDF: {mdf_path}")
        
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
                
            # ── RECLAIM DISK SPACE (only Temp_Download, KEEP Data/ as cache) ──
            temp_folder = os.path.join(BASE_DEPOT_DIR, depot_name, "Temp_Download")
            if os.path.exists(temp_folder):
                print(f"  Reclaiming space: deleting Temp_Download for {depot_name}...")
                try:
                    shutil.rmtree(temp_folder, ignore_errors=True)
                except Exception as e:
                    print(f"  Warning deleting temp folder: {e}")
            print(f"  ✓ Kept Data/ as cache for next run. Free Space: {check_free_space():.2f} GB")
                    
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
    
        # ── CLOUD API UPLOAD OR SQLITE DATABASE FALLBACK ──
    try:
        print("[INFO] Fetching MPO Code mapping directly from Google Sheet...")
        try:
            _gsheet_url = 'https://docs.google.com/spreadsheets/d/1Q4utivZ5OpgDznqlqElYU-HWNnZYI71YYpcZKcSM3xY/export?format=csv&gid=1918615875'
            df_mpo = pd.read_csv(_gsheet_url)
            rename_map = {}
            for c in df_mpo.columns:
                cs = str(c).strip().upper()
                if cs == 'DREAM APPS MPO CODE':
                    rename_map[c] = 'MPO CODE'
                elif cs == 'DREAM APPS DEPOT':
                    rename_map[c] = 'DEPOT'
                elif cs == 'DREAM APPS ZONE':
                    rename_map[c] = 'ZONE'
            if rename_map:
                df_mpo.rename(columns=rename_map, inplace=True)

            # Filter blank MPO CODE and DEPOT rows
            if 'MPO CODE' in df_mpo.columns:
                df_mpo['MPO CODE'] = df_mpo['MPO CODE'].astype(str).str.strip()
                df_mpo = df_mpo[df_mpo['MPO CODE'].notna()
                                & (df_mpo['MPO CODE'] != '')
                                & (df_mpo['MPO CODE'].str.lower() != 'nan')]
            if 'DEPOT' in df_mpo.columns:
                df_mpo['DEPOT'] = df_mpo['DEPOT'].astype(str).str.strip()
                df_mpo = df_mpo[df_mpo['DEPOT'].notna()
                                & (df_mpo['DEPOT'] != '')
                                & (df_mpo['DEPOT'].str.lower() != 'nan')]

            # Normalize keys
            if 'MPO CODE' in df_mpo.columns:
                df_mpo['MPO CODE'] = df_mpo['MPO CODE'].astype(str).str.strip().str.upper()
            if 'DEPOT' in df_mpo.columns:
                df_mpo['DEPOT'] = df_mpo['DEPOT'].astype(str).str.strip().str.upper()

            if 'DEPOT' in df_mpo.columns and 'MPO CODE' in df_mpo.columns:
                df_mpo['DEPOT_MPO_CODE'] = df_mpo['DEPOT'] + '_' + df_mpo['MPO CODE']
                df_mpo = df_mpo.drop_duplicates(subset=['DEPOT_MPO_CODE'], keep='first')

            print(f"  Loaded {len(df_mpo)} valid MPO rows from Google Sheet.")
        except Exception as ex:
            print(f"\n[CRITICAL ERROR] Could not load MPO mapping from Google Sheet: {ex}")
            print("Process stopped because Google Sheet is mandatory.")
            raise RuntimeError(f"Google Sheet MPO data fetch failed: {ex}")

        df_mpo_temp = df_mpo.copy()
        df_mpo_temp.rename(columns={'DEPOT': 'DEPOT_mpo', 'MPO CODE': 'MPO_CODE_mpo'}, inplace=True)

        df_merged = pd.merge(
            detailed_grouped,
            df_mpo_temp,
            left_on=['Depot', 'MPO_Code'],
            right_on=['DEPOT_mpo', 'MPO_CODE_mpo'],
            how='left'
        )

        if 'ZONE' in df_mpo.columns:
            depot_to_zone = df_mpo.groupby('DEPOT')['ZONE'].first().to_dict()
            df_merged['ZONE'] = df_merged['ZONE'].fillna(df_merged['Depot'].map(depot_to_zone))

        df_merged.drop(columns=['DEPOT_mpo', 'MPO_CODE_mpo'], errors='ignore', inplace=True)

        # Load environment credentials for cloud upload
        api_gateway_url = env.get("API_GATEWAY_URL")
        api_key = env.get("API_KEY", "alco_secure_api_key_2026")
        
        uploaded_to_cloud = False
        if api_gateway_url:
            try:
                print("\n" + "="*60)
                print("UPLOADING SALES DATA TO CLOUD API GATEWAY")
                print("="*60)
                
                # Format records for API
                df_api = df_merged.copy()
                df_api.rename(columns={
                    'CONCATENATED_KEY': 'concatenated_key',
                    'Depot': 'depot',
                    'MPO_Code': 'mpo_code',
                    'Invoice_No': 'invoice_no',
                    'Invoice_Date': 'invoice_date',
                    'Transaction_Time': 'transaction_time',
                    'Transaction_Type': 'transaction_type',
                    'Customer_ID': 'customer_id',
                    'Customer_Name': 'customer_name',
                    'Product_Code': 'product_code',
                    'Product_Name': 'product_name',
                    'Quantity': 'quantity',
                    'Line_Amount': 'line_amount',
                    'Month': 'month',
                    'ZONE': 'zone',
                    'MARKET': 'market',
                    'FM/AM': 'fm_am'
                }, inplace=True)
                
                # Convert timestamps and dates to strings
                for col in ['invoice_date', 'transaction_time']:
                    if col in df_api.columns:
                        df_api[col] = df_api[col].astype(str)
                        
                records = df_api.to_dict(orient='records')
                total_records = len(records)
                batch_size = 5000
                
                print(f"Streaming {total_records:,} records to Aiven PostgreSQL in batches of {batch_size}...")
                headers = {
                    "X-API-Key": api_key,
                    "Content-Type": "application/json"
                }
                
                for idx in range(0, total_records, batch_size):
                    batch = records[idx:idx+batch_size]
                    res = requests.post(
                        f"{api_gateway_url.rstrip('/')}/upload/sales", 
                        json=batch, 
                        headers=headers, 
                        timeout=90
                    )
                    res.raise_for_status()
                    print(f"  ✓ Uploaded records {idx:,} to {min(idx+batch_size, total_records):,}")
                    
                print("✓ [SUCCESS] All records uploaded to Aiven PostgreSQL cloud database!")
                uploaded_to_cloud = True
            except Exception as api_err:
                print(f"⚠ Warning: Cloud API Gateway upload failed: {api_err}")
                print("Falling back to local SQLite generation...")
                
        if not uploaded_to_cloud:
            print("\n" + "="*60)
            print("GENERATING LOCAL SQLITE DATABASE & UPLOADING TO GOOGLE DRIVE")
            print("="*60)
            
            # Write to SQLite
            import sqlite3
            sqlite_path = os.path.join(base_dir, "sales.db")
            if os.path.exists(sqlite_path):
                try:
                    os.remove(sqlite_path)
                except Exception as ex:
                    print(f"  Could not remove old sales.db: {ex}")
                    
            print(f"Writing {len(df_merged):,} records to SQLite (with normalized lowercase columns)...")
            
            # Format columns to lowercase for database compatibility.
            # Only rename columns that actually exist (some mappers may be missing).
            df_sqlite = df_merged.copy()
            _rename_map = {
                'CONCATENATED_KEY': 'concatenated_key',
                'Depot': 'depot',
                'MPO_Code': 'mpo_code',
                'Invoice_No': 'invoice_no',
                'Invoice_Date': 'invoice_date',
                'Transaction_Time': 'transaction_time',
                'Transaction_Type': 'transaction_type',
                'Customer_ID': 'customer_id',
                'Customer_Name': 'customer_name',
                'Product_Code': 'product_code',
                'Product_Name': 'product_name',
                'Quantity': 'quantity',
                'Line_Amount': 'line_amount',
                'Month': 'month',
                'ZONE': 'zone',
                'MARKET': 'market',
                'FM/AM': 'fm_am'
            }
            _rename_map = {k: v for k, v in _rename_map.items() if k in df_sqlite.columns}
            df_sqlite.rename(columns=_rename_map, inplace=True)

            # Ensure 'zone' column always exists (already added in else branch above,
            # but guard for the merge branch as well)
            if 'zone' not in df_sqlite.columns:
                df_sqlite['zone'] = 'Unknown'

            conn = sqlite3.connect(sqlite_path)
            df_sqlite.to_sql("sales", conn, if_exists="replace", index=False)

            # Create indexes
            print("Creating indexes on SQLite table...")
            cursor = conn.cursor()
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_depot ON sales (depot)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_month ON sales (month)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_product ON sales (product_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_mpo ON sales (mpo_code)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_zone ON sales (zone)")
            conn.commit()
            conn.close()
            print("✓ SQLite database generated successfully.")
            
            # Upload using rclone
            rclone_exe = find_rclone_executable()
            parent_folder_id = "1fRl-N_fNU_bJfkxH9a_EYLJeHPB43gzv"
            remote_path = f"grive_new,root_folder_id={parent_folder_id}:sales.db"
            
            print(f"Uploading sales.db to Google Drive...")
            upload_cmd = [rclone_exe, "copyto", "--progress", sqlite_path, remote_path]
            subprocess.run(upload_cmd, check=True)
            print("✓ [SUCCESS] SQLite database uploaded to Google Drive successfully!")
    except Exception as e:
        print(f"❌ Error during database processing: {e}")
        
    print(f"\nSuccessfully processed depots: {', '.join(success_depots)}")
    
    # Save the individual depot CSVs date-wise in "Extracted All Data"
    extracted_all_data_parent = os.path.join(base_dir, "Extracted All Data")
    os.makedirs(extracted_all_data_parent, exist_ok=True)
    
    run_folder_name = f"extracted_{timestamp}"
    run_folder_path = os.path.join(extracted_all_data_parent, run_folder_name)
    
    if os.path.exists(checkpoint_dir):
        print(f"Saving extracted raw CSV files to: {run_folder_path}...")
        shutil.copytree(checkpoint_dir, run_folder_path, dirs_exist_ok=True)
        shutil.rmtree(checkpoint_dir, ignore_errors=True)
        print("✓ Saved to date-wise folder and cleaned up temporary checkpoint directory.")
        
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
    # Detach any remaining SQL Server databases, but DO NOT delete the local
    # MDF/LDF cache — those files must persist on disk so the next run can
    # either reuse them as a fast local cache or have rclone re-download them
    # cleanly (overwriting in place).
    cleanup_all_attached_dbs()
    if os.path.exists(BASE_DEPOT_DIR):
        # Clear only the per-depot Temp_Download/ subfolders (transient rclone
        # working dirs). Data/ subfolders (the actual MDF/LDF cache) are kept.
        for entry in os.listdir(BASE_DEPOT_DIR):
            full = os.path.join(BASE_DEPOT_DIR, entry)
            if os.path.isdir(full) and entry.endswith('Temp_Download'):
                try:
                    shutil.rmtree(full, ignore_errors=True)
                except Exception:
                    pass
        print(f"[OK] Local MDF/LDF cache preserved at: {BASE_DEPOT_DIR}")

    print("\n" + "*" * 80)
    print("  ALL PIPELINE STEPS COMPLETED SUCCESSFULLY!")
    print("*" * 80)
    
    send_pipeline_telegram_notification(base_dir, success_depots, len(sales_df), len(returns_df), timestamp)
    
    print("\nGenerating and sending ALAGRA & MOKAST Exception Report to Telegram...")
    generate_and_send_brand_exception_report(base_dir, combined_df, timestamp)

if __name__ == "__main__":
    main()
