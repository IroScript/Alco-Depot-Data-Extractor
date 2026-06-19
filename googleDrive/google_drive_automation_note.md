# Google Drive & Cloud Database Extraction Automation Guide
This document details the architecture and step-by-step implementation guide to automate your entire workflow using **GitHub Actions**, **Docker (SQL Server)**, and **Google Drive/Sheets API** with **zero human touch**.

---

## 1. Automated Pipeline Architecture (Zero-Human-Touch)
Rather than manually running a heavy SQL Server on your local computer, the entire data pipeline can be executed automatically in the cloud (using GitHub Actions' free virtual machine with 80 GB storage):

```
┌────────────────────────┐
│  1. Upload MDF File    │  <-- User uploads new depot database (.mdf) to Google Drive
└───────────┬────────────┘
            │ (Trigger Webhook)
┌───────────▼────────────┐
│ 2. GitHub Actions VM   │  <-- GitHub spins up a free virtual Linux server
└───────────┬────────────┘
            │ (Automated Commands)
┌───────────▼────────────┐
│ 3. Docker SQL Server   │  <-- Launches MS SQL Server inside a Docker container
└───────────┬────────────┘
            │ (Attach & Query)
┌───────────▼────────────┐
│ 4. Python Data Extract │  <-- Python script downloads MDF, attaches it, extracts sales CSV
└───────────┬────────────┘
            │ (API Upload)
┌───────────▼────────────┐
│ 5. Google Sheet Update │  <-- Uploads results and updates Google Sheets/Drive automatically
└───────────┬────────────┘
            │ (Clean Up)
┌───────────▼────────────┐
│ 6. Auto Destroy VM     │  <-- Docker container and virtual VM are completely deleted
└────────────────────────┘
```

---

## 2. Technical Feasibility of Legacy SQL Server (2000 / 2005 / 2008) in Docker
You asked if we can run older versions of SQL Server inside Docker to parse older `.mdf` files. Here is the technical breakdown:

### A. Core Limitations
* **Official Images:** Microsoft **does not** provide Docker images for SQL Server 2008, 2005, or 2000.
* **Linux Docker:** Modern SQL Server Docker containers run on Linux, but SQL Server 2008 and older only ran on Windows.

### B. The Solution: Modern SQL Server with Compatibility Levels
SQL Server supports attaching database files from older versions through **Compatibility Levels**:
* **SQL Server 2019** supports database compatibility levels back to **100** (which corresponds to **SQL Server 2008**).
* Therefore, a SQL Server 2008 database file (`.mdf`) **can** be directly attached to a SQL Server 2019 Docker container.
* *Note:* SQL Server 2022 dropped compatibility level 100 (minimum is 110/SQL Server 2012), so we **must use SQL Server 2019** for the Docker container.

---

## 3. GitHub Actions Workflow Configuration
To implement this automation, you would save a YAML configuration file under `.github/workflows/data_pipeline.yml` in your repository. Here is a template config:

```yaml
name: Automated Depot Data Extractor

on:
  # Runs automatically on a daily schedule
  schedule:
    - cron: '0 18 * * *' # Every day at 6:00 PM
  # Allows manual run from the GitHub interface
  workflow_dispatch:

jobs:
  run-pipeline:
    runs-on: ubuntu-latest
    
    steps:
      # Step 1: Check out repository code
      - name: Checkout Code
        uses: actions/checkout@v3

      # Step 2: Set up Python
      - name: Set Up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      # Step 3: Install system dependencies (for SQL Server connections)
      - name: Install SQL Server ODBC Driver
        run: |
          sudo accept-mssql-eula apt-get install -y msodbcsql17 unixodbc-dev

      # Step 4: Run SQL Server 2019 Docker Container
      - name: Start SQL Server 2019 Docker Container
        run: |
          docker run -e "ACCEPT_EULA=Y" -e "SA_PASSWORD=YourSecurePassword123!" \
            -p 1433:1433 \
            -d mcr.microsoft.com/mssql/server:2019-latest

      # Step 5: Download MDF files from Google Drive
      - name: Download MDF Files from Google Drive
        env:
          GDRIVE_API_KEY: ${{ secrets.GDRIVE_API_KEY }}
        run: |
          python download_from_drive.py

      # Step 6: Execute Data Extraction (Attaches DB inside Docker, extracts sales)
      - name: Run Python Extraction
        run: |
          pip install pyodbc pandas openpyxl gspread google-auth
          python step_1_extract_Product_Level_Net_Sales_csv.py --server 127.0.0.1 --password 'YourSecurePassword123!'

      # Step 7: Process reports (Generate targets and matching reports)
      - name: Process Reports
        run: |
          python step_2_generate_MPO_Target_vs_Achievement_report.py
          python step_3_generate_Zone_Wise_Product_Sales_Report.py
          python step_4_analyze_Zone_Wise_Product_Sales_Report.py

      # Step 8: Upload Final Reports back to Google Drive
      - name: Upload Output Reports to Google Drive
        run: |
          python googleDrive/step_6_google_drive_upload.py
```

---

## 4. Local Upload Script
We have saved a Python script **[step_6_google_drive_upload.py](file:///c:/Users/Irak/Desktop/Barishal%20April%20Data/googleDrive/step_6_google_drive_upload.py)** in your `googleDrive` directory. 
* It uses the existing service account key file `alco-pharma-cf4b49e394bb.json` to authenticate.
* It scans the directory for the latest output files generated from Step 1 through Step 4.
* It uploads them to a newly created timestamped folder on your Google Drive (e.g. `Barishal April Data Run - 18-Jun-2026 08.57 PM`).
* You can configure a parent folder ID inside **[FieldEdit/config.json](file:///c:/Users/Irak/Desktop/Barishal%20April%20Data/FieldEdit/config.json)** by adding the key: `"drive_folder_id": "your_folder_id_here"`.
