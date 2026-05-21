"""
Master Script - Run All Depot Processing with Error Handling and Auto-Recovery

This script will:
1. Check prerequisites (SQL Server, Python packages)
2. Fix permissions if needed
3. Detach old databases if needed
4. Process all depots
5. Handle errors and retry with different approaches
6. Never fail - always find a way to complete

Usage:
    python run_all.py
"""

import os
import sys
import subprocess
import time
import pyodbc
import pandas as pd
from datetime import datetime

# Configuration
SQL_SERVER = r'.\SQLEXPRESS'
ALL_DEPOTS_FOLDER = r"C:\Users\Irak\Desktop\Barishal April Data\All_Depots"
INSTALLATION_FOLDER = r"C:\Users\Irak\Desktop\Barishal April Data\installation"

class Colors:
    """Console colors for better visibility"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print("=" * 70)

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")

def check_sql_server():
    """Check if SQL Server is running"""
    print_header("Step 1: Checking SQL Server")
    
    try:
        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SQL_SERVER};DATABASE=master;Trusted_Connection=yes;'
        conn = pyodbc.connect(conn_str, timeout=5)
        conn.close()
        print_success("SQL Server is running")
        return True
    except Exception as e:
        print_error(f"SQL Server not accessible: {e}")
        print_warning("Please start SQL Server service manually")
        return False

def check_python_packages():
    """Check if required Python packages are installed"""
    print_header("Step 2: Checking Python Packages")
    
    required = ['pyodbc', 'pandas', 'openpyxl']
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print_success(f"{package} is installed")
        except ImportError:
            missing.append(package)
            print_error(f"{package} is NOT installed")
    
    if missing:
        print_warning(f"Installing missing packages: {', '.join(missing)}")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install'] + missing, check=True)
            print_success("All packages installed successfully")
            return True
        except Exception as e:
            print_error(f"Failed to install packages: {e}")
            return False
    
    return True

def fix_permissions():
    """Fix file permissions for SQL Server"""
    print_header("Step 3: Fixing Permissions")
    
    try:
        # Check if fix_permissions.cmd exists
        fix_script = os.path.join(INSTALLATION_FOLDER, 'fix_permissions.cmd')
        
        if not os.path.exists(fix_script):
            print_warning("fix_permissions.cmd not found, skipping...")
            return True
        
        print_info("Running permission fix script...")
        result = subprocess.run([fix_script], cwd=INSTALLATION_FOLDER, capture_output=True, text=True)
        
        if "Successfully processed" in result.stdout:
            print_success("Permissions fixed successfully")
            return True
        else:
            print_warning("Permission fix completed with warnings")
            return True
            
    except Exception as e:
        print_warning(f"Permission fix failed: {e}")
        print_info("Continuing anyway - will retry if database attach fails")
        return True

def detach_old_databases():
    """Detach old depot databases"""
    print_header("Step 4: Cleaning Up Old Databases")
    
    try:
        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SQL_SERVER};DATABASE=master;Trusted_Connection=yes;'
        conn = pyodbc.connect(conn_str)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Get all depot databases
        cursor.execute("""
            SELECT name FROM sys.databases 
            WHERE name LIKE '%_DB'
            AND name NOT IN ('master', 'tempdb', 'model', 'msdb')
        """)
        
        databases = [row[0] for row in cursor.fetchall()]
        
        if not databases:
            print_info("No old databases to detach")
            conn.close()
            return True
        
        print_info(f"Found {len(databases)} old databases to detach")
        
        for db_name in databases:
            try:
                # Kill connections
                cursor.execute(f"ALTER DATABASE [{db_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;")
                # Detach
                cursor.execute(f"EXEC sp_detach_db '{db_name}'")
                print_success(f"Detached: {db_name}")
            except Exception as e:
                print_warning(f"Could not detach {db_name}: {e}")
        
        conn.close()
        return True
        
    except Exception as e:
        print_warning(f"Database cleanup failed: {e}")
        print_info("Continuing anyway - will handle during processing")
        return True

def process_all_depots():
    """Run the main depot processing script"""
    print_header("Step 5: Processing All Depots")
    
    try:
        print_info("Starting multi-depot extraction...")
        
        # Import and run the main script
        import process_all_depots
        process_all_depots.process_all_depots()
        
        print_success("All depots processed successfully!")
        return True
        
    except Exception as e:
        print_error(f"Processing failed: {e}")
        print_warning("Attempting recovery...")
        
        # Recovery attempt 1: Retry after detaching databases
        try:
            print_info("Recovery Attempt 1: Detaching databases and retrying...")
            detach_old_databases()
            time.sleep(2)
            
            import process_all_depots
            process_all_depots.process_all_depots()
            
            print_success("Recovery successful!")
            return True
            
        except Exception as e2:
            print_error(f"Recovery attempt 1 failed: {e2}")
            
            # Recovery attempt 2: Fix permissions and retry
            try:
                print_info("Recovery Attempt 2: Fixing permissions and retrying...")
                fix_permissions()
                time.sleep(2)
                detach_old_databases()
                time.sleep(2)
                
                import process_all_depots
                process_all_depots.process_all_depots()
                
                print_success("Recovery successful!")
                return True
                
            except Exception as e3:
                print_error(f"Recovery attempt 2 failed: {e3}")
                print_error("All recovery attempts exhausted")
                return False

def find_latest_report():
    """Find the latest generated report"""
    try:
        reports = [f for f in os.listdir('.') if f.startswith('All_Depots_MPO_Report_') and f.endswith('.xlsx')]
        if reports:
            latest = max(reports, key=lambda x: os.path.getctime(x))
            return latest
        return None
    except:
        return None

def main():
    """Main execution function"""
    start_time = time.time()
    
    print_header("🚀 Alco Depot Data Extractor - Master Script")
    print_info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Check SQL Server
    if not check_sql_server():
        print_error("Cannot proceed without SQL Server")
        print_info("Please start SQL Server and run this script again")
        return False
    
    # Step 2: Check Python packages
    if not check_python_packages():
        print_error("Cannot proceed without required packages")
        return False
    
    # Step 3: Fix permissions
    fix_permissions()
    
    # Step 4: Clean up old databases
    detach_old_databases()
    
    # Step 5: Process all depots
    if not process_all_depots():
        print_error("Processing failed after all recovery attempts")
        return False
    
    # Success!
    elapsed = time.time() - start_time
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    
    print_header("✅ SUCCESS!")
    print_success(f"All depots processed successfully in {minutes}m {seconds}s")
    
    # Find and display report location
    report = find_latest_report()
    if report:
        print_info(f"Report saved: {report}")
        print_info(f"File size: {os.path.getsize(report) / (1024*1024):.2f} MB")
    
    print("\n" + "=" * 70)
    print(f"{Colors.BOLD}Next Steps:{Colors.RESET}")
    print("1. Open the Excel report to view results")
    print("2. Check Depot Summary sheet for overview")
    print("3. Check MPO Summary sheet for detailed breakdown")
    print("=" * 70 + "\n")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_warning("\n\nProcess interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
