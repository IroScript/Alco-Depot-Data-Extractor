# Product-Level Net Sales Calculation
# Matches returns to sales at: Depot + MPO + Customer + Month + Product level

import pyodbc
import pandas as pd
import os
from datetime import datetime

# Configuration
ALL_DEPOTS_FOLDER = r"C:\Users\Irak\Desktop\Barishal April Data\All_Depots"
SQL_SERVER = r'.\SQLEXPRESS'

def find_all_depots():
    """Find all depot folders"""
    print(f"\nScanning for depots in: {ALL_DEPOTS_FOLDER}")
    
    if not os.path.exists(ALL_DEPOTS_FOLDER):
        print(f"  Error: Folder not found: {ALL_DEPOTS_FOLDER}")
        return []
    
    depots = []
    
    for depot_folder in os.listdir(ALL_DEPOTS_FOLDER):
        depot_path = os.path.join(ALL_DEPOTS_FOLDER, depot_folder)
        
        if os.path.isdir(depot_path):
            data_folder = os.path.join(depot_path, 'Data')
            
            if os.path.exists(data_folder):
                erp_mdf = None
                for file in os.listdir(data_folder):
                    if file.lower() == 'erponthenet_data.mdf':
                        erp_mdf = os.path.join(data_folder, file)
                        break
                
                if erp_mdf:
                    depots.append({
                        'name': depot_folder,
                        'path': depot_path,
                        'data_folder': data_folder,
                        'mdf_file': erp_mdf
                    })
                    print(f"  Found: {depot_folder}")
    
    print(f"\nTotal depots found: {len(depots)}")
    return depots

def attach_database(depot_name, mdf_path):
    """Attach MDF file to SQL Server"""
    try:
        mdf_dir = os.path.dirname(mdf_path)
        
        ldf_path = None
        for file in os.listdir(mdf_dir):
            if file.lower() == 'erponthenet_log.ldf':
                ldf_path = os.path.join(mdf_dir, file)
                break
        
        db_name = f"{depot_name}_DB"
        
        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SQL_SERVER};DATABASE=master;Trusted_Connection=yes;'
        conn = pyodbc.connect(conn_str)
        conn.autocommit = True
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT name FROM sys.databases WHERE name = '{db_name}'")
        if cursor.fetchone():
            print(f"    ✓ Database '{db_name}' already attached")
            conn.close()
            return db_name
        
        if ldf_path and os.path.exists(ldf_path):
            attach_query = f"""
            CREATE DATABASE [{db_name}] ON 
            (FILENAME = N'{mdf_path}'),
            (FILENAME = N'{ldf_path}')
            FOR ATTACH;
            """
            print(f"    Attaching with log file...")
        else:
            attach_query = f"""
            CREATE DATABASE [{db_name}] ON 
            (FILENAME = N'{mdf_path}')
            FOR ATTACH_REBUILD_LOG;
            """
            print(f"    Attaching and rebuilding log...")
        
        cursor.execute(attach_query)
        print(f"    ✓ Attached: {db_name}")
        
        conn.close()
        return db_name
        
    except Exception as e:
        print(f"    ✗ Error attaching: {e}")
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
            CASE 
                WHEN o.xordernum LIKE 'IN-%' OR o.xordernum LIKE 'IN--%' THEN 'Sale'
                WHEN o.xordernum LIKE 'SR-%' OR o.xordernum LIKE 'SR--%' THEN 'Return'
                ELSE 'Other'
            END AS Transaction_Type,
            o.xstatusord AS Status,
            o.xcus AS Customer_ID,
            LTRIM(RTRIM(c.xorg)) AS Customer_Name,
            od.xitem AS Product_Code,
            i.xdesc AS Product_Name,
            od.xqtyord AS Quantity,
            od.xprice AS Unit_Price,
            od.xlineamt AS Line_Amount
        FROM opord o
        LEFT JOIN opodt od ON o.xordernum = od.xordernum
        LEFT JOIN cacus c ON o.xcus = c.xcus
        LEFT JOIN caitem i ON od.xitem = i.xitem
        WHERE o.xsp IS NOT NULL 
          AND o.xsp != ''
          AND (o.xordernum LIKE 'IN-%' OR o.xordernum LIKE 'IN--%' 
               OR o.xordernum LIKE 'SR-%' OR o.xordernum LIKE 'SR--%')
        ORDER BY o.xcus, o.xdate
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        return df
        
    except Exception as e:
        print(f"    ✗ Error extracting data: {e}")
        return pd.DataFrame()

