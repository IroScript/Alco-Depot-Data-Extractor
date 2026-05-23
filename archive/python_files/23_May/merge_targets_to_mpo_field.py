"""
Merge Target Data into MPO_CODE_AND_FIELD File
==============================================
1. Load MPO_CODE_AND_FIELD.xlsx as base
2. Add DEPOT_MPO_CODE concatenation in column F
3. Pull all product targets from Target_Data_With_Products file
4. Match by market name (fuzzy matching)
5. Add product columns starting from column G

Author: Auto-generated
Date: 2026-05-23
"""

import pandas as pd
import numpy as np
from datetime import datetime
from difflib import SequenceMatcher
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

MPO_FIELD_FILE = r"C:\Users\Irak\Desktop\Barishal April Data\MPO_CODE_AND_FIELD.xlsx"
TARGET_FILE = r"C:\Users\Irak\Desktop\Barishal April Data\Target_Data_With_Products_20260523_100853.xlsx"

print("=" * 80)
print("MERGING TARGET DATA INTO MPO_CODE_AND_FIELD")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# ============================================================================
# STEP 1: LOAD MPO_CODE_AND_FIELD FILE
# ============================================================================

print("STEP 1: Loading MPO_CODE_AND_FIELD file...")

df_mpo = pd.read_excel(MPO_FIELD_FILE)

print(f"  - Total records: {len(df_mpo)}")
print(f"  - Columns: {df_mpo.columns.tolist()}")
print(f"  - Unique markets: {df_mpo['MARKET'].nunique()}")

# ============================================================================
# STEP 2: ADD DEPOT_MPO_CODE CONCATENATION
# ============================================================================

print("\nSTEP 2: Adding DEPOT_MPO_CODE concatenation...")

# Convert to string first
df_mpo['DEPOT'] = df_mpo['DEPOT'].astype(str)
df_mpo['MPO CODE'] = df_mpo['MPO CODE'].astype(str)

# Check if column F already has data
if len(df_mpo.columns) > 5:
    col_f_name = df_mpo.columns[5]
    print(f"  - Column F name: {col_f_name}")
    
    # Check if it's already concatenated
    if df_mpo.iloc[0, 5] and '_' in str(df_mpo.iloc[0, 5]):
        print(f"  - Column F already contains concatenated data")
        df_mpo['DEPOT_MPO_CODE'] = df_mpo.iloc[:, 5]
    else:
        # Create concatenation
        df_mpo['DEPOT_MPO_CODE'] = df_mpo['DEPOT'] + '_' + df_mpo['MPO CODE']
        print(f"  - Created DEPOT_MPO_CODE concatenation")
else:
    # Add new column
    df_mpo['DEPOT_MPO_CODE'] = df_mpo['DEPOT'] + '_' + df_mpo['MPO CODE']
    print(f"  - Added new DEPOT_MPO_CODE column")

print(f"  - Sample DEPOT_MPO_CODE: {df_mpo['DEPOT_MPO_CODE'].head(3).tolist()}")

# ============================================================================
# STEP 3: LOAD TARGET DATA
# ============================================================================

print("\nSTEP 3: Loading target data...")

df_target = pd.read_excel(TARGET_FILE, sheet_name='Full_Data')

print(f"  - Total target records: {len(df_target)}")
print(f"  - Columns: {len(df_target.columns)}")
print(f"  - Unique markets: {df_target['Market'].nunique()}")

# Get product columns (from column 8 onwards, excluding non-product columns)
product_cols = []
for col in df_target.columns[8:]:
    if col not in ['Zone', 'Total_Target'] and not str(col).startswith('Unnamed'):
        product_cols.append(col)

print(f"  - Product columns found: {len(product_cols)}")
print(f"  - Sample products: {product_cols[:5]}")

# ============================================================================
# STEP 4: NORMALIZE MARKET NAMES FOR MATCHING
# ============================================================================

print("\nSTEP 4: Normalizing market names for fuzzy matching...")

def normalize_market(name):
    """Normalize market name for matching"""
    if pd.isna(name):
        return ""
    name = str(name).upper().strip()
    # Remove punctuation
    name = name.replace(',', '').replace('.', '').replace('-', ' ')
    name = name.replace('(', '').replace(')', '')
    name = name.replace('+', ' ')
    # Remove extra spaces
    name = ' '.join(name.split())
    return name

def fuzzy_match_score(str1, str2):
    """Calculate similarity score between two strings"""
    return SequenceMatcher(None, str1, str2).ratio()

def find_best_match(target_market, mpo_markets, threshold=0.75):
    """Find best matching market from MPO list"""
    target_norm = normalize_market(target_market)
    
    if not target_norm:
        return None, 0
    
    best_match = None
    best_score = 0
    
    for mpo_market in mpo_markets:
        mpo_norm = normalize_market(mpo_market)
        score = fuzzy_match_score(target_norm, mpo_norm)
        
        if score > best_score:
            best_score = score
            best_match = mpo_market
    
    if best_score >= threshold:
        return best_match, best_score
    else:
        return None, best_score

# Normalize market names
df_mpo['Market_Normalized'] = df_mpo['MARKET'].apply(normalize_market)
df_target['Market_Normalized'] = df_target['Market'].apply(normalize_market)

print(f"  - MPO markets normalized: {df_mpo['Market_Normalized'].nunique()}")
print(f"  - Target markets normalized: {df_target['Market_Normalized'].nunique()}")

