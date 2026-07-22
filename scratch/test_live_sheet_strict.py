import os
import sys
import pandas as pd

# Add parent directory to path so we can import googleDrive loader
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PARENT_DIR)

from googleDrive.credentials_loader import get_sheet_service_account_credentials, get_spreadsheet_id
import gspread

def get_live_sheet_data_strict():
    try:
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = get_sheet_service_account_credentials(scopes=scopes)
        client = gspread.authorize(creds)
        sheet_id = '1Q4utivZ5OpgDznqlqElYU-HWNnZYI71YYpcZKcSM3xY'
        sheet = client.open_by_key(sheet_id)
        
        # Load worksheet by gid 1918615875
        target_gid = '1918615875'
        worksheet = None
        for ws in sheet.worksheets():
            if str(ws.id) == target_gid:
                worksheet = ws
                break
        if not worksheet:
            worksheet = sheet.get_worksheet(0)
            
        print(f"Connected! Worksheet: '{worksheet.title}'")
        all_values = worksheet.get_all_values()
        
        header = all_values[0]
        data_rows = []
        
        # Rule: If Column A (DEPOT) is blank, stop taking any rows below it.
        for r_idx in range(1, len(all_values)):
            row = all_values[r_idx]
            if len(row) == 0 or row[0].strip() == "":
                break
            data_rows.append(row)
            
        df = pd.DataFrame(data_rows, columns=header)
        
        fm_col = 'FM/AM'
        sm_col = 'ZONE'  # The user explicitly said: ZONE column is Sector Head (SH/Zone)
        mkt_col = 'MARKET'
        vacant_col = "VACANT (JUN'26)?"
        
        print(f"Columns used -> SH/Zone (from column 'ZONE'): '{sm_col}', FM: '{fm_col}', Market: '{mkt_col}', Vacant: '{vacant_col}'")
        
        df[sm_col] = df[sm_col].astype(str).str.strip().str.upper().fillna('VACANT')
        df[fm_col] = df[fm_col].astype(str).str.strip().str.upper().fillna('VACANT')
        df[mkt_col] = df[mkt_col].astype(str).str.strip().str.upper()
        df[vacant_col] = df[vacant_col].astype(str).str.strip().str.upper().fillna('')
        
        print("\n=== SECTOR HEAD (using ZONE column) COUNTS ===")
        sms = df[sm_col].unique()
        count_sm = 0
        for sm in sorted(sms):
            if not sm or sm == 'VACANT':
                continue
            sub = df[df[sm_col] == sm]
            total_mkt = sub[mkt_col].nunique()
            vacant_mkt = sub[sub[vacant_col].isin(['Y', 'YES', 'TRUE', '1'])][mkt_col].nunique()
            actual_mkt = total_mkt - vacant_mkt
            print(f"SH/Zone (ZONE column): {sm:<20} | Total Markets: {total_mkt:<3} | Vacant: {vacant_mkt:<2} | Actual Markets: {actual_mkt}")
            count_sm += 1
            if count_sm >= 5:
                break
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_live_sheet_data_strict()
