import pandas as pd
import glob
import os

base_dir = r"c:\Users\Irak\Desktop\Barishal April Data"
field_dir = os.path.join(base_dir, "FieldEdit", "Archive")

print("Searching for DSM or SM in Excel files...")
for f in glob.glob(os.path.join(field_dir, "*.xlsx")):
    try:
        xl = pd.ExcelFile(f)
        for sheet in xl.sheet_names:
            df = xl.parse(sheet, nrows=100)
            # Search for any cell containing SM or DSM
            for col in df.columns:
                matches = df[df[col].astype(str).str.contains('DSM|Sales Manager|District Sales', case=False, na=False)]
                if not matches.empty:
                    print(f"Found match in {os.path.basename(f)} | Sheet: {sheet} | Column: {col}")
                    print(matches[[col]].head(5))
                    print("-" * 30)
    except Exception as e:
        print(f"Error reading {f}: {e}")
