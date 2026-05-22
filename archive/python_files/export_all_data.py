# সব গুরুত্বপূর্ণ টেবিল একসাথে export করা

import pyodbc
import pandas as pd
import os
from datetime import datetime

def export_table(server_name, db_name, schema, table_name):
    """একটি টেবিল export করা"""
    try:
        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server_name};DATABASE={db_name};Trusted_Connection=yes;'
        conn = pyodbc.connect(conn_str)
        
        full_table = f"[{schema}].[{table_name}]"
        query = f"SELECT * FROM {full_table}"
        
        print(f"   📖 Reading '{table_name}'...")
        df = pd.read_sql(query, conn)
        
        if len(df) == 0:
            print(f"      ⚠️ Empty table")
            conn.close()
            return None
        
        # Save to Excel
        output_file = f"{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(output_file, index=False)
        
        print(f"      ✅ Saved: {output_file}")
        print(f"      📊 Rows: {len(df):,}, Columns: {len(df.columns)}")
        
        conn.close()
        return output_file
        
    except Exception as e:
        print(f"      ❌ Error: {e}")
        return None

def main():
    print("=" * 70)
    print("📦 ERP Database - Complete Data Export")
    print("=" * 70)
    
    server_name = r'.\SQLEXPRESS'
    db_name = 'ERPonTheNet'
    
    # Important tables to export
    important_tables = [
        ('dbo', 'cacus', 'Customers'),
        ('dbo', 'caitem', 'Items/Products'),
        ('dbo', 'casup', 'Suppliers'),
        ('dbo', 'opord', 'Orders'),
        ('dbo', 'opodt', 'Order Details'),
        ('dbo', 'opddt', 'Delivery Details'),
        ('dbo', 'opcollect', 'Collections'),
        ('dbo', 'poord', 'Purchase Orders'),
        ('dbo', 'poodt', 'Purchase Order Details'),
        ('dbo', 'pogrn', 'Goods Receipt'),
        ('dbo', 'imtrn', 'Inventory Transactions'),
        ('dbo', 'glheader', 'GL Headers'),
        ('dbo', 'GLdetail', 'GL Details'),
        ('dbo', 'xusers', 'Users'),
        ('dbo', 'xcodes', 'Codes'),
    ]
    
    print(f"\n🎯 Exporting {len(important_tables)} important tables...")
    print("=" * 70)
    
    exported = []
    failed = []
    
    for i, (schema, table, description) in enumerate(important_tables, 1):
        print(f"\n[{i}/{len(important_tables)}] {description} ({table})")
        
        result = export_table(server_name, db_name, schema, table)
        
        if result:
            exported.append((table, result))
        else:
            failed.append(table)
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Export Summary")
    print("=" * 70)
    print(f"✅ Successfully exported: {len(exported)} tables")
    print(f"❌ Failed: {len(failed)} tables")
    
    if exported:
        print("\n📁 Exported files:")
        for table, filename in exported:
            print(f"   - {filename}")
    
    if failed:
        print("\n⚠️ Failed tables:")
        for table in failed:
            print(f"   - {table}")
    
    print("\n🎉 Done! Check the Excel files in this folder.")
    print("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
