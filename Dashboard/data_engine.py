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
        url = 'https://docs.google.com/spreadsheets/d/1Q4utivZ5OpgDznqlqElYU-HWNnZYI71YYpcZKcSM3xY/export?format=csv&gid=1219133636'
        import pandas as pd
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        
        code_to_subgroup = {}
        dyn_s6 = {}
        for _, r in df.iterrows():
            pcode_raw = str(r.get('Product_Code', '')).strip().upper()
            pcode_all = str(r.get('PRODUCT_CODE_ALL_ROW', '')).strip().upper()
            code = pcode_raw if (pcode_raw and pcode_raw != "NAN") else pcode_all
            
            if not code or code == "NAN":
                continue
                
            subg = str(r.get('SUB_GROUP_STANDARD', '')).strip()
            if subg and subg != "NAN":
                code_to_subgroup[code] = subg
                
            s6_val = str(r.get('TOP_50_CALCULATION', '')).strip()
            if s6_val and s6_val != "NAN" and s6_val.lower() != "nan":
                dyn_s6.setdefault(s6_val, []).append(code)
                
        strategic_6_map = {k: sorted(list(set(v))) for k, v in dyn_s6.items() if k and k.lower() != 'nan'} if dyn_s6 else None
        print(f"Live Public Google Sheet (gid=1219133636): loaded {len(code_to_subgroup)} product subgroups and {len(strategic_6_map or {})} strategic groups.")
        _try_google_sheet_products._cache = (code_to_subgroup, strategic_6_map)
        return code_to_subgroup, strategic_6_map
    except Exception as e:
        print(f"[CRITICAL ERROR] Live Google Sheet for products failed: {e}")
        raise RuntimeError(f"Public Google Sheet product mapping fetch failed: {e}")

def load_strategic_6_mapping():
    _, gs_s6 = _try_google_sheet_products()
    if gs_s6:
        return gs_s6
    return {
        'ALAGRA 120 TAB': ['ALK1', 'ALM1', 'ZA04', 'ZA05'],
        'ALAGRA 180 TAB': ['ALN1', 'ALP1'],
        'AMDIN PLUS TAB': ['AMK3', 'AMM3', 'ZA11'],
        'DERMA CAP': ['DEJ1', 'DEK1', 'DEM1', 'DEN1', 'ZD01'],
        'MOKAST 10 TAB': ['MON1', 'MOO1', 'MOP1'],
        'TOLEC TAB': ['TOL2']
    }

STRATEGIC_6_MAPPING = load_strategic_6_mapping()

def load_excel_mappings():
    gs_subg, _ = _try_google_sheet_products()
    code_to_subgroup = gs_subg or {}
    for grp_name, codes in STRATEGIC_6_MAPPING.items():
        for c in codes:
            code_to_subgroup[c] = grp_name
    return code_to_subgroup

def _clean_cell(val):
    if val is None:
        return ''
    s = str(val).strip()
    return '' if s in ('None', 'nan', 'NaN') else s

def _clean_market_name(name):
    if not name:
        return ''
    name = _clean_cell(name).upper()
    import re
    name = re.sub(r'\s+', ' ', name)
    if name == 'HATIBANDHA (HATIB.)':
        return 'HATIBANDHA (HATIBANDHA-1)'
    return name

def load_mpo_market_lookup():
    mpo_map = {}
    try:
        url = 'https://docs.google.com/spreadsheets/d/1Q4utivZ5OpgDznqlqElYU-HWNnZYI71YYpcZKcSM3xY/export?format=csv&gid=1918615875'
        import pandas as pd
        df = pd.read_csv(url)
        
        for _, row in df.iterrows():
            mkt = _clean_market_name(row.get('MARKET'))
            depot = _clean_cell(row.get('DREAM APPS DEPOT')) or _clean_cell(row.get('DEPOT'))
            code = _clean_cell(row.get('DEPOTMPO CODE')) or _clean_cell(row.get('DREAM APPS MPO CODE'))
            if mkt and code:
                # Key by MPO code as well as composite key (DEPOT_MPO_CODE)
                mpo_map[code] = mkt
                if depot:
                    composite_key = f"{depot.upper()}_{code.upper()}"
                    mpo_map[composite_key] = mkt
        print(f"Live Public Google Sheet (gid=1918615875): loaded {len(mpo_map)} MPO->market entries (including DEPOT_MPO composite keys).")
        return mpo_map
    except Exception as e:
        print(f"[CRITICAL ERROR] Live Google Sheet market lookup failed: {e}")
        raise RuntimeError(f"Public Google Sheet market lookup failed: {e}")

