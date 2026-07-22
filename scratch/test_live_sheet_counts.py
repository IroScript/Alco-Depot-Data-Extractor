import os
import sys
import pandas as pd

# Add parent directory to path so we can import googleDrive loader
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PARENT_DIR)

from googleDrive.credentials_loader import get_sheet_service_account_credentials, get_spreadsheet_id
import gspread

def get_live_sheet_data():
    try:
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = get_sheet_service_account_credentials(scopes=scopes)
        client = gspread.authorize(creds)
        sheet_id = get_spreadsheet_id('master_field_force_sheet') or '1Q4utivZ5OpgDznqlqElYU-HWNnZYI71YYpcZKcSM3xY'
        sheet = client.open_by_key(sheet_id)
        
        # Load worksheet by gid
        target_gid = '1918615875'
        worksheet = None
        for ws in sheet.worksheets():
            if str(ws.id) == target_gid:
                worksheet = ws
                break
        if not worksheet:
            worksheet = sheet.get_worksheet(0)
            
        print(f"Successfully connected! Loading worksheet: '{worksheet.title}'...")
        all_values = worksheet.get_all_values()
        
        # Cut off secondary data block marker if present
        cutoff_idx = len(all_values)
        for r_idx in range(1, len(all_values)):
            row_str = " ".join([str(c) for c in all_values[r_idx] if c is not None])
            if "FM (SELF APP CODE)" in row_str or "FM (SELF" in row_str:
                cutoff_idx = r_idx
                break
        all_values = all_values[:cutoff_idx]
        
        header = all_values[0]
        data_rows = all_values[1:]
        df = pd.DataFrame(data_rows, columns=header)
        
        print(f"Total rows loaded: {len(df)}")
        print(f"Columns: {list(df.columns)}")
        
        # Let's inspect column names for FM, SM, Zone, Market, Vacant
        fm_col = [c for c in df.columns if 'FM/AM' in str(c) or 'FM' in str(c)][0]
        sm_col = [c for c in df.columns if 'SM' in str(c) or 'SECTOR' in str(c).upper()][0]
        zone_col = [c for c in df.columns if 'ZONE' in str(c).upper()][0]
        mkt_col = [c for c in df.columns if 'MARKET' in str(c).upper()][0]
        vacant_col = [c for c in df.columns if 'VACANT' in str(c).upper()][0]
        
        print(f"Normalizing columns: SM='{sm_col}', FM='{fm_col}', Market='{mkt_col}', Vacant='{vacant_col}'")
        
        df[sm_col] = df[sm_col].astype(str).str.strip().str.upper().fillna('VACANT')
        df[fm_col] = df[fm_col].astype(str).str.strip().str.upper().fillna('VACANT')
        df[mkt_col] = df[mkt_col].astype(str).str.strip().str.upper()
        df[vacant_col] = df[vacant_col].astype(str).str.strip().str.upper().fillna('')
        
        # Remove empty/header rows
        df = df[df[mkt_col] != '']
        
        print("\n=== FIELD MANAGER (FM/AM) COUNTS ===")
        fms = df[fm_col].unique()
        count_fm = 0
        for fm in sorted(fms):
            if not fm or fm == 'VACANT' or 'SELF' in fm:
                continue
            sub = df[df[fm_col] == fm]
            total_mkt = sub[mkt_col].nunique()
            vacant_mkt = sub[sub[vacant_col].isin(['Y', 'YES', 'TRUE', '1'])][mkt_col].nunique()
            actual_mkt = total_mkt - vacant_mkt
            print(f"FM: {fm:<30} | Total Markets: {total_mkt:<3} | Vacant: {vacant_mkt:<2} | Actual Markets: {actual_mkt}")
            count_fm += 1
            if count_fm >= 5:
                break
                
        print("\n=== SECTOR HEAD (SM / ZONE) COUNTS ===")
        sms = df[sm_col].unique()
        count_sm = 0
        for sm in sorted(sms):
            if not sm or sm == 'VACANT':
                continue
            sub = df[df[sm_col] == sm]
            total_mkt = sub[mkt_col].nunique()
            vacant_mkt = sub[sub[vacant_col].isin(['Y', 'YES', 'TRUE', '1'])][mkt_col].nunique()
            actual_mkt = total_mkt - vacant_mkt
            print(f"SH/SM: {sm:<30} | Total Markets: {total_mkt:<3} | Vacant: {vacant_mkt:<2} | Actual Markets: {actual_mkt}")
            count_sm += 1
            if count_sm >= 5:
                break
                
    except Exception as e:
        print(f"Error fetching live Google Sheet: {e}")

if __name__ == "__main__":
    get_live_sheet_data()
