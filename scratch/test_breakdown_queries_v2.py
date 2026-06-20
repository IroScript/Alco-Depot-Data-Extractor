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

def main():
    # 1. Load MPO mappings
    df_mpo = load_mpo_mappings()
    if df_mpo is None:
        print("MPO mapping file not found!")
        return
        
    # Build fallback depot -> zone mapping
    depot_to_zone = df_mpo.groupby('DEPOT')['ZONE'].first().to_dict()
    print("Depot to Zone mapping:")
    print(depot_to_zone)
    
    # 2. Load transactions
    latest_csv = get_latest_date_wise_csv()
    print(f"\nLoading {os.path.basename(latest_csv)}...")
    df = pd.read_csv(latest_csv)
    
    # Merge mappings
    df_mpo.rename(columns={'DEPOT': 'DEPOT_mpo', 'MPO CODE': 'MPO_CODE_mpo'}, inplace=True)
    df_merged = pd.merge(df, df_mpo, left_on=['Depot', 'MPO_Code'], right_on=['DEPOT_mpo', 'MPO_CODE_mpo'], how='left')
    
    # Apply fallback for unmatched MPO zones
    df_merged['ZONE'] = df_merged['ZONE'].fillna(df_merged['Depot'].map(depot_to_zone))
    
    # 3. Test query: "Alagra kon maase koto sale hoise? Faridpur Zone e"
    # Filter by Faridpur Zone (FRD) and Product ALAGRA
    filtered_df = df_merged[(df_merged['ZONE'] == 'FRD') & (df_merged['Product_Name'].str.contains('ALAGRA', case=False, na=False))]
    print(f"\nFiltered records count: {len(filtered_df):,}")
    
    # Monthly breakdown
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

if __name__ == "__main__":
    main()
