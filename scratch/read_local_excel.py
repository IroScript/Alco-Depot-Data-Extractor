import pandas as pd
import os

file_path = r'c:\Users\Irak\Desktop\Barishal April Data\FieldEdit\SAMPLE_FIELD_DATA_INPUT.xlsx'
if os.path.exists(file_path):
    df = pd.read_excel(file_path)
    print("Columns:")
    print(df.columns.tolist())
    print("\nShape:", df.shape)
    print("\nFirst 5 rows:")
    print(df.head())
else:
    print("File not found")
