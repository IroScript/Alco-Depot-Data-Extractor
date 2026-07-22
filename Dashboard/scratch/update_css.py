import re

file_path = r'C:\Users\Irak\Desktop\Alco_Depot_Data_Extractor_From_Git\Alco-Depot-Data-Extractor-main\Dashboard\css\style.css'
with open(file_path, 'r', encoding='utf-8') as f:
    css = f.read()

css = css.replace("--font-tech: 'Rajdhani', sans-serif;", "--font-tech: 'JetBrains Mono', monospace;")
css = css.replace("--font-body: 'Outfit', sans-serif;", "--font-body: 'JetBrains Mono', monospace;")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(css)

file_path2 = r'C:\Users\Irak\Desktop\Alco_Depot_Data_Extractor_From_Git\Alco-Depot-Data-Extractor-main\Dashboard\index.html'
with open(file_path2, 'r', encoding='utf-8') as f:
    html = f.read()

html = html.replace('<body class="min-h-screen bg-quantum-void bg-grid-pattern relative selection:bg-cyan-500 selection:text-black">', '<body class="min-h-screen bg-quantum-void bg-grid-pattern relative selection:bg-cyan-500 selection:text-black font-thin">')

with open(file_path2, 'w', encoding='utf-8') as f:
    f.write(html)

print("done css and html")
