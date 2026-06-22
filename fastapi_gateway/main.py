import os
import sys
from typing import List, Optional
from datetime import date, datetime
from fastapi import FastAPI, Header, HTTPException, Depends, status
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import execute_values

# Load env file if not set (useful for local runs)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env_paths = [
    os.path.join(BASE_DIR, "googleDrive", "env"),
    os.path.join(os.path.dirname(BASE_DIR), "googleDrive", "env")
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
DATABASE_URL = os.environ.get("DATABASE_URL") or env_vars.get("DATABASE_URL")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY") or env_vars.get("GROQ_API_KEY")

# Expose keys to the environment so modules we import can access them
if DATABASE_URL and not os.environ.get("DATABASE_URL"):
    os.environ["DATABASE_URL"] = DATABASE_URL
if GROQ_API_KEY and not os.environ.get("GROQ_API_KEY"):
    os.environ["GROQ_API_KEY"] = GROQ_API_KEY

app = FastAPI(title="Alco Pharma ERP API Gateway", version="1.0.0")

# Validate database URL
if not DATABASE_URL:
    print("⚠ WARNING: DATABASE_URL environment variable is not set!")

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

@app.get("/")
def read_root():
    return {"status": "running", "service": "Alco Pharma ERP API Gateway"}

@app.post("/upload/sales", status_code=status.HTTP_201_CREATED)
def upload_sales(records: List[SalesRecord], api_key: str = Depends(verify_api_key)):
    if not DATABASE_URL:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cloud Database URL not configured on server"
        )
        
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Prepare data for bulk upsert
        data_tuples = []
        for r in records:
            # Parse transaction_time to datetime object or string
            t_time = r.transaction_time
            if t_time:
                try:
                    # Clean timestamp format
                    t_time = datetime.strptime(t_time, "%Y-%m-%d %H:%M:%S.%f")
                except:
                    try:
                        t_time = datetime.strptime(t_time, "%Y-%m-%d %H:%M:%S")
                    except:
                        pass
                        
            data_tuples.append((
                r.concatenated_key, r.depot, r.mpo_code, r.invoice_no, r.invoice_date, t_time,
                r.transaction_type, r.customer_id, r.customer_name, r.product_code, r.product_name,
                r.quantity, r.line_amount, r.month, r.zone, r.market, r.fm_am
            ))
            
        # SQL statement for bulk upsert
        upsert_query = """
        INSERT INTO sales (
            concatenated_key, depot, mpo_code, invoice_no, invoice_date, transaction_time,
            transaction_type, customer_id, customer_name, product_code, product_name,
            quantity, line_amount, month, zone, market, fm_am
        ) VALUES %s
        ON CONFLICT (invoice_no, product_code, transaction_type, depot)
        DO UPDATE SET
            quantity = EXCLUDED.quantity,
            line_amount = EXCLUDED.line_amount,
            transaction_time = EXCLUDED.transaction_time,
            customer_name = EXCLUDED.customer_name,
            product_name = EXCLUDED.product_name,
            zone = EXCLUDED.zone,
            market = EXCLUDED.market,
            fm_am = EXCLUDED.fm_am;
        """
        
        # Execute batch upsert using execute_values (highly optimized)
        execute_values(cursor, upsert_query, data_tuples)
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"success": True, "count": len(records)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during insert: {str(e)}"
        )

@app.get("/sales/metadata")
def get_metadata(api_key: str = Depends(verify_api_key)):
    if not DATABASE_URL:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database URL not configured"
        )
    try:
        conn = psycopg2.connect(DATABASE_URL)
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
        parent_dir = os.path.dirname(BASE_DIR)
        if parent_dir not in sys.path:
            sys.path.append(parent_dir)
        
        # Import process_sales_query from telegram_bot
        from telegram_bot import process_sales_query
        
        response_text = process_sales_query(payload.session_id, payload.query)
        return {"response": response_text}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing error: {str(e)}"
        )

