import os
import sys
import glob
import json
import time
import requests
import pandas as pd
import sqlite3
import io
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Reconfigure console output encoding to prevent Windows crash on non-ASCII characters
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
    except:
        pass


# ══════════════════════════════════════════════════════════════════
#  Configuration & Environment Loader
# ══════════════════════════════════════════════════════════════════

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, "googleDrive", "env")

def load_env_variables(env_path):
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

ENV = load_env_variables(ENV_PATH)
TELEGRAM_BOT_TOKEN = ENV.get("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = ENV.get("GROQ_API_KEY")

if not TELEGRAM_BOT_TOKEN:
    print("❌ ERROR: TELEGRAM_BOT_TOKEN not found in googleDrive/env!")
    sys.exit(1)
if not GROQ_API_KEY:
    print("❌ ERROR: GROQ_API_KEY not found in googleDrive/env!")
    sys.exit(1)

# ══════════════════════════════════════════════════════════════════
#  Google Drive Sync & Database Downloader
# ══════════════════════════════════════════════════════════════════

def download_sales_db_from_gdrive(base_dir):
    creds_path = os.path.join(base_dir, "FieldEdit", "alco-pharma-cf4b49e394bb.json")
    if not os.path.exists(creds_path):
        print(f"❌ Error: Service account key not found at {creds_path}")
        return False
        
    try:
        print("🔄 Connecting to Google Drive via Service Account...")
        scopes = ['https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
        drive_service = build('drive', 'v3', credentials=creds)
        
        # Parent folder ID where sales.db is located
        parent_folder_id = "1fRl-N_fNU_bJfkxH9a_EYLJeHPB43gzv"
        query = f"'{parent_folder_id}' in parents and name = 'sales.db' and trashed = false"
        
        results = drive_service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])
        
        if not files:
            print("❌ Error: sales.db not found in Google Drive parent folder.")
            return False
            
        file_id = files[0]['id']
        print(f"✓ Found sales.db on Drive (ID: {file_id}). Downloading...")
        
        local_db_path = os.path.join(base_dir, "sales.db")
        request = drive_service.files().get_media(fileId=file_id)
        
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"  Download progress: {int(status.progress() * 100)}%")
            
        with open(local_db_path, "wb") as f:
            f.write(fh.getvalue())
            
        print(f"✓ SQLite database successfully synced locally to: {local_db_path}")
        return True
    except Exception as e:
        print(f"❌ Error downloading sales.db from Google Drive: {e}")
        return False

# ══════════════════════════════════════════════════════════════════
#  Data Manager (Handles SQLite Connection & Metadata Loading)
# ══════════════════════════════════════════════════════════════════

