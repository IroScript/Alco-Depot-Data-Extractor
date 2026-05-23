"""
Market-Wise Target vs Achievement Analysis
==========================================
This script matches market-wise unit targets with actual unit achievements.

Key Features:
- Reads target data from Unit Target Excel file (handles multi-row headers)
- Filters only actual markets (MPO/SMPO/MR/Self designations)
- Handles fuzzy market name matching (150+ different spellings)
- Uses existing extracted data (CSV from process_product_level_FAST.py)
- Produces market-wise comparison report

Author: Auto-generated
Date: 2026-05-22
"""

import pandas as pd
import os
from datetime import datetime
from difflib import SequenceMatcher
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

# File paths
TARGET_FILE = r"C:\Users\Irak\Desktop\Barishal April Data\Unit Target of April-2026 (2).xlsx"
MPO_REFERENCE_FILE = r"C:\Users\Irak\Desktop\Barishal April Data\MPO_CODE_AND_FIELD.xlsx"

# Valid designations for actual markets (not team leaders)
VALID_DESIGNATIONS = [
    'AFM(MMO)', 'AM(AFM)', 'AM(Self)', 'DAFM(MPO)', 'FM(Self)',
    'MMO', 'MPO', 'MR', 'Self', 'SMMO', 'SMPO',
    'Sr.DA', 'Sr.FM(Self)', 'Sr.RSM(Self)'
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def normalize_market_name(market_name):
    """
    Normalize market name for better matching.
    Removes extra spaces, converts to uppercase, removes special characters.
    """
    if pd.isna(market_name):
        return ""
    
    # Convert to string and uppercase
    name = str(market_name).upper().strip()
    
    # Remove extra spaces
    name = ' '.join(name.split())
    
    # Remove common punctuation variations
    name = name.replace(',', '').replace('.', '').replace('-', ' ')
    name = name.replace('(', '').replace(')', '')
    
    # Remove extra spaces again after replacements
    name = ' '.join(name.split())
    
    return name

def fuzzy_match_score(str1, str2):
    """
    Calculate similarity score between two strings (0-1).
    Uses SequenceMatcher for fuzzy matching.
    """
    return SequenceMatcher(None, str1, str2).ratio()

def find_best_market_match(target_market, achievement_markets, threshold=0.80):
    """
    Find the best matching market from achievement list.
    Returns the best match if similarity > threshold, else None.
    """
    target_norm = normalize_market_name(target_market)
    
    if not target_norm:
        return None
    
    best_match = None
    best_score = 0
    
    for ach_market in achievement_markets:
        ach_norm = normalize_market_name(ach_market)
        score = fuzzy_match_score(target_norm, ach_norm)
        
        if score > best_score:
            best_score = score
            best_match = ach_market
    
    # Return best match if score is above threshold
    if best_score >= threshold:
        return best_match
    else:
        return None

# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================

def load_target_data():
    """
    Load target data from Excel file with multi-row headers.
    Returns DataFrame with Market and product-wise targets.
    """
    print("Loading target data...")
    
    # Read Excel file - first read to get product names from row 0
    df_products = pd.read_excel(TARGET_FILE, header=0, nrows=1)
    product_names = df_products.iloc[0].tolist()
    
    # Read again with proper header
    df = pd.read_excel(TARGET_FILE, header=1)
    
    # Assign product names to columns
    for i, prod_name in enumerate(product_names):
        if i < len(df.columns) and not pd.isna(prod_name):
            df.columns.values[i] = str(prod_name)
    
    # Rename key columns
    df.columns.values[2] = 'Designation'
    df.columns.values[3] = 'Market'
    
    # Filter rows with valid designations
    df_filtered = df[df['Designation'].isin(VALID_DESIGNATIONS)].copy()
    
    # Remove rows where Market is NaN
    df_filtered = df_filtered[df_filtered['Market'].notna()].copy()
    
    # Remove zone header rows (rows where Market contains "Zone :")
    df_filtered = df_filtered[~df_filtered['Market'].astype(str).str.contains('Zone', case=False, na=False)]
    
    print(f"  - Total rows in target file: {len(df)}")
    print(f"  - Rows with valid designations: {len(df_filtered)}")
    print(f"  - Unique markets in target: {df_filtered['Market'].nunique()}")
    
    return df_filtered

def load_mpo_reference():
    """
    Load MPO reference data for market name mapping.
    Returns DataFrame with Depot, Market, and MPO Code.
    """
    print("Loading MPO reference data...")
    
    df = pd.read_excel(MPO_REFERENCE_FILE)
    
    print(f"  - Total MPO records: {len(df)}")
    print(f"  - Unique markets in reference: {df['MARKET'].nunique()}")
    
    return df

def load_achievement_data():
    """
    Load achievement data from existing CSV file.
    User should run process_product_level_FAST.py first to generate this file.
    """
    print("\nLoading achievement data from CSV...")
    
    # Find the most recent Product_Level_Net_Sales CSV file
    csv_files = [f for f in os.listdir('.') if f.startswith('Product_Level_Net_Sales_') and f.endswith('.csv')]
    
    if not csv_files:
        print("  ⚠ No Product_Level_Net_Sales CSV file found!")
        print("  Please run process_product_level_FAST.py first to generate achievement data.")
        return pd.DataFrame()
    
    # Sort by filename (timestamp) and get the latest
    csv_files.sort(reverse=True)
    latest_csv = csv_files[0]
    
    print(f"  - Using file: {latest_csv}")
    
    df = pd.read_csv(latest_csv)
    
    print(f"  - Total records: {len(df)}")
    
    return df

# ============================================================================
# PROCESSING FUNCTIONS
# ============================================================================

def map_mpo_to_market(achievement_df, mpo_reference_df):
    """
    Map MPO codes to markets using reference file.
    """
    print("\nMapping MPO codes to markets...")
    
    # Create MPO to Market mapping
    mpo_market_map = mpo_reference_df[['MPO CODE', 'MARKET']].drop_duplicates()
    mpo_market_map.rename(columns={'MPO CODE': 'MPO_Code', 'MARKET': 'Market'}, inplace=True)
    
    # Merge with achievement data
    achievement_with_market = achievement_df.merge(
        mpo_market_map,
        on='MPO_Code',
        how='left'
    )
    
    # Count unmapped MPOs
    unmapped = achievement_with_market['Market'].isna().sum()
    print(f"  - Mapped records: {len(achievement_with_market) - unmapped}")
    print(f"  - Unmapped records: {unmapped}")
    
    return achievement_with_market

def aggregate_market_wise(achievement_with_market):
    """
    Aggregate achievements at market level by product.
    """
    print("\nAggregating market-wise achievements...")
    
    # Remove unmapped records
    df_mapped = achievement_with_market[achievement_with_market['Market'].notna()].copy()
    
    # Use ACTUAL_SALE_QTY column from CSV
    market_product_agg = df_mapped.groupby(['Market', 'Product_Code', 'Product_Name'])['ACTUAL_SALE_QTY'].sum().reset_index()
    market_product_agg.rename(columns={'ACTUAL_SALE_QTY': 'Achievement_Qty'}, inplace=True)
    
    print(f"  - Unique market-product combinations: {len(market_product_agg)}")
    print(f"  - Unique markets: {market_product_agg['Market'].nunique()}")
    
    return market_product_agg

def aggregate_market_total(achievement_with_market):
    """
    Aggregate total achievements at market level (all products combined).
    """
    print("\nAggregating market-wise total achievements...")
    
    # Remove unmapped records
    df_mapped = achievement_with_market[achievement_with_market['Market'].notna()].copy()
    
    # Use ACTUAL_SALE_QTY column from CSV
    market_total_agg = df_mapped.groupby('Market')['ACTUAL_SALE_QTY'].sum().reset_index()
    market_total_agg.rename(columns={'ACTUAL_SALE_QTY': 'Total_Achievement_Qty'}, inplace=True)
    
    print(f"  - Unique markets: {len(market_total_agg)}")
    
    return market_total_agg

def extract_target_totals(target_df):
    """
    Extract total unit targets per market (sum across all products).
    """
    print("\nExtracting market-wise total targets...")
    
    # Get all columns after 'Market'
    market_col_idx = list(target_df.columns).index('Market')
    all_cols_after_market = target_df.columns[market_col_idx + 1:]
    
    # Filter only numeric columns (product targets)
    numeric_cols = []
    for col in all_cols_after_market:
        try:
            # Try to convert to numeric
            test_series = pd.to_numeric(target_df[col], errors='coerce')
            if test_series.notna().sum() > 0:  # Has at least some numeric values
                numeric_cols.append(col)
        except:
            pass
    
    print(f"  - Found {len(numeric_cols)} product columns with numeric data")
    
    # Convert columns to numeric
    for col in numeric_cols:
        target_df[col] = pd.to_numeric(target_df[col], errors='coerce').fillna(0)
    
    # Sum all product targets per market
    target_df['Total_Target_Qty'] = target_df[numeric_cols].sum(axis=1)
    
    # Create market-wise target summary
    market_targets = target_df[['Market', 'Designation', 'Total_Target_Qty']].copy()
    
    print(f"  - Total target quantity across all markets: {market_targets['Total_Target_Qty'].sum():,.2f}")
    
    return market_targets

def match_targets_with_achievements(target_df, achievement_df):
    """
    Match target markets with achievement markets using fuzzy matching.
    """
    print("\nMatching targets with achievements...")
    
    # Get unique markets from achievements
    achievement_markets = achievement_df['Market'].unique().tolist()
    
    # Create market mapping using fuzzy matching
    unique_target_markets = target_df['Market'].unique()
    market_mapping = {}
    
    print("  Performing fuzzy matching for market names...")
    match_count = 0
    no_match_count = 0
    
    for target_market in unique_target_markets:
        best_match = find_best_market_match(target_market, achievement_markets, threshold=0.80)
        
        if best_match:
            market_mapping[target_market] = best_match
            
            # Log if mapping is different
            if normalize_market_name(target_market) != normalize_market_name(best_match):
                match_count += 1
                if match_count <= 20:  # Show first 20 mappings
                    print(f"    Mapped: '{target_market}' → '{best_match}'")
        else:
            no_match_count += 1
            market_mapping[target_market] = target_market  # Keep original if no match
    
    if match_count > 20:
        print(f"    ... and {match_count - 20} more mappings")
    
    print(f"  - Successfully matched: {len(market_mapping) - no_match_count}")
    print(f"  - No match found: {no_match_count}")
    
    # Apply mapping to target data
    target_df['Market_Matched'] = target_df['Market'].map(market_mapping)
    
    return target_df

def create_comparison_report(market_targets, market_achievements):
    """
    Create final comparison report with targets and achievements.
    """
    print("\nCreating comparison report...")
    
    # Merge targets with achievements
    comparison = market_targets.merge(
        market_achievements,
        left_on='Market_Matched',
        right_on='Market',
        how='outer',
        suffixes=('_Target', '_Achievement')
    )
    
    # Fill NaN values
    comparison['Total_Target_Qty'] = comparison['Total_Target_Qty'].fillna(0)
    comparison['Total_Achievement_Qty'] = comparison['Total_Achievement_Qty'].fillna(0)
    
    # Calculate achievement percentage
    comparison['Achievement_Pct'] = 0.0
    mask = comparison['Total_Target_Qty'] > 0
    comparison.loc[mask, 'Achievement_Pct'] = (
        comparison.loc[mask, 'Total_Achievement_Qty'] / comparison.loc[mask, 'Total_Target_Qty'] * 100
    ).round(2)
    
    # Calculate variance
    comparison['Variance_Qty'] = comparison['Total_Achievement_Qty'] - comparison['Total_Target_Qty']
    
    # Clean up market column
    comparison['Market'] = comparison['Market_Target'].fillna(comparison['Market_Achievement'])
    
    # Select final columns
    final_columns = [
        'Market', 'Designation', 'Market_Matched',
        'Total_Target_Qty', 'Total_Achievement_Qty',
        'Variance_Qty', 'Achievement_Pct'
    ]
    
    comparison_final = comparison[final_columns].copy()
    
    # Sort by market name
    comparison_final = comparison_final.sort_values('Market')
    
    # Calculate statistics
    markets_with_both = ((comparison_final['Total_Target_Qty'] > 0) & (comparison_final['Total_Achievement_Qty'] > 0)).sum()
    markets_target_only = ((comparison_final['Total_Target_Qty'] > 0) & (comparison_final['Total_Achievement_Qty'] == 0)).sum()
    markets_achievement_only = ((comparison_final['Total_Target_Qty'] == 0) & (comparison_final['Total_Achievement_Qty'] > 0)).sum()
    
    print(f"  - Total markets in report: {len(comparison_final)}")
    print(f"  - Markets with both target & achievement: {markets_with_both}")
    print(f"  - Markets with targets only: {markets_target_only}")
    print(f"  - Markets with achievements only: {markets_achievement_only}")
    
    return comparison_final

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """
    Main execution function.
    """
    print("=" * 80)
    print("MARKET-WISE TARGET VS ACHIEVEMENT ANALYSIS")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Step 1: Load target data
    target_df = load_target_data()
    
    # Step 2: Load MPO reference
    mpo_reference_df = load_mpo_reference()
    
    # Step 3: Load achievement data from CSV
    achievement_df = load_achievement_data()
    
    if achievement_df.empty:
        print("\n⚠ No achievement data found. Exiting...")
        print("\nPlease run process_product_level_FAST.py first to generate achievement data.")
        return
    
    # Step 4: Map MPO to Market in achievement data
    achievement_with_market = map_mpo_to_market(achievement_df, mpo_reference_df)
    
    # Step 5: Aggregate market-wise achievements (by product)
    market_product_achievements = aggregate_market_wise(achievement_with_market)
    
    # Step 6: Aggregate market-wise total achievements
    market_total_achievements = aggregate_market_total(achievement_with_market)
    
    # Step 7: Extract market-wise total targets
    market_targets = extract_target_totals(target_df)
    
    # Step 8: Match targets with achievements using fuzzy matching
    market_targets_matched = match_targets_with_achievements(market_targets, market_total_achievements)
    
    # Step 9: Create comparison report
    comparison_report = create_comparison_report(market_targets_matched, market_total_achievements)
    
    # Step 10: Generate output report
    print("\nGenerating output report...")
    
    # Create output filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"Market_Wise_Target_vs_Achievement_{timestamp}.xlsx"
    
    # Create Excel writer
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Sheet 1: Summary Comparison
        comparison_report.to_excel(writer, sheet_name='Market_Summary', index=False)
        
        # Sheet 2: Product-Level Achievements
        market_product_achievements.to_excel(writer, sheet_name='Product_Level_Achievement', index=False)
        
        # Sheet 3: Full Target Data
        target_df.to_excel(writer, sheet_name='Full_Target_Data', index=False)
        
        # Sheet 4: Full Achievement Data
        achievement_with_market.to_excel(writer, sheet_name='Full_Achievement_Data', index=False)
    
    print(f"\n✓ Report saved: {output_file}")
    
    # Print summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    
    total_target = comparison_report['Total_Target_Qty'].sum()
    total_achievement = comparison_report['Total_Achievement_Qty'].sum()
    overall_pct = (total_achievement / total_target * 100) if total_target > 0 else 0
    
    print(f"Total Target Quantity: {total_target:,.2f}")
    print(f"Total Achievement Quantity: {total_achievement:,.2f}")
    print(f"Overall Achievement: {overall_pct:.2f}%")
    print(f"Variance: {total_achievement - total_target:,.2f}")
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
