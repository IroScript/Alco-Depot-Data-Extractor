import pandas as pd
import os

base_dir = r"c:\Users\Irak\Desktop\Barishal April Data"
mpo_code_xlsx = os.path.join(base_dir, "archive", "recent", "mpo_code.xlsx")
df = pd.read_excel(mpo_code_xlsx)

print("Unique Depots:")
print(df['DEPOT'].dropna().unique())

print("\nUnique Zones:")
print(df['ZONE'].dropna().unique())

print("\nSample FM/AM names:")
print(df['FM/AM'].dropna().unique()[:20])

print("\nCheck a specific row for Faridpur Zone:")
print(df[df['DEPOT'].str.contains('FARIDPUR', case=False, na=False)].head(5))
