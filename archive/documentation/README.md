# Barishal April Data - Active Files

## Overview
This directory contains scripts and data files for processing MPO-wise sales data, targets, and achievements across 9 depots in Bangladesh.

**Last Updated**: 2026-05-23

---

## 📁 Directory Structure

```
Barishal April Data/
├── archive/
│   ├── python_files/     # Old/test Python scripts
│   └── excel_files/      # Old/intermediate Excel files
├── All_Depots/           # SQL Server database files for 9 depots
├── Data/                 # Main database files
└── [Active files listed below]
```

---

## 🐍 Active Python Scripts

### 1. **extract_with_product_names.py**
**Purpose**: Extract target data from Unit Target Excel file
- Reads product names from row 3 (I3:AQ3)
- Filters valid designations (MPO, SMPO, MR, etc.)
- Extracts zones and market-wise targets
- **Output**: Target_Data_With_Products_[timestamp].xlsx

### 2. **merge_targets_to_mpo_field.py**
**Purpose**: Merge target data into MPO reference file
- Loads MPO_CODE_AND_FIELD.xlsx as base
- Uses fuzzy matching for market names
- Adds DEPOT_MPO_CODE concatenation
- Pulls all 35 product columns from target file
- **Output**: MPO_Field_With_Targets_[timestamp].xlsx

### 3. **process_product_level_FAST.py**
**Purpose**: Calculate product-level net sales (Sales - Returns)
- Processes all 9 depots
- Creates concatenated key: Depot_MPO_CustomerID_Month_ProductCode
- Matches returns to sales at most granular level
- **Output**: Product_Level_Net_Sales_[timestamp].csv

### 4. **create_achievement_pivot.py**
**Purpose**: Create pivot table of achievements
- Adds DepotMPO_CodeProduct_Code concatenation
- Creates pivot: Rows=Product details, Columns=Months, Values=Qty
- **Output**: Achievement_Pivot_[timestamp].xlsx

### 5. **fix_achievement_pivot_case.py**
**Purpose**: Fix case sensitivity issues in achievement file
- Adds LOOKUP_KEY_UPPER column for case-insensitive matching
- Target file has uppercase DEPOT names (CUMILLA)
- Achievement file has mixed case (Cumilla)
- **Output**: Achievement_Pivot_Fixed_[timestamp].xlsx

### 6. **create_target_vs_ach_alternating.py** ⭐ **MAIN SCRIPT**
**Purpose**: Create final Target vs Achievement report
- Alternating columns: TARGET, ACH, TARGET, ACH...
- Adds product codes row for VLOOKUP reference
- Inserts VLOOKUP formulas in ACH columns
- Creates both formula and values versions
- **Output**: 
  - MPO_Target_vs_Achievement_[timestamp].xlsx (with formulas)
  - MPO_Target_vs_Achievement_Values_[timestamp].xlsx (with values)

### 7. **cleanup_and_archive.py**
**Purpose**: Organize files and clean up workspace
- Moves old Python scripts to archive/python_files/
- Moves old Excel files to archive/excel_files/
- Keeps only active/final files in root

---

## 📊 Active Excel Files

### Source Files
1. **Unit Target of April-2026 (2).xlsx**
   - Source: User provided
   - Contains: Market-wise product targets for April 2026
   - Products: 35 columns (17 unique × 2 groups)

2. **MPO_CODE_AND_FIELD.xlsx**
   - Source: User provided
   - Contains: MPO codes and market reference data
   - Used for: Matching markets and MPO codes

### Intermediate Files
3. **Product_Level_Net_Sales_20260522_232817.csv**
   - Contains: 160,353 product-level sales records
   - Net Sales: 129,135,241.40 BDT
   - Columns: Depot, MPO_Code, Customer_ID, Product_Code, Product_Name, SALE_QTY, RETURN_QTY, ACTUAL_SALE_QTY, Month

4. **Achievement_Pivot_20260523_104633.xlsx**
   - Contains: 12,614 rows of achievement data
   - Pivot structure: Product details × Months
   - April achievement: 112,685 units

5. **Achievement_Pivot_Fixed_20260523_124434.xlsx** ⭐
   - Fixed version with uppercase lookup keys
   - Added LOOKUP_KEY_UPPER column for case-insensitive matching
   - **Required for VLOOKUP formulas to work**

