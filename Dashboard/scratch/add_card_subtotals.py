import re

js_path = r'C:\Users\Irak\Desktop\Alco_Depot_Data_Extractor_From_Git\Alco-Depot-Data-Extractor-main\Dashboard\js\script.js'
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# 1. Add IDs to the spans in renderStrategic6Products() for MPO, FM, and SH.
# We need to find the HTML generation for each section.

# MPO HTML
mpo_old = '''<span class="text-emerald-400 font-mono font-bold">📦  U</span>
                    <span>👥  Parties</span>
                    <span>🧾  Inv</span>'''
mpo_new = '''const safeId = prodName.replace(/[^a-zA-Z0-9]/g, '-');
        return 
            <button class="strat-btn p-3 rounded-xl border text-left transition-all duration-300 min-w-[200px] max-w-[220px] flex-shrink-0 snap-start " onclick="selectStrategicProduct('')">
                <div class="font-cyber font-bold text-sm text-white truncate mb-2 flex items-center justify-between" title="">
                    <span class="truncate"> </span>
                </div>
                <div class="flex items-center justify-between text-[10px] font-tech text-slate-400 border-t border-slate-800/80 pt-1.5 mt-1.5 gap-1.5">
                    <span id="card-mpo-units-" class="text-emerald-400 font-mono font-bold">📦  U</span>
                    <span id="card-mpo-parties-">👥  Parties</span>
                    <span id="card-mpo-invoices-">🧾  Inv</span>
                </div>
            </button>
        ;'''
# We can't safely replace just the spans because prodName is needed for the ID, and we are inside the template literal.
# Let's replace the whole return statement for MPO.
js = re.sub(r'return \s*<button class="strat-btn p-3 rounded-xl border text-left transition-all duration-300 min-w-\[200px\] max-w-\[220px\] flex-shrink-0 snap-start \$\{isActive \? \'active shadow-neon-cyan\' : \'bg-cyan-950/60 border-cyan-800 hover:border-cyan-500/50\'\}" onclick="selectStrategicProduct\(\'\$\{prodName.replace\(\/\'\/g, "\\\\\\\'"\)\}\'\)">[\s\S]*?<\/button>\s*;', mpo_new.replace('\\\\', '\\\\\\\\'), js) # Ugh escaping regex is hard.

# Let's write a JS snippet that appends the update function instead.
