"""
Cleanup and Archive Files
=========================
Move old Python scripts and Excel files to archive folders
Keep only active/final files in the root directory

Author: Auto-generated
Date: 2026-05-23
"""

import os
import shutil
from datetime import datetime

print("=" * 80)
print("CLEANUP AND ARCHIVE FILES")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Create archive folders if they don't exist
archive_python = "archive/python_files"
archive_excel = "archive/excel_files"

os.makedirs(archive_python, exist_ok=True)
os.makedirs(archive_excel, exist_ok=True)

print(f"Created archive folders:")
print(f"  - {archive_python}")
print(f"  - {archive_excel}")

# ============================================================================
# ACTIVE FILES TO KEEP IN ROOT
# ============================================================================

active_python_files = {
    # Main processing scripts
    "process_all_depots.py",
    "process_net_sales_final.py",
    "process_product_level_FAST.py",
    "create_achievement_pivot.py",
    "extract_with_product_names.py",
    "merge_targets_to_mpo_field.py",
    "create_target_vs_ach_alternating.py",
    "fix_achievement_pivot_case.py",
    
    # This cleanup script
    "cleanup_and_archive.py",
}

active_excel_files = {
    # Source files
    "Unit Target of April-2026 (2).xlsx",
    "MPO_CODE_AND_FIELD.xlsx",
    
    # Final output files (latest versions)
    "Achievement_Pivot_20260523_104633.xlsx",
    "Achievement_Pivot_Fixed_20260523_124434.xlsx",
    "Product_Level_Net_Sales_20260522_232817.csv",
    "MPO_Field_With_Targets_20260523_102519.xlsx",
    "MPO_Target_vs_Achievement_20260523_124531.xlsx",
    "MPO_Target_vs_Achievement_Values_20260523_124531.xlsx",
}

# ============================================================================
# MOVE PYTHON FILES TO ARCHIVE
# ============================================================================

print("\n" + "=" * 80)
print("ARCHIVING PYTHON FILES")
print("=" * 80)

python_files = [f for f in os.listdir('.') if f.endswith('.py')]
moved_python = 0

for file in python_files:
    if file not in active_python_files:
        src = file
        dst = os.path.join(archive_python, file)
        try:
            shutil.move(src, dst)
            print(f"  ✓ Moved: {file}")
            moved_python += 1
        except Exception as e:
            print(f"  ✗ Error moving {file}: {e}")

print(f"\nMoved {moved_python} Python files to archive")

# ============================================================================
# MOVE EXCEL FILES TO ARCHIVE
# ============================================================================

print("\n" + "=" * 80)
print("ARCHIVING EXCEL FILES")
print("=" * 80)

excel_files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.csv')) and not f.startswith('~$')]
moved_excel = 0

for file in excel_files:
    if file not in active_excel_files:
        src = file
        dst = os.path.join(archive_excel, file)
        try:
            shutil.move(src, dst)
            print(f"  ✓ Moved: {file}")
            moved_excel += 1
        except Exception as e:
            print(f"  ✗ Error moving {file}: {e}")

print(f"\nMoved {moved_excel} Excel files to archive")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

print(f"\nActive Python files in root ({len(active_python_files)}):")
for file in sorted(active_python_files):
    if os.path.exists(file):
        print(f"  ✓ {file}")

print(f"\nActive Excel files in root ({len(active_excel_files)}):")
for file in sorted(active_excel_files):
    if os.path.exists(file):
        print(f"  ✓ {file}")

print(f"\nArchived:")
print(f"  - Python files: {moved_python}")
print(f"  - Excel files: {moved_excel}")

print("\n" + "=" * 80)
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
