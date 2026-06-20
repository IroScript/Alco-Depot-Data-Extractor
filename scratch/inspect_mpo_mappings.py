import pandas as pd
import os

base_dir = r"c:\Users\Irak\Desktop\Barishal April Data"

# Let's inspect FIELD.xlsx if it exists
field_xlsx = os.path.join(base_dir, "FieldEdit", "FIELD.xlsx")
if os.path.exists(field_xlsx):
    print("\nFIELD.xlsx:")
    xl = pd.ExcelFile(field_xlsx)
    print(f"  Sheets: {xl.sheet_names}")
    df = xl.parse(xl.sheet_names[0])
    print(f"  Shape: {df.shape}")
    print(f"  Columns: {list(df.columns)}")
    print(df.head(5))

# Let's inspect mpo_code.xlsx in archive/recent/
mpo_code_xlsx = os.path.join(base_dir, "archive", "recent", "mpo_code.xlsx")
if os.path.exists(mpo_code_xlsx):
    print("\nmpo_code.xlsx:")
    xl = pd.ExcelFile(mpo_code_xlsx)
    print(f"  Sheets: {xl.sheet_names}")
    df = xl.parse(xl.sheet_names[0])
    print(f"  Shape: {df.shape}")
    print(f"  Columns: {list(df.columns)}")
    print(df.head(5))
