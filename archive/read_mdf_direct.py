# SQL Server MDF ফাইল থেকে সরাসরি ডেটা পড়া
# SQL Server ইনস্টল ছাড়াই কাজ করবে

import os
import struct
import pandas as pd
from datetime import datetime

class SimpleMDFReader:
    """
    SQL Server MDF ফাইলের বেসিক স্ট্রাকচার পড়ার জন্য
    """
    
    def __init__(self, mdf_path):
        self.mdf_path = mdf_path
        self.file_size = os.path.getsize(mdf_path)
        
    def read_header(self):
        """MDF ফাইলের হেডার ইনফরমেশন পড়া"""
        with open(self.mdf_path, 'rb') as f:
            # প্রথম 8192 bytes হলো file header page
            header = f.read(8192)
            
            # বেসিক ইনফরমেশন
            info = {
                'File Size': f'{self.file_size / (1024*1024):.2f} MB',
                'File Path': self.mdf_path,
                'Page Size': '8 KB (SQL Server Standard)',
                'Total Pages': self.file_size // 8192,
            }
            
            return info
    
    def extract_sample_data(self, num_pages=100):
        """
        MDF ফাইল থেকে স্যাম্পল ডেটা এক্সট্র্যাক্ট করা
        """
        data_found = []
        
        with open(self.mdf_path, 'rb') as f:
            # প্রথম কিছু পেজ স্ক্যান করা
            for page_num in range(min(num_pages, self.file_size // 8192)):
                f.seek(page_num * 8192)
                page_data = f.read(8192)
                
                # ASCII টেক্সট খোঁজা (printable characters)
                text = self._extract_text(page_data)
                
                if text and len(text) > 10:  # যদি কোনো টেক্সট পাওয়া যায়
                    data_found.append({
                        'Page': page_num,
                        'Data': text[:200],  # প্রথম 200 characters
                        'Length': len(text)
                    })
        
        return data_found
    
    def _extract_text(self, data):
        """বাইনারি ডেটা থেকে টেক্সট বের করা"""
        try:
            # Printable ASCII characters খোঁজা
            text = ''
            for byte in data:
                if 32 <= byte <= 126:  # Printable ASCII range
                    text += chr(byte)
                elif byte == 0 and len(text) > 0:
                    text += ' '
            
            # খালি স্পেস রিমুভ করা
            text = ' '.join(text.split())
            return text
        except:
            return ''


def main():
    print("=" * 70)
    print("SQL Server MDF ফাইল রিডার (SQL Server ছাড়াই)")
    print("=" * 70)
    
    mdf_path = r"c:\Users\Irak\Desktop\Barishal April Data\Data\ERPonTheNet_Data.MDF"
    
    if not os.path.exists(mdf_path):
        print(f"❌ Error: MDF ফাইল পাওয়া যায়নি!")
        print(f"Path: {mdf_path}")
        return
    
    print(f"\n📁 ফাইল পাওয়া গেছে: {os.path.basename(mdf_path)}")
    print(f"📊 সাইজ: {os.path.getsize(mdf_path) / (1024*1024):.2f} MB")
    
    # MDF Reader তৈরি করা
    reader = SimpleMDFReader(mdf_path)
    
    # হেডার ইনফরমেশন পড়া
    print("\n" + "=" * 70)
    print("📋 ফাইল ইনফরমেশন:")
    print("=" * 70)
    
    header_info = reader.read_header()
    for key, value in header_info.items():
        print(f"{key}: {value}")
    
    # স্যাম্পল ডেটা এক্সট্র্যাক্ট করা
    print("\n" + "=" * 70)
    print("🔍 ডেটা এক্সট্র্যাক্ট করা হচ্ছে...")
    print("=" * 70)
    
    sample_data = reader.extract_sample_data(num_pages=500)
    
    if sample_data:
        print(f"\n✅ {len(sample_data)} টি পেজে ডেটা পাওয়া গেছে!")
        
        # DataFrame তৈরি করা
        df = pd.DataFrame(sample_data)
        
        # Excel এ সেভ করা
        output_file = f"MDF_Extracted_Data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(output_file, index=False)
        
        print(f"\n🎉 সফল! ডেটা এক্সপোর্ট হয়েছে:")
        print(f"📄 ফাইল: {output_file}")
        print(f"📊 মোট রো: {len(df)}")
        
        # প্রথম কিছু ডেটা দেখানো
        print("\n" + "=" * 70)
        print("📝 স্যাম্পল ডেটা (প্রথম 5 রো):")
        print("=" * 70)
        print(df.head().to_string())
        
        # ফাইল ওপেন করা
        print(f"\n💡 Excel ফাইল ওপেন করতে:")
        print(f'   start excel "{output_file}"')
        
    else:
        print("\n⚠️ কোনো readable ডেটা পাওয়া যায়নি")
        print("\nসম্ভাব্য কারণ:")
        print("1. ফাইলটি এনক্রিপ্টেড হতে পারে")
        print("2. ডেটা কম্প্রেসড ফরম্যাটে আছে")
        print("3. SQL Server ছাড়া পড়া সম্ভব নয়")
        
        print("\n💡 বিকল্প সমাধান:")
        print("1. SQL Server Express (ফ্রি) ইনস্টল করুন")
        print("2. অথবা যে কম্পিউটারে সফটওয়্যার আছে সেখান থেকে ডেটা এক্সপোর্ট করুন")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
