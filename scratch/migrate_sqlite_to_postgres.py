import os
import sys
import sqlite3
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime

# Reconfigure console output encoding to prevent Windows crash on non-ASCII characters
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
    except:
        pass

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

def main():
    print("=" * 80)
    print("  MIGRATING DATA FROM SQLITE TO AIVEN POSTGRESQL")
    print("=" * 80)
    
    # 1. Load configuration
    env = load_env(ENV_PATH)
    db_url = env.get("DATABASE_URL")
    
    if not db_url:
        print("❌ ERROR: DATABASE_URL not configured in googleDrive/env!")
        sys.exit(1)
        
    sqlite_path = os.path.join(BASE_DIR, "sales.db")
    if not os.path.exists(sqlite_path):
        print(f"❌ ERROR: SQLite database 'sales.db' not found at {sqlite_path}!")
        sys.exit(1)
        
    # 2. Read from SQLite
    print("Connecting to local SQLite database...")
    lite_conn = sqlite3.connect(sqlite_path)
    lite_cursor = lite_conn.cursor()
    
    lite_cursor.execute("""
        SELECT 
            concatenated_key, depot, mpo_code, invoice_no, invoice_date, transaction_time,
            transaction_type, customer_id, customer_name, product_code, product_name,
            quantity, line_amount, month, zone, market, fm_am
        FROM sales
    """)
    rows = lite_cursor.fetchall()
    total_records = len(rows)
    print(f"✓ Retrieved {total_records:,} records from SQLite.")
    
    lite_cursor.close()
    lite_conn.close()
    
    if total_records == 0:
        print("⚠ Warning: No data in SQLite to migrate. Exiting.")
        return
        
    # 3. Upload to PostgreSQL
    print(f"\nConnecting to Aiven PostgreSQL database: {db_url.split('@')[-1]}...")
    try:
        pg_conn = psycopg2.connect(db_url)
        pg_cursor = pg_conn.cursor()
        
        # Prepare bulk UPSERT query
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
        
        batch_size = 5000
        print(f"Uploading in batches of {batch_size}...")
        
        start_time = datetime.now()
        for idx in range(0, total_records, batch_size):
            batch = rows[idx : idx + batch_size]
            
            # Format timestamps cleanly
            formatted_batch = []
            for r in batch:
                row_list = list(r)
                # Parse SQLite transaction_time to datetime
                t_time = row_list[5]
                if t_time:
                    try:
                        row_list[5] = datetime.strptime(t_time, "%Y-%m-%d %H:%M:%S.%f")
                    except:
                        try:
                            row_list[5] = datetime.strptime(t_time, "%Y-%m-%d %H:%M:%S")
                        except:
                            pass
                formatted_batch.append(tuple(row_list))
                
            execute_values(pg_cursor, upsert_query, formatted_batch)
            pg_conn.commit()
            print(f"  ✓ Uploaded records {idx:,} to {min(idx + batch_size, total_records):,}")
            
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        pg_cursor.close()
        pg_conn.close()
        print(f"\n🎉 SUCCESS: All {total_records:,} records migrated in {duration:.2f} seconds!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
