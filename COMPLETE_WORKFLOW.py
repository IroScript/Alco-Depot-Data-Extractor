"""
================================================================================
COMPLETE DEPOT DATA PROCESSING WORKFLOW
================================================================================
This script combines all steps from data extraction to final target vs achievement report.

WORKFLOW:
1. Extract product-level sales data from depot databases (uses process_product_level_FAST.py output)
2. Create achievement pivot table with concatenated keys
3. Extract target data with correct product names
4. Merge targets into MPO field data with fuzzy matching
5. Fix achievement pivot case sensitivity
6. Create final target vs achievement report with alternating columns

INPUT FILES REQUIRED:
- Product_Level_Net_Sales_*.csv (from process_product_level_FAST.py)
- Unit Target of April-2026 (2).xlsx
- MPO_CODE_AND_FIELD.xlsx

OUTPUT FILES:
- Achievement_Pivot_*.xlsx
- Target_Data_With_Products_*.xlsx
- MPO_Field_With_Targets_*.xlsx
- Achievement_Pivot_Fixed_*.xlsx
- MPO_Target_vs_Achievement_*.xlsx (FINAL OUTPUT with formulas)
- MPO_Target_vs_Achievement_Values_*.xlsx (FINAL OUTPUT with values)

Author: Auto-generated
Date: 2026-05-23
================================================================================
"""

import pandas as pd
import numpy as np
from datetime import datetime
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from difflib import SequenceMatcher
import re
import os
import glob
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

# Input files
MPO_FIELD_FILE = r"C:\Users\Irak\Desktop\Barishal April Data\MPO_CODE_AND_FIELD.xlsx"
TARGET_FILE = r"C:\Users\Irak\Desktop\Barishal April Data\Unit Target of April-2026 (2).xlsx"

# Find the latest Product_Level_Net_Sales CSV
csv_files = glob.glob(r"C:\Users\Irak\Desktop\Barishal April Data\Product_Level_Net_Sales_*.csv")
if not csv_files:
    print("ERROR: No Product_Level_Net_Sales CSV file found!")
    print("Please run process_product_level_FAST.py first to generate the sales data.")
    exit(1)

ACHIEVEMENT_CSV = max(csv_files, key=os.path.getctime)  # Get the latest file

print("=" * 80)
print("COMPLETE DEPOT DATA PROCESSING WORKFLOW")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
print(f"Using achievement file: {os.path.basename(ACHIEVEMENT_CSV)}\n")

# ============================================================================
# STEP 1: CREATE ACHIEVEMENT PIVOT TABLE
# ============================================================================

print("=" * 80)
print("STEP 1: CREATE ACHIEVEMENT PIVOT TABLE")
print("=" * 80)

print("\n1.1: Loading achievement CSV...")
df_sales = pd.read_csv(ACHIEVEMENT_CSV)
print(f"  - Total records: {len(df_sales)}")

print("\n1.2: Adding concatenated columns...")
df_sales['DepotMPO_CodeProduct_Code'] = df_sales['Depot'] + '_' + df_sales['MPO_Code'] + '_' + df_sales['Product_Code']
df_sales['DepotMPO_Code'] = df_sales['Depot'] + '_' + df_sales['MPO_Code']
print(f"  - Added DepotMPO_CodeProduct_Code and DepotMPO_Code")

print("\n1.3: Creating pivot table...")
pivot = pd.pivot_table(
    df_sales,
    values='ACTUAL_SALE_QTY',
    index=['DepotMPO_CodeProduct_Code', 'Depot', 'MPO_Code', 'DepotMPO_Code', 'Product_Code', 'Product_Name'],
    columns='Month',
    aggfunc='sum',
    fill_value=0,
    margins=True,
    margins_name='Grand Total'
)
pivot_df = pivot.reset_index()
print(f"  - Pivot table shape: {pivot_df.shape}")

print("\n1.4: Extracting April achievement...")
april_col = None
for col in pivot_df.columns:
    if '04' in str(col) or 'April' in str(col):
        april_col = col
        break

