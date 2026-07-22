import re

js_path = r'C:\Users\Irak\Desktop\Alco_Depot_Data_Extractor_From_Git\Alco-Depot-Data-Extractor-main\Dashboard\js\script.js'
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# For FM:
target_fm = '''<span class="text-emerald-400 font-mono font-bold">📦  U</span>
                        <span>👥  Parties</span>
                        <span>🧾  Inv</span>'''
repl_fm = '''<span class="strat-val-units text-emerald-400 font-mono font-bold">📦  U</span>
                        <span class="strat-val-parties">👥  Parties</span>
                        <span class="strat-val-invoices">🧾  Inv</span>'''

js = js.replace(target_fm, repl_fm)

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)