def load_vacant_mpos():
    vacant_codes = set()
    try:
        url = 'https://docs.google.com/spreadsheets/d/1Q4utivZ5OpgDznqlqElYU-HWNnZYI71YYpcZKcSM3xY/export?format=csv&gid=1918615875'
        import pandas as pd
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        
        for _, row in df.iterrows():
            vac_val = _clean_cell(row.get("VACANT (JUN'26)?"))
            if vac_val in ('Y', 'YES', 'TRUE', '1'):
                code = _clean_cell(row.get('DEPOTMPO CODE')) or _clean_cell(row.get('DREAM APPS MPO CODE'))
                if code:
                    vacant_codes.add(code)
    except Exception as e:
        print(f"Note: Could not load vacant MPOs from Google Sheet: {e}")
    return vacant_codes

def load_valid_master_filters(mpo_market_map):
    valid_mpos = set(mpo_market_map.keys())
    valid_fms = set()
    valid_zones = set()

    try:
        url = 'https://docs.google.com/spreadsheets/d/1Q4utivZ5OpgDznqlqElYU-HWNnZYI71YYpcZKcSM3xY/export?format=csv&gid=1918615875'
        import pandas as pd
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]

        for _, row in df.iterrows():
            c13 = _clean_cell(row.get('DREAM APPS MPO CODE'))
            if c13:
                valid_mpos.add(c13)
            c7 = _clean_cell(row.get('FM (FINAL NAME)')) or _clean_cell(row.get('FM/AM'))
            if c7 and "VACANT" not in c7.upper():
                valid_fms.add(c7)
            c2 = _clean_cell(row.get('DREAM APPS ZONE')) or _clean_cell(row.get('ZONE'))
            if c2:
                valid_zones.add(c2)
    except Exception as e:
        print(f"Note: Could not load master filters from Google Sheet: {e}")

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

            # Sort descending by total_quantity (Unit Box Qty Hierarchy) and process ALL product groups
            sorted_groups = sorted(grouped_prods.values(), key=lambda x: x["total_quantity"], reverse=True)
            
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

            # 4. ALL MPO CALCULATION (Sorted Hierarchy by Unit Box Sales)
            print("\n[DataEngine Progress] Processing ALL MPOs & Markets (Sorted by Unit Box Qty)...", flush=True)
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
                ORDER BY SUM(quantity) DESC
            """, valid_mpos)
            all_mpo_rows = cur.fetchall()
            total_mpo_count = len(all_mpo_rows)
            
            for idx, r in enumerate(all_mpo_rows, 1):
                m_code = r["mpo_code"]
                m_sales = float(r["total_sales"] or 0)
                m_qty = float(r["total_quantity"] or 0)

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
                    raw_mkt = mpo_market_map.get(m_code) or _clean_cell(r["depot"]) or "Unknown"

                if idx % 50 == 0 or idx == 1:
                    print(f"  ➜ Processing MPO [{idx}/{total_mpo_count}]: {m_code} | Market: {raw_mkt} | Units: {m_qty:,.0f}", flush=True)

                data["top_50_mpos"].append({
                    "rank": idx,
                    "mpo_code": m_code,
                    "market": raw_mkt,
                    "zone": r["zone"] or "Unknown",
                    "depot": r["depot"] or "Unknown",
                    "is_vacant": m_code in vacant_mpo_codes,
                    "total_sales": round(m_sales, 2),
                    "total_quantity": round(m_qty, 2),
                    "total_invoices": int(r["total_invoices"] or 0),
                    "total_parties": int(r["total_parties"] or 0),
                    "contribution_pct": round((m_sales / total_sales) * 100, 2) if total_sales > 0 else 0,
                    "monthly_breakdown": m_breakdown
                })

            # 5. ALL FIELD MANAGERS (FMs) (Sorted Hierarchy by Unit Box Sales)
            print("\n[DataEngine Progress] Processing ALL Field Managers (FMs) (Sorted by Unit Box Qty)...", flush=True)
            cur.execute(f"""
                SELECT 
                    fm_am as fm_name,
                    SUM(quantity) as total_quantity,
                    SUM(line_amount) as total_sales,
                    COUNT(DISTINCT mpo_code) as active_mpos,
                    COUNT(DISTINCT invoice_no) as total_invoices,
                    COUNT(DISTINCT customer_id) as total_parties
                FROM sales
                WHERE fm_am IN ({ph_fms}) AND mpo_code IN ({ph_mpos})
                GROUP BY fm_am
                ORDER BY SUM(quantity) DESC
            """, (*valid_fms, *valid_mpos))
            all_fm_rows = cur.fetchall()
            total_fm_count = len(all_fm_rows)
            for idx, r in enumerate(all_fm_rows, 1):
                fm_sales = float(r["total_sales"] or 0)
                fm_qty = float(r["total_quantity"] or 0)
                fm_nm = r["fm_name"]
                if idx % 10 == 0 or idx == 1:
                    print(f"  ➜ Processing FM [{idx}/{total_fm_count}]: {fm_nm} | Units: {fm_qty:,.0f}", flush=True)
                data["top_20_fms"].append({
                    "rank": idx,
                    "fm_name": fm_nm,
                    "total_sales": round(fm_sales, 2),
                    "total_quantity": round(fm_qty, 2),
                    "active_mpos": int(r["active_mpos"] or 0),
                    "total_invoices": int(r["total_invoices"] or 0),
                    "total_parties": int(r["total_parties"] or 0),
                    "contribution_pct": round((fm_sales / total_sales) * 100, 2) if total_sales > 0 else 0
                })

            # 6. ALL SECTOR HEADS / ZONES (Sorted Hierarchy by Unit Box Sales)
            print("\n[DataEngine Progress] Processing ALL Sector Heads / Zones (Sorted by Unit Box Qty)...", flush=True)
            cur.execute(f"""
                SELECT 
                    zone as sector_name,
                    SUM(quantity) as total_quantity,
                    SUM(line_amount) as total_sales,
                    COUNT(DISTINCT mpo_code) as active_mpos,
                    COUNT(DISTINCT invoice_no) as total_invoices,
                    COUNT(DISTINCT customer_id) as total_parties
                FROM sales
                WHERE zone IN ({ph_zones}) AND mpo_code IN ({ph_mpos})
                GROUP BY zone
                ORDER BY SUM(quantity) DESC
            """, (*valid_zones, *valid_mpos))
            all_zone_rows = cur.fetchall()
            total_zone_count = len(all_zone_rows)
            for idx, r in enumerate(all_zone_rows, 1):
                sec_sales = float(r["total_sales"] or 0)
                sec_qty = float(r["total_quantity"] or 0)
                sec_name = r["sector_name"]
                print(f"  ➜ Processing Zone [{idx}/{total_zone_count}]: {sec_name} (Units: {sec_qty:,.0f} | Sales: {sec_sales:,.2f})", flush=True)
                data["top_5_sector_heads"].append({
                    "rank": idx,
                    "sector_name": sec_name,
                    "total_sales": round(sec_sales, 2),
                    "total_quantity": round(sec_qty, 2),
                    "active_mpos": int(r["active_mpos"] or 0),
                    "total_invoices": int(r["total_invoices"] or 0),
                    "total_parties": int(r["total_parties"] or 0),
                    "contribution_pct": round((sec_sales / total_sales) * 100, 2) if total_sales > 0 else 0
                })

            # 7. STRATEGIC 6 PRODUCTS (TOP 50 MPO HIERARCHY BY UNIT WITH MONTH-WISE DATA)
            distinct_months = [t["month"] for t in data["monthly_trends"]]
            
            total_strat = len(STRATEGIC_6_MAPPING)
            print(f"\n[DataEngine Progress] Processing {total_strat} Strategic / Top Product Groups...", flush=True)
            for s_idx, (prod_name, codes) in enumerate(STRATEGIC_6_MAPPING.items(), 1):
                print(f"  ➜ [{s_idx}/{total_strat}] Processing Product Group: {prod_name} (Codes: {codes})", flush=True)
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
