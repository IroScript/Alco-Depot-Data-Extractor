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

class DataEngine:
    def __init__(self, db_path=DEFAULT_DB_PATH):
        self.db_path = db_path
        if not os.path.exists(self.db_path):
            print(f"Warning: Database not found at {self.db_path}")

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def generate_all_data(self):
        """
        Executes all SQL calculations emphasizing PRODUCT CODE as primary identifier
        and user-defined Top 50 product calculation & field force metrics.
        """
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        data = {
            "meta": {
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "db_path": self.db_path,
                "note": "Product calculations are strictly anchored on product_code as per system rules."
            },
            "kpis": {},
            "top_50_products": [],
            "top_5_products_deep": [],
            "top_50_mpos": [],
            "top_20_fms": [],
            "top_5_sector_heads": [],
            "monthly_trends": []
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

            # 3. TOP 50 PRODUCTS CALCULATION (Strictly grouped by product_code)
            cur.execute("""
                SELECT 
                    product_code,
                    MAX(product_name) as product_name,
                    SUM(line_amount) as total_sales,
                    SUM(quantity) as total_quantity,
                    COUNT(DISTINCT invoice_no) as total_invoices,
                    COUNT(DISTINCT customer_id) as total_parties
                FROM sales
                GROUP BY product_code
                ORDER BY SUM(line_amount) DESC
                LIMIT 50
            """)
            top_50_prod_rows = cur.fetchall()
            
            # For each top product, calculate month-wise breakdown (sales, invoices, party count)
            for idx, r in enumerate(top_50_prod_rows, 1):
                p_code = r["product_code"]
                p_sales = float(r["total_sales"] or 0)
                
                # Month-wise drill for this product_code
                cur.execute("""
                    SELECT 
                        month,
                        SUM(line_amount) as m_sales,
                        SUM(quantity) as m_qty,
                        COUNT(DISTINCT invoice_no) as m_invoices,
                        COUNT(DISTINCT customer_id) as m_parties
                    FROM sales
                    WHERE product_code = ?
                    GROUP BY month
                    ORDER BY month ASC
                """, (p_code,))
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
                    "product_code": p_code,
                    "product_name": r["product_name"] or f"Product {p_code}",
                    "total_sales": round(p_sales, 2),
                    "total_quantity": round(float(r["total_quantity"] or 0), 2),
                    "total_invoices": int(r["total_invoices"] or 0),
                    "total_parties": int(r["total_parties"] or 0),
                    "contribution_pct": round((p_sales / total_sales) * 100, 2) if total_sales > 0 else 0,
                    "monthly_breakdown": m_breakdown
                }
                data["top_50_products"].append(prod_item)
                if idx <= 5:
                    data["top_5_products_deep"].append(prod_item)

            # 4. TOP 50 MPO CALCULATION (With month-wise party and invoice visits as requested)
            cur.execute("""
                SELECT 
                    mpo_code,
                    MAX(zone) as zone,
                    MAX(depot) as depot,
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
                
                # Month-wise drill for this MPO
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
