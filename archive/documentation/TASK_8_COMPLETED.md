# TASK 8: ADD PRODUCT CODES AND VLOOKUP FORMULAS - COMPLETED

## Date: 2026-05-23

## Objective
Create a Target vs Achievement report with alternating columns for each product:
- Column 1: Product TARGET
- Column 2: Product ACHIEVEMENT (ACH.)

## Files Created

### 1. MPO_Target_vs_Achievement_20260523_122119.xlsx
**Description**: Final report with VLOOKUP formulas
**Sheet**: Target_vs_Achievement

**Structure**:
- **Row 1**: Column headers (DEPOT, ZONE, FM/AM ZONE, MARKET, MPO CODE, DEPOT_MPO_CODE, product names)
- **Row 2**: Product codes (empty for TARGET columns, product codes for ACH columns)
  - Example: H2 = "MON1", J2 = "ALK1", L2 = "ALN1"
- **Row 3**: Column labels ("TARGET" or "ACH.")
- **Row 4+**: MPO data with targets and VLOOKUP formulas for achievements

**VLOOKUP Formula**:
```excel
=IFERROR(VLOOKUP($F4&H$2,[Achievement_Pivot_20260523_104633.xlsx]April_Achievement!$A:$G,7,FALSE),0)
```

**Formula Explanation**:
- `$F4`: DEPOT_MPO_CODE (e.g., "CUMILLA_CM03")
- `H$2`: Product Code (e.g., "MON1")
- Concatenates them to create lookup key: "CUMILLA_CM03_MON1"
- Looks up in Achievement_Pivot file, column A:G, returns column 7 (April_Achievement)
- Returns 0 if not found

### 2. MPO_Target_vs_Achievement_Values_20260523_122119.xlsx
**Description**: Same structure but with calculated values instead of formulas
**Sheet**: Target_vs_Achievement

## Column Structure

### Base Columns (A-F):
1. DEPOT
2. ZONE
3. FM/AM, ZONE
4. MARKET
5. MPO CODE
6. DEPOT_MPO_CODE

### Product Columns (G onwards) - Alternating Pattern:
For each of the 17 matched products:
- Column N: Product Name (TARGET)
- Column N+1: Product Name_ACH (ACHIEVEMENT)

**Example**:
- G: Mokast-10 Tab. (TARGET)
- H: Mokast-10 Tab._ACH (ACHIEVEMENT with VLOOKUP)
- I: Alagra 120 Tab. (TARGET)
- J: Alagra 120 Tab._ACH (ACHIEVEMENT with VLOOKUP)
- K: Alagra 180 Tab. (TARGET)
- L: Alagra 180 Tab._ACH (ACHIEVEMENT with VLOOKUP)
- ... and so on for all 17 products

## Product Matching Results

**Total Products in Target File**: 35
**Products Matched to Achievement**: 17 (48.6%)

**Matched Products**:
1. Mokast-10 Tab. → MON1
2. Alagra 120 Tab. → ALK1
3. Alagra 180 Tab. → ALN1
4. Aclo-100mg Tab. → AC01
5. Amdin Plus Tab. → amk3
6. Diaprid Tab. → dip4
7. Dompi Tab. → DOT1
8. Esopra-20 Tab. → ESF1
9. Calmi-D 30 Tab. → CAJ1
10. Tixol Tab. → TIS1
11. Tolec Tab. → TOL2
12. Omepra-20 Cap. → OMP1
13. Saver 200 Cap. → SAJ1
14. Dumoflox 500 Tab. → DUJ1
15. Zinex 500 Tab. → ZIJ1
16. Derma 50 Cap. → DEJ1
17. Derma 150 Cap. → DEM1

**Unmatched Products**: 18 products (mostly duplicates with "_Group2" suffix)

## Data Summary

- **Total MPO Records**: 458
- **Total Rows in Output**: 460 (2 header rows + 458 data rows)
- **Total Columns**: 40 (6 base + 34 product columns)
- **Achievement Source**: Achievement_Pivot_20260523_104633.xlsx (12,614 records)

## Scripts Used

### Main Script: create_target_vs_ach_alternating.py
**Purpose**: Creates the alternating TARGET/ACH column structure with VLOOKUP formulas

**Key Features**:
1. Loads target and achievement files
2. Matches product names using fuzzy matching (75% threshold)
3. Creates alternating column structure
4. Adds product codes row for VLOOKUP reference
5. Inserts VLOOKUP formulas in ACH columns
6. Creates both formula and values versions

### Verification Scripts:
- verify_alternating.py: Checks structure and formulas
- check_columns.py: Verifies column order and cell values

## How to Use the Output File

1. **Open in Excel**: MPO_Target_vs_Achievement_20260523_122119.xlsx
2. **Formulas will calculate automatically** when the Achievement_Pivot file is in the same directory
3. **Each MPO row shows**:
   - Target for each product
   - Achievement for each product (via VLOOKUP)
4. **Add calculations** as needed (e.g., Achievement %, Variance, etc.)

## Notes

- Only products with matching codes in the Achievement file have VLOOKUP formulas
- Unmatched products show 0 in ACH columns
- IFERROR wrapper ensures formulas return 0 if lookup fails
- Product codes are case-insensitive in the lookup

## Next Steps (if needed)

1. Add calculated columns for Achievement % (ACH / TARGET * 100)
2. Add variance columns (ACH - TARGET)
3. Add conditional formatting for visual analysis
4. Create pivot tables for summary views
5. Add charts for visualization

---

**Status**: ✓ COMPLETED
**Date**: 2026-05-23 12:21:24
