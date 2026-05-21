# Organize files - Keep working files, move others to archive

import os
import shutil

# Working files that should stay in root
WORKING_FILES = [
    # Main scripts (actually working)
    'mpo_final_report.py',           # MPO-wise sales report (WORKING)
    'find_mpo_codes.py',              # Find MPO codes in database (WORKING)
    'export_all_data.py',             # Export all tables (WORKING)
    'read_with_sql2005.py',           # Attach MDF and read (WORKING)
    
    # Installation
    'download_sql2008.cmd',           # SQL Server installer
    'install_odbc.cmd',               # ODBC Driver installer
    'fix_permissions.cmd',            # Fix file permissions
    
    # Documentation
    'README.md',
    'README_BANGLA.md',
    'SOLUTION_FINAL.md',
    'GITHUB_UPLOAD_GUIDE.md',
    
    # Config
    'requirements.txt',
    '.gitignore',
    'upload_to_github.cmd',
]

# Files to archive (experimental/old versions)
ARCHIVE_FILES = [
    # Old/experimental scripts
    'create_sales_report.py',         # Old version (replaced by mpo_final_report.py)
    'automate_mpo_extraction.py',     # GUI automation (for different use case)
    'quick_test.py',                  # Test script
    'read_mdf_direct.py',             # Old approach
    'read_with_localdb.py',           # Old approach
    'extract_mdf_simple.py',          # Old approach
    'extract_with_sqlite.py',         # Old approach
    'extract_mpo_master.py',          # Old version
    
    # Installation helpers (old)
    'install_odbc_driver.ps1',        # PowerShell version (cmd is better)
    'install_sql2000_guide.md',       # Detailed guide (covered in SOLUTION_FINAL.md)
    
    # Sample data
    'mpo_list_sample.csv',            # Sample file
]

def organize():
    print("=" * 70)
    print("Organizing Files for GitHub Upload")
    print("=" * 70)
    
    # Create archive folder
    archive_dir = 'archive'
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)
        print(f"\nCreated: {archive_dir}/")
    
    # Move files to archive
    moved_count = 0
    for filename in ARCHIVE_FILES:
        if os.path.exists(filename):
            try:
                shutil.move(filename, os.path.join(archive_dir, filename))
                print(f"  Moved: {filename} -> archive/")
                moved_count += 1
            except Exception as e:
                print(f"  Error moving {filename}: {e}")
    
    print(f"\nMoved {moved_count} files to archive/")
    
    # List working files
    print("\n" + "=" * 70)
    print("Working Files (staying in root):")
    print("=" * 70)
    
    for filename in WORKING_FILES:
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"  {filename:40s} ({size:,} bytes)")
    
    # Create archive README
    archive_readme = os.path.join(archive_dir, 'README.md')
    with open(archive_readme, 'w', encoding='utf-8') as f:
        f.write("""# Archive

This folder contains old/experimental scripts and documentation.

## Old Scripts

These scripts were used during development but have been replaced by better versions:

- `create_sales_report.py` - Replaced by `mpo_final_report.py`
- `automate_mpo_extraction.py` - GUI automation (for different use case)
- `read_mdf_direct.py`, `read_with_localdb.py` - Old approaches
- `extract_*.py` - Experimental extraction methods

## Why Archived?

- **Working versions** are in the root folder
- These are kept for reference and historical purposes
- May contain useful code snippets for future development

## Usage

If you need to use any of these scripts, copy them back to the root folder.
""")
    
    print(f"\nCreated: {archive_readme}")
    
    print("\n" + "=" * 70)
    print("Organization Complete!")
    print("=" * 70)
    print("\nRoot folder now contains only:")
    print("  - Working scripts (4 main Python files)")
    print("  - Installation files (3 cmd files)")
    print("  - Documentation (4 md files)")
    print("  - Config files (requirements.txt, .gitignore)")
    print("\nArchive folder contains:")
    print(f"  - {moved_count} old/experimental files")
    print("\nReady for GitHub upload!")

if __name__ == "__main__":
    organize()
