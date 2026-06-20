import pandas as pd
import os

field_xlsx = r"c:\Users\Irak\Desktop\Barishal April Data\FieldEdit\FIELD.xlsx"
if os.path.exists(field_xlsx):
    xl = pd.ExcelFile(field_xlsx)
    print(f"Sheets in FIELD.xlsx: {xl.sheet_names}")
    for sheet in xl.sheet_names:
        df = xl.parse(sheet, nrows=5)
        print(f"\nSheet: {sheet} | Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        print(df.head(5))
else:
    print("FIELD.xlsx does not exist!")
