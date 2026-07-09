import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from credentials_loader import get_drive_service_account_credentials

def list_folder_recursive(drive_service, folder_id, indent="  "):
    try:
        query = f"'{folder_id}' in parents and trashed = false"
        results = drive_service.files().list(
            q=query,
            pageSize=100,
            fields="files(id, name, mimeType, size)"
        ).execute()
        
        files = results.get('files', [])
        if not files:
            print(f"{indent}(empty)")
            return
            
        for f in files:
            name = f['name']
            file_id = f['id']
            mime = f['mimeType']
            size_str = f.get('size', 'N/A')
            
            if size_str != 'N/A':
                size_mb = f"{float(size_str)/(1024*1024):.2f} MB"
            else:
                size_mb = "DIR"
                
            print(f"{indent}- [{mime}] {name} (ID: {file_id}, Size: {size_mb})")
            if mime == 'application/vnd.google-apps.folder':
                list_folder_recursive(drive_service, file_id, indent + "  ")
    except Exception as e:
        print(f"{indent}[ERROR] {e}")

def main():
    creds = get_drive_service_account_credentials()
    drive_service = build('drive', 'v3', credentials=creds)
    target_id = '17vBESDDaZL-Gf-0h4MzKZYrVRUxQD_2W'

    print(f"Listing target folder {target_id} recursively...")
    list_folder_recursive(drive_service, target_id)

if __name__ == '__main__':
    main()
