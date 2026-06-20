# FAST Product-Level Net Sales Calculation
# Uses CSV for speed, then converts to Excel

import sys
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
    except:
        pass

import pyodbc
import pandas as pd
import os
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading

# Configuration
SQL_SERVER = r'.\SQLEXPRESS'

def cleanup_existing_databases():
    """Detach all existing depot databases for fresh start"""
    try:
        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SQL_SERVER};DATABASE=master;Trusted_Connection=yes;'
        conn = pyodbc.connect(conn_str)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Find all databases ending with _DB (exclude system databases)
        cursor.execute("""
            SELECT name 
            FROM sys.databases 
            WHERE name LIKE '%_DB'
            AND name NOT IN ('master', 'model', 'msdb', 'tempdb')
        """)
        
        databases = [row[0] for row in cursor.fetchall()]
        
        if databases:
            print(f"\nCleaning up {len(databases)} existing database(s)...")
            
            for db_name in databases:
                try:
                    # Kill all connections using sp_who (compatible with older SQL Server)
                    cursor.execute(f"""
                        DECLARE @spid INT
                        DECLARE @sql VARCHAR(1000)
                        DECLARE spid_cursor CURSOR FOR
                        SELECT spid FROM master..sysprocesses 
                        WHERE dbid = DB_ID('{db_name}')
                        
                        OPEN spid_cursor
                        FETCH NEXT FROM spid_cursor INTO @spid
                        
                        WHILE @@FETCH_STATUS = 0
                        BEGIN
                            SET @sql = 'KILL ' + CAST(@spid AS VARCHAR(10))
                            EXEC(@sql)
                            FETCH NEXT FROM spid_cursor INTO @spid
                        END
                        
                        CLOSE spid_cursor
                        DEALLOCATE spid_cursor
                    """)
                    
                    # Set to single user mode and detach
                    cursor.execute(f"ALTER DATABASE [{db_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
                    cursor.execute(f"EXEC sp_detach_db '{db_name}', 'true'")
                    print(f"  [OK] Detached: {db_name}")
                    
                except Exception as e:
                    # If detach fails, try to drop the database instead
                    try:
                        cursor.execute(f"DROP DATABASE [{db_name}]")
                        print(f"  [OK] Dropped: {db_name}")
                    except:
                        print(f"  [ERROR] Could not remove {db_name}: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"  Note: Cleanup skipped - {e}")

def select_folders_gui():
    """GUI to select All_Depots folder and output directory"""
    
    class DepotSelectorGUI:
        def __init__(self, root):
            self.root = root
            self.root.title("Depot Data Extractor - Folder Selection")
            self.root.geometry("850x650")
            self.root.resizable(True, True)
            
            self.all_depots_folder = ""
            self.depot_folders = []
            self.output_dir = ""
            self.processing = False
            
            # Title
            title_label = tk.Label(root, text="Product-Level Net Sales Calculator", 
                                  font=("Arial", 14, "bold"), fg="#2c3e50")
            title_label.pack(pady=10)
            
            # All_Depots Folder Section
            depot_frame = tk.LabelFrame(root, text="Step 1: Select All_Depots Folder", 
                                       font=("Arial", 11, "bold"), padx=15, pady=10)
            depot_frame.pack(padx=15, pady=5, fill="both")
            
            # Selected folder label
            self.depot_folder_label = tk.Label(depot_frame, text="No folder selected", 
                                              font=("Arial", 9), fg="#7f8c8d", anchor="w",
                                              wraplength=750)
            self.depot_folder_label.pack(fill="x", pady=(0, 5))
            
            # Select button
            select_depot_btn = tk.Button(depot_frame, text="Select All_Depots Folder", 
                                         command=self.select_all_depots_folder, 
                                         bg="#3498db", fg="white",
                                         font=("Arial", 10, "bold"), padx=10, pady=5)
            select_depot_btn.pack(pady=(0, 5))
            
            # Depot list frame
            list_frame = tk.Frame(depot_frame)
            list_frame.pack(fill="both", expand=True)
            
            # Scrollbar
            scrollbar = tk.Scrollbar(list_frame)
            scrollbar.pack(side="right", fill="y")
            
            # Listbox for found depots
            self.depot_listbox = tk.Listbox(list_frame, height=4, font=("Arial", 9),
                                           yscrollcommand=scrollbar.set)
            self.depot_listbox.pack(side="left", fill="both", expand=True)
            scrollbar.config(command=self.depot_listbox.yview)
            
            # Status label
            self.status_label = tk.Label(depot_frame, text="", 
                                        font=("Arial", 8, "italic"), fg="#7f8c8d")
            self.status_label.pack(pady=(3, 0))
            
            # Output Directory Section
            output_frame = tk.LabelFrame(root, text="Step 2: Select Output Directory", 
                                        font=("Arial", 11, "bold"), padx=15, pady=10)
            output_frame.pack(padx=15, pady=5, fill="x")
            
            self.output_label = tk.Label(output_frame, text="No directory selected", 
                                         font=("Arial", 9), fg="#7f8c8d", anchor="w",
                                         wraplength=750)
            self.output_label.pack(fill="x", pady=(0, 5))
            
            output_btn = tk.Button(output_frame, text="Select Output Directory", 
                                  command=self.select_output_dir, bg="#27ae60", fg="white",
                                  font=("Arial", 10, "bold"), padx=10, pady=5)
            output_btn.pack()
            
            # Progress Section
            progress_frame = tk.LabelFrame(root, text="Processing Status", 
                                          font=("Arial", 11, "bold"), padx=15, pady=10)
            progress_frame.pack(padx=15, pady=5, fill="both")
            
            # Progress bar
            self.progress_var = tk.DoubleVar()
            self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                               maximum=100, length=400, mode='determinate')
            self.progress_bar.pack(fill="x", pady=(0, 3))
            
            # Progress label
            self.progress_label = tk.Label(progress_frame, text="Ready to start", 
                                          font=("Arial", 9), fg="#7f8c8d")
            self.progress_label.pack(pady=(0, 5))
            
            # Log text area with scrollbar
            log_frame = tk.Frame(progress_frame)
            log_frame.pack(fill="both")
            
            log_scrollbar = tk.Scrollbar(log_frame)
            log_scrollbar.pack(side="right", fill="y")
            
            self.log_text = tk.Text(log_frame, height=6, font=("Consolas", 8),
                                   bg="#f8f9fa", fg="#2c3e50",
                                   yscrollcommand=log_scrollbar.set, state="disabled")
            self.log_text.pack(side="left", fill="both", expand=True)
            log_scrollbar.config(command=self.log_text.yview)
            
            # Start Button - Larger and more visible
            self.start_btn = tk.Button(root, text="▶ START PROCESSING", 
                                      command=self.start_processing, bg="#16a085", fg="white",
                                      font=("Arial", 13, "bold"), padx=40, pady=12,
                                      state="disabled", relief="raised", bd=3)
            self.start_btn.pack(pady=10)
            
        def log(self, message):
            """Add message to log window - thread-safe"""
            def _log():
                self.log_text.config(state="normal")
                self.log_text.insert(tk.END, message + "\n")
                self.log_text.see(tk.END)
                self.log_text.config(state="disabled")
            
            # Schedule on main thread
            self.root.after(0, _log)
        
        def update_progress(self, value, message):
            """Update progress bar and label - thread-safe"""
            def _update():
                self.progress_var.set(value)
                self.progress_label.config(text=message)
            
            # Schedule on main thread
            self.root.after(0, _update)
        
        def select_all_depots_folder(self):
            folder = filedialog.askdirectory(title="Select All_Depots Folder")
            if folder:
                self.all_depots_folder = folder
                self.depot_folder_label.config(text=self.all_depots_folder, fg="#2c3e50")
                
                # Scan for depot subfolders
                self.scan_depot_folders()
        
        def scan_depot_folders(self):
            """Scan All_Depots folder for valid depot subfolders"""
            self.depot_listbox.delete(0, tk.END)
            self.depot_folders.clear()
            self.log_text.config(state="normal")
            self.log_text.delete(1.0, tk.END)
            self.log_text.config(state="disabled")
            
            self.log(f"Scanning folder: {self.all_depots_folder}")
            
            if not os.path.exists(self.all_depots_folder):
                self.status_label.config(text="❌ Folder does not exist!", fg="#e74c3c")
                self.log("ERROR: Folder does not exist!")
                return
            
            valid_count = 0
            invalid_count = 0
            
            # Scan all subfolders
            for item in os.listdir(self.all_depots_folder):
                item_path = os.path.join(self.all_depots_folder, item)
                
                if os.path.isdir(item_path):
                    data_folder = os.path.join(item_path, 'Data')
                    
                    if os.path.exists(data_folder):
                        # Check for ERPonTheNet_Data.MDF
                        mdf_found = False
                        for file in os.listdir(data_folder):
                            if file.lower() == 'erponthenet_data.mdf':
                                mdf_found = True
                                break
                        
                        if mdf_found:
                            self.depot_folders.append(item_path)
                            self.depot_listbox.insert(tk.END, f"✓ {item}")
                            self.depot_listbox.itemconfig(tk.END, fg="#27ae60")
                            self.log(f"✓ Valid depot found: {item}")
                            valid_count += 1
                        else:
                            self.depot_listbox.insert(tk.END, f"✗ {item} (No ERPonTheNet_Data.MDF)")
                            self.depot_listbox.itemconfig(tk.END, fg="#e74c3c")
                            self.log(f"✗ Invalid depot: {item} (No ERPonTheNet_Data.MDF)")
                            invalid_count += 1
                    else:
                        self.depot_listbox.insert(tk.END, f"✗ {item} (No Data subfolder)")
                        self.depot_listbox.itemconfig(tk.END, fg="#e74c3c")
                        self.log(f"✗ Invalid depot: {item} (No Data subfolder)")
                        invalid_count += 1
            
            # Update status
            if valid_count == 0:
                self.status_label.config(
                    text=f"❌ No valid depots found! Please ensure folder structure:\n"
                         f"All_Depots → [DepotName] → Data → ERPonTheNet_Data.MDF",
                    fg="#e74c3c"
                )
                self.log("ERROR: No valid depots found!")
                self.log("Expected structure: All_Depots → [DepotName] → Data → ERPonTheNet_Data.MDF")
                self.start_btn.config(state="disabled")
            else:
                self.status_label.config(
                    text=f"✓ Found {valid_count} valid depot(s), {invalid_count} invalid",
                    fg="#27ae60"
                )
                self.log(f"Scan complete: {valid_count} valid, {invalid_count} invalid")
                if self.output_dir:
                    self.start_btn.config(state="normal")
        
        def select_output_dir(self):
            directory = filedialog.askdirectory(title="Select Output Directory")
            if directory:
                self.output_dir = directory
                self.output_label.config(text=self.output_dir, fg="#2c3e50")
                self.log(f"Output directory selected: {self.output_dir}")
                
                # Enable start button if depots are selected
                if self.depot_folders:
                    self.start_btn.config(state="normal")
        
        def start_processing(self):
            if not self.depot_folders:
                messagebox.showerror("Error", 
                    "No valid depot folders found!\n\n"
                    "Please ensure folder structure:\n"
                    "All_Depots → [DepotName] → Data → ERPonTheNet_Data.MDF")
                return
            
            if not self.output_dir:
                messagebox.showerror("Error", "Please select an output directory!")
                return
            
            # Disable start button during processing
            self.start_btn.config(state="disabled", text="PROCESSING...", bg="#e67e22")
            self.processing = True
            
            # Start processing in a separate thread
            processing_thread = threading.Thread(target=self.run_processing)
            processing_thread.daemon = True
            processing_thread.start()
        
        def run_processing(self):
            """Run processing in separate thread"""
            try:
                # This will be called from process_all_depots
                pass
            except Exception as e:
                self.log(f"\nERROR: {str(e)}")
                messagebox.showerror("Error", f"An error occurred:\n\n{str(e)}")
    
    # Create and run GUI
    root = tk.Tk()
    app = DepotSelectorGUI(root)
    
    # Return app instance so we can update it during processing
    return app

def find_all_depots(depot_folders):
    """Process selected depot folders"""
    print(f"\nProcessing {len(depot_folders)} depot(s)...")
    
    depots = []
    
    for depot_folder in depot_folders:
        depot_name = os.path.basename(depot_folder)
        data_folder = os.path.join(depot_folder, 'Data')
        
        if os.path.exists(data_folder):
            erp_mdf = None
            for file in os.listdir(data_folder):
                if file.lower() == 'erponthenet_data.mdf':
                    erp_mdf = os.path.join(data_folder, file)
                    break
            
            if erp_mdf:
                depots.append({
                    'name': depot_name,
                    'path': depot_folder,
                    'data_folder': data_folder,
                    'mdf_file': erp_mdf
                })
                print(f"  [OK] {depot_name}")
    
    return depots

def grant_sql_server_permissions(folder_path):
    """Grant SQL Server service account read/write permissions to folder"""
    try:
        import subprocess
        # Grant permissions to SQL Server service accounts
        # This covers most common SQL Server service account names
        accounts = [
            'NT SERVICE\\MSSQL$SQLEXPRESS',
            'NT SERVICE\\MSSQLSERVER',
            'NT AUTHORITY\\NETWORK SERVICE',
            'NT AUTHORITY\\SYSTEM'
        ]
        
        for account in accounts:
            try:
                # Use icacls to grant permissions (Windows command)
                cmd = f'icacls "{folder_path}" /grant "{account}:(OI)(CI)F" /T /Q'
                subprocess.run(cmd, shell=True, capture_output=True, timeout=10)
            except:
                pass  # Silently continue if one fails
                
    except Exception as e:
        pass  # Permissions might already be set

def attach_database(depot_name, mdf_path):
    """Attach MDF file to SQL Server"""
    try:
        mdf_dir = os.path.dirname(mdf_path)
        
        # Grant SQL Server permissions to the Data folder
        grant_sql_server_permissions(mdf_dir)
        
        ldf_path = None
        for file in os.listdir(mdf_dir):
            if file.lower() == 'erponthenet_log.ldf':
                ldf_path = os.path.join(mdf_dir, file)
                break
        
        db_name = f"{depot_name.upper()}_DB"
        
        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SQL_SERVER};DATABASE=master;Trusted_Connection=yes;'
        conn = pyodbc.connect(conn_str)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Normalize paths - use backslashes for Windows
        mdf_path = os.path.normpath(mdf_path)
        
        if ldf_path and os.path.exists(ldf_path):
            ldf_path = os.path.normpath(ldf_path)
            attach_query = f"""
            CREATE DATABASE [{db_name}] ON 
            (FILENAME = N'{mdf_path}'),
            (FILENAME = N'{ldf_path}')
            FOR ATTACH;
            """
        else:
            attach_query = f"""
            CREATE DATABASE [{db_name}] ON 
            (FILENAME = N'{mdf_path}')
            FOR ATTACH_REBUILD_LOG;
            """
        
        cursor.execute(attach_query)
        conn.close()
        return db_name
        
    except Exception as e:
        print(f"    [ERROR] Error attaching: {e}")
        return None