class SalesDataManager:
    def __init__(self):
        self.depots_list = []
        self.zones_list = []
        self.fm_ams_list = []
        
        # Initial check/load
        self.check_and_load_data()

    def get_db_connection(self):
        db_url = ENV.get("DATABASE_URL")
        if db_url:
            try:
                import psycopg2
                return psycopg2.connect(db_url)
            except Exception as e:
                print(f"⚠ Warning: Failed to connect to PostgreSQL ({e}). Falling back to local SQLite...")
        
        sqlite_path = os.path.join(BASE_DIR, "sales.db")
        return sqlite3.connect(sqlite_path)

    def get_db_placeholder(self):
        db_url = ENV.get("DATABASE_URL")
        if db_url:
            return "%s"
        return "?"

    def check_and_load_data(self):
        db_url = ENV.get("DATABASE_URL")
        if db_url:
            return self.load_metadata()
            
        db_path = os.path.join(BASE_DIR, "sales.db")
        if not os.path.exists(db_path):
            print("sales.db not found locally. Syncing from Google Drive...")
            download_sales_db_from_gdrive(BASE_DIR)
            
        if os.path.exists(db_path):
            return self.load_metadata()
        return False

    def load_metadata(self):
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Fetch depots
            cursor.execute("SELECT DISTINCT depot FROM sales WHERE depot IS NOT NULL")
            self.depots_list = sorted([str(row[0]) for row in cursor.fetchall()])
            
            # Fetch zones
            cursor.execute("SELECT DISTINCT zone FROM sales WHERE zone IS NOT NULL")
            self.zones_list = sorted([str(row[0]) for row in cursor.fetchall()])
            
            # Fetch fm_ams
            cursor.execute("SELECT DISTINCT fm_am FROM sales WHERE fm_am IS NOT NULL")
            self.fm_ams_list = sorted([str(row[0]) for row in cursor.fetchall()])
            
            cursor.close()
            conn.close()
            print(f"✓ Loaded metadata (Depots: {len(self.depots_list)}, Zones: {len(self.zones_list)}, Managers: {len(self.fm_ams_list)})")
            return True
        except Exception as e:
            print(f"⚠ Warning: Failed to query metadata from database: {e}")
            return False

    def get_mpo_list_for_depot(self, depot_name):
        mpo_list = []
        if depot_name:
            try:
                conn = self.get_db_connection()
                cursor = conn.cursor()
                placeholder = self.get_db_placeholder()
                cursor.execute(
                    f"SELECT DISTINCT market, mpo_code FROM sales WHERE UPPER(depot) = {placeholder} AND market IS NOT NULL AND mpo_code IS NOT NULL", 
                    (depot_name.upper(),)
                )
                for row in cursor.fetchall():
                    mpo_list.append({
                        "MARKET": str(row[0]).strip(),
                        "MPO CODE": str(row[1]).strip()
                    })
                cursor.close()
                conn.close()
            except Exception as e:
                print(f"Error querying MPO list for depot {depot_name}: {e}")
        return mpo_list

# Instantiate Data Manager
DATA_MANAGER = SalesDataManager()


# ══════════════════════════════════════════════════════════════════
#  Chat Session Context Manager (For follow-up questions)
# ══════════════════════════════════════════════════════════════════

class ChatSessionManager:
    def __init__(self):
        self.sessions = {}  # chat_id -> list of message dicts

    def get_history(self, chat_id):
        if chat_id not in self.sessions:
            self.sessions[chat_id] = []
        return self.sessions[chat_id]

    def add_message(self, chat_id, role, content):
        history = self.get_history(chat_id)
        history.append({"role": role, "content": content})
        # Keep only the last 6 messages (3 turns) to prevent context bloat
        if len(history) > 6:
            self.sessions[chat_id] = history[-6:]

    def clear_session(self, chat_id):
        self.sessions[chat_id] = []

# Instantiate Session Manager
SESSION_MANAGER = ChatSessionManager()

# ══════════════════════════════════════════════════════════════════
#  Groq AI Intent Parser (Context Aware & Upgraded)
# ══════════════════════════════════════════════════════════════════

def extract_depot_with_ai(query_text, history_messages=None):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    system_prompt = f"""Identify which depot the user is talking about. 
The valid depots are: {', '.join(DATA_MANAGER.depots_list)}.
Map common variations (e.g. 'Bariahsal' or 'Barisal' -> 'BARISHAL', 'Chittagong' -> 'CHATTOGRAM', 'Comilla' -> 'CUMILLA', 'Faridpur Zone' -> 'FARIDPUR', 'Dhaka 1' -> 'DHAKA-1', 'Dhaka 2' -> 'DHAKA-2').

This is a chat context. If the user's latest query does not mention a depot, but the previous conversation did, you should refer to the history to identify the depot.
Return a JSON object with a single key 'depot' (string in uppercase, or null if not mentioned and cannot be inferred. Never return "Unknown", "ALL", "None", or "Null" as a string)."""

    # Build messages with history
    messages = [{"role": "system", "content": system_prompt}]
    if history_messages:
        for msg in history_messages[:-1]:
            if msg["role"] == "assistant":
                try:
                    js = json.loads(msg["content"])
                    messages.append({"role": "assistant", "content": f"Active Depot: {js.get('depot')}"})
                except:
                    messages.append(msg)
            else:
                messages.append(msg)
                
    messages.append({"role": "user", "content": f"Query: {query_text}"})

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.0,
        "response_format": {"type": "json_object"}
    }
    
    try:
        r = requests.post(url, headers=headers, json=data, timeout=15)
        r.raise_for_status()
        result = r.json()
        return json.loads(result["choices"][0]["message"]["content"]).get("depot")
    except Exception as e:
        print(f"  [AI] Error detecting depot: {e}")
        return None

