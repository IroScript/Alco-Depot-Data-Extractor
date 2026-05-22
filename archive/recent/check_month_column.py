# Check if Month column exists and is at the end

import pandas as pd
import os

# Find latest report
reports = [f for f in os.listdir('.') if f.startswith('All_Depots_MPO_Report_') and f.endswith('.xlsx')]
if not reports:
    print("No reports found!")
    exit()

latest = max(reports, key=lambda x: os.path.getctime(x))

print("=" * 80)
print(f"Checking Report: {latest}")
print("=" * 80)

# Read the Excel file
df = pd.read_excel(latest, sheet_name='All Data', nrows=20)

print("\nColumn Order:")
for i, col in enumerate(df.columns, 1):
    print(f"  {i:2}. {col}")

print(f"\nTotal Columns: {len(df.columns)}")
print(f"Last Column: {df.columns[-1]}")

if 'Month' in df.columns:
    print("\n✓ Month column EXISTS")
    month_position = list(df.columns).index('Month') + 1
    print(f"  Position: {month_position} of {len(df.columns)}")
    
    if month_position == len(df.columns):
        print("  ✓ Month column is at the END")
    else:
        print(f"  ✗ Month column is NOT at the end (position {month_position})")
    
    # Show sample data
    print("\nSample Month values:")
    print(df[['Invoice_Date', 'Month']].head(10).to_string(index=False))
else:
    print("\n✗ Month column DOES NOT EXIST")
    print("\nThis means the Month column was not added to the Excel file.")
    print("The code adds it to the DataFrame but it might not be saved correctly.")

print("\n" + "=" * 80)
