"""
Extract Target Data with Correct Product Names
==============================================
Step 1: Read product names from row 3 (I3:AQ3)
Step 2: Assign them as column headers
Step 3: Extract target data with proper product columns

Author: Auto-generated
Date: 2026-05-23
"""

import pandas as pd
import numpy as np
from datetime import datetime

TARGET_FILE = r"C:\Users\Irak\Desktop\Barishal April Data\Unit Target of April-2026 (2).xlsx"

print("=" * 80)
print("EXTRACTING TARGET DATA WITH PRODUCT NAMES")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# ============================================================================
# STEP 1: READ PRODUCT NAMES FROM ROW 3
# ============================================================================

print("STEP 1: Reading product names from row 3...")

# Read the entire file without headers
df_raw = pd.read_excel(TARGET_FILE, header=None)

# Row 3 (index 2) contains product names starting from column I (index 8)
product_names_row = df_raw.iloc[2]

print(f"Total columns in file: {len(product_names_row)}")
print(f"\nProduct names from row 3 (columns I to AQ):")

# Extract product names from column 8 onwards
product_names = []
for i in range(8, len(product_names_row)):
    prod_name = product_names_row.iloc[i]
    if pd.notna(prod_name):
        product_names.append(str(prod_name).strip())
        if i < 18:  # Show first 10 products
            print(f"  Column {i} (Excel col {chr(65 + i)}): {prod_name}")
    else:
        product_names.append(f"Product_{i}")

print(f"\nTotal product columns found: {len(product_names)}")

# ============================================================================
# STEP 2: READ DATA WITH PROPER HEADERS
# ============================================================================

print("\nSTEP 2: Reading data with proper headers...")

# Read data starting from row 2 (index 1) as header
df = pd.read_excel(TARGET_FILE, header=1)

print(f"Data shape: {df.shape}")
print(f"Original column names (first 15): {df.columns.tolist()[:15]}")

# ============================================================================
# STEP 3: ASSIGN PRODUCT NAMES TO COLUMNS
# ============================================================================

print("\nSTEP 3: Assigning product names to columns...")

# Assign key column names
df.columns.values[0] = 'Sl_No'
df.columns.values[1] = 'Name'
df.columns.values[2] = 'Designation'
df.columns.values[3] = 'Market'

# Assign product names starting from column 8
# Handle duplicates by adding suffix
product_name_counts = {}
for i, prod_name in enumerate(product_names):
    col_idx = 8 + i
    if col_idx < len(df.columns):
        # Check if this product name already exists
        if prod_name in product_name_counts:
            product_name_counts[prod_name] += 1
            unique_name = f"{prod_name}_Group{product_name_counts[prod_name]}"
        else:
            product_name_counts[prod_name] = 1
            unique_name = prod_name
        
        df.columns.values[col_idx] = unique_name

print(f"Updated column names (columns 8-18):")
for i in range(8, min(18, len(df.columns))):
    print(f"  Column {i}: {df.columns[i]}")

# ============================================================================
# STEP 4: FILTER VALID DESIGNATIONS
# ============================================================================

print("\nSTEP 4: Filtering valid designations...")

VALID_DESIGNATIONS = [
    'AFM(MMO)', 'AM(AFM)', 'AM(Self)', 'DAFM(MPO)', 'FM(Self)',
    'MMO', 'MPO', 'MR', 'Self', 'SMMO', 'SMPO',
    'Sr.DA', 'Sr.FM(Self)', 'Sr.RSM(Self)'
]

# Filter AFTER renaming columns
# Also skip the first row which contains product names
df_filtered = df[df['Designation'].isin(VALID_DESIGNATIONS)].reset_index(drop=True)
df_filtered = df_filtered[df_filtered['Market'].notna()].reset_index(drop=True)

# Remove any rows where Market contains product names or other header text
df_filtered = df_filtered[~df_filtered['Market'].astype(str).str.contains('Tab|Cap|Syp|Susp', case=False, na=False)]
df_filtered = df_filtered[~df_filtered['Market'].astype(str).str.contains('Present Market', case=False, na=False)]
df_filtered = df_filtered.reset_index(drop=True)

