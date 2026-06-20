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
    print(f"Total rows for BARISHAL in GSheet: {len(barishal_df)}")
    print("\nUnique Zones for BARISHAL:")
    print(barishal_df['ZONE'].unique())
    print("\nUnique FMs/AMs for BARISHAL:")
    print(barishal_df['FM/AM'].unique())
    print("\nSample records for BARISHAL:")
    columns_to_show = ['DEPOT', 'ZONE', 'FM/AM', 'DREAM APPS MPO CODE', 'DEPOTMPO CODE', "MPO NAME, JUN'26"]
    print(barishal_df[columns_to_show].head(15))
