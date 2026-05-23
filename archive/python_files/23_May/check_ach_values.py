import pandas as pd

df = pd.read_excel('MPO_Target_vs_Achievement_Values_20260523_123154.xlsx')

# Find Barishal_B001
row = df[df['DEPOT_MPO_CODE'] == 'Barishal_B001']

if len(row) > 0:
    row = row.iloc[0]
    print("Barishal_B001:")
    print(f"  Mokast-10 TARGET: {row['Mokast-10 Tab.']}")
    print(f"  Mokast-10 ACH: {row['Mokast-10 Tab._ACH']}")
    print(f"  Alagra 120 TARGET: {row['Alagra  120 Tab.']}")
    print(f"  Alagra 120 ACH: {row['Alagra  120 Tab._ACH']}")
else:
    print("Barishal_B001 not found")

# Check if any achievements are non-zero
print("\nChecking all ACH columns for non-zero values:")
ach_cols = [col for col in df.columns if '_ACH' in col]
for col in ach_cols[:5]:  # Check first 5
    non_zero = df[col][df[col] != 0].count()
    if non_zero > 0:
        print(f"  {col}: {non_zero} non-zero values")