def calculate_product_level_net_sales(df):
    """
    Calculate net sales at product level using concatenated key
    Key = Depot_MPO_CustomerID_Month_ProductCode
    """
    
    print("\n  Creating concatenated keys...")
    
    # Add Month column
    df['Month'] = pd.to_datetime(df['Invoice_Date']).dt.strftime('%Y-%m')
    
    # Create concatenated key: Depot_MPO_CustomerID_Month_ProductCode
    df['CONCATENATED_KEY'] = (
        df['Depot'].astype(str) + '_' +
        df['MPO_Code'].astype(str) + '_' +
        df['Customer_ID'].astype(str) + '_' +
        df['Month'].astype(str) + '_' +
        df['Product_Code'].astype(str)
    )
    
    # Separate sales and returns
    sales_df = df[df['Transaction_Type'] == 'Sale'].copy()
    returns_df = df[df['Transaction_Type'] == 'Return'].copy()
    
    print(f"  Sales records: {len(sales_df):,}")
    print(f"  Return records: {len(returns_df):,}")
    
    # Group sales by concatenated key
    print("\n  Grouping sales by key...")
    sales_grouped = sales_df.groupby('CONCATENATED_KEY').agg({
        'Depot': 'first',
        'MPO_Code': 'first',
        'Customer_ID': 'first',
        'Customer_Name': 'first',
        'Month': 'first',
        'Product_Code': 'first',
        'Product_Name': 'first',
        'Quantity': 'sum',
        'Line_Amount': 'sum',
        'Invoice_No': 'nunique'
    }).reset_index()
    
    sales_grouped.columns = [
        'CONCATENATED_KEY', 'Depot', 'MPO_Code', 'Customer_ID', 'Customer_Name',
        'Month', 'Product_Code', 'Product_Name', 'Sale_Qty', 'Sale_Amount', 'Sale_Invoices'
    ]
    
    print(f"  Unique sales keys: {len(sales_grouped):,}")
    
    # Group returns by concatenated key
    print("  Grouping returns by key...")
    returns_grouped = returns_df.groupby('CONCATENATED_KEY').agg({
        'Quantity': 'sum',
        'Line_Amount': 'sum',
        'Invoice_No': 'nunique'
    }).reset_index()
    
    returns_grouped.columns = ['CONCATENATED_KEY', 'Return_Qty', 'Return_Amount', 'Return_Invoices']
    
    print(f"  Unique return keys: {len(returns_grouped):,}")
    
    # Merge (VLOOKUP equivalent)
    print("\n  Matching returns to sales (VLOOKUP)...")
    net_sales = pd.merge(
        sales_grouped,
        returns_grouped,
        on='CONCATENATED_KEY',
        how='left'
    )
    
    # Fill NaN with 0 for products with no returns
    net_sales['Return_Qty'] = net_sales['Return_Qty'].fillna(0)
    net_sales['Return_Amount'] = net_sales['Return_Amount'].fillna(0)
    net_sales['Return_Invoices'] = net_sales['Return_Invoices'].fillna(0).astype(int)
    
    # Calculate ACTUAL SALE (Net Sale)
    net_sales['ACTUAL_SALE_QTY'] = net_sales['Sale_Qty'] - net_sales['Return_Qty']
    net_sales['ACTUAL_SALE_AMOUNT'] = net_sales['Sale_Amount'] - net_sales['Return_Amount']
    
    # Calculate return rate
    net_sales['Return_Rate_%'] = (net_sales['Return_Qty'] / net_sales['Sale_Qty'] * 100).round(2)
    
    print(f"  ✓ Net sales calculated for {len(net_sales):,} unique combinations")
    
    return df, sales_df, returns_df, sales_grouped, returns_grouped, net_sales

