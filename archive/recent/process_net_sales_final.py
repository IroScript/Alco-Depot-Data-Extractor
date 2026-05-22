# Process All Depots - Net Sales with Party-wise Return Matching
# For each Customer/Party: Net Sales = Sum(IN-) - Sum(SR-)

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
        ORDER BY o.xcus, o.xdate
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        return df
        
    except Exception as e:
        print(f"    ✗ Error extracting data: {e}")
        return pd.DataFrame()

def calculate_party_wise_net_sales(df):
    """Calculate net sales by matching returns to sales at PARTY/CUSTOMER level"""
    
    # Add Month column
    df['Month'] = pd.to_datetime(df['Invoice_Date']).dt.strftime('%Y-%m')
    
    # Separate sales and returns
    sales_df = df[df['Transaction_Type'] == 'Sale'].copy()
    returns_df = df[df['Transaction_Type'] == 'Return'].copy()
    
    # Calculate party-wise (customer-wise) net sales
    # Group by Depot, MPO, Customer_ID
    party_sales = sales_df.groupby(['Depot', 'MPO_Code', 'Customer_ID', 'Customer_Name']).agg({
        'Invoice_No': 'nunique',
        'Line_Amount': 'sum',
        'Quantity': 'sum'
    }).reset_index()
    party_sales.columns = ['Depot', 'MPO_Code', 'Customer_ID', 'Customer_Name', 'Sales_Invoices', 'Gross_Sales', 'Sales_Qty']
    
    party_returns = returns_df.groupby(['Depot', 'MPO_Code', 'Customer_ID', 'Customer_Name']).agg({
        'Invoice_No': 'nunique',
        'Line_Amount': 'sum',
        'Quantity': 'sum'
    }).reset_index()
    party_returns.columns = ['Depot', 'MPO_Code', 'Customer_ID', 'Customer_Name', 'Return_Invoices', 'Returns', 'Return_Qty']
    
    # Merge sales and returns by party
    party_net = pd.merge(
        party_sales, 
        party_returns[['Depot', 'MPO_Code', 'Customer_ID', 'Return_Invoices', 'Returns', 'Return_Qty']], 
        on=['Depot', 'MPO_Code', 'Customer_ID'], 
        how='left'
    )
    
    # Fill NaN with 0 for parties with no returns
    party_net['Return_Invoices'] = party_net['Return_Invoices'].fillna(0).astype(int)
    party_net['Returns'] = party_net['Returns'].fillna(0)
    party_net['Return_Qty'] = party_net['Return_Qty'].fillna(0)
    
    # Calculate net sales for each party
    party_net['Net_Sales'] = party_net['Gross_Sales'] - party_net['Returns']
    party_net['Net_Qty'] = party_net['Sales_Qty'] - party_net['Return_Qty']
    party_net['Return_Rate_%'] = (party_net['Returns'] / party_net['Gross_Sales'] * 100).round(2)
    
    return df, sales_df, returns_df, party_net

