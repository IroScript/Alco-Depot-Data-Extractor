"""
Fix Achievement Pivot - Add Uppercase Lookup Column
===================================================
The target file has uppercase DEPOT names (CUMILLA)
The achievement file has mixed case (Cumilla)
This script adds an uppercase lookup column to the achievement file

Author: Auto-generated
Date: 2026-05-23
"""

import pandas as pd
from openpyxl import load_workbook
from datetime import datetime

print("=" * 80)
print("FIX ACHIEVEMENT PIVOT - ADD UPPERCASE LOOKUP COLUMN")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Load the achievement file
df = pd.read_excel('Achievement_Pivot_20260523_104633.xlsx', sheet_name='April_Achievement')

print(f"Original shape: {df.shape}")
print(f"Original columns: {list(df.columns)}")

# Add uppercase lookup column at the beginning (column A)
df.insert(0, 'LOOKUP_KEY_UPPER', df['DepotMPO_CodeProduct_Code'].str.upper())

print(f"\nNew shape: {df.shape}")
print(f"New columns: {list(df.columns)}")

# Show sample
print(f"\nSample data:")
print(df[['LOOKUP_KEY_UPPER', 'DepotMPO_CodeProduct_Code', 'April_Achievement']].head())

# Save to new file
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file = f"Achievement_Pivot_Fixed_{timestamp}.xlsx"

df.to_excel(output_file, sheet_name='April_Achievement', index=False)

print(f"\n✓ Output saved: {output_file}")

# Verify
print(f"\nVerification:")
df_check = pd.read_excel(output_file, sheet_name='April_Achievement')
print(f"  - Rows: {len(df_check)}")
print(f"  - Columns: {len(df_check.columns)}")
print(f"  - First column: {df_check.columns[0]}")

# Test lookup
test_key = "CUMILLA_AS01_ACO1"
matching = df_check[df_check['LOOKUP_KEY_UPPER'] == test_key]
if len(matching) > 0:
    print(f"\n✓ Test lookup successful:")
    print(f"  Key: {test_key}")
    print(f"  Achievement: {matching.iloc[0]['April_Achievement']}")
else:
    print(f"\n✗ Test lookup failed for: {test_key}")

print("\n" + "=" * 80)
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
