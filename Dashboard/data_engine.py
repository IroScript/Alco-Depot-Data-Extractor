import os
import sys
import io
if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import sqlite3
import json
from datetime import datetime
import openpyxl

# Define base directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
DEFAULT_DB_PATH = os.path.join(PARENT_DIR, "sales.db")
DATA_OUT_DIR = os.path.join(BASE_DIR, "data")

os.makedirs(DATA_OUT_DIR, exist_ok=True)

# Google Sheets primary loader for product mappings (gid=1219133636)
def _try_google_sheet_products():
    if hasattr(_try_google_sheet_products, "_cache"):
        return _try_google_sheet_products._cache
    try:
        # Use single-source credentials from master file (in-memory)
        import sys
        sys.path.insert(0, PARENT_DIR)
        from googleDrive.credentials_loader import get_sheet_service_account_credentials, get_spreadsheet_id

        import gspread
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = get_sheet_service_account_credentials(scopes=scopes)
        client = gspread.authorize(creds)
        sheet_id = get_spreadsheet_id('master_field_force_sheet') or '1Q4utivZ5OpgDznqlqElYU-HWNnZYI71YYpcZKcSM3xY'
        sheet = client.open_by_key(sheet_id)
        ws = sheet.get_worksheet_by_id(1219133636)
        if not ws:
            return None, None
        
        rows = ws.get_all_records()
        code_to_subgroup = {}
        dyn_s6 = {}
        last_code = ""
        for r in rows:
            code = str(r.get('Product_Code', '')).strip().upper()
            if code and code != "NAN":
                last_code = code
            elif last_code:
                code = last_code
                
            subg = str(r.get('SUB_GROUP_STANDARD', '')).strip()
            if code and subg and subg != "NAN":
                code_to_subgroup[code] = subg
                
            s6_val = str(r.get('TOP_50_CALCULATION', '')).strip()
            if code and s6_val and s6_val != "NAN":
                dyn_s6.setdefault(s6_val, []).append(code)
                
        strategic_6_map = {k: sorted(list(set(v))) for k, v in dyn_s6.items()} if dyn_s6 else None
        print(f"Live Google Sheet (gid=1219133636): loaded {len(code_to_subgroup)} product subgroups and {len(strategic_6_map or {})} strategic groups.")
        _try_google_sheet_products._cache = (code_to_subgroup, strategic_6_map)
        return code_to_subgroup, strategic_6_map
    except Exception as e:
        print(f"Note: Live Google Sheet for products unavailable ({str(e)[:80]}). Using resilient fallback.")
        _try_google_sheet_products._cache = (None, None)
        return None, None

# 6 Strategic Product Groups defined by user (dynamically loaded from Google Sheet / TOP_50_CALCULATION column)
def load_strategic_6_mapping():
    _, gs_s6 = _try_google_sheet_products()
    if gs_s6:
        return gs_s6

    # Resilient fallback if Google API offline
    excel_path = os.path.join(PARENT_DIR, "PRODUCT_CODE_AND_SUBGROUP_OF_PRODUCTS.xlsx")
    mapping = {
        'ALAGRA 120 TAB': ['ALK1', 'ALM1', 'ZA04', 'ZA05'],
        'ALAGRA 180 TAB': ['ALN1', 'ALP1'],
        'AMDIN PLUS TAB': ['AMK3', 'AMM3', 'ZA11'],
        'DERMA CAP': ['DEJ1', 'DEK1', 'DEM1', 'DEN1', 'ZD01'],
        'MOKAST 10 TAB': ['MON1', 'MOO1', 'MOP1'],
        'TOLEC TAB': ['TOL2']
    }
    if os.path.exists(excel_path):
        try:
            import pandas as pd
            df = pd.read_excel(excel_path)
            if "TOP_50_CALCULATION" in df.columns:
                df["Product_Code_ffill"] = df["Product_Code"].ffill()
                dyn_map = {}
                for _, row in df.dropna(subset=["TOP_50_CALCULATION"]).iterrows():
                    code = str(row["Product_Code_ffill"]).strip().upper()
                    grp = str(row["TOP_50_CALCULATION"]).strip()
                    if code and code != "NAN" and grp and grp != "nan":
                        dyn_map.setdefault(grp, []).append(code)
                if dyn_map:
                    mapping = {k: sorted(list(set(v))) for k, v in dyn_map.items()}
        except Exception:
            pass
    return mapping

STRATEGIC_6_MAPPING = load_strategic_6_mapping()

def load_excel_mappings():
    gs_subg, _ = _try_google_sheet_products()
    code_to_subgroup = gs_subg or {}
    
    if not code_to_subgroup:
        # Resilient fallback if Google API offline
        excel_path = os.path.join(PARENT_DIR, "PRODUCT_CODE_AND_SUBGROUP_OF_PRODUCTS.xlsx")
        if os.path.exists(excel_path):
            try:
                import pandas as pd
                df_map = pd.read_excel(excel_path)
                df_map["Product_Code_ffill"] = df_map["Product_Code"].ffill()
                for _, row in df_map.iterrows():
                    code = str(row["Product_Code_ffill"]).strip().upper()
                    subg = str(row["SUB_GROUP_STANDARD"]).strip() if pd.notna(row["SUB_GROUP_STANDARD"]) else ""
                    if code and code != "NAN" and subg and subg != "nan":
                        code_to_subgroup[code] = subg
            except Exception as e:
                print(f"Note: Could not read fallback mapping via pandas: {e}")
            
    # Always ensure strategic 6 mappings exist in subgroup dict
    for grp_name, codes in STRATEGIC_6_MAPPING.items():
        for c in codes:
            code_to_subgroup[c] = grp_name
            
    return code_to_subgroup

