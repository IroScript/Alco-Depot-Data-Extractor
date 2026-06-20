import os
import glob
import json
import requests
import pandas as pd

# Load environment variables
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

base_dir = r"c:\Users\Irak\Desktop\Barishal April Data"
env = load_env_variables(os.path.join(base_dir, "googleDrive", "env"))
groq_api_key = env.get("GROQ_API_KEY")

# Find latest date-wise CSV file
def get_latest_date_wise_csv():
    csv_files = glob.glob(os.path.join(base_dir, "01.1_Date_wise_Customer_wise_Product_wise_Net_Sales_Extracted_Data_*.csv"))
    if not csv_files:
        raise FileNotFoundError("No date-wise CSV file found in root directory!")
    # Sort by modification time
    csv_files.sort(key=os.path.getmtime, reverse=True)
    return csv_files[0]

# Load MPO mappings
def load_mpo_mappings():
    mpo_code_xlsx = os.path.join(base_dir, "archive", "recent", "mpo_code.xlsx")
    if os.path.exists(mpo_code_xlsx):
        return pd.read_excel(mpo_code_xlsx)
    return None

# Map market and depot to MPO Code
def map_market_to_mpo(df_mpo, depot, market_name):
    if df_mpo is None:
        return None
    # Filter by Depot (case insensitive)
    df_depot = df_mpo[df_mpo['DEPOT'].str.upper() == depot.upper()]
    if df_depot.empty:
        return None
    
    # Try exact match first
    matches = df_depot[df_depot['MARKET'].str.upper() == market_name.upper()]
    if not matches.empty:
        return matches.iloc[0]['MPO CODE']
        
    # Try normalized matching (remove hyphens, spaces)
    def normalize(s):
        return "".join(str(s).upper().split()).replace("-", "")
        
    norm_market = normalize(market_name)
    for idx, row in df_depot.iterrows():
        if normalize(row['MARKET']) == norm_market:
            return row['MPO CODE']
            
    # Substring matching
    for idx, row in df_depot.iterrows():
        if norm_market in normalize(row['MARKET']) or normalize(row['MARKET']) in norm_market:
            return row['MPO CODE']
            
    return None

# AI Parsing using Groq API
def parse_query_with_ai(query_text):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }
    
    system_prompt = """You are an AI assistant designed to extract filtering parameters from a natural language query for a sales database.
The database has columns:
- Depot: BARISHAL, CHATTOGRAM, CUMILLA, DHAKA-1, DHAKA-2, FARIDPUR, JASHORE, MYMENSINGH, RAJSHAHI, RANGPUR. (Map words like 'Bariahsal' or 'Barishal' to the exact uppercase depot names).
- Month: Format YYYY-MM. (e.g. 'january' or 'jan' -> '2026-01', 'April' or 'apr' -> '2026-04', 'May' -> '2026-05', etc. Assume the year is 2026).
- Product_Name: E.g. 'ALAGRA', 'MOKAST'. Extract the base brand name (e.g. 'alagra' -> 'ALAGRA', 'mokast' -> 'MOKAST').
- Market: The name of the market mentioned (e.g. 'Barishal 1' -> 'BARISHAL-1', 'Burichong' -> 'BURICHONG'). Extract the raw market name.
- MPO_Code: e.g. 'B001'. Extract if explicitly mentioned.

Return ONLY a JSON object with keys:
- depot (string, or null)
- month (string 'YYYY-MM', or null)
- product_brand (string in uppercase like 'ALAGRA', 'MOKAST', or null)
- market (string, or null)
- mpo_code (string, or null)

Do not include any explanation or markdown formatting, return raw JSON string."""

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Query: {query_text}"}
        ],
        "temperature": 0.0,
        "response_format": {"type": "json_object"}
    }
    
    r = requests.post(url, headers=headers, json=data, timeout=30)
    r.raise_for_status()
    result = r.json()
    return json.loads(result["choices"][0]["message"]["content"])

def main():
    print("Testing local bot query logic...")
    query = "january maase Bariahsal 1 Market e alagra, koto invoice, koto customer , koto box sale hoise"
    print(f"User query: '{query}'")
    
    print("\n1. Sending query to Groq API...")
    intent = parse_query_with_ai(query)
    print(f"Extracted Intent: {json.dumps(intent, indent=2)}")
    
    print("\n2. Loading latest date-wise CSV...")
    latest_csv = get_latest_date_wise_csv()
    print(f"Loading file: {os.path.basename(latest_csv)}")
    df = pd.read_csv(latest_csv)
    print(f"Total rows in CSV: {len(df):,}")
    
    print("\n3. Loading MPO mappings...")
    df_mpo = load_mpo_mappings()
    if df_mpo is not None:
        print(f"Loaded {len(df_mpo)} MPO mappings.")
    
    # Apply filtering
    filtered_df = df.copy()
    
    depot = intent.get("depot")
    month = intent.get("month")
    product_brand = intent.get("product_brand")
    market = intent.get("market")
    mpo_code = intent.get("mpo_code")
    
    if depot:
        filtered_df = filtered_df[filtered_df['Depot'].str.upper() == depot.upper()]
        print(f"Filtered by Depot={depot}: {len(filtered_df):,} rows remaining")
        
    if month:
        filtered_df = filtered_df[filtered_df['Month'] == month]
        print(f"Filtered by Month={month}: {len(filtered_df):,} rows remaining")
        
    if product_brand:
        filtered_df = filtered_df[filtered_df['Product_Name'].str.contains(product_brand, case=False, na=False)]
        print(f"Filtered by Product Brand={product_brand}: {len(filtered_df):,} rows remaining")
        
    if mpo_code:
        filtered_df = filtered_df[filtered_df['MPO_Code'].str.upper() == mpo_code.upper()]
        print(f"Filtered by MPO Code={mpo_code}: {len(filtered_df):,} rows remaining")
    elif market and depot and df_mpo is not None:
        mapped_mpo = map_market_to_mpo(df_mpo, depot, market)
        print(f"Mapped market '{market}' in depot '{depot}' to MPO Code: {mapped_mpo}")
        if mapped_mpo:
            filtered_df = filtered_df[filtered_df['MPO_Code'].str.upper() == mapped_mpo.upper()]
            print(f"Filtered by MPO Code={mapped_mpo}: {len(filtered_df):,} rows remaining")
            
    if filtered_df.empty:
        print("Result is empty!")
        return
        
    # Calculate statistics
    invoices = filtered_df['Invoice_No'].nunique()
    customers = filtered_df['Customer_ID'].nunique()
    total_qty = filtered_df['Quantity'].sum()
    total_amount = filtered_df['Line_Amount'].sum()
    
    print("\n--- RESULTS ---")
    print(f"Invoice count: {invoices:,}")
    print(f"Unique customers: {customers:,}")
    print(f"Total box/qty sold: {total_qty:,}")
    print(f"Total net sales amount: {total_amount:,.2f}")

if __name__ == "__main__":
    main()