if april_col:
    april_summary = pivot_df[['DepotMPO_CodeProduct_Code', 'Depot', 'MPO_Code', 'DepotMPO_Code', 
                               'Product_Code', 'Product_Name', april_col]].copy()
    april_summary.rename(columns={april_col: 'April_Achievement'}, inplace=True)
    april_summary = april_summary[april_summary['DepotMPO_CodeProduct_Code'] != 'Grand Total']
    print(f"  - April records: {len(april_summary)}")
    print(f"  - Total April achievement: {april_summary['April_Achievement'].sum():,.0f}")
else:
    print("  ERROR: April column not found!")
    exit(1)

# Add uppercase lookup column
april_summary.insert(0, 'LOOKUP_KEY_UPPER', april_summary['DepotMPO_CodeProduct_Code'].str.upper())
print(f"  - Added LOOKUP_KEY_UPPER column")

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
achievement_pivot_file = f"Achievement_Pivot_{timestamp}.xlsx"

with pd.ExcelWriter(achievement_pivot_file, engine='openpyxl') as writer:
    pivot_df.to_excel(writer, sheet_name='Pivot_All_Months', index=False)
    april_summary.to_excel(writer, sheet_name='April_Achievement', index=False)
    df_sales.to_excel(writer, sheet_name='Data_With_Concatenations', index=False)

print(f"\n✓ Achievement pivot saved: {achievement_pivot_file}")

# ============================================================================
# STEP 2: EXTRACT TARGET DATA WITH PRODUCT NAMES
# ============================================================================

print("\n" + "=" * 80)
print("STEP 2: EXTRACT TARGET DATA WITH PRODUCT NAMES")
print("=" * 80)

print("\n2.1: Reading product names from row 3...")
df_raw = pd.read_excel(TARGET_FILE, header=None)
product_names_row = df_raw.iloc[2]

product_names = []
for i in range(8, len(product_names_row)):
    prod_name = product_names_row.iloc[i]
    if pd.notna(prod_name):
        product_names.append(str(prod_name).strip())
    else:
        product_names.append(f"Product_{i}")

print(f"  - Total product columns found: {len(product_names)}")

print("\n2.2: Reading data with proper headers...")
df_target_raw = pd.read_excel(TARGET_FILE, header=1)

# Assign column names
df_target_raw.columns.values[0] = 'Sl_No'
df_target_raw.columns.values[1] = 'Name'
df_target_raw.columns.values[2] = 'Designation'
df_target_raw.columns.values[3] = 'Market'

# Assign product names with duplicate handling
product_name_counts = {}
for i, prod_name in enumerate(product_names):
    col_idx = 8 + i
    if col_idx < len(df_target_raw.columns):
        if prod_name in product_name_counts:
            product_name_counts[prod_name] += 1
            unique_name = f"{prod_name}_Group{product_name_counts[prod_name]}"
        else:
            product_name_counts[prod_name] = 1
            unique_name = prod_name
        df_target_raw.columns.values[col_idx] = unique_name

print("\n2.3: Filtering valid designations...")
VALID_DESIGNATIONS = [
    'AFM(MMO)', 'AFM', 'AM(AFM)', 'AM(Self)', 'DA', 'FM(MPO)', 'FM(Self)',
    'MMO', 'MPO', 'MR', 'Self', 'SMMO', 'SMPO',
    'Sr.DA', 'Sr.FM(Self)', 'Sr.RSM(Self)'
]

df_target_filtered = df_target_raw[df_target_raw['Designation'].isin(VALID_DESIGNATIONS)].reset_index(drop=True)
df_target_filtered = df_target_filtered[df_target_filtered['Market'].notna()].reset_index(drop=True)
df_target_filtered = df_target_filtered[~df_target_filtered['Market'].astype(str).str.contains('Tab|Cap|Syp|Susp|Present Market', case=False, na=False)]
df_target_filtered = df_target_filtered.reset_index(drop=True)