def extract_sales_data(depot_name, db_name):
    """Extract sales and returns data"""
    try:
        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SQL_SERVER};DATABASE={db_name};Trusted_Connection=yes;'
        conn = pyodbc.connect(conn_str)
        
        query = f"""
        SELECT 
            '{depot_name}' AS Depot,
            o.xsp AS MPO_Code,
            o.xordernum AS Invoice_No,
            o.xdate AS Invoice_Date,
            o.ztime AS Transaction_Time,
            CASE 
                WHEN o.xordernum LIKE 'IN-%' OR o.xordernum LIKE 'IN--%' THEN 'Sale'
                WHEN o.xordernum LIKE 'SR-%' OR o.xordernum LIKE 'SR--%' THEN 'Return'
                ELSE 'Other'
            END AS Transaction_Type,
            o.xcus AS Customer_ID,
            LTRIM(RTRIM(c.xorg)) AS Customer_Name,
            od.xitem AS Product_Code,
            i.xdesc AS Product_Name,
            od.xqtyord AS Quantity,
            od.xlineamt AS Line_Amount
        FROM opord o
        LEFT JOIN opodt od ON o.xordernum = od.xordernum
        LEFT JOIN cacus c ON o.xcus = c.xcus
        LEFT JOIN caitem i ON od.xitem = i.xitem
        WHERE o.xsp IS NOT NULL 
          AND o.xsp != ''
          AND (o.xordernum LIKE 'IN-%' OR o.xordernum LIKE 'IN--%' 
               OR o.xordernum LIKE 'SR-%' OR o.xordernum LIKE 'SR--%')
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        return df
        
    except Exception as e:
        print(f"    [ERROR] Error extracting data: {e}")
        return pd.DataFrame()

def process_all_depots():
    """Main function"""
    print("=" * 80)
    print("FAST Product-Level Net Sales Calculator")
    print("=" * 80)
    
    # Clean up any existing databases for fresh start
    cleanup_existing_databases()
    
    # Show GUI to select folders
    gui = select_folders_gui()
    
    # Override the run_processing method to actually process
    def run_processing_impl():
        try:
            depot_folders = gui.depot_folders
            output_dir = gui.output_dir
            
            gui.log("=" * 60)
            gui.log("Starting data extraction...")
            gui.log("=" * 60)
            gui.update_progress(5, "Preparing to process depots...")
            
            depots = find_all_depots(depot_folders)
            if not depots:
                gui.log("ERROR: No valid depots found!")
                gui.update_progress(0, "Failed - No valid depots")
                messagebox.showerror("Error", "No valid depots found!")
                gui.start_btn.config(state="normal", text="▶ START PROCESSING", bg="#16a085")
                return
            
            all_data = []
            total_depots = len(depots)
            
            for i, depot in enumerate(depots, 1):
                progress = 10 + (i / total_depots * 40)  # 10-50% for data extraction
                gui.update_progress(progress, f"Processing depot {i}/{total_depots}: {depot['name']}")
                gui.log(f"\n[{i}/{total_depots}] Processing: {depot['name']}")
                
                db_name = attach_database(depot['name'], depot['mdf_file'])
                
                if db_name:
                    gui.log(f"  ✓ Database attached: {db_name}")
                    gui.log(f"  Extracting data...")
                    df = extract_sales_data(depot['name'], db_name)
                    
                    if len(df) > 0:
                        all_data.append(df)
                        sales_count = len(df[df['Transaction_Type'] == 'Sale'])
                        returns_count = len(df[df['Transaction_Type'] == 'Return'])
                        gui.log(f"  ✓ Extracted - Sales: {sales_count:,} | Returns: {returns_count:,}")
                    else:
                        gui.log(f"  ✗ No data found")
                else:
                    gui.log(f"  ✗ Failed to attach database")
            
            if not all_data:
                gui.log("\nERROR: No data extracted from any depot!")
                gui.update_progress(0, "Failed - No data extracted")
                messagebox.showerror("Error", "No data extracted!")
                gui.start_btn.config(state="normal", text="▶ START PROCESSING", bg="#16a085")
                return
            
            gui.log("\n" + "=" * 60)
            gui.log("Processing extracted data...")
            gui.log("=" * 60)
            gui.update_progress(55, "Combining data from all depots...")
            
            combined_df = pd.concat(all_data, ignore_index=True)
            
            # Add Month column
            gui.update_progress(60, "Adding Month column...")
            gui.log("[1/6] Adding Month column...")
            combined_df['Month'] = pd.to_datetime(combined_df['Invoice_Date']).dt.strftime('%Y-%m')
            
            # Create concatenated key
            gui.update_progress(65, "Creating concatenated keys...")
            gui.log("[2/6] Creating concatenated keys...")
            combined_df['CONCATENATED_KEY'] = (
                combined_df['Depot'].astype(str) + '_' +
                combined_df['MPO_Code'].astype(str) + '_' +
                combined_df['Customer_ID'].astype(str) + '_' +
                combined_df['Month'].astype(str) + '_' +
                combined_df['Product_Code'].astype(str)
            )
            
            # Separate sales and returns
            sales_df = combined_df[combined_df['Transaction_Type'] == 'Sale'].copy()
            returns_df = combined_df[combined_df['Transaction_Type'] == 'Return'].copy()
            
            gui.log(f"      Sales: {len(sales_df):,} | Returns: {len(returns_df):,}")
            
            # Group sales
            gui.update_progress(70, "Grouping sales data...")
            gui.log("[3/6] Grouping sales...")
            sales_grouped = sales_df.groupby('CONCATENATED_KEY').agg({
                'Depot': 'first',
                'MPO_Code': 'first',
                'Customer_ID': 'first',
                'Customer_Name': 'first',
                'Month': 'first',
                'Product_Code': 'first',
                'Product_Name': 'first',
                'Quantity': 'sum',
                'Line_Amount': 'sum'
            }).reset_index()
            
            sales_grouped.columns = [
                'CONCATENATED_KEY', 'Depot', 'MPO_Code', 'Customer_ID', 'Customer_Name',
                'Month', 'Product_Code', 'Product_Name', 'Sale_Qty', 'Sale_Amount'
            ]
            
            gui.log(f"      Unique keys: {len(sales_grouped):,}")
            
            # Group returns
            gui.update_progress(75, "Grouping returns data...")
            gui.log("[4/6] Grouping returns...")
            returns_grouped = returns_df.groupby('CONCATENATED_KEY').agg({
                'Depot': 'first',
                'MPO_Code': 'first',
                'Customer_ID': 'first',
                'Customer_Name': 'first',
                'Month': 'first',
                'Product_Code': 'first',
                'Product_Name': 'first',
                'Quantity': 'sum',
                'Line_Amount': 'sum'
            }).reset_index()
            
            returns_grouped.columns = [
                'CONCATENATED_KEY', 'Depot_ret', 'MPO_Code_ret', 'Customer_ID_ret', 'Customer_Name_ret',
                'Month_ret', 'Product_Code_ret', 'Product_Name_ret', 'Return_Qty', 'Return_Amount'
            ]
            
            gui.log(f"      Unique keys: {len(returns_grouped):,}")
            
            # Merge (VLOOKUP)
            gui.update_progress(80, "Matching returns to sales (VLOOKUP)...")
            gui.log("[5/6] Matching returns to sales (VLOOKUP)...")
            net_sales = pd.merge(
                sales_grouped,
                returns_grouped,
                on='CONCATENATED_KEY',
                how='outer'
            )
            
            # Fill NaN for Sales and Returns
            net_sales['Sale_Qty'] = net_sales['Sale_Qty'].fillna(0)
            net_sales['Sale_Amount'] = net_sales['Sale_Amount'].fillna(0)
            net_sales['Return_Qty'] = net_sales['Return_Qty'].fillna(0)
            net_sales['Return_Amount'] = net_sales['Return_Amount'].fillna(0)
            
            # Reconstruct missing columns using the values from returns if sales were empty
            for col in ['Depot', 'MPO_Code', 'Customer_ID', 'Customer_Name', 'Month', 'Product_Code', 'Product_Name']:
                net_sales[col] = net_sales[col].fillna(net_sales[col + '_ret'])
                
            # Drop the helper columns
            net_sales.drop(columns=[col + '_ret' for col in ['Depot', 'MPO_Code', 'Customer_ID', 'Customer_Name', 'Month', 'Product_Code', 'Product_Name']], inplace=True)
            
            # Recalculate actuals
            net_sales['ACTUAL_SALE_QTY'] = net_sales['Sale_Qty'] - net_sales['Return_Qty']
            net_sales['ACTUAL_SALE_AMOUNT'] = net_sales['Sale_Amount'] - net_sales['Return_Amount']
            net_sales['Return_Rate_%'] = (net_sales['Return_Qty'] / net_sales['Sale_Qty'] * 100).round(2).fillna(0)
            net_sales['Return_Rate_%'] = net_sales['Return_Rate_%'].replace([float('inf'), float('-inf')], 0)
            
            # Save to CSV in selected output directory
            gui.update_progress(90, "Saving to CSV file...")
            gui.log("[6/6] Saving to CSV...")
            timestamp = datetime.now().strftime('%d_%b_%Y_%I.%M_%p')
            csv_file = os.path.join(output_dir, f"01_Product_Level_Net_Sales_Extracted_Data_{timestamp}.csv")
            
            net_sales.to_csv(csv_file, index=False)
            
            file_size_mb = os.path.getsize(csv_file) / (1024 * 1024)
            gui.log(f"\n[OK] Saved File 1: {csv_file}")
            gui.log(f"  File size: {file_size_mb:.2f} MB")
            
            # Save File 2 (Daily/Detailed Raw Transactions)
            gui.update_progress(92, "Saving detailed daily CSV file...")
            gui.log("Generating File 2 (Daily/Detailed Raw Transactions)...")
            
            detailed_df = combined_df.copy()
            
            # Format datetime columns to string
            detailed_df['Invoice_Date'] = pd.to_datetime(detailed_df['Invoice_Date']).dt.strftime('%Y-%m-%d')
            detailed_df['Transaction_Time'] = pd.to_datetime(detailed_df['Transaction_Time']).dt.strftime('%Y-%m-%d %H:%M:%S.%f').str[:-3]
            
            # Clean names
            detailed_df['Customer_Name'] = detailed_df['Customer_Name'].astype(str).str.strip()
            detailed_df['Product_Name'] = detailed_df['Product_Name'].astype(str).str.strip()
            
            # Apply negative returns logic for daily transaction sheet
            detailed_df.loc[detailed_df['Transaction_Type'] == 'Return', 'Quantity'] *= -1
            detailed_df.loc[detailed_df['Transaction_Type'] == 'Return', 'Line_Amount'] *= -1
            
            # Group by transaction/invoice level detail
            detailed_grouped = detailed_df.groupby([
                'Depot', 'MPO_Code', 'Invoice_No', 'Invoice_Date', 'Transaction_Time', 
                'Transaction_Type', 'Customer_ID', 'Customer_Name', 'Product_Code', 'Product_Name', 'Month', 'CONCATENATED_KEY'
            ]).agg({
                'Quantity': 'sum',
                'Line_Amount': 'sum'
            }).reset_index()
            
            # Reorder columns
            col_order = [
                'CONCATENATED_KEY', 'Depot', 'MPO_Code', 'Invoice_No', 'Invoice_Date', 'Transaction_Time', 
                'Transaction_Type', 'Customer_ID', 'Customer_Name', 'Product_Code', 'Product_Name', 
                'Quantity', 'Line_Amount', 'Month'
            ]
            detailed_grouped = detailed_grouped[col_order]
            
            csv_file_detailed = os.path.join(output_dir, f"01.1_Date_wise_Customer_wise_Product_wise_Net_Sales_Extracted_Data_{timestamp}.csv")
            detailed_grouped.to_csv(csv_file_detailed, index=False)
            
            detailed_size_mb = os.path.getsize(csv_file_detailed) / (1024 * 1024)
            gui.log(f"[OK] Saved File 2: {csv_file_detailed}")
            gui.log(f"  File size: {detailed_size_mb:.2f} MB")
            
            # Statistics
            total_sale_qty = net_sales['Sale_Qty'].sum()
            total_return_qty = net_sales['Return_Qty'].sum()
            total_actual_qty = net_sales['ACTUAL_SALE_QTY'].sum()
            
            total_sale_amt = net_sales['Sale_Amount'].sum()
            total_return_amt = net_sales['Return_Amount'].sum()
            total_actual_amt = net_sales['ACTUAL_SALE_AMOUNT'].sum()
            
            gui.update_progress(95, "Generating summary...")
            gui.log("\n" + "=" * 60)
            gui.log("SUMMARY")
            gui.log("=" * 60)
            gui.log(f"Unique Product-Level Combinations: {len(net_sales):,}")
            gui.log(f"\nQuantity:")
            gui.log(f"  Sale Qty:       {total_sale_qty:>15,.2f}")
            gui.log(f"  Return Qty:     {total_return_qty:>15,.2f}")
            gui.log(f"  ────────────────────────────────")
            gui.log(f"  ACTUAL SALE:    {total_actual_qty:>15,.2f}")
            gui.log(f"\nAmount (BDT):")
            gui.log(f"  Sale Amount:    {total_sale_amt:>15,.2f}")
            gui.log(f"  Return Amount:  {total_return_amt:>15,.2f}")
            gui.log(f"  ────────────────────────────────")
            gui.log(f"  ACTUAL SALE:    {total_actual_amt:>15,.2f}")
            gui.log(f"  Return Rate:    {total_return_amt/total_sale_amt*100:>14.2f}%")
            
            # Depot summary
            depot_summary = net_sales.groupby('Depot').agg({
                'Sale_Amount': 'sum',
                'Return_Amount': 'sum',
                'ACTUAL_SALE_AMOUNT': 'sum'
            }).reset_index()
            depot_summary['Return_Rate_%'] = (depot_summary['Return_Amount'] / depot_summary['Sale_Amount'] * 100).round(2)
            depot_summary = depot_summary.sort_values('ACTUAL_SALE_AMOUNT', ascending=False)
            
            gui.log(f"\n" + "=" * 60)
            gui.log("Depot Summary:")
            gui.log("=" * 60)
            for _, row in depot_summary.iterrows():
                gui.log(f"{row['Depot']:12} | Sale: {row['Sale_Amount']:>12,.2f} | "
                       f"Return: {row['Return_Amount']:>10,.2f} | "
                       f"Net: {row['ACTUAL_SALE_AMOUNT']:>12,.2f} | "
                       f"Rate: {row['Return_Rate_%']:>5.2f}%")
            
            gui.update_progress(100, "✓ Processing complete!")
            gui.log("\n" + "=" * 60)
            gui.log("✓ PROCESSING COMPLETE!")
            gui.log("=" * 60)
            
            # Update button
            gui.start_btn.config(state="normal", text="CLOSE", bg="#e74c3c",
                                command=gui.root.destroy)
            
            # Show success message
            messagebox.showinfo("Success", 
                               f"Processing complete!\n\n"
                               f"File 1 saved to:\n{csv_file}\n\n"
                               f"File 2 saved to:\n{csv_file_detailed}\n\n"
                               f"Total records (File 1): {len(net_sales):,}\n"
                               f"Total records (File 2): {len(detailed_grouped):,}\n"
                               f"Net Sales: {total_actual_amt:,.2f} BDT")
        
        except Exception as e:
            gui.log(f"\nERROR: {str(e)}")
            gui.update_progress(0, "Error occurred")
            gui.start_btn.config(state="normal", text="▶ START PROCESSING", bg="#16a085")
            messagebox.showerror("Error", f"An error occurred:\n\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    # Replace the run_processing method
    gui.run_processing = run_processing_impl
    
    # Start GUI event loop
    gui.root.mainloop()

if __name__ == "__main__":
    try:
        process_all_depots()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        try:
            messagebox.showerror("Error", f"An error occurred:\n\n{str(e)}")
        except:
            pass
