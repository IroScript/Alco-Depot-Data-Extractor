# Sales Report Generator - MPO/Customer/Product wise analysis

import pyodbc
import pandas as pd
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def create_connection():
    """Database connection"""
    server_name = r'.\SQLEXPRESS'
    db_name = 'ERPonTheNet'
    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server_name};DATABASE={db_name};Trusted_Connection=yes;'
    return pyodbc.connect(conn_str)

def generate_mpo_sales_report(conn):
    """MPO/Sales Person wise sales report"""
    
    query = """
    SELECT 
        o.xordernum AS InvoiceNo,
        o.xdate AS InvoiceDate,
        o.xcus AS CustomerID,
        c.xorg AS CustomerName,
        c.xoffadd AS CustomerAddress,
        c.xphone AS CustomerPhone,
        o.xsm AS SalesPersonCode,
        sm.xlong AS SalesPersonName,
        o.xzone AS ZoneCode,
        zone.xlong AS ZoneName,
        od.xitem AS ProductCode,
        i.xdesc AS ProductName,
        od.xqtyord AS Quantity,
        od.xprice AS UnitPrice,
        od.xlineamt AS LineAmount,
        od.xdisc AS Discount,
        o.xtotamt AS TotalAmount,
        o.xstatusord AS OrderStatus
    FROM opord o
    LEFT JOIN opodt od ON o.xordernum = od.xordernum
    LEFT JOIN cacus c ON o.xcus = c.xcus
    LEFT JOIN caitem i ON od.xitem = i.xitem
    LEFT JOIN xcodes sm ON o.xsm = sm.xcode AND sm.xtype = 'Sales Manager'
    LEFT JOIN xcodes zone ON o.xzone = zone.xcode AND zone.xtype = 'Zone'
    WHERE o.xordernum IS NOT NULL
    ORDER BY o.xdate DESC, o.xordernum
    """
    
    print("   Generating MPO/Sales Person wise report...")
    df = pd.read_sql(query, conn)
    
    if len(df) > 0:
        # Add calculated columns
        df['Year'] = pd.to_datetime(df['InvoiceDate'], errors='coerce').dt.year
        df['Month'] = pd.to_datetime(df['InvoiceDate'], errors='coerce').dt.month
        df['MonthName'] = pd.to_datetime(df['InvoiceDate'], errors='coerce').dt.strftime('%B')
        
        output_file = f"Sales_Report_MPO_Wise_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Main detailed report
            df.to_excel(writer, sheet_name='Detailed Sales', index=False)
            
            # MPO wise summary
            mpo_summary = df.groupby(['SalesPersonCode', 'SalesPersonName']).agg({
                'InvoiceNo': 'count',
                'Quantity': 'sum',
                'LineAmount': 'sum',
                'TotalAmount': 'sum'
            }).reset_index()
            mpo_summary.columns = ['MPO Code', 'MPO Name', 'Total Invoices', 'Total Quantity', 'Total Line Amount', 'Total Amount']
            mpo_summary.to_excel(writer, sheet_name='MPO Summary', index=False)
            
            # Customer wise summary
            customer_summary = df.groupby(['CustomerID', 'CustomerName']).agg({
                'InvoiceNo': 'count',
                'Quantity': 'sum',
                'LineAmount': 'sum'
            }).reset_index()
            customer_summary.columns = ['Customer ID', 'Customer Name', 'Total Invoices', 'Total Quantity', 'Total Amount']
            customer_summary.to_excel(writer, sheet_name='Customer Summary', index=False)
            
            # Product wise summary
            product_summary = df.groupby(['ProductCode', 'ProductName']).agg({
                'InvoiceNo': 'count',
                'Quantity': 'sum',
                'LineAmount': 'sum'
            }).reset_index()
            product_summary.columns = ['Product Code', 'Product Name', 'Total Invoices', 'Total Quantity', 'Total Amount']
            product_summary.to_excel(writer, sheet_name='Product Summary', index=False)
            
            # Month wise summary
            month_summary = df.groupby(['Year', 'Month', 'MonthName']).agg({
                'InvoiceNo': 'count',
                'Quantity': 'sum',
                'LineAmount': 'sum'
            }).reset_index()
            month_summary.columns = ['Year', 'Month', 'Month Name', 'Total Invoices', 'Total Quantity', 'Total Amount']
            month_summary.to_excel(writer, sheet_name='Monthly Summary', index=False)
        
        print(f"      Saved: {output_file}")
        print(f"      Total Records: {len(df):,}")
        print(f"      Sheets: Detailed Sales, MPO Summary, Customer Summary, Product Summary, Monthly Summary")
        return output_file
    else:
        print("      No data found!")
        return None

