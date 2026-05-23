import pandas as pd

df_raw = pd.read_excel(r"C:\Users\Irak\Desktop\Barishal April Data\Unit Target of April-2026 (2).xlsx", header=None)
prod_row = df_raw.iloc[2, 8:43]

print("Product names from row 3:")
for i, p in enumerate(prod_row):
    print(f"{i+8}: {p}")

# Check for duplicates
prod_list = [str(p) for p in prod_row if pd.notna(p)]
print(f"\nTotal products: {len(prod_list)}")
print(f"Unique products: {len(set(prod_list))}")
print(f"Duplicates: {len(prod_list) - len(set(prod_list))}")

# Show duplicates
from collections import Counter
counts = Counter(prod_list)
duplicates = {k: v for k, v in counts.items() if v > 1}
if duplicates:
    print("\nDuplicate products:")
    for prod, count in duplicates.items():
        print(f"  {prod}: appears {count} times")
