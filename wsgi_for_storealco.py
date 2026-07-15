# -*- coding: utf-8 -*-
"""
PythonAnywhere WSGI configuration for storealco
================================================
আপনার ডোমেইন:  storealco.pythonanywhere.com
হোম ডিরেক্টরি:  /home/storealco/
ফাস্টএপিআই পাথ: /home/storealco/fastapi_gateway/main.py

এই ফাইলটি /var/www/storealco_pythonanywhere_com_wsgi.py তে কপি করুন।
"""

import sys
import os

# -----------------------------------------------------------------
# ১. আপনার প্রজেক্টের home এবং fastapi_gateway ফোল্ডার sys.path তে যোগ করা
# -----------------------------------------------------------------
PROJECT_HOME = '/home/storealco'
FASTAPI_DIR = os.path.join(PROJECT_HOME, 'fastapi_gateway')

# দুটো path যোগ করা — যাতে telegram_bot.py ইমপোর্ট করতে পারে
for p in (PROJECT_HOME, FASTAPI_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

# -----------------------------------------------------------------
# ২. ভার্চুয়াল এনভায়রনমেন্ট সক্রিয় করা (FastAPI, pydantic, uvicorn লোড হবে)
# -----------------------------------------------------------------
VENV_PATH = '/home/storealco/.virtualenvs/alco_env'

# PythonAnywhere-এর activate_this.py ফাইলটি রান করে venv activate হয়
activate_this = os.path.join(VENV_PATH, 'bin', 'activate_this.py')
if os.path.exists(activate_this):
    with open(activate_this) as f:
        exec(f.read(), {'__file__': activate_this})
else:
    # যদি venv "alco_env" না হয়ে অন্য নামে থাকে, তাহলে এখানে error দেখাবে
    sys.stderr.write(
        f"\n[!] ভার্চুয়াল এনভায়রনমেন্ট পাওয়া যায়নি: {VENV_PATH}\n"
        f"    আপনার venv লিস্ট দেখতে Bash console এ:  workon\n"
    )

# -----------------------------------------------------------------
# ৩. working directory সেট করা (DB ফাইল খুঁজে পেতে)
# -----------------------------------------------------------------
os.chdir(PROJECT_HOME)

# -----------------------------------------------------------------
# ৪. FastAPI অ্যাপ লোড করা
# -----------------------------------------------------------------
try:
    from fastapi_gateway.main import app
    class WSGIWrapper:
        def __init__(self, asgi_app):
            self.asgi_app = asgi_app
        def __call__(self, environ, start_response):
            # A tiny synchronous WSGI adapter for FastAPI apps that do simple routing.
            # However, since ASGI-WSGI conversion is complex, we can use a2wsgi if available,
            # or try using the raw WSGIMiddleware wrapper in a cleaner format.
            # Let's import it safely.
            try:
                from a2wsgi import ASGIMiddleware
                return ASGIMiddleware(self.asgi_app)(environ, start_response)
            except ImportError:
                # Fallback to simple compatibility
                from asgiref.wsgi import WsgiToAsgi
                # Note: WSGI servers expect a WSGI app. On PythonAnywhere, ASGI can also be served using a2wsgi.
                # Let's define fallback.
                raise ImportError("Please run: pip install a2wsgi")
    application = WSGIWrapper(app)
except Exception as e:
    # কোনো ইমপোর্ট ত্রুটি হলে Web → Error log এ দেখা যাবে
    sys.stderr.write(f"\n[!] FastAPI app load failed: {e}\n")
    raise
