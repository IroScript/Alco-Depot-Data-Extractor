# Quick check to verify Month column exists in the report

import pandas as pd

# Read the latest report
report_file = "All_Depots_MPO_Report_20260521_220658.xlsx"

print("=" * 70)
print(f"Checking Report: {report_file}")
print("=" * 70)

# Read first sheet
df = pd.read_excel(report_file, sheet_name='All Data', nrows=10)

print("\nColumns in report:")
for i, col in enumerate(df.columns, 1):
    print(f"  {i}. {col}")

print("\nSample data (first 5 rows):")
print(df[['Depot', 'MPO_Code', 'Invoice_Date', 'Month', 'Line_Amount']].head())

print("\n" + "=" * 70)
print("✓ Month column successfully added!")
print("=" * 70)
