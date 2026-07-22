import re

# Update index.html to include Roboto Condensed
file_path_html = r'C:\Users\Irak\Desktop\Alco_Depot_Data_Extractor_From_Git\Alco-Depot-Data-Extractor-main\Dashboard\index.html'
with open(file_path_html, 'r', encoding='utf-8') as f:
    html = f.read()

old_fonts = '<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;800;900&family=Rajdhani:wght@500;600;700&family=Outfit:wght@400;600;700&family=JetBrains+Mono:wght@100;200;300;400;500;600;700;800&display=swap" rel="stylesheet">'
new_fonts = '<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;800;900&family=Rajdhani:wght@500;600;700&family=Outfit:wght@400;600;700&family=JetBrains+Mono:wght@100;200;300;400;500;600;700;800&family=Roboto+Condensed:wght@300;400;700&display=swap" rel="stylesheet">'
html = html.replace(old_fonts, new_fonts)

with open(file_path_html, 'w', encoding='utf-8') as f:
    f.write(html)

# Update style.css to use Roboto Condensed
file_path_css = r'C:\Users\Irak\Desktop\Alco_Depot_Data_Extractor_From_Git\Alco-Depot-Data-Extractor-main\Dashboard\css\style.css'
with open(file_path_css, 'r', encoding='utf-8') as f:
    css = f.read()

old_uighur = '''/* Temporary MPO Table Font Change */
#table-strategic-mpos th,
#table-strategic-mpos td,
#table-strategic-mpos .cell-clip {
    font-family: "Microsoft Uighur", sans-serif !important;
    font-size: 1.2rem !important; /* Uighur is usually very small, needs a bump */
    letter-spacing: normal !important;
}'''

new_roboto = '''/* Temporary MPO Table Font Change */
#table-strategic-mpos th,
#table-strategic-mpos td,
#table-strategic-mpos .cell-clip {
    font-family: "Roboto Condensed", sans-serif !important;
    font-size: 0.9rem !important;
    font-weight: 300 !important;
    letter-spacing: normal !important;
}'''

css = css.replace(old_uighur, new_roboto)

with open(file_path_css, 'w', encoding='utf-8') as f:
    f.write(css)

print("done adding roboto condensed")
