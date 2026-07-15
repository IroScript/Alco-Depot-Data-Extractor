import sqlite3
import os

db_path = r"C:\Users\Irak\Desktop\Barishal April Data - Copy\New folder\Alco-Depot-Data-Extractor\sales.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("Records in sales table for mpo_code = 'B003':")
cur.execute("SELECT DISTINCT zone, fm_am, depot, market FROM sales WHERE mpo_code = 'B003'")
for r in cur.fetchall():
    print(dict(r))