def extract_query_intent(query_text, depot, mpo_list, history_messages=None):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    mpo_context = ""
    if mpo_list:
        mpo_context = "Valid markets and MPO Codes for this Depot:\n"
        for m in mpo_list:
            mpo_context += f"- Market: {m['MARKET']} -> MPO Code: {m['MPO CODE']}\n"
            
    system_prompt = f"""You are an AI assistant designed to extract filtering and aggregation parameters from a natural language query for a sales database.
Here is the context for the current Depot '{depot or "Unknown"}':
{mpo_context}

Valid Zones (e.g. 'FRD' is Faridpur Zone, 'BARI' is Barishal Zone): {', '.join(DATA_MANAGER.zones_list)}
Some Example FM/AM Names: {', '.join(DATA_MANAGER.fm_ams_list[:20])}

The database fields to extract are:
- month: Format YYYY-MM. (e.g. 'january', 'jan' -> '2026-01', 'April', 'apr' -> '2026-04', 'May' -> '2026-05', etc. Assume the year is 2026).
- product_brand: Must match one of these brand names (in uppercase): ALAGRA, MOKAST, DOMPI, ESOPRA, BETASEF, OMEPRA, AMDIN, AXECLAV, CALMI, ECOX, ROSVIN, SAVER, STAFLU, VERTIG, ZINEX, ACIPRA, ACLO, ADNIX, BENDIL, BROLYT, CLOPIDOL, DAZINE, DIRIN, DUMAFLOX, EMISET, EPIZAM, GLUVIL, LEAXE, LEBROD, LEOFLOX, LEVOCET, LOSA, METMIN, MOXIFLOX, NOLAR, NOLER, OTICEF, PANTOPRA, RUPALER, SAPOX, TIEMO, TIXOL, TOLEC, TOSMA, VERTIC, VIEV, ZIVIT.
- product_code: E.g. 'ALK1', 'MON1' (code if explicitly mentioned).
- mpo_code: Match from MPO code list, or if explicitly mentioned.
- zone: Match to a valid zone code (e.g. 'FRD', 'BARI', 'COM').
- fm_am: The name of the Field Manager / Area Manager.
- market: The name of the market mentioned.
- vacant_only: boolean (true if user asks for vacant markets, vacant MPOs, or vacant forces. Otherwise false).

Aggregation fields:
- group_by: Set to "month" if the user asks for a breakdown by month (e.g. 'kon maase koto sale hoise', 'month-wise', 'monthly sales'). Set to "market" if they ask for market-wise breakdown. Set to "fm_am" if they ask for manager-wise. Set to "mpo_code" if they ask for MPO-wise. Otherwise null.

This is a chat conversation. If the user's latest query is a follow-up, inherit parameters from previous assistant's JSON responses in the history, unless explicitly changed.

Return ONLY a JSON object with keys:
- depot (string, or null. If not specified or refers to all depots, set to null. Never return "Unknown", "ALL", or "None" as a string)
- month (string 'YYYY-MM', or null)
- product_brand (string, or null)
- product_code (string, or null)
- mpo_code (string, or null)
- zone (string, or null)
- fm_am (string, or null)
- market (string, or null)
- vacant_only (boolean)
- group_by (string: "month", "market", "fm_am", "mpo_code", or null)

Do not include any explanation or markdown formatting, return raw JSON string."""

    # Build messages with history
    messages = [{"role": "system", "content": system_prompt}]
    if history_messages:
        for msg in history_messages[:-1]:
            messages.append(msg)
    messages.append({"role": "user", "content": f"Query: {query_text}"})

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.0,
        "response_format": {"type": "json_object"}
    }
    
    try:
        r = requests.post(url, headers=headers, json=data, timeout=20)
        r.raise_for_status()
        result = r.json()
        return json.loads(result["choices"][0]["message"]["content"])
    except Exception as e:
        print(f"  [AI] Error extracting query intent: {e}")
        return {}

