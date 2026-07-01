# ⚡ Alco Pharma - Top Field Force & Product Analytics Dashboard

Welcome to the **Top Field Force & Product Analytics Dashboard**, custom-built for Alco Pharma. This system provides state-of-the-art analytical reporting anchored strictly on **unique Product Code (`product_code`)** and user-defined top calculations.

---

## 🌟 Key Architectural Rules Implemented

1. **Strict Product Code Anchor (`product_code`)**:
   - In accordance with system rules, all product-level aggregations (net sales, invoice frequency, party coverage, and monthly trajectories) are strictly grouped and evaluated by `product_code`.
2. **Top 50 Product & Field Force Analytics**:
   - Computes month-wise (Jan - Jun 2026) billing frequency, unique visited parties (`customer_id`), and net sales for the **Top 50 Products**, **Top 50 MPOs**, **Top 20 FMs**, and **Top 5 Sector Heads / Zones**.
3. **Dual Mode Operation (Live API + Static Offline Fallback)**:
   - When connected to a live Python backend (`server.py`, Django, or PythonAnywhere), it queries the database dynamically.
   - If opened directly as a static file (`index.html`), it automatically loads from `data/api_data.json` without throwing errors!

---

## 🚀 How to Run Locally

### Method 1: Instant Python Server (Recommended)
Open your terminal inside this folder (`TOP_FIELD_FORCE`) and run:
```powershell
py -3.12 server.py
```
Then open your browser and go to: **http://127.0.0.1:8080**

### Method 2: Direct Static File View
Simply double-click `index.html` to open it in Google Chrome or Edge. It will seamlessly load the pre-computed snapshot from `data/api_data.json`.

---

## 🌐 Deploying to PythonAnywhere / Django

If you wish to host this dashboard on PythonAnywhere or inside a Django project:
1. **Django Integration**: Check `django_api_snippet.py` for copy-paste view functions and template rendering code.
2. **PythonAnywhere Deployment**:
   - Upload the `TOP_FIELD_FORCE` folder to your PythonAnywhere account.
   - Point your Web App WSGI or FastAPI router to read `data/api_data.json` or connect to `sales.db` using the exact queries in `data_engine.py`.

---

## 📊 Available REST API Endpoints

When running `server.py` or integrated into your gateway:
* `GET /api/all-dashboard-data` - Full system analytics payload
* `GET /api/top-50-products` - Top 50 products grouped by `product_code` with monthly breakdown
* `GET /api/top-50-mpos` - Top 50 MPO leaderboard with monthly party visits & invoices
* `GET /api/top-20-fms` - Top 20 Field Managers
* `GET /api/top-5-sectors` - Top 5 Sector Heads / Zones
* `GET /api/monthly-trends` - Month-wise system trajectory
* `GET /api/refresh` - Re-execute SQL queries against `sales.db` and update cache
