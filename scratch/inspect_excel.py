import pandas as pd
import glob
import os

base_dir = r"c:\Users\Irak\Desktop\Barishal April Data"
field_dir = os.path.join(base_dir, "FieldEdit")

print("Searching for Excel files in FieldEdit...")
for f in glob.glob(os.path.join(field_dir, "*.xlsx")):
    print(f"\nFile: {os.path.basename(f)}")
    xl = pd.ExcelFile(f)
    print(f"  Sheets: {xl.sheet_names}")
    for sheet in xl.sheet_names[:3]:  # inspect first 3 sheets
        df = xl.parse(sheet, nrows=5)
        print(f"  Sheet: {sheet} | Columns: {list(df.columns)}")
