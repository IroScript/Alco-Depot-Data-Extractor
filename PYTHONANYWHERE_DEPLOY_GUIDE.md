# PythonAnywhere Deployment Guide — Alco Pharma ERP

This guide walks you through deploying the **two halves** of this project on PythonAnywhere:

| Half | What it does | Hosting type |
|---|---|---|
| **FastAPI Gateway** (`fastapi_gateway/`) | Receives sales uploads, serves metadata, proxies the AI chat | Always-on task / Web service |
| **TOP_FIELD_FORCE Dashboard** (`TOP_FIELD_FORCE/`) | Static HTML/CSS/JS dashboard that reads `data/api_data.json` | Static files via a Web App |

You can run them on a **free PythonAnywhere account** (one Web App + one Always-on task).

---

## 0. Prerequisites

1. A PythonAnywhere account (free tier is enough to start): https://www.pythonanywhere.com/registration/register/beginner/
2. Your local project working (already verified ✅)
3. Your Aiven PostgreSQL connection string (optional — you can also keep using SQLite)

---

## 1. Upload Your Code

You have three options to upload the project. Pick whichever is easiest.

### Option A — ZIP via Files API (fastest)

```bash
# From your project root, locally:
cd "/c/Users/Irak/Desktop/Barishal April Data - Copy/New folder/Alco-Depot-Data-Extractor"
python deploy.py
```

This packages the project into `erp_setup.zip` and pushes it to PythonAnywhere, **if** you have these two lines in your `googleDrive/env`:

```ini
PYTHONANYWHERE_USERNAME=yourusername
PYTHONANYWHERE_API_TOKEN=your-token-from-account-page
```

The token is found at **Account page → API Token → "Create a new API token"**.

### Option B — Manual ZIP upload (recommended if you prefer the GUI)

1. In your terminal: `python deploy.py` (just to create the zip — no API call)
2. PythonAnywhere → **Files** tab → upload `erp_setup.zip` to `/home/yourusername/`
3. Open a **Bash console** from the **Consoles** tab and run:

```bash
cd ~
unzip -o erp_setup.zip
ls -la
```

### Option C — Git (best for ongoing updates)

```bash
cd ~
git clone https://github.com/IroScript/Alco-Depot-Data-Extractor.git
cd Alco-Depot-Data-Extractor
```

Whichever option you choose, ensure the final folder structure on PythonAnywhere is:

```
/home/yourusername/Alco-Depot-Data-Extractor/
├── fastapi_gateway/
│   ├── main.py
│   └── requirements.txt
├── TOP_FIELD_FORCE/
│   ├── index.html
│   ├── server.py          # local-only; for PythonAnywhere use FastAPI
│   ├── data/
│   │   └── api_data.json  # pre-generated cache
│   ├── css/
│   └── js/
├── sales.db               # or replaced with PostgreSQL
├── telegram_bot.py
├── googleDrive/
│   ├── env                # 🔒 contains secrets
│   └── credentials_master.json
├── data_engine.py
├── step_1_extract_Product_Level_Net_Sales_csv.py
├── step_2_generate_MPO_Target_vs_Achievement_report.py
├── step_3_generate_Zone_Wise_Product_Sales_Report.py
├── step_4_analyze_Zone_Wise_Product_Sales_Report.py
└── ... (the rest)
```

---

## 2. Set Up the Python Virtualenv

Open a **Bash console** on PythonAnywhere:

```bash
mkvirtualenv --python=python3.12 alco_env
workon alco_env

cd ~/Alco-Depot-Data-Extractor
pip install -r fastapi_gateway/requirements.txt
pip install gspread google-auth google-api-python-client google-auth-httplib2
# Optional (only if you want Aiven PostgreSQL too):
pip install psycopg2-binary
```

> **Free account note:** `mkvirtualenv` and `workon` work the same on free accounts. The image-based "system image" PythonAnywhere uses already includes Python 3.10–3.12.

---

## 3. Configure Secrets (`googleDrive/env`)

