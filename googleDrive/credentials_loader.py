"""
credentials_loader.py — Load Google credentials from credentials_master.json (in-memory).

This module ELIMINATES the need for scattered JSON credential files throughout the project.
Instead of having:
  - googleDrive/service_account.json
  - googleDrive/driveautomation-499816-645466ddac74.json
  - googleDrive/alco-pharma-69bef270eefd.json
  - FieldEdit/alco-pharma-cf4b49e394bb.json
  - googleDrive/client_secret_*.json
...all credentials live in a SINGLE file: googleDrive/credentials_master.json

This loader reads that master file and provides:
  - get_drive_service_account_credentials() — returns SA #1 (Drive) credentials object
  - get_sheet_service_account_credentials() — returns SA #2 (Sheets) credentials object
  - get_oauth_client_config() — returns OAuth client config dict
  - get_env_var(key) — returns env var from the master file's env section

Usage in any script (replaces hardcoded JSON path):
    from googleDrive.credentials_loader import get_drive_service_account_credentials
    creds = get_drive_service_account_credentials()
    service = build('drive', 'v3', credentials=creds)

Note: This module NEVER writes any JSON files to disk. All credentials stay in memory.
"""
import os
import json
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google.oauth2.credentials import Credentials as OAuthCredentials

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
MASTER_PATH = os.path.join(SCRIPT_DIR, "credentials_master.json")

# Module-level cache so we don't re-parse the JSON for every call
_master_cache = None


def _load_master():
    """Load and cache credentials_master.json."""
    global _master_cache
    if _master_cache is None:
        if not os.path.exists(MASTER_PATH):
            raise FileNotFoundError(
                f"credentials_master.json not found at {MASTER_PATH}.\n"
                f"Please bring the master file from your secure channel and place it there.\n"
                f"(See googleDrive/credentials_master.example.json for the schema.)"
            )
        with open(MASTER_PATH, "r", encoding="utf-8") as f:
            _master_cache = json.load(f)
    return _master_cache


def _make_sa_credentials(sa_dict, scopes):
    """Build a google-auth Credentials object from a SA dict (in-memory)."""
    # google-auth expects the dict to have a 'type' == 'service_account' and a 'private_key'.
    # We pass the dict directly via from_service_account_info (no file I/O).
    return ServiceAccountCredentials.from_service_account_info(sa_dict, scopes=scopes)


def get_drive_service_account_credentials(scopes=None):
    """Return SA #1 credentials for Google Drive access (alcodrivestorage@...)."""
    if scopes is None:
        scopes = ["https://www.googleapis.com/auth/drive"]
    master = _load_master()
    sa_dict = master["service_accounts"]["sa_1_drive_automation"]["json_content"]
    return _make_sa_credentials(sa_dict, scopes)


def get_sheet_service_account_credentials(scopes=None):
    """Return SA #2 credentials for Google Sheets access (drive-sheet-automation@...)."""
    if scopes is None:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
    master = _load_master()
    sa_dict = master["service_accounts"]["sa_2_sheet_automation"]["json_content"]
    return _make_sa_credentials(sa_dict, scopes)


def get_oauth_client_config():
    """Return the OAuth client config dict (for user-flow OAuth)."""
    master = _load_master()
    return master["oauth_client"]["json_content"]


def get_env_var(key, default=None):
    """Return an env var from the master file's env section (parsed)."""
    master = _load_master()
    env_lines = master.get("env_file_content", {}).get("content", [])
    for line in env_lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            if k.strip() == key:
                return v.strip()
    return default


def get_drive_folder_id(depot_name):
    """Return the Drive folder_id for a given depot name (e.g., 'BARISHAL')."""
    master = _load_master()
    for depot in master.get("google_drive_folder_map", {}).get("depots", []):
        if depot["name"].upper() == depot_name.upper():
            return depot.get("folder_id")
    return None


def get_data_folder_id(depot_name):
    """Return the Drive 'Data/' subfolder_id for a given depot name."""
    master = _load_master()
    for depot in master.get("google_drive_folder_map", {}).get("depots", []):
        if depot["name"].upper() == depot_name.upper():
            return depot.get("data_folder_id")
    return None