print(f"  - Total rows with valid designations: {len(df_target_filtered)}")

print("\n2.4: Extracting zones...")
zones_dict = {}
current_zone = None

for idx, row in df_raw.iterrows():
    if pd.notna(row.iloc[1]) and 'Zone' in str(row.iloc[1]):
        current_zone = str(row.iloc[1]).replace('Zone :', '').replace('Zone', '').strip()
    if pd.notna(row.iloc[3]):
        market = str(row.iloc[3]).strip()
        if market and market != 'Present Market':
            zones_dict[market] = current_zone

df_target_filtered['Zone'] = df_target_filtered['Market'].map(zones_dict)
print(f"  - Unique zones found: {df_target_filtered['Zone'].nunique()}")

print("\n2.5: Processing product targets...")
product_cols = []
for i in range(8, len(df_target_filtered.columns)):
    col_name = df_target_filtered.columns[i]
    if col_name and not str(col_name).startswith('Unnamed') and not str(col_name).startswith('Product_'):
        product_cols.append(col_name)

for col in product_cols:
    if col in df_target_filtered.columns:
        try:
            df_target_filtered.loc[:, col] = pd.to_numeric(df_target_filtered[col], errors='coerce').fillna(0).round(0).astype(int)
        except:
            df_target_filtered.loc[:, col] = 0

df_target_filtered['Total_Target'] = df_target_filtered[product_cols].sum(axis=1)
print(f"  - Product columns: {len(product_cols)}")
print(f"  - Total target quantity: {df_target_filtered['Total_Target'].sum():,.0f}")

target_data_file = f"Target_Data_With_Products_{timestamp}.xlsx"
with pd.ExcelWriter(target_data_file, engine='openpyxl') as writer:
    df_target_filtered[['Zone', 'Market', 'Designation', 'Total_Target']].to_excel(writer, sheet_name='Summary', index=False)
    df_target_filtered.to_excel(writer, sheet_name='Full_Data', index=False)

print(f"\n✓ Target data saved: {target_data_file}")

# ============================================================================
# STEP 3: MERGE TARGETS INTO MPO FIELD DATA
# ============================================================================

print("\n" + "=" * 80)
print("STEP 3: MERGE TARGETS INTO MPO FIELD DATA")
print("=" * 80)

print("\n3.1: Loading MPO_CODE_AND_FIELD file...")
df_mpo = pd.read_excel(MPO_FIELD_FILE)
print(f"  - Total records: {len(df_mpo)}")

print("\n3.2: Adding DEPOT_MPO_CODE concatenation...")
df_mpo['DEPOT'] = df_mpo['DEPOT'].astype(str)
df_mpo['MPO CODE'] = df_mpo['MPO CODE'].astype(str)
df_mpo['DEPOT_MPO_CODE'] = df_mpo['DEPOT'] + '_' + df_mpo['MPO CODE']
print(f"  - Added DEPOT_MPO_CODE")

print("\n3.3: Normalizing market names for matching...")

def strip_depot_code(name):
    """Remove trailing depot codes like (BARI), (DK.B), (CTG.A), (RNG) etc."""
    import re
    cleaned = re.sub(r'\s*\([A-Z]{2,5}(?:[\.\-][A-Z0-9])?\)\s*$', '', name.strip().upper())
    return cleaned.strip()

def normalize_core(name):
    """Normalize keeping numbers and hyphens - removes only depot suffix"""
    if pd.isna(name):
        return ""
    n = strip_depot_code(str(name))
    n = re.sub(r'\s*-\s*', '-', n)
    n = re.sub(r'\s*\+\s*', '+', n)
    return ' '.join(n.split())

def remove_all_parens(n):
    """Strip ALL parentheticals for fuzzy matching"""
    return ' '.join(re.sub(r'\s*\([^)]*\)\s*', ' ', n).split())

# Build target lookups
target_norm_map = {normalize_core(t): t for t in df_target_filtered['Market'].unique()}
target_no_paren_map = {remove_all_parens(normalize_core(t)): t for t in df_target_filtered['Market'].unique()}

