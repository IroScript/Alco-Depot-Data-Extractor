# SQL Server 2005/2008 দিয়ে MDF ফাইল পড়া
# SQL Server 2000 database support করে

import pyodbc
import pandas as pd
import os
from datetime import datetime

def check_sql_server():
    """
    SQL Server ইনস্টল আছে কিনা চেক করা
    """
    try:
        # Try different server names
        servers = [
            r'.\SQLEXPRESS',
            r'localhost\SQLEXPRESS',
            r'localhost',
            r'(local)',
            r'127.0.0.1',
        ]
        
        for server in servers:
            try:
                conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};Trusted_Connection=yes;Timeout=5;'
                conn = pyodbc.connect(conn_str)
                conn.close()
                return server
            except:
                continue
        
        return None
    except:
        return None

def attach_database(server_name, mdf_path, ldf_path):
    """
    MDF ফাইল attach করা
    """
    try:
        # Connect to master database
        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server_name};DATABASE=master;Trusted_Connection=yes;'
        conn = pyodbc.connect(conn_str)
        conn.autocommit = True
        cursor = conn.cursor()
        
        db_name = 'ERPonTheNet'
        
        # Check if database already exists
        cursor.execute(f"SELECT name FROM sys.databases WHERE name = '{db_name}'")
        if cursor.fetchone():
            print(f"   ✅ Database '{db_name}' ইতিমধ্যে attach আছে")
            return db_name
        
        print("📎 MDF ফাইল attach করা হচ্ছে...")
        
        # Attach database
        attach_query = f"""
        CREATE DATABASE [{db_name}] ON 
        (FILENAME = N'{mdf_path}'),
        (FILENAME = N'{ldf_path}')
        FOR ATTACH;
        """
        
        cursor.execute(attach_query)
        print(f"   ✅ Database '{db_name}' successfully attached!")
        
        conn.close()
        return db_name
        
    except Exception as e:
        print(f"\n❌ Attach Error: {e}")
        
        # যদি version issue হয়, upgrade করার চেষ্টা করি
        if "version" in str(e).lower() or "upgrade" in str(e).lower():
            print("\n💡 Database upgrade করার চেষ্টা করা হচ্ছে...")
            try:
                # Try attach with upgrade
                attach_query = f"""
                CREATE DATABASE [{db_name}] ON 
                (FILENAME = N'{mdf_path}')
                FOR ATTACH_REBUILD_LOG;
                """
                cursor.execute(attach_query)
                print(f"   ✅ Database upgraded and attached!")
                conn.close()
                return db_name
            except Exception as e2:
                print(f"   ❌ Upgrade failed: {e2}")
        
        return None

def list_tables(server_name, db_name):
    """
    সব টেবিলের লিস্ট দেখা
    """
    try:
        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server_name};DATABASE={db_name};Trusted_Connection=yes;'
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("""
            SELECT TABLE_SCHEMA, TABLE_NAME, 
                   (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = t.TABLE_NAME AND TABLE_SCHEMA = t.TABLE_SCHEMA) as ColumnCount
            FROM INFORMATION_SCHEMA.TABLES t
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """)
        
        tables = cursor.fetchall()
        
        print("\n" + "=" * 70)
        print(f"📋 মোট {len(tables)}টি টেবিল পাওয়া গেছে:")
        print("=" * 70)
        
        table_list = []
        for i, (schema, table, col_count) in enumerate(tables, 1):
            print(f"{i:3d}. {schema}.{table} ({col_count} columns)")
            table_list.append((schema, table))
        
        conn.close()
        return table_list
        
    except Exception as e:
        print(f"\n❌ Error listing tables: {e}")
        return []

def export_table_to_excel(server_name, db_name, schema, table_name, limit=None):
    """
    একটি টেবিল থেকে ডেটা Excel এ export করা
    """
    try:
        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server_name};DATABASE={db_name};Trusted_Connection=yes;'
        conn = pyodbc.connect(conn_str)
        
        # Build query
        full_table = f"[{schema}].[{table_name}]"
        if limit:
            query = f"SELECT TOP {limit} * FROM {full_table}"
        else:
            query = f"SELECT * FROM {full_table}"
        
        print(f"\n🔍 '{table_name}' টেবিল থেকে ডেটা পড়া হচ্ছে...")
        
        # Read data
        df = pd.read_sql(query, conn)
        
        if len(df) == 0:
            print(f"   ⚠️ টেবিল খালি!")
            conn.close()
            return None
        
        # Save to Excel
        output_file = f"{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(output_file, index=False)
        
        print(f"   ✅ সফল!")
        print(f"   📄 ফাইল: {output_file}")
        print(f"   📊 রো: {len(df):,}, কলাম: {len(df.columns)}")
        
        # Show sample data
        print(f"\n   📝 কলাম নাম: {', '.join(df.columns.tolist()[:10])}")
        if len(df.columns) > 10:
            print(f"       ... এবং আরও {len(df.columns) - 10}টি কলাম")
        
        conn.close()
        return output_file
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def export_all_tables(server_name, db_name, table_list):
    """
    সব টেবিল export করা
    """
    print("\n" + "=" * 70)
    print("📦 সব টেবিল export করা হচ্ছে...")
    print("=" * 70)
    
    exported = []
    
    for i, (schema, table) in enumerate(table_list, 1):
        print(f"\n[{i}/{len(table_list)}] Processing: {table}")
        
        output_file = export_table_to_excel(server_name, db_name, schema, table, limit=10000)
        
        if output_file:
            exported.append(output_file)
    
    return exported

