import os
import sys
import shutil
import zipfile
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, "googleDrive", "env")

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

ENV = load_env(ENV_PATH)
API_URL = ENV.get("API_GATEWAY_URL", "http://127.0.0.1:8000") # PythonAnywhere URL
API_KEY = ENV.get("API_KEY", "alco_secure_api_key_2026")

def create_zip():
    zip_path = os.path.join(BASE_DIR, "erp_setup.zip")
    print("📦 Packaging files into erp_setup.zip...")
    
    # List of files/folders to include in deployment package
    items = [
        "telegram_bot.py",
        "init_db.py",
        "googleDrive",
        "FieldEdit",
        "fastapi_gateway",
        "step_1_extract_Product_Level_Net_Sales_csv.py",
        "step_2_generate_MPO_Target_vs_Achievement_report.py",
        "step_3_generate_Zone_Wise_Product_Sales_Report.py",
        "step_4_analyze_Zone_Wise_Product_Sales_Report.py",
        "manual_single_click_auto_run_no_need__following_steps.py",
        "auto_single_click_auto_run_no_need__following_steps.py",
        "above_5_box",
        "telegram_notifier.py",
        "local_gateway_sync.py",
        "sales.db"
    ]
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for item in items:
            item_path = os.path.join(BASE_DIR, item)
            if not os.path.exists(item_path):
                continue
            if os.path.isdir(item_path):
                for root, dirs, files in os.walk(item_path):
                    # Skip __pycache__ folders and archives
                    if "__pycache__" in root or "Archive" in root:
                        continue
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, BASE_DIR)
                        zipf.write(file_path, arcname)
            else:
                zipf.write(item_path, item)
                
    print(f"✅ Created zip successfully at {zip_path} (Size: {os.path.getsize(zip_path)/(1024*1024):.2f} MB)")
    return zip_path

def deploy_to_pythonanywhere():
    zip_path = create_zip()
    
    # PythonAnywhere API credentials from env
    pa_username = ENV.get("PYTHONANYWHERE_USERNAME", "storealco")
    pa_token = ENV.get("PYTHONANYWHERE_API_TOKEN") # Add PYTHONANYWHERE_API_TOKEN in googleDrive/env
    
    if not pa_token:
        print("\n❌ Error: PYTHONANYWHERE_API_TOKEN not found in googleDrive/env.")
        print("Please configure PYTHONANYWHERE_API_TOKEN=your_token inside googleDrive/env.")
        print("Create a token at: PythonAnywhere Account page -> API Token tab.")
        return False
        
    headers = {
        "Authorization": f"Token {pa_token}"
    }
    
    # 1. Upload Zip File using PythonAnywhere Files API
    upload_url = f"https://www.pythonanywhere.com/api/v0/user/{pa_username}/files/path/home/{pa_username}/erp_setup.zip"
    print(f"\n📤 Uploading erp_setup.zip to PythonAnywhere...")
    
    try:
        with open(zip_path, "rb") as f:
            files = {"content": f}
            r = requests.post(upload_url, headers=headers, files=files, timeout=120)
            
        if r.status_code in [200, 201]:
            print("✅ File uploaded successfully.")
        else:
            print(f"❌ Upload failed: HTTP {r.status_code} - {r.text}")
            return False
            
        # 2. Run remote unzip and pkill/restart telegram bot via Console API
        console_create_url = f"https://www.pythonanywhere.com/api/v0/user/{pa_username}/consoles/"
        print("\n⚙️ Opening remote PythonAnywhere console to extract & restart bot...")
        
        # Command sequence to extract zip and restart bot
        cmd = (
            "unzip -o erp_setup.zip && "
            "pkill -f telegram_bot.py ; "
            "workon erp_env && "
            "nohup python telegram_bot.py > bot.log 2>&1 &"
        )
        
        console_payload = {
            "executable": "bash",
            "arguments": f"-c \"{cmd}\""
        }
        
        console_res = requests.post(console_create_url, headers=headers, json=console_payload, timeout=30)
        if console_res.status_code == 201:
            print("✅ Remote extraction and bot restart triggered.")
        else:
            # Fallback warning if console limit reached
            print(f"⚠️ Console trigger HTTP {console_res.status_code}. (You may need to manually run: unzip -o erp_setup.zip && pkill -f telegram_bot.py ; workon erp_env && nohup python telegram_bot.py > bot.log 2>&1 &)")
            
        # 3. Reload Web App (FastAPI Gateway)
        domain = f"{pa_username}.pythonanywhere.com"
        reload_url = f"https://www.pythonanywhere.com/api/v0/user/{pa_username}/webapps/{domain}/reload/"
        print(f"\n🔄 Reloading Web App ({domain})...")
        
        webapp_res = requests.post(reload_url, headers=headers, timeout=30)
        if webapp_res.status_code == 200:
            print("✅ FastAPI Web App reloaded successfully!")
            print("\n🎉 ERP Deployment completed successfully!")
            return True
        else:
            print(f"❌ Web App reload failed: HTTP {webapp_res.status_code} - {webapp_res.text}")
            return False
            
    except Exception as e:
        print(f"❌ Deployment connection error: {e}")
        return False

if __name__ == "__main__":
    deploy_to_pythonanywhere()