def get_spreadsheet_id(name="master_field_force_sheet"):
    """Return a Google Sheets spreadsheet_id by name."""
    master = _load_master()
    return master.get("google_sheets", {}).get(name, {}).get("spreadsheet_id")


def list_depots():
    """Return list of all depot dicts from the master file."""
    master = _load_master()
    return master.get("google_drive_folder_map", {}).get("depots", [])


def get_gmail_account():
    """Return the Gmail account info dict."""
    master = _load_master()
    return master.get("_sole_gmail_account", {})


# ────────────────────────────────────────────────────────────────
# Self-test
# ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Reconfigure stdout to UTF-8 so Windows console can print Unicode chars (em-dash, arrow)
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
        except Exception:
            pass

    print("=" * 80)
    print(f"  credentials_master.json loader — self-test")
    print("=" * 80)

    master = _load_master()
    print(f"\n[OK] Master file loaded: {os.path.relpath(MASTER_PATH, PROJECT_DIR)}")
    print(f"[OK] Gmail account: {get_gmail_account().get('login_email', 'N/A')}")

    print(f"\n[SA #1] Drive automation:")
    sa1 = master["service_accounts"]["sa_1_drive_automation"]
    print(f"        client_email: {sa1['json_content']['client_email']}")
    print(f"        project_id:   {sa1['json_content']['project_id']}")
    print(f"        private_key_id: {sa1['json_content']['private_key_id']}")
    creds1 = get_drive_service_account_credentials()
    print(f"        Credentials object: {type(creds1).__name__}, valid={creds1.valid}, scopes={list(creds1.scopes)}")

    print(f"\n[SA #2] Sheet automation:")
    sa2 = master["service_accounts"]["sa_2_sheet_automation"]
    print(f"        client_email: {sa2['json_content']['client_email']}")
    print(f"        project_id:   {sa2['json_content']['project_id']}")
    print(f"        private_key_id: {sa2['json_content']['private_key_id']}")
    creds2 = get_sheet_service_account_credentials()
    print(f"        Credentials object: {type(creds2).__name__}, valid={creds2.valid}, scopes={list(creds2.scopes)}")

    print(f"\n[OAuth] Client config:")
    oauth = get_oauth_client_config()
    print(f"        client_id:     {oauth['installed']['client_id']}")
    print(f"        project_id:    {oauth['installed']['project_id']}")
    print(f"        redirect_uris: {oauth['installed']['redirect_uris']}")

    print(f"\n[Depots] Found {len(list_depots())} depot(s) in master file:")
    for d in list_depots():
        data_ok = 'YES' if d.get('data_folder_id') else '---'
        mdf_ok = 'YES' if d.get('key_mdf_file_id') else '---'
        print(f"   - {d['name']:<12} folder_id={d['folder_id']:<35} data={data_ok} mdf={mdf_ok}")

    print(f"\n[Sheets]")
    print(f"   master_field_force: {get_spreadsheet_id('master_field_force_sheet')}")
    print(f"   secondary:          {get_spreadsheet_id('secondary_sheet')}")

    print(f"\n[Env vars] Sample lookups:")
    for k in ["TELEGRAM_BOT_TOKEN", "GROQ_API_KEY", "PYTHONANYWHERE_USERNAME"]:
        v = get_env_var(k)
        if v:
            masked = v[:4] + "***" + v[-4:] if len(v) > 8 else "***"
            print(f"   {k} = {masked}")

    print(f"\n[Folder IDs] Sample depot lookups:")
    for depot in ["BARISHAL", "DHAKA-1", "DHAKA-2", "SYLHET", "FARIDPUR"]:
        print(f"   {depot:<10} folder_id={get_drive_folder_id(depot)}  data_folder_id={get_data_folder_id(depot)}")

    print("\n" + "=" * 80)
    print("  All credential lookups succeeded — master file is properly configured.")
    print("=" * 80)