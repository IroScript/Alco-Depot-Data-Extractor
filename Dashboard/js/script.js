/* ==========================================================================
   ALCO PHARMA // ADVANCED FIELD FORCE ANALYTICS - TELEMETRY & UI ENGINE
   Dynamic JavaScript Frontend Logic with Professional Corporate Formatting
   ========================================================================== */

let GLOBAL_DATA = null;
let charts = {};

// Strategic table global state
let STRATEGIC_PAGE = 1;
const STRATEGIC_PER_PAGE = 20;

// Strategic table filters global selection state
let STRATEGIC_FILTERS_SELECTIONS = {
    rank: null,
    zone: null,
    fm: null,
    code: null,
    market: null,
    units: null,
    parties: null,
    invoices: null,
    sales: null
};

// Temp selection state to hold values before clicking "OK"
let TEMP_FILTERS_SELECTIONS = {};

const MONTH_MAP = {
    '2026-01': 'Jan',
    '2026-02': 'Feb',
    '2026-03': 'Mar',
    '2026-04': 'Apr',
    '2026-05': 'May',
    '2026-06': 'Jun',
    '2026-07': 'Jul',
    '2026-08': 'Aug',
    '2026-09': 'Sep',
    '2026-10': 'Oct',
    '2026-11': 'Nov',
    '2026-12': 'Dec'
};

document.addEventListener("DOMContentLoaded", () => {
    initTabs();
    initEventListeners();
    loadDashboardData();
});

/* Initialize Navigation Tabs */
function initTabs() {
    const tabLinks = document.querySelectorAll(".tab-link");
    const tabContents = document.querySelectorAll(".tab-content");

    tabLinks.forEach(link => {
        link.addEventListener("click", () => {
            tabLinks.forEach(l => l.classList.remove("active"));
            tabContents.forEach(c => c.classList.remove("active"));

            link.classList.add("active");
            const targetId = link.getAttribute("data-target");
            const targetEl = document.getElementById(targetId);
            if (targetEl) targetEl.classList.add("active");

            // Trigger chart resize & Three.js canvas update
            window.dispatchEvent(new Event('resize'));
        });
    });
}

/* Initialize Event Listeners */
function initEventListeners() {
    // Sync / Refresh Button
    const btnRefresh = document.getElementById("btn-refresh-api");
    if (btnRefresh) {
        btnRefresh.addEventListener("click", () => {
            btnRefresh.innerHTML = `⏳ RESYNCING DATA...`;
            loadDashboardData(true).finally(() => {
                btnRefresh.innerHTML = `⚡ RESYNC DATA`;
            });
        });
    }

    // Product Search
    const searchProd = document.getElementById("search-product");
    if (searchProd) {
        searchProd.addEventListener("input", (e) => {
            filterProducts(e.target.value.toLowerCase(), getActivePill("filter-prod"));
        });
    }

    // Product Filter Pills
    document.querySelectorAll("[data-filter-prod]").forEach(pill => {
        pill.addEventListener("click", () => {
            document.querySelectorAll("[data-filter-prod]").forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            const filterVal = pill.getAttribute("data-filter-prod");
            if (searchProd) filterProducts(searchProd.value.toLowerCase(), filterVal);
        });
    });

    // MPO Search
    const searchMPO = document.getElementById("search-mpo");
    if (searchMPO) {
        searchMPO.addEventListener("input", (e) => {
            filterMPOs(e.target.value.toLowerCase(), getActivePill("filter-mpo"));
        });
    }

    // MPO Filter Pills
    document.querySelectorAll("[data-filter-mpo]").forEach(pill => {
        pill.addEventListener("click", () => {
            document.querySelectorAll("[data-filter-mpo]").forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            const filterVal = pill.getAttribute("data-filter-mpo");
            if (searchMPO) filterMPOs(searchMPO.value.toLowerCase(), filterVal);
        });
    });

    // Toggle Top Collapsible Section
    const toggleBtn = document.getElementById("toggle-top-section-btn");
    const collapsibleSection = document.getElementById("collapsible-top-section");
    const toggleIcon = document.getElementById("toggle-icon");
    if (toggleBtn && collapsibleSection && toggleIcon) {
        toggleBtn.addEventListener("click", () => {
            const isHidden = collapsibleSection.classList.contains("hidden");
            if (isHidden) {
                collapsibleSection.classList.remove("hidden");
                toggleIcon.textContent = "−";
                // Trigger charts rendering since container is now visible
                if (typeof renderCharts === "function") {
                    renderCharts();
                }
                // Trigger resize for Dijkstra network canvas
                window.dispatchEvent(new Event('resize'));
            } else {
                collapsibleSection.classList.add("hidden");
                toggleIcon.textContent = "+";
            }
        });
    }

    // Strategic MPO Column Filters popover click outside listener
    document.addEventListener("click", (e) => {
        const popovers = document.querySelectorAll('[id^="popover-"]');
        popovers.forEach(popover => {
            const colName = popover.id.replace("popover-", "");
            const triggerCol = document.getElementById(`filter-col-${colName}`);
            if (triggerCol && !triggerCol.contains(e.target)) {
                popover.classList.add("hidden");
            }
        });
    });
}

function getActivePill(group) {
    const active = document.querySelector(`[data-${group}].active`);
    return active ? active.getAttribute(`data-${group}`) : "all";
}

/* Load Dashboard Data (API -> Fallback Static JSON) */
async function loadDashboardData(forceRefresh = false) {
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
        console.warn("API server unreachable, falling back to data/api_data.json...", err);
        try {
            const resStatic = await fetch("data/api_data.json");
            if (resStatic.ok) {
                GLOBAL_DATA = await resStatic.json();
                if (statusBadge && statusText) {
                    statusBadge.className = "px-3 py-1 rounded-full bg-amber-950/60 border border-amber-500/50 text-amber-300 font-tech font-semibold text-xs flex items-center gap-2 shadow-neon-purple";
                    statusText.textContent = "STATIC DATA CACHE";
                }
            } else {
                throw new Error("Static JSON unreachable");
            }
        } catch (staticErr) {
            console.error("Failed to load dashboard data:", staticErr);
            if (statusBadge && statusText) {
                statusBadge.className = "px-3 py-1 rounded-full bg-rose-950/60 border border-rose-500/50 text-rose-300 font-tech font-semibold text-xs flex items-center gap-2";
                statusText.textContent = "DATA SYNC FAILED";
            }
            return;
        }
    }

    renderAllComponents();
}

