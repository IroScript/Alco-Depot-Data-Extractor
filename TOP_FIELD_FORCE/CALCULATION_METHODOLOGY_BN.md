# 📊 Alco Pharma — ড্যাশবোর্ডের হিসেব-নিকাশ ও ক্যালকুলেশন পদ্ধতি (Calculation Methodology)

আপনার নির্দেশনা অনুযায়ী **Top Field Force & Product Analytics Dashboard**-এ যে সকল হিসেব-নিকাশ করা হয়েছে, তার লজিক, বেস (Base), ফর্মুলা এবং কারণ নিচে বিস্তারিতভাবে ব্যাখ্যা করা হলো:

---

## ১. মূল ভিত্তি (Core Anchor): `product_code`

### 🔹 কী ধরেছি (Base & Grouping Rule):
প্রোডাক্ট লেভেলের সমস্ত ক্যালকুলেশনে প্রোডাক্টের নাম (`product_name`) ব্যবহার না করে **`product_code`**-কে প্রাইমারি কি (Primary Key) বা গ্রুপিংয়ের মূল ভিত্তি ধরা হয়েছে।
* **SQL ফর্মুলা:** `GROUP BY product_code`

### 💡 কেন করেছি (Why):
বিভিন্ন ডিপো বা ইনভয়েসে অনেক সময় প্রোডাক্টের নামের বানানে ছোটখাটো পার্থক্য, স্পেসের হেরফের বা ব্র্যাকেট (যেমন `ACIPRA 20 CAP` বনাম `ACIPRA 20CAP(New)`) থাকতে পারে। নাম ধরে হিসেব করলে একই ওষুধ দুইবার আলাদা হিসেবে চলে আসার ঝুঁকি থাকে। কিন্তু **`product_code` (যেমন `ACE1`, `AC01`, `DEJ1`) সবসময় অদ্বিতীয় (Unique) এবং অপরিবর্তিত থাকে**। তাই কোড দিয়ে গ্রুপ করায় আপনার প্রোডাক্ট ক্যালকুলেশন ১০০% নির্ভুল হয়েছে।

---

## ২. মোট সেলস বা রেভিনিউ (Total Net Sales / Revenue)

### 🔹 ফর্মুলা ও যোগ-বিয়োগ:
* **SQL ফর্মুলা:** `SUM(line_amount)`
* **যোগ-বিয়োগের নিয়ম:** ডেটাবেসের `sales` টেবিলের প্রতিটি লেনদেনের `line_amount` কলামের মান যোগ করা হয়েছে। 

### 💡 কেন করেছি:
ইনভয়েসের প্রতিটি লাইনে নির্দিষ্ট প্রোডাক্টের বিক্রয়মূল্য `line_amount`-এ সংরক্ষিত থাকে। ডেটাবেসে বিক্রয় ও রিটার্ন এডজাস্ট হয়ে নেট ভ্যালু থাকায় সরাসরি `SUM(line_amount)` নেওয়ার মাধ্যমে সঠিক নেট সেলস পাওয়া যায়।

---

## ৩. ইউনিক পার্টি ভিজিট বা কাস্টমার কভারেজ (Unique Billed Parties)

### 🔹 ফর্মুলা ও লজিক:
* **SQL ফর্মুলা:** `COUNT(DISTINCT customer_id)`

### 💡 কেন করেছি:
একজন কেমিস্ট, ডাক্তার বা ফার্মেসি (পার্টি) মাসে একাধিকবার ওষুধ কিনতে পারেন বা একাধিক ইনভয়েস করতে পারেন। আমরা যদি শুধু ইনভয়েস বা রো (Row) গণনা করি, তবে পার্টির সংখ্যা অনেক বেশি ও ভুল দেখাবে। তাই `DISTINCT customer_id` ব্যবহার করা হয়েছে, যাতে **একজন পার্টি মাসে ১০ বার পণ্য নিলেও তাকে ১ জন ইউনিক পার্টি হিসেবেই গণনা করা হয়**।

---

## ৪. ইনভয়েস বা মেমো সংখ্যা (Total Invoice Velocity)

