import json
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

config_path = r'c:\Users\Irak\Desktop\Barishal April Data\FieldEdit\config.json'
creds_path = r'c:\Users\Irak\Desktop\Barishal April Data\FieldEdit\alco-pharma-cf4b49e394bb.json'

with open(config_path, 'r') as f:
    config = json.load(f)

scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
client = gspread.authorize(creds)
sheet = client.open_by_key(config['spreadsheet_id'])

# Get worksheet
ws = None
for w in sheet.worksheets():
    if str(w.id) == str(config.get('gid', '1918615875')):
        ws = w
        break
if not ws:
    ws = sheet.get_worksheet(0)

all_values = ws.get_all_values()
if all_values:
    header = all_values[0]
    df = pd.DataFrame(all_values[1:], columns=header)
    barishal_df = df[df['DEPOT'].str.strip().str.upper() == 'BARISHAL']
    print(f"Total rows for BARISHAL: {len(barishal_df)}")
    
    # Group by Zone, FM and print
    grouped = barishal_df.groupby(['ZONE', 'FM/AM'])
    for (zone, fm), group in grouped:
        print(f"\nZone: {zone} | FM/AM: {fm}")
        mpos_in_group = []
        for idx, row in group.iterrows():
            mpo_code = row['DREAM APPS MPO CODE'].strip()
            mpo_name = row["MPO NAME, JUN'26"].strip()
            mpos_in_group.append(f"{mpo_code} ({mpo_name})")
        print("  MPOs:", ", ".join(mpos_in_group))