/* Render All UI Components */
function renderAllComponents() {
    if (!GLOBAL_DATA) return;

    // Set ACTIVE_STRATEGIC_MONTH to the latest month by default if still "ALL"
    if (GLOBAL_DATA.monthly_trends && GLOBAL_DATA.monthly_trends.length > 0 && ACTIVE_STRATEGIC_MONTH === "ALL") {
        const months = GLOBAL_DATA.monthly_trends.map(t => t.month);
        months.sort((a, b) => b.localeCompare(a));
        ACTIVE_STRATEGIC_MONTH = months[0];
    }

    renderKPIs(GLOBAL_DATA.kpis);
    renderSpotlight(GLOBAL_DATA.top_5_products_deep || GLOBAL_DATA.top_50_products.slice(0, 5));
    renderProductsTable(GLOBAL_DATA.top_50_products);
    renderMPOsTable(GLOBAL_DATA.top_50_mpos);
    renderFMsTable(GLOBAL_DATA.top_20_fms);
    renderSectorsTable(GLOBAL_DATA.top_5_sector_heads);
    renderMonthlyTable(GLOBAL_DATA.monthly_trends);
    renderStrategic6Products();
    
    renderCharts();
}

/* Format Currency in Bangladesh Standard */
function formatBDT(val) {
    const num = Number(val) || 0;
    const absNum = Math.abs(num);
    if (absNum >= 1000000) {
        return "৳ " + (num / 1000000).toFixed(2) + " M";
    } else if (absNum >= 1000) {
        return "৳ " + (num / 1000).toFixed(2) + " K";
    }
    return "৳ " + num.toFixed(2);
}

/* Render KPI Matrix */
function renderKPIs(kpis) {
    if (!kpis) return;
    const elSales = document.getElementById("kpi-sales"); if (elSales) elSales.textContent = formatBDT(kpis.total_sales);
    const elInvoices = document.getElementById("kpi-invoices"); if (elInvoices) elInvoices.textContent = Number(kpis.total_invoices).toLocaleString('en-IN');
    const elParties = document.getElementById("kpi-parties"); if (elParties) elParties.textContent = Number(kpis.total_parties).toLocaleString('en-IN');
    const elMpos = document.getElementById("kpi-mpos"); if (elMpos) elMpos.textContent = Number(kpis.total_mpos).toLocaleString('en-IN');
    const elProducts = document.getElementById("kpi-products"); if (elProducts) elProducts.textContent = Number(kpis.total_products).toLocaleString('en-IN');
    const elAov = document.getElementById("kpi-aov"); if (elAov) elAov.textContent = formatBDT(kpis.avg_invoice_val);
}

/* Render Top 5 Spotlight Cards */
function renderSpotlight(top5) {
    const container = document.getElementById("spotlight-cards-container");
    if (!container) return;
    if (!top5 || top5.length === 0) {
        container.innerHTML = `<div class="col-span-full text-center py-10 font-cyber text-cyan-400">NO SPOTLIGHT DATA AVAILABLE.</div>`;
        return;
    }

    container.innerHTML = top5.map(p => `
        <div class="spotlight-card">
            <div class="spotlight-header">
                <span class="spotlight-rank" title="Product Performance Rank">#${p.rank}</span>
                <span class="spotlight-code" title="Strict Product Code Anchor">${p.product_code}</span>
            </div>
            <div class="spotlight-title">${p.product_name}</div>
            
            <div class="space-y-1 my-1">
                <div class="flex justify-between text-[11px] font-tech text-cyan-300">
                    <span>REVENUE SHARE INDEX</span>
                    <span class="font-bold">${p.contribution_pct}%</span>
                </div>
                <div class="w-full bg-slate-900 rounded-full h-2 border border-cyan-500/30 overflow-hidden">
                    <div class="bg-gradient-to-r from-cyan-400 via-indigo-500 to-purple-500 h-full rounded-full shadow-neon-cyan animate-pulse" style="width: ${Math.min(100, p.contribution_pct * 6)}%"></div>
                </div>
            </div>

            <div class="spotlight-stats">
                <div class="stat-item">
                    <span class="stat-label">NET REVENUE</span>
                    <span class="stat-val val-highlight">${formatBDT(p.total_sales)}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">VISITED PARTIES 👥</span>
                    <span class="stat-val"><span class="badge-party">${Number(p.total_parties).toLocaleString()} Parties</span></span>
                </div>
                <div class="stat-item col-span-full">
                    <span class="stat-label">INVOICES BILLED 🧾</span>
                    <span class="stat-val"><span class="badge-invoice w-full justify-center">${Number(p.total_invoices).toLocaleString()} Invoices Generated</span></span>
                </div>
            </div>

            <button class="btn-action w-full justify-center mt-2" onclick="openDrillModal('product', '${p.product_code}')">
                📊 VIEW MONTHLY PARTY & INVOICE TREND
            </button>
        </div>
    `).join('');
}

/* Render Top 50 Products Table */
function renderProductsTable(products) {
    const tbody = document.getElementById("tbody-top50-products");
    if (!tbody) return;
    if (!products || products.length === 0) {
        tbody.innerHTML = `<tr><td colspan="9" style="text-align:center;">No product lines found</td></tr>`;
        return;
    }

    tbody.innerHTML = products.map(p => `
        <tr data-prod-code="${p.product_code.toLowerCase()}" data-prod-name="${p.product_name.toLowerCase()}" data-rank="${p.rank}">
            <td><strong class="font-cyber text-amber-400">#${p.rank}</strong></td>
            <td><span class="code-badge">${p.product_code}</span></td>
            <td><strong class="text-white text-base font-bold">${p.product_name}</strong> <span class="text-[10px] text-cyan-400 font-mono ml-2">[🔒 CODE ANCHOR]</span></td>
            <td class="val-highlight font-cyber text-base">${formatBDT(p.total_sales)}</td>
            <td class="font-mono text-cyan-200">${Number(p.total_quantity).toLocaleString()}</td>
            <td><span class="badge-invoice">${Number(p.total_invoices).toLocaleString()} Invoices</span></td>
            <td><span class="badge-party">${Number(p.total_parties).toLocaleString()} Parties</span></td>
            <td>
                <div class="flex items-center gap-2">
                    <div class="w-16 bg-slate-900 rounded-full h-2 border border-cyan-500/30 overflow-hidden hidden md:block">
                        <div class="bg-gradient-to-r from-cyan-400 to-purple-500 h-full rounded-full shadow-neon-cyan" style="width: ${Math.min(100, p.contribution_pct * 5)}%"></div>
                    </div>
                    <strong class="font-cyber text-cyan-300 text-xs">${p.contribution_pct}%</strong>
                </div>
            </td>
            <td>
                <button class="btn-action text-xs py-1 px-3" onclick="openDrillModal('product', '${p.product_code}')">
                    🔍 MONTHLY BREAKDOWN
                </button>
            </td>
        </tr>
    `).join('');
}