### 🔹 ফর্মুলা ও লজিক:
* **SQL ফর্মুলা:** `COUNT(DISTINCT invoice_no)`

### 💡 কেন করেছি:
একটি ইনভয়েস বা মেমোতে ৫ থেকে ১০টি ভিন্ন ভিন্ন ওষুধের লাইন থাকতে পারে (ডেটাবেসে যা ৫-১০টি আলাদা রো হিসেবে থাকে)। তাই মোট কতটি মেমো কাটা হয়েছে তা বের করার জন্য `DISTINCT invoice_no` ধরে গণনা করা হয়েছে।

---

## ৫. Top 50 Products Calculation (শীর্ষ ৫০ প্রোডাক্ট নির্বাচন)

### 🔹 ফর্মুলা ও লজিক:
```sql
SELECT 
    product_code,
    MAX(product_name) AS product_name,
    SUM(line_amount) AS total_sales,
    SUM(quantity) AS total_quantity,
    COUNT(DISTINCT invoice_no) AS total_invoices,
    COUNT(DISTINCT customer_id) AS total_parties
FROM sales
GROUP BY product_code
ORDER BY SUM(line_amount) DESC
LIMIT 50;
```

### 💡 কেন ও কীভাবে করেছি:
* সব প্রোডাক্টকে তাদের কোড (`product_code`) অনুযায়ী একীভূত করে যাদের মোট সেলস ভ্যালু সবথেকে বেশি, তাদের শীর্ষ ৫০টিকে নির্বাচন করা হয়েছে।
* **মাসওয়ারি পার্টি ও ইনভয়েস (Month-wise Breakdown):** এই ৫০টি প্রোডাক্টের প্রতিটির জন্য জানুয়ারি থেকে জুন (`2026-01` থেকে `2026-06`) পর্যন্ত প্রতি মাসে কত টাকার সেলস, কতটি ইনভয়েস এবং কতজন ইউনিক পার্টিতে সেল হয়েছে তা আলাদা কুয়েরি (`WHERE product_code = ? GROUP BY month`) করে বের করা হয়েছে, যা ড্যাশবোর্ডের **"🔍 Monthly Breakdown"** বাটনে ক্লিক করলে গ্রাফ আকারে দেখা যায়।

---

## ৬. Top 50 MPO Calculation (শীর্ষ ৫০ এম.পি.ও পারফরম্যান্স)

### 🔹 ফর্মুলা ও লজিক:
```sql
SELECT 
    mpo_code,
    MAX(zone) AS zone,
    MAX(depot) AS depot,
    SUM(line_amount) AS total_sales,
    COUNT(DISTINCT invoice_no) AS total_invoices,
    COUNT(DISTINCT customer_id) AS total_parties
FROM sales
WHERE mpo_code IS NOT NULL AND mpo_code != ''
GROUP BY mpo_code
ORDER BY SUM(line_amount) DESC
LIMIT 50;
```

### 💡 কেন করেছি:
* কোন এম.পি.ও সবথেকে বেশি রেভিনিউ এনেছেন তা বের করার জন্য এম.পি.ও কোড (`mpo_code`) দিয়ে গ্রুপ করা হয়েছে।
* **আপনার বিশেষ নির্দেশ অনুযায়ী মাসওয়ারি হিসেব:** আপনি বলেছিলেন—*"top 50 der kar koto month wise party holo......invoice holo"*। তাই আমরা প্রতিটি এম.পি.ও-র জন্য মাসওয়ারি (`month` কলাম ধরে) ইউনিক পার্টি এবং ইনভয়েস সংখ্যা আলাদাভাবে হিসাব করেছি।

---

## ৭. Top 20 FM (Field Manager / Area Manager) হিসেব

### 🔹 ফর্মুলা ও লজিক:
```sql
SELECT 
    fm_am AS fm_name,
    SUM(line_amount) AS total_sales,
    COUNT(DISTINCT mpo_code) AS active_mpos,
    COUNT(DISTINCT invoice_no) AS total_invoices,
    COUNT(DISTINCT customer_id) AS total_parties
FROM sales
WHERE fm_am IS NOT NULL AND fm_am != ''
GROUP BY fm_am
ORDER BY SUM(line_amount) DESC
LIMIT 20;
```