print("\n3.4: Matching markets (two-pass: exact first, then fuzzy)...")

# Target product data lookup
target_market_data = {}
for idx, row in df_target_filtered.iterrows():
    market = row['Market']
    if market:
        target_market_data[market] = {col: row[col] for col in product_cols}

used_target_markets = set()
matches = []      # (mpo_market, target_market, score)
fuzzy_matches = []
no_matches = []

# PASS 1: Exact matches for ALL markets (no ordering bias)
for idx, row in df_mpo.iterrows():
    mpo_market = row['MARKET']
    norm = normalize_core(mpo_market)
    no_paren = remove_all_parens(norm)
    
    if norm in target_norm_map and target_norm_map[norm] not in used_target_markets:
        t = target_norm_map[norm]
        matches.append((mpo_market, t, 1.0))
        used_target_markets.add(t)
        df_mpo.at[idx, '_matched_to'] = t
    elif no_paren in target_no_paren_map and target_no_paren_map[no_paren] not in used_target_markets:
        t = target_no_paren_map[no_paren]
        matches.append((mpo_market, t, 1.0))
        used_target_markets.add(t)
        df_mpo.at[idx, '_matched_to'] = t
    else:
        df_mpo.at[idx, '_matched_to'] = None

# PASS 2: Fuzzy matches for unmatched markets
for idx, row in df_mpo.iterrows():
    if pd.notna(row.get('_matched_to')):
        continue
    mpo_market = row['MARKET']
    no_paren = remove_all_parens(normalize_core(mpo_market))
    best_t, best_s = None, 0
    for t_key, t_orig in target_no_paren_map.items():
        if t_orig in used_target_markets:
            continue
        s = SequenceMatcher(None, no_paren, t_key).ratio()
        if s > best_s:
            best_s = s
            best_t = t_orig
    if best_s >= 0.83 and best_t:
        fuzzy_matches.append((mpo_market, best_t, best_s))
        used_target_markets.add(best_t)
        df_mpo.at[idx, '_matched_to'] = best_t
    else:
        no_matches.append((mpo_market, best_s))

# Apply product data from matches
for idx, row in df_mpo.iterrows():
    matched_to = row.get('_matched_to')
    if pd.notna(matched_to) and matched_to in target_market_data:
        for col in product_cols:
            df_mpo.at[idx, col] = target_market_data[matched_to].get(col, 0)
    else:
        for col in product_cols:
            df_mpo.at[idx, col] = 0

print(f"  - Exact matches: {len(matches)}")
print(f"  - Fuzzy matches: {len(fuzzy_matches)}")
print(f"  - No matches: {len(no_matches)}")

base_cols = ['DEPOT', 'ZONE', 'FM/AM, ZONE', 'MARKET', 'MPO CODE', 'DEPOT_MPO_CODE']
final_cols = base_cols + product_cols
df_mpo_final = df_mpo[final_cols].copy()
df_mpo_final['Total_Target'] = df_mpo_final[product_cols].sum(axis=1)

