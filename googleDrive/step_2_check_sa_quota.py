import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

def main():
    creds_path = r'c:\Users\Irak\Desktop\Barishal April Data\FieldEdit\alco-pharma-cf4b49e394bb.json'
    if not os.path.exists(creds_path):
        print(f"Credentials not found at {creds_path}")
        return
        
    scopes = ['https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
    drive_service = build('drive', 'v3', credentials=creds)
    
    try:
        about = drive_service.about().get(fields="storageQuota").execute()
        quota = about.get('storageQuota', {})
        limit = float(quota.get('limit', 0))
        usage = float(quota.get('usage', 0))
        
        limit_gb = limit / (1024**3)
        usage_gb = usage / (1024**3)
        free_gb = (limit - usage) / (1024**3)
        
        print("Service Account Storage Quota:")
        print(f"Limit: {limit_gb:.2f} GB")
        print(f"Usage: {usage_gb:.2f} GB")
        print(f"Free:  {free_gb:.2f} GB")
        
        # Also let's list files in the Service Account's own drive to see what is consuming space
        print("\nListing files in Service Account's own drive:")
        results = drive_service.files().list(
            pageSize=10,
            fields="files(id, name, size, mimeType)"
        ).execute()
        files = results.get('files', [])
        if not files:
            print("No files found.")
        else:
            for f in files:
                size_mb = float(f.get('size', 0)) / (1024**2) if 'size' in f else 0
                print(f"- {f['name']} ({size_mb:.2f} MB, ID: {f['id']})")
    except Exception as e:
        print(f"Error checking quota: {e}")

if __name__ == '__main__':
    main()