### 💡 কেন করেছি:
একজন ফিল্ড ম্যানেজারের অধীনে কতজন এম.পি.ও কাজ করছেন (`COUNT(DISTINCT mpo_code)`), এবং তাদের সম্মিলিত সেলস ও পার্টি কভারেজ কত তা বের করে টপ ২০ জন ম্যানেজারকে র‍্যাংক করা হয়েছে।

---

## ৮. Top 5 Sector Head / Zone (জোনভিত্তিক পারফরম্যান্স)

### 🔹 ফর্মুলা ও লজিক:
```sql
SELECT 
    zone AS sector_name,
    SUM(line_amount) AS total_sales,
    COUNT(DISTINCT mpo_code) AS active_mpos,
    COUNT(DISTINCT invoice_no) AS total_invoices,
    COUNT(DISTINCT customer_id) AS total_parties
FROM sales
WHERE zone IS NOT NULL AND zone != ''
GROUP BY zone
ORDER BY SUM(line_amount) DESC
LIMIT 5;
```

### 💡 কেন করেছি:
কোম্পানির সামগ্রিক সেলস কোন অঞ্চলে (Zone/Sector) সবথেকে ভালো হচ্ছে এবং কোথায় কতজন এম.পি.ও ও পার্টি রয়েছে তা পরিমাপ করার জন্য জোনভিত্তিক এই এগ্রিগেশন করা হয়েছে।

---

## ৯. মার্কেট শেয়ার বা অবদান শতাংশ (Contribution Percentage Formula)

### 🔹 ফর্মুলা:
$$\text{Contribution \%} = \left( \frac{\text{নির্দিষ্ট প্রোডাক্ট বা MPO-র সেলস}}{\text{পুরো কোম্পানির মোট সেলস}} \right) \times 100$$

### 💡 কেন করেছি:
একটি প্রোডাক্ট বা একজন MPO পুরো কোম্পানির মোট রেভিনিউতে শতকরা কত ভাগ অবদান রাখছেন, তা এক পলকে বোঝার জন্য এই হার হিসাব করা হয়েছে।

---

## ১০. গড় ইনভয়েস মূল্য (Average Order Value — AOV)

### 🔹 ফর্মুলা:
$$\text{AOV} = \frac{\text{মোট সেলস (Total Sales)}}{\text{মোট ইনভয়েস সংখ্যা (Total Invoices)}}$$

### 💡 কেন করেছি:
প্রতিবার মেমো করার সময় গড়পড়তা কত টাকার অর্ডার কাটা হচ্ছে, তা ফিল্ড ফোর্সের দক্ষতা ও অর্ডারের সাইজ পরিমাপের একটি অত্যন্ত গুরুত্বপূর্ণ প্রফেশনাল সূচক।

---

## ১১. ৬ স্ট্র্যাটেজিক প্রোডাক্ট গ্রুপিং এবং MPO র‍্যাংকিং (6 Strategic Products & SUB_GROUP_STANDARD Merging)

### 🔹 প্রোডাক্ট গ্রুপিং ও মার্জিং নিয়ম (Excel & Strategic Base):
আপনার নির্দেশনা অনুযায়ী ডেটাবেসের `product_code` গুলোকে এক্সেল ফাইলের (`PRODUCT_CODE_AND_SUBGROUP_OF_PRODUCTS.xlsx`) **`SUB_GROUP_STANDARD`** কলাম অনুযায়ী একীভূত (Merge/Group) করা হয়েছে। এর ফলে একই গ্রুপের বিভিন্ন কোড (যেমন `ALK1`, `ALM1`, `ZA04`, `ZA05`) আলাদা না থেকে একটি সিঙ্গেল স্ট্যান্ডার্ড গ্রুপে (যেমন `ALAGRA 120 TAB`) রূপান্তরিত হয়েছে।