def _clean_cell(val):
    """Normalise a cell value to a trimmed string; '' for None/blank/'None'."""
    if val is None:
        return ''
    s = str(val).strip()
    return '' if s in ('None', 'nan', 'NaN') else s


def _clean_market_name(name):
    """Human-level market name formatting (mirrors FieldEdit's clean_market_name)."""
    if not name:
        return ''
    name = _clean_cell(name).upper()
    import re
    name = re.sub(r'\s+', ' ', name)
    if name == 'HATIBANDHA (HATIB.)':
        return 'HATIBANDHA (HATIBANDHA-1)'
    return name


def _add_from_excel(mpo_map, fpath, header_row, code_cols, market_col, skip_if_present=True):
    """Generic helper: read one workbook and union code->market entries.

    code_cols / market_col are 1-based column numbers as seen in Excel.
    Multiple code columns (aliases) all map to the same market.
    """
    try:
        import openpyxl
        if not os.path.exists(fpath):
            return
        wb = openpyxl.load_workbook(fpath, data_only=True)
        ws = wb.active
        for r in range(header_row + 1, ws.max_row + 1):
            mkt = _clean_market_name(ws.cell(row=r, column=market_col).value)
            if not mkt:
                continue
            for cc in code_cols:
                code = _clean_cell(ws.cell(row=r, column=cc).value)
                if code and (not skip_if_present or code not in mpo_map):
                    mpo_map[code] = mkt
    except Exception as e:
        print(f"Note: Could not read {os.path.basename(fpath)}: {e}")


def _try_google_sheet_market_map(mpo_map):
    """Attempt the live FieldEdit Google Sheet (complete source of truth).

    Replicates FieldEdit/field_formatter_updated_gui_active_data.py:process_excel
    auth flow + cutoff logic + clean_market_name. Silent no-op if credentials
    are unavailable or the service-account key is revoked.
    """
    try:
        import json, sys
        sys.path.insert(0, PARENT_DIR)
        from googleDrive.credentials_loader import get_sheet_service_account_credentials, get_spreadsheet_id

        import gspread
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = get_sheet_service_account_credentials(scopes=scopes)
        client = gspread.authorize(creds)
        sheet_id = get_spreadsheet_id('master_field_force_sheet') or '1Q4utivZ5OpgDznqlqElYU-HWNnZYI71YYpcZKcSM3xY'
        sheet = client.open_by_key(sheet_id)

        worksheet = None
        target_gid = '1918615875'  # from master file's google_sheets.master_field_force_sheet.gid_used
        for ws in sheet.worksheets():
            if str(ws.id) == target_gid:
                worksheet = ws
                break
        if not worksheet:
            worksheet = sheet.get_worksheet(0)

        all_values = worksheet.get_all_values()

        # cutoff at the secondary data block marker (FieldEdit logic)
        cutoff_idx = len(all_values)
        for r_idx in range(1, len(all_values)):
            row_str = " ".join([str(c) for c in all_values[r_idx] if c is not None])
            if "FM (SELF APP CODE)" in row_str or "FM (SELF" in row_str:
                cutoff_idx = r_idx
                break
        all_values = all_values[:cutoff_idx]
        while len(all_values) > 1:
            if all(c is None or str(c).strip() == "" for c in all_values[-1]):
                all_values.pop()
            else:
                break

        def gv(row, idx):
            return row[idx] if idx < len(row) else ""

        added = 0
        for row in all_values[1:]:
            mkt = _clean_market_name(gv(row, 3))  # MARKET (idx3)
            if not mkt:
                continue
            # Strictly use Dream Apps MPO Code (idx 12) per user instruction
            for ci in (12,):  # DREAM APPS MPO CODE ONLY
                code = _clean_cell(gv(row, ci))
                if code and code not in mpo_map:
                    mpo_map[code] = mkt
                    added += 1
        print(f"Live Google Sheet: enriched {added} additional MPO->market entries.")
    except Exception as e:
        print(f"Note: Live Google Sheet unavailable ({str(e)[:80]}). Using local Excel union + depot fallback.")


