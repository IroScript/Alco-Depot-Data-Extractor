import sqlite3
import os
import sys

db_path = r"C:\Users\Irak\Desktop\Barishal April Data - Copy\New folder\Alco-Depot-Data-Extractor\sales.db"

print("DB Path:", db_path)
if not os.path.exists(db_path):
    print("DB not found!")
    sys.exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Get distinct MPOs in sales db
cur.execute("SELECT COUNT(DISTINCT mpo_code) as cnt FROM sales")
print("Total distinct MPOs in sales table:", cur.fetchone()["cnt"])

# Let's count how many MPOs for product codes of MOKAST 10 TAB: ['MON1', 'MOO1', 'MOP1']
cur.execute("SELECT COUNT(DISTINCT mpo_code) as cnt FROM sales WHERE product_code IN ('MON1', 'MOO1', 'MOP1')")
print("MPOs with MOKAST sales in sales table:", cur.fetchone()["cnt"])

# Let's check how many MPOs in valid_mpos
import sys
BASE_DIR = r"C:\Users\Irak\Desktop\Barishal April Data - Copy\New folder\Alco-Depot-Data-Extractor\TOP_FIELD_FORCE"
sys.path.append(BASE_DIR)
from data_engine import load_mpo_market_lookup, load_valid_master_filters
mpo_market_map = load_mpo_market_lookup()
valid_mpos, valid_fms, valid_zones = load_valid_master_filters(mpo_market_map)
print("Len valid_mpos:", len(valid_mpos))

# Let's see how many valid_mpos have MOKAST sales
ph = ",".join(["?"] * len(valid_mpos))
cur.execute(f"SELECT COUNT(DISTINCT mpo_code) as cnt FROM sales WHERE product_code IN ('MON1', 'MOO1', 'MOP1') AND mpo_code IN ({ph})", valid_mpos)
print("Valid MPOs with MOKAST sales:", cur.fetchone()["cnt"])
