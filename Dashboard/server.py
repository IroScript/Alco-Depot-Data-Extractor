import os
import sys
import json
import sqlite3
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from data_engine import DataEngine, DATA_OUT_DIR

# Reconfigure console output encoding to prevent Windows crash on non-ASCII characters
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
    except:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
API_DATA_PATH = os.path.join(DATA_OUT_DIR, "api_data.json")

class DashboardHTTPRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        # CORS headers support for API calling
        if path.startswith("/api/"):
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
            self.end_headers()

            data = self.get_api_data()
            
            if path == "/api/all-dashboard-data":
                response_data = data
            elif path == "/api/kpis":
                response_data = {"kpis": data.get("kpis", {}), "meta": data.get("meta", {})}
            elif path == "/api/top-50-products":
                response_data = {"top_50_products": data.get("top_50_products", [])}
            elif path == "/api/top-5-products-deep":
                response_data = {"top_5_products_deep": data.get("top_5_products_deep", [])}
            elif path == "/api/top-50-mpos":
                response_data = {"top_50_mpos": data.get("top_50_mpos", [])}
            elif path == "/api/top-20-fms":
                response_data = {"top_20_fms": data.get("top_20_fms", [])}
            elif path == "/api/top-5-sectors":
                response_data = {"top_5_sector_heads": data.get("top_5_sector_heads", [])}
            elif path == "/api/monthly-trends":
                response_data = {"monthly_trends": data.get("monthly_trends", [])}
            elif path == "/api/refresh":
                # Force recalculation from database
                engine = DataEngine()
                response_data = engine.generate_all_data()
            else:
                response_data = {"error": "API endpoint not found", "available_endpoints": [
                    "/api/all-dashboard-data", "/api/kpis", "/api/top-50-products", 
                    "/api/top-50-mpos", "/api/top-20-fms", "/api/top-5-sectors", 
                    "/api/monthly-trends", "/api/refresh"
                ]}

            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode("utf-8"))
            return

        # Fallback to serving static files (index.html, css, js)
        try:
            return super().do_GET()
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError) as e:
            print(f"ℹ️ [Info] Client connection closed prematurely: {e}")
            return

    def get_api_data(self):
        if os.path.exists(API_DATA_PATH):
            try:
                with open(API_DATA_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error reading JSON cache: {e}")
        # If cache is missing, generate on the fly
        engine = DataEngine()
        return engine.generate_all_data()

def run(port=8080):
    server_address = ('', port)
    httpd = HTTPServer(server_address, DashboardHTTPRequestHandler)
    print("="*80)
    print(f" 🚀 TOP FIELD FORCE DASHBOARD SERVER RUNNING AT: http://127.0.0.1:{port}")
    print("="*80)
    print(" Available API endpoints for PythonAnywhere / Django / Frontend:")
    print(f"   -> http://127.0.0.1:{port}/api/all-dashboard-data")
    print(f"   -> http://127.0.0.1:{port}/api/top-50-products (Always anchored on Product Code)")
    print(f"   -> http://127.0.0.1:{port}/api/top-50-mpos")
    print(f"   -> http://127.0.0.1:{port}/api/top-20-fms")
    print(f"   -> http://127.0.0.1:{port}/api/top-5-sectors")
    print("="*80)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer shutting down...")
        httpd.server_close()

if __name__ == '__main__':
    run()
