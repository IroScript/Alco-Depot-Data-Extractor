import pandas as pd

df = pd.read_excel('MPO_Target_vs_Achievement_Values_20260523_124531.xlsx')

print("=" * 80)
print("FINAL ACHIEVEMENT VERIFICATION")
print("=" * 80)

# Check first few data rows (skip header rows 0 and 1)
print("\nFirst 5 MPO rows:")
for idx in range(2, 7):
    row = df.iloc[idx]
    print(f"\n{row['DEPOT_MPO_CODE']}:")
    print(f"  Mokast-10 TARGET: {row['Mokast-10 Tab.']}")
    print(f"  Mokast-10 ACH: {row['Mokast-10 Tab._ACH']}")
    print(f"  Alagra 120 TARGET: {row['Alagra  120 Tab.']}")
    print(f"  Alagra 120 ACH: {row['Alagra  120 Tab._ACH']}")

# Count non-zero achievements
print("\n\nNon-zero achievement counts:")
ach_cols = [col for col in df.columns if '_ACH' in col]
total_non_zero = 0
for col in ach_cols:
    # Skip header rows
    non_zero = (df[col].iloc[2:] != 0).sum()
    total_non_zero += non_zero
    if non_zero > 0:
        print(f"  {col}: {non_zero} non-zero")

print(f"\nTotal non-zero achievement cells: {total_non_zero}")

# Calculate total achievements
print("\n\nTotal achievements by product:")
for col in ach_cols:
    total = df[col].iloc[2:].sum()
    if total > 0:
        print(f"  {col}: {total:.0f}")
