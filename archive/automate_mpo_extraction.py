# পুরোনো সফটওয়্যার থেকে ২০০০ MPO এর ডেটা অটোমেটিক এক্সট্র্যাক্ট
# SQL Server ছাড়াই কাজ করবে - শুধু Python লাগবে

import pyautogui
import time
import pandas as pd
import pyperclip
from datetime import datetime

# প্রথমে ইনস্টল করতে হবে:
# pip install pyautogui pandas openpyxl pyperclip pillow

class MPODataExtractor:
    def __init__(self, mpo_list_file):
        """
        Parameters:
        - mpo_list_file: MPO আইডি গুলোর Excel/CSV ফাইল
        """
        # MPO লিস্ট লোড করা
        if mpo_list_file.endswith('.xlsx'):
            self.mpo_df = pd.read_excel(mpo_list_file)
        else:
            self.mpo_df = pd.read_csv(mpo_list_file)
        
        self.mpo_list = self.mpo_df.iloc[:, 0].tolist()
        self.extracted_data = []
        
        print(f"✅ {len(self.mpo_list)}টি MPO লোড হয়েছে")
        
    def setup_software_window(self):
        """
        পুরোনো সফটওয়্যার উইন্ডো খোঁজা এবং ফোকাস করা
        """
        print("\n⚠️ গুরুত্বপূর্ণ নির্দেশনা:")
        print("1. আপনার পুরোনো সফটওয়্যার ওপেন করুন")
        print("2. যেখানে MPO আইডি টাইপ করতে হয় সেই স্ক্রিনে যান")
        print("3. কার্সর সেই ইনপুট বক্সে রাখুন")
        print("\n10 সেকেন্ড পর অটোমেশন শুরু হবে...")
        
        for i in range(10, 0, -1):
            print(f"{i}...", end=" ", flush=True)
            time.sleep(1)
        print("\n\n🚀 শুরু হচ্ছে!")
        
    def extract_single_mpo(self, mpo_id):
        """
        একটি MPO এর ডেটা এক্সট্র্যাক্ট করা
        """
        try:
            # পুরোনো টেক্সট মুছে ফেলা (Ctrl+A, Delete)
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.2)
            pyautogui.press('delete')
            time.sleep(0.2)
            
            # MPO আইডি টাইপ করা
            pyautogui.write(str(mpo_id), interval=0.1)
            time.sleep(0.3)
            
            # Enter চাপা (অথবা আপনার সফটওয়্যারে যে কমান্ড লাগে)
            pyautogui.press('enter')
            time.sleep(2)  # ডেটা লোড হওয়ার জন্য অপেক্ষা
            
            # ডেটা সিলেক্ট করা (Ctrl+A)
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.3)
            
            # কপি করা (Ctrl+C)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.5)
            
            # ক্লিপবোর্ড থেকে ডেটা নেওয়া
            data = pyperclip.paste()
            
            return {
                'MPO_ID': mpo_id,
                'Extracted_Data': data,
                'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'Status': 'Success'
            }
            
        except Exception as e:
            return {
                'MPO_ID': mpo_id,
                'Extracted_Data': '',
                'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'Status': f'Error: {str(e)}'
            }
    
    def extract_all(self, output_file='extracted_mpo_data.xlsx'):
        """
        সব MPO এর ডেটা এক্সট্র্যাক্ট করা
        """
        self.setup_software_window()
        
        total = len(self.mpo_list)
        
        for i, mpo_id in enumerate(self.mpo_list, 1):
            print(f"\n[{i}/{total}] Processing MPO: {mpo_id}")
            
            result = self.extract_single_mpo(mpo_id)
            self.extracted_data.append(result)
            
            # প্রতি 100 MPO পর পর সেভ করা (যাতে ডেটা হারিয়ে না যায়)
            if i % 100 == 0:
                self.save_data(f'backup_{i}_{output_file}')
                print(f"✅ Backup saved: {i} MPOs processed")
        
        # ফাইনাল সেভ
        self.save_data(output_file)
        print(f"\n\n🎉 সম্পন্ন! সব ডেটা '{output_file}' ফাইলে সেভ হয়েছে")
        
    def save_data(self, filename):
        """
        ডেটা Excel ফাইলে সেভ করা
        """
        df = pd.DataFrame(self.extracted_data)
        df.to_excel(filename, index=False)


# ========================
# ব্যবহার করার নিয়ম:
# ========================

def main():
    print("=" * 60)
    print("MPO ডেটা অটোমেটিক এক্সট্র্যাক্টর")
    print("=" * 60)
    
    # আপনার MPO লিস্ট ফাইলের নাম দিন
    mpo_list_file = input("\nMPO লিস্ট ফাইলের নাম লিখুন (যেমন: mpo_list.xlsx): ")
    
    if not os.path.exists(mpo_list_file):
        print(f"❌ Error: '{mpo_list_file}' ফাইল পাওয়া যায়নি!")
        print("\nপ্রথমে একটি Excel ফাইল তৈরি করুন যেখানে প্রথম কলামে সব MPO আইডি থাকবে")
        return
    
    # Extractor তৈরি করা
    extractor = MPODataExtractor(mpo_list_file)
    
    # এক্সট্র্যাকশন শুরু
    output_file = f"MPO_Data_Extracted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    extractor.extract_all(output_file)


if __name__ == "__main__":
    import os
    
    # প্রয়োজনীয় লাইব্রেরি চেক করা
    try:
        import pyautogui
        import pyperclip
        main()
    except ImportError:
        print("⚠️ প্রয়োজনীয় লাইব্রেরি ইনস্টল করা নেই!")
        print("\nএই কমান্ড চালান:")
        print("pip install pyautogui pandas openpyxl pyperclip pillow")
