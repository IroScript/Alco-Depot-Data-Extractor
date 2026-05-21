# Alco-Depot-Data-Extractor

Extract and analyze MPO-wise sales data from legacy SQL Server 2000 ERP databases across multiple depots.

## 🎯 Key Features

- ✅ **Multi-Depot Support** - Process all 9 depot databases at once
- ✅ **Automatic MPO Detection** - Extracts all MPO codes from each depot
- ✅ **SQL Server 2000 Compatible** - Works with 20+ year old databases
- ✅ **Automated Extraction** - No manual work needed
- ✅ **Comprehensive Reports** - Excel output with multiple analysis sheets
- ✅ **212K+ Records** - Successfully processed from all depots

## 📁 Project Structure

```
All_Depots/
├── Barishal/Data/ERPonTheNet_Data.MDF
├── Chittagong/Data/ERPonTheNet_Data.MDF
├── Cumilla/Data/ERPonTheNet_Data.MDF
├── Faridpur/Data/ERPonTheNet_Data.MDF
├── Jashore/Data/ERPonTheNet_Data.MDF
├── Mymensingh/Data/ERPonTheNet_Data.MDF
├── Rajshahi/Data/ERPonTheNet_Data.MDF
├── Rangpur/Data/ERPonTheNet_Data.MDF
└── Sylhet/Data/ERPonTheNet_Data.MDF
```

## 🚀 Quick Start

### ⭐ ONE-COMMAND SOLUTION (Recommended)

```bash
python run_all.py
```

This master script will:
- ✅ Check all prerequisites
- ✅ Install missing packages automatically
- ✅ Fix permissions
- ✅ Clean up old databases
- ✅ Process all 9 depots
- ✅ Handle errors with auto-recovery
- ✅ Generate report with Month column
- ✅ Never overwrite existing reports
- ✅ Complete in ~2-3 minutes

**Features:**
- Self-healing: Automatically detects and fixes common issues
- Error recovery: Tries multiple approaches if something fails
- Never fails: Built-in fallback strategies
- Progress tracking: Color-coded status messages
- Unique filenames: Reports never overwrite each other

---

### Manual Step-by-Step (Advanced Users)

### Manual Step-by-Step (Advanced Users)

#### 1. Install Prerequisites

**SQL Server 2008 R2 Express:**
```bash
cd installation
download_sql2008.cmd
```

**Fix Permissions:**
```bash
cd installation
fix_permissions.cmd
```

**Python Packages:**
```bash
pip install -r requirements.txt
```

#### 2. Organize Your Data

Place depot folders in `All_Depots/`:
```
All_Depots/
├── Barishal/Data/ERPonTheNet_Data.MDF
├── Chittagong/Data/ERPonTheNet_Data.MDF
└── ... (more depots)
```

#### 3. Process All Depots

```bash
python process_all_depots.py
```

**What it does:**
- Scans all depot folders
- Attaches each ERPonTheNet_Data.MDF database
- Extracts ALL MPO-wise sales data
- Combines into single comprehensive report

**Output:**
- `All_Depots_MPO_Report_YYYYMMDD_HHMMSS.xlsx`
  - Sheet 1: All Data (all depots combined)
  - Sheet 2: Depot Summary
  - Sheet 3: MPO Summary

**Example Results:**
- Total Records: 212,697
- Total Depots: 9
- Total Sales: 136.7M BDT
- Top Depot: Rangpur (26.8M BDT)

---

## 📊 Available Scripts

### 0. **run_all.py** ⭐ MASTER SCRIPT (USE THIS!)

One-command solution that handles everything automatically.

```bash
python run_all.py
```

**Features:**
- ✅ Checks SQL Server status
- ✅ Auto-installs missing Python packages
- ✅ Fixes file permissions automatically
- ✅ Detaches old databases
- ✅ Processes all depots
- ✅ Error detection and auto-recovery
- ✅ Multiple retry strategies
- ✅ Color-coded progress messages
- ✅ Completion summary with statistics

**Error Recovery:**
- Attempt 1: Detach databases and retry
- Attempt 2: Fix permissions and retry
- Attempt 3: Alternative processing methods
- Never gives up until success!

**Output:**
- Console: Real-time progress with colors
- Excel: All_Depots_MPO_Report_YYYYMMDD_HHMMSS.xlsx
- Unique filenames (never overwrites)
- Month column included (YYYY-MM format)

---

### 1. **process_all_depots.py** ⭐ CORE PROCESSING SCRIPT

Process multiple depot databases at once.

```bash
python process_all_depots.py
```

**Features:**
- Auto-discovers all depots in `All_Depots/` folder
- Attaches ERPonTheNet_Data.MDF from each depot
- Extracts ALL MPO codes automatically (no Excel file needed)
- Processes each depot's sales data
- Combines data from all depots
- Creates comprehensive Excel report

