# Process All Depots - Net Sales Calculation (Sales - Returns)
# MR- (Money Receipt) excluded from sales calculation

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
    """Extract sales and returns data (excluding MR- Money Receipts)"""
    try:
        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SQL_SERVER};DATABASE={db_name};Trusted_Connection=yes;'
        conn = pyodbc.connect(conn_str)
        
        # Extract ONLY IN- (Sales) and SR- (Returns), EXCLUDE MR- (Money Receipt)
        query = f"""
        SELECT 
            '{depot_name}' AS Depot,
            o.xsp AS MPO_Code,
            o.xordernum AS Invoice_No,
            o.xdate AS Invoice_Date,
            CASE 
                WHEN o.xordernum LIKE 'IN-%' OR o.xordernum LIKE 'IN--%' THEN 'Sale'
                WHEN o.xordernum LIKE 'SR-%' OR o.xordernum LIKE 'SR--%' THEN 'Sales Return'
                ELSE 'Other'
            END AS Transaction_Type,
            o.xstatusord AS Status,
            o.xcus AS Customer_ID,
            c.xorg AS Customer_Name,
            od.xitem AS Product_Code,
            i.xdesc AS Product_Name,
            od.xqtyord AS Quantity,
            od.xprice AS Unit_Price,
            od.xlineamt AS Line_Amount,
            o.xtotamt AS Invoice_Total
        FROM opord o
        LEFT JOIN opodt od ON o.xordernum = od.xordernum
        LEFT JOIN cacus c ON o.xcus = c.xcus
        LEFT JOIN caitem i ON od.xitem = i.xitem
        WHERE o.xsp IS NOT NULL 
          AND o.xsp != ''
          AND (o.xordernum LIKE 'IN-%' OR o.xordernum LIKE 'IN--%' 
               OR o.xordernum LIKE 'SR-%' OR o.xordernum LIKE 'SR--%')
        ORDER BY o.xsp, o.xdate DESC
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        return df
        
    except Exception as e:
        print(f"    ✗ Error extracting data: {e}")
        return pd.DataFrame()

def calculate_net_sales(df):
    """Calculate net sales by subtracting returns from sales"""
    
    # Add Month column
    df['Month'] = pd.to_datetime(df['Invoice_Date']).dt.strftime('%Y-%m')
    
    # Separate sales and returns
    sales_df = df[df['Transaction_Type'] == 'Sale'].copy()
    returns_df = df[df['Transaction_Type'] == 'Sales Return'].copy()
    
    # Calculate totals
    sales_total = sales_df['Line_Amount'].sum()
    returns_total = returns_df['Line_Amount'].sum()
    net_sales = sales_total - returns_total
    
    return df, sales_df, returns_df, sales_total, returns_total, net_sales

def process_all_depots():
    """Main function to process all depots"""
    print("=" * 80)
    print("Multi-Depot NET SALES Calculator")
    print("Sales (IN-) minus Returns (SR-), excluding Money Receipts (MR-)")
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
            print(f"  Extracting sales and returns data...")
            df = extract_sales_data(depot['name'], db_name)
            
            if len(df) > 0:
                all_data.append(df)
                sales_count = len(df[df['Transaction_Type'] == 'Sale'])
                returns_count = len(df[df['Transaction_Type'] == 'Sales Return'])
                print(f"  ✓ Sales: {sales_count:,} | Returns: {returns_count:,} | Total: {len(df):,}")
            else:
                print(f"  ✗ No data found")
        else:
            print(f"  ✗ Failed to attach database")
    
    if all_data:
        print("\n" + "=" * 80)
        print("Combining and Calculating Net Sales")
        print("=" * 80)
        
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Calculate net sales
        all_df, sales_df, returns_df, sales_total, returns_total, net_sales = calculate_net_sales(combined_df)
        
        # Create unique output filename
        base_name = "Net_Sales_Report"
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"{base_name}_{timestamp}.xlsx"
        
        counter = 1
        while os.path.exists(output_file):
            output_file = f"{base_name}_{timestamp}_{counter}.xlsx"
            counter += 1
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Sheet 1: Net Sales Detail (Sales - Returns matched)
            all_df.to_excel(writer, sheet_name='All Transactions', index=False)
            
            # Sheet 2: Sales Only (IN-)
            sales_df.to_excel(writer, sheet_name='Sales (IN)', index=False)
            
            # Sheet 3: Returns Only (SR-)
            returns_df.to_excel(writer, sheet_name='Returns (SR)', index=False)
            
            # Sheet 4: Net Sales by Depot
            depot_net_sales = pd.DataFrame()
            depot_net_sales['Depot'] = sales_df.groupby('Depot')['Line_Amount'].sum().index
            depot_net_sales['Gross_Sales'] = sales_df.groupby('Depot')['Line_Amount'].sum().values
            depot_net_sales['Returns'] = returns_df.groupby('Depot')['Line_Amount'].sum().reindex(depot_net_sales['Depot'], fill_value=0).values
            depot_net_sales['Net_Sales'] = depot_net_sales['Gross_Sales'] - depot_net_sales['Returns']
            depot_net_sales['Return_Rate_%'] = (depot_net_sales['Returns'] / depot_net_sales['Gross_Sales'] * 100).round(2)
            depot_net_sales.to_excel(writer, sheet_name='Net Sales by Depot', index=False)
            
            # Sheet 5: Net Sales by MPO
            mpo_sales = sales_df.groupby(['Depot', 'MPO_Code'])['Line_Amount'].sum().reset_index()
            mpo_sales.columns = ['Depot', 'MPO_Code', 'Gross_Sales']
            
            mpo_returns = returns_df.groupby(['Depot', 'MPO_Code'])['Line_Amount'].sum().reset_index()
            mpo_returns.columns = ['Depot', 'MPO_Code', 'Returns']
            
            mpo_net = pd.merge(mpo_sales, mpo_returns, on=['Depot', 'MPO_Code'], how='left')
            mpo_net['Returns'] = mpo_net['Returns'].fillna(0)
            mpo_net['Net_Sales'] = mpo_net['Gross_Sales'] - mpo_net['Returns']
            mpo_net['Return_Rate_%'] = (mpo_net['Returns'] / mpo_net['Gross_Sales'] * 100).round(2)
            mpo_net = mpo_net.sort_values('Net_Sales', ascending=False)
            mpo_net.to_excel(writer, sheet_name='Net Sales by MPO', index=False)
            
            # Sheet 6: Monthly Net Sales
            monthly_sales = sales_df.groupby(['Depot', 'Month'])['Line_Amount'].sum().reset_index()
            monthly_sales.columns = ['Depot', 'Month', 'Gross_Sales']
            
            monthly_returns = returns_df.groupby(['Depot', 'Month'])['Line_Amount'].sum().reset_index()
            monthly_returns.columns = ['Depot', 'Month', 'Returns']
            
            monthly_net = pd.merge(monthly_sales, monthly_returns, on=['Depot', 'Month'], how='left')
            monthly_net['Returns'] = monthly_net['Returns'].fillna(0)
            monthly_net['Net_Sales'] = monthly_net['Gross_Sales'] - monthly_net['Returns']
            monthly_net = monthly_net.sort_values(['Depot', 'Month'])
            monthly_net.to_excel(writer, sheet_name='Monthly Net Sales', index=False)
            
            # Sheet 7: Customer-wise Returns Analysis
            customer_returns = returns_df.groupby(['Depot', 'Customer_ID', 'Customer_Name']).agg({
                'Invoice_No': 'nunique',
                'Line_Amount': 'sum'
            }).reset_index()
            customer_returns.columns = ['Depot', 'Customer_ID', 'Customer_Name', 'Return_Count', 'Return_Amount']
            customer_returns = customer_returns.sort_values('Return_Amount', ascending=False)
            customer_returns.to_excel(writer, sheet_name='Customer Returns', index=False)
            
            # Sheet 8: Product-wise Returns Analysis
            product_returns = returns_df.groupby(['Depot', 'Product_Code', 'Product_Name']).agg({
                'Quantity': 'sum',
                'Line_Amount': 'sum'
            }).reset_index()
            product_returns.columns = ['Depot', 'Product_Code', 'Product_Name', 'Return_Qty', 'Return_Amount']
            product_returns = product_returns.sort_values('Return_Amount', ascending=False)
            product_returns.to_excel(writer, sheet_name='Product Returns', index=False)
        
        print(f"\n✓ Saved: {output_file}")
        print(f"\n" + "=" * 80)
        print("SUMMARY STATISTICS")
        print("=" * 80)
        print(f"Total Transactions: {len(all_df):,}")
        print(f"  - Sales (IN-): {len(sales_df):,} ({len(sales_df)/len(all_df)*100:.1f}%)")
        print(f"  - Returns (SR-): {len(returns_df):,} ({len(returns_df)/len(all_df)*100:.1f}%)")
        print(f"\nFinancial Summary:")
        print(f"  Gross Sales (IN-): {sales_total:,.2f} BDT")
        print(f"  Returns (SR-):     {returns_total:,.2f} BDT")
        print(f"  ─────────────────────────────────────")
        print(f"  NET SALES:         {net_sales:,.2f} BDT")
        print(f"  Return Rate:       {returns_total/sales_total*100:.2f}%")
        
        print(f"\n" + "=" * 80)
        print("Net Sales by Depot:")
        print("=" * 80)
        print(depot_net_sales.to_string(index=False))
        
    else:
        print("\nNo data extracted from any depot.")
    
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
