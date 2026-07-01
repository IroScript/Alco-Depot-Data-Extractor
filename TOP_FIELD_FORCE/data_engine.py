import os
import sys
import sqlite3
import json
from datetime import datetime

# Define base directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
DEFAULT_DB_PATH = os.path.join(PARENT_DIR, "sales.db")
DATA_OUT_DIR = os.path.join(BASE_DIR, "data")

os.makedirs(DATA_OUT_DIR, exist_ok=True)

# 6 Strategic Product Groups defined by user
STRATEGIC_6_MAPPING = {
    'ALAGRA 120 TAB': ['ALK1', 'ALM1', 'ZA04', 'ZA05'],
    'ALAGRA 180 TAB': ['ALN1', 'ALP1'],
    'AMDIN PLUS TAB': ['AMK3', 'AMM3', 'ZA11'],
    'DERMA CAP': ['DEJ1', 'DEK1', 'DEM1', 'DEN1', 'ZD01'],
    'MOKAST 10 TAB': ['MON1', 'MOO1', 'MOP1'],
    'TOLEC TAB': ['TOL2']
}

def load_excel_mappings():
    excel_path = os.path.join(PARENT_DIR, "PRODUCT_CODE_AND_SUBGROUP_OF_PRODUCTS.xlsx")
    code_to_subgroup = {}
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
            print(f"Note: Could not read Excel mapping via pandas: {e}")
            
    # Always ensure strategic 6 mappings exist
    for grp_name, codes in STRATEGIC_6_MAPPING.items():
        for c in codes:
            code_to_subgroup[c] = grp_name
            
    return code_to_subgroup

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
            cur.execute("""
                SELECT 
                    SUM(line_amount) as total_sales,
                    COUNT(DISTINCT invoice_no) as total_invoices,
                    COUNT(DISTINCT customer_id) as total_parties,
                    COUNT(DISTINCT mpo_code) as total_mpos,
                    COUNT(DISTINCT product_code) as total_products,
                    COUNT(DISTINCT fm_am) as total_fms
                FROM sales
            """)
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
            cur.execute("""
                SELECT 
                    month,
                    SUM(line_amount) as sales,
                    COUNT(DISTINCT invoice_no) as invoices,
                    COUNT(DISTINCT customer_id) as parties,
                    SUM(quantity) as quantity
                FROM sales
                GROUP BY month
                ORDER BY month ASC
            """)
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

            cur.execute("""
                SELECT 
                    product_code,
                    MAX(product_name) as product_name,
                    SUM(line_amount) as total_sales,
                    SUM(quantity) as total_quantity,
                    COUNT(DISTINCT invoice_no) as total_invoices,
                    COUNT(DISTINCT customer_id) as total_parties
                FROM sales
                WHERE product_code IS NOT NULL AND product_code != ''
                GROUP BY product_code
            """)
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
                    WHERE product_code IN ({placeholders})
                    GROUP BY month
                    ORDER BY month ASC
                """, g["codes"])
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
            cur.execute("""
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
                WHERE mpo_code IS NOT NULL AND mpo_code != ''
                GROUP BY mpo_code
                ORDER BY SUM(line_amount) DESC
                LIMIT 50
            """)
            top_50_mpo_rows = cur.fetchall()
            
            for idx, r in enumerate(top_50_mpo_rows, 1):
                m_code = r["mpo_code"]
                m_sales = float(r["total_sales"] or 0)
                
                cur.execute("""
                    SELECT 
                        month,
                        SUM(line_amount) as m_sales,
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
                        "invoices": int(mb["m_invoices"] or 0),
                        "parties": int(mb["m_parties"] or 0)
                    })

                data["top_50_mpos"].append({
                    "rank": idx,
                    "mpo_code": m_code,
                    "market": r["market"] or r["zone"] or "Unknown",
                    "zone": r["zone"] or "Unknown",
                    "depot": r["depot"] or "Unknown",
                    "total_sales": round(m_sales, 2),
                    "total_quantity": round(float(r["total_quantity"] or 0), 2),
                    "total_invoices": int(r["total_invoices"] or 0),
                    "total_parties": int(r["total_parties"] or 0),
                    "contribution_pct": round((m_sales / total_sales) * 100, 2) if total_sales > 0 else 0,
                    "monthly_breakdown": m_breakdown
                })

            # 5. TOP 20 FM (Field Managers)
            cur.execute("""
                SELECT 
                    fm_am as fm_name,
                    SUM(line_amount) as total_sales,
                    COUNT(DISTINCT mpo_code) as active_mpos,
                    COUNT(DISTINCT invoice_no) as total_invoices,
                    COUNT(DISTINCT customer_id) as total_parties
                FROM sales
                WHERE fm_am IS NOT NULL AND fm_am != ''
                GROUP BY fm_am
                ORDER BY SUM(line_amount) DESC
                LIMIT 20
            """)
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
            cur.execute("""
                SELECT 
                    zone as sector_name,
                    SUM(line_amount) as total_sales,
                    COUNT(DISTINCT mpo_code) as active_mpos,
                    COUNT(DISTINCT invoice_no) as total_invoices,
                    COUNT(DISTINCT customer_id) as total_parties
                FROM sales
                WHERE zone IS NOT NULL AND zone != ''
                GROUP BY zone
                ORDER BY SUM(line_amount) DESC
                LIMIT 5
            """)
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
                    WHERE product_code IN ({placeholders})
                """, codes)
                stat_row = cur.fetchone()
                
                # Top 50 MPOs overall sorted by UNIT DESC (Hierarchy by unit)
                cur.execute(f"""
                    SELECT 
                        mpo_code,
                        MAX(market) as market,
                        MAX(zone) as zone,
                        MAX(depot) as depot,
                        SUM(quantity) as units,
                        COUNT(DISTINCT customer_id) as parties,
                        COUNT(DISTINCT invoice_no) as invoices,
                        SUM(line_amount) as sales
                    FROM sales
                    WHERE product_code IN ({placeholders}) AND mpo_code IS NOT NULL AND mpo_code != ''
                    GROUP BY mpo_code
                    ORDER BY SUM(quantity) DESC
                    LIMIT 50
                """, codes)
                
                mpo_list_all = []
                for idx, mr in enumerate(cur.fetchall(), 1):
                    m_code = mr["mpo_code"]
                    
                    cur.execute(f"""
                        SELECT 
                            month,
                            SUM(quantity) as m_units,
                            COUNT(DISTINCT customer_id) as m_parties,
                            COUNT(DISTINCT invoice_no) as m_invoices,
                            SUM(line_amount) as m_sales
                        FROM sales
                        WHERE product_code IN ({placeholders}) AND mpo_code = ?
                        GROUP BY month
                        ORDER BY month ASC
                    """, (*codes, m_code))
                    m_break = []
                    for mb in cur.fetchall():
                        m_break.append({
                            "month": mb["month"],
                            "units": round(float(mb["m_units"] or 0), 2),
                            "parties": int(mb["m_parties"] or 0),
                            "invoices": int(mb["m_invoices"] or 0),
                            "sales": round(float(mb["m_sales"] or 0), 2)
                        })
                        
                    mpo_list_all.append({
                        "rank": idx,
                        "mpo_code": m_code,
                        "market": mr["market"] or mr["zone"] or "Unknown",
                        "zone": mr["zone"] or "Unknown",
                        "depot": mr["depot"] or "Unknown",
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
                            MAX(market) as market,
                            MAX(zone) as zone,
                            MAX(depot) as depot,
                            SUM(quantity) as units,
                            COUNT(DISTINCT customer_id) as parties,
                            COUNT(DISTINCT invoice_no) as invoices,
                            SUM(line_amount) as sales
                        FROM sales
                        WHERE product_code IN ({placeholders}) AND month = ? AND mpo_code IS NOT NULL AND mpo_code != ''
                        GROUP BY mpo_code
                        ORDER BY SUM(quantity) DESC
                        LIMIT 50
                    """, (*codes, m_val))
                    mpo_list_month = []
                    for idx, mr in enumerate(cur.fetchall(), 1):
                        mpo_list_month.append({
                            "rank": idx,
                            "mpo_code": mr["mpo_code"],
                            "market": mr["market"] or mr["zone"] or "Unknown",
                            "zone": mr["zone"] or "Unknown",
                            "depot": mr["depot"] or "Unknown",
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
