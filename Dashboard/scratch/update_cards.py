import re

js_path = r'C:\Users\Irak\Desktop\Alco_Depot_Data_Extractor_From_Git\Alco-Depot-Data-Extractor-main\Dashboard\js\script.js'
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# 1. Add const keys = ... at the top of renderStrategicMPOTable
js = js.replace('''    const stratData = GLOBAL_DATA.strategic_6_products;
    const prodItem = stratData[ACTIVE_STRATEGIC_PROD];''', '''    const stratData = GLOBAL_DATA.strategic_6_products;
    const keys = GLOBAL_DATA._strategic_keys || Object.keys(stratData);
    const prodItem = stratData[ACTIVE_STRATEGIC_PROD];''')

# 2. MPO product cards update
mpo_target = '''    CURRENT_FILTERED_MPOS = filteredMpos;'''
mpo_repl = '''    CURRENT_FILTERED_MPOS = filteredMpos;
    const isMpoFiltered = filteredMpos.length < displayMpos.length;
    const mpoCards = document.querySelectorAll("#strategic-6-buttons-container .strat-btn");
    if (mpoCards && mpoCards.length > 0) {
        let selK = ACTIVE_STRATEGIC_PRODS.filter(k => keys.includes(k));
        let unselK = keys.filter(k => !ACTIVE_STRATEGIC_PRODS.includes(k));
        const ordK = [...selK, ...unselK];
        const validIds = new Set(filteredMpos.map(m => m.depot + '_' + m.mpo_code));
        ordK.forEach((prodName, idx) => {
            const card = mpoCards[idx];
            if (!card) return;
            const item = stratData[prodName];
            let dU = 0, dP = 0, dI = 0;
            if (isMpoFiltered) {
                let source = (ACTIVE_STRATEGIC_MONTH === "ALL") ? (item.mpo_top50_all || []) : ((item.mpo_top50_by_month && item.mpo_top50_by_month[ACTIVE_STRATEGIC_MONTH]) ? item.mpo_top50_by_month[ACTIVE_STRATEGIC_MONTH] : []);
                source.forEach(m => {
                    const mk = (m.depot || 'Unknown') + '_' + m.mpo_code;
                    if (validIds.has(mk)) { dU += (m.units || 0); dP += (m.parties || 0); dI += (m.invoices || 0); }
                });
            } else {
                if (ACTIVE_STRATEGIC_MONTH === "ALL") {
                    dU = item.total_units; dP = item.total_parties; dI = item.total_invoices;
                } else {
                    let source = (item.mpo_top50_by_month && item.mpo_top50_by_month[ACTIVE_STRATEGIC_MONTH]) ? item.mpo_top50_by_month[ACTIVE_STRATEGIC_MONTH] : [];
                    dU = source.reduce((s, m) => s + (m.units || 0), 0); dP = source.reduce((s, m) => s + (m.parties || 0), 0); dI = source.reduce((s, m) => s + (m.invoices || 0), 0);
                }
            }
            const spans = card.querySelectorAll("div:nth-of-type(2) span");
            if (spans.length >= 3) {
                spans[0].innerHTML = 📦 \ U;
                spans[1].innerHTML = 👥 \ Parties;
                spans[2].innerHTML = 🧾 \ Inv;
            }
        });
    }'''
js = js.replace(mpo_target, mpo_repl)