def load_mpo_market_lookup():
    """
    Build the canonical MPO_CODE -> MARKET_NAME map.

    Field-force understanding (source priority):
      1. Live FieldEdit Google Sheet (complete source of truth) — attempted first;
         silently falls back if the service account key is revoked/unavailable.
      2. FieldEdit/Archive/FIELD.xlsx  — flat export of that same Google Sheet
         (DEPOT, ZONE, NEW CODE, MARKET, OLD CODE, ..., DREAM APPS MPO CODE,
          DEPOTMPO CODE, APP CODE (FINAL)). Multiple code columns all map to MARKET.
      3. 02E_FINAL_MPO_Target_vs_Achievement (col5 code -> col4 market).
      4. archive/03_Zone_Wise_Sales_Grouped_Report (FIXED: col9 DREAM APPS MPO CODE
         -> col3 MARKET). NOTE: the previous code wrongly read col4 (FM/AM,ZONE text)
         as the code; the real MPO code lives in col9.
      5. archive/recent/mpo_code.xlsx (the file init_db.py joins against).

    Market names are normalised via clean_market_name (uppercase / whitespace /
    HATIBANDHA override) to match the human-level standard formatting used by
    the field-force reports.
    """
    mpo_map = {}

    # 1. Live Google Sheet (best-effort; enriches on top of local union)
    _try_google_sheet_market_map(mpo_map)

    # 2. FIELD.xlsx — flat export of the live Google Sheet (richest local source)
    _add_from_excel(
        mpo_map,
        os.path.join(PARENT_DIR, "FieldEdit", "Archive", "FIELD.xlsx"),
        header_row=1,
        code_cols=[13],                  # DREAM APPS MPO CODE ONLY (strictly col M per user instruction)
        market_col=4,                    # MARKET
    )

    # 3. 02E achievement report (code col5 -> market col4)
    _add_from_excel(
        mpo_map,
        os.path.join(PARENT_DIR, "02E_FINAL_MPO_Target_vs_Achievement_Values_24_Jun_2026_02.13_PM.xlsx"),
        header_row=3,
        code_cols=[5],
        market_col=4,
    )

    # 4. 03_Zone_Wise — FIXED: real MPO code is in col9 (DREAM APPS MPO CODE), market in col3
    _add_from_excel(
        mpo_map,
        os.path.join(PARENT_DIR, "archive", "03_Zone_Wise_Sales_Grouped_Report_23_Jun_2026_09.30_AM.xlsx"),
        header_row=1,
        code_cols=[9],   # was wrongly 4
        market_col=3,
    )

    # 5. mpo_code.xlsx — the file the init pipeline LEFT JOINs against
    #    Schema: col1 DEPOT, col2 ZONE, col3 MARKET, col4 FM/AM, col5 MPO CODE
    _add_from_excel(
        mpo_map,
        os.path.join(PARENT_DIR, "archive", "recent", "mpo_code.xlsx"),
        header_row=1,
        code_cols=[5],   # MPO CODE
        market_col=3,     # MARKET
    )

    return mpo_map


def load_vacant_mpos():
    """
    Returns a set of canonical Dream Apps MPO Codes that are marked as VACANT
    in the master field forces sheets (checking column I / VACANT (JUN'26)? / VACANT (JAN'26)?).
    Per user instruction: Vacant status is strictly determined by Column I, never by
    ambiguous text labels like 'DK.A' or 'Vacant' in market names.
    """
    vacant_codes = set()
    
    # 1. Try Live Google Sheet
    try:
        import json, sys
        sys.path.insert(0, PARENT_DIR)
        from googleDrive.credentials_loader import get_sheet_service_account_credentials, get_spreadsheet_id

        import gspread
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = get_sheet_service_account_credentials(scopes=scopes)
        client = gspread.authorize(creds)
        sheet_id = get_spreadsheet_id('master_field_force_sheet') or '1Q4utivZ5OpgDznqlqElYU-HWNnZYI71YYpcZKcSM3xY'
        sheet = client.open_by_key(sheet_id)
        worksheet = None
        target_gid = '1918615875'  # from credentials_master.json
        for ws in sheet.worksheets():
            if str(ws.id) == target_gid:
                worksheet = ws
                break
        if not worksheet:
            worksheet = sheet.get_worksheet(0)
        all_values = worksheet.get_all_values()

        def gv(row, idx):
            return row[idx] if idx < len(row) else ""

        for row in all_values[1:]:
            vac_val = _clean_cell(gv(row, 8)) # Col I (index 8)
            if vac_val in ('Y', 'YES', 'TRUE', '1'):
                        code = _clean_cell(gv(row, 12)) # Dream Apps MPO Code (index 12)
                        if code:
                            vacant_codes.add(code)
    except Exception as e:
        pass

    # 2. Try FIELD.xlsx
    try:
        import openpyxl
        fpath = os.path.join(PARENT_DIR, "FieldEdit", "Archive", "FIELD.xlsx")
        if os.path.exists(fpath):
            wb = openpyxl.load_workbook(fpath, data_only=True)
            ws = wb.active
            for r in range(2, ws.max_row + 1):
                vac_val = _clean_cell(ws.cell(row=r, column=9).value) # Col I (column 9)
                if vac_val in ('Y', 'YES', 'TRUE', '1'):
                    code = _clean_cell(ws.cell(row=r, column=13).value) # Dream Apps MPO Code (col 13)
                    if code:
                        vacant_codes.add(code)
    except Exception as e:
        pass

    return vacant_codes


