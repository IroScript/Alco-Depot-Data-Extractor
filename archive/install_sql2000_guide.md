# SQL Server 2000 ইনস্টল করার গাইড

## 🎯 কেন SQL Server 2000?

আপনার MDF ফাইল **SQL Server 2000** (version 539) এ তৈরি। Modern SQL Server এটা পড়তে পারে না। তাই পুরোনো version লাগবে।

---

## 📥 অপশন ১: SQL Server 2005 Express (সবচেয়ে সহজ)

SQL Server 2000 এর চেয়ে 2005 ভালো কারণ:
- ✅ Windows 10/11 এ চলে
- ✅ SQL Server 2000 এর database পড়তে পারে
- ✅ ফ্রি এবং হালকা
- ✅ এখনও ডাউনলোড পাওয়া যায়

### ডাউনলোড লিংক:
```
https://www.microsoft.com/en-us/download/details.aspx?id=21844
```

অথবা direct link:
```
https://download.microsoft.com/download/3/c/c/3cc6b0cb-4c51-4c1f-a2e0-79c5e6e6c3e3/SQLEXPR_ADV.EXE
```

### ইনস্টল স্টেপ:

1. **SQLEXPR_ADV.EXE** ডাউনলোড করুন (প্রায় 250 MB)

2. রান করুন এবং এই অপশন সিলেক্ট করুন:
   - ✅ Database Engine Services
   - ✅ Management Tools (SQL Server Management Studio Express)
   - ❌ বাকি সব unchecked রাখুন

3. **Instance Name:** `SQLEXPRESS` (default রাখুন)

4. **Authentication Mode:** 
   - ✅ Windows Authentication Mode (সহজ)

5. ইনস্টল শেষ হলে কম্পিউটার restart করুন

---

## 📥 অপশন ২: SQL Server 2008 R2 Express (আরও ভালো)

এটি আরও stable এবং Windows 10/11 এ ভালো চলে।

### ডাউনলোড লিংক:
```
https://www.microsoft.com/en-us/download/details.aspx?id=30438
```

ফাইল: **SQLEXPR_x64_ENU.exe** (64-bit) অথবা **SQLEXPR_x86_ENU.exe** (32-bit)

### ইনস্টল স্টেপ:

1. ডাউনলোড করা ফাইল রান করুন

2. **New SQL Server stand-alone installation** সিলেক্ট করুন

3. **Feature Selection:**
   - ✅ Database Engine Services
   - ✅ Management Tools - Basic
   - ✅ Management Tools - Complete

4. **Instance Configuration:**
   - ✅ Default instance: `MSSQLSERVER`
   - অথবা Named instance: `SQLEXPRESS`

5. **Server Configuration:**
   - সব service এর জন্য **NT AUTHORITY\SYSTEM** সিলেক্ট করুন

6. **Database Engine Configuration:**
   - ✅ Windows authentication mode
   - ✅ Add Current User

7. Install করুন (15-20 মিনিট লাগবে)

---

## 📥 অপশন ৩: SQL Server 2000 (যদি একদমই পুরোনো চান)

⚠️ **সতর্কতা:** Windows 10/11 এ officially support করে না, কিন্তু compatibility mode এ চলতে পারে।

### ডাউনলোড:
- SQL Server 2000 এখন Microsoft officially provide করে না
- Archive.org থেকে পাওয়া যেতে পারে
- অথবা পুরোনো CD/DVD থাকলে সেটা ব্যবহার করুন

### Compatibility Mode এ চালানো:

1. Setup.exe এ right-click করুন
2. **Properties** → **Compatibility** tab
3. ✅ Run this program in compatibility mode for: **Windows XP (Service Pack 3)**
4. ✅ Run this program as an administrator
5. Apply → OK
6. Setup রান করুন

---

## 🔧 ইনস্টল হওয়ার পর

### ১. SQL Server চালু আছে কিনা চেক করুন:

```cmd
sc query MSSQLSERVER
```

অথবা

```cmd
sc query MSSQL$SQLEXPRESS
```

### ২. SQL Server Management Studio (SSMS) ওপেন করুন

- Start Menu → Microsoft SQL Server → SQL Server Management Studio

### ৩. Connect করুন:

- **Server name:** `localhost` অথবা `.\SQLEXPRESS`
- **Authentication:** Windows Authentication
- Click **Connect**

---

## 📊 MDF ফাইল Attach করা

### GUI Method (সহজ):

1. SSMS এ **Databases** folder এ right-click
2. **Attach...** সিলেক্ট করুন
3. **Add** button ক্লিক করুন
4. আপনার MDF ফাইল সিলেক্ট করুন:
   ```
   c:\Users\Irak\Desktop\Barishal April Data\Data\ERPonTheNet_Data.MDF
   ```
5. **OK** ক্লিক করুন

### SQL Command Method:

```sql
CREATE DATABASE ERPonTheNet ON 
(FILENAME = 'c:\Users\Irak\Desktop\Barishal April Data\Data\ERPonTheNet_Data.MDF'),
(FILENAME = 'c:\Users\Irak\Desktop\Barishal April Data\Data\ERPonTheNet_log.LDF')
FOR ATTACH;
```

---

## 🐍 Python দিয়ে ডেটা এক্সট্র্যাক্ট

ইনস্টল হওয়ার পর আমার তৈরি করা Python script চালান:

```cmd
python read_with_sql2005.py
```

এটি:
- ✅ SQL Server 2005/2008 এর সাথে connect করবে
- ✅ সব টেবিল লিস্ট করবে
- ✅ ডেটা Excel এ export করবে
- ✅ ২০০০ MPO এর ডেটা একসাথে বের করবে

---

## ❓ সমস্যা সমাধান

### Error: "SQL Server does not exist or access denied"

**সমাধান:**
```cmd
sc config MSSQLSERVER start= auto
net start MSSQLSERVER
```

### Error: "Cannot open database"

**সমাধান:**
- MDF এবং LDF ফাইল একই folder এ আছে কিনা চেক করুন
- File permissions চেক করুন (Read/Write access)

### Error: "Version not supported"

**সমাধান:**
- SQL Server 2005 বা 2008 ব্যবহার করুন (2000 এর চেয়ে ভালো)

---

## 💡 আমার সুপারিশ

**SQL Server 2008 R2 Express** ইনস্টল করুন কারণ:
- ✅ Windows 10/11 এ perfectly চলে
- ✅ SQL Server 2000 database পড়তে পারে
- ✅ Free এবং stable
- ✅ Management Studio included
- ✅ Python integration সহজ

---

## 📞 পরবর্তী পদক্ষেপ

1. SQL Server 2008 R2 Express ডাউনলোড করুন
2. ইনস্টল করুন (উপরের স্টেপ অনুসরণ করুন)
3. আমাকে জানান - আমি একটি Python script তৈরি করে দেব
4. Script চালিয়ে সব ডেটা Excel এ export করুন

কোনো সমস্যা হলে জানাবেন! 💪