# ══════════════════════════════════════════════════════════════════
#  Query Processor (Filters Data & Formats Response)
# ══════════════════════════════════════════════════════════════════

def process_sales_query(chat_id, query_text):
    # Ensure latest data is loaded
    DATA_MANAGER.check_and_load_data()
    
    db_url = ENV.get("DATABASE_URL")
    if not db_url:
        db_path = os.path.join(BASE_DIR, "sales.db")
        if not os.path.exists(db_path):
            return "❌ Error: Sales database file is not loaded or not found. Please ask the Admin to run the pipeline first."
        
    print(f"\nProcessing query for Chat {chat_id}: '{query_text}'")
    
    # Get history for this session
    history = SESSION_MANAGER.get_history(chat_id)
    # Temporary append user query for the detection step
    temp_msg = {"role": "user", "content": query_text}
    history.append(temp_msg)
    
    # Helper function to normalize parameters (map Unknown/ALL/None/Null to None)
    def normalize_param(val):
        if val is None:
            return None
        if isinstance(val, str):
            val_clean = val.strip()
            if val_clean.lower() in ["unknown", "all", "none", "null", "any", "undefined", ""]:
                return None
            return val_clean
        return val

    # 1. Detect Depot (Context Aware)
    depot = extract_depot_with_ai(query_text, history)
    depot = normalize_param(depot)
    print(f"  Depot detected: {depot}")
    
    # 2. Get markets list for this depot
    mpo_list = DATA_MANAGER.get_mpo_list_for_depot(depot)
    
    # 3. Extract details using AI with MPO context and full history
    intent = extract_query_intent(query_text, depot, mpo_list, history)
    
    # Normalize all extracted parameters in the intent dict
    for key in ["depot", "month", "product_brand", "product_code", "mpo_code", "zone", "fm_am", "market"]:
        intent[key] = normalize_param(intent.get(key))
        
    print(f"  Extracted Intent (Normalized): {json.dumps(intent)}")
    
    # Update the depot if intent found a different one
    if intent.get("depot"):
        depot = intent["depot"]
        
    # Standardize intent by injecting the detected depot
    intent["depot"] = depot
    
    # Store this turn in history (we remove the temporary user message and add structured ones)
    history.pop()  # remove temp user message
    SESSION_MANAGER.add_message(chat_id, "user", query_text)
    SESSION_MANAGER.add_message(chat_id, "assistant", json.dumps(intent))
    
    month = intent.get("month")
    product_brand = intent.get("product_brand")
    product_code = intent.get("product_code")
    mpo_code = intent.get("mpo_code")
    zone = intent.get("zone")
    fm_am = intent.get("fm_am")
    market = intent.get("market")
    vacant_only = intent.get("vacant_only")
    group_by = intent.get("group_by")
    
    # 4. Build Query
    conditions = []
    params = []
    placeholder = DATA_MANAGER.get_db_placeholder()
    
    if depot:
        conditions.append(f"UPPER(depot) = {placeholder}")
        params.append(depot.upper())
    if zone:
        conditions.append(f"UPPER(zone) = {placeholder}")
        params.append(zone.upper())
    if month:
        conditions.append(f"month = {placeholder}")
        params.append(month)
    if product_brand:
        conditions.append(f"product_name LIKE {placeholder}")
        params.append(f"%{product_brand}%")
    if product_code:
        conditions.append(f"UPPER(product_code) = {placeholder}")
        params.append(product_code.upper())
    if mpo_code:
        conditions.append(f"UPPER(mpo_code) = {placeholder}")
        params.append(mpo_code.upper())
    if fm_am:
        conditions.append(f"fm_am LIKE {placeholder}")
        params.append(f"%{fm_am}%")
    if market:
        conditions.append(f"market LIKE {placeholder}")
        params.append(f"%{market}%")
    if vacant_only:
        conditions.append(f"fm_am LIKE {placeholder}")
        params.append("%VACANT%")
        
    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)
        
    conn = DATA_MANAGER.get_db_connection()
    cursor = conn.cursor()
    
    # Check if empty first
    cursor.execute(f"SELECT COUNT(*) FROM sales {where_clause}", params)
    total_records = cursor.fetchone()[0]
    
    if total_records == 0:
        cursor.close()
        conn.close()
        # Build friendly empty-result message
        filters = []
        if depot: filters.append(f"Depot: {depot}")
        if zone: filters.append(f"Zone: {zone}")
        if month: filters.append(f"Month: {month}")
        if product_brand: filters.append(f"Product: {product_brand}")
        if mpo_code: filters.append(f"MPO: {mpo_code}")
        if fm_am: filters.append(f"Manager: {fm_am}")
        if market: filters.append(f"Market: {market}")
        if vacant_only: filters.append("Vacant Markets Only")
        
        filter_str = ", ".join(filters) if filters else "No filters"
        return f"⚠️ *No records found matching your query.*\n\n*Applied Filters:* {filter_str}\n\nPlease verify your query details and try again."

    # 5. Build response Markdown message
    msg_lines = [
        "📊 *SALES REPORT SUMMARY*",
        "=========================================",
        f"🔍 *Query:* \"{query_text}\"",
        "",
        "📍 *Filter Details:*"
    ]
    
    if depot:
        msg_lines.append(f"▪️ *Depot:* {depot}")
    else:
        msg_lines.append("▪️ *Depot:* ALL")
        
    if zone:
        msg_lines.append(f"▪️ *Zone:* {zone}")
    if month:
        try:
            dt = datetime.strptime(month, "%Y-%m")
            msg_lines.append(f"▪️ *Month:* {dt.strftime('%B %Y')}")
        except:
            msg_lines.append(f"▪️ *Month:* {month}")
            
    if product_brand:
        msg_lines.append(f"▪️ *Product:* {product_brand}")
    if product_code:
        msg_lines.append(f"▪️ *Product Code:* {product_code}")
    if mpo_code:
        market_display = None
        try:
            cursor.execute(
                f"SELECT DISTINCT market FROM sales WHERE UPPER(mpo_code) = {placeholder} AND UPPER(depot) = {placeholder} AND market IS NOT NULL LIMIT 1",
                (mpo_code.upper(), (depot or "").upper())
            )
            match_row = cursor.fetchone()
            if match_row:
                market_display = match_row[0]
        except Exception as e:
            print(f"Error querying market display: {e}")
            
        mpo_info = f"{mpo_code}"
        if market_display:
            mpo_info += f" ({market_display})"
        msg_lines.append(f"▪️ *Market/MPO:* {mpo_info}")
        
    if fm_am:
        msg_lines.append(f"▪️ *Manager (FM/AM):* {fm_am}")
    if market and not mpo_code:
        msg_lines.append(f"▪️ *Market:* {market}")
    if vacant_only:
        msg_lines.append("▪️ *Forces:* VACANT ONLY")
        
    msg_lines.append("=========================================")

    # 6. Aggregation & Formatting
    if group_by:
        group_col = None
        group_label = ""
        order_by = ""
        
        if group_by == 'month':
            group_col = 'month'
            group_label = 'Monthly breakdown'
            order_by = "month ASC"
        elif group_by == 'market':
            group_col = 'market'
            group_label = 'Market-wise breakdown (Top 15)'
            order_by = "box_sold DESC"
        elif group_by == 'fm_am':
            group_col = 'fm_am'
            group_label = 'Manager-wise breakdown (Top 15)'
            order_by = "box_sold DESC"
        elif group_by == 'mpo_code':
            group_col = 'mpo_code'
            group_label = 'MPO-wise breakdown (Top 15)'
            order_by = "box_sold DESC"
            
        # Group stats
        query = f"""
            SELECT 
                {group_col} AS group_col,
                SUM(quantity) AS box_sold,
                SUM(line_amount) AS sales_amount,
                COUNT(DISTINCT invoice_no) AS invoices,
                COUNT(DISTINCT customer_id) AS customers
            FROM sales
            {where_clause}
            GROUP BY {group_col}
            ORDER BY {order_by}
        """
        if group_by != 'month':
            query += " LIMIT 15"
            
        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            msg_lines.append(f"📈 *{group_label}:*")
            
            for row in rows:
                col_val = row[0]
                box_sold = float(row[1]) if row[1] is not None else 0.0
                sales_amount = float(row[2]) if row[2] is not None else 0.0
                invoices_cnt = int(row[3]) if row[3] is not None else 0
                customers_cnt = int(row[4]) if row[4] is not None else 0
                
                # Format month name
                if group_by == 'month':
                    try:
                        dt = datetime.strptime(str(col_val), "%Y-%m")
                        col_val = dt.strftime("%b %Y")
                    except:
                        pass
                
                # Format amounts
                box_str = f"{box_sold:,.2f} Boxes"
                amt_str = f"{sales_amount:,.2f} TK"
                inv_str = f"{invoices_cnt:,} Inv"
                cus_str = f"{customers_cnt:,} Cus"
                
                msg_lines.append(f"▪️ *{col_val}:* {box_str} ({amt_str}, {inv_str}, {cus_str})")
                
            # Grand total
            cursor.execute(f"SELECT SUM(quantity), SUM(line_amount) FROM sales {where_clause}", params)
            gt_row = cursor.fetchone()
            total_qty = float(gt_row[0]) if gt_row[0] is not None else 0.0
            total_amount = float(gt_row[1]) if gt_row[1] is not None else 0.0
            
            msg_lines.extend([
                "-----------------------------------------",
                f"🧮 *Grand Total:* *{total_qty:,.2f} Boxes* ({total_amount:,.2f} TK)"
            ])
        except Exception as e:
            print(f"Error querying group breakdown: {e}")
            msg_lines.append(f"⚠ Aggregation field '{group_by}' could not be processed.")
            
    else:
        # Standard grand totals output
        cursor.execute(f"""
            SELECT 
                SUM(quantity), 
                SUM(line_amount), 
                COUNT(DISTINCT invoice_no), 
                COUNT(DISTINCT customer_id) 
            FROM sales 
            {where_clause}
        """, params)
        gt_row = cursor.fetchone()
        total_qty = float(gt_row[0]) if gt_row[0] is not None else 0.0
        total_amount = float(gt_row[1]) if gt_row[1] is not None else 0.0
        invoices = int(gt_row[2]) if gt_row[2] is not None else 0
        customers = int(gt_row[3]) if gt_row[3] is not None else 0
        
        msg_lines.extend([
            "📈 *Calculated Statistics:*",
            f"▪️ *Total Box Sold:* *{total_qty:,.2f}*",
            f"▪️ *Total Net Sales:* *{total_amount:,.2f} TK*",
            f"▪️ *Total Invoices:* *{invoices:,}*",
            f"▪️ *Unique Customers:* *{customers:,}*"
        ])
        
    msg_lines.append("=========================================")
    cursor.close()
    conn.close()
    return "\n".join(msg_lines)