যে ৬টি বিশেষ স্ট্র্যাটেজিক প্রোডাক্টের জন্য আলাদা অপশন তৈরি করা হয়েছে, সেগুলোর কোড ম্যাপিং নিচে দেওয়া হলো:
1. **ALAGRA 120 TAB:** `ALK1, ALM1, ZA04, ZA05`
2. **ALAGRA 180 TAB:** `ALN1, ALP1`
3. **AMDIN PLUS TAB:** `AMK3, AMM3, ZA11`
4. **DERMA CAP:** `DEJ1, DEK1, DEM1, DEN1, ZD01`
5. **MOKAST 10 TAB:** `MON1, MOO1, MOP1`
6. **TOLEC TAB:** `TOL2`

### 🔹 Top 50 MPO by UNIT (কোয়ান্টিটি বা ইউনিটের ভিত্তিতে এম.পি.ও নির্বাচন):
* **SQL ফর্মুলা ও লজিক:**
```sql
SELECT 
    mpo_code,
    MAX(market) AS market,
    MAX(zone) AS zone,
    SUM(quantity) AS units,
    COUNT(DISTINCT customer_id) AS parties,
    COUNT(DISTINCT invoice_no) AS invoices,
    SUM(line_amount) AS sales
FROM sales
WHERE product_code IN ('MON1', 'MOO1', 'MOP1')
GROUP BY mpo_code
ORDER BY SUM(quantity) DESC
LIMIT 50;
```
* **কেন ও কীভাবে করা হয়েছে:** এই ৬টি প্রোডাক্টের বাটনে ক্লিক করলে যে পপআপ বা টেবিল আসে, সেখানে এম.পি.ও-দের টাকার অঙ্কে (Sales Value) নয়, বরং **সর্বোচ্চ ইউনিট বা কোয়ান্টিটি বিক্রির (`ORDER BY SUM(quantity) DESC`) ভিত্তিতে টপ ৫০ এম.পি.ও** নির্বাচন করা হয়েছে। 
* **মার্কেট নেম ও মাসওয়ারি ফিল্টার:** প্রতিটি এম.পি.ও-র নামের সাথে তাদের মার্কেট নেম (`MAX(market)`) এবং জানুয়ারি থেকে জুন পর্যন্ত মাসভিত্তিক ফিল্টার বাটন যুক্ত করা হয়েছে, যাতে ইউজার যেকোনো মাসের (যেমন শুধু মার্চ বা এপ্রিলের) টপ এম.পি.ও-দের ইউনিট, পার্টি ও ইনভয়েস এক ক্লিকে দেখতে পারেন।

---

## ১২. MPO → মার্কেট নাম রিজোলিউশন (Field-Force ডেটার ভিত্তিতে)

### 🔹 সমস্যা ও সমাধান:
`sales` টেবিলের `market` কলামটি মূল এক্সট্র্যাকশনের সময় `archive/recent/mpo_code.xlsx` এর সাথে LEFT JOIN করে তৈরি করা হয়েছিল (যাতে ৪৪৭টি কোড আছে)। ফলে যেসব MPO কোড ওই ফাইলে নেই, তাদের `market` ফিল্ড `NULL` থেকে যায় (৭৩০টি কোডের মধ্যে ~৪০২টি)। আগের ভার্সনে এই NULL মার্কেটের জায়গায় `zone` দেখানো হতো — যার ফলে **`DK.A` / `DK.B`** (যা আসলে **Zone কোড** — Dhaka-A / Dhaka-B, কোনো মার্কেটের নাম নয়) মার্কেটের জায়গায় চলে আসত। 

এখন `data_engine.py` এর `load_mpo_market_lookup()` ও `load_vacant_mpos()` ফিল্ড-ফোর্স ডেটার মানব-স্তরের বোঝাপড়ার ভিত্তিতে কাজ করে:

### 🔹 ১. সর্বক্ষেত্রে শুধুমাত্র "Dream Apps MPO Code" ব্যবহার (Strict Identifier):
* ইউজারের সুস্পষ্ট নির্দেশ অনুযায়ী সকল শিটে শুধুমাত্র **Dream Apps MPO Code** (যা মূলত **M কলামে / 13th column / index 12**-এ থাকে) প্রধান আইডেন্টিফায়ার হিসেবে ব্যবহার করা হচ্ছে।
* অন্যান্য alias কোড (যেমন `NEW CODE`, `OLD CODE`, `DEPOTMPO CODE`, `APP CODE (FINAL)`) বাদ দেওয়া হয়েছে, যাতে কোনো ভুল বা অস্পষ্ট ম্যাপিং না ঘটে।

