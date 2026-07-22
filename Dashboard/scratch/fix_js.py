import re
file_path = r'C:\Users\Irak\Desktop\Alco_Depot_Data_Extractor_From_Git\Alco-Depot-Data-Extractor-main\Dashboard\js\script.js'

with open(file_path, 'r', encoding='utf-8') as f:
    js = f.read()

# Replace _portalPopover calls with popover.classList.remove('hidden')
js = js.replace('_portalPopover(popover, event.currentTarget);', 'popover.classList.remove("hidden");')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(js)
print("done")
