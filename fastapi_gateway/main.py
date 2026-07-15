import os
import sys
import shutil
import sqlite3
from typing import List, Optional
from datetime import date, datetime
from fastapi import FastAPI, Header, HTTPException, Depends, status
from pydantic import BaseModel

# Load env file if not set (useful for local runs)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
env_paths = [
    os.path.join(BASE_DIR, "googleDrive", "env"),
    os.path.join(PARENT_DIR, "googleDrive", "env")
]
env_vars = {}
for path in env_paths:
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        env_vars[parts[0].strip()] = parts[1].strip()
        break

API_KEY = os.environ.get("API_KEY") or env_vars.get("API_KEY", "alco_secure_api_key_2026")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY") or env_vars.get("GROQ_API_KEY")

# Expose key to env
if GROQ_API_KEY and not os.environ.get("GROQ_API_KEY"):
    os.environ["GROQ_API_KEY"] = GROQ_API_KEY

# Set Local SQLite database path (hosted inside the parent directory of fastapi_gateway)
DB_PATH = os.path.join(PARENT_DIR, "sales.db")
BACKUP_DB_PATH = os.path.join(PARENT_DIR, "sales_backup.db")

app = FastAPI(title="Alco Pharma ERP API Gateway", version="1.0.0")

# Dependency to check API Key
def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return x_api_key

# Pydantic Model for Sales Record
class SalesRecord(BaseModel):
    concatenated_key: str
    depot: str
    mpo_code: str
    invoice_no: str
    invoice_date: str
    transaction_time: str
    transaction_type: str
    customer_id: str
    customer_name: str
    product_code: str
    product_name: str
    quantity: float
    line_amount: float
    month: str
    zone: Optional[str] = None
    market: Optional[str] = None
    fm_am: Optional[str] = None

# Pydantic Model for Bulk Upload Wrapper
class UploadPayload(BaseModel):
    extraction_time: str # Format YYYY-MM-DD HH:MM:SS (local PC sync time)
    records: List[SalesRecord]

@app.get("/")
def read_root():
    return {"status": "running", "service": "Alco Pharma ERP API Gateway (SQLite Mode)"}

