"""
Insert Achievement Columns Next to Target Columns
=================================================
Keep MPO target file format (column-wise)
Insert achievement column after each target column
Format: Target | Achievement | Target | Achievement | ...

Author: Auto-generated
Date: 2026-05-23
"""

import pandas as pd
import numpy as np
from datetime import datetime
from difflib import SequenceMatcher
import re
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

TARGET_FILE = r"C:\Users\Irak\Desktop\Barishal April Data\MPO_Field_With_Targets_20260523_102519.xlsx"
ACHIEVEMENT_FILE = r"C:\Users\Irak\Desktop\Barishal April Data\Achievement_Pivot_20260523_104633.xlsx"

print("=" * 80)
print("INSERT ACHIEVEMENT COLUMNS NEXT TO TARGET COLUMNS")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def normalize_product_name(name):
    """Normalize product name for matching"""
    if pd.isna(name):
        return ""
    
    name = str(name).upper().strip()
    
    # Remove common suffixes
    name = re.sub(r'\s*(TAB|TABLET|CAP|CAPSULE|SYP|SYRUP|SUSP|SUSPENSION)\.?\s*', '', name, flags=re.IGNORECASE)
    
    # Remove (New), (70), etc.
    name = re.sub(r'\([^)]*\)', '', name)
    
    # Remove numbers with mg
    name = re.sub(r'\d+\s*MG', '', name, flags=re.IGNORECASE)
    
    # Remove punctuation
    name = name.replace('-', '').replace('.', '').replace(',', '').replace('+', '')
    
    # Remove extra spaces and convert to core
    name = ' '.join(name.split())
    name_core = name.replace(' ', '')
    
    return name_core

def fuzzy_match_products(target_product, achievement_products, threshold=0.75):
    """Find best matching product from achievement list"""
    target_norm = normalize_product_name(target_product)
    
    if not target_norm:
        return None, 0
    
    best_match = None
    best_score = 0
    
    for ach_product in achievement_products:
        ach_norm = normalize_product_name(ach_product)
        score = SequenceMatcher(None, target_norm, ach_norm).ratio()
        
        if score > best_score:
            best_score = score
            best_match = ach_product
    
    if best_score >= threshold:
        return best_match, best_score
    else:
        return None, best_score

# ============================================================================
# STEP 1: LOAD TARGET DATA
# ============================================================================

print("STEP 1: Loading target data...")

df_target = pd.read_excel(TARGET_FILE, sheet_name='MPO_Field_Targets')

print(f"  - Total records: {len(df_target)}")
print(f"  - Total columns: {len(df_target.columns)}")

# Identify base columns and product columns
base_cols = ['DEPOT', 'ZONE', 'FM/AM, ZONE', 'MARKET', 'MPO CODE', 'DEPOT_MPO_CODE']
product_cols = [col for col in df_target.columns if col not in base_cols + ['Total_Target']]

print(f"  - Base columns: {len(base_cols)}")
print(f"  - Product columns: {len(product_cols)}")

# ============================================================================
# STEP 2: LOAD ACHIEVEMENT DATA
# ============================================================================

print("\nSTEP 2: Loading achievement data...")

df_achievement = pd.read_excel(ACHIEVEMENT_FILE, sheet_name='April_Achievement')

print(f"  - Total records: {len(df_achievement)}")
print(f"  - Unique products: {df_achievement['Product_Name'].nunique()}")

# Normalize DEPOT_MPO_CODE for matching
df_achievement['DepotMPO_Code_NORM'] = df_achievement['DepotMPO_Code'].str.upper()

# ============================================================================
# STEP 3: MATCH PRODUCTS
# ============================================================================

print("\nSTEP 3: Matching products...")

achievement_products = df_achievement['Product_Name'].unique()
product_mapping = {}
matched_count = 0
unmatched_count = 0

for target_prod in product_cols:
    best_match, score = fuzzy_match_products(target_prod, achievement_products, threshold=0.75)
    
    if best_match:
        product_mapping[target_prod] = best_match
        matched_count += 1
        if matched_count <= 10:
            print(f"  ✓ '{target_prod}' → '{best_match}' (score: {score:.2f})")
    else:
        unmatched_count += 1

print(f"\n  Matched: {matched_count}/{len(product_cols)}")
print(f"  Unmatched: {unmatched_count}")

# ============================================================================
# STEP 4: CREATE ACHIEVEMENT LOOKUP
# ============================================================================

print("\nSTEP 4: Creating achievement lookup...")

