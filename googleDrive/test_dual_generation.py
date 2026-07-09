import os
import pyodbc
import pandas as pd
import subprocess
from datetime import datetime

def grant_sql_server_permissions(folder_path):
    try:
        accounts = [
            'NT SERVICE\\MSSQL$SQLEXPRESS',
            'NT SERVICE\\MSSQLSERVER',
            'NT AUTHORITY\\NETWORK SERVICE',
            'NT AUTHORITY\\SYSTEM'
        ]
        for account in accounts:
            try:
                cmd = f'icacls "{folder_path}" /grant "{account}:(OI)(CI)F" /T /Q'
                subprocess.run(cmd, shell=True, capture_output=True, timeout=10)
            except:
                pass
    except Exception as e:
        print(f"Warning: Permissions check failed: {e}")

def main():
    server = r'.\SQLEXPRESS'
    db_name = 'TEMP_TEST_DUAL_DB'
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    barishal_temp_data = os.path.join(project_dir, 'Barishal_Temp', 'Data')
    mdf_path = os.path.join(barishal_temp_data, 'ERPonTheNet_Data.MDF')
    ldf_path = os.path.join(barishal_temp_data, 'ERPonTheNet_log.LDF')
    
    if not os.path.exists(mdf_path):
        print(f"File not found: {mdf_path}")
        return
        
    mdf_path = os.path.normpath(mdf_path)
    ldf_path = os.path.normpath(ldf_path)
    
    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE=master;Trusted_Connection=yes;'
    try:
        conn = pyodbc.connect(conn_str)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database already exists, if so drop/detach it
        cursor.execute(f"SELECT database_id FROM sys.databases WHERE name = '{db_name}'")
        row = cursor.fetchone()
        if row:
            print("Database already exists, detaching...")
            try:
                cursor.execute(f"ALTER DATABASE [{db_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
                cursor.execute(f"EXEC sp_detach_db '{db_name}', 'true'")
            except Exception as e:
                print(f"Error detaching: {e}")
                
        # Grant permissions
        grant_sql_server_permissions(os.path.dirname(mdf_path))
        
        # Attach database
        print(f"Attaching {db_name}...")
        attach_query = f"""
        CREATE DATABASE [{db_name}] ON 
        (FILENAME = N'{mdf_path}'),
        (FILENAME = N'{ldf_path}')
        FOR ATTACH;
        """
        cursor.execute(attach_query)
        print("Attached successfully!")
        
        # Extract Query
        query = f"""
        SELECT 
            'BARISHAL' AS Depot,
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
        FROM [{db_name}].dbo.opord o
        LEFT JOIN [{db_name}].dbo.opodt od ON o.xordernum = od.xordernum
        LEFT JOIN [{db_name}].dbo.cacus c ON o.xcus = c.xcus
        LEFT JOIN [{db_name}].dbo.caitem i ON od.xitem = i.xitem
        WHERE o.xsp IS NOT NULL 
          AND o.xsp != ''
          AND (o.xordernum LIKE 'IN-%' OR o.xordernum LIKE 'IN--%' 
               OR o.xordernum LIKE 'SR-%' OR o.xordernum LIKE 'SR--%')
        """
        print("Extracting sales data from SQL Server...")
        df_raw = pd.read_sql(query, conn)
        print(f"Extracted {len(df_raw)} raw database records.")
        
        # ──────────────────────────────────────────────────────────
        # GENERATE FILE 1: Monthly Grouped (Existing Workflow Format)
        # ──────────────────────────────────────────────────────────
        print("\nGenerating File 1 (Monthly Grouped)...")
        combined_df = df_raw.copy()
        combined_df['Month'] = pd.to_datetime(combined_df['Invoice_Date']).dt.strftime('%Y-%m')
        
        combined_df['CONCATENATED_KEY'] = (
            combined_df['Depot'].astype(str) + '_' +
            combined_df['MPO_Code'].astype(str) + '_' +
            combined_df['Customer_ID'].astype(str) + '_' +
            combined_df['Month'].astype(str) + '_' +
            combined_df['Product_Code'].astype(str)
        )
        
        sales_df = combined_df[combined_df['Transaction_Type'] == 'Sale'].copy()
        returns_df = combined_df[combined_df['Transaction_Type'] == 'Return'].copy()
        
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
        
        returns_grouped = returns_df.groupby('CONCATENATED_KEY').agg({
            'Quantity': 'sum',
            'Line_Amount': 'sum'
        }).reset_index()
        returns_grouped.columns = ['CONCATENATED_KEY', 'Return_Qty', 'Return_Amount']
        
        net_sales = pd.merge(sales_grouped, returns_grouped, on='CONCATENATED_KEY', how='left')
        net_sales['Return_Qty'] = net_sales['Return_Qty'].fillna(0)
        net_sales['Return_Amount'] = net_sales['Return_Amount'].fillna(0)
        net_sales['ACTUAL_SALE_QTY'] = net_sales['Sale_Qty'] - net_sales['Return_Qty']
        net_sales['ACTUAL_SALE_AMOUNT'] = net_sales['Sale_Amount'] - net_sales['Return_Amount']
        net_sales['Return_Rate_%'] = (net_sales['Return_Qty'] / net_sales['Sale_Qty'] * 100).round(2)
        
        f1_path = os.path.join(project_dir, '01_Product_Level_Net_Sales_Extracted_Data_TEST.csv')
        net_sales.to_csv(f1_path, index=False)
        print(f"[SUCCESS] Saved File 1: {f1_path} (Rows: {len(net_sales)}, Size: {os.path.getsize(f1_path)/1024:.2f} KB)")
        
        # ──────────────────────────────────────────────────────────
        # GENERATE FILE 2: Daily/Detailed Raw Transactions (The New File)
        # ──────────────────────────────────────────────────────────
        print("\nGenerating File 2 (Daily/Detailed Raw Transactions)...")
        detailed_df = df_raw.copy()
        
        # Convert datetime columns to string for clean output format
        detailed_df['Invoice_Date'] = pd.to_datetime(detailed_df['Invoice_Date']).dt.strftime('%Y-%m-%d')
        # Format transaction time to YYYY-MM-DD HH:MM:SS.fff
        detailed_df['Transaction_Time'] = pd.to_datetime(detailed_df['Transaction_Time']).dt.strftime('%Y-%m-%d %H:%M:%S.%f').str[:-3]
        detailed_df['Month'] = pd.to_datetime(detailed_df['Invoice_Date']).dt.strftime('%Y-%m')
        
        # Clean Customer Names
        detailed_df['Customer_Name'] = detailed_df['Customer_Name'].astype(str).str.strip()
        detailed_df['Product_Name'] = detailed_df['Product_Name'].astype(str).str.strip()
        
        # Group by transaction/invoice level detail
        detailed_grouped = detailed_df.groupby([
            'Depot', 'MPO_Code', 'Invoice_No', 'Invoice_Date', 'Transaction_Time', 
            'Transaction_Type', 'Customer_ID', 'Customer_Name', 'Product_Code', 'Product_Name', 'Month'
        ]).agg({
            'Quantity': 'sum',
            'Line_Amount': 'sum'
        }).reset_index()
        
        # Order columns nicely
        col_order = [
            'Depot', 'MPO_Code', 'Invoice_No', 'Invoice_Date', 'Transaction_Time', 
            'Transaction_Type', 'Customer_ID', 'Customer_Name', 'Product_Code', 'Product_Name', 
            'Quantity', 'Line_Amount', 'Month'
        ]
        detailed_grouped = detailed_grouped[col_order]
        
        f2_path = os.path.join(project_dir, '01.1_Date_wise_Customer_wise_Product_wise_Net_Sales_Extracted_Data_TEST.csv')
        detailed_grouped.to_csv(f2_path, index=False)
        print(f"[SUCCESS] Saved File 2: {f2_path} (Rows: {len(detailed_grouped)}, Size: {os.path.getsize(f2_path)/1024:.2f} KB)")
        
        # Detach
        print("\nDetaching database...")
        cursor.execute(f"ALTER DATABASE [{db_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
        cursor.execute(f"EXEC sp_detach_db '{db_name}', 'true'")
        print("Detached successfully!")
        
        conn.close()
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    main()