# ══════════════════════════════════════════════════════════════════
#  Telegram Bot Core & Long Polling Loop
# ══════════════════════════════════════════════════════════════════

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"❌ Error sending message to {chat_id}: {e}")

def handle_start_command(chat_id):
    SESSION_MANAGER.clear_session(chat_id)
    welcome_text = """👋 *Hello! I am the Alco Pharma Sales Query Bot.*

I can query the latest sales transaction report generated by the Admin and give you quick stats on demand.

ℹ️ *What you can ask me (Bangla or English):*
▪️ "january maase Bariahsal 1 Market e alagra koto box sale hoise"
▪️ "chattogram depot e may maase mokast koto invoice aar customer cilo"
▪️ "B001 mpo code er alagra total sales amount koto"
▪️ "Alagra kon maase koto sale hoise? Faridpur Zone e"

💬 *Note:* I remember the context of the chat! If you ask a follow-up question, I will keep your previous filters (like month or product) active!

To reset context and start fresh, type `/reset` or `/start`.

Just type your question below! 👇"""
    send_telegram_message(chat_id, welcome_text)

def handle_reset_command(chat_id):
    SESSION_MANAGER.clear_session(chat_id)
    send_telegram_message(chat_id, "🔄 *Chat context has been reset.* You can start a new query now.")