def main():
    print("=" * 70)
    print("SQL Server 2005/2008 MDF ফাইল রিডার")
    print("=" * 70)
    
    mdf_path = r"c:\Users\Irak\Desktop\Barishal April Data\Data\ERPonTheNet_Data.MDF"
    ldf_path = r"c:\Users\Irak\Desktop\Barishal April Data\Data\ERPonTheNet_log.LDF"
    
    # Check files
    if not os.path.exists(mdf_path):
        print(f"❌ MDF ফাইল পাওয়া যায়নি: {mdf_path}")
        return
    
    if not os.path.exists(ldf_path):
        print(f"⚠️ LDF ফাইল পাওয়া যায়নি: {ldf_path}")
        print("   LDF ছাড়াই attach করার চেষ্টা করা হবে...")
    
    print(f"\n✅ ফাইল পাওয়া গেছে:")
    print(f"   MDF: {os.path.getsize(mdf_path) / (1024*1024):.2f} MB")
    if os.path.exists(ldf_path):
        print(f"   LDF: {os.path.getsize(ldf_path) / (1024*1024):.2f} MB")
    
    # Check SQL Server
    print("\n🔍 SQL Server খোঁজা হচ্ছে...")
    server_name = check_sql_server()
    
    if not server_name:
        print("\n❌ SQL Server পাওয়া যায়নি!")
        print("\n📥 SQL Server ইনস্টল করুন:")
        print("   'install_sql2000_guide.md' ফাইল দেখুন")
        print("\n   সুপারিশ: SQL Server 2008 R2 Express")
        print("   লিংক: https://www.microsoft.com/en-us/download/details.aspx?id=30438")
        return
    
    print(f"   ✅ SQL Server পাওয়া গেছে: {server_name}")
    
    # Attach database
    print("\n🔧 Database attach করা হচ্ছে...")
    db_name = attach_database(server_name, mdf_path, ldf_path)
    
    if not db_name:
        print("\n❌ Database attach করা সম্ভব হয়নি!")
        print("\n💡 সমাধান:")
        print("1. SQL Server Management Studio (SSMS) ওপেন করুন")
        print("2. Manually database attach করুন")
        print("3. তারপর আবার এই script চালান")
        return
    
    # List tables
    table_list = list_tables(server_name, db_name)
    
    if not table_list:
        print("\n❌ কোনো টেবিল পাওয়া যায়নি!")
        return
    
    # Ask user what to do
    print("\n" + "=" * 70)
    print("কী করতে চান?")
    print("=" * 70)
    print("1. একটি নির্দিষ্ট টেবিল export করুন")
    print("2. সব টেবিল export করুন (সময় লাগবে)")
    print("3. প্রথম 5টি টেবিল export করুন (টেস্টের জন্য)")
    print("4. Exit")
    
    choice = input("\nআপনার পছন্দ (1-4): ").strip()
    
    if choice == "1":
        table_num = int(input(f"\nটেবিল নম্বর (1-{len(table_list)}): "))
        if 1 <= table_num <= len(table_list):
            schema, table = table_list[table_num - 1]
            export_table_to_excel(server_name, db_name, schema, table)
    
    elif choice == "2":
        confirm = input("\n⚠️ সব টেবিল export করতে সময় লাগবে। Continue? (y/n): ")
        if confirm.lower() == 'y':
            exported = export_all_tables(server_name, db_name, table_list)
            print(f"\n🎉 মোট {len(exported)}টি টেবিল export হয়েছে!")
    
    elif choice == "3":
        exported = export_all_tables(server_name, db_name, table_list[:5])
        print(f"\n🎉 মোট {len(exported)}টি টেবিল export হয়েছে!")
    
    else:
        print("\nExit করা হচ্ছে...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ User interrupted!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
