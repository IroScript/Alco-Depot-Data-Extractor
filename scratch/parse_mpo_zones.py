import pandas as pd
import os

file_path = r'c:\Users\Irak\Desktop\Barishal April Data\FieldEdit\SAMPLE_FIELD_DATA_INPUT.xlsx'
if os.path.exists(file_path):
    df = pd.read_excel(file_path, header=None)
    
    # We want to scan the rows. The first row contains sheet title or headers.
    # Let's print rows that contain "Zone :" or "FM (" or similar patterns
    zones = []
    fms = []
    mpos = []
    
    current_zone = None
    current_fm = None
    
    for idx, row in df.iterrows():
        row_str_list = [str(val).strip() for val in row.values if pd.notna(val)]
        row_str = " ".join(row_str_list)
        
        # Check if it defines a Zone
        if "Zone :" in row_str or "Zone:" in row_str:
            current_zone = row_str
            zones.append((idx, row_str))
        
        # Check if it defines an FM
        if "FM (" in row_str or "FM:" in row_str or "FM Name" in row_str:
            current_fm = row_str
            fms.append((idx, current_zone, row_str))
            
        # Check if it looks like an MPO row (typically has a serial number and name/code)
        # Let's see if first cell is a number
        first_cell = row.iloc[0]
        try:
            val = float(first_cell)
            if not pd.isna(val) and val.is_integer():
                mpos.append((idx, current_zone, current_fm, row_str_list))
        except:
            pass
            
    print(f"Total Zones found: {len(zones)}")
    for z in zones[:5]:
        print(f"  Line {z[0]}: {z[1]}")
        
    print(f"\nTotal FMs found: {len(fms)}")
    for f in fms[:5]:
        print(f"  Line {f[0]} | Zone: {f[1]} | FM: {f[2]}")
        
    print(f"\nTotal MPO rows found: {len(mpos)}")
    for m in mpos[:10]:
        print(f"  Line {m[0]} | Zone: {m[1]} | FM: {m[2]} | Data: {m[3]}")
else:
    print("Excel file not found")
