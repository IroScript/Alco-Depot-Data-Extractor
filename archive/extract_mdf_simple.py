# MDF ফাইল থেকে সরাসরি ডেটা এক্সট্র্যাক্ট করার স্ক্রিপ্ট
# SQL Server ছাড়াই কাজ করবে

import subprocess
import os

# প্রথমে mdf-reader ইনস্টল করতে হবে
# কমান্ড: pip install mdf-reader

try:
    from mdf_reader import MDFReader
    
    # আপনার MDF ফাইলের পাথ
    mdf_path = r"c:\Users\Irak\Desktop\Barishal April Data\Data\ERPonTheNet_Data.MDF"
    
    # MDF ফাইল ওপেন করা
    print("MDF ফাইল পড়া হচ্ছে...")
    reader = MDFReader(mdf_path)
    
    # সব টেবিলের নাম দেখা
    tables = reader.get_tables()
    print(f"\nমোট {len(tables)}টি টেবিল পাওয়া গেছে:")
    for i, table in enumerate(tables, 1):
        print(f"{i}. {table}")
    
    # একটি নির্দিষ্ট টেবিল থেকে ডেটা পড়া
    # (আপনার MPO ডেটা যে টেবিলে আছে সেটার নাম দিন)
    table_name = input("\nকোন টেবিল থেকে ডেটা বের করবেন? টেবিলের নাম লিখুন: ")
    
    data = reader.read_table(table_name)
    
    # Excel এ সেভ করা
    import pandas as pd
    df = pd.DataFrame(data)
    output_file = f"{table_name}_data.xlsx"
    df.to_excel(output_file, index=False)
    
    print(f"\n✅ ডেটা সফলভাবে '{output_file}' ফাইলে সেভ হয়েছে!")
    print(f"মোট {len(df)} টি রো পাওয়া গেছে")
    
except ImportError:
    print("⚠️ mdf-reader লাইব্রেরি ইনস্টল করা নেই!")
    print("\nইনস্টল করতে এই কমান্ড চালান:")
    print("pip install mdf-reader pandas openpyxl")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nবিকল্প পদ্ধতি ব্যবহার করুন (নিচে দেখুন)")
