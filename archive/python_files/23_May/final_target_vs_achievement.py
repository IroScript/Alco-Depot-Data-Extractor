"""
Final Target vs Achievement Comparison
======================================
1. Load target data (column-wise products)
2. Load achievement data (row-wise products)
3. Match products using fuzzy logic
4. Transpose and merge
5. Create final comparison

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
print("FINAL TARGET VS ACHIEVEMENT COMPARISON")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def normalize_product_name(name):
    """
    Normalize product name for matching.
    Extract core product name by removing:
    - Spaces, hyphens, dots, commas
    - Tab, Cap, Syp, Susp suffixes
    - Numbers and mg
    - Convert to uppercase
    """
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
    
    # Remove extra spaces
    name = ' '.join(name.split())
    
    # Remove all spaces for core matching
    name_core = name.replace(' ', '')
    
    return name_core

def fuzzy_match_products(target_product, achievement_products, threshold=0.75):
    """
    Find best matching product from achievement list.
    """
    target_norm = normalize_product_name(target_product)
    
    if not target_norm:
        return None, 0
    
    best_match = None
    best_score = 0
    
    for ach_product in achievement_products:
        ach_norm = normalize_product_name(ach_product)
        
        # Calculate similarity
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
print(f"  - Columns: {len(df_target.columns)}")

# Get base columns and product columns
base_cols = ['DEPOT', 'ZONE', 'FM/AM, ZONE', 'MARKET', 'MPO CODE', 'DEPOT_MPO_CODE']
product_cols = [col for col in df_target.columns if col not in base_cols + ['Total_Target']]

print(f"  - Base columns: {len(base_cols)}")
print(f"  - Product columns: {len(product_cols)}")
print(f"  - Sample products: {product_cols[:5]}")

# ============================================================================
# STEP 2: LOAD ACHIEVEMENT DATA
# ============================================================================

print("\nSTEP 2: Loading achievement data...")

df_achievement = pd.read_excel(ACHIEVEMENT_FILE, sheet_name='April_Achievement')

print(f"  - Total records: {len(df_achievement)}")
print(f"  - Columns: {df_achievement.columns.tolist()}")
print(f"  - Unique products: {df_achievement['Product_Name'].nunique()}")
print(f"  - Sample products: {df_achievement['Product_Name'].unique()[:5].tolist()}")

# ============================================================================
# STEP 3: MATCH PRODUCTS
# ============================================================================

print("\nSTEP 3: Matching products between target and achievement...")

# Get unique achievement products
achievement_products = df_achievement['Product_Name'].unique()

# Create product mapping
product_mapping = {}
matched_products = []
unmatched_products = []

for target_prod in product_cols:
    best_match, score = fuzzy_match_products(target_prod, achievement_products, threshold=0.75)
    
    if best_match:
        product_mapping[target_prod] = best_match
        matched_products.append((target_prod, best_match, score))
    else:
        unmatched_products.append((target_prod, score))

print(f"\n  Results:")
print(f"  - Matched products: {len(matched_products)}")
print(f"  - Unmatched products: {len(unmatched_products)}")

if matched_products:
    print(f"\n  Sample matches (first 10):")
    for target, ach, score in matched_products[:10]:
        print(f"    '{target}' → '{ach}' (score: {score:.2f})")

if unmatched_products:
    print(f"\n  Unmatched products (first 10):")
    for prod, score in unmatched_products[:10]:
        print(f"    '{prod}' (best score: {score:.2f})")

# ============================================================================
# STEP 4: TRANSPOSE TARGET DATA TO ROW-WISE
# ============================================================================

print("\nSTEP 4: Transposing target data to row-wise format...")

# Melt target data from column-wise to row-wise
df_target_melted = df_target.melt(
    id_vars=base_cols,
    value_vars=product_cols,
    var_name='Target_Product',
    value_name='Target_Qty'
)

# Add matched achievement product name
df_target_melted['Achievement_Product'] = df_target_melted['Target_Product'].map(product_mapping)

# Filter only matched products
df_target_matched = df_target_melted[df_target_melted['Achievement_Product'].notna()].copy()

print(f"  - Total target records (row-wise): {len(df_target_melted)}")
print(f"  - Matched target records: {len(df_target_matched)}")

# ============================================================================
# STEP 5: MERGE TARGET WITH ACHIEVEMENT
# ============================================================================

print("\nSTEP 5: Merging target with achievement...")

# Normalize DEPOT_MPO_CODE for matching (convert to uppercase)
df_target_matched['DEPOT_MPO_CODE_NORM'] = df_target_matched['DEPOT_MPO_CODE'].str.upper()
df_achievement['DepotMPO_Code_NORM'] = df_achievement['DepotMPO_Code'].str.upper()

print(f"  - Sample target codes: {df_target_matched['DEPOT_MPO_CODE_NORM'].head(3).tolist()}")
print(f"  - Sample achievement codes: {df_achievement['DepotMPO_Code_NORM'].head(3).tolist()}")

# Merge on normalized DEPOT_MPO_CODE and Product
df_final = df_target_matched.merge(
    df_achievement[['DepotMPO_Code_NORM', 'Product_Name', 'April_Achievement']],
    left_on=['DEPOT_MPO_CODE_NORM', 'Achievement_Product'],
    right_on=['DepotMPO_Code_NORM', 'Product_Name'],
    how='left'
)

# Fill missing achievements with 0
df_final['April_Achievement'] = df_final['April_Achievement'].fillna(0)

# Calculate variance and achievement %
df_final['Variance'] = df_final['April_Achievement'] - df_final['Target_Qty']
df_final['Achievement_Pct'] = 0.0
mask = df_final['Target_Qty'] > 0
df_final.loc[mask, 'Achievement_Pct'] = (df_final.loc[mask, 'April_Achievement'] / df_final.loc[mask, 'Target_Qty'] * 100).round(2)

print(f"  - Final records: {len(df_final)}")
print(f"  - Records with both target & achievement: {(df_final['April_Achievement'] > 0).sum()}")

# ============================================================================
# STEP 6: CREATE SUMMARY
# ============================================================================

print("\nSTEP 6: Creating summary...")

# Summary by DEPOT_MPO_CODE
summary_depot_mpo = df_final.groupby(['DEPOT', 'ZONE', 'MARKET', 'MPO CODE', 'DEPOT_MPO_CODE']).agg({
    'Target_Qty': 'sum',
    'April_Achievement': 'sum'
}).reset_index()

summary_depot_mpo['Variance'] = summary_depot_mpo['April_Achievement'] - summary_depot_mpo['Target_Qty']
summary_depot_mpo['Achievement_Pct'] = 0.0
mask = summary_depot_mpo['Target_Qty'] > 0
summary_depot_mpo.loc[mask, 'Achievement_Pct'] = (summary_depot_mpo.loc[mask, 'April_Achievement'] / summary_depot_mpo.loc[mask, 'Target_Qty'] * 100).round(2)

print(f"  - Summary records: {len(summary_depot_mpo)}")

# ============================================================================
# STEP 7: SAVE OUTPUT
# ============================================================================

print("\nSTEP 7: Saving output...")

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file = f"Final_Target_vs_Achievement_{timestamp}.xlsx"

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    # Sheet 1: Product-level detail
    output_cols = [
        'DEPOT', 'ZONE', 'MARKET', 'MPO CODE', 'DEPOT_MPO_CODE',
        'Target_Product', 'Achievement_Product',
        'Target_Qty', 'April_Achievement', 'Variance', 'Achievement_Pct'
    ]
    df_final[output_cols].to_excel(writer, sheet_name='Product_Level_Detail', index=False)
    
    # Sheet 2: Summary by DEPOT_MPO_CODE
    summary_depot_mpo.to_excel(writer, sheet_name='Summary_By_DepotMPO', index=False)
    
    # Sheet 3: Product mapping
    mapping_df = pd.DataFrame([
        {'Target_Product': k, 'Achievement_Product': v, 'Match_Score': next((s for t, a, s in matched_products if t == k), 0)}
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

total_target = df_final['Target_Qty'].sum()
total_achievement = df_final['April_Achievement'].sum()
overall_pct = (total_achievement / total_target * 100) if total_target > 0 else 0

print(f"Total Target: {total_target:,.0f}")
print(f"Total Achievement: {total_achievement:,.0f}")
print(f"Overall Achievement: {overall_pct:.2f}%")
print(f"Variance: {total_achievement - total_target:,.0f}")

print(f"\nProduct Matching:")
print(f"  - Matched: {len(matched_products)}/{len(product_cols)} ({len(matched_products)/len(product_cols)*100:.1f}%)")
print(f"  - Unmatched: {len(unmatched_products)}")

print(f"\nData Records:")
print(f"  - Product-level records: {len(df_final)}")
print(f"  - DEPOT_MPO combinations: {len(summary_depot_mpo)}")
print(f"  - Records with achievement: {(df_final['April_Achievement'] > 0).sum()}")

print("\n" + "=" * 80)
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
