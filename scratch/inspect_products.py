import pandas as pd
import glob
import os

csv_files = glob.glob(r'c:\Users\Irak\Desktop\Barishal April Data\01_Product_Level_Net_Sales_Extracted_Data_*.csv')
if csv_files:
    latest_file = max(csv_files, key=os.path.getmtime)
    print("Reading latest CSV:", latest_file)
    df = pd.read_csv(latest_file)
    print("Columns:", df.columns.tolist())
    print("\nTotal rows:", len(df))
    
    # Search for ALAGRA and MOKAST
    alagra = df[df['Product_Name'].str.contains('ALAGRA', case=False, na=False)]
    mokast = df[df['Product_Name'].str.contains('MOKAST', case=False, na=False)]
    
    print("\nALAGRA products found:")
    print(alagra[['Product_Code', 'Product_Name']].drop_duplicates())
    
    print("\nMOKAST products found:")
    print(mokast[['Product_Code', 'Product_Name']].drop_duplicates())
    
    print("\nSample unique MPOs:")
    print(df['MPO_Code'].dropna().unique()[:10])
    
    print("\nSample unique Depots:")
    print(df['Depot'].dropna().unique())
else:
    print("No CSV files found matching pattern.")
