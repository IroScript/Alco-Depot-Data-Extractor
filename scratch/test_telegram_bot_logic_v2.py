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
    csv_files.sort(key=os.path.getmtime, reverse=True)
    return csv_files[0]

# Load MPO mappings
def load_mpo_mappings():
    mpo_code_xlsx = os.path.join(base_dir, "archive", "recent", "mpo_code.xlsx")
    if os.path.exists(mpo_code_xlsx):
        return pd.read_excel(mpo_code_xlsx)
    return None

# AI Parsing step 1: Extract Depot and basic info
def extract_depot_with_ai(query_text):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }
    
    system_prompt = """Identify which depot the user is talking about. 
The valid depots are: BARISHAL, CHATTOGRAM, CUMILLA, DHAKA-1, DHAKA-2, FARIDPUR, JASHORE, MYMENSINGH, RAJSHAHI, RANGPUR.
Map variations (e.g. 'Bariahsal' or 'Barishal' -> 'BARISHAL', 'Rangpur' -> 'RANGPUR').
Return a JSON object with a single key 'depot' (string in uppercase, or null if not mentioned)."""

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
    return json.loads(result["choices"][0]["message"]["content"]).get("depot")

# AI Parsing step 2: Extract details using MPO list as context
def extract_details_with_context(query_text, depot, mpo_list):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }
    
    mpo_context = ""
    if mpo_list:
        mpo_context = "Valid markets and MPO Codes for this Depot:\n"
        for m in mpo_list:
            mpo_context += f"- Market: {m['MARKET']} -> MPO Code: {m['MPO CODE']}\n"
            
    system_prompt = f"""You are an AI assistant designed to extract filtering parameters from a natural language query.
Here is the context for the current Depot '{depot}':
{mpo_context}

The database columns / fields to extract are:
- Month: Format YYYY-MM. (e.g. 'january' or 'jan' -> '2026-01', 'April' or 'apr' -> '2026-04', 'May' -> '2026-05', etc. Assume the year is 2026).
- Product_Name: E.g. 'ALAGRA', 'MOKAST'. Extract the base brand name (e.g. 'alagra' -> 'ALAGRA', 'mokast' -> 'MOKAST').
- MPO_Code: Based on the market/MPO mentioned in the query, find the closest matching MPO Code from the list above. If the query mentions 'Barishal 1 Market' and the list has 'BSHL. MEDICAL-1 -> B001', then select 'B001'.
- Customer_Name: Extract if a specific customer name/pharmacy is mentioned in the query.

Return ONLY a JSON object with keys:
- month (string 'YYYY-MM', or null)
- product_brand (string in uppercase like 'ALAGRA', 'MOKAST', or null)
- mpo_code (string from the provided list, or null)
- customer_name (string, or null)

Do not include any explanation, return raw JSON string."""

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
    print("Testing local bot query logic v2...")
    query = "january maase Bariahsal 1 Market e alagra, koto invoice, koto customer , koto box sale hoise"
    print(f"User query: '{query}'")
    
    print("\n1. Detecting Depot...")
    depot = extract_depot_with_ai(query)
    print(f"Detected Depot: {depot}")
    
    mpo_list = []
    if depot:
        df_mpo = load_mpo_mappings()
        if df_mpo is not None:
            # Filter by depot (case insensitive)
            df_depot = df_mpo[df_mpo['DEPOT'].str.upper() == depot.upper()]
            # Convert to list of dicts, handle NaN values
            for idx, row in df_depot.iterrows():
                if pd.notna(row['MARKET']) and pd.notna(row['MPO CODE']):
                    mpo_list.append({
                        "MARKET": str(row['MARKET']).strip(),
                        "MPO CODE": str(row['MPO CODE']).strip()
                    })
            print(f"Loaded {len(mpo_list)} markets/MPOs for depot {depot}.")
            
    print("\n2. Extracting details with MPO context...")
    intent = extract_details_with_context(query, depot, mpo_list)
    print(f"Extracted Details: {json.dumps(intent, indent=2)}")
    
    print("\n3. Loading latest date-wise CSV...")
    latest_csv = get_latest_date_wise_csv()
    print(f"Loading file: {os.path.basename(latest_csv)}")
    df = pd.read_csv(latest_csv)
    print(f"Total rows in CSV: {len(df):,}")
    
    # Apply filtering
    filtered_df = df.copy()
    
    month = intent.get("month")
    product_brand = intent.get("product_brand")
    mpo_code = intent.get("mpo_code")
    customer_name = intent.get("customer_name")
    
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
        
    if customer_name:
        filtered_df = filtered_df[filtered_df['Customer_Name'].str.contains(customer_name, case=False, na=False)]
        print(f"Filtered by Customer={customer_name}: {len(filtered_df):,} rows remaining")
        
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
