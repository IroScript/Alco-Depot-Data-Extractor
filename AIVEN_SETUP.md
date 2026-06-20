# Aiven PostgreSQL & FastAPI Gateway Cloud Setup Guide

This guide describes how to configure your lifetime-free **Aiven PostgreSQL** database, run the database initialization script, deploy the **FastAPI gateway** to Render or PythonAnywhere, and sync your sales data securely to the cloud.

---

## 1. Set Up Aiven PostgreSQL (Free Tier)

Aiven offers a free tier for PostgreSQL that includes up to **5 GB of storage**, which is more than enough for your sales transaction histories.

1. **Sign Up**: Go to [aiven.io](https://aiven.io/) and create an account.
2. **Create Project**: Name your project (e.g., `alco-pharma-erp`).
3. **Create Service**:
   - Choose **PostgreSQL** as the database service.
   - Select the cloud provider (Google Cloud or AWS) and a region close to your target users (e.g., Singapore `asia-southeast1`).
   - Select the **Free Plan** (Hobbies/Projects) tier.
   - Click **Create Service**.
4. **Get Connection String**:
   - Once the service is running (takes 2–3 minutes), find the **Service URI**.
   - It will look like: `postgres://avnadmin:password@host-name.aivencloud.com:port/defaultdb?sslmode=require`
   - Copy this URL.

---

## 2. Update Configuration Locally

Open the file `googleDrive/env` inside your project directory and add the `DATABASE_URL` variable:

```ini
# Add your Aiven PostgreSQL Connection URL here
DATABASE_URL=postgres://avnadmin:your_aiven_password@your_aiven_host.aivencloud.com:your_port/defaultdb?sslmode=require
```

> [!NOTE]
> Keep the rest of your variables (e.g. `GROQ_API_KEY`, `TELEGRAM_BOT_TOKEN`, etc.) unchanged.

---

## 3. Initialize the Database Schema

To create the `sales` table, composite unique constraints, and indexes on your Aiven PostgreSQL cloud database, run the initialization script locally:

```powershell
python init_db.py
```

*This will connect to Aiven, build the schema, and print `✓ Table 'sales' created.` when successful.*

---

## 4. Deploy the FastAPI Gateway (Secure Intermediary)

To host your FastAPI gateway for free, use **Render** or **PythonAnywhere**. Render is recommended for its native support of Docker/Python and simple GitHub integrations.

### Option A: Deploying on Render (Recommended)

1. **Push Code to GitHub**: Ensure the `fastapi_gateway/` folder is pushed to your GitHub repository.
2. **Create Render Web Service**:
   - Go to [render.com](https://render.com/) and sign up.
   - Click **New +** and select **Web Service**.
   - Connect your GitHub repository.
3. **Configure Service Details**:
   - **Name**: `alco-pharma-api`
   - **Region**: Same as Aiven DB (e.g., Singapore or US East).
   - **Runtime**: `Python 3` (or Docker).
   - **Root Directory**: `fastapi_gateway` (Optional, or leave empty if the build command specifies path).
   - **Build Command**: `pip install -r requirements.txt` (or `pip install -r fastapi_gateway/requirements.txt` depending on root path setting).
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000` (or `uvicorn fastapi_gateway.main:app --host 0.0.0.0 --port 10000`).
4. **Configure Environment Variables**:
   Under the **Environment** tab on Render, add these variables:
   - `DATABASE_URL`: *Your Aiven PostgreSQL Connection URI*
   - `API_KEY`: `alco_secure_api_key_2026` *(Keep this secure. This key authenticates requests from your pipeline and Telegram bot)*
5. **Deploy**: Click **Deploy Web Service**. Render will build and host your API at a public URL like `https://alco-pharma-api.onrender.com`.

---

## 5. Enable Cloud Sync in Your Pipeline

Once the FastAPI app is deployed, you want your daily scripts (`auto_single_click_...` or `manual_single_click_...`) to upload data directly to this API.

Open your local `googleDrive/env` file and add the API details:

```ini
# Add your deployed FastAPI Gateway URL
API_GATEWAY_URL=https://alco-pharma-api.onrender.com
API_KEY=alco_secure_api_key_2026
```

Now, every time you or the pipeline runs a data extractor:
1. It combines and processes the sales data.
2. It sends batches of data (UPSERT format) directly to Aiven PostgreSQL via the FastAPI endpoint.
3. If the server is offline or config is missing, it automatically falls back to generating a local SQLite database (`sales.db`) and uploading it to Google Drive via `rclone`.

---

## 6. Run your Telegram Bot in the Cloud

You can run `telegram_bot.py` 24/7 on Render (as a Background Worker) or PythonAnywhere:
1. Make sure `DATABASE_URL` is configured in the environment variables of your bot hosting environment.
2. If `DATABASE_URL` is set, the bot will query your Aiven PostgreSQL database directly with sub-millisecond responses.
3. If `DATABASE_URL` is empty, the bot automatically downloads the SQLite database `sales.db` from your Google Drive on startup or when the `/reload` admin command is triggered.