### 🔹 ২. ভ্যাক্যান্ট (Vacant) পজিশন নির্ধারণে "VACANT (JUN'26)?" কলাম ব্যবহার:
* কোনো মার্কেট বা MPO ভ্যাক্যান্ট কিনা, তা নির্ধারণ করতে কখনোই অস্পষ্ট টেক্সট লেবেল (যেমন মার্কেট বা জোন ফিল্ডে `DK.A` বা `Vacant` লেখা) ব্যবহার করা হয় না।
* এর পরিবর্তে মাস্টার শিটগুলোর **I কলাম / `VACANT (JUN'26)?` / `VACANT (JAN'26)?`** (index 8 / column 9) সরাসরি চেক করা হয়। যদি এই কলামে `Y`, `YES`, `TRUE` বা `1` থাকে, তবেই সেই MPO কোডটিকে `is_vacant: True` হিসেবে চিহ্নিত করা হয়।
* ভ্যাক্যান্ট হলেও MPO-র আসল মার্কেট নাম (যেমন `HIZLA`, `TANORE`, `SEED STORE`) বজায় থাকে এবং ড্যাশবোর্ডে নামের পাশে একটি স্পষ্ট `[VACANT]` ব্যাজ দেখানো হয়।

### 🔹 ৩. সোর্স প্রায়োরিটি (priority order, first match wins):
1. **লাইভ FieldEdit Google Sheet** (সম্পূর্ণ source of truth) — col M (`DREAM APPS MPO CODE`) → col D (`MARKET`), এবং col I (`VACANT`) চেক।
2. **`FieldEdit/Archive/FIELD.xlsx`** — সেই Google Sheet-এরই flat export (col 13 → col 4, এবং col 9 চেক)।
3. **`02E_FINAL_MPO_Target_vs_Achievement_Values_*.xlsx`** (col 5 = code → col 4 = market)।
4. **`archive/03_Zone_Wise_Sales_Grouped_Report_*.xlsx`** — col 9 `DREAM APPS MPO CODE` → col 3 `MARKET`।
5. **`archive/recent/mpo_code.xlsx`** (col 5 = MPO CODE → col 3 = MARKET)।

### 🔹 ৪. ফলব্যাক নিয়ম (যদি কোনো সোর্সেও না পাওয়া যায়):
কিছু সক্রিয় MPO (যেমন `D203`, `D204`, `BG##`, `BB##`) এমন যাদের কোনো local ফাইলেই মার্কেট নাম নেই। এদের জন্য:
* ❌ আর কখনো `zone` (যেমন `DK.A`) মার্কেট হিসেবে দেখানো হয় না।
* ❌ "Vacant / Unassigned" লেখা হয় না (কারণ ভ্যাক্যান্ট নির্ধারণ শুধুমাত্র I কলাম দিয়ে হয়)।
* ✅ ঐ MPO-র আসল **Depot নাম** (যেমন `DHAKA-1`, `RAJSHAHI`, `CUMILLA`) দেখানো হয় — যা ১০০% সত্য ডেটা এবং কখনো বিভ্রান্তিকর zone কোড নয়।

### 🔹 ফলাফল:
* ড্যাশবোর্ডে এখন আর কোনো `market` ফিল্ডে `DK.A` / `DK.B` বা ভুল `Vacant` দেখা যায় না।
* Overall Top 50 MPO এবং Strategic 6 Products উভয় টেবিলেই এখন MPO কোডের সাথে তাদের আসল মার্কেট নাম (`📍 MARKET`) এবং প্রযোজ্য ক্ষেত্রে `[VACANT]` ব্যাজ প্রদর্শিত হচ্ছে।


---
*এই ডকুমেন্টটি আপনার প্রজেক্টের `TOP_FIELD_FORCE` ফোল্ডারে `CALCULATION_METHODOLOGY_BN.md` নামে সেভ করা হয়েছে।*
