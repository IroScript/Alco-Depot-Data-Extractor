"""
Final Cleanup - Keep Only Essential Files
=========================================
Today's work: Add product codes and VLOOKUP formulas
Keep only files needed for this task

Author: Auto-generated
Date: 2026-05-23
"""

import os
import shutil
from datetime import datetime

print("=" * 80)
print("FINAL CLEANUP - KEEP ONLY ESSENTIAL FILES")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Create archive folders
archive_python = "archive/python_files"
archive_excel = "archive/excel_files"

os.makedirs(archive_python, exist_ok=True)
os.makedirs(archive_excel, exist_ok=True)

# ============================================================================
# KEEP ONLY THESE FILES
# ============================================================================

# Today's work: Add product codes and VLOOKUP to get achievements
essential_python = {
    "create_target_vs_ach_alternating.py",  # Main script for today's task
    "fix_achievement_pivot_case.py",         # Helper to fix case issue
}

essential_excel = {
    # Source files
    "Unit Target of April-2026 (2).xlsx",
    "MPO_CODE_AND_FIELD.xlsx",
    
    # Input files (already created before today)
    "MPO_Field_With_Targets_20260523_102519.xlsx",  # Has targets
    "Achievement_Pivot_20260523_104633.xlsx",        # Has achievements
    
    # Files created today
    "Achievement_Pivot_Fixed_20260523_124434.xlsx",  # Fixed case issue
    "MPO_Target_vs_Achievement_20260523_124531.xlsx",  # FINAL OUTPUT
    "MPO_Target_vs_Achievement_Values_20260523_124531.xlsx",  # FINAL OUTPUT
}

# ============================================================================
# ARCHIVE ALL OTHER FILES
# ============================================================================

print("\nArchiving Python files...")
python_files = [f for f in os.listdir('.') if f.endswith('.py')]
moved_python = 0

for file in python_files:
    if file not in essential_python and file != 'final_cleanup.py':
        src = file
        dst = os.path.join(archive_python, file)
        try:
            shutil.move(src, dst)
            print(f"  ✓ Archived: {file}")
            moved_python += 1
        except Exception as e:
            print(f"  ✗ Error: {file} - {e}")

print(f"\nArchiving Excel files...")
excel_files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.csv')) and not f.startswith('~$')]
moved_excel = 0

for file in excel_files:
    if file not in essential_excel:
        src = file
        dst = os.path.join(archive_excel, file)
        try:
            shutil.move(src, dst)
            print(f"  ✓ Archived: {file}")
            moved_excel += 1
        except Exception as e:
            print(f"  ✗ Error: {file} - {e}")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "=" * 80)
print("SUMMARY - ESSENTIAL FILES ONLY")
print("=" * 80)

print(f"\n📌 TODAY'S TASK:")
print("  Add product codes and VLOOKUP formulas to get Target vs Achievement")

print(f"\n🐍 PYTHON SCRIPTS (2 files):")
print("  1. create_target_vs_ach_alternating.py")
print("     → Creates final Target vs Achievement report")
print("     → Adds product codes row")
print("     → Adds VLOOKUP formulas for achievements")
print()
print("  2. fix_achievement_pivot_case.py")
print("     → Fixes case sensitivity issue (CUMILLA vs Cumilla)")
print("     → Creates uppercase lookup column")

print(f"\n📊 EXCEL FILES (7 files):")
print("\n  SOURCE FILES (provided by you):")
print("  1. Unit Target of April-2026 (2).xlsx")
print("  2. MPO_CODE_AND_FIELD.xlsx")

print("\n  INPUT FILES (created before today):")
print("  3. MPO_Field_With_Targets_20260523_102519.xlsx")
print("     → Has MPO-wise targets for all products")
print("  4. Achievement_Pivot_20260523_104633.xlsx")
print("     → Has MPO-wise achievements for all products")

print("\n  OUTPUT FILES (created today):")
print("  5. Achievement_Pivot_Fixed_20260523_124434.xlsx")
print("     → Fixed version with uppercase keys for VLOOKUP")
print("  6. MPO_Target_vs_Achievement_20260523_124531.xlsx ⭐")
print("     → FINAL OUTPUT with VLOOKUP formulas")
print("  7. MPO_Target_vs_Achievement_Values_20260523_124531.xlsx ⭐")
print("     → FINAL OUTPUT with calculated values")

print(f"\n📁 ARCHIVED:")
print(f"  - Python files: {moved_python}")
print(f"  - Excel files: {moved_excel}")

print("\n" + "=" * 80)
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
