# Alco-Depot-Data-Extractor

Extract and analyze data from legacy SQL Server 2000 ERP databases (ERPonTheNet).

## 🎯 Features

- **Extract data from SQL Server 2000 MDF files** without modern SQL Server
- **MPO/Sales Person wise sales analysis** with complete details
- **Customer, Product, and Invoice reports** with proper relationships
- **Automated data extraction** from old ERP systems
- **Excel export** with multiple analysis sheets

## 📊 What This Tool Does

This tool helps extract and analyze sales data from old ERP systems, specifically:

- **MPO-wise Sales Reports**: Complete sales breakdown by Medical/Pharmaceutical Representatives
- **Customer Ledgers**: Customer-wise purchase history
- **Product Analysis**: Product-wise sales and inventory
- **Invoice Details**: Complete invoice information with all related data

## 🚀 Quick Start

### Prerequisites

1. **SQL Server 2008 R2 Express** (or later)
   - Download: https://www.microsoft.com/en-us/download/details.aspx?id=30438
   - Lightweight and free

2. **Python 3.12+**
   - Download: https://www.python.org/downloads/

3. **Required Python packages**:
   ```bash
   pip install pyodbc pandas openpyxl
   ```

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/IroScript/Alco-Depot-Data-Extractor.git
   cd Alco-Depot-Data-Extractor
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install SQL Server 2008 R2 Express:
   ```bash
   download_sql2008.cmd
   ```

### Usage

#### 1. Attach Your MDF Database

```bash
python read_with_sql2005.py
```

This will:
- Connect to SQL Server
- Attach your MDF file
- List all available tables

#### 2. Extract MPO-wise Sales Data

```bash
python mpo_final_report.py
```

Generates:
- **MPO_Complete_Report.xlsx** with:
  - All sales details (19,000+ records)
  - MPO summary (total sales per MPO)
  - Top 20 MPOs by sales

#### 3. Find MPO Codes in Database

```bash
python find_mpo_codes.py
```

Searches entire database for MPO codes (B001, B002, B045, etc.) and shows where they're located.

#### 4. Export All Data

```bash
python export_all_data.py
```

Exports all important tables to Excel:
- Customers (cacus)
- Items/Products (caitem)
- Orders (opord)
- Order Details (opodt)
- Inventory Transactions (imtrn)

## 📁 Project Structure

```
Alco-Depot-Data-Extractor/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── .gitignore                        # Git ignore rules
│
├── Installation/
│   ├── download_sql2008.cmd          # SQL Server installer
│   ├── install_odbc.cmd              # ODBC Driver installer
│   └── fix_permissions.cmd           # Fix file permissions
│
├── Scripts/
│   ├── read_with_sql2005.py          # Attach MDF and list tables
│   ├── mpo_final_report.py           # MPO-wise sales report
│   ├── find_mpo_codes.py             # Find MPO codes in database
│   ├── export_all_data.py            # Export all tables
│   ├── create_sales_report.py        # Comprehensive sales analysis
│   └── automate_mpo_extraction.py    # GUI automation (for old software)
│
└── Documentation/
    ├── README_BANGLA.md              # Bengali documentation
    ├── SOLUTION_FINAL.md             # Complete solution guide
    └── install_sql2000_guide.md      # SQL Server installation guide
```

## 🔧 Troubleshooting

### Permission Error (Error 5)

If you get "Operating system error 5" when attaching database:

```bash
fix_permissions.cmd
```

This grants SQL Server access to your MDF files.

### Database Version Not Supported

Your MDF file is from SQL Server 2000. Use SQL Server 2008 R2 or later to read it.

### ODBC Driver Not Found

Install ODBC Driver 17 for SQL Server:

```bash
install_odbc.cmd
```

## 📊 Sample Output

### MPO Summary Report

| MPO Code | Total Invoices | Total Customers | Total Sales Amount |
|----------|----------------|-----------------|-------------------|
| B036     | 593            | 215             | 1,598,000         |
| B011     | 553            | 193             | 1,476,000         |
| B038     | 516            | 187             | 1,393,000         |
| B064     | 497            | 217             | 1,346,000         |
| B001     | 468            | 175             | 1,268,000         |

### Data Extracted

- **21,291 sales records** with complete details
- **54 database tables** identified
- **19,274 MPO-related transactions**
- **7,837 orders** with customer and product information

## 🌟 Key Features

### 1. MPO-wise Analysis
- Complete sales breakdown by MPO/Sales Person
- Customer assignments per MPO
- Product-wise sales per MPO
- Monthly performance tracking

### 2. Customer Ledger
- Customer-wise purchase history
- Credit limits and status
- Contact information
- Zone and territory mapping

### 3. Product Analysis
- Product-wise sales volume
- Inventory transactions
- Pricing information
- Stock movements

### 4. Invoice Details
- Complete invoice information
- Line-item details
- Customer and product relationships
- Date-wise analysis

## 🛠️ Technical Details

### Database Structure

The ERPonTheNet database contains:

- **cacus**: Customer master (43 columns)
- **caitem**: Item/Product master (57 columns)
- **opord**: Sales orders (51 columns)
- **opodt**: Order details (47 columns)
- **imtrn**: Inventory transactions (33 columns)
- **xcodes**: Code master (MPO codes, zones, etc.)

### MPO Code Location

MPO codes (B001, B002, B045, etc.) are found in:

1. **opord.xsp** - Sales Person in orders
2. **cacus.xsp** - Sales Person assigned to customers
3. **xcodes.xcode** - Master code table

## 📝 License

MIT License - feel free to use and modify

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Contact

For questions or support, please open an issue on GitHub.

## 🙏 Acknowledgments

- Built for extracting data from legacy ERP systems
- Supports SQL Server 2000 databases
- Designed for pharmaceutical/medical distribution companies

---

**Note**: This tool is designed for data extraction and analysis from legacy systems. Always backup your original database files before processing.
