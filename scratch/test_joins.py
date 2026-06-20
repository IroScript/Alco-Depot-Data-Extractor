import os
import pyodbc
import pandas as pd

def main():
    server = r'.\SQLEXPRESS'
    db_name = 'TEMP_TEST_JOIN_DB'
    mdf_path = r'c:\Users\Irak\Desktop\Barishal April Data\Barishal_Temp\Data\ERPonTheNet_Data.MDF'
    ldf_path = r'c:\Users\Irak\Desktop\Barishal April Data\Barishal_Temp\Data\ERPonTheNet_log.LDF'
    
    if not os.path.exists(mdf_path):
        print(f"File not found: {mdf_path}")
        return
        
    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE=master;Trusted_Connection=yes;'
    conn = pyodbc.connect(conn_str)
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Detach if exists
    cursor.execute(f"SELECT database_id FROM sys.databases WHERE name = '{db_name}'")
    if cursor.fetchone():
        cursor.execute(f"ALTER DATABASE [{db_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
        cursor.execute(f"EXEC sp_detach_db '{db_name}', 'true'")
        
    # Attach
    attach_query = f"CREATE DATABASE [{db_name}] ON (FILENAME = N'{mdf_path}'), (FILENAME = N'{ldf_path}') FOR ATTACH;"
    cursor.execute(attach_query)
    
    # Query
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
    df_raw = pd.read_sql(query, conn)
    
    # Detach
    cursor.execute(f"ALTER DATABASE [{db_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
    cursor.execute(f"EXEC sp_detach_db '{db_name}', 'true'")
    conn.close()
    
    # Process
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
        'Depot': 'first', 'MPO_Code': 'first', 'Customer_ID': 'first', 'Customer_Name': 'first',
        'Month': 'first', 'Product_Code': 'first', 'Product_Name': 'first', 'Quantity': 'sum', 'Line_Amount': 'sum'
    }).reset_index()
    sales_grouped.columns = [
        'CONCATENATED_KEY', 'Depot', 'MPO_Code', 'Customer_ID', 'Customer_Name',
        'Month', 'Product_Code', 'Product_Name', 'Sale_Qty', 'Sale_Amount'
    ]
    
    returns_grouped = returns_df.groupby('CONCATENATED_KEY').agg({
        'Quantity': 'sum', 'Line_Amount': 'sum'
    }).reset_index()
    returns_grouped.columns = ['CONCATENATED_KEY', 'Return_Qty', 'Return_Amount']
    
    # 1. Left Join
    left_sales = pd.merge(sales_grouped, returns_grouped, on='CONCATENATED_KEY', how='left')
    left_sales['Return_Qty'] = left_sales['Return_Qty'].fillna(0)
    left_sales['Return_Amount'] = left_sales['Return_Amount'].fillna(0)
    left_sales['ACTUAL_SALE_QTY'] = left_sales['Sale_Qty'] - left_sales['Return_Qty']
    left_sales['ACTUAL_SALE_AMOUNT'] = left_sales['Sale_Amount'] - left_sales['Return_Amount']
    
    # 2. Outer Join
    outer_sales = pd.merge(sales_grouped, returns_grouped, on='CONCATENATED_KEY', how='outer')
    outer_sales['Sale_Qty'] = outer_sales['Sale_Qty'].fillna(0)
    outer_sales['Sale_Amount'] = outer_sales['Sale_Amount'].fillna(0)
    outer_sales['Return_Qty'] = outer_sales['Return_Qty'].fillna(0)
    outer_sales['Return_Amount'] = outer_sales['Return_Amount'].fillna(0)
    outer_sales['ACTUAL_SALE_QTY'] = outer_sales['Sale_Qty'] - outer_sales['Return_Qty']
    outer_sales['ACTUAL_SALE_AMOUNT'] = outer_sales['Sale_Amount'] - outer_sales['Return_Amount']
    
    # 3. Detailed Daily (with negative returns)
    detailed_df = df_raw.copy()
    detailed_df['Month'] = pd.to_datetime(detailed_df['Invoice_Date']).dt.strftime('%Y-%m')
    detailed_df.loc[detailed_df['Transaction_Type'] == 'Return', 'Quantity'] *= -1
    detailed_df.loc[detailed_df['Transaction_Type'] == 'Return', 'Line_Amount'] *= -1
    detailed_grouped = detailed_df.groupby([
        'Depot', 'MPO_Code', 'Invoice_No', 'Invoice_Date', 'Transaction_Time', 
        'Transaction_Type', 'Customer_ID', 'Customer_Name', 'Product_Code', 'Product_Name', 'Month'
    ]).agg({
        'Quantity': 'sum',
        'Line_Amount': 'sum'
    }).reset_index()
    
    # Outputs Comparison
    print("\n" + "="*60)
    print("JOINS TEST RESULTS FOR BARISHAL")
    print("="*60)
    print(f"Total Rows in Left Join:   {len(left_sales)}")
    print(f"Total Rows in Outer Join:  {len(outer_sales)}")
    print(f"Row Difference:            {len(outer_sales) - len(left_sales)}")
    print("-" * 50)
    
    left_qty_sum = left_sales['ACTUAL_SALE_QTY'].sum()
    outer_qty_sum = outer_sales['ACTUAL_SALE_QTY'].sum()
    detailed_qty_sum = detailed_grouped['Quantity'].sum()
    
    print(f"Left Join Actual Qty Sum:  {left_qty_sum:,.2f}")
    print(f"Outer Join Actual Qty Sum: {outer_qty_sum:,.2f}")
    print(f"Detailed Qty Sum:          {detailed_qty_sum:,.2f}")
    print("-" * 50)
    print(f"Detailed - Left Join:      {detailed_qty_sum - left_qty_sum:,.2f}  (Difference!)")
    print(f"Detailed - Outer Join:     {detailed_qty_sum - outer_qty_sum:,.2f}  (Zero Difference!)")
    print("="*60)
    
    # Check sample transaction time format
    print("\nSample Transaction Time Values in Raw DF:")
    print(df_raw[['Invoice_No', 'Invoice_Date', 'Transaction_Time']].head(5))
    
    # Format and check again
    formatted_time = pd.to_datetime(df_raw['Transaction_Time']).dt.strftime('%Y-%m-%d %H:%M:%S.%f').str[:-3]
    print("\nSample Processed Time Values:")
    print(formatted_time.head(5))

if __name__ == '__main__':
    main()
