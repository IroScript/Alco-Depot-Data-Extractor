# 🚨 MASTER AI CODING RULES & DOMAIN CONVENTIONS (`AGENTS.md`) 🚨
**Project Name:** IroScript / Barishal April Data / Top Field Force Sales Analytics Dashboard  
**Language/Stack:** Python 3.12, SQLite (`sales.db`), openpyxl / pandas, HTML5, Vanilla CSS, Vanilla JavaScript (`js/script.js`).

---

### 1. 👑 ZERO LOCAL DEPENDENCY & GOOGLE SHEETS MASTER RULES (CRITICAL BUSINESS LOGIC)
Never make assumptions about MPO, FM/AM, Zone codes, or Product mappings! Strict adherence to the following rules is mandatory across all scripts and SQL queries:

1. **NO LOCAL OR OFFLINE DEPENDENCY (Live Google Sheets is the Sole Standard):**
   - The architecture must **never rely on local or offline files as the primary standard**. All critical master data (Field Forces, MPO Codes, FM Codes, Product Groups, and Strategic 6 calculations) must be structured around the Live Master Google Spreadsheet ecosystem.
   - **Master Spreadsheet ID:** `1Q4utivZ5OpgDznqlqElYU-HWNnZYI71YYpcZKcSM3xY`

2. **Field Forces Identification (MPO & FM Codes):**
   - **For MPO Codes:** Strictly use **Column M (`DREAM APPS MPO CODE`)** from the Master Field Forces Google Sheet tab (`gid=1918615875`):
     `https://docs.google.com/spreadsheets/d/1Q4utivZ5OpgDznqlqElYU-HWNnZYI71YYpcZKcSM3xY/edit?gid=1918615875#gid=1918615875`
   - **For Field Manager (FM/AM) Codes & Reference:** Use the reference sheet tab (`gid=501612498`):
     `https://docs.google.com/spreadsheets/d/1ywTyruBLxNXz6pjsGgufNstb0hOsrM9P-ER65iVvqN8/edit?gid=501612498#gid=501612498`
     (Contains `"MPO CODE \n(DREAM APPS )"` and FM mappings).
   - Never use any unauthorized local file as the standard for MPO identification!

3. **Strict Field Force Filtering (No Institutional / Bulk Data in Reports):**
   - The database (`sales.db`) and raw CSV files contain institutional, bulk, and depot-level accounts (e.g., `D203`, `D204`, `'DK.A // DHAKA-1'`, etc.).
   - **RULE:** All reports, dashboards, KPIs, leaderboard tables, and charts (especially in `TOP_FIELD_FORCE/data_engine.py`) **MUST strictly filter out** non-field codes!
   - Always validate against the verified Google Sheet MPO/FM list. Do NOT include `D203`, `D204`, or institutional accounts in Top MPO, Top FM, or Top Sector calculations.

4. **Vacant MPO & FM Handling:**
   - Vacant MPO status is identified strictly by checking the status column (e.g., for the word `"VACANT"`).
   - **RULE:** If an FM/AM entry contains the word `"VACANT"` (e.g., `'VACANT, BARI-2'`, `'VACANT, BABUGANJ'`), **it is NOT a human Field Manager** and MUST be excluded/filtered out from Top FM/AM leaderboards!
   - Only actual human Field Managers (e.g., `'MOSTAFIZUR RAHMAN'`, `'NURUL ISLAM'`, etc.) should appear in FM rankings.

---

### 2. 📦 PRODUCT MAPPINGS & STRATEGIC 6 (GOOGLE SHEETS STANDARD)
1. **Product Codes Sheet Tab (`gid=1219133636`):**
   - All product classifications, subgroups, and Strategic 6 mappings must be fetched from the Product Code tab in the Master Google Spreadsheet:
     `https://docs.google.com/spreadsheets/d/1Q4utivZ5OpgDznqlqElYU-HWNnZYI71YYpcZKcSM3xY/edit?gid=1219133636#gid=1219133636`

2. **Strategic 6 Products (`TOP_50_CALCULATION` Column):**
   - For Strategic 6 Products calculations, strictly use the **`TOP_50_CALCULATION` column** from the Product Code sheet (`gid=1219133636`).
   - Map product codes where `TOP_50_CALCULATION` is specified. Do not hardcode static product lists.

3. **Top 50 Products Grouping (`SUB_GROUP_STANDARD` Column):**
   - For general Top 50 Products rankings, always group and merge items by the **`SUB_GROUP_STANDARD`** column from the Product Code sheet (`gid=1219133636`).

*Note on Markets vs. Zones:*
- Zone codes like `'DK.A'`, `'DK.B'` mean Dhaka-A/Dhaka-B institutional zones. They are NOT market names!
- Always map MPO codes to their proper Market Name or fallback to Depot Name. Never display zone codes as market names.

---

### 3. ⚙️ WORKFLOW (`TOP_FIELD_FORCE`)
1. **Data Engine (`data_engine.py`):**
   - Connects to `../sales.db` (or `sales.db` in workspace root).
   - Generates all analytical aggregations (KPIs, Monthly Trends, Top 50 Products grouped by `SUB_GROUP_STANDARD`, Top 50 MPOs, Top 20 FMs, Top 5 Sectors, and Strategic 6 Products anchored by `TOP_50_CALCULATION`).
   - Saves final JSON output to `data/api_data.json`.
   - Note on API fallback: If Google Sheets OAuth/JWT API authentication fails temporarily (e.g., `invalid_grant`), the engine may use a local cached copy as a resilient fallback, but Google Sheets remains the architectural source of truth.
   - **Whenever database queries or calculation rules change, always run `py -3.12 data_engine.py` to regenerate `api_data.json`.**

2. **Frontend UI (`index.html`, `js/script.js`, `css/style.css`):**
   - A modern, responsive, high-performance vanilla JS SPA dashboard.
   - Reads data asynchronously from `data/api_data.json`.
   - Served locally via Python HTTP server (`py -3.12 server.py` on port 8000).

---

### 4. 💻 CODING STANDARDS & BEST PRACTICES
1. **Python / SQLite:**
   - Always use Python 3.12 (`py -3.12`).
   - Use uppercase clean trimming for Excel/Sheet cell values: `str(val).strip().upper()`.
   - Ensure all data reading blocks handle API failures gracefully without crashing.
   - When writing SQL `WHERE ... IN (...)` queries with large lists, generate parameter placeholders dynamically (`",".join(["?"] * len(list))`) and pass tuples.

2. **Windows OS Compatibility:**
   - The OS is Windows. Use `os.path.join` for paths. Avoid hardcoded UNIX slashes `/` for local file paths in Python scripts.
   - Do NOT propose `cd` commands in `run_command`. Always pass exact `Cwd`.
   - Do NOT use Linux-only terminal commands like `cat`, `ls`, `grep` inside terminal commands; use proper Python scripts or specific tools (`grep_search`, `view_file`, etc.).

3. **UI / Aesthetics (Web Apps):**
   - Maintain rich, premium design aesthetics (glassmorphism, vibrant palettes, smooth transitions, readable typography). Never downgrade UI visual quality.

4. **Strict Git / Version Control Policy:**
   - **NEVER execute `git push` or publish commits autonomously.** Do not push code unless the user explicitly commands it (e.g., `"git push"` or `"gitpush"`).

---
**⚡ REMINDER FOR AI AGENTS:** Read this document before suggesting any architectural changes, SQL query modifications, or data parsing adjustments!
