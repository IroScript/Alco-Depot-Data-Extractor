import re

file_path = r'C:\Users\Irak\Desktop\Alco_Depot_Data_Extractor_From_Git\Alco-Depot-Data-Extractor-main\Dashboard\js\script.js'
with open(file_path, 'r', encoding='utf-8') as f:
    js = f.read()

# Fix mismatched strong and span tags
js = js.replace('<td><strong class="font-cyber text-amber-400">#</span></td>', '<td><span class="font-cyber text-amber-400">#</span></td>')
js = js.replace('<td><strong class="font-cyber text-emerald-400">#</span></td>', '<td><span class="font-cyber text-emerald-400">#</span></td>')
js = js.replace('<td><strong class="font-cyber text-cyan-300"></span></td>', '<td><span class="font-cyber text-cyan-300"></span></td>')
js = js.replace('<td><strong></span> </td>', '<td><span></span> </td>')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(js)
print("fixed tags")
