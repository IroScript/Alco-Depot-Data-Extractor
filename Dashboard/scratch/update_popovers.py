import re

file_path = r'C:\Users\Irak\Desktop\Alco_Depot_Data_Extractor_From_Git\Alco-Depot-Data-Extractor-main\Dashboard\index.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Make thead sticky for the three tables
tables = ['table-strategic-mpos', 'table-strategic-mpos-copy', 'table-strategic-mpos-copy2']
for t_id in tables:
    # Find the table tag
    table_match = re.search(f'<table id="{t_id}".*?>\s*<thead>', content)
    if table_match:
        old_thead = table_match.group(0)
        new_thead = old_thead.replace('<thead>', '<thead class="sticky top-[72px] z-40 bg-slate-950/90">')
        content = content.replace(old_thead, new_thead)

# Regex to find all popover divs. They start with <div id="popover-... and end with the matching </div>
# It's tricky with regex, but we know the structure has exactly 3 nested divs and ends with </div>\s*</div>\s*</th> (wait, it's inside th)
# Let's just find each line containing popover- specific classes and replace them globally, BUT carefully.
# Wait, are these classes used elsewhere?
# min-w-[200px] -> maybe
# text-[10px] -> maybe used in product cards! We shouldn't replace globally.

# Let's extract the exact blocks!
# A popover block starts with <div id="popover-
# and ends with the next </div>\n                            </div>
# We can just iterate through each popover id found in the file.

popover_ids = re.findall(r'id="(popover-[^"]+)"', content)

for pid in popover_ids:
    # Find the start of this popover
    start_idx = content.find(f'id="{pid}"')
    if start_idx == -1: continue
    
    # We want to find the whole div block. It ends with the last </div> before the </th>
    # Let's just grab the next 1500 characters which definitely covers the popover.
    # Then we balance tags or just use string manipulation since the structure is fixed.
    
    chunk_start = content.rfind('<div', 0, start_idx)
    # The popover has 1 main div, 1 input, 1 div for select/clear, 1 div for options, 1 div for footer.
    # Total 4 </div> tags.
    search_chunk = content[chunk_start:chunk_start+2000]
    
    # We can just replace specific strings inside this chunk
    new_chunk = search_chunk
    new_chunk = new_chunk.replace('min-w-[200px]', 'min-w-[240px]')
    new_chunk = new_chunk.replace('text-[10px]', 'text-[12px]')
    new_chunk = new_chunk.replace('text-xs', 'text-[14px]')
    new_chunk = new_chunk.replace('max-h-[140px]', 'max-h-[170px]')
    new_chunk = new_chunk.replace('p-2.5', 'p-3')
    new_chunk = new_chunk.replace('px-2 py-1', 'px-2.5 py-1.5')
    new_chunk = new_chunk.replace('pt-2 mt-2', 'pt-2.5 mt-2.5')
    
    content = content.replace(search_chunk, new_chunk)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated HTML successfully")