/* Filter Products */
function filterProducts(query, pill) {
    const rows = document.querySelectorAll("#tbody-top50-products tr");
    rows.forEach(row => {
        const code = row.getAttribute("data-prod-code") || "";
        const name = row.getAttribute("data-prod-name") || "";
        const rank = parseInt(row.getAttribute("data-rank") || "100");

        const matchesQuery = code.includes(query) || name.includes(query);
        let matchesPill = true;
        if (pill === "top10") matchesPill = rank <= 10;
        if (pill === "top25") matchesPill = rank <= 25;

        row.style.display = (matchesQuery && matchesPill) ? "" : "none";
    });
}

/* Render Top 50 MPOs Table */
function renderMPOsTable(mpos) {
    const tbody = document.getElementById("tbody-top50-mpos");
    if (!tbody) return;
    if (!mpos || mpos.length === 0) {
        tbody.innerHTML = `<tr><td colspan="9" style="text-align:center;">No MPO records found</td></tr>`;
        return;
    }

    tbody.innerHTML = mpos.map(m => `
        <tr data-mpo-code="${m.mpo_code.toLowerCase()}" data-mpo-zone="${(m.zone||'').toLowerCase()}" data-mpo-depot="${(m.depot||'').toLowerCase()}">
            <td><strong class="font-cyber text-purple-400">#${m.rank}</strong></td>
            <td>
                <span class="code-badge" style="background: rgba(168, 85, 247, 0.25); border-color: #a855f7; color: #f3e8ff;">
                    👤 ${m.mpo_code}
                </span>
            </td>
            <td>
                <strong class="text-white font-bold text-sm bg-purple-950/60 px-2.5 py-1 rounded border border-purple-500/30">📍 ${m.market||'Unknown'}</strong>
                ${m.is_vacant ? '<span class="bg-amber-900/80 text-amber-300 text-xs px-1.5 py-0.5 rounded border border-amber-500/40 ml-1 font-mono">VACANT</span>' : ''}
            </td>
            <td><span class="px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-cyan-300 font-mono text-xs">${m.zone}</span></td>
            <td><span class="text-slate-300 font-tech font-bold">${m.depot}</span></td>
            <td class="val-highlight font-cyber text-base">${formatBDT(m.total_sales)}</td>
            <td class="font-mono text-purple-200">${Number(m.total_quantity).toLocaleString()}</td>
            <td><span class="badge-party">${Number(m.total_parties).toLocaleString()} Parties 👥</span></td>
            <td><span class="badge-invoice">${Number(m.total_invoices).toLocaleString()} Invoices 🧾</span></td>
            <td>
                <button class="btn-action text-xs py-1 px-3" onclick="openDrillModal('mpo', '${m.mpo_code}')">
                    📈 MONTHLY VISITS
                </button>
            </td>
        </tr>
    `).join('');
}

/* Filter MPOs */
function filterMPOs(query, pill) {
    const rows = document.querySelectorAll("#tbody-top50-mpos tr");
    rows.forEach(row => {
        const code = row.getAttribute("data-mpo-code") || "";
        const zone = row.getAttribute("data-mpo-zone") || "";
        const depot = row.getAttribute("data-mpo-depot") || "";

        const matchesQuery = code.includes(query) || zone.includes(query) || depot.includes(query);
        let matchesPill = true;
        if (pill !== "all") matchesPill = zone.includes(pill.toLowerCase()) || depot.includes(pill.toLowerCase());

        row.style.display = (matchesQuery && matchesPill) ? "" : "none";
    });
}

/* Render FMs and Sectors Tables */
function renderFMsTable(fms) {
    const tbody = document.getElementById("tbody-fms");
    if (!tbody || !fms) return;
    tbody.innerHTML = fms.map(f => `
        <tr class="hover:bg-amber-950/20 transition-colors">
            <td><strong class="font-cyber text-amber-400">#${f.rank}</strong></td>
            <td><strong class="text-white font-bold text-base">${f.fm_name}</strong></td>
            <td><span class="px-2 py-0.5 rounded bg-amber-950/50 border border-amber-500/40 text-amber-300 font-mono text-xs">${f.active_mpos} MPOs</span></td>
            <td class="val-highlight font-cyber">${formatBDT(f.total_sales)}</td>
            <td><span class="badge-party text-xs">${Number(f.total_parties).toLocaleString()}</span></td>
            <td><span class="badge-invoice text-xs">${Number(f.total_invoices).toLocaleString()}</span></td>
        </tr>
    `).join('');
}

function renderSectorsTable(sectors) {
    const tbody = document.getElementById("tbody-sectors");
    if (!tbody || !sectors) return;
    tbody.innerHTML = sectors.map(s => `
        <tr class="hover:bg-emerald-950/20 transition-colors">
            <td><strong class="font-cyber text-emerald-400">#${s.rank}</strong></td>
            <td><strong class="text-cyan-300 font-bold text-base uppercase tracking-wider">${s.sector_name}</strong></td>
            <td><span class="px-2 py-0.5 rounded bg-emerald-950/50 border border-emerald-500/40 text-emerald-300 font-mono text-xs">${s.active_mpos} MPOs</span></td>
            <td class="val-highlight font-cyber">${formatBDT(s.total_sales)}</td>
            <td><span class="badge-party text-xs">${Number(s.total_parties).toLocaleString()}</span></td>
        </tr>
    `).join('');
}

/* Render Monthly Table */
function renderMonthlyTable(trends) {
    const tbody = document.getElementById("tbody-monthly-table");
    if (!tbody || !trends) return;
    tbody.innerHTML = trends.map(t => {
        const aov = t.invoices > 0 ? (t.sales / t.invoices) : 0;
        return `
            <tr>
                <td><strong class="font-cyber text-cyan-300 text-base">[ ${t.month} ]</strong></td>
                <td class="val-highlight font-cyber text-base">${formatBDT(t.sales)}</td>
                <td class="font-mono text-cyan-100">${Number(t.quantity).toLocaleString()}</td>
                <td><span class="badge-invoice">${Number(t.invoices).toLocaleString()} Invoices</span></td>
                <td><span class="badge-party">${Number(t.parties).toLocaleString()} Parties</span></td>
                <td class="font-mono text-purple-300 font-bold">${formatBDT(aov)}</td>
            </tr>
        `;
    }).join('');
}

/* ==========================================================================
   STRATEGIC 6 PRODUCTS // TOP 50 MPO BY UNIT HIERARCHY ENGINE
   ========================================================================== */
let ACTIVE_STRATEGIC_PROD = "MOKAST 10 TAB";
let ACTIVE_STRATEGIC_MONTH = "ALL";

