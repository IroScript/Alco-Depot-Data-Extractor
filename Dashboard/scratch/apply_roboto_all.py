import re

file_path_html = r'C:\Users\Irak\Desktop\Alco_Depot_Data_Extractor_From_Git\Alco-Depot-Data-Extractor-main\Dashboard\index.html'
with open(file_path_html, 'r', encoding='utf-8') as f:
    html = f.read()

# Update Tailwind config fonts
old_tw = '''                    fontFamily: {
                        cyber: ['Orbitron', 'sans-serif'],
                        tech: ['"JetBrains Mono"', 'monospace'],
                        body: ['"JetBrains Mono"', 'monospace']
                    },'''
new_tw = '''                    fontFamily: {
                        cyber: ['"Roboto Condensed"', 'sans-serif'],
                        tech: ['"Roboto Condensed"', 'sans-serif'],
                        body: ['"Roboto Condensed"', 'sans-serif'],
                        sans: ['"Roboto Condensed"', 'sans-serif'],
                        mono: ['"Roboto Condensed"', 'sans-serif']
                    },'''
if old_tw in html:
    html = html.replace(old_tw, new_tw)
else:
    print("Warning: old_tw not found")

# Update body style font
html = re.sub(r'body\s*\{\s*background-color:\s*#02040a;\s*color:\s*#e2e8f0;\s*font-family:[^;]+;', 
              r'body {\n            background-color: #02040a;\n            color: #e2e8f0;\n            font-family: "Roboto Condensed", sans-serif;', html)

with open(file_path_html, 'w', encoding='utf-8') as f:
    f.write(html)


file_path_css = r'C:\Users\Irak\Desktop\Alco_Depot_Data_Extractor_From_Git\Alco-Depot-Data-Extractor-main\Dashboard\css\style.css'
with open(file_path_css, 'r', encoding='utf-8') as f:
    css = f.read()

# Replace css variables
css = re.sub(r'--font-heading:[^;]+;', r'--font-heading: "Roboto Condensed", sans-serif;', css)
css = re.sub(r'--font-tech:[^;]+;', r'--font-tech: "Roboto Condensed", sans-serif;', css)
css = re.sub(r'--font-body:[^;]+;', r'--font-body: "Roboto Condensed", sans-serif;', css)

# Remove the temporary MPO table rule
mpo_rule = '''/* Temporary MPO Table Font Change */
#table-strategic-mpos th,
#table-strategic-mpos td,
#table-strategic-mpos .cell-clip {
    font-family: "Roboto Condensed", sans-serif !important;
    font-size: 0.9rem !important;
    font-weight: 300 !important;
    letter-spacing: normal !important;
}'''
css = css.replace(mpo_rule, '')

# Ensure * selector uses it
css = css.replace("font-family: var(--font-body);", "font-family: var(--font-body) !important;")

with open(file_path_css, 'w', encoding='utf-8') as f:
    f.write(css)

print("done applying roboto everywhere")