print(f"Total rows with valid designations: {len(df_filtered)}")
print(f"Unique markets: {df_filtered['Market'].nunique()}")

# ============================================================================
# STEP 5: EXTRACT ZONES
# ============================================================================

print("\nSTEP 5: Extracting zones...")

zones_dict = {}
current_zone = None

for idx, row in df_raw.iterrows():
    # Check column B (index 1) for zone
    if pd.notna(row.iloc[1]) and 'Zone' in str(row.iloc[1]):
        current_zone = str(row.iloc[1]).replace('Zone :', '').replace('Zone', '').strip()
    
    # Check if this row has a market in column D (index 3)
    if pd.notna(row.iloc[3]):
        market = str(row.iloc[3]).strip()
        if market and market != 'Present Market':
            zones_dict[market] = current_zone

# Assign zones
df_filtered['Zone'] = df_filtered['Market'].map(zones_dict)

print(f"Unique zones found: {df_filtered['Zone'].nunique()}")
print(f"Sample zones: {[z for z in df_filtered['Zone'].unique() if z is not None][:5]}")

# ============================================================================
# STEP 6: PROCESS PRODUCT TARGETS
# ============================================================================

print("\nSTEP 6: Processing product targets...")

# Get product columns (from column 8 onwards) - only those that exist
product_cols = []
for i in range(8, len(df_filtered.columns)):
    col_name = df_filtered.columns[i]
    # Check if it's a valid product column (not empty, not unnamed)
    if col_name and not str(col_name).startswith('Unnamed') and not str(col_name).startswith('Product_'):
        product_cols.append(col_name)

print(f"Valid product columns found: {len(product_cols)}")

# Convert to numeric and round
for col in product_cols:
    if col in df_filtered.columns:
        try:
            # Use .loc to avoid SettingWithCopyWarning
            df_filtered.loc[:, col] = pd.to_numeric(df_filtered[col], errors='coerce').fillna(0).round(0).astype(int)
        except Exception as e:
            print(f"  Warning: Could not process column '{col}': {e}")
            df_filtered.loc[:, col] = 0

# Calculate total target
if product_cols:
    df_filtered['Total_Target'] = df_filtered[product_cols].sum(axis=1)
else:
    df_filtered['Total_Target'] = 0

print(f"Product columns: {len(product_cols)}")
print(f"Total target quantity: {df_filtered['Total_Target'].sum():,.0f}")

# Show sample data
print(f"\nSample data (first 5 rows):")
sample_cols = ['Zone', 'Market', 'Designation'] + product_cols[:3] + ['Total_Target']
print(df_filtered[sample_cols].head())

# ============================================================================
# STEP 7: SAVE OUTPUT
# ============================================================================

print("\nSTEP 7: Saving output...")

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file = f"Target_Data_With_Products_{timestamp}.xlsx"

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    # Sheet 1: Summary
    summary_cols = ['Zone', 'Market', 'Designation', 'Total_Target']
    df_filtered[summary_cols].to_excel(writer, sheet_name='Summary', index=False)
    
    # Sheet 2: Full data with all products
    df_filtered.to_excel(writer, sheet_name='Full_Data', index=False)
    
    # Sheet 3: Product list
    product_df = pd.DataFrame({
        'Column_Index': range(8, 8 + len(product_cols)),
        'Product_Name': product_cols
    })
    product_df.to_excel(writer, sheet_name='Product_List', index=False)

print(f"\n✓ Output saved: {output_file}")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total markets: {len(df_filtered)}")
print(f"Unique zones: {df_filtered['Zone'].nunique()}")
print(f"Product columns: {len(product_cols)}")
print(f"Total target: {df_filtered['Total_Target'].sum():,.0f}")

print("\nProduct names extracted:")
for i, prod in enumerate(product_cols[:10]):
    print(f"  {i+1}. {prod}")
if len(product_cols) > 10:
    print(f"  ... and {len(product_cols) - 10} more products")

print("\n" + "=" * 80)
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