def generate_customer_ledger(conn):
    """Customer wise complete ledger"""
    
    query = """
    SELECT 
        c.xcus AS CustomerID,
        c.xorg AS CustomerName,
        c.xoffadd AS Address,
        c.xphone AS Phone,
        c.xemail AS Email,
        c.xsm AS SalesPersonCode,
        c.xzone AS ZoneCode,
        c.xblock AS BlockCode,
        c.xstatuscus AS Status,
        c.xcrlimit AS CreditLimit,
        o.xordernum AS InvoiceNo,
        o.xdate AS InvoiceDate,
        o.xtotamt AS InvoiceAmount,
        o.xstatusord AS InvoiceStatus
    FROM cacus c
    LEFT JOIN opord o ON c.xcus = o.xcus
    WHERE c.xcus IS NOT NULL
    ORDER BY c.xcus, o.xdate DESC
    """
    
    print("   Generating Customer Ledger...")
    df = pd.read_sql(query, conn)
    
    if len(df) > 0:
        output_file = f"Customer_Ledger_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(output_file, index=False)
        
        print(f"      Saved: {output_file}")
        print(f"      Total Records: {len(df):,}")
        return output_file
    else:
        print("      No data found!")
        return None

def generate_inventory_report(conn):
    """Product/Item wise inventory and sales"""
    
    query = """
    SELECT 
        i.xitem AS ProductCode,
        i.xdesc AS ProductName,
        i.xalias AS Alias,
        i.xgitem AS ProductGroup,
        i.xprice AS Price,
        i.xstdcost AS StandardCost,
        i.xunitsel AS Unit,
        t.xdate AS TransactionDate,
        t.xtype AS TransactionType,
        t.xqty AS Quantity,
        t.xwh AS Warehouse,
        t.xref AS Reference
    FROM caitem i
    LEFT JOIN imtrn t ON i.xitem = t.xitem
    WHERE i.xitem IS NOT NULL
    ORDER BY i.xitem, t.xdate DESC
    """
    
    print("   Generating Inventory Report...")
    df = pd.read_sql(query, conn)
    
    if len(df) > 0:
        output_file = f"Inventory_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Detailed transactions
            df.to_excel(writer, sheet_name='Transactions', index=False)
            
            # Product summary
            product_summary = df.groupby(['ProductCode', 'ProductName', 'Price']).agg({
                'Quantity': 'sum',
                'Reference': 'count'
            }).reset_index()
            product_summary.columns = ['Product Code', 'Product Name', 'Price', 'Total Quantity', 'Total Transactions']
            product_summary.to_excel(writer, sheet_name='Product Summary', index=False)
        
        print(f"      Saved: {output_file}")
        print(f"      Total Records: {len(df):,}")
        return output_file
    else:
        print("      No data found!")
        return None

def main():
    print("=" * 70)
    print("Sales Analysis Report Generator")
    print("=" * 70)
    print("\nThis will create comprehensive reports with:")
    print("- MPO/Sales Person wise sales")
    print("- Customer wise ledger")
    print("- Product wise inventory")
    print("- All data properly joined and related")
    print("\n" + "=" * 70)
    
    try:
        conn = create_connection()
        print("\nConnected to database successfully!")
        
        reports = []
        
        # Generate reports
        print("\n[1/3] MPO/Sales Person Wise Report")
        report1 = generate_mpo_sales_report(conn)
        if report1:
            reports.append(report1)
        
        print("\n[2/3] Customer Ledger Report")
        report2 = generate_customer_ledger(conn)
        if report2:
            reports.append(report2)
        
        print("\n[3/3] Inventory Report")
        report3 = generate_inventory_report(conn)
        if report3:
            reports.append(report3)
        
        conn.close()
        
        # Summary
        print("\n" + "=" * 70)
        print("Report Generation Complete!")
        print("=" * 70)
        print(f"\nGenerated {len(reports)} reports:")
        for i, report in enumerate(reports, 1):
            print(f"{i}. {report}")
        
        print("\nThese reports contain:")
        print("- Invoice details with customer, product, MPO information")
        print("- Summaries by MPO, Customer, Product, Month")
        print("- All data properly related and easy to understand")
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