def load_valid_master_filters(mpo_market_map):
    """
    Returns (valid_mpos, valid_fms, valid_zones) loaded strictly from Master Sheets
    (Google Sheet, FIELD.xlsx, 03_Zone_Wise, 02E).
    This ensures we filter out all non-field / institutional / bulk DB records like D203, D204
    and dummy text strings across all queries.
    """
    valid_mpos = set(mpo_market_map.keys())
    valid_fms = set()
    valid_zones = set()

    # 1. From FIELD.xlsx
    fe_xlsx = os.path.join(PARENT_DIR, "FieldEdit", "Archive", "FIELD.xlsx")
    if os.path.exists(fe_xlsx):
        try:
            wb = openpyxl.load_workbook(fe_xlsx, data_only=True)
            ws = wb.active
            for r in range(2, ws.max_row + 1):
                c13 = _clean_cell(ws.cell(row=r, column=13).value)
                if c13:
                    valid_mpos.add(c13)
                c7 = _clean_cell(ws.cell(row=r, column=7).value)
                if c7 and "VACANT" not in c7.upper():
                    valid_fms.add(c7)
                c2 = _clean_cell(ws.cell(row=r, column=2).value)
                if c2:
                    valid_zones.add(c2)
        except Exception:
            pass

    # 2. From 03_Zone_Wise
    for path in [os.path.join(PARENT_DIR, "03_Zone_Wise_Sales_Grouped_Report_24_Jun_2026_02.14_PM.xlsx"),
                 os.path.join(PARENT_DIR, "archive", "03_Zone_Wise_Sales_Grouped_Report_24_Jun_2026_02.14_PM.xlsx"),
                 os.path.join(PARENT_DIR, "archive", "03_Zone_Wise_Sales_Grouped_Report_23_Jun_2026_09.30_AM.xlsx")]:
        if os.path.exists(path):
            try:
                wb = openpyxl.load_workbook(path, data_only=True)
                ws = wb.active
                for r in range(2, ws.max_row + 1):
                    c9 = _clean_cell(ws.cell(row=r, column=9).value)
                    if c9:
                        valid_mpos.add(c9)
                    c4 = _clean_cell(ws.cell(row=r, column=4).value)
                    if c4:
                        fm_part = c4.split(',')[0].strip()
                        if fm_part and "VACANT" not in fm_part.upper():
                            valid_fms.add(fm_part)
                    c2 = _clean_cell(ws.cell(row=r, column=2).value)
                    if c2:
                        valid_zones.add(c2)
            except Exception:
                pass

    return sorted(list(valid_mpos)), sorted(list(valid_fms)), sorted(list(valid_zones))


