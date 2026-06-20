import os
import sys
import glob
import json
import requests
import pandas as pd

# Reconfigure console output encoding to prevent Windows crash on non-ASCII characters
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
    except:
        pass

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
        raise FileNotFoundError("No date-wise CSV file found!")
    csv_files.sort(key=os.path.getmtime, reverse=True)
    return csv_files[0]

# Load MPO mappings
def load_mpo_mappings():
    mpo_code_xlsx = os.path.join(base_dir, "archive", "recent", "mpo_code.xlsx")
    if os.path.exists(mpo_code_xlsx):
        return pd.read_excel(mpo_code_xlsx)
    return None

# AI Parsing using Groq API
def parse_query_with_ai(query_text, depots_list, zones_list, fm_am_list):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }
    
    system_prompt = f"""You are an AI assistant designed to extract filtering and aggregation parameters from a natural language query for a sales database.

Valid Depots: {', '.join(depots_list)}
Valid Zones: {', '.join(zones_list)}
Some Example FM/AM Names: {', '.join(fm_am_list[:30])}

The database columns and structural fields you can filter by are:
- depot: Match to one of the valid depots. (e.g. 'Faridpur Zone' -> 'FARIDPUR' depot and 'FRD' zone).
- zone: Match to one of the valid zones (e.g. 'FRD', 'BARI', 'COM').
- month: Format YYYY-MM. (e.g. 'january' -> '2026-01', 'April' -> '2026-04', 'May' -> '2026-05', etc.).
- product_brand: e.g. 'ALAGRA', 'MOKAST' (brand name in uppercase).
- product_code: e.g. 'ALK1', 'MON1' (code if explicitly mentioned).
- mpo_code: MPO Code if explicitly mentioned.
- fm_am: The name of the Field Manager / Area Manager from the list.
- market: The name of the market mentioned.
- vacant_only: boolean (true if user asks for vacant markets, vacant MPOs, or vacant forces. Otherwise false).

Aggregation fields:
- group_by: Set to "month" if the user asks for a breakdown by month (e.g., 'kon maase koto sale hoise', 'month-wise', 'monthly sales'). Set to "market" if they ask for market-wise breakdown. Set to "fm_am" if they ask for manager-wise. Set to "mpo_code" if they ask for MPO-wise. Otherwise null.

Return ONLY a JSON object with these keys. No explanation or markdown formatting."""

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
    print("Testing upgraded bot query parser...")
    
    # 1. Load MPO mappings to get unique metadata
    df_mpo = load_mpo_mappings()
    if df_mpo is None:
        print("MPO mapping file not found!")
        return
        
    depots = [str(x) for x in df_mpo['DEPOT'].dropna().unique()]
    zones = [str(x) for x in df_mpo['ZONE'].dropna().unique()]
    fm_ams = [str(x) for x in df_mpo['FM/AM'].dropna().unique()]
    
    # 2. Test query
    query = "Alagra kon maase koto sale hoise? Faridpur Zone e"
    print(f"User query: '{query}'")
    
    intent = parse_query_with_ai(query, depots, zones, fm_ams)
    print(f"Extracted Intent:\n{json.dumps(intent, indent=2)}")
    
    # 3. Load transactions
    latest_csv = get_latest_date_wise_csv()
    print(f"\nLoading {os.path.basename(latest_csv)}...")
    df = pd.read_csv(latest_csv)
    
    # Merge mappings
    df_mpo.rename(columns={'DEPOT': 'DEPOT_mpo', 'MPO CODE': 'MPO_CODE_mpo'}, inplace=True)
    df_merged = pd.merge(df, df_mpo, left_on=['Depot', 'MPO_Code'], right_on=['DEPOT_mpo', 'MPO_CODE_mpo'], how='left')
    
    # Apply filters
    filtered_df = df_merged.copy()
    
    depot = intent.get("depot")
    zone = intent.get("zone")
    month = intent.get("month")
    product_brand = intent.get("product_brand")
    product_code = intent.get("product_code")
    mpo_code = intent.get("mpo_code")
    fm_am = intent.get("fm_am")
    market = intent.get("market")
    vacant_only = intent.get("vacant_only")
    group_by = intent.get("group_by")
    
    if depot:
        filtered_df = filtered_df[filtered_df['Depot'].str.upper() == depot.upper()]
    if zone:
        filtered_df = filtered_df[filtered_df['ZONE'].str.upper() == zone.upper()]
    if month:
        filtered_df = filtered_df[filtered_df['Month'] == month]
    if product_brand:
        filtered_df = filtered_df[filtered_df['Product_Name'].str.contains(product_brand, case=False, na=False)]
    if product_code:
        filtered_df = filtered_df[filtered_df['Product_Code'].str.upper() == product_code.upper()]
    if mpo_code:
        filtered_df = filtered_df[filtered_df['MPO_Code'].str.upper() == mpo_code.upper()]
    if fm_am:
        filtered_df = filtered_df[filtered_df['FM/AM'].str.contains(fm_am, case=False, na=False)]
    if market:
        filtered_df = filtered_df[filtered_df['MARKET'].str.contains(market, case=False, na=False)]
    if vacant_only:
        filtered_df = filtered_df[filtered_df['FM/AM'].str.contains('VACANT', case=False, na=False)]
        
    print(f"Filtered records count: {len(filtered_df):,}")
    
    if filtered_df.empty:
        print("No records found!")
        return
        
    # Check for group_by
    if group_by == 'month':
        print("\n--- MONTHLY BREAKDOWN ---")
        monthly_stats = filtered_df.groupby('Month').agg(
            box_sold=('Quantity', 'sum'),
            sales_amount=('Line_Amount', 'sum'),
            invoices=('Invoice_No', 'nunique'),
            customers=('Customer_ID', 'nunique')
        ).reset_index()
        
        for idx, row in monthly_stats.iterrows():
            print(f"Month: {row['Month']}")
            print(f"  - Boxes Sold: {row['box_sold']:,.2f}")
            print(f"  - Net Sales: {row['sales_amount']:,.2f} TK")
            print(f"  - Invoices: {row['invoices']:,}")
            print(f"  - Customers: {row['customers']:,}")
            print()
    else:
        # Grand total
        total_qty = filtered_df['Quantity'].sum()
        total_amount = filtered_df['Line_Amount'].sum()
        invoices = filtered_df['Invoice_No'].nunique()
        customers = filtered_df['Customer_ID'].nunique()
        print("\n--- GRAND TOTALS ---")
        print(f"Boxes Sold: {total_qty:,.2f}")
        print(f"Net Sales: {total_amount:,.2f} TK")
        print(f"Invoices: {invoices:,}")
        print(f"Customers: {customers:,}")

if __name__ == "__main__":
    main()