def main_loop():
    print("=" * 80)
    print("  TELEGRAM SALES QUERY BOT - RUNNING (SQLITE + GOOGLE DRIVE SYNC)")
    print("=" * 80)
    print(f"Bot Token: {TELEGRAM_BOT_TOKEN[:15]}...")
    db_path = os.path.join(BASE_DIR, "sales.db")
    if os.path.exists(db_path):
        print(f"Active SQLite DB: sales.db")
    else:
        print("Active SQLite DB: None (waiting for file sync)")
    print("Bot is listening for messages... Press Ctrl+C to exit.\n")
    
    offset = None
    
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
            params = {"timeout": 30}
            if offset:
                params["offset"] = offset
                
            response = requests.get(url, params=params, timeout=35)
            if response.status_code != 200:
                print(f"⚠ Telegram API returned status {response.status_code}. Retrying...")
                time.sleep(5)
                continue
                
            updates = response.json().get("result", [])
            
            for update in updates:
                offset = update["update_id"] + 1
                
                if "message" not in update:
                    continue
                    
                message = update["message"]
                chat_id = message["chat"]["id"]
                user_info = message["chat"].get("username") or message["chat"].get("first_name") or "User"
                
                if "text" not in message:
                    continue
                    
                text = message["text"].strip()
                print(f"📩 Received message from {user_info} ({chat_id}): '{text}'")
                
                # Check for commands
                if text.startswith("/start") or text.startswith("/help"):
                    handle_start_command(chat_id)
                    continue
                elif text.startswith("/reset"):
                    handle_reset_command(chat_id)
                    continue
                elif text.startswith("/reload"):
                    send_telegram_message(chat_id, "🔄 *Syncing sales database from Google Drive...*")
                    if download_sales_db_from_gdrive(BASE_DIR):
                        DATA_MANAGER.check_and_load_data()
                        send_telegram_message(chat_id, "✅ *Database reload complete!* Using the latest data.")
                    else:
                        send_telegram_message(chat_id, "❌ *Failed to reload database.* Please check server logs.")
                    continue
                
                # Process query
                send_telegram_message(chat_id, "⏳ *Processing your query... please wait.*")
                
                try:
                    response_text = process_sales_query(chat_id, text)
                except Exception as ex:
                    print(f"❌ Error processing query: {ex}")
                    response_text = "❌ *An error occurred while processing your query.* Please make sure the query format is correct."
                    
                send_telegram_message(chat_id, response_text)
                print(f"📤 Sent reply to {user_info} ({chat_id})")
                
        except KeyboardInterrupt:
            print("\nShutting down bot...")
            break
        except Exception as e:
            print(f"⚠ Loop Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main_loop()
