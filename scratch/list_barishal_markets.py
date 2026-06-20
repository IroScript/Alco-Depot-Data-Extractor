import pandas as pd
import os

base_dir = r"c:\Users\Irak\Desktop\Barishal April Data"
mpo_code_xlsx = os.path.join(base_dir, "archive", "recent", "mpo_code.xlsx")
df = pd.read_excel(mpo_code_xlsx)
df_barishal = df[df['DEPOT'] == 'BARISHAL']
print(df_barishal[['MARKET', 'MPO CODE']])
