import re

file_path = r'C:\Users\Irak\Desktop\Alco_Depot_Data_Extractor_From_Git\Alco-Depot-Data-Extractor-main\Dashboard\js\script.js'
with open(file_path, 'r', encoding='utf-8') as f:
    js = f.read()

# Remove font-bold inside paginatedMpos
js = js.replace('font-mono text-center font-bold', 'font-mono text-center')
js = js.replace('<strong class="text-white font-bold text-base">', '<span class="text-white text-base">')
js = js.replace('<strong class="text-cyan-300 font-bold text-base uppercase tracking-wider">', '<span class="text-cyan-300 text-base uppercase tracking-wider">')
js = js.replace('<strong class="font-cyber text-cyan-300 text-base">', '<span class="font-cyber text-cyan-300 text-base">')
js = js.replace('</strong>', '</span>')
js = js.replace('<td class="font-mono text-purple-300 font-bold">', '<td class="font-mono text-purple-300">')
js = js.replace('<td><span class="text-slate-300 font-tech font-bold">', '<td><span class="text-slate-300 font-tech">')
js = js.replace('<strong class="text-white text-base font-bold">', '<span class="text-white text-base">')
js = js.replace('<strong class="text-white font-bold text-sm bg-purple-950/60 px-2.5 py-1 rounded border border-purple-500/30">', '<span class="text-white text-sm bg-purple-950/60 px-2.5 py-1 rounded border border-purple-500/30">')

# Also check for simple <strong></strong>
js = js.replace('<td><strong></strong>', '<td><span></span>')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(js)
print("done removing bold")