@app.post("/upload/sales", status_code=status.HTTP_201_CREATED)
def upload_sales(payload: UploadPayload, api_key: str = Depends(verify_api_key)):
    records = payload.records
    if not records:
        return {"success": True, "count": 0, "message": "No records supplied"}
        
    # Backup current DB before modification to ensure rollbacks
    db_existed = os.path.exists(DB_PATH)
    if db_existed:
        try:
            shutil.copy2(DB_PATH, BACKUP_DB_PATH)
        except Exception as backup_ex:
            print(f"Failed to create database backup: {backup_ex}")
            
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 1. Initialize tables if they don't exist yet
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concatenated_key TEXT NOT NULL,
                depot TEXT NOT NULL,
                mpo_code TEXT NOT NULL,
                invoice_no TEXT NOT NULL,
                invoice_date TEXT NOT NULL,
                transaction_time TEXT,
                transaction_type TEXT NOT NULL,
                customer_id TEXT NOT NULL,
                customer_name TEXT,
                product_code TEXT NOT NULL,
                product_name TEXT,
                quantity REAL NOT NULL,
                line_amount REAL NOT NULL,
                month TEXT NOT NULL,
                zone TEXT,
                market TEXT,
                fm_am TEXT,
                sync_status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_sales_transaction UNIQUE (invoice_no, product_code, transaction_type, depot)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS depot_sync_meta (
                depot_name TEXT PRIMARY KEY,
                last_sync_time TEXT NOT NULL,
                last_uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'SUCCESS'
            )
        """)
        conn.commit()
        
        # 2. Identify all depots present in the incoming payload
        depots_to_update = list(set([r.depot.upper() for r in records]))
        
        # 3. Incremental Delete: Clear old records for ONLY the incoming depots
        for depot_name in depots_to_update:
            cursor.execute("DELETE FROM sales WHERE UPPER(depot) = ?", (depot_name,))
            
        # 4. Bulk Insert new rows
        insert_query = """
            INSERT INTO sales (
                concatenated_key, depot, mpo_code, invoice_no, invoice_date, transaction_time,
                transaction_type, customer_id, customer_name, product_code, product_name,
                quantity, line_amount, month, zone, market, fm_am
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        data_tuples = []
        for r in records:
            data_tuples.append((
                r.concatenated_key, r.depot, r.mpo_code, r.invoice_no, r.invoice_date, r.transaction_time,
                r.transaction_type, r.customer_id, r.customer_name, r.product_code, r.product_name,
                r.quantity, r.line_amount, r.month, r.zone, r.market, r.fm_am
            ))
            
        cursor.executemany(insert_query, data_tuples)
        
        # 5. Update depot sync metadata timestamps
        for depot_name in depots_to_update:
            # Find original cased name from records
            orig_name = next((r.depot for r in records if r.depot.upper() == depot_name), depot_name)
            cursor.execute("""
                INSERT INTO depot_sync_meta (depot_name, last_sync_time, last_uploaded_at, status)
                VALUES (?, ?, datetime('now'), 'SUCCESS')
                ON CONFLICT(depot_name) DO UPDATE SET
                    last_sync_time = EXCLUDED.last_sync_time,
                    last_uploaded_at = EXCLUDED.last_uploaded_at,
                    status = 'SUCCESS'
            """, (orig_name, payload.extraction_time))
            
        conn.commit()
        cursor.close()
        conn.close()
        
        # Remove backup file on successful transaction commit
        if os.path.exists(BACKUP_DB_PATH):
            try:
                os.remove(BACKUP_DB_PATH)
            except:
                pass
                
        return {"success": True, "count": len(records), "depots_updated": depots_to_update}
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        # Restore backup if transaction failed
        if db_existed and os.path.exists(BACKUP_DB_PATH):
            try:
                shutil.copy2(BACKUP_DB_PATH, DB_PATH)
            except Exception as restore_ex:
                print(f"Failed to restore database from backup: {restore_ex}")
                
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during merge upload: {str(e)}"
        )

@app.get("/sales/metadata")
def get_metadata(api_key: str = Depends(verify_api_key)):
    if not os.path.exists(DB_PATH):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Database file not found"
        )
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT depot FROM sales WHERE depot IS NOT NULL")
        depots = sorted([r[0] for r in cursor.fetchall()])
        
        cursor.execute("SELECT DISTINCT zone FROM sales WHERE zone IS NOT NULL")
        zones = sorted([r[0] for r in cursor.fetchall()])
        
        cursor.execute("SELECT DISTINCT fm_am FROM sales WHERE fm_am IS NOT NULL")
        fm_ams = sorted([r[0] for r in cursor.fetchall()])
        
        cursor.close()
        conn.close()
        
        return {
            "depots": depots,
            "zones": zones,
            "fm_ams": fm_ams
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Pydantic Model for Chat Request
class ChatPayload(BaseModel):
    session_id: str
    query: str

@app.post("/api/chat")
def chat_endpoint(payload: ChatPayload, api_key: str = Depends(verify_api_key)):
    try:
        # Dynamically add the parent directory to sys.path so we can import telegram_bot
        if PARENT_DIR not in sys.path:
            sys.path.append(PARENT_DIR)
        
        # Import process_sales_query from telegram_bot
        from telegram_bot import process_sales_query
        
        response_text = process_sales_query(payload.session_id, payload.query)
        return {"response": response_text}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing error: {str(e)}"
        )

# Mounting the Dashboard directory as a static folder to serve index.html directly from PythonAnywhere
from fastapi.staticfiles import StaticFiles
static_dir = os.path.join(PARENT_DIR, "Dashboard")
if os.path.exists(static_dir):
    app.mount("/Dashboard", StaticFiles(directory=static_dir, html=True), name="static")

