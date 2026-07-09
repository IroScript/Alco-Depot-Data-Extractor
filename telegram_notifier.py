import os
import sys
import requests
import json

# Reconfigure console output encoding to prevent Windows crash on non-ASCII characters
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
    except:
        pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Telegram credentials now live in googleDrive/credentials_master.json.
from googleDrive.credentials_loader import get_env_var

# ── SAMPLE DATA FOR FIRST WEEK OF MAY (EXCEPTION REPORT) ──
SAMPLE_REPORT_TEXT = """🚨 *ALCO PHARMA LTD. - SALES EXCEPTION REPORT* 🚨
=========================================
📅 *Period:* May 1 – May 7, 2026 (First Week of May)
🏢 *Depot:* BARISHAL (BARI Zone)
👤 *Field Manager (FM):* RIPAN KUMAR HALDER
💊 *Monitored Brands:* ALAGRA & MOKAST

This report highlights MPOs under FM RIPAN KUMAR HALDER who had *ZERO* or *VERY POOR* sales for ALAGRA and MOKAST products in the first week of May.

-----------------------------------------
📊 *MPO SALES EXCEPTION DETAILS:*
-----------------------------------------

1️⃣ *MPO Code:* B001
   👤 *Name:* RAFIQUL ISLAM (Barishal Sadar)
   ▪️ *ALAGRA:* 0 Tab Sold (❌ ZERO SALE)
   ▪️ *MOKAST:* 5 Tab Sold (⚠️ Poor Sale - Target: 100 Tab)

2️⃣ *MPO Code:* B002
   👤 *Name:* MISS. MIRZAHAN SABINA (Barishal Sadar-2)
   ▪️ *ALAGRA:* 0 Tab Sold (❌ ZERO SALE)
   ▪️ *MOKAST:* 0 Tab Sold (❌ ZERO SALE)

3️⃣ *MPO Code:* B004
   👤 *Name:* HAMIDUR RAHMAN (Babuganj)
   ▪️ *ALAGRA:* 12 Tab Sold (⚠️ Poor Sale - Target: 80 Tab)
   ▪️ *MOKAST:* 0 Tab Sold (❌ ZERO SALE)

4️⃣ *MPO Code:* B006
   👤 *Name:* VACANT (Wazirpur)
   ▪️ *ALAGRA:* 0 Tab Sold (❌ ZERO SALE)
   ▪️ *MOKAST:* 0 Tab Sold (❌ ZERO SALE)

5️⃣ *MPO Code:* B008
   👤 *Name:* VACANT (Banaripara)
   ▪️ *ALAGRA:* 0 Tab Sold (❌ ZERO SALE)
   ▪️ *MOKAST:* 0 Tab Sold (❌ ZERO SALE)

=========================================
📈 *SUMMARY:*
Out of 9 markets under FM RIPAN KUMAR HALDER, *5 markets* had critical sales exceptions. 
- *ALAGRA:* Zero sales in 4 markets.
- *MOKAST:* Zero sales in 4 markets.
⚠️ *Immediate field visit and recovery action is required.*
=========================================
"""

def load_env_variables(env_path):
    env = {}
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        env[parts[0].strip()] = parts[1].strip()
    return env

def send_telegram_message(bot_token, chat_id, message_text):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message_text,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
        return True, response.json()
    except Exception as e:
        return False, str(e)

def main():
    print("=" * 60)
    print("  TELEGRAM SALES NOTIFICATION UTILITY")
    print("=" * 60)

    bot_token = get_env_var("TELEGRAM_BOT_TOKEN")
    chat_id = get_env_var("TELEGRAM_CHAT_ID")

    print("\n--- [PREPARED SAMPLE REPORT TEXT] ---")
    print(SAMPLE_REPORT_TEXT)
    print("--------------------------------------\n")

    if not bot_token or not chat_id:
        print("STATUS: Telegram credentials not set in googleDrive/credentials_master.json (env_file_content).")
        print("Please add the following keys to the env_file_content section of credentials_master.json:")
        print("\n  TELEGRAM_BOT_TOKEN=your_bot_token_here")
        print("  TELEGRAM_CHAT_ID=your_chat_id_here")
        print("\nOnce you supply these credentials, run this script again to test sending the message.")
    else:
        print(f"✓ Credentials detected in env file:")
        print(f"  Bot Token: {bot_token[:10]}...{bot_token[-5:] if len(bot_token) > 15 else ''}")
        print(f"  Chat ID: {chat_id}")
        
        print("\nSending sample report to Telegram...")
        success, response = send_telegram_message(bot_token, chat_id, SAMPLE_REPORT_TEXT)
        if success:
            print("✓ [SUCCESS] Message sent successfully to Telegram!")
        else:
            print(f"❌ [ERROR] Failed to send message: {response}")

if __name__ == "__main__":
    main()
