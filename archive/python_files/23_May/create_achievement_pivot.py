"""
Create Achievement Pivot Table
==============================
1. Load Product_Level_Net_Sales CSV
2. Add Depot_MPO_Code_Product_Code concatenation
3. Add Depot_MPO_Code concatenation
4. Create pivot table by Month
5. Get April achievement by Depot_MPO_Code and Product

Author: Auto-generated
Date: 2026-05-23
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

ACHIEVEMENT_CSV = r"C:\Users\Irak\Desktop\Barishal April Data\Product_Level_Net_Sales_20260522_232817.csv"

print("=" * 80)
print("CREATE ACHIEVEMENT PIVOT TABLE")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# ============================================================================
# STEP 1: LOAD CSV FILE
# ============================================================================

print("STEP 1: Loading achievement CSV...")

df = pd.read_csv(ACHIEVEMENT_CSV)

print(f"  - Total records: {len(df)}")
print(f"  - Columns: {df.columns.tolist()}")

# ============================================================================
# STEP 2: ADD CONCATENATED COLUMNS
# ============================================================================

print("\nSTEP 2: Adding concatenated columns...")

# Insert Depot_MPO_Code_Product_Code after column C (index 3)
# Column order: A=CONCATENATED_KEY, B=Depot, C=MPO_Code, D=NEW, E=NEW, F=Customer_ID...

# Create Depot_MPO_Code_Product_Code
df['DepotMPO_CodeProduct_Code'] = df['Depot'] + '_' + df['MPO_Code'] + '_' + df['Product_Code']

# Create Depot_MPO_Code
df['DepotMPO_Code'] = df['Depot'] + '_' + df['MPO_Code']

print(f"  - Added DepotMPO_CodeProduct_Code")
print(f"  - Added DepotMPO_Code")
print(f"  - Sample DepotMPO_CodeProduct_Code: {df['DepotMPO_CodeProduct_Code'].head(3).tolist()}")
print(f"  - Sample DepotMPO_Code: {df['DepotMPO_Code'].head(3).tolist()}")

# Reorder columns to insert after column C
# Original: CONCATENATED_KEY, Depot, MPO_Code, Customer_ID, Customer_Name, Month, Product_Code, Product_Name, ...
# New: CONCATENATED_KEY, Depot, MPO_Code, DepotMPO_CodeProduct_Code, DepotMPO_Code, Customer_ID, ...

cols = df.columns.tolist()
# Find the position of MPO_Code
mpo_code_idx = cols.index('MPO_Code')

# Reorder: everything up to MPO_Code, then new columns, then rest
new_order = (
    cols[:mpo_code_idx + 1] +  # Up to and including MPO_Code
    ['DepotMPO_CodeProduct_Code', 'DepotMPO_Code'] +  # New columns
    [col for col in cols[mpo_code_idx + 1:] if col not in ['DepotMPO_CodeProduct_Code', 'DepotMPO_Code']]  # Rest
)

df = df[new_order]

print(f"  - Reordered columns")
print(f"  - New column order (first 10): {df.columns.tolist()[:10]}")

# ============================================================================
# STEP 3: CREATE PIVOT TABLE
# ============================================================================

print("\nSTEP 3: Creating pivot table...")

# Pivot table with Month as columns
pivot = pd.pivot_table(
    df,
    values='ACTUAL_SALE_QTY',
    index=['DepotMPO_CodeProduct_Code', 'Depot', 'MPO_Code', 'DepotMPO_Code', 'Product_Code', 'Product_Name'],
    columns='Month',
    aggfunc='sum',
    fill_value=0,
    margins=True,
    margins_name='Grand Total'
)

print(f"  - Pivot table shape: {pivot.shape}")
print(f"  - Months in columns: {[col for col in pivot.columns if col != 'Grand Total']}")

# Reset index to make it a regular dataframe
pivot_df = pivot.reset_index()

print(f"  - Pivot dataframe shape: {pivot_df.shape}")
print(f"  - Columns: {pivot_df.columns.tolist()}")

# ============================================================================
# STEP 4: EXTRACT APRIL DATA
# ============================================================================

print("\nSTEP 4: Extracting April achievement...")

# Check if 2026-04 column exists
if '2026-04' in pivot_df.columns:
    april_col = '2026-04'
elif 'April' in pivot_df.columns:
    april_col = 'April'
else:
    # Find column with '04' in it
    april_col = [col for col in pivot_df.columns if '04' in str(col)]
    if april_col:
        april_col = april_col[0]
    else:
        print("  ⚠ Warning: April column not found!")
        april_col = None

if april_col:
    print(f"  - April column: {april_col}")
    
    # Create April summary
    april_summary = pivot_df[['DepotMPO_CodeProduct_Code', 'Depot', 'MPO_Code', 'DepotMPO_Code', 
                               'Product_Code', 'Product_Name', april_col]].copy()
    april_summary.rename(columns={april_col: 'April_Achievement'}, inplace=True)
    
    # Remove Grand Total row
    april_summary = april_summary[april_summary['DepotMPO_CodeProduct_Code'] != 'Grand Total']
    
    print(f"  - April records: {len(april_summary)}")
    print(f"  - Total April achievement: {april_summary['April_Achievement'].sum():,.0f}")
    
    # Show sample
    print(f"\n  Sample April data:")
    print(april_summary.head(10).to_string())

# ============================================================================
# STEP 5: SAVE OUTPUT
# ============================================================================

print("\nSTEP 5: Saving output...")

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file = f"Achievement_Pivot_{timestamp}.xlsx"

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    # Sheet 1: Full pivot table with all months
    pivot_df.to_excel(writer, sheet_name='Pivot_All_Months', index=False)
    
    # Sheet 2: April only
    if april_col:
        april_summary.to_excel(writer, sheet_name='April_Achievement', index=False)
    
    # Sheet 3: Original data with new columns
    df.to_excel(writer, sheet_name='Data_With_Concatenations', index=False)

print(f"\n✓ Output saved: {output_file}")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total records: {len(df)}")
print(f"Pivot table rows: {len(pivot_df)}")

if april_col:
    print(f"\nApril Achievement:")
    print(f"  - Total records: {len(april_summary)}")
    print(f"  - Total quantity: {april_summary['April_Achievement'].sum():,.0f}")
    print(f"  - Unique Depot_MPO combinations: {april_summary['DepotMPO_Code'].nunique()}")
    print(f"  - Unique products: {april_summary['Product_Code'].nunique()}")

print("\n" + "=" * 80)
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