Edit `~/Alco-Depot-Data-Extractor/googleDrive/env` and fill in **only the variables you actually use**:

```ini
# --- FastAPI auth (REQUIRED) ---
API_KEY=alco_secure_api_key_2026

# --- Aiven PostgreSQL (OPTIONAL — leave blank to keep SQLite) ---
DATABASE_URL=

# --- Telegram bot (OPTIONAL — only needed if you run telegram_bot.py) ---
TELEGRAM_BOT_TOKEN=
GROQ_API_KEY=

# --- Cloud sync used by the local pipeline (OPTIONAL) ---
API_GATEWAY_URL=https://yourusername.pythonanywhere.com
```

> **🔒 SECURITY:** `googleDrive/env` is in `.gitignore`. Never commit it.

---

## 4. Deploy the FastAPI Gateway as a Web App

> **Important:** PythonAnywhere's free tier supports Web Apps but **does NOT support Uvicorn/ASGI on free accounts**. For full FastAPI/ASGI support, use an **Always-On Task** (described in step 4B).

You have two deployment paths on free PythonAnywhere. Pick the one that fits:

### 4A. Web App with FastAPI (recommended on paid Hacker plan)

If you have a paid plan with custom ASGI support, the Web App approach is cleanest.

1. PythonAnywhere → **Web** tab → **Add a new web app** → **Manual configuration** → **Python 3.12**
2. Choose **FastAPI** as the framework → **ASGI**
3. Edit the generated WSGI/ASGI file (path will be shown on the Web tab; usually `/var/www/yourusername_pythonanywhere_com_wsgi.py`):
   Replace the entire contents with:

   ```python
   import sys
   import os

   # Adjust this to your project root:
   PROJECT_HOME = '/home/yourusername/Alco-Depot-Data-Extractor'
   if PROJECT_HOME not in sys.path:
       sys.path.insert(0, PROJECT_HOME)

   # Activate the virtualenv
   activate_this = '/home/yourusername/.virtualenvs/alco_env/bin/activate_this.py'
   with open(activate_this) as f:
       exec(f.read(), {'__file__': activate_this})

   os.chdir(PROJECT_HOME)
   from fastapi_gateway.main import app as application
   ```

4. In the **Web** tab → **Virtualenv** section → enter: `/home/yourusername/.virtualenvs/alco_env`
5. Click **Reload** yourusername.pythonanywhere.com
6. Visit `https://yourusername.pythonanywhere.com/` — you should see:

   ```json
   {"status": "running", "service": "Alco Pharma ERP API Gateway (SQLite Mode)"}
   ```

### 4B. Always-On Task (works on FREE plan)

This is the path I'd recommend on the **free tier**.

1. **Don't** create a Web App for the gateway. Instead:
2. PythonAnywhere → **Tasks** tab → **Create a new Always-On Task**
3. Fill in:

   - **Command**:
     ```bash
     workon alco_env && cd ~/Alco-Depot-Data-Extractor && uvicorn fastapi_gateway.main:app --host 0.0.0.0 --port 8080
     ```
   - **Enabled**: ✅

> **Caveat:** Always-On Tasks on free tier run on port `8080` and **are not exposed publicly** by default. If you need a public URL on the free tier, use the **Web App** path (4A) with the WSGI shim — even free accounts can run ASGI FastAPI through the Web tab's WSGI file.

For free-tier public exposure, the supported route is:

1. **Web** tab → **Add a new web app** → **Manual configuration** → **Python 3.12**
2. Choose **Bottle / Flask / Django** as the framework — but pick **Manual config**
3. After it's created, click the blue link to open the WSGI file
4. Replace its contents with:

   ```python
   import sys, os
   PROJECT_HOME = '/home/yourusername/Alco-Depot-Data-Extractor'
   if PROJECT_HOME not in sys.path:
       sys.path.insert(0, PROJECT_HOME)
   activate_this = '/home/yourusername/.virtualenvs/alco_env/bin/activate_this.py'
   with open(activate_this) as f:
       exec(f.read(), {'__file__': activate_this})
   os.chdir(PROJECT_HOME)
   from fastapi_gateway.main import app as application
   ```

