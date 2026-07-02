import os
import pandas as pd
import glob

print("--- Searching for D203 in all CSV files and Excel files in workspace ---")

for root, dirs, files in os.walk("."):
    for f in files:
        if f.endswith(".csv"):
            path = os.path.join(root, f)
            try:
                # read in chunks or check text
                with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
                    for line_no, line in enumerate(fp, 1):
                        if "D203" in line or "d203" in line:
                            print(f"[CSV MATCH] {path} (line {line_no}): {line.strip()[:150]}")
                            break
            except Exception as e:
                pass
        elif f.endswith(".xlsx") or f.endswith(".xls"):
            if "FIELD.xlsx" in f or "mpo_code.xlsx" in f:
                continue
            path = os.path.join(root, f)
            try:
                wb = pd.ExcelFile(path)
                for sname in wb.sheet_names:
                    df = pd.read_excel(path, sheet_name=sname, nrows=1000)
                    for col in df.columns:
                        matches = df[df[col].astype(str).str.contains("D203|d203", na=False)]
                        if len(matches) > 0:
                            print(f"[EXCEL MATCH] {path} -> Sheet '{sname}' -> Col '{col}': {len(matches)} rows")
            except Exception as e:
                pass
