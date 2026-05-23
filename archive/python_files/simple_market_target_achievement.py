"""
Simple Market Target vs Achievement
===================================
Simplified approach:
1. Read target file and extract: Zone, Market, Designation, Total Target (sum of all products)
2. Match with MPO reference to get MPO codes
3. Match with achievement CSV (April data only)
4. Output: Market-wise Target vs Achievement

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

TARGET_FILE = r"C:\Users\Irak\Desktop\Barishal April Data\Unit Target of April-2026 (2).xlsx"
MPO_REFERENCE_FILE = r"C:\Users\Irak\Desktop\Barishal April Data\MPO_CODE_AND_FIELD.xlsx"
ACHIEVEMENT_CSV = r"C:\Users\Irak\Desktop\Barishal April Data\Product_Level_Net_Sales_20260522_232817.csv"

# Valid designations for actual markets (not team leaders)
VALID_DESIGNATIONS = [
    'AFM(MMO)', 'AM(AFM)', 'AM(Self)', 'DAFM(MPO)', 'FM(Self)',
    'MMO', 'MPO', 'MR', 'Self', 'SMMO', 'SMPO',
    'Sr.DA', 'Sr.FM(Self)', 'Sr.RSM(Self)'
]

print("=" * 80)
print("SIMPLE MARKET TARGET VS ACHIEVEMENT")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# ============================================================================
# STEP 1: READ TARGET FILE
# ============================================================================

print("STEP 1: Reading target file...")

# Read with header at row 1
df_target = pd.read_excel(TARGET_FILE, header=1)

# Rename key columns
df_target.columns.values[2] = 'Designation'
df_target.columns.values[3] = 'Market'

# Filter valid designations
df_target_filtered = df_target[df_target['Designation'].isin(VALID_DESIGNATIONS)].copy()
df_target_filtered = df_target_filtered[df_target_filtered['Market'].notna()].copy()

print(f"  - Total target records: {len(df_target_filtered)}")

# Extract zones by reading the full file again
df_full = pd.read_excel(TARGET_FILE, header=None)
zones_dict = {}
current_zone = None

for idx, row in df_full.iterrows():
    # Check column B (index 1) for zone
    if pd.notna(row.iloc[1]) and 'Zone' in str(row.iloc[1]):
        current_zone = str(row.iloc[1]).replace('Zone :', '').replace('Zone', '').strip()
    
    # Check if this row has a market in column D (index 3)
    if pd.notna(row.iloc[3]):
        market = str(row.iloc[3]).strip()
        if market and market != 'Present Market':
            zones_dict[market] = current_zone

# Assign zones
df_target_filtered['Zone'] = df_target_filtered['Market'].map(zones_dict)

print(f"  - Unique zones: {df_target_filtered['Zone'].nunique()}")
print(f"  - Unique markets: {df_target_filtered['Market'].nunique()}")

# Calculate total target (sum all numeric columns after Market)
market_col_idx = list(df_target_filtered.columns).index('Market')
numeric_cols = []

for col in df_target_filtered.columns[market_col_idx + 1:]:
    try:
        test = pd.to_numeric(df_target_filtered[col], errors='coerce')
        if test.notna().sum() > 0:
            numeric_cols.append(col)
            df_target_filtered[col] = test.fillna(0)
    except:
        pass

print(f"  - Found {len(numeric_cols)} numeric columns for target calculation")

# Round and sum
for col in numeric_cols:
    df_target_filtered[col] = df_target_filtered[col].round(0).astype(int)

df_target_filtered['Total_Target'] = df_target_filtered[numeric_cols].sum(axis=1)

print(f"  - Total target quantity: {df_target_filtered['Total_Target'].sum():,.0f}")

# ============================================================================
# STEP 2: LOAD MPO REFERENCE
# ============================================================================

print("\nSTEP 2: Loading MPO reference...")

df_mpo = pd.read_excel(MPO_REFERENCE_FILE)

print(f"  - MPO records: {len(df_mpo)}")

# Normalize market names for matching
def normalize_market(name):
    if pd.isna(name):
        return ""
    name = str(name).upper().strip()
    name = name.replace(',', '').replace('.', '').replace('-', ' ')
    name = name.replace('(', '').replace(')', '')
    name = ' '.join(name.split())
    return name

df_target_filtered['Market_Norm'] = df_target_filtered['Market'].apply(normalize_market)
df_mpo['Market_Norm'] = df_mpo['MARKET'].apply(normalize_market)

# Merge
df_with_mpo = df_target_filtered.merge(
    df_mpo[['DEPOT', 'MARKET', 'MPO CODE', 'Market_Norm']],
    on='Market_Norm',
    how='left'
)

df_with_mpo.rename(columns={'DEPOT': 'Depot', 'MPO CODE': 'MPO_Code', 'MARKET': 'Market_Ref'}, inplace=True)

matched = df_with_mpo['MPO_Code'].notna().sum()
print(f"  - Matched: {matched}/{len(df_with_mpo)}")

# ============================================================================
# STEP 3: LOAD ACHIEVEMENT DATA (APRIL ONLY)
# ============================================================================

print("\nSTEP 3: Loading achievement data...")

df_ach = pd.read_csv(ACHIEVEMENT_CSV)

print(f"  - Total records: {len(df_ach)}")

# Filter April only
df_ach_april = df_ach[df_ach['Month'] == '2026-04'].copy()

print(f"  - April records: {len(df_ach_april)}")

# Create DEPOT_MPO_CODE
df_ach_april['DEPOT_MPO_CODE'] = df_ach_april['Depot'] + '_' + df_ach_april['MPO_Code']

# Aggregate by DEPOT_MPO_CODE
df_ach_agg = df_ach_april.groupby('DEPOT_MPO_CODE')['ACTUAL_SALE_QTY'].sum().reset_index()
df_ach_agg.rename(columns={'ACTUAL_SALE_QTY': 'Total_Achievement'}, inplace=True)

print(f"  - Unique DEPOT_MPO combinations: {len(df_ach_agg)}")
print(f"  - Total achievement quantity: {df_ach_agg['Total_Achievement'].sum():,.0f}")

# ============================================================================
# STEP 4: MERGE TARGET WITH ACHIEVEMENT
# ============================================================================

print("\nSTEP 4: Merging target with achievement...")

# Normalize depot names for matching
# Achievement CSV has: Barishal, Chittagong, Cumilla, Faridpur, Jashore, Mymensingh, Rajshahi, Rangpur, Sylhet
# MPO reference has: BARISHAL, CHITTAGONG, CUMILLA, FARIDPUR, JASHORE, MYMENSINGH, RAJSHAHI, RANGPUR, SYLHET, DHAKA-2, etc.

def normalize_depot(depot_name):
    if pd.isna(depot_name):
        return ""
    depot = str(depot_name).upper().strip()
    # Remove numbers and hyphens
    depot = depot.split('-')[0]  # Take only the first part before hyphen
    return depot

# Normalize depots in both dataframes
df_with_mpo['Depot_Norm'] = df_with_mpo['Depot'].apply(normalize_depot)
df_ach_april['Depot_Norm'] = df_ach_april['Depot'].apply(normalize_depot)

# Create normalized DEPOT_MPO_CODE
df_with_mpo['MPO_Code'] = df_with_mpo['MPO_Code'].astype(str).fillna('')
df_with_mpo['DEPOT_MPO_NORM'] = df_with_mpo['Depot_Norm'] + '_' + df_with_mpo['MPO_Code']

df_ach_april['DEPOT_MPO_NORM'] = df_ach_april['Depot_Norm'] + '_' + df_ach_april['MPO_Code']

# Aggregate achievement by normalized DEPOT_MPO
df_ach_agg_norm = df_ach_april.groupby('DEPOT_MPO_NORM')['ACTUAL_SALE_QTY'].sum().reset_index()
df_ach_agg_norm.rename(columns={'ACTUAL_SALE_QTY': 'Total_Achievement'}, inplace=True)

print(f"  - Unique normalized DEPOT_MPO combinations in achievement: {len(df_ach_agg_norm)}")
print(f"  - Sample achievement keys: {df_ach_agg_norm['DEPOT_MPO_NORM'].head(10).tolist()}")
print(f"  - Sample target keys: {df_with_mpo['DEPOT_MPO_NORM'].head(10).tolist()}")

# Merge
df_final = df_with_mpo.merge(
    df_ach_agg_norm,
    on='DEPOT_MPO_NORM',
    how='left'
)

df_final['Total_Achievement'] = df_final['Total_Achievement'].fillna(0)

# Calculate metrics
df_final['Variance'] = df_final['Total_Achievement'] - df_final['Total_Target']
df_final['Achievement_Pct'] = 0.0
mask = df_final['Total_Target'] > 0
df_final.loc[mask, 'Achievement_Pct'] = (df_final.loc[mask, 'Total_Achievement'] / df_final.loc[mask, 'Total_Target'] * 100).round(2)

print(f"  - Final records: {len(df_final)}")

# ============================================================================
# STEP 5: CREATE OUTPUT
# ============================================================================

print("\nSTEP 5: Creating output...")

# Select key columns
output_cols = [
    'Zone', 'Depot', 'Market', 'Market_Ref', 'MPO_Code', 'Designation',
    'Total_Target', 'Total_Achievement', 'Variance', 'Achievement_Pct'
]

df_output = df_final[output_cols].copy()

# Sort by Zone and Market
df_output = df_output.sort_values(['Zone', 'Market'])

# Create output file
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file = f"Market_Target_Achievement_{timestamp}.xlsx"

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    df_output.to_excel(writer, sheet_name='Market_Summary', index=False)
    df_final.to_excel(writer, sheet_name='Full_Data', index=False)

print(f"\n✓ Output saved: {output_file}")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

total_target = df_output['Total_Target'].sum()
total_achievement = df_output['Total_Achievement'].sum()
overall_pct = (total_achievement / total_target * 100) if total_target > 0 else 0

print(f"Total Target: {total_target:,.0f}")
print(f"Total Achievement: {total_achievement:,.0f}")
print(f"Overall Achievement: {overall_pct:.2f}%")
print(f"Variance: {total_achievement - total_target:,.0f}")

markets_with_both = ((df_output['Total_Target'] > 0) & (df_output['Total_Achievement'] > 0)).sum()
markets_target_only = ((df_output['Total_Target'] > 0) & (df_output['Total_Achievement'] == 0)).sum()

print(f"\nMarkets with both: {markets_with_both}")
print(f"Markets with target only: {markets_target_only}")

print("\n" + "=" * 80)
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