def process_all_depots():
    """Main function"""
    print("=" * 80)
    print("Product-Level Net Sales Calculator")
    print("Matching: Depot + MPO + Customer + Month + Product")
    print("=" * 80)
    
    depots = find_all_depots()
    if not depots:
        print("\nNo depots found. Exiting.")
        return
    
    all_data = []
    
    for i, depot in enumerate(depots, 1):
        print(f"\n[{i}/{len(depots)}] Processing: {depot['name']}")
        print("-" * 80)
        
        db_name = attach_database(depot['name'], depot['mdf_file'])
        
        if db_name:
            print(f"  Extracting data...")
            df = extract_sales_data(depot['name'], db_name)
            
            if len(df) > 0:
                all_data.append(df)
                sales_count = len(df[df['Transaction_Type'] == 'Sale'])
                returns_count = len(df[df['Transaction_Type'] == 'Return'])
                print(f"  ✓ Sales: {sales_count:,} | Returns: {returns_count:,}")
            else:
                print(f"  ✗ No data found")
        else:
            print(f"  ✗ Failed to attach database")
    
    if all_data:
        print("\n" + "=" * 80)
        print("Calculating Product-Level Net Sales")
        print("=" * 80)
        
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Calculate product-level net sales
        all_df, sales_df, returns_df, sales_grouped, returns_grouped, net_sales = calculate_product_level_net_sales(combined_df)
        
        # Create output filename
        base_name = "Product_Level_Net_Sales"
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"{base_name}_{timestamp}.xlsx"
        
        counter = 1
        while os.path.exists(output_file):
            output_file = f"{base_name}_{timestamp}_{counter}.xlsx"
            counter += 1
        
        print(f"\n  Preparing summaries...")
        
        # Pre-calculate all summaries before opening Excel writer
        print("    - Sorting main data...")
        net_sales_sorted = net_sales.sort_values('ACTUAL_SALE_AMOUNT', ascending=False)
        
        print("    - Depot summary...")
        depot_summary = net_sales.groupby('Depot').agg({
            'Sale_Amount': 'sum',
            'Return_Amount': 'sum',
            'ACTUAL_SALE_AMOUNT': 'sum',
            'Sale_Qty': 'sum',
            'Return_Qty': 'sum',
            'ACTUAL_SALE_QTY': 'sum'
        }).reset_index()
        depot_summary['Return_Rate_%'] = (depot_summary['Return_Amount'] / depot_summary['Sale_Amount'] * 100).round(2)
        depot_summary = depot_summary.sort_values('ACTUAL_SALE_AMOUNT', ascending=False)
        
        print("    - MPO summary...")
        mpo_summary = net_sales.groupby(['Depot', 'MPO_Code']).agg({
            'Sale_Amount': 'sum',
            'Return_Amount': 'sum',
            'ACTUAL_SALE_AMOUNT': 'sum',
            'Sale_Qty': 'sum',
            'Return_Qty': 'sum',
            'ACTUAL_SALE_QTY': 'sum'
        }).reset_index()
        mpo_summary['Return_Rate_%'] = (mpo_summary['Return_Amount'] / mpo_summary['Sale_Amount'] * 100).round(2)
        mpo_summary = mpo_summary.sort_values('ACTUAL_SALE_AMOUNT', ascending=False)
        
        print("    - Monthly summary...")
        monthly_summary = net_sales.groupby(['Depot', 'Month']).agg({
            'Sale_Amount': 'sum',
            'Return_Amount': 'sum',
            'ACTUAL_SALE_AMOUNT': 'sum',
            'Sale_Qty': 'sum',
            'Return_Qty': 'sum',
            'ACTUAL_SALE_QTY': 'sum'
        }).reset_index()
        monthly_summary['Return_Rate_%'] = (monthly_summary['Return_Amount'] / monthly_summary['Sale_Amount'] * 100).round(2)
        monthly_summary = monthly_summary.sort_values(['Depot', 'Month'])
        
        print("    - Product summary...")
        product_summary = net_sales.groupby(['Product_Code', 'Product_Name']).agg({
            'Sale_Qty': 'sum',
            'Return_Qty': 'sum',
            'ACTUAL_SALE_QTY': 'sum',
            'Sale_Amount': 'sum',
            'Return_Amount': 'sum',
            'ACTUAL_SALE_AMOUNT': 'sum'
        }).reset_index()
        product_summary['Return_Rate_%'] = (product_summary['Return_Qty'] / product_summary['Sale_Qty'] * 100).round(2)
        product_summary = product_summary.sort_values('ACTUAL_SALE_AMOUNT', ascending=False)
        
        print("    - Customer summary...")
        customer_summary = net_sales.groupby(['Depot', 'Customer_ID', 'Customer_Name']).agg({
            'Sale_Amount': 'sum',
            'Return_Amount': 'sum',
            'ACTUAL_SALE_AMOUNT': 'sum',
            'Sale_Qty': 'sum',
            'Return_Qty': 'sum',
            'ACTUAL_SALE_QTY': 'sum'
        }).reset_index()
        customer_summary['Return_Rate_%'] = (customer_summary['Return_Amount'] / customer_summary['Sale_Amount'] * 100).round(2)
        customer_summary = customer_summary.sort_values('ACTUAL_SALE_AMOUNT', ascending=False)
        
        print(f"\n  Writing to Excel (this may take 2-3 minutes)...")
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Sheet 1: Product-Level Net Sales (MAIN RESULT)
            print("    [1/9] Product Level Net Sales...")
            net_sales_sorted.to_excel(writer, sheet_name='Product Level Net Sales', index=False)
            
            # Sheet 2: Sales Grouped (Pivot equivalent)
            print("    [2/9] Sales Grouped...")
            sales_grouped.to_excel(writer, sheet_name='Sales Grouped', index=False)
            
            # Sheet 3: Returns Grouped (Pivot equivalent)
            print("    [3/9] Returns Grouped...")
            returns_grouped.to_excel(writer, sheet_name='Returns Grouped', index=False)
            
            # Sheet 4: All Transactions with Key (SKIP - too large)
            # print("    [4/9] All Transactions...")
            # all_df.to_excel(writer, sheet_name='All Transactions', index=False)
            
            # Sheet 5: Depot Summary
            print("    [4/9] Depot Summary...")
            depot_summary.to_excel(writer, sheet_name='Depot Summary', index=False)
            
            # Sheet 6: MPO Summary
            print("    [5/9] MPO Summary...")
            mpo_summary.to_excel(writer, sheet_name='MPO Summary', index=False)
            
            # Sheet 7: Monthly Summary
            print("    [6/9] Monthly Summary...")
            monthly_summary.to_excel(writer, sheet_name='Monthly Summary', index=False)
            
            # Sheet 8: Product Summary (Top products)
            print("    [7/9] Product Summary...")
            product_summary.to_excel(writer, sheet_name='Product Summary', index=False)
            
            # Sheet 9: Customer Summary
            print("    [8/9] Customer Summary...")
            customer_summary.to_excel(writer, sheet_name='Customer Summary', index=False)
            
            print("    [9/9] Finalizing file...")
        
        file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
        print(f"\n✓ Saved: {output_file} ({file_size_mb:.2f} MB)")
        
        # Statistics
        total_sale_qty = net_sales['Sale_Qty'].sum()
        total_return_qty = net_sales['Return_Qty'].sum()
        total_actual_qty = net_sales['ACTUAL_SALE_QTY'].sum()
        
        total_sale_amt = net_sales['Sale_Amount'].sum()
        total_return_amt = net_sales['Return_Amount'].sum()
        total_actual_amt = net_sales['ACTUAL_SALE_AMOUNT'].sum()
        
        print(f"\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Unique Product-Level Combinations: {len(net_sales):,}")
        print(f"\nQuantity:")
        print(f"  Sale Qty:       {total_sale_qty:>15,.2f}")
        print(f"  Return Qty:     {total_return_qty:>15,.2f}")
        print(f"  ────────────────────────────────")
        print(f"  ACTUAL SALE:    {total_actual_qty:>15,.2f}")
        print(f"\nAmount (BDT):")
        print(f"  Sale Amount:    {total_sale_amt:>15,.2f}")
        print(f"  Return Amount:  {total_return_amt:>15,.2f}")
        print(f"  ────────────────────────────────")
        print(f"  ACTUAL SALE:    {total_actual_amt:>15,.2f}")
        print(f"  Return Rate:    {total_return_amt/total_sale_amt*100:>14.2f}%")
        
        print(f"\n" + "=" * 80)
        print("Depot Summary:")
        print("=" * 80)
        print(depot_summary[['Depot', 'Sale_Amount', 'Return_Amount', 'ACTUAL_SALE_AMOUNT', 'Return_Rate_%']].to_string(index=False))
        
    else:
        print("\nNo data extracted.")
    
    print("\n" + "=" * 80)
    print("Processing Complete!")
    print("=" * 80)

if __name__ == "__main__":
    try:
        process_all_depots()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