function renderStrategic6Products() {
    if (!GLOBAL_DATA || !GLOBAL_DATA.strategic_6_products) return;
    const stratData = GLOBAL_DATA.strategic_6_products;
    const container = document.getElementById("strategic-6-buttons-container");
    if (!container) return;

    const keys = Object.keys(stratData);
    if (keys.length === 0) {
        container.innerHTML = `<div class="col-span-full text-center py-6 text-cyan-400 font-cyber">NO STRATEGIC PRODUCTS FOUND.</div>`;
        return;
    }

    if (!stratData[ACTIVE_STRATEGIC_PROD] && keys.length > 0) {
        ACTIVE_STRATEGIC_PROD = keys[0];
    }

    container.innerHTML = keys.map(prodName => {
        const item = stratData[prodName];
        const isActive = (prodName === ACTIVE_STRATEGIC_PROD);
        return `
            <button class="strat-btn p-3 rounded-xl border text-left transition-all ${isActive ? 'bg-gradient-to-tr from-cyan-600/40 via-indigo-600/40 to-purple-600/40 border-cyan-400 shadow-neon-cyan transform scale-105' : 'bg-slate-900/80 border-slate-800 hover:border-cyan-500/50'}" onclick="selectStrategicProduct('${prodName.replace(/'/g, "\\'")}')">
                <div class="flex justify-between items-center mb-1">
                    <span class="text-[10px] font-cyber tracking-wider text-purple-400 bg-purple-950/60 px-1.5 py-0.5 rounded border border-purple-500/30">TOP 50 MPO</span>
                    <span class="font-mono text-[10px] text-emerald-400">📦 ${Number(item.total_units).toLocaleString()} U</span>
                </div>
                <div class="font-cyber font-bold text-sm text-white truncate my-1" title="${prodName}">💊 ${prodName}</div>
                <div class="flex justify-between items-center text-[11px] font-tech text-slate-400 border-t border-slate-800/80 pt-1 mt-1">
                    <span>👥 ${Number(item.total_parties).toLocaleString()} Parties</span>
                    <span>🧾 ${Number(item.total_invoices).toLocaleString()} Inv</span>
                </div>
            </button>
        `;
    }).join('');

    const monthPillsEl = document.getElementById("strategic-month-pills");
    if (monthPillsEl && GLOBAL_DATA.monthly_trends) {
        const months = GLOBAL_DATA.monthly_trends.map(t => t.month);
        // Sort months latest first (descending order)
        const sortedMonths = [...months].sort((a, b) => b.localeCompare(a));
        
        // Find dynamic min and max month labels
        const minMonth = sortedMonths[sortedMonths.length - 1];
        const maxMonth = sortedMonths[0];
        const minLabel = (MONTH_MAP[minMonth] || minMonth).toUpperCase();
        const maxLabel = (MONTH_MAP[maxMonth] || maxMonth).toUpperCase();

        monthPillsEl.innerHTML = `
            <button class="strat-month-pill ${ACTIVE_STRATEGIC_MONTH === 'ALL' ? 'active bg-cyan-600 text-white shadow-neon-cyan font-bold' : 'bg-slate-900 text-slate-300 hover:bg-slate-800'} px-3 py-1.5 rounded font-tech text-xs" onclick="selectStrategicMonth('ALL')">ALL MONTHS (${minLabel} - ${maxLabel})</button>
            ${sortedMonths.map(m => {
                const monthLabel = MONTH_MAP[m] || m;
                return `
                    <button class="strat-month-pill ${ACTIVE_STRATEGIC_MONTH === m ? 'active bg-cyan-600 text-white shadow-neon-cyan font-bold' : 'bg-slate-900 text-slate-300 hover:bg-slate-800'} px-3 py-1.5 rounded font-tech text-xs" onclick="selectStrategicMonth('${m}')">[ ${monthLabel} ]</button>
                `;
            }).join('')}
        `;
    }

    renderStrategicMPOTable();
}

function selectStrategicProduct(prodName) {
    ACTIVE_STRATEGIC_PROD = prodName;
    STRATEGIC_PAGE = 1; // Reset page
    STRATEGIC_FILTERS_SELECTIONS = { rank: null, zone: null, fm: null, code: null, market: null, units: null, parties: null, invoices: null, sales: null };
    TEMP_FILTERS_SELECTIONS = {};
    renderStrategic6Products();
}

function selectStrategicMonth(monthVal) {
    ACTIVE_STRATEGIC_MONTH = monthVal;
    STRATEGIC_PAGE = 1; // Reset page
    STRATEGIC_FILTERS_SELECTIONS = { rank: null, zone: null, fm: null, code: null, market: null, units: null, parties: null, invoices: null, sales: null };
    TEMP_FILTERS_SELECTIONS = {};
    renderStrategic6Products();
}

function setStrategicPage(page) {
    STRATEGIC_PAGE = page;
    renderStrategicMPOTable();
}

