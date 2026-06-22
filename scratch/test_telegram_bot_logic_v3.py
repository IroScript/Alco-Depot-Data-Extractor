import sys
import os
import json

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram_bot import process_sales_query, download_sales_db_from_gdrive

def test_queries():
    print("=== TESTING SQLITE BOT QUERY PROCESSING ===")
    
    # Query 1: Country-wide query for Dompi in April
    q1 = "Dompi koto Box sale hoise April maase?"
    print(f"\nQuery 1: {q1}")
    res1 = process_sales_query(12345, q1)
    print(res1)
    
    # Query 2: Country-wide query for Mokast in March
    q2 = "Mokast Koto Box sale hoise march maase?"
    print(f"\nQuery 2: {q2}")
    res2 = process_sales_query(12345, q2)
    print(res2)
    
    # Query 3: Depot-specific query
    q3 = "Barishal depot e May maase Alagra sales koto?"
    print(f"\nQuery 3: {q3}")
    res3 = process_sales_query(12345, q3)
    print(res3)

    # Query 4: Group by breakdown query
    q4 = "Alagra kon maase koto sale hoise? Faridpur Zone e"
    print(f"\nQuery 4: {q4}")
    res4 = process_sales_query(12345, q4)
    print(res4)

if __name__ == "__main__":
    test_queries()
