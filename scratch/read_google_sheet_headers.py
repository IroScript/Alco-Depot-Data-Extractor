import json
import gspread
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from googleDrive.credentials_loader import get_sheet_service_account_credentials, get_spreadsheet_id

scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds = get_sheet_service_account_credentials(scopes=scopes)
client = gspread.authorize(creds)
sheet = client.open_by_key(get_spreadsheet_id('master_field_force_sheet') or '1Q4utivZ5OpgDznqlqElYU-HWNnZYI71YYpcZKcSM3xY')

# Get worksheet (gid from credentials_master.json)
ws = None
for w in sheet.worksheets():
    if str(w.id) == '1918615875':
        ws = w
        break
if not ws:
    ws = sheet.get_worksheet(0)

all_values = ws.get_all_values()
if all_values:
    header = all_values[0]
    print("Total columns:", len(header))
    for i, col in enumerate(header):
        print(f"Col {i}: {col}")
    print("\nRow 1 sample:")
    print(all_values[1])
