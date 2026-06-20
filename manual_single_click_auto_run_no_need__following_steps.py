import os
import sys
import time
import glob
import shutil
import tkinter as tk
import pandas as pd
import requests
from datetime import datetime
from unittest.mock import patch


# Reconfigure console output encoding to prevent Windows crash on non-ASCII characters
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
    except:
        pass

import subprocess

def find_rclone_executable():
    if shutil.which("rclone"):
        return "rclone"
    common_paths = [r"C:\rclone\rclone.exe"]
    try:
        for item in os.listdir("C:\\"):
            if "rclone" in item.lower():
                full_path = os.path.join("C:\\", item, "rclone.exe")
                if os.path.exists(full_path):
                    common_paths.append(full_path)
    except:
        pass
    for path in common_paths:
        if os.path.exists(path):
            return path
    return "rclone"


# ══════════════════════════════════════════════════════════════════
#  Pipeline Execution Steps
# ══════════════════════════════════════════════════════════════════

def run_step_2():
    print("\n" + "="*60)
    print("STEP 2: Generate MPO Target vs Achievement")
    print("="*60)
    import step_2_generate_MPO_Target_vs_Achievement_report as s2
    return True

def run_step_3(root, csv_file):
    print("\n" + "="*60)
    print("STEP 3: Generate Zone Wise Product Sales Report")
    print("="*60)
    import step_3_generate_Zone_Wise_Product_Sales_Report as s3
    
    app = s3.ZoneReportApp(root)
    
    # Force step 3 to use our new CSV
    app.input_file.set(csv_file)
    
    def on_success(title, msg):
        print(f"\n  [SUCCESS] {msg.split(chr(10))[0]}")
        
    def on_error(title, msg):
        print(f"\n  [ERROR] {msg}")

    def mock_show_success_dialog(out_path):
        print(f"\n  [SUCCESS] Zone Wise Sales Report saved to: {out_path}")

    class SyncThread:
        def __init__(self, target, *args, **kwargs):
            self.target = target
        def start(self):
            self.target()

    with patch('tkinter.messagebox.showinfo', side_effect=on_success), \
         patch('tkinter.messagebox.showerror', side_effect=on_error), \
         patch('threading.Thread', SyncThread), \
         patch.object(s3.ZoneReportApp, 'show_success_dialog', mock_show_success_dialog):
         
         app.run_process()
         
    # Clean up Step 3 widgets
    for widget in root.winfo_children():
        try:
            widget.destroy()
        except:
            pass
            
    return True

def run_step_4(root, excel_file):
    print("\n" + "="*60)
    print("STEP 4: Analyze Zone Wise Report (10 Parameters)")
    print("="*60)
    import step_4_analyze_Zone_Wise_Product_Sales_Report as s4
    
    app = s4.ZoneDataAnalyzerApp(root)
    
    # Force step 4 to use the specified Excel file from Step 3
    app.input_file.set(excel_file)

    def on_success(title, msg):
        print(f"\n  [SUCCESS] {msg.split(chr(10))[0]}")
        
    def on_error(title, msg):
        print(f"\n  [ERROR] {msg}")

    def mock_show_success_dialog(out_path):
        print(f"\n  [SUCCESS] 10 Parameter Analysis saved to: {out_path}")

    class SyncThread:
        def __init__(self, target, *args, **kwargs):
            self.target = target
        def start(self):
            self.target()

    with patch('tkinter.messagebox.showinfo', side_effect=on_success), \
         patch('tkinter.messagebox.showerror', side_effect=on_error), \
         patch('threading.Thread', SyncThread), \
         patch.object(s4.ZoneDataAnalyzerApp, 'show_success_dialog', mock_show_success_dialog):
         
         app.run_process()
         
    # Clean up Step 4 widgets
    for widget in root.winfo_children():
        try:
            widget.destroy()
        except:
            pass
            
    return True

