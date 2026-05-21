# Final cleanup - Move Excel files to archive, keep single README

import os
import shutil
import glob

def cleanup():
    print("=" * 70)
    print("Final Cleanup for GitHub Upload")
    print("=" * 70)
    
    archive_dir = 'archive'
    
    # Move all Excel files to archive
    excel_files = glob.glob('*.xlsx') + glob.glob('*.xls')
    
    if excel_files:
        print(f"\nMoving {len(excel_files)} Excel files to archive...")
        for excel_file in excel_files:
            try:
                dest = os.path.join(archive_dir, excel_file)
                shutil.move(excel_file, dest)
                print(f"  Moved: {excel_file}")
            except Exception as e:
                print(f"  Error: {excel_file} - {e}")
    
    # Move extra MD files to archive (keep only README.md)
    md_files_to_move = [
        'README_BANGLA.md',
        'SOLUTION_FINAL.md',
        'GITHUB_UPLOAD_GUIDE.md',
        'UPLOAD_NOW.md',
        'PROJECT_SUMMARY.md',
        'install_sql2000_guide.md',
    ]
    
    print(f"\nMoving extra documentation to archive...")
    for md_file in md_files_to_move:
        if os.path.exists(md_file):
            try:
                dest = os.path.join(archive_dir, md_file)
                shutil.move(md_file, dest)
                print(f"  Moved: {md_file}")
            except Exception as e:
                print(f"  Error: {md_file} - {e}")
    
    # Move organize and cleanup scripts to archive
    utility_scripts = [
        'organize_files.py',
        'cleanup_for_github.py',
    ]
    
    print(f"\nMoving utility scripts to archive...")
    for script in utility_scripts:
        if os.path.exists(script) and script != 'cleanup_for_github.py':
            try:
                dest = os.path.join(archive_dir, script)
                shutil.move(script, dest)
                print(f"  Moved: {script}")
            except Exception as e:
                print(f"  Error: {script} - {e}")
    
    # Remove temporary files
    temp_files = ['query', '~$*.xlsx']
    print(f"\nRemoving temporary files...")
    for pattern in temp_files:
        for temp_file in glob.glob(pattern):
            try:
                os.remove(temp_file)
                print(f"  Removed: {temp_file}")
            except Exception as e:
                print(f"  Error: {temp_file} - {e}")
    
    print("\n" + "=" * 70)
    print("Cleanup Complete!")
    print("=" * 70)
    
    # Show final structure
    print("\nFinal Root Folder Contents:")
    print("-" * 70)
    
    root_files = [f for f in os.listdir('.') if os.path.isfile(f)]
    root_files.sort()
    
    for f in root_files:
        size = os.path.getsize(f)
        print(f"  {f:45s} ({size:,} bytes)")
    
    print("\nFolders:")
    folders = [f for f in os.listdir('.') if os.path.isdir(f) and not f.startswith('.')]
    for folder in folders:
        print(f"  {folder}/")
    
    print("\n" + "=" * 70)
    print("Ready for GitHub Upload!")
    print("=" * 70)
    print("\nRoot folder now contains:")
    print("  ✅ 4 Python scripts (working tools)")
    print("  ✅ 3 CMD files (installation)")
    print("  ✅ 1 README.md (documentation)")
    print("  ✅ requirements.txt")
    print("  ✅ .gitignore")
    print("  ✅ upload_to_github.cmd")
    print("\nArchive folder contains:")
    print("  📦 All Excel reports")
    print("  📦 Extra documentation")
    print("  📦 Old scripts")
    print("\nIgnored (won't upload):")
    print("  🚫 Data/ folder")

if __name__ == "__main__":
    cleanup()