6. **MPO_Field_With_Targets_20260523_102519.xlsx**
   - Contains: 458 MPO records with targets
   - Columns: DEPOT, ZONE, FM/AM, MARKET, MPO CODE, DEPOT_MPO_CODE + 35 product columns
   - Total target: 134,439 units

### Final Output Files ⭐
7. **MPO_Target_vs_Achievement_20260523_124531.xlsx**
   - **MAIN OUTPUT FILE** with VLOOKUP formulas
   - Structure: Alternating TARGET and ACH columns for each product
   - Row 1: Column headers
   - Row 2: Product codes (for ACH columns)
   - Row 3: "TARGET" and "ACH." labels
   - Row 4+: 458 MPO records with targets and achievements
   - **VLOOKUP Formula**: `=IFERROR(VLOOKUP(UPPER($F4&"_"&H$2),[Achievement_Pivot_Fixed_20260523_124434.xlsx]April_Achievement!$A:$H,8,FALSE),0)`

8. **MPO_Target_vs_Achievement_Values_20260523_124531.xlsx**
   - Same structure as above but with calculated values instead of formulas
   - Total achievements: 64,716 units across all products
   - Non-zero achievement cells: 2,952

---

## 🔄 Workflow

```
1. Extract Targets
   └─> extract_with_product_names.py
       └─> Target_Data_With_Products.xlsx

2. Merge with MPO Reference
   └─> merge_targets_to_mpo_field.py
       └─> MPO_Field_With_Targets.xlsx

3. Process Sales Data (from 9 depots)
   └─> process_product_level_FAST.py
       └─> Product_Level_Net_Sales.csv

4. Create Achievement Pivot
   └─> create_achievement_pivot.py
       └─> Achievement_Pivot.xlsx

5. Fix Case Sensitivity
   └─> fix_achievement_pivot_case.py
       └─> Achievement_Pivot_Fixed.xlsx

6. Create Final Report ⭐
   └─> create_target_vs_ach_alternating.py
       └─> MPO_Target_vs_Achievement.xlsx (FINAL)
```

---

## 📈 Key Metrics

### Sales Data (April 2026)
- **Gross Sales**: 132,641,811.42 BDT
- **Returns**: 4,059,706.33 BDT
- **Net Sales**: 128,582,105.09 BDT
- **Return Rate**: 3.06%

### Targets vs Achievements
- **Total Target**: 134,439 units
- **Total Achievement**: 64,716 units
- **Achievement Rate**: 48.1%
- **Products Tracked**: 17 (matched from 35 in target file)

### Top Performing Products (by achievement)
1. Derma 50 Cap: 12,749 units
2. Mokast-10 Tab: 9,014 units
3. Alagra 120 Tab: 7,432 units
4. Derma 150 Cap: 7,281 units
5. Amdin Plus Tab: 5,929 units

---

## 🔧 Technical Notes

### Case Sensitivity Issue
- **Problem**: Target file has uppercase DEPOT names (CUMILLA), Achievement file has mixed case (Cumilla)
- **Solution**: Created Achievement_Pivot_Fixed with LOOKUP_KEY_UPPER column
- **VLOOKUP**: Uses UPPER() function to ensure case-insensitive matching

### Product Matching
- Uses fuzzy matching with 75% threshold
- Normalizes product names (removes spaces, hyphens, Tab/Cap suffixes)
- Core product name is key: "MOKAST10" matches "Mokast-10 Tab.", "MOKAST-10 TAB(NEW)", etc.

### Concatenated Keys
- Format: `DEPOT_MPO_CODE_PRODUCTCODE`
- Example: `CUMILLA_CM03_MON1`
- Used for: Matching achievements to targets at product level

---

## 📝 Important Files to Keep

**Never delete these files:**
1. Achievement_Pivot_Fixed_20260523_124434.xlsx (required for VLOOKUP)
2. MPO_Target_vs_Achievement_20260523_124531.xlsx (final output)
3. Unit Target of April-2026 (2).xlsx (source data)
4. MPO_CODE_AND_FIELD.xlsx (reference data)

---

## 🗂️ Archive

Old/intermediate files are stored in:
- `archive/python_files/` - Test scripts and old versions
- `archive/excel_files/` - Intermediate Excel files and old versions

---

**For questions or issues, refer to TASK_8_COMPLETED.md for detailed documentation.**
