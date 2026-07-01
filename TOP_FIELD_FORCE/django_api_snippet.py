"""
=============================================================================
  DJANGO & PYTHONANYWHERE DEPLOYMENT INTEGRATION GUIDE
=============================================================================
If you want to host this dashboard inside a Django application or on 
PythonAnywhere, you can easily integrate this API engine using the code below.
=============================================================================
"""

# ---------------------------------------------------------------------------
# OPTION 1: DJANGO INTEGRATION (views.py)
# ---------------------------------------------------------------------------
"""
# In your Django app's views.py:

import os
import json
from django.http import JsonResponse
from django.shortcuts import render
from .data_engine import DataEngine, DATA_OUT_DIR

def dashboard_view(request):
    # Render the index.html template
    return render(request, "top_field_force/index.html")

def api_all_dashboard_data(request):
    cache_path = os.path.join(DATA_OUT_DIR, "api_data.json")
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return JsonResponse(data, safe=False)
    
    # Generate live from SQLite/PostgreSQL if cache missing
    engine = DataEngine()
    data = engine.generate_all_data()
    return JsonResponse(data, safe=False)

def api_top_50_products(request):
    engine = DataEngine()
    data = engine.generate_all_data()
    return JsonResponse({"top_50_products": data.get("top_50_products", [])}, safe=False)
"""

# ---------------------------------------------------------------------------
# OPTION 2: PYTHONANYWHERE WSGI CONFIGURATION (/var/www/your_app_wsgi.py)
# ---------------------------------------------------------------------------
"""
# If using PythonAnywhere standalone WSGI without Django:

import sys
import os

path = '/home/yourusername/Barishal April Data/TOP_FIELD_FORCE'
if path not in sys.path:
    sys.path.append(path)

from server import DashboardHTTPRequestHandler
from wsgiref.simple_server import make_server

# You can wrap the server or use FastAPI/Flask as needed.
"""
