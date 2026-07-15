# -*- coding: utf-8 -*-
"""
================================================================================
 PythonAnywhere WSGI Configuration — storealco.pythonanywhere.com
================================================================================
  Username:        storealco
  Project home:    /home/storealco/
  FastAPI module:  /home/storealco/fastapi_gateway/main.py
  Virtualenv:      /home/storealco/.virtualenvs/erp_env

  এই ফাইলটি এখানে বসান:
    /var/www/storealco_pythonanywhere_com_wsgi.py
================================================================================
"""

import sys
import os

# ───────────────────────────────────────────────────────────────────────────────
# ১. PROJECT PATHS
# ───────────────────────────────────────────────────────────────────────────────
PROJECT_HOME = '/home/storealco'
FASTAPI_DIR = os.path.join(PROJECT_HOME, 'fastapi_gateway')

# sys.path তে যোগ করা (FastAPI + telegram_bot দুটোই import হতে পারে)
for p in (PROJECT_HOME, FASTAPI_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

# working directory সেট করা (sales.db খুঁজতে)
os.chdir(PROJECT_HOME)


# ───────────────────────────────────────────────────────────────────────────────
# ২. VIRTUALENV ACTIVATE
# ───────────────────────────────────────────────────────────────────────────────
# আপনার venv এর নাম erp_env। যদি অন্য নামে থাকে, নিচের PATH বদলান।
VENV_CANDIDATES = [
    '/home/storealco/.virtualenvs/erp_env',
    '/home/storealco/.virtualenvs/alco_env',
]

activated = False
for venv in VENV_CANDIDATES:
    activate_this = os.path.join(venv, 'bin', 'activate_this.py')
    if os.path.exists(activate_this):
        try:
            with open(activate_this) as f:
                exec(f.read(), {'__file__': activate_this})
            sys.stderr.write(f"\n[OK] Virtualenv activated: {venv}\n")
            activated = True
            break
        except Exception as e:
            sys.stderr.write(f"\n[!] venv activate failed ({venv}): {e}\n")

if not activated:
    sys.stderr.write(
        "\n[!] কোনো virtualenv পাওয়া যায়নি। নিচের path গুলো চেক করুন:\n"
        + "\n".join(f"    {v}/bin/python" for v in VENV_CANDIDATES)
        + "\n    আসল নাম জানতে Bash console এ:  ls /home/storealco/.virtualenvs/\n"
    )


# ───────────────────────────────────────────────────────────────────────────────
# ৩. SECRET FILE খোঁজা (env vs env_erp)
# ───────────────────────────────────────────────────────────────────────────────
# fastapi_gateway/main.py শুধু 'env' নামের ফাইল খোঁজে।
# তাই নিশ্চিত করি যে 'env' নামে একটা ফাইল আছে — না থাকলে env_erp থেকে symlink।

ENV_CANDIDATES = [
    os.path.join(PROJECT_HOME, 'googleDrive', 'env'),
    os.path.join(PROJECT_HOME, 'googleDrive', 'env_erp'),
    os.path.join(FASTAPI_DIR, 'googleDrive', 'env'),
    os.path.join(FASTAPI_DIR, 'googleDrive', 'env_erp'),
]

canonical_env = ENV_CANDIDATES[0]  # /home/storealco/googleDrive/env
canonical_exists = os.path.exists(canonical_env)

if not canonical_exists:
    # খুঁজে দেখি অন্য কোথাও আছে কিনা
    for candidate in ENV_CANDIDATES[1:]:
        if os.path.exists(candidate):
            try:
                import shutil
                os.makedirs(os.path.dirname(canonical_env), exist_ok=True)
                shutil.copy2(candidate, canonical_env)
                sys.stderr.write(
                    f"\n[OK] Copied {candidate} → {canonical_env}\n"
                    f"     (পরে আপনি সরাসরি {canonical_env} ব্যবহার করতে পারবেন)\n"
                )
                canonical_exists = True
            except Exception as e:
                sys.stderr.write(f"\n[!] Could not copy env file: {e}\n")
            break

if not canonical_exists:
    sys.stderr.write(
        "\n[!] googleDrive/env পাওয়া যায়নি। API_KEY কাজ করবে না।\n"
        f"    এই path এ একটা env ফাইল তৈরি করুন:\n"
        f"      {canonical_env}\n"
        f"    ভেতরে লিখুন:\n"
        f"      API_KEY=alco_secure_api_key_2026\n"
    )


# ───────────────────────────────────────────────────────────────────────────────
# ৪. DATABASE যাচাই
# ───────────────────────────────────────────────────────────────────────────────
DB_PATH = os.path.join(PROJECT_HOME, 'sales.db')
if not os.path.exists(DB_PATH):
    sys.stderr.write(
        f"\n[!] sales.db পাওয়া যায়নি: {DB_PATH}\n"
        f"    Files ট্যাব থেকে sales.db আপলোড করুন অথবা\n"
        f"    Telegram bot-এ /reload দিন (Drive থেকে sync হবে)।\n"
    )
else:
    sys.stderr.write(f"\n[OK] sales.db পাওয়া গেছে ({os.path.getsize(DB_PATH)/1024/1024:.1f} MB)\n")


# ───────────────────────────────────────────────────────────────────────────────
# ৫. FASTAPI APP LOAD
# ───────────────────────────────────────────────────────────────────────────────
try:
    from fastapi_gateway.main import app
    try:
        from a2wsgi import ASGIMiddleware
        application = ASGIMiddleware(app)
        sys.stderr.write("\n[OK] FastAPI app loaded successfully via a2wsgi ASGIMiddleware.\n")
    except ImportError:
        from asgiref.wsgi import WsgiToAsgi
        application = WsgiToAsgi(app)
        sys.stderr.write("\n[OK] FastAPI app loaded successfully via WsgiToAsgi (Warning: may need a2wsgi).\n")
except Exception as e:
    sys.stderr.write(f"\n[!] FastAPI app load failed: {type(e).__name__}: {e}\n")
    # আবার চেষ্টা: সরাসরি fastapi_gateway/main.py
    try:
        sys.path.insert(0, FASTAPI_DIR)
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "main", os.path.join(FASTAPI_DIR, "main.py")
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        try:
            from a2wsgi import ASGIMiddleware
            application = ASGIMiddleware(mod.app)
            sys.stderr.write("[OK] FastAPI app loaded via fallback (a2wsgi ASGIMiddleware).\n")
        except ImportError:
            from asgiref.wsgi import WsgiToAsgi
            application = WsgiToAsgi(mod.app)
            sys.stderr.write("[OK] FastAPI app loaded via fallback (WsgiToAsgi).\n")
    except Exception as e2:
        sys.stderr.write(f"[!] Fallback also failed: {type(e2).__name__}: {e2}\n")
        raise