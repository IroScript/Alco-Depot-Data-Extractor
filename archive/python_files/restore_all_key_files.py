"""
Restore All Key Files from Complete Workflow
============================================
Restore all important files from the archive based on the complete workflow

Author: Auto-generated
Date: 2026-05-23
"""

import os
import shutil

print("=" * 80)
print("RESTORING ALL KEY FILES FROM COMPLETE WORKFLOW")
print("=" * 80)

# All key files from the complete workflow
key_files_to_restore = [
    # From archive/python_files/
    ("archive/python_files/process_all_depots.py", "process_all_depots.py"),
    ("archive/python_files/process_product_level_FAST.py", "process_product_level_FAST.py"),
    
    # From archive/python_files/23_May/
    ("archive/python_files/23_May/extract_with_product_names.py", "extract_with_product_names.py"),
    ("archive/python_files/23_May/merge_targets_to_mpo_field.py", "merge_targets_to_mpo_field.py"),
    ("archive/python_files/23_May/create_achievement_pivot.py", "create_achievement_pivot.py"),
]

print("\nRestoring key files...")
restored = 0

for src, dst in key_files_to_restore:
    if os.path.exists(src):
        try:
            shutil.copy(src, dst)
            print(f"  ✓ Restored: {dst}")
            restored += 1
        except Exception as e:
            print(f"  ✗ Error restoring {dst}: {e}")
    else:
        print(f"  ✗ Not found: {src}")

print(f"\n✓ Restored {restored} files")

print("\n" + "=" * 80)
print("COMPLETE WORKFLOW - ALL KEY FILES")
print("=" * 80)

print("\n📋 COMPLETE WORKFLOW (ALL STEPS):")
print("\n1️⃣ EXTRACT TARGETS FROM EXCEL")
print("   Script: extract_with_product_names.py")
print("   Input: Unit Target of April-2026 (2).xlsx")
print("   Output: Target_Data_With_Products.xlsx")

print("\n2️⃣ MERGE TARGETS WITH MPO REFERENCE")
print("   Script: merge_targets_to_mpo_field.py")
print("   Input: MPO_CODE_AND_FIELD.xlsx + Target_Data_With_Products.xlsx")
print("   Output: MPO_Field_With_Targets.xlsx")

print("\n3️⃣ PROCESS SALES DATA FROM ALL DEPOTS")
print("   Script: process_all_depots.py (extracts from 9 depot databases)")
print("   OR: process_product_level_FAST.py (processes product-level sales)")
print("   Output: Product_Level_Net_Sales.csv")

print("\n4️⃣ CREATE ACHIEVEMENT PIVOT")
print("   Script: create_achievement_pivot.py")
print("   Input: Product_Level_Net_Sales.csv")
print("   Output: Achievement_Pivot.xlsx")

print("\n5️⃣ FIX CASE SENSITIVITY")
print("   Script: fix_achievement_pivot_case.py")
print("   Input: Achievement_Pivot.xlsx")
print("   Output: Achievement_Pivot_Fixed.xlsx")

print("\n6️⃣ CREATE FINAL TARGET VS ACHIEVEMENT REPORT")
print("   Script: create_target_vs_ach_alternating.py")
print("   Input: MPO_Field_With_Targets.xlsx + Achievement_Pivot_Fixed.xlsx")
print("   Output: MPO_Target_vs_Achievement.xlsx ⭐")

print("\n" + "=" * 80)