mpo_field_targets_file = f"MPO_Field_With_Targets_{timestamp}.xlsx"
with pd.ExcelWriter(mpo_field_targets_file, engine='openpyxl') as writer:
    df_mpo_final.to_excel(writer, sheet_name='MPO_Field_Targets', index=False)
    df_mpo_final[base_cols + ['Total_Target']].to_excel(writer, sheet_name='Summary', index=False)
    
    # Match Report
    match_report = pd.DataFrame({
        'MPO_Market': [m[0] for m in matches] + [m[0] for m in fuzzy_matches] + [m[0] for m in no_matches],
        'Target_Market': [m[1] for m in matches] + [m[1] for m in fuzzy_matches] + ['NO MATCH'] * len(no_matches),
        'Match_Score': [m[2] for m in matches] + [m[2] for m in fuzzy_matches] + [m[1] for m in no_matches],
        'Match_Type': ['Exact'] * len(matches) + ['Fuzzy'] * len(fuzzy_matches) + ['No Match'] * len(no_matches),
        'MPO_Normalized': [normalize_core(m[0]) for m in matches] + [normalize_core(m[0]) for m in fuzzy_matches] + [normalize_core(m[0]) for m in no_matches],
        'Target_Normalized': [normalize_core(m[1]) for m in matches] + [normalize_core(m[1]) for m in fuzzy_matches] + [''] * len(no_matches)
    })
    match_report.to_excel(writer, sheet_name='Match_Report', index=False)
    
    # Markets Taken (Successfully Matched)
    markets_taken = pd.DataFrame({
        'Market': [m[0] for m in matches] + [m[0] for m in fuzzy_matches],
        'Matched_To': [m[1] for m in matches] + [m[1] for m in fuzzy_matches],
        'Match_Type': ['Exact'] * len(matches) + ['Fuzzy'] * len(fuzzy_matches),
        'Match_Score': [m[2] for m in matches] + [m[2] for m in fuzzy_matches],
        'Total_Target': [df_mpo_final[df_mpo_final['MARKET'] == m[0]]['Total_Target'].iloc[0] if len(df_mpo_final[df_mpo_final['MARKET'] == m[0]]) > 0 else 0 for m in matches + fuzzy_matches]
    })
    markets_taken = markets_taken.sort_values('Market')
    markets_taken.to_excel(writer, sheet_name='Markets_Taken', index=False)
    
    # Markets Skipped (No Match Found)
    markets_skipped = pd.DataFrame({
        'Market': [m[0] for m in no_matches],
        'Best_Score': [m[1] for m in no_matches],
        'Reason': ['No match found (score < 0.83)'] * len(no_matches),
        'MPO_Normalized': [normalize_core(m[0]) for m in no_matches]
    })
    markets_skipped = markets_skipped.sort_values('Market')
    markets_skipped.to_excel(writer, sheet_name='Markets_Skipped', index=False)
    
    # Target Markets Not Used
    used_target_markets = set([m[1] for m in matches] + [m[1] for m in fuzzy_matches])
    all_target_markets = set(df_target_filtered['Market'].unique())
    unused_target_markets = all_target_markets - used_target_markets
    
    if unused_target_markets:
        unused_df = pd.DataFrame({
            'Target_Market': sorted(list(unused_target_markets)),
            'Reason': ['Not matched to any MPO market'] * len(unused_target_markets),
            'Target_Normalized': [normalize_core(m) for m in sorted(list(unused_target_markets))]
        })
        unused_df.to_excel(writer, sheet_name='Target_Markets_Not_Used', index=False)

print(f"\n✓ MPO field with targets saved: {mpo_field_targets_file}")
print(f"  - Sheet 1: MPO_Field_Targets (full data)")
print(f"  - Sheet 2: Summary (without products)")
print(f"  - Sheet 3: Match_Report (all matches)")
print(f"  - Sheet 4: Markets_Taken ({len(matches) + len(fuzzy_matches)} markets)")
print(f"  - Sheet 5: Markets_Skipped ({len(no_matches)} markets)")
if unused_target_markets:
    print(f"  - Sheet 6: Target_Markets_Not_Used ({len(unused_target_markets)} markets)")

# ============================================================================
# STEP 4: CREATE FINAL TARGET VS ACHIEVEMENT REPORT
# ============================================================================

print("\n" + "=" * 80)
print("STEP 4: CREATE FINAL TARGET VS ACHIEVEMENT REPORT")
print("=" * 80)

print("\n4.1: Creating product code mapping...")
product_mapping = april_summary[['Product_Code', 'Product_Name']].drop_duplicates()
product_code_dict = dict(zip(product_mapping['Product_Name'], product_mapping['Product_Code']))
print(f"  - Unique products in achievement: {len(product_code_dict)}")

print("\n4.2: Matching target products to codes...")

