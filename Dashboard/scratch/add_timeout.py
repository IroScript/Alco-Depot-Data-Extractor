import re

file_path = r'C:\Users\Irak\Desktop\Alco_Depot_Data_Extractor_From_Git\Alco-Depot-Data-Extractor-main\Dashboard\js\script.js'

with open(file_path, 'r', encoding='utf-8') as f:
    js = f.read()

old_block = '''async function loadDashboardData(forceRefresh = false) {
    const statusBadge = document.getElementById("connection-status");
    const statusText = document.getElementById("status-text");

    const url = forceRefresh ? "/api/refresh" : "/api/all-dashboard-data";
    
    try {
        const res = await fetch(url);
        if (res.ok) {
            GLOBAL_DATA = await res.json();
            if (statusBadge && statusText) {
                statusBadge.className = "px-3 py-1 rounded-full bg-emerald-950/60 border border-emerald-500/50 text-emerald-300 font-tech font-semibold text-xs flex items-center gap-2 shadow-neon-cyan";
                statusText.textContent = "LIVE SQL ENGINE: ACTIVE";
            }
        } else {
            throw new Error("API server returned status " + res.status);
        }
    } catch (err) {
        console.warn("API server unreachable, falling back to data/api_data.json...", err);'''

new_block = '''async function loadDashboardData(forceRefresh = false) {
    const statusBadge = document.getElementById("connection-status");
    const statusText = document.getElementById("status-text");

    const url = forceRefresh ? "/api/refresh" : "/api/all-dashboard-data";
    
    // Abort controller to prevent 10 second delay if API hangs
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 1000); // 1 second timeout
    
    try {
        const res = await fetch(url, { signal: controller.signal });
        clearTimeout(timeoutId);
        if (res.ok) {
            GLOBAL_DATA = await res.json();
            if (statusBadge && statusText) {
                statusBadge.className = "px-3 py-1 rounded-full bg-emerald-950/60 border border-emerald-500/50 text-emerald-300 font-tech font-semibold text-xs flex items-center gap-2 shadow-neon-cyan";
                statusText.textContent = "LIVE SQL ENGINE: ACTIVE";
            }
        } else {
            throw new Error("API server returned status " + res.status);
        }
    } catch (err) {
        clearTimeout(timeoutId);
        console.warn("API server unreachable, falling back to data/api_data.json...", err);'''

js = js.replace(old_block, new_block)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(js)
print("Updated js successfully")
