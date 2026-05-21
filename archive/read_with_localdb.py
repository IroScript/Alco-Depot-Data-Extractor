# SQL Server LocalDB দিয়ে MDF ফাইল পড়া
# হালকা এবং কার্যকর পদ্ধতি

import subprocess
import pandas as pd
import os
from datetime import datetime

def check_localdb():
    """
    SQL Server LocalDB ইনস্টল আছে কিনা চেক করা
    """
    try:
        result = subprocess.run(['sqllocaldb', 'info'], 
                              capture_output=True, 
                              text=True,
                              timeout=5)
        return result.returncode == 0
    except:
        return False

def install_localdb_guide():
    """
    LocalDB ইনস্টল করার গাইড
    """
    print("\n" + "=" * 70)
    print("📥 SQL Server LocalDB ইনস্টল করুন (হালকা, ফ্রি)")
    print("=" * 70)
    print("\n1. এই লিংক থেকে ডাউনলোড করুন:")
    print("   https://go.microsoft.com/fwlink/?linkid=866658")
    print("\n2. অথবা এই কমান্ড চালান:")
    print("   winget install Microsoft.SQLServerLocalDB")
    print("\n3. ইনস্টল হলে আবার এই স্ক্রিপ্ট চালান")
    print("\n💡 LocalDB হলো SQL Server এর হালকা ভার্সন (50 MB)")
    print("   পুরো SQL Server এর মতো ভারী না!")

def attach_and_read_mdf(mdf_path, ldf_path):
    """
    MDF ফাইল attach করে ডেটা পড়া
    """
    try:
        import pyodbc
        
        # LocalDB instance তৈরি/শুরু করা
        print("\n🔧 LocalDB instance শুরু করা হচ্ছে...")
        subprocess.run(['sqllocaldb', 'create', 'MSSQLLocalDB'], 
                      capture_output=True)
        subprocess.run(['sqllocaldb', 'start', 'MSSQLLocalDB'], 
                      capture_output=True)
        
        # Connection string - ODBC Driver 17 detected
        conn_str = r'DRIVER={ODBC Driver 17 for SQL Server};SERVER=(localdb)\MSSQLLocalDB;Trusted_Connection=yes;Timeout=30;'
        
        try:
            print(f"   Connecting with ODBC Driver 17...")
            conn = pyodbc.connect(conn_str)
            print(f"   ✅ Connected!")
        except Exception as e:
            print(f"\n❌ Connection Error: {e}")
            print("\nসমস্যা সমাধান:")
            print("1. LocalDB restart করুন:")
            print("   sqllocaldb stop MSSQLLocalDB")
            print("   sqllocaldb start MSSQLLocalDB")
            print("2. তারপর আবার চেষ্টা করুন")
            return False
        
        print("🔌 ডেটাবেজের সাথে কানেক্ট করা হচ্ছে...")
        cursor = conn.cursor()
        
        # Disable autocommit for CREATE DATABASE
        conn.autocommit = True
        
        # Database attach করা
        db_name = 'ERPonTheNet_Temp'
        
        # Check if database already exists
        cursor.execute(f"SELECT name FROM sys.databases WHERE name = '{db_name}'")
        if cursor.fetchone():
            print(f"   Database '{db_name}' ইতিমধ্যে attach আছে")
        else:
            print("📎 MDF ফাইল attach করা হচ্ছে...")
            attach_query = f"""
            CREATE DATABASE [{db_name}] ON 
            (FILENAME = '{mdf_path}'),
            (FILENAME = '{ldf_path}')
            FOR ATTACH;
            """
            cursor.execute(attach_query)
            print(f"   ✅ Database attached!")
        
        # Re-enable autocommit
        conn.autocommit = False
        
        # Database এ switch করা
        cursor.execute(f"USE [{db_name}]")
        
        # সব টেবিলের লিস্ট দেখা
        print("\n📋 টেবিল লিস্ট:")
        cursor.execute("""
            SELECT TABLE_SCHEMA, TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """)
        
        tables = cursor.fetchall()
        print(f"\n✅ মোট {len(tables)}টি টেবিল পাওয়া গেছে:\n")
        
        for i, (schema, table) in enumerate(tables, 1):
            print(f"{i}. {schema}.{table}")
        
        # প্রথম টেবিল থেকে স্যাম্পল ডেটা
        if tables:
            schema, table_name = tables[0]
            full_table = f"[{schema}].[{table_name}]"
            
            print(f"\n🔍 '{table_name}' টেবিল থেকে স্যাম্পল ডেটা পড়া হচ্ছে...")
            
            query = f"SELECT TOP 100 * FROM {full_table}"
            df = pd.read_sql(query, conn)
            
            # Excel এ সেভ করা
            output_file = f"Sample_Data_{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df.to_excel(output_file, index=False)
            
            print(f"\n🎉 সফল!")
            print(f"📄 ফাইল: {output_file}")
            print(f"📊 রো: {len(df)}, কলাম: {len(df.columns)}")
            print(f"\n📝 কলাম নাম: {', '.join(df.columns.tolist())}")
            
            # প্রথম কিছু রো দেখানো
            print("\n" + "=" * 70)
            print("স্যাম্পল ডেটা (প্রথম 5 রো):")
            print("=" * 70)
            print(df.head().to_string())
            
            return True
        
        conn.close()
        
    except ImportError:
        print("\n⚠️ pyodbc লাইব্রেরি ইনস্টল করা নেই!")
        print("\nইনস্টল করতে:")
        print("pip install pyodbc")
        return False
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def main():
    print("=" * 70)
    print("SQL Server MDF ফাইল রিডার (LocalDB দিয়ে)")
    print("=" * 70)
    
    mdf_path = r"c:\Users\Irak\Desktop\Barishal April Data\Data\ERPonTheNet_Data.MDF"
    ldf_path = r"c:\Users\Irak\Desktop\Barishal April Data\Data\ERPonTheNet_log.LDF"
    
    # ফাইল চেক করা
    if not os.path.exists(mdf_path):
        print(f"❌ MDF ফাইল পাওয়া যায়নি: {mdf_path}")
        return
    
    if not os.path.exists(ldf_path):
        print(f"❌ LDF ফাইল পাওয়া যায়নি: {ldf_path}")
        return
    
    print(f"\n✅ ফাইল পাওয়া গেছে:")
    print(f"   MDF: {os.path.getsize(mdf_path) / (1024*1024):.2f} MB")
    print(f"   LDF: {os.path.getsize(ldf_path) / (1024*1024):.2f} MB")
    
    # LocalDB চেক করা
    if not check_localdb():
        print("\n⚠️ SQL Server LocalDB পাওয়া যায়নি")
        install_localdb_guide()
        return
    
    print("\n✅ LocalDB পাওয়া গেছে!")
    
    # MDF পড়া
    attach_and_read_mdf(mdf_path, ldf_path)


if __name__ == "__main__":
    main()