def normalize_product_name(name):
    if pd.isna(name):
        return ""
    name = str(name).upper().strip()
    name = re.sub(r'\s*(TAB|TABLET|CAP|CAPSULE|SYP|SYRUP|SUSP|SUSPENSION)\.?\s*', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\([^)]*\)', '', name)
    name = re.sub(r'\d+\s*MG', '', name, flags=re.IGNORECASE)
    name = name.replace('-', '').replace('.', '').replace(',', '').replace('+', '')
    name = ' '.join(name.split())
    return name.replace(' ', '')

def find_product_code(target_product, product_code_dict):
    target_norm = normalize_product_name(target_product)
    best_match = None
    best_score = 0
    
    for ach_product, code in product_code_dict.items():
        ach_norm = normalize_product_name(ach_product)
        score = SequenceMatcher(None, target_norm, ach_norm).ratio()
        if score > best_score:
            best_score = score
            best_match = code
    
    if best_score >= 0.75:
        return best_match
    else:
        return None

target_to_code = {}
for prod in product_cols:
    code = find_product_code(prod, product_code_dict)
    target_to_code[prod] = code if code else ""

matched = sum(1 for v in target_to_code.values() if v)
print(f"  - Matched: {matched}/{len(product_cols)}")

print("\n4.3: Creating dataframe with alternating columns...")
new_columns = base_cols.copy()
new_col_mapping = {}

for prod in product_cols:
    if target_to_code.get(prod):
        target_col = f"{prod}"
        ach_col = f"{prod}_ACH"
        new_columns.append(target_col)
        new_columns.append(ach_col)
        new_col_mapping[target_col] = (prod, 'target')
        new_col_mapping[ach_col] = (prod, 'ach')

df_new = pd.DataFrame(columns=new_columns)
for col in base_cols:
    df_new[col] = df_mpo_final[col]

for new_col, (orig_col, col_type) in new_col_mapping.items():
    if col_type == 'target':
        df_new[new_col] = df_mpo_final[orig_col]
    else:
        df_new[new_col] = 0

print(f"  - New shape: {df_new.shape}")

print("\n4.4: Adding product codes and labels rows...")
row1_data = {}
for col in base_cols:
    row1_data[col] = ""
for new_col, (orig_col, col_type) in new_col_mapping.items():
    if col_type == 'target':
        row1_data[new_col] = ""
    else:
        row1_data[new_col] = target_to_code.get(orig_col, "")

row2_data = {}
for col in base_cols:
    row2_data[col] = ""
for new_col, (orig_col, col_type) in new_col_mapping.items():
    if col_type == 'target':
        row2_data[new_col] = "TARGET"
    else:
        row2_data[new_col] = "ACH."

df_row1 = pd.DataFrame([row1_data])
df_row2 = pd.DataFrame([row2_data])
df_final = pd.concat([df_row1, df_row2, df_new], ignore_index=True)

print(f"  - Final shape: {df_final.shape}")

print("\n4.5: Saving with VLOOKUP formulas...")
output_file = f"MPO_Target_vs_Achievement_{timestamp}.xlsx"
df_final.to_excel(output_file, sheet_name='Target_vs_Achievement', index=False)

wb = load_workbook(output_file)
ws = wb['Target_vs_Achievement']

for excel_col_idx, col_name in enumerate(df_final.columns, start=1):
    if col_name in new_col_mapping:
        orig_col, col_type = new_col_mapping[col_name]
        
        if col_type == 'ach':
            col_letter = get_column_letter(excel_col_idx)
            product_code_cell = f"{col_letter}$2"
            depot_mpo_cell = "$F"
            
            for row_idx in range(4, len(df_final) + 2):
                formula = f'=IFERROR(VLOOKUP(UPPER({depot_mpo_cell}{row_idx}&"_"&{product_code_cell}),[{achievement_pivot_file}]April_Achievement!$A:$H,8,FALSE),0)'
                ws[f"{col_letter}{row_idx}"] = formula

wb.save(output_file)
wb.close()
print(f"  - Formulas added for {matched} products")

