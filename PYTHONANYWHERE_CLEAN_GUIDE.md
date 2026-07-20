# PythonAnywhere (PA) আলটিমেট ডিপ্লয়মেন্ট ও ফুল কনফিগারেশন গাইড (Merged & Detailed)

এই গাইডটি আপনার লোকাল প্রজেক্টটিকে PythonAnywhere হোস্টিং-এ সফলভাবে ডিপ্লয় করার জন্য প্রস্তুত করা হয়েছে। এখানে সম্পূর্ণ প্রক্রিয়াটিকে **৩০টি সুনির্দিষ্ট ধাপে** ভাগ করা হয়েছে যাতে পরবর্তীতে কোনো ভুল বা বিভ্রান্তি না ঘটে।

---

## 🛠️ সম্পূর্ণ ৩০-ধাপের সেটআপ গাইড

### পার্ট ১: লোকাল পিসি ও ফাইল প্রিপারেশন
1. **লোকাল ফাইল ক্লিনআপ:** লোকাল পিসিতে প্রজেক্টের অপ্রয়োজনীয় বড় ফাইল বা ডুপ্লিকেট ব্যাকআপ ফাইলগুলো (যেমন: প্রসেস করার পর তৈরি হওয়া বড় CSV ফাইলগুলো) ডিলিট বা অন্য ডিরেক্টরিতে সরিয়ে ফেলুন।
2. **ডিপ্লয়মেন্ট স্ক্রিপ্ট চেক:** আপনার প্রজেক্টের রুট ডিরেক্টরিতে [deploy.py](file:///C:/Users/Irak/Desktop/Alco_Depot_Data_Extractor_From_Git/Alco-Depot-Data-Extractor-main/deploy.py) ফাইলটি আছে কিনা নিশ্চিত করুন।
3. **লোকাল এনভায়রনমেন্ট কনফিগারেশন:** `googleDrive/env` ফাইলে PythonAnywhere-এর ইউজারনেম এবং API টোকেন যোগ করুন:
   ```ini
   PYTHONANYWHERE_USERNAME=storealco
   PYTHONANYWHERE_API_TOKEN=আপনার_এপিআই_টোকেন
   ```
   *(টোকেনটি পাবেন: PythonAnywhere Account Settings -> API token tab -> Create token)*
4. **লোকাল ডিপ্লয়মেন্ট স্ক্রিপ্ট রান:** লোকাল পিসিতে টার্মিনাল বা PowerShell খুলে নিচের কমান্ডটি রান করুন:
   ```bash
   python deploy.py
   ```
5. **জিপ ফাইল আপলোড নিশ্চিতকরণ:** স্ক্রিপ্টটি সফলভাবে রান হলে এটি প্রজেক্টের প্রয়োজনীয় ফাইলগুলোকে `erp_setup.zip` নামে জিপ করে PythonAnywhere-এ আপলোড করে দেবে। আপলোড সফল হয়েছে কিনা তা PythonAnywhere-এর **Files** ট্যাবে গিয়ে চেক করুন।

### পার্ট ২: PythonAnywhere ড্যাশবোর্ড ও কনসোল সেটআপ
6. **PythonAnywhere লগইন:** ব্রাউজারে PythonAnywhere-এ লগইন করুন এবং ড্যাশবোর্ডে যান।
7. **কনসোল ট্যাবে প্রবেশ:** ড্যাশবোর্ড থেকে **Consoles** ট্যাবে ক্লিক করুন।
8. **Bash Console ওপেন:** Consoles সেকশন থেকে একটি নতুন **Bash Console** ওপেন করুন।
9. **হোম ডিরেক্টরিতে প্রবেশ:** Bash কনসোলে নিচের কমান্ডটি রান করে হোম ডিরেক্টরিতে অবস্থান নিশ্চিত করুন:
   ```bash
   cd ~
   ```
10. **জিপ ফাইল এক্সট্র্যাক্ট:** হোম ডিরেক্টরিতে আপলোড করা জিপ ফাইলটি আনজিপ করতে রান করুন:
    ```bash
    unzip -o erp_setup.zip
    ```
11. **ফাইল যাচাইকরণ:** এক্সট্র্যাক্ট করা ফাইলগুলোর লিস্ট দেখতে রান করুন:
    ```bash
    ls -la
    ```

### পার্ট ৩: ভার্চুয়াল এনভায়রনমেন্ট (venv) তৈরি ও অ্যাক্টিভেট করা
12. **ভার্চুয়াল এনভায়রনমেন্ট তৈরি:** Python 3.12 সংস্করণ ব্যবহার করে একটি নতুন ভার্চুয়াল এনভায়রনমেন্ট তৈরি করুন:
    ```bash
    mkvirtualenv --python=python3.12 erp_env
    ```
13. **ভার্চুয়াল এনভায়রনমেন্ট অ্যাক্টিভেট:** যদি ভেনভ তৈরি করার পর অটো-অ্যাক্টিভেট না হয়, তবে রান করুন:
    ```bash
    workon erp_env
    ```

### পার্ট ৪: প্যাকেজ ইনস্টলেশন বিকল্পসমূহ (গুরুত্বপূর্ণ)
14. **অপশন ১: শুধুমাত্র সার্ভার চাইলে (সর্বনিম্ন প্যাকেজ ইনস্টলেশন):**
    যদি আপনি প্রজেক্টের এক্সট্রাকশন বা টেলিগ্রাম বট রান না করে শুধুমাত্র FastAPI সার্ভার ও ড্যাশবোর্ড সচল রাখতে চান, তবে শুধু এই প্যাকেজগুলো ইনস্টল করুন:
    ```bash
    pip install fastapi a2wsgi asgiref uvicorn
    ```
15. **অপশন ২: সার্ভার + টেলিগ্রাম বট চাইলে:**
    যদি আপনি এপিআই সার্ভারের সাথে টেলিগ্রাম বটের মাধ্যমে কুয়েরি করার সুবিধাও চান, তবে নিচের কমান্ডটি রান করুন:
    ```bash
    pip install fastapi a2wsgi asgiref uvicorn requests pandas openpyxl
    ```
16. **অপশন ৩: ফুল প্রজেক্ট চাইলে (গুগল ড্রাইভ সিঙ্ক, শিট ডাউনলোড ও এক্সট্রাকশন সহ):**
    যদি আপনি ড্রাইভ অটোমেশন, গুগল শিট থেকে ডাটা ডাউনলোড এবং সম্পূর্ণ ডাটা এনালাইসিস ক্লাউডেই করতে চান, তবে সব প্যাকেজ ইনস্টল করুন:
    ```bash
    pip install fastapi a2wsgi asgiref uvicorn requests pandas openpyxl gspread google-auth google-api-python-client google-auth-httplib2
    ```

### 📋 প্যাকেজ ইনস্টলেশন সারাংশ
* **Only Server (FastAPI):** `fastapi`, `a2wsgi`, `asgiref`, `uvicorn`
* **Telegram Bot:** `requests`, `pandas`, `openpyxl` (প্লাস সার্ভার প্যাকেজসমূহ)
* **Full Automation/Google Sync:** `gspread`, `google-auth`, `google-api-python-client`, `google-auth-httplib2` (প্লাস উপরের সব)

---

### পার্ট ৫: Web App তৈরি ও ভার্চুয়াল এনভায়রনমেন্ট লিংক করা
17. **ওয়েব অ্যাপ তৈরি শুরু:** PythonAnywhere-এর **Web** ট্যাবে যান।
18. **নতুন অ্যাপ যোগ করা:** **Add a new web app** বাটনে ক্লিক করুন।
19. **ম্যানুয়াল কনফিগারেশন:** কনফিগারেশন টাইপ হিসেবে **Manual configuration** সিলেক্ট করুন (এটি অত্যন্ত গুরুত্বপূর্ণ, সরাসরি FastAPI সিলেক্ট করবেন না)।
20. **পাইথন সংস্করণ নির্বাচন:** পাইথন সংস্করণ হিসেবে **Python 3.12** সিলেক্ট করুন এবং নেক্সট চাপুন।
21. **ভার্চুয়াল এনভায়রনমেন্ট পাথ সেট:** Web ট্যাবের নিচে স্ক্রল করে **Virtualenv** সেকশনে যান। পাথ হিসেবে লিখুন:
    `/home/storealco/.virtualenvs/erp_env`
    এবং টিক চিহ্নে ক্লিক করে সেভ করুন।

### পার্ট ৬: WSGI কনফিগারেশন ফাইল এডিট ও কোড বসানো
22. **WSGI ফাইল ওপেন:** Web ট্যাবের **Code** সেকশনে থাকা **WSGI configuration file** এর লিঙ্কে ক্লিক করুন।
23. **কোড পেস্ট:** এডিটরের পূর্ববর্তী সমস্ত কোড মুছে ফেলুন এবং নিচের ইউনিভার্সাল WSGI কোডটি পেস্ট করুন:
    ```python
    # -*- coding: utf-8 -*-
    import sys
    import os

    PROJECT_HOME = '/home/storealco'
    FASTAPI_DIR = os.path.join(PROJECT_HOME, 'fastapi_gateway')

    for p in (PROJECT_HOME, FASTAPI_DIR):
        if p not in sys.path:
            sys.path.insert(0, p)

    os.chdir(PROJECT_HOME)

    # Virtualenv Activation
    VENV_CANDIDATES = [
        '/home/storealco/.virtualenvs/erp_env',
        '/home/storealco/.virtualenvs/alco_env',
    ]

    activated = False
    for venv in VENV_CANDIDATES:
        activate_this = os.path.join(venv, 'bin', 'activate_this.py')
        if os.path.exists(activate_this):
            try:
                with open(activate_this) as f:
                    exec(f.read(), {'__file__': activate_this})
                sys.stderr.write(f"\n[OK] Virtualenv activated: {venv}\n")
                activated = True
                break
            except Exception as e:
                sys.stderr.write(f"\n[!] venv activate failed ({venv}): {e}\n")

    if not activated:
        sys.stderr.write("\n[!] No virtualenv found.\n")

    # FastAPI App Loading using a2wsgi
    try:
        from fastapi_gateway.main import app
        from a2wsgi import ASGIMiddleware
        application = ASGIMiddleware(app)
        sys.stderr.write("\n[OK] FastAPI app loaded successfully via a2wsgi.\n")
    except Exception as e:
        sys.stderr.write(f"\n[!] FastAPI app load failed: {e}\n")
        raise
    ```
24. **WSGI ফাইল সেভ:** এডিটরের উপরে থাকা **Save** বাটনে ক্লিক করে ফাইলটি সংরক্ষণ করুন।

### পার্ট ৭: স্ট্যাটিক ফাইল ও ড্যাশবোর্ড কনফিগারেশন
25. **রুট URL স্ট্যাটিক রুল:** Web ট্যাবের **Static files** সেকশনে গিয়ে প্রথম রুলটি যোগ করুন:
    * **URL:** `/`
    * **Directory:** `/home/storealco/Dashboard`
26. **static/ URL স্ট্যাটিক রুল:** একই সেকশনে ড্যাশবোর্ডের রিসোর্সের জন্য দ্বিতীয় রুলটি যোগ করুন:
    * **URL:** `/static/`
    * **Directory:** `/home/storealco/Dashboard/`
    *(এটি রুট ডোমেইনেই আপনার ভিজ্যুয়াল ড্যাশবোর্ড লোড হওয়া নিশ্চিত করবে।)*

### পার্ট ৮: সিক্রেটস ও ডাটাবেস ভেরিফিকেশন
27. **এনভায়রনমেন্ট ফাইল যাচাই:** নিশ্চিত করুন যে `/home/storealco/googleDrive/env` ফাইলটি সঠিক এপিআই কী ও টেলিগ্রাম বট টোকেন সহ তৈরি করা আছে।
28. **ডাটাবেস চেক:** প্রজেক্ট রুটে `sales.db` ডাটাবেস ফাইলটি সঠিক সাইজে উপস্থিত আছে কিনা দেখে নিন।

### পার্ট ৯: টেলিগ্রাম বট চালুকরণ
29. **বট রান করা:** PythonAnywhere-এর Consoles ট্যাব থেকে আরেকটি নতুন Bash Console খুলে নিচের কমান্ড দিয়ে বটটি ব্যাকগ্রাউন্ডে সবসময় সচল রাখুন:
    ```bash
    workon erp_env
    nohup python telegram_bot.py > bot.log 2>&1 &
    ```
    *(ফ্রি অ্যাকাউন্টে ব্যাকগ্রাউন্ড প্রসেস বন্ধ হয়ে গেলে এই কনসোলে এসে আবার রান করে দিতে হবে।)*

### পার্ট ১০: রিলোড ও চূড়ান্ত টেস্টিং
30. **ওয়েব অ্যাপ রিলোড ও লাইভ চেক:** Web ট্যাবে ফিরে গিয়ে একদম উপরে থাকা সবুজ **Reload storealco.pythonanywhere.com** বাটনে ক্লিক করুন। ব্রাউজারে `https://storealco.pythonanywhere.com/` ভিজিট করে আপনার ড্যাশবোর্ড ও সার্ভার লাইভ দেখুন।

---

## ❓ সাধারণ প্রশ্ন ও সমাধান

* **প্রশ্ন: সার্ভারের ডাটা কি সরাসরি গুগল শিট থেকে প্রতিবার ফেচ হচ্ছে?**
  * **উত্তর:** না। সার্ভারটি সরাসরি প্রতিবার গুগল শিট থেকে ডাটা ফেচ করে না। প্রজেক্টের লোকাল রান বা এনালাইসিস পাইপলাইনটি (`auto_single_click_auto_run_no_need__following_steps.py` বা `step_2`) গুগল শিট থেকে ফিল্ড ফোর্স (Field Force) ও টার্গেট ডাটা ফেচ করে। এরপর লোকাল ডাটাবেস `sales.db` জেনারেট করে এবং সেটি গেটওয়ের মাধ্যমে সার্ভারে আপলোড করে। তাই সার্ভার সবসময় পারফর্ম্যান্সের স্বার্থে লোকাল এপিআই ডাটা বা আপলোড করা `sales.db` ব্যবহার করে কাজ করে।
