import re

file_path = r'C:\Users\Irak\Desktop\Alco_Depot_Data_Extractor_From_Git\Alco-Depot-Data-Extractor-main\Dashboard\css\style.css'
with open(file_path, 'r', encoding='utf-8') as f:
    css = f.read()

# Replace td definition
old_td = '''td {
    padding: 1rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    font-family: var(--font-tech);
    font-size: 0.95rem;
    font-weight: 600;
    color: #e2e8f0;
    transition: background-color 0.2s ease, color 0.2s ease;
}'''
new_td = '''td {
    padding: 1rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    font-family: var(--font-tech);
    font-size: 0.8rem;
    font-weight: 200;
    letter-spacing: -0.5px;
    color: #e2e8f0;
    transition: background-color 0.2s ease, color 0.2s ease;
}'''
css = css.replace(old_td, new_td)

# We also need to check .cell-clip if it has font-size
# .cell-clip in style.css doesn't have font-size. But td has font-size: 0.95rem;

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(css)

# Also let's check th font-weight in css
print("done")