class DataEngine:
    def __init__(self, db_path=DEFAULT_DB_PATH):
        self.db_path = db_path
        if not os.path.exists(self.db_path):
            print(f"Warning: Database not found at {self.db_path}")

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def generate_all_data(self):
        """
        Executes all SQL calculations emphasizing PRODUCT CODE as primary identifier,
        grouping by SUB_GROUP_STANDARD, and calculating the 6 Strategic Products Top 50 MPO by UNIT.
        """
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        mpo_market_map = load_mpo_market_lookup()
        vacant_mpo_codes = load_vacant_mpos()
        valid_mpos, valid_fms, valid_zones = load_valid_master_filters(mpo_market_map)
        
        ph_mpos = ",".join(["?"] * len(valid_mpos))
        ph_fms = ",".join(["?"] * len(valid_fms))
        ph_zones = ",".join(["?"] * len(valid_zones))

        data = {
            "meta": {
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "db_path": self.db_path,
                "note": "Product calculations are anchored on product_code and grouped by SUB_GROUP_STANDARD."
            },
            "kpis": {},
            "top_50_products": [],
            "top_5_products_deep": [],
            "top_50_mpos": [],
            "top_20_fms": [],
            "top_5_sector_heads": [],
            "monthly_trends": [],
            "strategic_6_products": {}
        }

        try:
            # 1. OVERVIEW KPIS
            cur.execute(f"""
                SELECT 
                    SUM(line_amount) as total_sales,
                    COUNT(DISTINCT invoice_no) as total_invoices,
                    COUNT(DISTINCT customer_id) as total_parties,
                    COUNT(DISTINCT mpo_code) as total_mpos,
                    COUNT(DISTINCT product_code) as total_products,
                    COUNT(DISTINCT fm_am) as total_fms
                FROM sales
                WHERE mpo_code IN ({ph_mpos})
            """, valid_mpos)
            row = cur.fetchone()
            total_sales = float(row["total_sales"] or 0)
            total_invoices = int(row["total_invoices"] or 0)
            total_parties = int(row["total_parties"] or 0)
            
            data["kpis"] = {
                "total_sales": total_sales,
                "total_invoices": total_invoices,
                "total_parties": total_parties,
                "total_mpos": int(row["total_mpos"] or 0),
                "total_products": int(row["total_products"] or 0),
                "total_fms": int(row["total_fms"] or 0),
                "avg_invoice_val": round(total_sales / total_invoices, 2) if total_invoices > 0 else 0
            }

            # 2. MONTHLY TRENDS (Overall)
            cur.execute(f"""
                SELECT 
                    month,
                    SUM(line_amount) as sales,
                    COUNT(DISTINCT invoice_no) as invoices,
                    COUNT(DISTINCT customer_id) as parties,
                    SUM(quantity) as quantity
                FROM sales
                WHERE mpo_code IN ({ph_mpos})
                GROUP BY month
                ORDER BY month ASC
            """, valid_mpos)
            for r in cur.fetchall():
                data["monthly_trends"].append({
                    "month": r["month"],
                    "sales": round(float(r["sales"] or 0), 2),
                    "invoices": int(r["invoices"] or 0),
                    "parties": int(r["parties"] or 0),
                    "quantity": round(float(r["quantity"] or 0), 2)
                })

            # 3. TOP 50 PRODUCTS CALCULATION (Grouped/merged by SUB_GROUP_STANDARD as per user rule)
            code_to_subgroup = load_excel_mappings()

            cur.execute(f"""
                SELECT 
                    product_code,
                    MAX(product_name) as product_name,
                    SUM(line_amount) as total_sales,
                    SUM(quantity) as total_quantity,
                    COUNT(DISTINCT invoice_no) as total_invoices,
                    COUNT(DISTINCT customer_id) as total_parties
                FROM sales
                WHERE product_code IS NOT NULL AND product_code != '' AND mpo_code IN ({ph_mpos})
                GROUP BY product_code
            """, valid_mpos)
            raw_prod_rows = cur.fetchall()
            
            # Group/merge by SUB_GROUP_STANDARD
            grouped_prods = {}
            for r in raw_prod_rows:
                p_code = str(r["product_code"]).strip().upper()
                grp_name = code_to_subgroup.get(p_code, r["product_name"] or p_code)
                if grp_name not in grouped_prods:
                    grouped_prods[grp_name] = {
                        "group_name": grp_name,
                        "codes": [],
                        "total_sales": 0.0,
                        "total_quantity": 0.0,
                        "total_invoices": 0,
                        "total_parties": 0
                    }
                grouped_prods[grp_name]["codes"].append(p_code)
                grouped_prods[grp_name]["total_sales"] += float(r["total_sales"] or 0)
                grouped_prods[grp_name]["total_quantity"] += float(r["total_quantity"] or 0)
                grouped_prods[grp_name]["total_invoices"] += int(r["total_invoices"] or 0)
                grouped_prods[grp_name]["total_parties"] += int(r["total_parties"] or 0)

            # Sort descending by total_sales and take Top 50
            sorted_groups = sorted(grouped_prods.values(), key=lambda x: x["total_sales"], reverse=True)[:50]
            
            for idx, g in enumerate(sorted_groups, 1):
                placeholders = ",".join(["?"] * len(g["codes"]))
                cur.execute(f"""
                    SELECT 
                        month,
                        SUM(line_amount) as m_sales,
                        SUM(quantity) as m_qty,
                        COUNT(DISTINCT invoice_no) as m_invoices,
                        COUNT(DISTINCT customer_id) as m_parties
                    FROM sales
                    WHERE product_code IN ({placeholders}) AND mpo_code IN ({ph_mpos})
                    GROUP BY month
                    ORDER BY month ASC
                """, (*g["codes"], *valid_mpos))
                m_breakdown = []
                for mb in cur.fetchall():
                    m_breakdown.append({
                        "month": mb["month"],
                        "sales": round(float(mb["m_sales"] or 0), 2),
                        "quantity": round(float(mb["m_qty"] or 0), 2),
                        "invoices": int(mb["m_invoices"] or 0),
                        "parties": int(mb["m_parties"] or 0)
                    })

                prod_item = {
                    "rank": idx,
                    "product_code": ", ".join(g["codes"]),
                    "product_name": g["group_name"],
                    "total_sales": round(g["total_sales"], 2),
                    "total_quantity": round(g["total_quantity"], 2),
                    "total_invoices": g["total_invoices"],
                    "total_parties": g["total_parties"],
                    "contribution_pct": round((g["total_sales"] / total_sales) * 100, 2) if total_sales > 0 else 0,
                    "monthly_breakdown": m_breakdown
                }
                data["top_50_products"].append(prod_item)
                if idx <= 5:
                    data["top_5_products_deep"].append(prod_item)

            # 4. TOP 50 MPO CALCULATION
            cur.execute(f"""
                SELECT 
                    mpo_code,
                    MAX(zone) as zone,
                    MAX(depot) as depot,
                    MAX(market) as market,
                    SUM(line_amount) as total_sales,
                    SUM(quantity) as total_quantity,
                    COUNT(DISTINCT invoice_no) as total_invoices,
                    COUNT(DISTINCT customer_id) as total_parties
                FROM sales
                WHERE mpo_code IN ({ph_mpos})
                GROUP BY mpo_code
                ORDER BY SUM(line_amount) DESC
                LIMIT 50
            """, valid_mpos)
            top_50_mpo_rows = cur.fetchall()
            
            for idx, r in enumerate(top_50_mpo_rows, 1):
                m_code = r["mpo_code"]
                m_sales = float(r["total_sales"] or 0)

                cur.execute("""
                    SELECT
                        month,
                        SUM(line_amount) as m_sales,
                        SUM(quantity) as m_units,
                        COUNT(DISTINCT invoice_no) as m_invoices,
                        COUNT(DISTINCT customer_id) as m_parties
                    FROM sales
                    WHERE mpo_code = ?
                    GROUP BY month
                    ORDER BY month ASC
                """, (m_code,))
                m_breakdown = []
                for mb in cur.fetchall():
                    m_breakdown.append({
                        "month": mb["month"],
                        "sales": round(float(mb["m_sales"] or 0), 2),
                        "units": round(float(mb["m_units"] or 0), 2),
                        "quantity": round(float(mb["m_units"] or 0), 2),
                        "invoices": int(mb["m_invoices"] or 0),
                        "parties": int(mb["m_parties"] or 0)
                    })

                raw_mkt = r["market"]
                if not raw_mkt or str(raw_mkt).strip() in ['', 'None', 'Unknown'] or str(raw_mkt).strip().startswith('DK.'):
                    # Zone codes like 'DK.A'/'DK.B' are NOT market names (they mean Dhaka-A/B);
                    # fall back to the mapped market, then to the real DEPOT name (never the zone).
                    raw_mkt = mpo_market_map.get(m_code) or _clean_cell(r["depot"]) or "Unknown"

                data["top_50_mpos"].append({
                    "rank": idx,
                    "mpo_code": m_code,
                    "market": raw_mkt,
                    "zone": r["zone"] or "Unknown",
                    "depot": r["depot"] or "Unknown",
                    "is_vacant": m_code in vacant_mpo_codes,
                    "total_sales": round(m_sales, 2),
                    "total_quantity": round(float(r["total_quantity"] or 0), 2),
                    "total_invoices": int(r["total_invoices"] or 0),
                    "total_parties": int(r["total_parties"] or 0),
                    "contribution_pct": round((m_sales / total_sales) * 100, 2) if total_sales > 0 else 0,
                    "monthly_breakdown": m_breakdown
                })

            # 5. TOP 20 FM (Field Managers)
            cur.execute(f"""
                SELECT 
                    fm_am as fm_name,
                    SUM(line_amount) as total_sales,
                    COUNT(DISTINCT mpo_code) as active_mpos,
                    COUNT(DISTINCT invoice_no) as total_invoices,
                    COUNT(DISTINCT customer_id) as total_parties
                FROM sales
                WHERE fm_am IN ({ph_fms}) AND mpo_code IN ({ph_mpos})
                GROUP BY fm_am
                ORDER BY SUM(line_amount) DESC
                LIMIT 20
            """, (*valid_fms, *valid_mpos))
            for idx, r in enumerate(cur.fetchall(), 1):
                fm_sales = float(r["total_sales"] or 0)
                data["top_20_fms"].append({
                    "rank": idx,
                    "fm_name": r["fm_name"],
                    "total_sales": round(fm_sales, 2),
                    "active_mpos": int(r["active_mpos"] or 0),
                    "total_invoices": int(r["total_invoices"] or 0),
                    "total_parties": int(r["total_parties"] or 0),
                    "contribution_pct": round((fm_sales / total_sales) * 100, 2) if total_sales > 0 else 0
                })

            # 6. TOP 5 SECTOR HEADS / ZONES
            cur.execute(f"""
                SELECT 
                    zone as sector_name,
                    SUM(line_amount) as total_sales,
                    COUNT(DISTINCT mpo_code) as active_mpos,
                    COUNT(DISTINCT invoice_no) as total_invoices,
                    COUNT(DISTINCT customer_id) as total_parties
                FROM sales
                WHERE zone IN ({ph_zones}) AND mpo_code IN ({ph_mpos})
                GROUP BY zone
                ORDER BY SUM(line_amount) DESC
                LIMIT 5
            """, (*valid_zones, *valid_mpos))
            for idx, r in enumerate(cur.fetchall(), 1):
                sec_sales = float(r["total_sales"] or 0)
                data["top_5_sector_heads"].append({
                    "rank": idx,
                    "sector_name": r["sector_name"],
                    "total_sales": round(sec_sales, 2),
                    "active_mpos": int(r["active_mpos"] or 0),
                    "total_invoices": int(r["total_invoices"] or 0),
                    "total_parties": int(r["total_parties"] or 0),
                    "contribution_pct": round((sec_sales / total_sales) * 100, 2) if total_sales > 0 else 0
                })

            # 7. STRATEGIC 6 PRODUCTS (TOP 50 MPO HIERARCHY BY UNIT WITH MONTH-WISE DATA)
            distinct_months = [t["month"] for t in data["monthly_trends"]]
            
            for prod_name, codes in STRATEGIC_6_MAPPING.items():
                placeholders = ",".join(["?"] * len(codes))
                
                # Overall stats
                cur.execute(f"""
                    SELECT 
                        SUM(quantity) as tot_units,
                        SUM(line_amount) as tot_sales,
                        COUNT(DISTINCT customer_id) as tot_parties,
                        COUNT(DISTINCT invoice_no) as tot_invoices
                    FROM sales
                    WHERE product_code IN ({placeholders}) AND mpo_code IN ({ph_mpos})
                """, (*codes, *valid_mpos))
                stat_row = cur.fetchone()
                
                # Top 50 MPOs overall sorted by UNIT DESC (Hierarchy by unit)
                cur.execute(f"""
                    SELECT 
                        mpo_code,
                        zone,
                        MAX(market) as market,
                        MAX(depot) as depot,
                        MAX(fm_am) as fm_name,
                        SUM(quantity) as units,
                        COUNT(DISTINCT customer_id) as parties,
                        COUNT(DISTINCT invoice_no) as invoices,
                        SUM(line_amount) as sales
                    FROM sales
                    WHERE product_code IN ({placeholders}) AND mpo_code IN ({ph_mpos})
                    GROUP BY mpo_code, zone
                    ORDER BY SUM(quantity) DESC
                """, (*codes, *valid_mpos))
                
                mpo_list_all = []
                for idx, mr in enumerate(cur.fetchall(), 1):
                    m_code = mr["mpo_code"]
                    m_zone = mr["zone"]
                    
                    cur.execute(f"""
                        SELECT 
                            month,
                            SUM(quantity) as m_units,
                            COUNT(DISTINCT customer_id) as m_parties,
                            COUNT(DISTINCT invoice_no) as m_invoices,
                            SUM(line_amount) as m_sales
                        FROM sales
                        WHERE product_code IN ({placeholders}) AND mpo_code = ? AND zone = ?
                        GROUP BY month
                        ORDER BY month ASC
                    """, (*codes, m_code, m_zone))
                    m_break = []
                    for mb in cur.fetchall():
                        m_break.append({
                            "month": mb["month"],
                            "units": round(float(mb["m_units"] or 0), 2),
                            "parties": int(mb["m_parties"] or 0),
                            "invoices": int(mb["m_invoices"] or 0),
                            "sales": round(float(mb["m_sales"] or 0), 2)
                        })
                        
                    raw_mkt = mr["market"]
                    if not raw_mkt or str(raw_mkt).strip() in ['', 'None', 'Unknown'] or str(raw_mkt).strip().startswith('DK.'):
                        raw_mkt = mpo_market_map.get(m_code) or _clean_cell(mr["depot"]) or "Unknown"

                    mpo_list_all.append({
                        "rank": idx,
                        "mpo_code": m_code,
                        "market": raw_mkt,
                        "zone": mr["zone"] or "Unknown",
                        "depot": mr["depot"] or "Unknown",
                        "fm_name": mr["fm_name"] or "Unknown",
                        "is_vacant": m_code in vacant_mpo_codes,
                        "units": round(float(mr["units"] or 0), 2),
                        "parties": int(mr["parties"] or 0),
                        "invoices": int(mr["invoices"] or 0),
                        "sales": round(float(mr["sales"] or 0), 2),
                        "monthly_breakdown": m_break
                    })
                    
                # Month-wise Top 50 MPOs (by unit)
                mpo_by_month = {}
                for m_val in distinct_months:
                    cur.execute(f"""
                        SELECT 
                            mpo_code,
                            zone,
                            MAX(market) as market,
                            MAX(depot) as depot,
                            MAX(fm_am) as fm_name,
                            SUM(quantity) as units,
                            COUNT(DISTINCT customer_id) as parties,
                            COUNT(DISTINCT invoice_no) as invoices,
                            SUM(line_amount) as sales
                        FROM sales
                        WHERE product_code IN ({placeholders}) AND month = ? AND mpo_code IN ({ph_mpos})
                        GROUP BY mpo_code, zone
                        ORDER BY SUM(quantity) DESC
                    """, (*codes, m_val, *valid_mpos))
                    mpo_list_month = []
                    for idx, mr in enumerate(cur.fetchall(), 1):
                        raw_mkt = mr["market"]
                        if not raw_mkt or str(raw_mkt).strip() in ['', 'None', 'Unknown'] or str(raw_mkt).strip().startswith('DK.'):
                            raw_mkt = mpo_market_map.get(mr["mpo_code"]) or _clean_cell(mr["depot"]) or "Unknown"

                        mpo_list_month.append({
                            "rank": idx,
                            "mpo_code": mr["mpo_code"],
                            "market": raw_mkt,
                            "zone": mr["zone"] or "Unknown",
                            "depot": mr["depot"] or "Unknown",
                            "fm_name": mr["fm_name"] or "Unknown",
                            "is_vacant": mr["mpo_code"] in vacant_mpo_codes,
                            "units": round(float(mr["units"] or 0), 2),
                            "parties": int(mr["parties"] or 0),
                            "invoices": int(mr["invoices"] or 0),
                            "sales": round(float(mr["sales"] or 0), 2)
                        })
                    mpo_by_month[m_val] = mpo_list_month
                    
                data["strategic_6_products"][prod_name] = {
                    "product_name": prod_name,
                    "merged_codes": codes,
                    "total_units": round(float(stat_row["tot_units"] or 0), 2),
                    "total_sales": round(float(stat_row["tot_sales"] or 0), 2),
                    "total_parties": int(stat_row["tot_parties"] or 0),
                    "total_invoices": int(stat_row["tot_invoices"] or 0),
                    "mpo_top50_all": mpo_list_all,
                    "mpo_top50_by_month": mpo_by_month
                }

            # Process all remaining products
            strategic_6_names = list(STRATEGIC_6_MAPPING.keys())
            remaining_products = [grp for grp in grouped_prods.keys() if grp not in strategic_6_names]
            
            for prod_name in remaining_products:
                codes = grouped_prods[prod_name]["codes"]
                if not codes:
                    continue
                placeholders = ",".join(["?"] * len(codes))
                
                # Overall stats
                cur.execute(f"""
                    SELECT 
                        SUM(quantity) as tot_units,
                        SUM(line_amount) as tot_sales,
                        COUNT(DISTINCT customer_id) as tot_parties,
                        COUNT(DISTINCT invoice_no) as tot_invoices
                    FROM sales
                    WHERE product_code IN ({placeholders}) AND mpo_code IN ({ph_mpos})
                """, (*codes, *valid_mpos))
                stat_row = cur.fetchone()
                
                # Top 50 MPOs overall sorted by UNIT DESC (Hierarchy by unit)
                cur.execute(f"""
                    SELECT 
                        mpo_code,
                        zone,
                        MAX(market) as market,
                        MAX(depot) as depot,
                        MAX(fm_am) as fm_name,
                        SUM(quantity) as units,
                        COUNT(DISTINCT customer_id) as parties,
                        COUNT(DISTINCT invoice_no) as invoices,
                        SUM(line_amount) as sales
                    FROM sales
                    WHERE product_code IN ({placeholders}) AND mpo_code IN ({ph_mpos})
                    GROUP BY mpo_code, zone
                    ORDER BY SUM(quantity) DESC
                """, (*codes, *valid_mpos))
                
                mpo_list_all = []
                for idx, mr in enumerate(cur.fetchall(), 1):
                    m_code = mr["mpo_code"]
                    m_zone = mr["zone"]
                    
                    cur.execute(f"""
                        SELECT 
                            month,
                            SUM(quantity) as m_units,
                            COUNT(DISTINCT customer_id) as m_parties,
                            COUNT(DISTINCT invoice_no) as m_invoices,
                            SUM(line_amount) as m_sales
                        FROM sales
                        WHERE product_code IN ({placeholders}) AND mpo_code = ? AND zone = ?
                        GROUP BY month
                        ORDER BY month ASC
                    """, (*codes, m_code, m_zone))
                    m_break = []
                    for mb in cur.fetchall():
                        m_break.append({
                            "month": mb["month"],
                            "units": round(float(mb["m_units"] or 0), 2),
                            "parties": int(mb["m_parties"] or 0),
                            "invoices": int(mb["m_invoices"] or 0),
                            "sales": round(float(mb["m_sales"] or 0), 2)
                        })
                        
                    raw_mkt = mr["market"]
                    if not raw_mkt or str(raw_mkt).strip() in ['', 'None', 'Unknown'] or str(raw_mkt).strip().startswith('DK.'):
                        raw_mkt = mpo_market_map.get(m_code) or _clean_cell(mr["depot"]) or "Unknown"

                    mpo_list_all.append({
                        "rank": idx,
                        "mpo_code": m_code,
                        "market": raw_mkt,
                        "zone": mr["zone"] or "Unknown",
                        "depot": mr["depot"] or "Unknown",
                        "fm_name": mr["fm_name"] or "Unknown",
                        "is_vacant": m_code in vacant_mpo_codes,
                        "units": round(float(mr["units"] or 0), 2),
                        "parties": int(mr["parties"] or 0),
                        "invoices": int(mr["invoices"] or 0),
                        "sales": round(float(mr["sales"] or 0), 2),
                        "monthly_breakdown": m_break
                    })
                    
                # Month-wise Top 50 MPOs (by unit)
                mpo_by_month = {}
                for m_val in distinct_months:
                    cur.execute(f"""
                        SELECT 
                            mpo_code,
                            zone,
                            MAX(market) as market,
                            MAX(depot) as depot,
                            MAX(fm_am) as fm_name,
                            SUM(quantity) as units,
                            COUNT(DISTINCT customer_id) as parties,
                            COUNT(DISTINCT invoice_no) as invoices,
                            SUM(line_amount) as sales
                        FROM sales
                        WHERE product_code IN ({placeholders}) AND month = ? AND mpo_code IN ({ph_mpos})
                        GROUP BY mpo_code, zone
                        ORDER BY SUM(quantity) DESC
                    """, (*codes, m_val, *valid_mpos))
                    mpo_list_month = []
                    for idx, mr in enumerate(cur.fetchall(), 1):
                        raw_mkt = mr["market"]
                        if not raw_mkt or str(raw_mkt).strip() in ['', 'None', 'Unknown'] or str(raw_mkt).strip().startswith('DK.'):
                            raw_mkt = mpo_market_map.get(mr["mpo_code"]) or _clean_cell(mr["depot"]) or "Unknown"

                        mpo_list_month.append({
                            "rank": idx,
                            "mpo_code": mr["mpo_code"],
                            "market": raw_mkt,
                            "zone": mr["zone"] or "Unknown",
                            "depot": mr["depot"] or "Unknown",
                            "fm_name": mr["fm_name"] or "Unknown",
                            "is_vacant": mr["mpo_code"] in vacant_mpo_codes,
                            "units": round(float(mr["units"] or 0), 2),
                            "parties": int(mr["parties"] or 0),
                            "invoices": int(mr["invoices"] or 0),
                            "sales": round(float(mr["sales"] or 0), 2)
                        })
                    mpo_by_month[m_val] = mpo_list_month
                    
                data["strategic_6_products"][prod_name] = {
                    "product_name": prod_name,
                    "merged_codes": codes,
                    "total_units": round(float(stat_row["tot_units"] or 0), 2),
                    "total_sales": round(float(stat_row["tot_sales"] or 0), 2),
                    "total_parties": int(stat_row["tot_parties"] or 0),
                    "total_invoices": int(stat_row["tot_invoices"] or 0),
                    "mpo_top50_all": mpo_list_all,
                    "mpo_top50_by_month": mpo_by_month
                }

            sorted_remaining = sorted(remaining_products)
            data["_strategic_keys"] = strategic_6_names + sorted_remaining


        except Exception as e:
            print(f"Error executing SQL calculations: {e}")
            raise
        finally:
            conn.close()

        # Save to JSON for static / instant dashboard load
        out_file = os.path.join(DATA_OUT_DIR, "api_data.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        print(f"✓ Data generation complete! Saved snapshot to: {out_file}")
        return data

if __name__ == "__main__":
    engine = DataEngine()
    engine.generate_all_data()
