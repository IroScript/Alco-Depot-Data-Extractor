import pandas as pd

# Load the values file
df = pd.read_excel('MPO_Target_vs_Achievement_Values_20260523_122936.xlsx', sheet_name='Target_vs_Achievement')

print("=" * 80)
print("ACHIEVEMENT DATA VERIFICATION")
print("=" * 80)

print("\nSample data (first 5 MPO rows):")
print(df.iloc[2:7, [5, 6, 7, 8, 9]].to_string())

print("\n\nChecking for non-zero achievements:")
ach_cols = [col for col in df.columns if '_ACH' in col]
print(f"Total ACH columns: {len(ach_cols)}")

total_ach = 0
non_zero_count = 0
for col in ach_cols:
    col_sum = df[col].sum()
    total_ach += col_sum
    non_zero = (df[col] > 0).sum()
    non_zero_count += non_zero
    if col_sum > 0:
        print(f"  {col}: {col_sum:.0f} (non-zero rows: {non_zero})")

print(f"\nTotal achievements across all ACH columns: {total_ach:.0f}")
print(f"Total non-zero achievement cells: {non_zero_count}")

# Check a specific example
print("\n\nSpecific example - CUMILLA_CM03:")
cumilla_rows = df[df['DEPOT_MPO_CODE'] == 'CUMILLA_CM03']
if len(cumilla_rows) > 0:
    print(f"Found {len(cumilla_rows)} row(s)")
    for idx, row in cumilla_rows.iterrows():
        print(f"\nRow {idx}:")
        print(f"  DEPOT: {row['DEPOT']}")
        print(f"  MARKET: {row['MARKET']}")
        print(f"  MPO CODE: {row['MPO CODE']}")
        print(f"  Mokast-10 TARGET: {row['Mokast-10 Tab.']}")
        print(f"  Mokast-10 ACH: {row['Mokast-10 Tab._ACH']}")
        print(f"  Alagra 120 TARGET: {row['Alagra  120 Tab.']}")
        print(f"  Alagra 120 ACH: {row['Alagra  120 Tab._ACH']}")
