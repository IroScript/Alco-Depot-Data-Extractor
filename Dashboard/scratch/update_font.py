import re

file_path = r'C:\Users\Irak\Desktop\Alco_Depot_Data_Extractor_From_Git\Alco-Depot-Data-Extractor-main\Dashboard\index.html'

with open(file_path, 'r', encoding='utf-8') as f:
    html = f.read()

# Add JetBrains Mono to Google Fonts link
old_fonts = '<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;800;900&family=Rajdhani:wght@500;600;700&family=Outfit:wght@400;600;700&display=swap" rel="stylesheet">'
new_fonts = '<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;800;900&family=Rajdhani:wght@500;600;700&family=Outfit:wght@400;600;700&family=JetBrains+Mono:wght@100;200;300;400;500;600;700;800&display=swap" rel="stylesheet">'
html = html.replace(old_fonts, new_fonts)

# Update Tailwind config
old_tw_fonts = '''                    fontFamily: {
                        cyber: ['Orbitron', 'sans-serif'],
                        tech: ['Rajdhani', 'sans-serif'],
                        body: ['Outfit', 'sans-serif']
                    },'''
new_tw_fonts = '''                    fontFamily: {
                        cyber: ['Orbitron', 'sans-serif'],
                        tech: ['"JetBrains Mono"', 'monospace'],
                        body: ['"JetBrains Mono"', 'monospace']
                    },'''
html = html.replace(old_tw_fonts, new_tw_fonts)

# Force weight for tech font to be Extra Thin (200) everywhere? The user said "extra thin font diye dekhba? sob design, bold color kono kisu touch korba naa"
# If I don't touch bold, then bold text will remain bold (700). That's what they asked for ("sob design, bold color kono kisu touch korba naa").
# So just changing the fontFamily is enough.

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(html)
print("done")
