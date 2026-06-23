import os
import sys
import sqlite3
import requests
from datetime import datetime

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

def get_config():
    # Use pythonanywhere url or localhost for testing
    api_url = ENV.get("API_GATEWAY_URL", "http://127.0.0.1:8000")
    api_key = ENV.get("API_KEY", "alco_secure_api_key_2026")
    return api_url, api_key

def sync_depots_to_gateway(depot_filter=None):
    db_path = os.path.join(BASE_DIR, "sales.db")
    if not os.path.exists(db_path):
        print(f"❌ Error: Local sales.db not found at {db_path}")
        return False
        
    api_url, api_key = get_config()
    upload_url = f"{api_url.rstrip('/')}/upload/sales"
    
    print("=" * 80)
    print("  INCREMENTAL GATEWAY SYNC SCRIPT")
    print("=" * 80)
    print(f"Target API Endpoint: {upload_url}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Determine depots to sync
        if depot_filter:
            depots = [depot_filter]
        else:
            cursor.execute("SELECT DISTINCT depot FROM sales WHERE depot IS NOT NULL")
            depots = [row[0] for row in cursor.fetchall()]
            
        print(f"Found depots to sync: {', '.join(depots)}")
        
        # Get current extraction/sync timestamp
        extraction_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for depot in depots:
            print(f"\n🔄 Fetching records for depot: {depot}...")
            cursor.execute("""
                SELECT 
                    concatenated_key, depot, mpo_code, invoice_no, invoice_date, transaction_time,
                    transaction_type, customer_id, customer_name, product_code, product_name,
                    quantity, line_amount, month, zone, market, fm_am
                FROM sales
                WHERE UPPER(depot) = ?
            """, (depot.upper(),))
            
            rows = cursor.fetchall()
            if not rows:
                print(f"⚠️ No records found locally for depot: {depot}. Skipping...")
                continue
                
            print(f"✓ Found {len(rows)} records. Packaging payload...")
            
            records_list = []
            for row in rows:
                records_list.append({
                    "concatenated_key": str(row[0]),
                    "depot": str(row[1]),
                    "mpo_code": str(row[2]),
                    "invoice_no": str(row[3]),
                    "invoice_date": str(row[4]),
                    "transaction_time": str(row[5]) if row[5] else "",
                    "transaction_type": str(row[6]),
                    "customer_id": str(row[7]),
                    "customer_name": str(row[8]) if row[8] else "",
                    "product_code": str(row[9]),
                    "product_name": str(row[10]) if row[10] else "",
                    "quantity": float(row[11]),
                    "line_amount": float(row[12]),
                    "month": str(row[13]),
                    "zone": str(row[14]) if row[14] else None,
                    "market": str(row[15]) if row[15] else None,
                    "fm_am": str(row[16]) if row[16] else None
                })
                
            payload = {
                "extraction_time": extraction_time,
                "records": records_list
            }
            
            # Post to gateway api
            headers = {
                "x-api-key": api_key,
                "Content-Type": "application/json"
            }
            
            print(f"📤 Uploading {depot} data to FastAPI gateway...")
            response = requests.post(upload_url, json=payload, headers=headers, timeout=60)
            
            if response.status_code == 201:
                res_data = response.json()
                print(f"✅ Successful sync: {res_data.get('count')} records updated.")
            else:
                print(f"❌ Failed to sync: HTTP {response.status_code} - {response.text}")
                
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Sync error: {e}")
        return False

if __name__ == "__main__":
    depot_arg = sys.argv[1] if len(sys.argv) > 1 else None
    sync_depots_to_gateway(depot_arg)
