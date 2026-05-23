"""
Market-Wise Target vs Achievement - Detailed Analysis
=====================================================
This script creates a comprehensive market-wise comparison with:
- Zone information
- Market names
- Product-wise targets (rounded)
- MPO codes
- April achievements

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

# ============================================================================
# STEP 1: EXTRACT TARGET DATA
# ============================================================================

def extract_target_data():
    """
    Extract zone, market, designation, products, and targets from Excel file.
    """
    print("=" * 80)
    print("STEP 1: EXTRACTING TARGET DATA")
    print("=" * 80)
    
    # Read Excel file - row 2 (0-indexed) contains product names
    df_products = pd.read_excel(TARGET_FILE, header=None, nrows=3)
    product_names_row = df_products.iloc[2]  # Row 3 (0-indexed as 2)
    
    # Read again with proper header starting from row 1
    df = pd.read_excel(TARGET_FILE, header=1)
    
    # Assign column names from row 3 (product names)
    for i in range(len(df.columns)):
        if i < len(product_names_row):
            prod_name = product_names_row.iloc[i]
            if pd.notna(prod_name) and str(prod_name).strip() and 'Unnamed' not in str(df.columns[i]):
                # Only replace if it's a valid product name
                if i >= 8:  # Products start from column 8 onwards
                    df.columns.values[i] = str(prod_name).strip()
    
    # Assign key column names
    df.columns.values[2] = 'Designation'
    df.columns.values[3] = 'Market'
    
    print(f"Total rows loaded: {len(df)}")
    print(f"Total columns: {len(df.columns)}")
    print(f"Sample column names: {df.columns.tolist()[:15]}")
    
    # Filter only valid designations
    df_filtered = df[df['Designation'].isin(VALID_DESIGNATIONS)].copy()
    
    # Remove rows where Market is NaN
    df_filtered = df_filtered[df_filtered['Market'].notna()].copy()
    
    print(f"Rows with valid designations: {len(df_filtered)}")
    
    # Extract zone information from previous rows
    # Zone rows contain "Zone :" in column B (index 1)
    zones = []
    current_zone = None
    
    for idx, row in df.iterrows():
        # Check if this is a zone row (check column B - index 1)
        if pd.notna(row.iloc[1]) and 'Zone' in str(row.iloc[1]):
            current_zone = str(row.iloc[1]).replace('Zone :', '').replace('Zone', '').strip()
        
        # If this row is in our filtered data, assign the zone
        if idx in df_filtered.index:
            zones.append(current_zone)
    
    df_filtered['Zone'] = zones
    
    print(f"Unique zones found: {df_filtered['Zone'].nunique()}")
    print(f"Unique markets: {df_filtered['Market'].nunique()}")
    print(f"Sample zones: {df_filtered['Zone'].unique()[:5]}")
    
    return df_filtered

# ============================================================================
# STEP 2: PROCESS PRODUCT TARGETS
# ============================================================================

def process_product_targets(df_target):
    """
    Extract and round product-wise targets.
    """
    print("\n" + "=" * 80)
    print("STEP 2: PROCESSING PRODUCT TARGETS")
    print("=" * 80)
    
    # Identify product columns (numeric columns after 'Market')
    market_col_idx = list(df_target.columns).index('Market')
    potential_product_cols = df_target.columns[market_col_idx + 1:]
    
    product_cols = []
    for col in potential_product_cols:
        # Check if column has numeric data
        try:
            test_series = pd.to_numeric(df_target[col], errors='coerce')
            if test_series.notna().sum() > 0:
                product_cols.append(col)
        except:
            pass
    
    print(f"Found {len(product_cols)} product columns")
    
    # Convert to numeric and round
    for col in product_cols:
        df_target[col] = pd.to_numeric(df_target[col], errors='coerce').fillna(0)
        df_target[col] = df_target[col].round(0).astype(int)
    
    # Create a clean dataframe with key columns + products
    key_cols = ['Zone', 'Designation', 'Market']
    result_df = df_target[key_cols + product_cols].copy()
    
    print(f"Product columns: {product_cols[:5]}... (showing first 5)")
    
    return result_df, product_cols

# ============================================================================
# STEP 3: MERGE WITH MPO REFERENCE
# ============================================================================

def merge_with_mpo_reference(df_target):
    """
    Add MPO codes, Depot, and FM/AM information from reference file.
    """
    print("\n" + "=" * 80)
    print("STEP 3: MERGING WITH MPO REFERENCE")
    print("=" * 80)
    
    # Load MPO reference
    df_mpo = pd.read_excel(MPO_REFERENCE_FILE)
    
    print(f"MPO reference records: {len(df_mpo)}")
    print(f"Columns: {df_mpo.columns.tolist()}")
    
    # Normalize market names for matching
    df_target['Market_Normalized'] = df_target['Market'].str.upper().str.strip()
    df_target['Market_Normalized'] = df_target['Market_Normalized'].str.replace(r'[,.\-()]', ' ', regex=True)
    df_target['Market_Normalized'] = df_target['Market_Normalized'].str.replace(r'\s+', ' ', regex=True)
    
    df_mpo['Market_Normalized'] = df_mpo['MARKET'].str.upper().str.strip()
    df_mpo['Market_Normalized'] = df_mpo['Market_Normalized'].str.replace(r'[,.\-()]', ' ', regex=True)
    df_mpo['Market_Normalized'] = df_mpo['Market_Normalized'].str.replace(r'\s+', ' ', regex=True)
    
    # Merge
    df_merged = df_target.merge(
        df_mpo[['DEPOT', 'ZONE', 'FM/AM, ZONE', 'MARKET', 'MPO CODE', 'Market_Normalized']],
        on='Market_Normalized',
        how='left'
    )
    
    # Rename columns
    df_merged.rename(columns={
        'DEPOT': 'Depot',
        'ZONE': 'Zone_Code',
        'FM/AM, ZONE': 'FM_AM',
        'MARKET': 'Market_Reference',
        'MPO CODE': 'MPO_Code'
    }, inplace=True)
    
    # Drop normalized column
    df_merged.drop('Market_Normalized', axis=1, inplace=True)
    
    matched = df_merged['MPO_Code'].notna().sum()
    unmatched = df_merged['MPO_Code'].isna().sum()
    
    print(f"Matched markets: {matched}")
    print(f"Unmatched markets: {unmatched}")
    
    return df_merged

# ============================================================================
# STEP 4: LOAD AND PROCESS ACHIEVEMENT DATA
# ============================================================================

def load_achievement_data():
    """
    Load achievement CSV and create DEPOT_MPO_CODE concatenation.
    """
    print("\n" + "=" * 80)
    print("STEP 4: LOADING ACHIEVEMENT DATA")
    print("=" * 80)
    
    df_ach = pd.read_csv(ACHIEVEMENT_CSV)
    
    print(f"Total achievement records: {len(df_ach)}")
    print(f"Columns: {df_ach.columns.tolist()}")
    
    # Create DEPOT_MPO_CODE concatenation
    df_ach['DEPOT_MPO_CODE'] = df_ach['Depot'] + '_' + df_ach['MPO_Code']
    
    print(f"Unique DEPOT_MPO_CODE combinations: {df_ach['DEPOT_MPO_CODE'].nunique()}")
    
    return df_ach

def pivot_achievement_by_month(df_ach):
    """
    Create pivot table: DEPOT_MPO_CODE x Month with ACTUAL_SALE_QTY.
    """
    print("\n" + "=" * 80)
    print("STEP 5: PIVOTING ACHIEVEMENT BY MONTH")
    print("=" * 80)
    
    # Aggregate by DEPOT_MPO_CODE, Product, and Month
    df_agg = df_ach.groupby(['DEPOT_MPO_CODE', 'Product_Code', 'Product_Name', 'Month'])['ACTUAL_SALE_QTY'].sum().reset_index()
    
    print(f"Aggregated records: {len(df_agg)}")
    print(f"Unique months: {df_agg['Month'].unique()}")
    
    # Filter only April data (2026-04)
    df_april = df_agg[df_agg['Month'] == '2026-04'].copy()
    
    print(f"April records: {len(df_april)}")
    
    return df_april

# ============================================================================
# STEP 6: MERGE TARGETS WITH ACHIEVEMENTS
# ============================================================================

def merge_targets_with_achievements(df_target, df_achievement, product_cols):
    """
    Merge target data with April achievements.
    """
    print("\n" + "=" * 80)
    print("STEP 6: MERGING TARGETS WITH ACHIEVEMENTS")
    print("=" * 80)
    
    # Create DEPOT_MPO_CODE in target data (convert to string first)
    df_target['Depot'] = df_target['Depot'].astype(str)
    df_target['MPO_Code'] = df_target['MPO_Code'].astype(str)
    df_target['DEPOT_MPO_CODE'] = df_target['Depot'] + '_' + df_target['MPO_Code']
    
    # Pivot achievement data by product
    df_ach_pivot = df_achievement.pivot_table(
        index='DEPOT_MPO_CODE',
        columns='Product_Code',
        values='ACTUAL_SALE_QTY',
        aggfunc='sum',
        fill_value=0
    ).reset_index()
    
    print(f"Achievement pivot shape: {df_ach_pivot.shape}")
    
    # Merge
    df_final = df_target.merge(
        df_ach_pivot,
        on='DEPOT_MPO_CODE',
        how='left',
        suffixes=('_Target', '_Achievement')
    )
    
    print(f"Final merged records: {len(df_final)}")
    
    return df_final

# ============================================================================
# STEP 7: CREATE FINAL OUTPUT
# ============================================================================

def create_final_output(df_final, product_cols):
    """
    Create final Excel output with targets and achievements side by side.
    """
    print("\n" + "=" * 80)
    print("STEP 7: CREATING FINAL OUTPUT")
    print("=" * 80)
    
    # Calculate totals
    total_target = 0
    total_achievement = 0
    
    for col in product_cols:
        if col + '_Target' in df_final.columns:
            total_target += df_final[col + '_Target'].sum()
        if col + '_Achievement' in df_final.columns:
            total_achievement += df_final[col + '_Achievement'].sum()
    
    print(f"Total Target: {total_target:,.0f}")
    print(f"Total Achievement: {total_achievement:,.0f}")
    
    # Create output filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"Market_Target_Achievement_Detailed_{timestamp}.xlsx"
    
    # Write to Excel
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Sheet 1: Full data
        df_final.to_excel(writer, sheet_name='Full_Data', index=False)
        
        # Sheet 2: Summary by market
        summary_cols = ['Zone', 'Depot', 'Market', 'MPO_Code', 'Designation']
        summary_df = df_final[summary_cols].copy()
        
        # Add total target and achievement
        summary_df['Total_Target'] = df_final[[col for col in df_final.columns if '_Target' in col]].sum(axis=1)
        summary_df['Total_Achievement'] = df_final[[col for col in df_final.columns if '_Achievement' in col]].sum(axis=1)
        summary_df['Achievement_Pct'] = (summary_df['Total_Achievement'] / summary_df['Total_Target'] * 100).round(2)
        summary_df['Variance'] = summary_df['Total_Achievement'] - summary_df['Total_Target']
        
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    print(f"\n✓ Output saved: {output_file}")
    
    return output_file

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """
    Main execution function.
    """
    print("\n" + "=" * 80)
    print("MARKET TARGET VS ACHIEVEMENT - DETAILED ANALYSIS")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        # Step 1: Extract target data
        df_target = extract_target_data()
        
        # Step 2: Process product targets
        df_target_processed, product_cols = process_product_targets(df_target)
        
        # Step 3: Merge with MPO reference
        df_target_with_mpo = merge_with_mpo_reference(df_target_processed)
        
        # Step 4: Load achievement data
        df_achievement = load_achievement_data()
        
        # Step 5: Pivot achievement by month (April only)
        df_april_achievement = pivot_achievement_by_month(df_achievement)
        
        # Step 6: Merge targets with achievements
        df_final = merge_targets_with_achievements(df_target_with_mpo, df_april_achievement, product_cols)
        
        # Step 7: Create final output
        output_file = create_final_output(df_final, product_cols)
        
        print("\n" + "=" * 80)
        print("ANALYSIS COMPLETE")
        print("=" * 80)
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Output file: {output_file}")
        
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