function renderStrategicMPOTable() {
    if (!GLOBAL_DATA || !GLOBAL_DATA.strategic_6_products) return;
    const stratData = GLOBAL_DATA.strategic_6_products;
    const prodItem = stratData[ACTIVE_STRATEGIC_PROD];
    if (!prodItem) return;

    const titleEl = document.getElementById("strategic-active-title");
    const subEl = document.getElementById("strategic-active-subtitle");
    
    const displayMonth = ACTIVE_STRATEGIC_MONTH === "ALL" ? "ALL" : (MONTH_MAP[ACTIVE_STRATEGIC_MONTH] || ACTIVE_STRATEGIC_MONTH);
    if (titleEl) titleEl.textContent = `💊 ${prodItem.product_name} [ MONTH: ${displayMonth} ]`;
    if (subEl) subEl.textContent = `Merged Product Codes: ${(prodItem.merged_codes || []).join(', ')} // Total Units Sold: ${Number(prodItem.total_units).toLocaleString()} Units`;

    let mpos = [];
    if (ACTIVE_STRATEGIC_MONTH === "ALL") {
        mpos = prodItem.mpo_top50_all || [];
    } else {
        mpos = (prodItem.mpo_top50_by_month && prodItem.mpo_top50_by_month[ACTIVE_STRATEGIC_MONTH]) ? prodItem.mpo_top50_by_month[ACTIVE_STRATEGIC_MONTH] : [];
    }

    // Apply Excel-like column filters
    const filteredMpos = mpos.filter(m => {
        // Rank filter
        if (STRATEGIC_FILTERS_SELECTIONS.rank && !STRATEGIC_FILTERS_SELECTIONS.rank.includes(String(m.rank))) return false;
        // Zone filter
        if (STRATEGIC_FILTERS_SELECTIONS.zone && !STRATEGIC_FILTERS_SELECTIONS.zone.includes(m.zone)) return false;
        // FM filter
        if (STRATEGIC_FILTERS_SELECTIONS.fm && !STRATEGIC_FILTERS_SELECTIONS.fm.includes(m.fm_name || 'Unknown')) return false;
        // Code filter
        if (STRATEGIC_FILTERS_SELECTIONS.code && !STRATEGIC_FILTERS_SELECTIONS.code.includes(m.mpo_code)) return false;
        // Market filter
        if (STRATEGIC_FILTERS_SELECTIONS.market && !STRATEGIC_FILTERS_SELECTIONS.market.includes(m.market)) return false;
        // Units filter
        if (STRATEGIC_FILTERS_SELECTIONS.units) {
            const unitsLabel = `${m.units} U`;
            if (!STRATEGIC_FILTERS_SELECTIONS.units.includes(unitsLabel)) return false;
        }
        // Parties filter
        if (STRATEGIC_FILTERS_SELECTIONS.parties && !STRATEGIC_FILTERS_SELECTIONS.parties.includes(String(m.parties))) return false;
        // Invoices filter
        if (STRATEGIC_FILTERS_SELECTIONS.invoices && !STRATEGIC_FILTERS_SELECTIONS.invoices.includes(String(m.invoices))) return false;
        // Sales filter
        if (STRATEGIC_FILTERS_SELECTIONS.sales) {
            const salesLabel = formatBDT(m.sales);
            if (!STRATEGIC_FILTERS_SELECTIONS.sales.includes(salesLabel)) return false;
        }
        return true;
    });

    const totalRecords = filteredMpos.length;
    const totalPages = Math.ceil(totalRecords / STRATEGIC_PER_PAGE) || 1;
    if (STRATEGIC_PAGE > totalPages) STRATEGIC_PAGE = totalPages;

    const startIdx = (STRATEGIC_PAGE - 1) * STRATEGIC_PER_PAGE;
    const paginatedMpos = filteredMpos.slice(startIdx, startIdx + STRATEGIC_PER_PAGE);

    const tbody = document.getElementById("tbody-strategic-mpos");
    if (!tbody) return;
    if (!paginatedMpos || paginatedMpos.length === 0) {
        tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding: 20px;">No MPO records found for this selection.</td></tr>`;
        
        // Clear pagination
        const pagContainer = document.getElementById("strategic-mpo-pagination");
        if (pagContainer) pagContainer.innerHTML = "";
        return;
    }

    tbody.innerHTML = paginatedMpos.map(m => `
        <tr class="hover:bg-cyan-950/20 transition-colors">
            <td><div class="cell-clip">${m.rank}</div></td>
            <td><div class="cell-clip" title="${m.zone}">${m.zone}</div></td>
            <td><div class="cell-clip" title="${m.fm_name || 'Unknown'}">${m.fm_name || 'Unknown'}</div></td>
            <td><div class="cell-clip" title="${m.mpo_code}">👤 ${m.mpo_code}</div></td>
            <td><div class="cell-clip" title="${m.market}">📍 ${m.market}${m.is_vacant ? ' (VACANT)' : ''}</div></td>
            <td><div class="cell-clip">📦 ${Number(m.units).toLocaleString()} U</div></td>
            <td><div class="cell-clip">${Number(m.parties).toLocaleString()} Parties 👥</div></td>
            <td><div class="cell-clip">${Number(m.invoices).toLocaleString()} Inv 🧾</div></td>
            <td><div class="cell-clip">${formatBDT(m.sales)}</div></td>
            <td>
                <div class="cell-clip">
                    <button class="btn-action text-[10px] py-0.5 px-2 bg-purple-900/60 hover:bg-purple-800 border border-purple-400" onclick="openDrillModal('mpo', '${m.mpo_code}')">
                        📈 GRAPH
                    </button>
                </div>
            </td>
        </tr>
    `).join('');

    // Render page numbers (1, 2, 3, 4, 5... all without dots)
    const pagContainer = document.getElementById("strategic-mpo-pagination");
    if (pagContainer) {
        let pagesHtml = "";
        for (let i = 1; i <= totalPages; i++) {
            const isActive = (i === STRATEGIC_PAGE);
            pagesHtml += `
                <button class="px-3 py-1.5 rounded text-xs font-tech font-bold transition-all ${isActive ? 'bg-cyan-600 text-white shadow-neon-cyan border border-cyan-400' : 'bg-slate-900 border border-slate-800 text-slate-300 hover:bg-slate-800'}" onclick="setStrategicPage(${i})">${i}</button>
            `;
        }
        pagContainer.innerHTML = pagesHtml;
    }
}