def send_pipeline_telegram_notification(base_dir, success_depots, sales_count, returns_count, timestamp):
    env_path = os.path.join(base_dir, "googleDrive", "env")
    env = {}
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        env[parts[0].strip()] = parts[1].strip()
                        
    bot_token = env.get("TELEGRAM_BOT_TOKEN")
    chat_id = env.get("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("  [Telegram] Notification skipped: Credentials not found in env.")
        return
        
    msg = f"""🚀 *ALCO PHARMA LTD. - PIPELINE REPORT* 🚀
===================================
📅 *Completed:* {datetime.now().strftime('%Y-%m-%d %I:%M %p')}
✅ *Status:* PIPELINE STEPS COMPLETED SUCCESSFULLY!
📂 *Depots Processed:* {', '.join(success_depots)} ({len(success_depots)} Depots)

📊 *Statistics:*
- Sales Transactions: {sales_count:,}
- Returns Transactions: {returns_count:,}

📁 *New Files Created:*
1. 01\_Product\_Level\_Net\_Sales\_Extracted\_Data\_{timestamp}.csv
2. 01.1\_Date\_wise\_Customer\_wise\_Product\_wise\_Net\_Sales\_Extracted\_Data\_{timestamp}.csv
3. 02A\_MPO\_Achievement\_Pivot\_Analysis\_{timestamp}.xlsx
4. 02D\_FINAL\_MPO\_Target\_vs\_Achievement\_Formula\_{timestamp}.xlsx
5. 03\_Zone\_Wise\_Sales\_Grouped\_Report\_{timestamp}.xlsx
6. 04\_Analyzed\_10\_Param\_Zone\_Wise\_Sales\_Grouped\_Report\_{timestamp}.xlsx
==================================="""
    
    import requests
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": msg,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
        print("  ✓ [Telegram] Success notification sent successfully!")
    except Exception as e:
        print(f"  [Telegram] Warning: Failed to send notification: {e}")

def generate_and_send_brand_exception_report(base_dir, combined_df, timestamp):
    summary_files = [f for f in os.listdir(base_dir) if f.startswith('02C_MPO_Matched_Targets_Summary_') and f.endswith('.xlsx')]
    summary_files.sort(reverse=True)
    if not summary_files:
        print("  [Telegram] Exception report skipped: 02C summary file not found.")
        return
        
    summary_path = os.path.join(base_dir, summary_files[0])
    try:
        df_mpo = pd.read_excel(summary_path, sheet_name='MPO_Field_Targets')
    except Exception as e:
        print(f"  [Telegram] Warning: Failed to read {summary_files[0]}: {e}")
        return
        
    sales_only = combined_df[combined_df['Transaction_Type'] == 'Sale'].copy()
    
    sales_only['is_alagra'] = sales_only['Product_Name'].str.contains('ALAGRA', case=False, na=False)
    sales_only['is_mokast'] = sales_only['Product_Name'].str.contains('MOKAST', case=False, na=False)
    
    mpo_sales = sales_only.groupby(['Depot', 'MPO_Code']).agg(
        alagra_sold=('Quantity', lambda x: x[sales_only.loc[x.index, 'is_alagra']].sum()),
        mokast_sold=('Quantity', lambda x: x[sales_only.loc[x.index, 'is_mokast']].sum())
    ).reset_index()
    
    df_mpo['MPO CODE'] = df_mpo['MPO CODE'].astype(str).str.strip().str.upper()
    df_mpo['DEPOT'] = df_mpo['DEPOT'].astype(str).str.strip().str.upper()
    
    mpo_sales['MPO_Code'] = mpo_sales['MPO_Code'].astype(str).str.strip().str.upper()
    mpo_sales['Depot'] = mpo_sales['Depot'].astype(str).str.strip().str.upper()
    
    merged = pd.merge(
        df_mpo, 
        mpo_sales, 
        left_on=['DEPOT', 'MPO CODE'], 
        right_on=['Depot', 'MPO_Code'], 
        how='left'
    )
    
    merged['alagra_sold'] = merged['alagra_sold'].fillna(0)
    merged['mokast_sold'] = merged['mokast_sold'].fillna(0)
    
    exceptions = merged[(merged['alagra_sold'] == 0) | (merged['mokast_sold'] == 0)].copy()
    
    if len(exceptions) == 0:
        print("  [Telegram] No sales exceptions found for ALAGRA/MOKAST.")
        return
        
    exceptions = exceptions.sort_values(by=['DEPOT', 'FM/AM, ZONE', 'MPO CODE'])
    
    msg_lines = [
        "🚨 *ALCO PHARMA - SALES EXCEPTION REPORT* 🚨",
        "=========================================",
        f"📅 *Report Date:* {datetime.now().strftime('%d-%b-%Y')}",
        "💊 *Target Brands:* ALAGRA & MOKAST (Zero Sales Alert)",
        "",
        "The following MPOs have *ZERO* sales for ALAGRA or MOKAST in the processed data:",
        "-----------------------------------------"
    ]
    
    count = 0
    max_display = 15
    for idx, row in exceptions.iterrows():
        count += 1
        if count > max_display:
            msg_lines.append(f"⚠️ *...and {len(exceptions) - max_display} more exceptions. See detailed CSV.*")
            break
            
        depot = row['DEPOT']
        zone = row['ZONE']
        fm = row['FM/AM, ZONE']
        mpo = row['MPO CODE']
        market = row['MARKET']
        alagra = int(row['alagra_sold'])
        mokast = int(row['mokast_sold'])
        
        status_alagra = "❌ ZERO SALE" if alagra == 0 else f"{alagra:,} Sold"
        status_mokast = "❌ ZERO SALE" if mokast == 0 else f"{mokast:,} Sold"
        
        msg_lines.append(f"📍 *Depot:* {depot} ({zone})")
        msg_lines.append(f"👤 *FM:* {fm}")
        msg_lines.append(f"🔑 *MPO:* {mpo} ({market})")
        msg_lines.append(f"   ▪️ ALAGRA: {status_alagra}")
        msg_lines.append(f"   ▪️ MOKAST: {status_mokast}")
        msg_lines.append("")
        
    msg_lines.append("=========================================")
    msg_lines.append(f"📈 *SUMMARY:*")
    msg_lines.append(f"- Total MPOs with exceptions: *{len(exceptions)}*")
    msg_lines.append(f"- Zero ALAGRA sales: *{len(exceptions[exceptions['alagra_sold'] == 0])} MPOs*")
    msg_lines.append(f"- Zero MOKAST sales: *{len(exceptions[exceptions['mokast_sold'] == 0])} MPOs*")
    msg_lines.append("=========================================")
    
    msg_text = "\n".join(msg_lines)
    
    env_path = os.path.join(base_dir, "googleDrive", "env")
    env = {}
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        env[parts[0].strip()] = parts[1].strip()
                        
    bot_token = env.get("TELEGRAM_BOT_TOKEN")
    chat_id = env.get("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        return
        
    import requests
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": msg_text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=15).raise_for_status()
        print("  ✓ [Telegram] Exception report sent successfully!")
    except Exception as e:
        print(f"  [Telegram] Warning: Failed to send exception report: {e}")

# ══════════════════════════════════════════════════════════════════
#  Main Orchestrator
# ══════════════════════════════════════════════════════════════════

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    print("*" * 80)
    print("  MANUAL SALES DATA EXTRACTOR & ANALYZER - LOAD FROM SAVED RAW CSV")
    print("*" * 80)
    
    extracted_all_data_parent = os.path.join(base_dir, "Extracted All Data")
    if not os.path.exists(extracted_all_data_parent):
        print(f"ERROR: Parent directory '{extracted_all_data_parent}' does not exist!")
        print("Please run the auto script at least once, or create this folder manually and put raw CSV files in it.")
        return

    # Find latest extracted_* folder
    subfolders = [f for f in glob.glob(os.path.join(extracted_all_data_parent, "extracted_*")) if os.path.isdir(f)]
    if not subfolders:
        print(f"ERROR: No extracted_* folder found under {extracted_all_data_parent}!")
        return

    # Sort subfolders to get the latest one
    subfolders.sort(key=os.path.getmtime, reverse=True)
    latest_folder = subfolders[0]
    print(f"\nFound latest raw CSV folder: {os.path.basename(latest_folder)}")
    
    csv_files = glob.glob(os.path.join(latest_folder, "*.csv"))
    if not csv_files:
        print(f"ERROR: No CSV files found inside {latest_folder}!")
        return

    print(f"Found {len(csv_files)} depot CSV files to combine.")
    
    all_data = []
    success_depots = []
    for csv_file_path in csv_files:
        depot_name = os.path.splitext(os.path.basename(csv_file_path))[0]
        try:
            df = pd.read_csv(csv_file_path)
            if len(df) > 0:
                all_data.append(df)
                success_depots.append(depot_name)
                print(f"  ✓ Loaded {len(df):,} records for {depot_name}")
        except Exception as e:
            print(f"  [ERROR] Failed to load {csv_file_path}: {e}")

    if not all_data:
        print("\nERROR: No data loaded. Pipeline stopping.")
        return
        
    # ──────────────────────────────────────────────────────────
    # Combine and perform exact OUTER merge (avoiding returns loss)
    # ──────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("COMBINING AND PROCESSING ALL SAVED RAW DATA")
    print("=" * 60)
    
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Add Month column
    combined_df['Month'] = pd.to_datetime(combined_df['Invoice_Date']).dt.strftime('%Y-%m')
    
    # Create concatenated key
    combined_df['CONCATENATED_KEY'] = (
        combined_df['Depot'].astype(str) + '_' +
        combined_df['MPO_Code'].astype(str) + '_' +
        combined_df['Customer_ID'].astype(str) + '_' +
        combined_df['Month'].astype(str) + '_' +
        combined_df['Product_Code'].astype(str)
    )
    
    sales_df = combined_df[combined_df['Transaction_Type'] == 'Sale'].copy()
    returns_df = combined_df[combined_df['Transaction_Type'] == 'Return'].copy()
    
    print(f"Total Combined Sales: {len(sales_df):,} | Returns: {len(returns_df):,}")
    
    # Group sales
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
    
    # Group returns
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
    
    # Merge using how='outer' to prevent return loss
    net_sales = pd.merge(sales_grouped, returns_grouped, on='CONCATENATED_KEY', how='outer')
    
    # Fill NaN and calculate
    net_sales['Sale_Qty'] = net_sales['Sale_Qty'].fillna(0)
    net_sales['Sale_Amount'] = net_sales['Sale_Amount'].fillna(0)
    net_sales['Return_Qty'] = net_sales['Return_Qty'].fillna(0)
    net_sales['Return_Amount'] = net_sales['Return_Amount'].fillna(0)
    
    # Reconstruct metadata columns from returns if sales were empty
    for col in ['Depot', 'MPO_Code', 'Customer_ID', 'Customer_Name', 'Month', 'Product_Code', 'Product_Name']:
        net_sales[col] = net_sales[col].fillna(net_sales[col + '_ret'])
        
    # Drop helper columns
    net_sales.drop(columns=[col + '_ret' for col in ['Depot', 'MPO_Code', 'Customer_ID', 'Customer_Name', 'Month', 'Product_Code', 'Product_Name']], inplace=True)
    
    net_sales['ACTUAL_SALE_QTY'] = net_sales['Sale_Qty'] - net_sales['Return_Qty']
    net_sales['ACTUAL_SALE_AMOUNT'] = net_sales['Sale_Amount'] - net_sales['Return_Amount']
    net_sales['Return_Rate_%'] = (net_sales['Return_Qty'] / net_sales['Sale_Qty'] * 100).round(2).fillna(0)
    net_sales['Return_Rate_%'] = net_sales['Return_Rate_%'].replace([float('inf'), float('-inf')], 0)
    
    timestamp = datetime.now().strftime('%d_%b_%Y_%I.%M_%p')
    csv_file = os.path.join(base_dir, f"01_Product_Level_Net_Sales_Extracted_Data_{timestamp}.csv")
    net_sales.to_csv(csv_file, index=False)
    print(f"\n[SAVED FILE 1] {csv_file}")
    
    # Save Detailed (Detailed Raw Transactions)
    detailed_df = combined_df.copy()
    detailed_df['Invoice_Date'] = pd.to_datetime(detailed_df['Invoice_Date']).dt.strftime('%Y-%m-%d')
    detailed_df['Transaction_Time'] = pd.to_datetime(detailed_df['Transaction_Time']).dt.strftime('%Y-%m-%d %H:%M:%S.%f').str[:-3]
    detailed_df['Customer_Name'] = detailed_df['Customer_Name'].astype(str).str.strip()
    detailed_df['Product_Name'] = detailed_df['Product_Name'].astype(str).str.strip()
    
    # Format returns with negative quantities/amounts for invoice view
    detailed_df.loc[detailed_df['Transaction_Type'] == 'Return', 'Quantity'] *= -1
    detailed_df.loc[detailed_df['Transaction_Type'] == 'Return', 'Line_Amount'] *= -1
    
    detailed_grouped = detailed_df.groupby([
        'Depot', 'MPO_Code', 'Invoice_No', 'Invoice_Date', 'Transaction_Time', 
        'Transaction_Type', 'Customer_ID', 'Customer_Name', 'Product_Code', 'Product_Name', 'Month', 'CONCATENATED_KEY'
    ]).agg({
        'Quantity': 'sum',
        'Line_Amount': 'sum'
    }).reset_index()
    
    # Place CONCATENATED_KEY as the very first column
    col_order = [
        'CONCATENATED_KEY', 'Depot', 'MPO_Code', 'Invoice_No', 'Invoice_Date', 'Transaction_Time', 
        'Transaction_Type', 'Customer_ID', 'Customer_Name', 'Product_Code', 'Product_Name', 
        'Quantity', 'Line_Amount', 'Month'
    ]
    detailed_grouped = detailed_grouped[col_order]
    
    csv_file_detailed = os.path.join(base_dir, f"01.1_Date_wise_Customer_wise_Product_wise_Net_Sales_Extracted_Data_{timestamp}.csv")
    detailed_grouped.to_csv(csv_file_detailed, index=False)
    print(f"[SAVED FILE 2] {csv_file_detailed}")
    
    # ── CLOUD API UPLOAD OR SQLITE DATABASE FALLBACK ──
    try:
        mpo_code_xlsx = os.path.join(base_dir, "archive", "recent", "mpo_code.xlsx")
        if os.path.exists(mpo_code_xlsx):
            print("Enriching sales data with MPO mappings...")
            df_mpo = pd.read_excel(mpo_code_xlsx)
            df_mpo_temp = df_mpo.copy()
            df_mpo_temp.rename(columns={'DEPOT': 'DEPOT_mpo', 'MPO CODE': 'MPO_CODE_mpo'}, inplace=True)
            
            # Merge
            df_merged = pd.merge(
                detailed_grouped, 
                df_mpo_temp, 
                left_on=['Depot', 'MPO_Code'], 
                right_on=['DEPOT_mpo', 'MPO_CODE_mpo'], 
                how='left'
            )
            
            # Fallback depot to zone
            depot_to_zone = df_mpo.groupby('DEPOT')['ZONE'].first().to_dict()
            df_merged['ZONE'] = df_merged['ZONE'].fillna(df_merged['Depot'].map(depot_to_zone))
            
            # Drop helper columns
            df_merged.drop(columns=['DEPOT_mpo', 'MPO_CODE_mpo'], errors='ignore', inplace=True)
        else:
            print("⚠ Warning: mpo_code.xlsx not found. Processing raw detailed data without mapping.")
            df_merged = detailed_grouped.copy()

        # Load environment credentials for cloud upload
        def load_env_local(e_path):
            ev = {}
            if os.path.exists(e_path):
                with open(e_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            parts = line.split('=', 1)
                            if len(parts) == 2:
                                ev[parts[0].strip()] = parts[1].strip()
            return ev

        env_path = os.path.join(base_dir, "googleDrive", "env")
        env = load_env_local(env_path)
        
        api_gateway_url = env.get("API_GATEWAY_URL")
        api_key = env.get("API_KEY", "alco_secure_api_key_2026")
        
        uploaded_to_cloud = False
        if api_gateway_url:
            try:
                print("\n" + "="*60)
                print("UPLOADING SALES DATA TO CLOUD API GATEWAY")
                print("="*60)
                
                # Format records for API
                df_api = df_merged.copy()
                df_api.rename(columns={
                    'CONCATENATED_KEY': 'concatenated_key',
                    'Depot': 'depot',
                    'MPO_Code': 'mpo_code',
                    'Invoice_No': 'invoice_no',
                    'Invoice_Date': 'invoice_date',
                    'Transaction_Time': 'transaction_time',
                    'Transaction_Type': 'transaction_type',
                    'Customer_ID': 'customer_id',
                    'Customer_Name': 'customer_name',
                    'Product_Code': 'product_code',
                    'Product_Name': 'product_name',
                    'Quantity': 'quantity',
                    'Line_Amount': 'line_amount',
                    'Month': 'month',
                    'ZONE': 'zone',
                    'MARKET': 'market',
                    'FM/AM': 'fm_am'
                }, inplace=True)
                
                # Convert timestamps and dates to strings
                for col in ['invoice_date', 'transaction_time']:
                    if col in df_api.columns:
                        df_api[col] = df_api[col].astype(str)
                        
                records = df_api.to_dict(orient='records')
                total_records = len(records)
                batch_size = 5000
                
                print(f"Streaming {total_records:,} records to Aiven PostgreSQL in batches of {batch_size}...")
                headers = {
                    "X-API-Key": api_key,
                    "Content-Type": "application/json"
                }
                
                for idx in range(0, total_records, batch_size):
                    batch = records[idx:idx+batch_size]
                    res = requests.post(
                        f"{api_gateway_url.rstrip('/')}/upload/sales", 
                        json=batch, 
                        headers=headers, 
                        timeout=90
                    )
                    res.raise_for_status()
                    print(f"  ✓ Uploaded records {idx:,} to {min(idx+batch_size, total_records):,}")
                    
                print("✓ [SUCCESS] All records uploaded to Aiven PostgreSQL cloud database!")
                uploaded_to_cloud = True
            except Exception as api_err:
                print(f"⚠ Warning: Cloud API Gateway upload failed: {api_err}")
                print("Falling back to local SQLite generation...")
                
        if not uploaded_to_cloud:
            print("\n" + "="*60)
            print("GENERATING LOCAL SQLITE DATABASE & UPLOADING TO GOOGLE DRIVE")
            print("="*60)
            
            # Write to SQLite
            import sqlite3
            sqlite_path = os.path.join(base_dir, "sales.db")
            if os.path.exists(sqlite_path):
                try:
                    os.remove(sqlite_path)
                except Exception as ex:
                    print(f"  Could not remove old sales.db: {ex}")
                    
            print(f"Writing {len(df_merged):,} records to SQLite (with normalized lowercase columns)...")
            
            # Format columns to lowercase for database compatibility
            df_sqlite = df_merged.copy()
            df_sqlite.rename(columns={
                'CONCATENATED_KEY': 'concatenated_key',
                'Depot': 'depot',
                'MPO_Code': 'mpo_code',
                'Invoice_No': 'invoice_no',
                'Invoice_Date': 'invoice_date',
                'Transaction_Time': 'transaction_time',
                'Transaction_Type': 'transaction_type',
                'Customer_ID': 'customer_id',
                'Customer_Name': 'customer_name',
                'Product_Code': 'product_code',
                'Product_Name': 'product_name',
                'Quantity': 'quantity',
                'Line_Amount': 'line_amount',
                'Month': 'month',
                'ZONE': 'zone',
                'MARKET': 'market',
                'FM/AM': 'fm_am'
            }, inplace=True)
            
            conn = sqlite3.connect(sqlite_path)
            df_sqlite.to_sql("sales", conn, if_exists="replace", index=False)
            
            # Create indexes
            print("Creating indexes on SQLite table...")
            cursor = conn.cursor()
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_depot ON sales (depot)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_month ON sales (month)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_product ON sales (product_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_mpo ON sales (mpo_code)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_zone ON sales (zone)")
            conn.commit()
            conn.close()
            print("✓ SQLite database generated successfully.")
            
            # Upload using rclone
            rclone_exe = find_rclone_executable()
            parent_folder_id = "1fRl-N_fNU_bJfkxH9a_EYLJeHPB43gzv"
            remote_path = f"grive_new,root_folder_id={parent_folder_id}:sales.db"
            
            print(f"Uploading sales.db to Google Drive...")
            upload_cmd = [rclone_exe, "copyto", "--progress", sqlite_path, remote_path]
            subprocess.run(upload_cmd, check=True)
            print("✓ [SUCCESS] SQLite database uploaded to Google Drive successfully!")
    except Exception as e:
        print(f"❌ Error during database processing: {e}")
        
    print(f"\nSuccessfully combined depots: {', '.join(success_depots)}")
    
    print("\nWaiting 5 seconds before next step...")
    time.sleep(5)
    
    # ──────────────────────────────────────────────────────────
    # Run Steps 2, 3, and 4
    # ──────────────────────────────────────────────────────────
    
    # Run Step 2 (Generate MPO Report)
    # Patch glob.glob inside step 2 script to return our newly created CSV instead of globbing
    with patch('glob.glob', return_value=[csv_file]):
        run_step_2()
        
    print("\nWaiting 5 seconds before next step...")
    time.sleep(5)
    
    # Create hidden TKinter root window for Step 3 & 4 GUI apps
    root = tk.Tk()
    root.withdraw()
    
    # Run Step 3 (Zone Wise Sales Report)
    if not run_step_3(root, csv_file):
        print("\nPipeline stopped at Step 3.")
        root.destroy()
        return
        
    print("\nWaiting 5 seconds before next step...")
    time.sleep(5)
    
    # Find latest zone report file from Step 3
    zone_files = [f for f in os.listdir(base_dir) if f.startswith('03_Zone_Wise_Sales_Grouped_Report_') and f.endswith('.xlsx')]
    zone_files.sort(reverse=True)
    if zone_files:
        latest_zone_path = os.path.join(base_dir, zone_files[0])
        # Run Step 4 (10 Parameter Analyzed Report)
        if not run_step_4(root, latest_zone_path):
            print("\nPipeline stopped at Step 4.")
            root.destroy()
            return
    else:
        print("Error: Could not find Step 3 Excel output to run Step 4!")
        
    root.destroy()
    
    print("\n" + "*" * 80)
    print("  MANUAL RUN PIPELINE STEPS COMPLETED SUCCESSFULLY!")
    print("*" * 80)
    
    send_pipeline_telegram_notification(base_dir, success_depots, len(sales_df), len(returns_df), timestamp)
    
    print("\nGenerating and sending ALAGRA & MOKAST Exception Report to Telegram...")
    generate_and_send_brand_exception_report(base_dir, combined_df, timestamp)

if __name__ == "__main__":
    main()
