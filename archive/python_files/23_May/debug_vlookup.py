import pandas as pd

# Load both files
df_target = pd.read_excel('MPO_Field_With_Targets_20260523_102519.xlsx', sheet_name='MPO_Field_Targets')
df_achievement = pd.read_excel('Achievement_Pivot_20260523_104633.xlsx', sheet_name='April_Achievement')

print("=" * 80)
print("VLOOKUP DEBUG")
print("=" * 80)

# Check a specific example: CUMILLA_CM03 with MON1
test_depot_mpo = "CUMILLA_CM03"
test_product_code = "MON1"
test_key = f"{test_depot_mpo}_{test_product_code}"

print(f"\nTest lookup key: {test_key}")

# Check if this key exists in achievement file
matching_rows = df_achievement[df_achievement['DepotMPO_CodeProduct_Code'] == test_key]

if len(matching_rows) > 0:
    print(f"✓ Found in Achievement file!")
    print(f"  April_Achievement value: {matching_rows.iloc[0]['April_Achievement']}")
else:
    print(f"✗ NOT found in Achievement file")
    
    # Try case-insensitive search
    matching_rows_upper = df_achievement[df_achievement['DepotMPO_CodeProduct_Code'].str.upper() == test_key.upper()]
    if len(matching_rows_upper) > 0:
        print(f"  But found with case-insensitive match:")
        print(f"    Actual key: {matching_rows_upper.iloc[0]['DepotMPO_CodeProduct_Code']}")
        print(f"    April_Achievement: {matching_rows_upper.iloc[0]['April_Achievement']}")

# Check what keys exist for CUMILLA_CM03
print(f"\n\nAll keys for CUMILLA_CM03:")
cumilla_keys = df_achievement[df_achievement['DepotMPO_CodeProduct_Code'].str.startswith('CUMILLA_CM03')]
if len(cumilla_keys) > 0:
    print(f"  Found {len(cumilla_keys)} keys:")
    for idx, row in cumilla_keys.head(10).iterrows():
        print(f"    {row['DepotMPO_CodeProduct_Code']} → {row['April_Achievement']}")
else:
    print("  No keys found starting with CUMILLA_CM03")

# Check what DEPOT_MPO_CODE values exist in target file
print(f"\n\nDEPOT_MPO_CODE values in target file (first 10):")
target_codes = df_target['DEPOT_MPO_CODE'].dropna().unique()[:10]
for code in target_codes:
    print(f"  {code}")

# Check what DepotMPO_Code values exist in achievement file (without product code)
print(f"\n\nDepotMPO_Code values in achievement file (first 10):")
ach_depot_codes = df_achievement['DepotMPO_Code'].dropna().unique()[:10]
for code in ach_depot_codes:
    print(f"  {code}")

# Check if there's a mismatch
print(f"\n\nChecking for exact match:")
if test_depot_mpo in df_target['DEPOT_MPO_CODE'].values:
    print(f"  ✓ {test_depot_mpo} exists in target file")
else:
    print(f"  ✗ {test_depot_mpo} NOT in target file")

if test_depot_mpo in df_achievement['DepotMPO_Code'].values:
    print(f"  ✓ {test_depot_mpo} exists in achievement file")
else:
    print(f"  ✗ {test_depot_mpo} NOT in achievement file")

# Check product codes
print(f"\n\nProduct codes in achievement file:")
product_codes = df_achievement['Product_Code'].dropna().unique()
print(f"  Total unique: {len(product_codes)}")
print(f"  Sample: {list(product_codes[:10])}")

if test_product_code in product_codes:
    print(f"  ✓ {test_product_code} exists")
else:
    print(f"  ✗ {test_product_code} NOT found")
    # Check case-insensitive
    product_codes_upper = [str(p).upper() for p in product_codes]
    if test_product_code.upper() in product_codes_upper:
        actual_code = product_codes[product_codes_upper.index(test_product_code.upper())]
        print(f"    But found with different case: {actual_code}")