/* Render Chart.js Visualizations */
function renderCharts() {
    if (!GLOBAL_DATA || !window.Chart) return;

    const months = GLOBAL_DATA.monthly_trends.map(t => t.month);
    const monthlySales = GLOBAL_DATA.monthly_trends.map(t => t.sales);
    const monthlyParties = GLOBAL_DATA.monthly_trends.map(t => t.parties);
    const monthlyInvoices = GLOBAL_DATA.monthly_trends.map(t => t.invoices);

    Chart.defaults.color = "#cbd5e1";
    Chart.defaults.font.family = "Rajdhani";
    Chart.defaults.font.size = 13;
    Chart.defaults.font.weight = "600";

    const commonTooltip = {
        backgroundColor: 'rgba(2, 4, 10, 0.95)',
        borderColor: '#06b6d4',
        borderWidth: 2,
        titleFont: { family: 'Orbitron', size: 14, weight: '800' },
        bodyFont: { family: 'Rajdhani', size: 13 },
        padding: 12,
        boxPadding: 6,
        usePointStyle: true
    };

    // 0. Futuristic Velocity Matrix (Hero Left Panel)
    const ctxMatrix = document.getElementById("chart-futuristic-matrix");
    if (ctxMatrix) {
        if (charts.matrix) charts.matrix.destroy();
        charts.matrix = new Chart(ctxMatrix, {
            type: "line",
            data: {
                labels: months,
                datasets: [
                    {
                        label: "Net Revenue Trajectory (৳)",
                        data: monthlySales,
                        borderColor: "#06b6d4",
                        backgroundColor: (context) => {
                            const ctx = context.chart.ctx;
                            const gradient = ctx.createLinearGradient(0, 0, 0, 260);
                            gradient.addColorStop(0, "rgba(6, 182, 212, 0.45)");
                            gradient.addColorStop(1, "rgba(6, 182, 212, 0.0)");
                            return gradient;
                        },
                        borderWidth: 3,
                        fill: true,
                        tension: 0.45,
                        pointBackgroundColor: "#06b6d4",
                        pointBorderColor: "#fff",
                        pointBorderWidth: 2,
                        pointRadius: 5,
                        pointHoverRadius: 9,
                        yAxisID: 'y'
                    },
                    {
                        label: "Party Visits Frequency 👥",
                        data: monthlyParties,
                        borderColor: "#a855f7",
                        backgroundColor: (context) => {
                            const ctx = context.chart.ctx;
                            const gradient = ctx.createLinearGradient(0, 0, 0, 260);
                            gradient.addColorStop(0, "rgba(168, 85, 247, 0.35)");
                            gradient.addColorStop(1, "rgba(168, 85, 247, 0.0)");
                            return gradient;
                        },
                        borderWidth: 3,
                        borderDash: [4, 4],
                        fill: true,
                        tension: 0.45,
                        pointBackgroundColor: "#a855f7",
                        pointBorderColor: "#fff",
                        pointBorderWidth: 2,
                        pointRadius: 5,
                        pointHoverRadius: 9,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: commonTooltip
                },
                scales: {
                    y: {
                        type: 'linear',
                        position: 'left',
                        grid: { color: "rgba(6, 182, 212, 0.15)" },
                        ticks: { color: "#06b6d4", font: { family: 'Orbitron', size: 11 } }
                    },
                    y1: {
                        type: 'linear',
                        position: 'right',
                        grid: { display: false },
                        ticks: { color: "#a855f7", font: { family: 'Orbitron', size: 11 } }
                    },
                    x: {
                        grid: { color: "rgba(255, 255, 255, 0.05)" },
                        ticks: { color: "#cbd5e1", font: { family: 'Orbitron', size: 11 } }
                    }
                }
            }
        });
    }

    // 1. Overview Monthly Trajectory
    const ctxOverview = document.getElementById("chart-overview-monthly");
    if (ctxOverview) {
        if (charts.overview) charts.overview.destroy();
        charts.overview = new Chart(ctxOverview, {
            type: "line",
            data: {
                labels: months,
                datasets: [{
                    label: "Net Revenue (৳)",
                    data: monthlySales,
                    borderColor: "#06b6d4",
                    backgroundColor: "rgba(6, 182, 212, 0.2)",
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: "#a855f7",
                    pointBorderColor: "#fff",
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 9
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false }, tooltip: commonTooltip },
                scales: {
                    y: { grid: { color: "rgba(6, 182, 212, 0.15)" }, ticks: { color: "#06b6d4" } },
                    x: { grid: { display: false }, ticks: { color: "#cbd5e1" } }
                }
            }
        });
    }

    // 2. Overview Doughnut (Top 5 vs Others)
    const ctxDoughnut = document.getElementById("chart-overview-doughnut");
    if (ctxDoughnut) {
        if (charts.doughnut) charts.doughnut.destroy();
        const top5 = GLOBAL_DATA.top_5_products_deep || GLOBAL_DATA.top_50_products.slice(0, 5);
        const top5Sales = top5.reduce((acc, p) => acc + p.total_sales, 0);
        const totalSales = GLOBAL_DATA.kpis.total_sales || 1;
        const otherSales = Math.max(0, totalSales - top5Sales);

        charts.doughnut = new Chart(ctxDoughnut, {
            type: "doughnut",
            data: {
                labels: [...top5.map(p => p.product_name), "Other Products"],
                datasets: [{
                    data: [...top5.map(p => p.total_sales), otherSales],
                    backgroundColor: [
                        "#06b6d4", "#6366f1", "#a855f7", "#10b981", "#f59e0b", "rgba(255,255,255,0.08)"
                    ],
                    borderColor: "#02040a",
                    borderWidth: 3,
                    hoverOffset: 12
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom', labels: { boxWidth: 12, font: { family: 'Rajdhani', size: 12 } } },
                    tooltip: commonTooltip
                },
                cutout: "75%"
            }
        });
    }

    // 3. Sector Bar Chart
    const ctxSector = document.getElementById("chart-sector-bar");
    if (ctxSector && GLOBAL_DATA.top_5_sector_heads) {
        if (charts.sector) charts.sector.destroy();
        charts.sector = new Chart(ctxSector, {
            type: "bar",
            data: {
                labels: GLOBAL_DATA.top_5_sector_heads.map(s => s.sector_name),
                datasets: [{
                    label: "Sector Revenue (৳)",
                    data: GLOBAL_DATA.top_5_sector_heads.map(s => s.total_sales),
                    backgroundColor: "rgba(16, 185, 129, 0.7)",
                    borderColor: "#10b981",
                    borderWidth: 2,
                    borderRadius: 8
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false }, tooltip: commonTooltip },
                scales: {
                    x: { grid: { color: "rgba(16, 185, 129, 0.15)" }, ticks: { color: "#10b981" } },
                    y: { grid: { display: false }, ticks: { color: "#fff", font: { weight: 'bold' } } }
                }
            }
        });
    }

    // 4. Monthly Dual Axis Chart
    const ctxDual = document.getElementById("chart-monthly-dual");
    if (ctxDual) {
        if (charts.dual) charts.dual.destroy();
        charts.dual = new Chart(ctxDual, {
            type: "bar",
            data: {
                labels: months,
                datasets: [
                    {
                        label: "Net Revenue (৳)",
                        data: monthlySales,
                        backgroundColor: "rgba(99, 102, 241, 0.7)",
                        borderColor: "#6366f1",
                        borderWidth: 2,
                        borderRadius: 8,
                        yAxisID: 'y'
                    },
                    {
                        label: "Unique Visited Parties 👥",
                        data: monthlyParties,
                        type: "line",
                        borderColor: "#10b981",
                        backgroundColor: "#10b981",
                        borderWidth: 3,
                        pointRadius: 6,
                        yAxisID: 'y1'
                    },
                    {
                        label: "Invoices Billed 🧾",
                        data: monthlyInvoices,
                        type: "line",
                        borderColor: "#f59e0b",
                        backgroundColor: "#f59e0b",
                        borderWidth: 2,
                        borderDash: [5, 5],
                        pointRadius: 5,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { tooltip: commonTooltip },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: { display: true, text: 'Net Revenue (৳)', color: '#6366f1' },
                        grid: { color: "rgba(99, 102, 241, 0.15)" },
                        ticks: { color: '#6366f1' }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: { display: true, text: 'Visits & Memos (Parties / Invoices)', color: '#10b981' },
                        grid: { display: false },
                        ticks: { color: '#10b981' }
                    },
                    x: { grid: { display: false }, ticks: { color: '#fff' } }
                }
            }
        });
    }
}

/* Open Modal for Detailed Drilldown */
function openDrillModal(type, code) {
    const modal = document.getElementById("drill-modal");
    const title = document.getElementById("modal-title");
    const subtitle = document.getElementById("modal-subtitle");
    const tbody = document.getElementById("modal-tbody");

    if (!modal) return;

    let item = null;
    if (type === "product") {
        item = GLOBAL_DATA.top_50_products.find(p => p.product_code === code);
        if (item) {
            title.innerHTML = `💊 <span class="text-white">${item.product_name}</span> <span class="text-cyan-400 font-mono">(${item.product_code})</span>`;
            subtitle.innerHTML = `<span class="text-emerald-400 font-bold">🔒 STRICT CODE ANCHOR</span> // TOTAL REVENUE: <span class="text-white font-cyber">${formatBDT(item.total_sales)}</span> // UNIQUE PARTIES: <span class="text-purple-300 font-bold">${item.total_parties}</span>`;
        }
    } else if (type === "mpo") {
        item = GLOBAL_DATA.top_50_mpos.find(m => m.mpo_code === code);
        if (!item && GLOBAL_DATA.strategic_6_products && GLOBAL_DATA.strategic_6_products[ACTIVE_STRATEGIC_PROD]) {
            const stratItem = GLOBAL_DATA.strategic_6_products[ACTIVE_STRATEGIC_PROD];
            const allMpos = stratItem.mpo_top50_all || [];
            item = allMpos.find(m => m.mpo_code === code);
        }
        if (item) {
            title.innerHTML = `👔 MPO PERFORMANCE: <span class="text-purple-300">${item.mpo_code}</span> // <span class="text-emerald-400 font-bold">📍 ${item.market||'Unknown'}</span> ${item.is_vacant ? '<span class="bg-amber-900/80 text-amber-300 text-xs px-2 py-0.5 rounded border border-amber-500/40 ml-1 font-mono">VACANT</span>' : ''}`;
            const salesVal = item.total_sales || item.sales || 0;
            subtitle.innerHTML = `ASSIGNED ZONE: <span class="text-cyan-400 font-bold">${item.zone}</span> // CORE DEPOT: <span class="text-white font-bold">${item.depot}</span> // NET SALES: <span class="text-emerald-400 font-cyber">${formatBDT(salesVal)}</span>`;
        }
    }

    if (!item || !item.monthly_breakdown) {
        alert("Monthly breakdown telemetry not available for this selection.");
        return;
    }

    // Populate Modal Table
    tbody.innerHTML = item.monthly_breakdown.map(mb => `
        <tr class="hover:bg-cyan-950/30 transition-colors">
            <td><strong class="font-cyber text-cyan-300">[ ${mb.month} ]</strong></td>
            <td class="val-highlight font-cyber">${formatBDT(mb.sales)}</td>
            <td><span class="badge-invoice text-xs">${Number(mb.invoices).toLocaleString()} Invoices</span></td>
            <td><span class="badge-party text-xs">${Number(mb.parties).toLocaleString()} Parties</span></td>
            <td class="font-mono text-slate-300">${Number(mb.quantity || 0).toLocaleString()}</td>
        </tr>
    `).join('');

    // Render Modal Chart
    const ctxModal = document.getElementById("modal-chart");
    if (charts.modal) charts.modal.destroy();
    
    if (ctxModal && window.Chart) {
        charts.modal = new Chart(ctxModal, {
            type: "bar",
            data: {
                labels: item.monthly_breakdown.map(mb => mb.month),
                datasets: [
                    {
                        label: "Monthly Net Revenue (৳)",
                        data: item.monthly_breakdown.map(mb => mb.sales),
                        backgroundColor: "rgba(6, 182, 212, 0.7)",
                        borderColor: "#06b6d4",
                        borderWidth: 2,
                        borderRadius: 6,
                        yAxisID: 'y'
                    },
                    {
                        label: "Unique Parties Visited 👥",
                        data: item.monthly_breakdown.map(mb => mb.parties),
                        type: "line",
                        borderColor: "#a855f7",
                        backgroundColor: "#a855f7",
                        borderWidth: 3,
                        pointRadius: 6,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'top', labels: { font: { family: 'Rajdhani', size: 12 }, color: '#fff' } },
                    tooltip: {
                        backgroundColor: 'rgba(2, 4, 10, 0.95)',
                        borderColor: '#a855f7',
                        borderWidth: 2,
                        titleFont: { family: 'Orbitron', size: 13 }
                    }
                },
                scales: {
                    y: { type: 'linear', position: 'left', grid: { color: "rgba(6, 182, 212, 0.15)" }, ticks: { color: '#06b6d4' } },
                    y1: { type: 'linear', position: 'right', grid: { display: false }, ticks: { color: '#a855f7' } },
                    x: { grid: { display: false }, ticks: { color: '#fff' } }
                }
            }
        });
    }

    modal.classList.add("active");
}

function closeModal() {
    const modal = document.getElementById("drill-modal");
    if (modal) modal.classList.remove("active");
}

/* CSV Export Utility */
function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;

    let csv = [];
    const rows = table.querySelectorAll("tr");
    
    rows.forEach(row => {
        if (row.style.display === "none") return;
        const cols = row.querySelectorAll("th, td");
        let rowData = [];
        cols.forEach((col, idx) => {
            if (col.textContent.includes("MONTHLY BREAKDOWN") || col.textContent.includes("MONTHLY VISITS") || col.textContent.includes("ACTION")) return;
            let text = col.innerText.replace(/(\r\n|\n|\r)/gm, " ").replace(/৳/g, "").replace(/,/g, "").replace(/\[🔒 CODE ANCHOR\]/g, "").trim();
            rowData.push('"' + text + '"');
        });
        if (rowData.length > 0) csv.push(rowData.join(","));
    });

    const csvFile = new Blob([csv.join("\n")], { type: "text/csv;charset=utf-8;" });
    const downloadLink = document.createElement("a");
    downloadLink.download = filename;
    downloadLink.href = window.URL.createObjectURL(csvFile);
    downloadLink.style.display = "none";
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}

/* ==========================================================================
   EXCEL PIVOT-STYLE FILTER TRAVERSAL ENGINE
   ========================================================================== */
function toggleFilterPopover(event, colName) {
    event.stopPropagation();
    
    // Hide all other popovers
    const allPopovers = document.querySelectorAll('[id^="popover-"]');
    allPopovers.forEach(p => {
        if (p.id !== `popover-${colName}`) {
            p.classList.add("hidden");
        }
    });

    const popover = document.getElementById(`popover-${colName}`);
    if (popover) {
        const isHidden = popover.classList.contains("hidden");
        if (isHidden) {
            // Reset temp selections to current actual selections
            if (STRATEGIC_FILTERS_SELECTIONS[colName]) {
                TEMP_FILTERS_SELECTIONS[colName] = new Set(STRATEGIC_FILTERS_SELECTIONS[colName]);
            } else {
                TEMP_FILTERS_SELECTIONS[colName] = null; // means all selected initially
            }
            populateFilterOptions(colName);
            popover.classList.remove("hidden");
        } else {
            popover.classList.add("hidden");
        }
    }
}

function populateFilterOptions(colName) {
    const optionsDiv = document.getElementById(`options-${colName}`);
    if (!optionsDiv) return;

    if (!GLOBAL_DATA || !GLOBAL_DATA.strategic_6_products) return;
    const stratData = GLOBAL_DATA.strategic_6_products;
    const prodItem = stratData[ACTIVE_STRATEGIC_PROD];
    if (!prodItem) return;

    let mpos = [];
    if (ACTIVE_STRATEGIC_MONTH === "ALL") {
        mpos = prodItem.mpo_top50_all || [];
    } else {
        mpos = (prodItem.mpo_top50_by_month && prodItem.mpo_top50_by_month[ACTIVE_STRATEGIC_MONTH]) ? prodItem.mpo_top50_by_month[ACTIVE_STRATEGIC_MONTH] : [];
    }

    // Get all unique values for this column from mpos
    const uniqueValues = new Set();
    mpos.forEach(m => {
        let val = "";
        if (colName === "rank") val = String(m.rank);
        else if (colName === "zone") val = m.zone;
        else if (colName === "fm") val = m.fm_name || 'Unknown';
        else if (colName === "code") val = m.mpo_code;
        else if (colName === "market") val = m.market;
        else if (colName === "units") val = `${m.units} U`;
        else if (colName === "parties") val = `${m.parties}`;
        else if (colName === "invoices") val = `${m.invoices}`;
        else if (colName === "sales") val = formatBDT(m.sales);
        
        if (val) uniqueValues.add(val);
    });

    const valuesArray = Array.from(uniqueValues).sort((a, b) => {
        const numA = parseFloat(a.replace(/[^0-9.]/g, ''));
        const numB = parseFloat(b.replace(/[^0-9.]/g, ''));
        if (!isNaN(numA) && !isNaN(numB)) return numA - numB;
        return a.localeCompare(b);
    });

    // Initialize TEMP selections if not set yet for this col
    if (!TEMP_FILTERS_SELECTIONS[colName]) {
        if (STRATEGIC_FILTERS_SELECTIONS[colName]) {
            TEMP_FILTERS_SELECTIONS[colName] = new Set(STRATEGIC_FILTERS_SELECTIONS[colName]);
        } else {
            TEMP_FILTERS_SELECTIONS[colName] = new Set(valuesArray);
        }
    }

    // Render checkbox list
    optionsDiv.innerHTML = valuesArray.map(val => {
        const isChecked = TEMP_FILTERS_SELECTIONS[colName].has(val);
        return `
            <label class="flex items-center gap-2 cursor-pointer py-0.5 hover:bg-slate-900 rounded px-1 w-full text-slate-300 hover:text-white">
                <input type="checkbox" class="option-chk-item" value="${val}" ${isChecked ? 'checked' : ''} onchange="handleOptionCheckboxChange('${colName}', '${val}', this.checked)">
                <span class="truncate" title="${val}">${val}</span>
            </label>
        `;
    }).join('');
}

function handleOptionCheckboxChange(colName, value, checked) {
    if (!TEMP_FILTERS_SELECTIONS[colName]) {
        TEMP_FILTERS_SELECTIONS[colName] = new Set();
    }
    if (checked) {
        TEMP_FILTERS_SELECTIONS[colName].add(value);
    } else {
        TEMP_FILTERS_SELECTIONS[colName].delete(value);
    }
}

function searchFilterOptions(colName, searchVal) {
    const optionsDiv = document.getElementById(`options-${colName}`);
    if (!optionsDiv) return;
    const items = optionsDiv.querySelectorAll('label');
    const query = searchVal.trim().toLowerCase();
    items.forEach(item => {
        const txt = item.textContent.toLowerCase();
        if (query === "" || txt.includes(query)) {
            item.style.display = "flex";
        } else {
            item.style.display = "none";
        }
    });
}

function selectAllFilterOptions(colName, selectAll) {
    const optionsDiv = document.getElementById(`options-${colName}`);
    if (!optionsDiv) return;
    const checkboxes = optionsDiv.querySelectorAll('input[type="checkbox"]');
    
    checkboxes.forEach(chk => {
        const label = chk.closest('label');
        if (label && label.style.display !== "none") {
            chk.checked = selectAll;
            handleOptionCheckboxChange(colName, chk.value, selectAll);
        }
    });
}

function applyFilter(colName) {
    STRATEGIC_FILTERS_SELECTIONS[colName] = TEMP_FILTERS_SELECTIONS[colName] ? Array.from(TEMP_FILTERS_SELECTIONS[colName]) : null;
    
    // Hide popover
    const popover = document.getElementById(`popover-${colName}`);
    if (popover) popover.classList.add("hidden");

    STRATEGIC_PAGE = 1;
    renderStrategicMPOTable();
}

function cancelFilter(colName) {
    // Hide popover
    const popover = document.getElementById(`popover-${colName}`);
    if (popover) popover.classList.add("hidden");
}

function clearColumnFilter(colName) {
    STRATEGIC_FILTERS_SELECTIONS[colName] = null;
    TEMP_FILTERS_SELECTIONS[colName] = null;
    const popover = document.getElementById(`popover-${colName}`);
    if (popover) popover.classList.add("hidden");
    STRATEGIC_PAGE = 1;
    renderStrategicMPOTable();
}

/* ==========================================================================
   DYNAMIC COLUMN RESIZING TELEMETRY (EXCEL PIVOT EMULATOR)
   ========================================================================== */
let COLUMNS_LOCKED = true;

function toggleColumnLock() {
    COLUMNS_LOCKED = !COLUMNS_LOCKED;
    const btn = document.getElementById("btn-lock-columns");
    if (btn) {
        if (COLUMNS_LOCKED) {
            btn.innerHTML = "🔒 Columns Locked";
            btn.className = "px-3.5 py-2 rounded bg-amber-600/80 border border-amber-500/50 text-white font-tech text-xs font-bold hover:bg-amber-700 transition-all flex items-center gap-1.5";
            removeResizers();
        } else {
            btn.innerHTML = "🔓 Resizing Unlocked";
            btn.className = "px-3.5 py-2 rounded bg-emerald-600/80 border border-emerald-500/50 text-white font-tech text-xs font-bold hover:bg-emerald-700 transition-all flex items-center gap-1.5 shadow-neon-cyan";
            createResizers();
        }
    }
}

function createResizers() {
    const table = document.getElementById("table-strategic-mpos");
    if (!table) return;
    const cols = table.querySelectorAll("thead tr:first-child th");
    
    removeResizers();

    cols.forEach((col, idx) => {
        // Skip last column (Action)
        if (idx === cols.length - 1) return;

        const resizer = document.createElement("div");
        resizer.className = "resizer";
        col.appendChild(resizer);

        let startX, startWidth;

        resizer.addEventListener("mousedown", (e) => {
            if (COLUMNS_LOCKED) return;
            e.preventDefault();
            resizer.classList.add("resizing");
            startX = e.pageX;
            startWidth = col.offsetWidth;

            const onMouseMove = (e) => {
                const delta = e.pageX - startX;
                const newWidth = Math.max(3, startWidth + delta);
                col.style.width = newWidth + "px";
            };

            const onMouseUp = () => {
                resizer.classList.remove("resizing");
                document.removeEventListener("mousemove", onMouseMove);
                document.removeEventListener("mouseup", onMouseUp);
            };

            document.addEventListener("mousemove", onMouseMove);
            document.addEventListener("mouseup", onMouseUp);
        });
    });
}

function removeResizers() {
    const table = document.getElementById("table-strategic-mpos");
    if (!table) return;
    const resizers = table.querySelectorAll(".resizer");
    resizers.forEach(r => r.remove());
}
