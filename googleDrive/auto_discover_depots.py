"""
auto_discover_depots.py — Auto-discover MDF/LDF file IDs for all 11 depots.

For each depot in credentials_master.json's google_drive_folder_map.depots
that has folder_id but missing data_folder_id / key_mdf_file_id / key_ldf_file_id,
this script:
  1. Lists the depot's Drive folder
  2. Recursively searches for ERPonTheNet_Data.MDF and ERPonTheNet_log.LDF
  3. Updates credentials_master.json with the discovered IDs

Run:  python googleDrive/auto_discover_depots.py
"""
import os
import json
import sys
from googleapiclient.discovery import build

# Make sure we can import the loader from the project root
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

from googleDrive.credentials_loader import (
    get_drive_service_account_credentials,
    list_depots,
    _load_master,
    MASTER_PATH,
)

MDF_NAME = 'erponthenet_data.mdf'
LDF_NAME = 'erponthenet_log.ldf'


def search_drive_recursive(service, folder_id, max_depth=4, _depth=0, _path=""):
    """Yield (file_id, file_name) for every file in folder and subfolders."""
    try:
        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed = false",
            pageSize=100,
            fields="files(id, name, mimeType)"
        ).execute()
        for f in results.get('files', []):
            current_path = f"{_path}/{f['name']}" if _path else f['name']
            if f['mimeType'] == 'application/vnd.google-apps.folder':
                if _depth < max_depth:
                    yield from search_drive_recursive(service, f['id'], max_depth, _depth + 1, current_path)
            else:
                yield (f['id'], f['name'], current_path)
    except Exception as e:
        print(f"    [WARN] Could not list folder {folder_id}: {e}")


def find_mdf_ldf(service, folder_id):
    """Find MDF and LDF in a depot's Drive folder. Returns (mdf_id, ldf_id, data_folder_id)."""
    mdf = None
    ldf = None
    data_folder_id = None

    for file_id, file_name, path in search_drive_recursive(service, folder_id):
        name_lower = file_name.lower()
        # Identify the "Data" sub-folder by name
        if file_name == 'Data' or file_name.lower() == 'data':
            # We can't directly get a folder id from this iteration, but
            # data_folder_id is set later by the parent if needed.
            pass
        if name_lower == MDF_NAME and mdf is None:
            mdf = file_id
            print(f"    [FOUND] MDF: {path}  (id={file_id})")
        elif name_lower == LDF_NAME and ldf is None:
            ldf = file_id
            print(f"    [FOUND] LDF: {path}  (id={file_id})")

    # Try to find the immediate "Data" sub-folder
    try:
        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed = false and mimeType='application/vnd.google-apps.folder' and name='Data'",
            pageSize=10,
            fields="files(id, name)"
        ).execute()
        for f in results.get('files', []):
            if f['name'].lower() == 'data':
                data_folder_id = f['id']
                print(f"    [FOUND] Data/ sub-folder  (id={data_folder_id})")
                break
    except Exception as e:
        print(f"    [WARN] Could not look for Data/ sub-folder: {e}")

    return mdf, ldf, data_folder_id


def main():
    print("=" * 80)
    print("  AUTO-DISCOVER DEPOT MDF/LDF FILE IDS")
    print("=" * 80)

    creds = get_drive_service_account_credentials()
    service = build('drive', 'v3', credentials=creds)

    master = _load_master()
    depots = master['google_drive_folder_map']['depots']

    updated = []
    for d in depots:
        name = d['name']
        folder_id = d.get('folder_id')
        if not folder_id:
            continue

        # Skip if everything is already filled
        already_complete = all(d.get(k) for k in ('data_folder_id', 'key_mdf_file_id', 'key_ldf_file_id'))
        if already_complete:
            print(f"\n[{name}] Already complete. Skipping.")
            continue

        print(f"\n[{name}] folder_id={folder_id}")
        mdf, ldf, data_folder = find_mdf_ldf(service, folder_id)

        if mdf:
            d['key_mdf_file_id'] = mdf
        if ldf:
            d['key_ldf_file_id'] = ldf
        if data_folder:
            d['data_folder_id'] = data_folder

        if mdf or ldf or data_folder:
            updated.append(name)
            print(f"  [UPDATED] {name}: data={d.get('data_folder_id')} mdf={d.get('key_mdf_file_id')} ldf={d.get('key_ldf_file_id')}")
        else:
            print(f"  [NOTHING FOUND] No MDF/LDF discovered for {name}")

    # Persist
    with open(MASTER_PATH, 'w', encoding='utf-8') as f:
        json.dump(master, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print(f"  DONE. Updated {len(updated)} depot(s): {updated}")
    print("=" * 80)


if __name__ == '__main__':
    # UTF-8 stdout for Windows console
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
        except Exception:
            pass
    main()
