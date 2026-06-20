import os
import sys
import psycopg2

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
    print("  ALCO PHARMA ERP - DATABASE INITIALIZATION SCRIPT")
    print("=" * 80)
    
    # Load from env file
    env = load_env(ENV_PATH)
    db_url = env.get("DATABASE_URL") or os.environ.get("DATABASE_URL")
    
    if not db_url:
        print("❌ ERROR: DATABASE_URL not found in googleDrive/env or system environment variables!")
        print("Please configure DATABASE_URL=postgres://user:password@host:port/dbname in googleDrive/env")
        sys.exit(1)
        
    print(f"Connecting to database: {db_url.split('@')[-1]}...")
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # 1. Create Sales Table
        print("Creating table 'sales' if not exists...")
        create_table_query = """
        CREATE TABLE IF NOT EXISTS sales (
            id SERIAL PRIMARY KEY,
            concatenated_key VARCHAR(100) NOT NULL,
            depot VARCHAR(50) NOT NULL,
            mpo_code VARCHAR(50) NOT NULL,
            invoice_no VARCHAR(50) NOT NULL,
            invoice_date DATE NOT NULL,
            transaction_time TIMESTAMP,
            transaction_type VARCHAR(20) NOT NULL,
            customer_id VARCHAR(50) NOT NULL,
            customer_name VARCHAR(150),
            product_code VARCHAR(50) NOT NULL,
            product_name VARCHAR(150),
            quantity NUMERIC(12, 2) NOT NULL,
            line_amount NUMERIC(12, 2) NOT NULL,
            month VARCHAR(10) NOT NULL,
            zone VARCHAR(50),
            market VARCHAR(100),
            fm_am VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT uq_sales_transaction UNIQUE (invoice_no, product_code, transaction_type, depot)
        );
        """
        cursor.execute(create_table_query)
        print("✓ Table 'sales' created.")
        
        # 2. Create Indexes for rapid bot lookup
        print("Creating indexes on search columns...")
        indexes = {
            "idx_sales_depot": "CREATE INDEX IF NOT EXISTS idx_sales_depot ON sales (depot)",
            "idx_sales_month": "CREATE INDEX IF NOT EXISTS idx_sales_month ON sales (month)",
            "idx_sales_product": "CREATE INDEX IF NOT EXISTS idx_sales_product ON sales (product_name)",
            "idx_sales_mpo": "CREATE INDEX IF NOT EXISTS idx_sales_mpo ON sales (mpo_code)",
            "idx_sales_zone": "CREATE INDEX IF NOT EXISTS idx_sales_zone ON sales (zone)"
        }
        
        for name, sql in indexes.items():
            cursor.execute(sql)
            print(f"  ✓ Index {name} checked/created.")
            
        conn.commit()
        cursor.close()
        conn.close()
        print("\n🎉 Database initialization completed successfully!")
    except Exception as e:
        print(f"❌ Connection or Execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