def process_all_depots():
    """Main function to process all depots"""
    print("=" * 80)
    print("Multi-Depot NET SALES Calculator - PARTY WISE")
    print("For each Customer/Party: Net Sales = Sum(IN-) - Sum(SR-)")
    print("Excluding Money Receipts (MR-)")
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
                returns_count = len(df[df['Transaction_Type'] == 'Return'])
                print(f"  ✓ Sales: {sales_count:,} | Returns: {returns_count:,} | Total: {len(df):,}")
            else:
                print(f"  ✗ No data found")
        else:
            print(f"  ✗ Failed to attach database")
    
    if all_data:
        print("\n" + "=" * 80)
        print("Calculating Party-wise Net Sales")
        print("=" * 80)
        
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Calculate party-wise net sales
        all_df, sales_df, returns_df, party_net = calculate_party_wise_net_sales(combined_df)
        
        # Create unique output filename
        base_name = "Party_Wise_Net_Sales"
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"{base_name}_{timestamp}.xlsx"
        
        counter = 1
        while os.path.exists(output_file):
            output_file = f"{base_name}_{timestamp}_{counter}.xlsx"
            counter += 1
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Sheet 1: Party-wise Net Sales (MAIN REPORT)
            party_net_sorted = party_net.sort_values('Net_Sales', ascending=False)
            party_net_sorted.to_excel(writer, sheet_name='Party Wise Net Sales', index=False)
            
            # Sheet 2: All Transactions Detail
            all_df.to_excel(writer, sheet_name='All Transactions', index=False)
            
            # Sheet 3: Sales Only (IN-)
            sales_df.to_excel(writer, sheet_name='Sales Detail (IN)', index=False)
            
            # Sheet 4: Returns Only (SR-)
            returns_df.to_excel(writer, sheet_name='Returns Detail (SR)', index=False)
            
            # Sheet 5: Depot Summary
            depot_summary = party_net.groupby('Depot').agg({
                'Gross_Sales': 'sum',
                'Returns': 'sum',
                'Net_Sales': 'sum',
                'Customer_ID': 'nunique'
            }).reset_index()
            depot_summary.columns = ['Depot', 'Gross_Sales', 'Returns', 'Net_Sales', 'Total_Customers']
            depot_summary['Return_Rate_%'] = (depot_summary['Returns'] / depot_summary['Gross_Sales'] * 100).round(2)
            depot_summary = depot_summary.sort_values('Net_Sales', ascending=False)
            depot_summary.to_excel(writer, sheet_name='Depot Summary', index=False)
            
            # Sheet 6: MPO Summary
            mpo_summary = party_net.groupby(['Depot', 'MPO_Code']).agg({
                'Gross_Sales': 'sum',
                'Returns': 'sum',
                'Net_Sales': 'sum',
                'Customer_ID': 'nunique'
            }).reset_index()
            mpo_summary.columns = ['Depot', 'MPO_Code', 'Gross_Sales', 'Returns', 'Net_Sales', 'Total_Customers']
            mpo_summary['Return_Rate_%'] = (mpo_summary['Returns'] / mpo_summary['Gross_Sales'] * 100).round(2)
            mpo_summary = mpo_summary.sort_values('Net_Sales', ascending=False)
            mpo_summary.to_excel(writer, sheet_name='MPO Summary', index=False)
            
            # Sheet 7: Monthly Net Sales
            all_df['Month'] = pd.to_datetime(all_df['Invoice_Date']).dt.strftime('%Y-%m')
            
            monthly_sales = sales_df.groupby(['Depot', 'Month'])['Line_Amount'].sum().reset_index()
            monthly_sales.columns = ['Depot', 'Month', 'Gross_Sales']
            
            monthly_returns = returns_df.groupby(['Depot', 'Month'])['Line_Amount'].sum().reset_index()
            monthly_returns.columns = ['Depot', 'Month', 'Returns']
            
            monthly_net = pd.merge(monthly_sales, monthly_returns, on=['Depot', 'Month'], how='left')
            monthly_net['Returns'] = monthly_net['Returns'].fillna(0)
            monthly_net['Net_Sales'] = monthly_net['Gross_Sales'] - monthly_net['Returns']
            monthly_net['Return_Rate_%'] = (monthly_net['Returns'] / monthly_net['Gross_Sales'] * 100).round(2)
            monthly_net = monthly_net.sort_values(['Depot', 'Month'])
            monthly_net.to_excel(writer, sheet_name='Monthly Net Sales', index=False)
            
            # Sheet 8: Top Customers by Net Sales
            top_customers = party_net.nlargest(100, 'Net_Sales')[['Depot', 'MPO_Code', 'Customer_ID', 'Customer_Name', 'Gross_Sales', 'Returns', 'Net_Sales', 'Return_Rate_%']]
            top_customers.to_excel(writer, sheet_name='Top 100 Customers', index=False)
            
            # Sheet 9: Customers with High Return Rate
            high_return = party_net[party_net['Gross_Sales'] > 10000].copy()  # Only customers with >10K sales
            high_return = high_return.nlargest(100, 'Return_Rate_%')[['Depot', 'MPO_Code', 'Customer_ID', 'Customer_Name', 'Gross_Sales', 'Returns', 'Net_Sales', 'Return_Rate_%']]
            high_return.to_excel(writer, sheet_name='High Return Rate', index=False)
        
        print(f"\n✓ Saved: {output_file}")
        
        # Calculate overall statistics
        total_gross = party_net['Gross_Sales'].sum()
        total_returns = party_net['Returns'].sum()
        total_net = party_net['Net_Sales'].sum()
        total_customers = party_net['Customer_ID'].nunique()
        
        print(f"\n" + "=" * 80)
        print("OVERALL SUMMARY")
        print("=" * 80)
        print(f"Total Transactions: {len(all_df):,}")
        print(f"  - Sales (IN-): {len(sales_df):,} ({len(sales_df)/len(all_df)*100:.1f}%)")
        print(f"  - Returns (SR-): {len(returns_df):,} ({len(returns_df)/len(all_df)*100:.1f}%)")
        print(f"\nTotal Unique Customers/Parties: {total_customers:,}")
        print(f"\nFinancial Summary:")
        print(f"  Gross Sales (IN-):  {total_gross:>15,.2f} BDT")
        print(f"  Returns (SR-):      {total_returns:>15,.2f} BDT")
        print(f"  ────────────────────────────────────────")
        print(f"  NET SALES:          {total_net:>15,.2f} BDT")
        print(f"  Return Rate:        {total_returns/total_gross*100:>14.2f}%")
        
        print(f"\n" + "=" * 80)
        print("Net Sales by Depot:")
        print("=" * 80)
        print(depot_summary.to_string(index=False))
        
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
