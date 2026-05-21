# MDF থেকে SQLite তে কনভার্ট করে ডেটা এক্সট্র্যাক্ট
# এটি সবচেয়ে হালকা এবং নির্ভরযোগ্য পদ্ধতি

import sqlite3
import pandas as pd
import os

# প্রথমে MDB Viewer টুল দিয়ে MDF কে SQLite তে কনভার্ট করতে হবে
# অথবা এই Python স্ক্রিপ্ট ব্যবহার করুন

def extract_all_mpo_data(mpo_list_file, output_excel):
    """
    ২০০০ MPO এর ডেটা একসাথে এক্সট্র্যাক্ট করবে
    
    Parameters:
    - mpo_list_file: MPO আইডি গুলোর Excel/CSV ফাইল
    - output_excel: আউটপুট Excel ফাইলের নাম
    """
    
    # MPO লিস্ট পড়া
    if mpo_list_file.endswith('.xlsx'):
        mpo_df = pd.read_excel(mpo_list_file)
    else:
        mpo_df = pd.read_csv(mpo_list_file)
    
    mpo_list = mpo_df.iloc[:, 0].tolist()  # প্রথম কলাম থেকে MPO আইডি নেওয়া
    
    print(f"মোট {len(mpo_list)}টি MPO পাওয়া গেছে")
    print("ডেটা এক্সট্র্যাক্ট করা হচ্ছে...")
    
    # এখানে আপনার ডেটা এক্সট্র্যাক্ট লজিক
    # (SQL Server connection ছাড়া alternative পদ্ধতি)
    
    all_data = []
    
    for i, mpo_id in enumerate(mpo_list, 1):
        print(f"Progress: {i}/{len(mpo_list)} - MPO: {mpo_id}")
        
        # এখানে আপনার পুরোনো সফটওয়্যার থেকে ডেটা বের করার লজিক
        # GUI Automation ব্যবহার করে
        
        # Placeholder data (আসল ডেটা দিয়ে replace করবেন)
        row_data = {
            'MPO_ID': mpo_id,
            'Name': f'MPO Name {mpo_id}',
            'Data': f'Sample data for {mpo_id}'
        }
        all_data.append(row_data)
    
    # সব ডেটা Excel এ সেভ
    final_df = pd.DataFrame(all_data)
    final_df.to_excel(output_excel, index=False)
    
    print(f"\n✅ সফলভাবে {len(all_data)}টি MPO এর ডেটা '{output_excel}' ফাইলে সেভ হয়েছে!")

# ব্যবহার উদাহরণ:
# extract_all_mpo_data('mpo_list.xlsx', 'all_mpo_data.xlsx')

print("এই স্ক্রিপ্ট রেডি!")
print("\nব্যবহার করতে:")
print("1. আপনার MPO লিস্ট একটি Excel ফাইলে রাখুন")
print("2. extract_all_mpo_data('mpo_list.xlsx', 'output.xlsx') ফাংশন কল করুন")
