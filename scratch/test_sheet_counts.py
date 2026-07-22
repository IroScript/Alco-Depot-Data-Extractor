import pandas as pd
import os

def check_field_xlsx():
    # Candidates for local Excel fallback representing the google sheet
    fpath = os.path.abspath("FieldEdit/Archive/FIELD.xlsx")
    if not os.path.exists(fpath):
        print(f"File not found: {fpath}")
        return

    print(f"Loading {fpath}...")
    df = pd.read_excel(fpath, header=1) # The header is in row 2 (index 1) in the python script loading
    print(f"Columns: {list(df.columns)}")
    
    # Clean rows similar to python loading
    # Clean SM, ZONE, FM/AM, MARKET, VACANT
    df_clean = df.copy()
    
    # We want FM column name. In script it checks for 'FM/AM'
    # Let's inspect column names for FM and SM
    fm_col = [c for c in df_clean.columns if 'FM' in str(c)][0]
    sm_col = [c for c in df_clean.columns if 'SM' in str(c) or 'SECTOR' in str(c).upper()][0]
    zone_col = [c for c in df_clean.columns if 'ZONE' in str(c).upper()][0]
    mkt_col = [c for c in df_clean.columns if 'MARKET' in str(c).upper()][0]
    vacant_col = [c for c in df_clean.columns if 'VACANT' in str(c).upper()][0]
    
    print(f"Detected columns -> SM: '{sm_col}', FM: '{fm_col}', Zone: '{zone_col}', Market: '{mkt_col}', Vacant: '{vacant_col}'")
    
    # Drop rows where essential columns are empty
    df_clean = df_clean.dropna(subset=[mkt_col])
    
    df_clean[sm_col] = df_clean[sm_col].astype(str).str.strip().str.upper().fillna('VACANT')
    df_clean[fm_col] = df_clean[fm_col].astype(str).str.strip().str.upper().fillna('VACANT')
    df_clean[zone_col] = df_clean[zone_col].astype(str).str.strip().str.upper()
    df_clean[mkt_col] = df_clean[mkt_col].astype(str).str.strip().str.upper()
    df_clean[vacant_col] = df_clean[vacant_col].astype(str).str.strip().str.upper().fillna('')
    
    # Exclude cutoff lines (e.g. FM (SELF APP CODE) / FM (SELF)
    df_clean = df_clean[~df_clean[fm_col].str.contains("SELF", na=False)]
    
    print("\n=== FIELD MANAGER (FM/AM) COUNTS FROM SHEET ===")
    fms = df_clean[fm_col].unique()
    count_fm = 0
    for fm in sorted(fms):
        if not fm or fm == 'VACANT' or 'SELF' in fm:
            continue
        sub = df_clean[df_clean[fm_col] == fm]
        total_mkt = sub[mkt_col].nunique()
        vacant_mkt = sub[sub[vacant_col].isin(['Y', 'YES', 'TRUE', '1'])][mkt_col].nunique()
        actual_mkt = total_mkt - vacant_mkt
        print(f"FM: {fm:<30} | Total Markets: {total_mkt:<3} | Vacant Markets: {vacant_mkt:<2} | Actual Markets: {actual_mkt}")
        count_fm += 1
        if count_fm >= 5:
            break
            
    print("\n=== SECTOR HEAD (SM / ZONE) COUNTS FROM SHEET ===")
    sms = df_clean[sm_col].unique()
    count_sm = 0
    for sm in sorted(sms):
        if not sm or sm == 'VACANT':
            continue
        sub = df_clean[df_clean[sm_col] == sm]
        total_mkt = sub[mkt_col].nunique()
        vacant_mkt = sub[sub[vacant_col].isin(['Y', 'YES', 'TRUE', '1'])][mkt_col].nunique()
        actual_mkt = total_mkt - vacant_mkt
        print(f"SH/SM: {sm:<30} | Total Markets: {total_mkt:<3} | Vacant Markets: {vacant_mkt:<2} | Actual Markets: {actual_mkt}")
        count_sm += 1
        if count_sm >= 5:
            break

if __name__ == "__main__":
    check_field_xlsx()
