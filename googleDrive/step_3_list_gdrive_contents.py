import os
import re
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from credentials_loader import get_drive_service_account_credentials, list_depots

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_TXT = os.path.join(SCRIPT_DIR, 'all_drive_files.txt')

def list_folder_recursive(drive_service, folder_id, f_out, indent="  ", depth=1, max_depth=4):
    if depth > max_depth:
        return
        
    try:
        query = f"'{folder_id}' in parents and trashed = false"
        results = drive_service.files().list(
            q=query,
            pageSize=100,
            fields="nextPageToken, files(id, name, mimeType, createdTime, modifiedTime, size)"
        ).execute()
        
        files = results.get('files', [])
        for f in files:
            name = f['name']
            file_id = f['id']
            mime = f['mimeType']
            size_str = f.get('size', 'N/A')
            
            if size_str != 'N/A':
                size_mb = f"{float(size_str)/(1024*1024):.2f} MB"
            else:
                size_mb = "DIR"
                
            f_out.write(f"{indent}- [{mime}] {name} (ID: {file_id}, Size: {size_mb})\n")
            
            if mime == 'application/vnd.google-apps.folder':
                list_folder_recursive(drive_service, file_id, f_out, indent + "  ", depth + 1, max_depth)
    except Exception as e:
        f_out.write(f"{indent}[ERROR] {e}\n")

def main():
    creds = get_drive_service_account_credentials()
    drive_service = build('drive', 'v3', credentials=creds)
    output_txt = OUTPUT_TXT

    # Depot list now comes from credentials_master.json via the loader.
    depots = list_depots()

    with open(output_txt, 'w', encoding='utf-8') as f_out:
        for depot in depots:
            depot_name = depot['name']
            folder_id = depot.get('folder_id')
            if not folder_id:
                continue
            f_out.write(f"\n========================================\nDepot: {depot_name} (ID: {folder_id})\n========================================\n")
            list_folder_recursive(drive_service, folder_id, f_out)

    print(f"Done! Written to {output_txt}")

if __name__ == '__main__':
    main()