# 3. FM product cards update
fm_target = '''    CURRENT_FILTERED_FMS = filteredFMs;'''
fm_repl = '''    CURRENT_FILTERED_FMS = filteredFMs;
    const isFmFiltered = filteredFMs.length < fmsList.length;
    const fmCards = document.querySelectorAll("#strategic-6-buttons-container-copy .strat-btn");
    if (fmCards && fmCards.length > 0) {
        let selK = ACTIVE_STRATEGIC_PRODS_FM.filter(k => keys.includes(k));
        let unselK = keys.filter(k => !ACTIVE_STRATEGIC_PRODS_FM.includes(k));
        const ordK = [...selK, ...unselK];
        const validFMs = new Set(filteredFMs.map(f => f.fm_name));
        ordK.forEach((prodName, idx) => {
            const card = fmCards[idx];
            if (!card) return;
            const item = stratData[prodName];
            let dU = 0, dP = 0, dI = 0;
            if (isFmFiltered) {
                let source = (ACTIVE_STRATEGIC_MONTH_FM === "ALL") ? (item.mpo_top50_all || []) : ((item.mpo_top50_by_month && item.mpo_top50_by_month[ACTIVE_STRATEGIC_MONTH_FM]) ? item.mpo_top50_by_month[ACTIVE_STRATEGIC_MONTH_FM] : []);
                source.forEach(m => {
                    const fName = m.fm_name || 'Unknown';
                    if (validFMs.has(fName)) { dU += (m.units || 0); dP += (m.parties || 0); dI += (m.invoices || 0); }
                });
            } else {
                if (ACTIVE_STRATEGIC_MONTH_FM === "ALL") {
                    dU = item.total_units; dP = item.total_parties; dI = item.total_invoices;
                } else {
                    let source = (item.mpo_top50_by_month && item.mpo_top50_by_month[ACTIVE_STRATEGIC_MONTH_FM]) ? item.mpo_top50_by_month[ACTIVE_STRATEGIC_MONTH_FM] : [];
                    dU = source.reduce((s, m) => s + (m.units || 0), 0); dP = source.reduce((s, m) => s + (m.parties || 0), 0); dI = source.reduce((s, m) => s + (m.invoices || 0), 0);
                }
            }
            const spans = card.querySelectorAll("div:nth-of-type(2) span");
            if (spans.length >= 3) {
                spans[0].innerHTML = 📦 \ U;
                spans[1].innerHTML = 👥 \ Parties;
                spans[2].innerHTML = 🧾 \ Inv;
            }
        });
    }'''
js = js.replace(fm_target, fm_repl)

# 4. SH product cards update
sh_target = '''    CURRENT_FILTERED_ZONES = filteredZones;'''
sh_repl = '''    CURRENT_FILTERED_ZONES = filteredZones;
    const isShFiltered = filteredZones.length < zonesList.length;
    const shCards = document.querySelectorAll("#strategic-6-buttons-container-copy2 .strat-btn");
    if (shCards && shCards.length > 0) {
        let selK = ACTIVE_STRATEGIC_PRODS_SH.filter(k => keys.includes(k));
        let unselK = keys.filter(k => !ACTIVE_STRATEGIC_PRODS_SH.includes(k));
        const ordK = [...selK, ...unselK];
        const validZones = new Set(filteredZones.map(z => z.zone));
        ordK.forEach((prodName, idx) => {
            const card = shCards[idx];
            if (!card) return;
            const item = stratData[prodName];
            let dU = 0, dP = 0, dI = 0;
            if (isShFiltered) {
                let source = (ACTIVE_STRATEGIC_MONTH_SH === "ALL") ? (item.mpo_top50_all || []) : ((item.mpo_top50_by_month && item.mpo_top50_by_month[ACTIVE_STRATEGIC_MONTH_SH]) ? item.mpo_top50_by_month[ACTIVE_STRATEGIC_MONTH_SH] : []);
                source.forEach(m => {
                    const zName = m.zone || 'Unknown';
                    if (validZones.has(zName)) { dU += (m.units || 0); dP += (m.parties || 0); dI += (m.invoices || 0); }
                });
            } else {
                if (ACTIVE_STRATEGIC_MONTH_SH === "ALL") {
                    dU = item.total_units; dP = item.total_parties; dI = item.total_invoices;
                } else {
                    let source = (item.mpo_top50_by_month && item.mpo_top50_by_month[ACTIVE_STRATEGIC_MONTH_SH]) ? item.mpo_top50_by_month[ACTIVE_STRATEGIC_MONTH_SH] : [];
                    dU = source.reduce((s, m) => s + (m.units || 0), 0); dP = source.reduce((s, m) => s + (m.parties || 0), 0); dI = source.reduce((s, m) => s + (m.invoices || 0), 0);
                }
            }
            const spans = card.querySelectorAll("div:nth-of-type(2) span");
            if (spans.length >= 3) {
                spans[0].innerHTML = 📦 \ U;
                spans[1].innerHTML = 👥 \ Parties;
                spans[2].innerHTML = 🧾 \ Inv;
            }
        });
    }'''
js = js.replace(sh_target, sh_repl)

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)
print("Product cards update injected!")