print("\n4.6: Creating version with calculated values...")
achievement_lookup = {}
for idx, row in april_summary.iterrows():
    key = row['LOOKUP_KEY_UPPER']
    achievement_lookup[key] = row['April_Achievement']

df_with_values = pd.read_excel(output_file, sheet_name='Target_vs_Achievement')
for col in df_with_values.columns:
    df_with_values[col] = df_with_values[col].astype(object)

for new_col, (orig_col, col_type) in new_col_mapping.items():
    if col_type == 'ach':
        code = target_to_code.get(orig_col)
        if code:
            for row_idx in range(2, len(df_with_values)):
                depot_mpo = df_with_values.iloc[row_idx]['DEPOT_MPO_CODE']
                if pd.notna(depot_mpo):
                    key = f"{depot_mpo}_{code}".upper()
                    ach_value = achievement_lookup.get(key, 0)
                    if isinstance(ach_value, (int, float)) and not pd.isna(ach_value):
                        df_with_values.at[row_idx, new_col] = int(ach_value) if ach_value == int(ach_value) else ach_value
                    else:
                        df_with_values.at[row_idx, new_col] = 0

values_file = f"MPO_Target_vs_Achievement_Values_{timestamp}.xlsx"
df_with_values.to_excel(values_file, sheet_name='Target_vs_Achievement', index=False)

print(f"\n✓ Target vs Achievement saved: {output_file}")
print(f"✓ Values version saved: {values_file}")

# ============================================================================
# FINAL SUMMARY
# ============================================================================

print("\n" + "=" * 80)
print("WORKFLOW COMPLETED SUCCESSFULLY!")
print("=" * 80)

print(f"\nFILES CREATED:")
print(f"  1. {achievement_pivot_file}")
print(f"  2. {target_data_file}")
print(f"  3. {mpo_field_targets_file} ⭐ (with verification sheets)")
print(f"  4. {output_file} (FINAL - with VLOOKUP formulas)")
print(f"  5. {values_file} (FINAL - with calculated values)")

print(f"\nSTATISTICS:")
print(f"  - Total MPO records: {len(df_mpo_final)}")
print(f"  - Product columns: {len(product_cols)}")
print(f"  - Products matched: {matched}/{len(product_cols)}")
print(f"  - Total target: {df_mpo_final['Total_Target'].sum():,.0f}")
print(f"  - Total achievement: {april_summary['April_Achievement'].sum():,.0f}")

print(f"\nMARKET MATCHING:")
print(f"  - Exact matches: {len(matches)} ({len(matches)/len(df_mpo)*100:.1f}%)")
print(f"  - Fuzzy matches: {len(fuzzy_matches)} ({len(fuzzy_matches)/len(df_mpo)*100:.1f}%)")
print(f"  - No matches (ZERO targets): {len(no_matches)} ({len(no_matches)/len(df_mpo)*100:.1f}%)")
print(f"  - Total matched: {len(matches) + len(fuzzy_matches)} ({(len(matches) + len(fuzzy_matches))/len(df_mpo)*100:.1f}%)")

if no_matches:
    print(f"\n⚠ MARKETS WITH ZERO TARGETS (first 10):")
    for market, score in no_matches[:10]:
        print(f"    - {market} (best score: {score:.2f})")
    if len(no_matches) > 10:
        print(f"    ... and {len(no_matches) - 10} more (see Markets_Skipped sheet)")

print("\n" + "=" * 80)
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
print("\nVERIFICATION SHEETS:")
print(f"  ✓ Open '{mpo_field_targets_file}'")
print(f"  ✓ Check 'Markets_Taken' sheet - All successfully matched markets")
print(f"  ✓ Check 'Markets_Skipped' sheet - Markets with ZERO targets")
print(f"  ✓ Check 'Target_Markets_Not_Used' sheet - Target markets not matched to any MPO")
print(f"  ✓ Check 'Match_Report' sheet - Detailed matching information")
print("\n" + "=" * 80)
