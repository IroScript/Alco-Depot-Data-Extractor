import os
import glob
import pandas as pd

base_dir = r"c:\Users\Irak\Desktop\Barishal April Data"

def get_latest_date_wise_csv():
    csv_files = glob.glob(os.path.join(base_dir, "01.1_Date_wise_Customer_wise_Product_wise_Net_Sales_Extracted_Data_*.csv"))
    if not csv_files:
        raise FileNotFoundError("No date-wise CSV file found!")
    csv_files.sort(key=os.path.getmtime, reverse=True)
    return csv_files[0]

def main():
    latest_csv = get_latest_date_wise_csv()
    print(f"Loading {os.path.basename(latest_csv)} for verification...")
    df = pd.read_csv(latest_csv)
    print(f"Loaded {len(df):,} records.\n")
    
    # -------------------------------------------------------------
    # VERIFICATION 1: Alagra Total May 2026 (Whole country)
    # -------------------------------------------------------------
    v1 = df[(df['Month'] == '2026-05') & (df['Product_Name'].str.contains('ALAGRA', case=False, na=False))]
    print("--- Verification 1: Alagra, May 2026, Whole Country ---")
    print(f"Number of rows matching: {len(v1)}")
    print(f"Total Box Sold (Quantity sum): {v1['Quantity'].sum():,.2f}")
    print(f"Total Net Sales Amount: {v1['Line_Amount'].sum():,.2f}")
    print(f"Unique Invoices: {v1['Invoice_No'].nunique()}")
    print(f"Unique Customers: {v1['Customer_ID'].nunique()}")
    print("-" * 50)
    
    # -------------------------------------------------------------
    # VERIFICATION 2: Only Barishal Depot (All products, all months)
    # -------------------------------------------------------------
    v2 = df[df['Depot'].str.upper() == 'BARISHAL']
    print("\n--- Verification 2: Depot = BARISHAL (All Products, All Months) ---")
    print(f"Number of rows matching: {len(v2)}")
    print(f"Total Box Sold (Quantity sum): {v2['Quantity'].sum():,.2f}")
    print(f"Total Net Sales Amount: {v2['Line_Amount'].sum():,.2f}")
    print(f"Unique Invoices: {v2['Invoice_No'].nunique()}")
    print(f"Unique Customers: {v2['Customer_ID'].nunique()}")
    print("-" * 50)
    
    # -------------------------------------------------------------
    # VERIFICATION 3: Barishal Depot + Alagra + May 2026 (Context-aware check)
    # -------------------------------------------------------------
    v3 = df[(df['Depot'].str.upper() == 'BARISHAL') & 
            (df['Month'] == '2026-05') & 
            (df['Product_Name'].str.contains('ALAGRA', case=False, na=False))]
    print("\n--- Verification 3: Depot = BARISHAL, Product = ALAGRA, Month = May 2026 ---")
    print(f"Number of rows matching: {len(v3)}")
    print(f"Total Box Sold (Quantity sum): {v3['Quantity'].sum():,.2f}")
    print(f"Total Net Sales Amount: {v3['Line_Amount'].sum():,.2f}")
    print(f"Unique Invoices: {v3['Invoice_No'].nunique()}")
    print(f"Unique Customers: {v3['Customer_ID'].nunique()}")
    print("-" * 50)

if __name__ == "__main__":
    main()
