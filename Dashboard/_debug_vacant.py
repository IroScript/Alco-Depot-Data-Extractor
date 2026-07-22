import pandas as pd

url = 'https://docs.google.com/spreadsheets/d/1Q4utivZ5OpgDznqlqElYU-HWNnZYI71YYpcZKcSM3xY/export?format=csv&gid=1918615875'
df = pd.read_csv(url)
df.columns = [str(c).strip() for c in df.columns]

print("=== ALL COLUMNS ===")
for i, c in enumerate(df.columns):
    print(f"  [{i}] '{c}'")

print(f"\n=== Total Rows: {len(df)} ===")

# Find vacant column
vac_cols = [c for c in df.columns if 'VACANT' in c.upper()]
print(f"\n=== Vacant columns: {vac_cols} ===")
if vac_cols:
    print("Vacant value counts:")
    print(df[vac_cols[0]].value_counts(dropna=False))

# Find MPO columns
print("\n=== MPO-related columns ===")
for c in df.columns:
    if 'MPO' in c.upper() or 'DEPOTMPO' in c.upper():
        print(f"  '{c}' - Sample: {df[c].dropna().head(5).tolist()}")

# Find DEPOT columns
print("\n=== DEPOT-related columns ===")
for c in df.columns:
    if 'DEPOT' in c.upper():
        print(f"  '{c}' - Sample: {df[c].dropna().head(5).tolist()}")

# Check what load_vacant_mpos would produce
print("\n=== Simulating load_vacant_mpos() ===")
def _clean_cell(val):
    if pd.isna(val):
        return ''
    return str(val).strip()

vacant_map = {}
for _, row in df.iterrows():
    vac_val = _clean_cell(row.get("VACANT (JUN'26)?"))
    depot = _clean_cell(row.get('DREAM APPS DEPOT')) or _clean_cell(row.get('DEPOT'))
    code = _clean_cell(row.get('DEPOTMPO CODE')) or _clean_cell(row.get('DREAM APPS MPO CODE'))
    if code:
        vac_status = vac_val if vac_val else 'NO'
        vacant_map[code.upper()] = vac_status
        if depot:
            composite_key = f"{depot.upper()}_{code.upper()}"
            vacant_map[composite_key] = vac_status

y_count = sum(1 for v in vacant_map.values() if v.upper() in ('Y', 'YES'))
n_count = sum(1 for v in vacant_map.values() if v.upper() in ('N', 'NO'))
other = sum(1 for v in vacant_map.values() if v.upper() not in ('Y', 'YES', 'N', 'NO'))
print(f"Total keys in vacant_map: {len(vacant_map)}")
print(f"  Y/YES values: {y_count}")
print(f"  N/NO values: {n_count}")
print(f"  Other values: {other}")

# Show all unique vacant values
print(f"\n=== Unique vacant values in map ===")
unique_vals = set(vacant_map.values())
for v in sorted(unique_vals):
    cnt = sum(1 for x in vacant_map.values() if x == v)
    print(f"  '{v}': {cnt}")

# Show some Y entries
print(f"\n=== Sample Y/YES entries (max 20) ===")
count = 0
for k, v in vacant_map.items():
    if v.upper() in ('Y', 'YES'):
        print(f"  Key='{k}' -> Value='{v}'")
        count += 1
        if count >= 20:
            break

# Check the DEPOTMPO CODE vs DREAM APPS MPO CODE
print(f"\n=== DEPOTMPO CODE vs DREAM APPS MPO CODE comparison ===")
depotmpo = df.get('DEPOTMPO CODE')
dreammpo = df.get('DREAM APPS MPO CODE')
if depotmpo is not None and dreammpo is not None:
    mismatches = 0
    for i, row in df.iterrows():
        d = _clean_cell(row.get('DEPOTMPO CODE'))
        m = _clean_cell(row.get('DREAM APPS MPO CODE'))
        if d and m and d.upper() != m.upper():
            mismatches += 1
            if mismatches <= 10:
                print(f"  Row {i}: DEPOTMPO='{d}' vs DREAM APPS MPO='{m}'")
    print(f"Total mismatches: {mismatches}")
elif depotmpo is not None:
    print("Only DEPOTMPO CODE column exists")
elif dreammpo is not None:
    print("Only DREAM APPS MPO CODE column exists (no DEPOTMPO CODE)")
else:
    print("NEITHER column found!")
