import sqlite3

def run_test():
    conn = sqlite3.connect('sales.db')
    cursor = conn.cursor()
    
    print("=== FIELD MANAGERS (FM) EXAMPLES ===")
    cursor.execute("""
        SELECT 
            fm_am, 
            COUNT(DISTINCT market) as total_mkt, 
            COUNT(DISTINCT CASE WHEN "VACANT (JUN'26)?" IN ('Y', 'YES', 'TRUE', '1') THEN market END) as vacant_mkt 
        FROM sales 
        WHERE fm_am IS NOT NULL AND fm_am != '' AND fm_am != 'VACANT'
        GROUP BY fm_am 
        LIMIT 5
    """)
    for row in cursor.fetchall():
        fm, total, vacant = row
        actual = total - vacant
        print(f"FM: {fm:<20} | Total Markets: {total:<3} | Vacant: {vacant:<2} | Actual Markets: {actual}")
        
    print("\n=== ZONES (SM) EXAMPLES ===")
    cursor.execute("""
        SELECT 
            SM, 
            COUNT(DISTINCT market) as total_mkt, 
            COUNT(DISTINCT CASE WHEN "VACANT (JUN'26)?" IN ('Y', 'YES', 'TRUE', '1') THEN market END) as vacant_mkt 
        FROM sales 
        WHERE SM IS NOT NULL AND SM != '' AND SM != 'VACANT'
        GROUP BY SM 
        LIMIT 5
    """)
    for row in cursor.fetchall():
        sm, total, vacant = row
        actual = total - vacant
        print(f"Zone (SH): {sm:<20} | Total Markets: {total:<3} | Vacant: {vacant:<2} | Actual Markets: {actual}")

if __name__ == "__main__":
    run_test()