5. Save + **Reload** the Web App.

Whichever path you took, after the API is live, verify it with:

```bash
curl -H "x-api-key: alco_secure_api_key_2026" https://yourusername.pythonanywhere.com/sales/metadata
```

You should get a JSON listing 10 depots, 22 zones, 84 FMs.

---

## 5. Deploy the Dashboard as a SECOND Web App

The dashboard is mostly static. You have two options:

### Option A — Static files (simplest)

1. PythonAnywhere → **Web** tab → **Add a new web app** → yourusername **+1** (e.g. `yourusername.static.pythonanywhere.com` is unavailable on free; use the same domain with a subpath)
2. Choose **Manual configuration** → **Python 3.12**
3. Replace the WSGI file with:

   ```python
   import sys, os
   PROJECT_HOME = '/home/yourusername/Alco-Depot-Data-Extractor/TOP_FIELD_FORCE'
   sys.path.insert(0, PROJECT_HOME)
   os.chdir(PROJECT_HOME)
   from server import DashboardHTTPRequestHandler
   from wsgiref.simple_server import WSGIServer, WSGIRequestHandler
   # PythonAnywhere calls this as WSGI; our handler is HTTPServer-only, so use a tiny shim:
   ```

   Actually, the cleanest way: skip the custom WSGI shim and just point PythonAnywhere's static-files feature at the `TOP_FIELD_FORCE/` directory:
   - In the **Web** tab → **Static files** section, add:
     - URL: `/`
     - Directory: `/home/yourusername/Alco-Depot-Data-Extractor/TOP_FIELD_FORCE`
   - **Important:** also add:
     - URL: `/data/`
     - Directory: `/home/yourusername/Alco-Depot-Data-Extractor/TOP_FIELD_FORCE/data`

   Done — your dashboard will now be served at `https://yourusername.pythonanywhere.com/`. The dashboard reads `data/api_data.json` via a synchronous `fetch()` call which works fine on PythonAnywhere.

### Option B — Single domain with both (recommended if your FastAPI gateway is on the same domain)

If your FastAPI Web App is at `yourusername.pythonanywhere.com` and you want the dashboard **on the same domain**:

- In the Web tab → **Static files** section, add `/TOP_FIELD_FORCE/` mapped to the local folder.
- The FastAPI app already exposes `/api/*`-style routes but they don't conflict with the dashboard's static files.

### Refreshing `data/api_data.json`

The dashboard pre-loads the cache `data/api_data.json`. To regenerate it (after running the pipeline locally):

1. SSH/scp the fresh `sales.db` over, **or** sync it from Google Drive (the bot does this on `/reload`).
2. Run on PythonAnywhere (in a Bash console):

   ```bash
   workon alco_env
   cd ~/Alco-Depot-Data-Extractor
   python -c "from TOP_FIELD_FORCE.data_engine import DataEngine; DataEngine().generate_all_data()"
   ```

3. Hard-refresh the dashboard in the browser (Ctrl/Cmd+Shift+R).

---

## 6. Run the Telegram Bot 24/7

Optional but recommended for live Telegram queries.

1. Make sure `TELEGRAM_BOT_TOKEN` is set in `googleDrive/env`.
2. PythonAnywhere → **Tasks** → create a second Always-On task:

   ```bash
   workon alco_env && cd ~/Alco-Depot-Data-Extractor && python telegram_bot.py > ~/bot.log 2>&1
   ```

3. Tail the log to verify:

   ```bash
   tail -f ~/bot.log
   ```

> Free PythonAnywhere allows **one Always-On task**. To run both the API and the bot on a free account, host the API as a **Web App** (step 4A or 4B with public WSGI) and the bot as the **single Always-On task**.

---

## 7. Point Your Local Pipeline at the Live API

