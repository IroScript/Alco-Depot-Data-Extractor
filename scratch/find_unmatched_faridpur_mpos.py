import pandas as pd
import os
import glob

base_dir = r"c:\Users\Irak\Desktop\Barishal April Data"
latest_csv = glob.glob(os.path.join(base_dir, "01.1_Date_wise_Customer_wise_Product_wise_Net_Sales_Extracted_Data_*.csv"))[0]
df = pd.read_csv(latest_csv)
df_faridpur = df[df['Depot'] == 'FARIDPUR']

mpo_code_xlsx = os.path.join(base_dir, "archive", "recent", "mpo_code.xlsx")
df_mpo = pd.read_excel(mpo_code_xlsx)
df_mpo_faridpur = df_mpo[df_mpo['DEPOT'] == 'FARIDPUR']

print("MPO codes in Faridpur Sales Data:")
sales_mpos = df_faridpur['MPO_Code'].dropna().unique()
print(sorted(sales_mpos))

print("\nMPO codes in Faridpur Mappings:")
map_mpos = df_mpo_faridpur['MPO CODE'].dropna().unique()
print(sorted(map_mpos))

unmatched = set(sales_mpos) - set(map_mpos)
print(f"\nUnmatched MPO codes (exist in Sales but not in Mapping): {unmatched}")