# ============================================================================
# STEP 5: MATCH MARKETS AND MERGE DATA
# ============================================================================

print("\nSTEP 5: Matching markets and merging data...")

# Create a mapping dictionary for faster lookup
target_market_data = {}
for idx, row in df_target.iterrows():
    market_norm = row['Market_Normalized']
    if market_norm:
        # Store product data for this market
        product_data = {}
        for col in product_cols:
            product_data[col] = row[col]
        target_market_data[market_norm] = product_data

print(f"  - Target market data prepared: {len(target_market_data)} markets")

# Match each MPO market with target market
matches = []
no_matches = []
fuzzy_matches = []

for idx, row in df_mpo.iterrows():
    mpo_market = row['MARKET']
    mpo_market_norm = row['Market_Normalized']
    
    # Try exact match first
    if mpo_market_norm in target_market_data:
        matches.append((mpo_market, mpo_market, 1.0))
        # Add product data
        for col in product_cols:
            df_mpo.at[idx, col] = target_market_data[mpo_market_norm].get(col, 0)
    else:
        # Try fuzzy match
        best_match, score = find_best_match(mpo_market, df_target['Market'].unique(), threshold=0.75)
        
        if best_match:
            fuzzy_matches.append((mpo_market, best_match, score))
            # Get normalized version of best match
            best_match_norm = normalize_market(best_match)
            if best_match_norm in target_market_data:
                for col in product_cols:
                    df_mpo.at[idx, col] = target_market_data[best_match_norm].get(col, 0)
        else:
            no_matches.append((mpo_market, score))
            # Fill with 0
            for col in product_cols:
                df_mpo.at[idx, col] = 0

print(f"\n  Results:")
print(f"  - Exact matches: {len(matches)}")
print(f"  - Fuzzy matches: {len(fuzzy_matches)}")
print(f"  - No matches: {len(no_matches)}")

if fuzzy_matches:
    print(f"\n  Sample fuzzy matches (first 10):")
    for mpo_m, target_m, score in fuzzy_matches[:10]:
        print(f"    '{mpo_m}' → '{target_m}' (score: {score:.2f})")

if no_matches:
    print(f"\n  Markets with no match (first 10):")
    for market, score in no_matches[:10]:
        print(f"    '{market}' (best score: {score:.2f})")

# ============================================================================
# STEP 6: REORGANIZE COLUMNS
# ============================================================================

print("\nSTEP 6: Reorganizing columns...")

# Desired column order:
# A: DEPOT
# B: ZONE
# C: FM/AM, ZONE
# D: MARKET
# E: MPO CODE
# F: DEPOT_MPO_CODE
# G onwards: Product columns

base_cols = ['DEPOT', 'ZONE', 'FM/AM, ZONE', 'MARKET', 'MPO CODE', 'DEPOT_MPO_CODE']
final_cols = base_cols + product_cols

# Reorder columns
df_final = df_mpo[final_cols].copy()

print(f"  - Final columns: {len(final_cols)}")
print(f"  - Base columns (A-F): {base_cols}")
print(f"  - Product columns (G onwards): {len(product_cols)}")

# ============================================================================
# STEP 7: CALCULATE TOTAL TARGET
# ============================================================================

print("\nSTEP 7: Calculating total target...")

df_final['Total_Target'] = df_final[product_cols].sum(axis=1)

print(f"  - Total target across all markets: {df_final['Total_Target'].sum():,.0f}")

# ============================================================================
# STEP 8: SAVE OUTPUT
# ============================================================================

print("\nSTEP 8: Saving output...")

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file = f"MPO_Field_With_Targets_{timestamp}.xlsx"

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    # Sheet 1: Full data with all products
    df_final.to_excel(writer, sheet_name='MPO_Field_Targets', index=False)
    
    # Sheet 2: Summary (without individual products)
    summary_cols = base_cols + ['Total_Target']
    df_final[summary_cols].to_excel(writer, sheet_name='Summary', index=False)
    
    # Sheet 3: Match report
    match_report = pd.DataFrame({
        'MPO_Market': [m[0] for m in matches] + [m[0] for m in fuzzy_matches] + [m[0] for m in no_matches],
        'Target_Market': [m[1] for m in matches] + [m[1] for m in fuzzy_matches] + ['NO MATCH'] * len(no_matches),
        'Match_Score': [m[2] for m in matches] + [m[2] for m in fuzzy_matches] + [m[1] for m in no_matches],
        'Match_Type': ['Exact'] * len(matches) + ['Fuzzy'] * len(fuzzy_matches) + ['No Match'] * len(no_matches)
    })
    match_report.to_excel(writer, sheet_name='Match_Report', index=False)

print(f"\n✓ Output saved: {output_file}")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total MPO records: {len(df_final)}")
print(f"Product columns added: {len(product_cols)}")
print(f"Total target: {df_final['Total_Target'].sum():,.0f}")
print(f"\nMatching results:")
print(f"  - Exact matches: {len(matches)} ({len(matches)/len(df_mpo)*100:.1f}%)")
print(f"  - Fuzzy matches: {len(fuzzy_matches)} ({len(fuzzy_matches)/len(df_mpo)*100:.1f}%)")
print(f"  - No matches: {len(no_matches)} ({len(no_matches)/len(df_mpo)*100:.1f}%)")

print("\n" + "=" * 80)
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
