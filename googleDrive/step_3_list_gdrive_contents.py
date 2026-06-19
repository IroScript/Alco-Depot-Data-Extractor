import os
import re
import json
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

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
    creds_path = r'c:\Users\Irak\Desktop\Barishal April Data\FieldEdit\alco-pharma-cf4b49e394bb.json'
    excel_path = r'c:\Users\Irak\Desktop\Barishal April Data\googleDrive\gDriveDepotLinks.xlsx'
    output_txt = r'c:\Users\Irak\Desktop\Barishal April Data\googleDrive\all_drive_files.txt'
    
    if not os.path.exists(creds_path):
        print(f"Credentials not found at {creds_path}")
        return
        
    scopes = ['https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
    drive_service = build('drive', 'v3', credentials=creds)
    
    df = pd.read_excel(excel_path)
    depot_col = df.columns[0]
    link_col = df.columns[1]
    
    with open(output_txt, 'w', encoding='utf-8') as f_out:
        for idx, row in df.iterrows():
            depot_name = row[depot_col]
            url = row[link_col]
            
            folder_id_match = re.search(r'folders/([a-zA-Z0-9-_]+)', str(url))
            if not folder_id_match:
                continue
                
            folder_id = folder_id_match.group(1)
            f_out.write(f"\n========================================\nDepot: {depot_name} (ID: {folder_id})\n========================================\n")
            list_folder_recursive(drive_service, folder_id, f_out)
            
    print(f"Done! Written to {output_txt}")

if __name__ == '__main__':
    main()