# Create a pivot of achievement data for fast lookup
# Key: (DEPOT_MPO_CODE_NORM, Product_Name) -> Achievement
achievement_lookup = {}
for idx, row in df_achievement.iterrows():
    key = (row['DepotMPO_Code_NORM'], row['Product_Name'])
    achievement_lookup[key] = row['April_Achievement']

print(f"  - Achievement lookup entries: {len(achievement_lookup)}")

# ============================================================================
# STEP 5: INSERT ACHIEVEMENT COLUMNS
# ============================================================================

print("\nSTEP 5: Inserting achievement columns next to target columns...")

# Create new dataframe with base columns
df_final = df_target[base_cols].copy()

# Normalize DEPOT_MPO_CODE in target
df_final['DEPOT_MPO_CODE_NORM'] = df_final['DEPOT_MPO_CODE'].str.upper()

# For each product column, add target and achievement columns
for target_prod in product_cols:
    # Add target column
    df_final[f"{target_prod}"] = df_target[target_prod]
    
    # Add achievement column
    ach_col_name = f"{target_prod}_Ach"
    
    if target_prod in product_mapping:
        # Get matched achievement product name
        ach_product = product_mapping[target_prod]
        
        # Lookup achievement for each row
        achievements = []
        for idx, row in df_final.iterrows():
            key = (row['DEPOT_MPO_CODE_NORM'], ach_product)
            ach_value = achievement_lookup.get(key, 0)
            achievements.append(ach_value)
        
        df_final[ach_col_name] = achievements
    else:
        # No match, fill with 0
        df_final[ach_col_name] = 0

# Remove the normalized column
df_final = df_final.drop('DEPOT_MPO_CODE_NORM', axis=1)

print(f"  - Final columns: {len(df_final.columns)}")
print(f"  - Expected: {len(base_cols)} base + {len(product_cols) * 2} product pairs = {len(base_cols) + len(product_cols) * 2}")

# ============================================================================
# STEP 6: CALCULATE TOTALS
# ============================================================================

print("\nSTEP 6: Calculating totals...")

# Calculate total target and total achievement
target_cols_only = [col for col in df_final.columns if not col.endswith('_Ach') and col not in base_cols]
ach_cols_only = [col for col in df_final.columns if col.endswith('_Ach')]

df_final['Total_Target'] = df_final[target_cols_only].sum(axis=1)
df_final['Total_Achievement'] = df_final[ach_cols_only].sum(axis=1)
df_final['Total_Variance'] = df_final['Total_Achievement'] - df_final['Total_Target']
df_final['Total_Achievement_Pct'] = 0.0

mask = df_final['Total_Target'] > 0
df_final.loc[mask, 'Total_Achievement_Pct'] = (df_final.loc[mask, 'Total_Achievement'] / df_final.loc[mask, 'Total_Target'] * 100).round(2)

print(f"  - Total target: {df_final['Total_Target'].sum():,.0f}")
print(f"  - Total achievement: {df_final['Total_Achievement'].sum():,.0f}")
print(f"  - Overall achievement: {(df_final['Total_Achievement'].sum() / df_final['Total_Target'].sum() * 100):.2f}%")

# ============================================================================
# STEP 7: SAVE OUTPUT
# ============================================================================

print("\nSTEP 7: Saving output...")

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file = f"MPO_Target_vs_Achievement_{timestamp}.xlsx"

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    # Main sheet with all data
    df_final.to_excel(writer, sheet_name='Target_vs_Achievement', index=False)
    
    # Product mapping sheet
    mapping_df = pd.DataFrame([
        {'Target_Product': k, 'Achievement_Product': v}
        for k, v in product_mapping.items()
    ])
    mapping_df.to_excel(writer, sheet_name='Product_Mapping', index=False)

print(f"\n✓ Output saved: {output_file}")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total MPO records: {len(df_final)}")
print(f"Product columns: {len(product_cols)}")
print(f"Matched products: {matched_count}")
print(f"Unmatched products: {unmatched_count}")
print(f"\nTotal Target: {df_final['Total_Target'].sum():,.0f}")
print(f"Total Achievement: {df_final['Total_Achievement'].sum():,.0f}")
print(f"Overall Achievement: {(df_final['Total_Achievement'].sum() / df_final['Total_Target'].sum() * 100):.2f}%")
print(f"Variance: {df_final['Total_Variance'].sum():,.0f}")

print("\n" + "=" * 80)
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
