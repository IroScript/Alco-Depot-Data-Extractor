# দ্রুত টেস্ট - MDF ফাইল থেকে কিছু ডেটা দেখা
# কোনো ইনস্টলেশন ছাড়াই

import os
import pandas as pd
from datetime import datetime

def extract_strings_from_mdf(mdf_path, min_length=5):
    """
    MDF ফাইল থেকে সব readable strings বের করা
    """
    print(f"📖 ফাইল পড়া হচ্ছে: {os.path.basename(mdf_path)}")
    print(f"📊 সাইজ: {os.path.getsize(mdf_path) / (1024*1024):.2f} MB")
    print("\n⏳ এটি কিছু সময় নিতে পারে...\n")
    
    strings_found = []
    current_string = ""
    
    with open(mdf_path, 'rb') as f:
        # ফাইলের প্রথম 10 MB পড়া (দ্রুত টেস্টের জন্য)
        chunk_size = 10 * 1024 * 1024  # 10 MB
        data = f.read(chunk_size)
        
        for byte in data:
            # Printable ASCII characters
            if 32 <= byte <= 126:
                current_string += chr(byte)
            else:
                if len(current_string) >= min_length:
                    # শুধু meaningful strings রাখা
                    if any(c.isalpha() for c in current_string):
                        strings_found.append(current_string.strip())
                current_string = ""
        
        # শেষ string
        if len(current_string) >= min_length:
            strings_found.append(current_string.strip())
    
    return strings_found

def analyze_strings(strings):
    """
    Strings analyze করে টেবিল/কলাম নাম খোঁজা
    """
    # সম্ভাব্য টেবিল নাম (SQL keywords এর পরে)
    table_keywords = ['CREATE TABLE', 'FROM', 'INSERT INTO', 'UPDATE', 'DELETE FROM']
    
    # সম্ভাব্য কলাম নাম (ছোট strings যেগুলো identifier এর মতো)
    potential_columns = []
    potential_tables = []
    potential_data = []
    
    for s in strings:
        # টেবিল নাম খোঁজা
        for keyword in table_keywords:
            if keyword in s.upper():
                potential_tables.append(s)
                break
        
        # Identifier এর মতো (letters, numbers, underscore)
        if s.replace('_', '').replace(' ', '').isalnum() and len(s) < 50:
            if '_' in s or s[0].isupper():
                potential_columns.append(s)
        
        # ডেটা এর মতো (longer strings)
        if len(s) > 10 and len(s) < 200:
            potential_data.append(s)
    
    return {
        'tables': list(set(potential_tables))[:20],
        'columns': list(set(potential_columns))[:50],
        'data': list(set(potential_data))[:100]
    }

def main():
    print("=" * 70)
    print("🚀 Quick MDF Data Viewer")
    print("=" * 70)
    print("\nএটি একটি দ্রুত টেস্ট - MDF ফাইল থেকে readable text বের করবে")
    print("পুরো ডেটা এক্সট্র্যাক্ট করতে SQL Server LocalDB লাগবে\n")
    
    mdf_path = r"c:\Users\Irak\Desktop\Barishal April Data\Data\ERPonTheNet_Data.MDF"
    
    if not os.path.exists(mdf_path):
        print(f"❌ ফাইল পাওয়া যায়নি: {mdf_path}")
        return
    
    # Strings extract করা
    print("🔍 ডেটা এক্সট্র্যাক্ট করা হচ্ছে...\n")
    strings = extract_strings_from_mdf(mdf_path)
    
    print(f"✅ মোট {len(strings)}টি readable strings পাওয়া গেছে!\n")
    
    # Analyze করা
    print("🔬 ডেটা analyze করা হচ্ছে...\n")
    analysis = analyze_strings(strings)
    
    # Results দেখানো
    print("=" * 70)
    print("📋 সম্ভাব্য টেবিল নাম:")
    print("=" * 70)
    for i, table in enumerate(analysis['tables'][:10], 1):
        print(f"{i}. {table}")
    
    print("\n" + "=" * 70)
    print("📝 সম্ভাব্য কলাম নাম:")
    print("=" * 70)
    for i, col in enumerate(analysis['columns'][:20], 1):
        print(f"{i}. {col}")
    
    print("\n" + "=" * 70)
    print("💾 স্যাম্পল ডেটা:")
    print("=" * 70)
    for i, data in enumerate(analysis['data'][:20], 1):
        print(f"{i}. {data[:100]}...")
    
    # Excel এ সেভ করা
    output_file = f"MDF_Strings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    # DataFrame তৈরি করা
    max_len = max(len(analysis['tables']), len(analysis['columns']), len(analysis['data']))
    
    df = pd.DataFrame({
        'Possible_Tables': analysis['tables'] + [''] * (max_len - len(analysis['tables'])),
        'Possible_Columns': analysis['columns'] + [''] * (max_len - len(analysis['columns'])),
        'Sample_Data': analysis['data'] + [''] * (max_len - len(analysis['data']))
    })
    
    df.to_excel(output_file, index=False)
    
    print(f"\n🎉 ডেটা সেভ হয়েছে: {output_file}")
    print(f"📊 মোট রো: {len(df)}")
    
    print("\n" + "=" * 70)
    print("💡 পরবর্তী পদক্ষেপ:")
    print("=" * 70)
    print("1. Excel ফাইল খুলে দেখুন কী ডেটা আছে")
    print("2. সম্পূর্ণ ডেটা এক্সট্র্যাক্ট করতে:")
    print("   - SQL Server LocalDB ইনস্টল করুন (50 MB, ফ্রি)")
    print("   - তারপর 'read_with_localdb.py' চালান")
    print("\n3. অথবা যে কম্পিউটারে সফটওয়্যার আছে সেখান থেকে:")
    print("   - 'automate_mpo_extraction.py' ব্যবহার করুন")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
