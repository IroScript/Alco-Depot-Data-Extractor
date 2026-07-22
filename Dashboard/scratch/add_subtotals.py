import re

js_path = r'C:\Users\Irak\Desktop\Alco_Depot_Data_Extractor_From_Git\Alco-Depot-Data-Extractor-main\Dashboard\js\script.js'
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# 1. MPO
js = js.replace('''    CURRENT_FILTERED_MPOS = filteredMpos;''', '''    CURRENT_FILTERED_MPOS = filteredMpos;
    if (filteredMpos.length < mposList.length) {
        let stU = 0, stP = 0, stI = 0, stS = 0;
        filteredMpos.forEach(m => { stU += (m.units || 0); stP += (m.parties || 0); stI += (m.invoices || 0); stS += (m.sales || 0); });
        const stText =  // FILTER SUBTOTAL: \ U, \ P, \ Inv, \ Sales;
        if (subEl) subEl.textContent = (subEl.textContent.split(' // FILTER SUBTOTAL:')[0]) + stText;
    } else {
        if (subEl) subEl.textContent = subEl.textContent.split(' // FILTER SUBTOTAL:')[0];
    }''')

# Wait, in MPO, what is the array before filtering? Is it mposList?
# Let's check script.js for the MPO filtering block.