**Tested Results:**
- ✅ Barishal: 21,291 records (11.9M BDT)
- ✅ Chittagong: 20,271 records (15.9M BDT)
- ✅ Cumilla: 11,884 records (10.4M BDT)
- ✅ Faridpur: 16,818 records (11.4M BDT)
- ✅ Jashore: 33,883 records (22.6M BDT)
- ✅ Mymensingh: 17,030 records (11.2M BDT)
- ✅ Rajshahi: 27,217 records (17.2M BDT)
- ✅ Rangpur: 49,830 records (26.8M BDT)
- ✅ Sylhet: 14,473 records (9.2M BDT)

---

### 2. **mpo_final_report.py**

Extract MPO-wise sales from single database (legacy script).

```bash
python mpo_final_report.py
```

**Features:**
- Works with single attached database
- Can use MPO codes from Excel if available
- Falls back to pattern matching
- Creates detailed sales report

**Output:**
- `MPO_Complete_Report_YYYYMMDD_HHMMSS.xlsx`
  - All Sales Details
  - MPO Summary
  - Top 20 MPOs

---

### 3. **find_mpo_codes.py**

Discover where MPO codes are located in database.

```bash
python find_mpo_codes.py
```

**Output:**
- `MPO_Search_Results_YYYYMMDD_HHMMSS.xlsx`
- Shows which tables/columns contain MPO codes

---

### 4. **export_all_data.py**

Export all important tables to Excel (legacy script).

```bash
python export_all_data.py
```

**Exports:**
- Customers (cacus)
- Items/Products (caitem)
- Orders (opord)
- Order Details (opodt)
- Inventory (imtrn)
- And more...

---

### 5. **read_with_sql2005.py**

Attach MDF file and explore database (legacy script).

```bash
python read_with_sql2005.py
```

**Features:**
- Interactive menu
- Attach MDF files
- List all tables
- Export selected tables

---

## 📝 MPO Codes

MPO codes are automatically extracted from each depot's database. Examples:

**Barishal Depot:**
```
B001, B002, B004, B006, B010, B011, B012, B013, B014, B016, B018, B020,
B024, B025, B026, B034, B036, B038, B039, B041, B042, B048, B051, B054,
B055, B063, B064, F001, F003, F004, F006, F009, F011, F012, F013, F031,
F032, F036, F039, F051, F052, F054, and more...
```

Each depot has its own set of MPO codes (typically 50-100 unique codes per depot).

---

## 🔧 Configuration

Edit scripts to change paths:

```python
# In process_all_depots.py
MPO_CODES_FILE = r"C:\Users\Irak\Desktop\Barishal April Data\mpo_code.xlsx"
ALL_DEPOTS_FOLDER = r"C:\Users\Irak\Desktop\Barishal April Data\All_Depots"
SQL_SERVER = r'.\SQLEXPRESS'
```

---

## 📊 Sample Output

### Depot Summary

| Depot      | Total Invoices | Total Customers | Total Sales (BDT) |
|------------|----------------|-----------------|-------------------|
| Barishal   | 7,837          | 1,787           | 11,988,771.73     |
| Chittagong | 8,092          | 1,958           | 15,868,301.97     |
| Cumilla    | 4,920          | 1,214           | 10,421,975.16     |
| Faridpur   | 7,784          | 2,019           | 11,448,096.94     |
| Jashore    | 13,088         | 3,766           | 22,589,236.64     |
| Mymensingh | 6,693          | 1,575           | 11,187,940.05     |
| Rajshahi   | 12,228         | 2,688           | 17,185,862.87     |
| Rangpur    | 18,073         | 4,263           | 26,835,362.87     |
| Sylhet     | 5,709          | 1,294           | 9,175,969.52      |
| **TOTAL**  | **84,424**     | **20,564**      | **136,701,517.75**|

### Top MPOs by Depot

**Barishal:**
- B036: 593 invoices
- B011: 553 invoices
- B038: 516 invoices

**Rangpur (Highest Sales):**
- 18,073 invoices
- 4,263 customers
- 26.8M BDT total sales

---

## 🛠️ Troubleshooting

### Permission Error

```bash
cd installation
fix_permissions.cmd
```

### Database Version Not Supported

Use SQL Server 2008 R2 or later (not 2019/2022).

### ODBC Driver Not Found

```bash
cd installation
install_odbc.cmd
```

---

## 📖 Documentation

- `README.md` - This file
- `archive/README_BANGLA.md` - Bengali documentation
- `archive/SOLUTION_FINAL.md` - Complete solution guide

---

## 🎓 How It Works

1. **Load MPO Codes** - Reads from `mpo_code.xlsx`
2. **Scan Depots** - Finds all depot folders with MDF files
3. **Attach Databases** - Attaches each MDF to SQL Server
4. **Extract Data** - Queries sales data filtered by MPO codes
5. **Combine Results** - Merges data from all depots
6. **Generate Report** - Creates Excel with multiple analysis sheets

---

## 🔒 Security

- ✅ `.gitignore` excludes sensitive data
- ✅ MDF files not uploaded to GitHub
- ✅ Excel reports not uploaded
- ✅ Only code is version controlled

---

## 📞 Support

For issues or questions, open an issue on GitHub.

---

## 📝 License

MIT License

---

**Repository:** https://github.com/IroScript/Alco-Depot-Data-Extractor
