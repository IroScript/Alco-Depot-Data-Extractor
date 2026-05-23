================================================================================
COMPLETE WORKFLOW - ALL STEPS (2026-05-23)
================================================================================

GOAL: Create Target vs Achievement Report for all MPOs and Products

--------------------------------------------------------------------------------
PYTHON SCRIPTS (7 files) - IN ORDER OF EXECUTION
--------------------------------------------------------------------------------

STEP 1: Extract Targets from Excel
  Script: extract_with_product_names.py
  Input: Unit Target of April-2026 (2).xlsx
  Output: Target_Data_With_Products.xlsx
  What it does: Reads product names from row 3, filters valid designations,
                extracts zones and market-wise targets

STEP 2: Merge Targets with MPO Reference
  Script: merge_targets_to_mpo_field.py
  Input: MPO_CODE_AND_FIELD.xlsx + Target_Data_With_Products.xlsx
  Output: MPO_Field_With_Targets.xlsx
  What it does: Uses fuzzy matching for market names, adds DEPOT_MPO_CODE,
                pulls all 35 product columns

STEP 3: Process Sales Data from All Depots
  Script: process_all_depots.py (extracts from 9 depot SQL databases)
  OR: process_product_level_FAST.py (processes product-level sales)
  Input: All_Depots/[9 depots]/Data/ERPonTheNet_Data.MDF
  Output: Product_Level_Net_Sales.csv
  What it does: Calculates product-level net sales (Sales - Returns),
                creates concatenated key for matching

STEP 4: Create Achievement Pivot
  Script: create_achievement_pivot.py
  Input: Product_Level_Net_Sales.csv
  Output: Achievement_Pivot.xlsx
  What it does: Adds DepotMPO_CodeProduct_Code concatenation,
                creates pivot table with months as columns

STEP 5: Fix Case Sensitivity Issue
  Script: fix_achievement_pivot_case.py
  Input: Achievement_Pivot.xlsx
  Output: Achievement_Pivot_Fixed.xlsx
  What it does: Adds LOOKUP_KEY_UPPER column for case-insensitive matching
                (Target: CUMILLA, Achievement: Cumilla)

STEP 6: Create Final Target vs Achievement Report
  Script: create_target_vs_ach_alternating.py
  Input: MPO_Field_With_Targets.xlsx + Achievement_Pivot_Fixed.xlsx
  Output: MPO_Target_vs_Achievement.xlsx ⭐ FINAL OUTPUT
  What it does: Creates alternating TARGET/ACH columns, adds product codes,
                inserts VLOOKUP formulas to pull achievements

--------------------------------------------------------------------------------
EXCEL FILES (8 files)
--------------------------------------------------------------------------------

SOURCE FILES (you provided):
  1. Unit Target of April-2026 (2).xlsx - Market-wise product targets
  2. MPO_CODE_AND_FIELD.xlsx - MPO codes and market reference

INTERMEDIATE FILES (created by workflow):
  3. Product_Level_Net_Sales_20260522_232817.csv - Product-level sales data
     (160,353 records, Net Sales: 129,135,241.40 BDT)
  
  4. MPO_Field_With_Targets_20260523_102519.xlsx - MPO targets merged
     (458 MPO records with 35 product columns)
  
  5. Achievement_Pivot_20260523_104633.xlsx - Achievement pivot table
     (12,614 rows, April achievement: 112,685 units)
  
  6. Achievement_Pivot_Fixed_20260523_124434.xlsx - Fixed with uppercase keys
     (Required for VLOOKUP to work)

FINAL OUTPUT FILES:
  7. MPO_Target_vs_Achievement_20260523_124531.xlsx ⭐ MAIN OUTPUT
     (With VLOOKUP formulas)
  
  8. MPO_Target_vs_Achievement_Values_20260523_124531.xlsx ⭐ MAIN OUTPUT
     (With calculated values)

--------------------------------------------------------------------------------
FINAL OUTPUT FILE STRUCTURE
--------------------------------------------------------------------------------

File: MPO_Target_vs_Achievement_20260523_124531.xlsx

Row 1: Column headers
Row 2: Product codes (for ACH columns only)
Row 3: "TARGET" and "ACH." labels
Row 4+: 458 MPO records

Columns:
  A-F: Base info (DEPOT, ZONE, FM/AM, MARKET, MPO CODE, DEPOT_MPO_CODE)
  G: Mokast-10 TARGET
  H: Mokast-10 ACH (VLOOKUP formula)
  I: Alagra 120 TARGET
  J: Alagra 120 ACH (VLOOKUP formula)
  ... and so on for 17 products

VLOOKUP Formula:
=IFERROR(VLOOKUP(UPPER($F4&"_"&H$2),[Achievement_Pivot_Fixed_20260523_124434.xlsx]April_Achievement!$A:$H,8,FALSE),0)

--------------------------------------------------------------------------------
RESULTS
--------------------------------------------------------------------------------

Total Achievements: 64,716 units
Non-zero cells: 2,952
Products matched: 17 out of 35

Top Products:
  - Derma 50 Cap: 12,749 units
  - Mokast-10 Tab: 9,014 units
  - Alagra 120 Tab: 7,432 units
  - Derma 150 Cap: 7,281 units
  - Amdin Plus Tab: 5,929 units

--------------------------------------------------------------------------------
ARCHIVE FOLDER
--------------------------------------------------------------------------------

All old/test files moved to:
  - archive/python_files/ (old scripts)
  - archive/excel_files/ (old Excel files)
  - archive/documentation/ (documentation files)

================================================================================