Edit your **local** `googleDrive/env`:

```ini
API_GATEWAY_URL=https://yourusername.pythonanywhere.com
API_KEY=alco_secure_api_key_2026
```

Now `auto_single_click_auto_run_no_need__following_steps.py` (and the manual version) will upload finished batches to your **live** API instead of running only locally.

---

## 8. Verify the Full Stack

A quick checklist once everything is live:

```bash
# 1. FastAPI gateway health
curl https://yourusername.pythonanywhere.com/

# 2. Authenticated metadata
curl -H "x-api-key: alco_secure_api_key_2026" https://yourusername.pythonanywhere.com/sales/metadata

# 3. Dashboard renders
# Open https://yourusername.pythonanywhere.com/ in Chrome → should see the dashboard with KPIs

# 4. Telegram bot responds
# Send /help to your bot in Telegram
```

---

## 9. Common Pitfalls on PythonAnywhere

| Pitfall | Fix |
|---|---|
| `ModuleNotFoundError: fastapi` after reload | Web app virtualenv not pointing to `alco_env`. Re-set in Web tab → Virtualenv. |
| Web App shows 500 after editing WSGI file | Check `/var/log/yourusername.pythonanywhere.com.error.log`; usually a path typo. |
| `OutOfMemory` running the dashboard generator | The dashboard generator loads 100k+ rows into pandas — re-run during off-hours or split by month. |
| Bot says `❌ Error downloading sales.db` | Service-account key may have been revoked. Re-share the Drive folder, re-export `credentials_master.json`. |
| `uvicorn` not allowed on free Web App | Use the WSGI shim (the Web App can serve ASGI apps via the WSGI compatibility wrapper) instead of running `uvicorn` directly. |
| `H14` / no response | Your Bash console didn't `cd` into the project dir before launching — the Always-On task runs from `$HOME`. |

---

## 10. Optional: Use Aiven PostgreSQL Instead of SQLite

1. Follow **AIVEN_SETUP.md** (already in your project) to get a free Aiven Postgres URI.
2. Add to `googleDrive/env` on **PythonAnywhere**:
   ```ini
   DATABASE_URL=postgres://avnadmin:xxx@xxx.aivencloud.com:port/defaultdb?sslmode=require
   ```
3. Run once on PythonAnywhere:
   ```bash
   workon alco_env
   cd ~/Alco-Depot-Data-Extractor
   python init_db.py
   ```
4. Reload the Web App. The FastAPI gateway will switch to PostgreSQL automatically.

> **Database location reminder:** the `fastapi_gateway/main.py` shipped in the repo currently uses **SQLite** by default for simplicity (you can confirm by reading the file). If you want it to use Postgres, add a small `if DATABASE_URL:` branch around the `sqlite3.connect(DB_PATH)` call before deploying. A diff is shown in `AIVEN_SETUP.md`.

---

## TL;DR — Quick Start (most common setup)

```bash
# On PythonAnywhere Bash console:

mkvirtualenv --python=python3.12 alco_env
workon alco_env

cd ~
git clone https://github.com/IroScript/Alco-Depot-Data-Extractor.git
cd Alco-Depot-Data-Extractor

pip install -r fastapi_gateway/requirements.txt
pip install gspread google-auth google-api-python-client httpx

# Edit googleDrive/env with your secrets (at minimum API_KEY)

# Then go to the Web tab → Add web app → Manual config → Python 3.12
# Replace the WSGI file with the snippet in step 4B (the free-tier-friendly version).
# Add / and /data/ static-files mappings pointing at TOP_FIELD_FORCE/.

# Then Tasks tab → Always-On task: workon alco_env && cd ~/Alco-Depot-Data-Extractor && python telegram_bot.py
```

After a few minutes you should have:
- Dashboard live at `https://yourusername.pythonanywhere.com`
- FastAPI API at the same URL (paths `/sales/metadata`, `/upload/sales`, `/api/chat`)
- Telegram bot answering queries
