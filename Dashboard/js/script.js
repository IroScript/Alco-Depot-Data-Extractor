/* ==========================================================================
   ALCO PHARMA // ADVANCED FIELD FORCE ANALYTICS - TELEMETRY & UI ENGINE
   Dynamic JavaScript Frontend Logic with Professional Corporate Formatting
   ========================================================================== */

let GLOBAL_DATA = null;
let charts = {};

// Strategic table global state
let STRATEGIC_PAGE = 1;
const STRATEGIC_PER_PAGE = 20;
const STRATEGIC_PER_PAGE_FM = 10;
const STRATEGIC_PER_PAGE_SH = 5;

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

// Strategic table copy global state
let STRATEGIC_PAGE_COPY = 1;
let STRATEGIC_FILTERS_SELECTIONS_COPY = {
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
let TEMP_FILTERS_SELECTIONS_COPY = {};
let COLUMNS_LOCKED_COPY = true;

// Strategic table copy 2 global state
let STRATEGIC_PAGE_COPY2 = 1;
let STRATEGIC_FILTERS_SELECTIONS_COPY2 = {
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
let TEMP_FILTERS_SELECTIONS_COPY2 = {};
let COLUMNS_LOCKED_COPY2 = true;

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
            PRODUCTS_PAGE = 1;
            renderProductsTable();
        });
    }

    // Product Filter Pills (Top 5 / Show All)
    document.querySelectorAll("[data-filter-prod]").forEach(pill => {
        pill.addEventListener("click", () => {
            document.querySelectorAll("[data-filter-prod]").forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            const filterVal = pill.getAttribute("data-filter-prod");
            ACTIVE_PRODUCT_PILL = filterVal;
            PRODUCTS_PAGE = 1;
            renderProductsTable();
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
            if (popover.classList.contains("hidden")) return;
            // Check if click is inside the popover itself
            if (popover.contains(e.target)) return;
            // Check if click is on the trigger button
            const triggerBtn = popover._triggerBtn;
            if (triggerBtn && triggerBtn.contains(e.target)) return;
            popover.classList.add("hidden");
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

function formatBDT(val) {
    const num = Number(val) || 0;
    const absNum = Math.abs(num);
    if (absNum >= 10000000) { // 1 Crore = 10,000,000
        return "৳ " + (num / 10000000).toFixed(2) + " Cr";
    } else if (absNum >= 100000) { // 1 Lakh = 100,000
        return "৳ " + (num / 100000).toFixed(2) + " L";
    }
    // For values under 1 Lakh (e.g. 4000), use standard comma formatting for readability
    return "৳ " + num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatBDTRound(val) {
    const num = Math.round(Number(val) || 0);
    const absNum = Math.abs(num);
    if (absNum >= 10000000) {
        return "৳ " + (num / 10000000).toFixed(2) + " Cr";
    } else if (absNum >= 100000) {
        return "৳ " + (num / 100000).toFixed(2) + " L";
    }
    return "৳ " + num.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
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

function getProductPackTagsHTML(productName, codesString) {
    if (!codesString) return "";
    const codes = codesString.split(',').map(c => c.trim().toUpperCase());
    
    const tagMap = {
        "ACO1": "Standard", "ACQ1": "Bonus", "ZA03": "100mg",
        "ALK1": "60's", "ALM1": "Bonus", "ZA04": "12's", "ZA05": "30's",
        "ALN1": "30's", "ALP1": "Bonus", "AMK3": "Standard", "AMM3": "Bonus",
        "ZA11": "10's", "DEJ1": "50mg", "DEM1": "150mg", "MON1": "60's", "MOP1": "Bonus",
        "TOL2": "Standard"
    };

    let tags = [];
    codes.forEach(c => {
        let label = tagMap[c];
        if (!label) {
            if (c.endsWith('M') || c.endsWith('Q') || c.endsWith('L') || c.endsWith('U') || c.endsWith('W') || c.endsWith('H') || c.endsWith('R') || c.endsWith('T') || c.endsWith('Y') || c.includes('B')) {
                label = "Bonus";
            } else if (c.startsWith('ZA') || c.startsWith('ZB') || c.startsWith('ZC') || c.startsWith('ZD') || c.startsWith('ZE')) {
                if (c === "ZA11") label = "10's";
                else if (c === "ZA04") label = "12's";
                else if (c === "ZA05") label = "30's";
                else if (c === "ZD06") label = "30's";
                else label = "Pack Size";
            }
        }
        
        if (label) {
            let colorClass = "text-slate-400 bg-slate-800/80 border-slate-700";
            if (label.toLowerCase().includes("bonus")) {
                colorClass = "text-amber-300 bg-amber-950/60 border-amber-500/30";
            } else if (label.toLowerCase().includes("60's") || label.toLowerCase().includes("30's") || label.toLowerCase().includes("12's") || label.toLowerCase().includes("10's")) {
                colorClass = "text-cyan-300 bg-cyan-950/60 border-cyan-500/30";
            }
            tags.push(`<span class="text-[9px] px-1.5 py-0.5 rounded border ${colorClass} font-mono ml-1.5 uppercase">${label}</span>`);
        }
    });

    return tags.join('');
}

let PRODUCTS_PAGE = 1;
let ACTIVE_PRODUCT_PILL = "top5"; // default is top5 (Top 5)

/* Render Top 50 Products Table */
function renderProductsTable(products) {
    if (!products) {
        if (GLOBAL_DATA && GLOBAL_DATA.top_50_products) {
            products = GLOBAL_DATA.top_50_products;
        } else {
            return;
        }
    }

    const tbody = document.getElementById("tbody-top50-products");
    if (!tbody) return;

    // 1. Get search query
    const searchQuery = (document.getElementById("search-product")?.value || "").toLowerCase();

    // 2. Filter products based on search query
    const filteredProducts = products.filter(p => {
        const code = (p.product_code || "").toLowerCase();
        const name = (p.product_name || "").toLowerCase();
        return code.includes(searchQuery) || name.includes(searchQuery);
    });

    // Determine page size (Top 5 = 5, Show All = 50)
    const pageSize = ACTIVE_PRODUCT_PILL === "top5" ? 5 : 50;
    
    const totalRecords = filteredProducts.length;
    const totalPages = Math.ceil(totalRecords / pageSize) || 1;
    if (PRODUCTS_PAGE > totalPages) PRODUCTS_PAGE = totalPages;

    const startIdx = (PRODUCTS_PAGE - 1) * pageSize;
    const paginatedProducts = filteredProducts.slice(startIdx, startIdx + pageSize);

    if (paginatedProducts.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding: 20px;">No product lines found</td></tr>`;
        const paginationContainer = document.getElementById("products-pagination");
        if (paginationContainer) paginationContainer.innerHTML = "";
        return;
    }

    // Dynamic month pills render for Top 50 Products tab
    renderProductMonthPills();

    tbody.innerHTML = paginatedProducts.map(p => {
        let displaySales = p.total_sales;
        let displayQty = p.total_quantity;
        let displayInvoices = p.total_invoices;
        let displayParties = p.total_parties;
        let displayPct = p.contribution_pct;

        if (ACTIVE_PRODUCT_MONTH !== "ALL") {
            const mData = (p.monthly_breakdown || []).find(m => m.month === ACTIVE_PRODUCT_MONTH);
            displaySales = mData ? mData.sales : 0;
            displayQty = mData ? mData.quantity : 0;
            displayInvoices = mData ? mData.invoices : 0;
            displayParties = mData ? mData.parties : 0;

            // Recalculate contribution pct based on the selected month's total sales
            let monthTotalSales = 1;
            if (GLOBAL_DATA && GLOBAL_DATA.monthly_trends) {
                const monthTrend = GLOBAL_DATA.monthly_trends.find(t => t.month === ACTIVE_PRODUCT_MONTH);
                if (monthTrend && monthTrend.sales) monthTotalSales = monthTrend.sales;
            }
            displayPct = Math.round((displaySales / monthTotalSales) * 10000) / 100;
        }

        return `
            <tr data-prod-code="${p.product_code.toLowerCase()}" data-prod-name="${p.product_name.toLowerCase()}" data-rank="${p.rank}">
                <td><strong class="font-cyber text-amber-400">#${p.rank}</strong></td>
                <td><strong class="text-white text-base font-bold">${p.product_name}</strong> ${getProductPackTagsHTML(p.product_name, p.product_code)}</td>
                <td class="font-mono text-cyan-200">${Number(displayQty).toLocaleString()}</td>
                <td><span class="badge-invoice">${Number(displayInvoices).toLocaleString()} Invoices</span></td>
                <td><span class="badge-party">${Number(displayParties).toLocaleString()} Parties</span></td>
                <td>
                    <div class="flex items-center gap-2">
                        <div class="w-16 bg-slate-900 rounded-full h-2 border border-cyan-500/30 overflow-hidden hidden md:block">
                            <div class="bg-gradient-to-r from-cyan-400 to-purple-500 h-full rounded-full shadow-neon-cyan" style="width: ${Math.min(100, displayPct * 5)}%"></div>
                        </div>
                        <strong class="font-cyber text-cyan-300 text-xs">${displayPct}%</strong>
                    </div>
                </td>
                <td class="val-highlight font-cyber text-base">${formatBDT(displaySales)}</td>
                <td>
                    <button class="btn-action text-xs py-1 px-3" onclick="openDrillModal('product', '${p.product_code}')">
                        🔍 MONTHLY BREAKDOWN
                    </button>
                </td>
            </tr>
        `;
    }).join('');

    // Generate pagination controls
    renderProductsPagination(totalPages);
}

function renderProductsPagination(totalPages) {
    const container = document.getElementById("products-pagination");
    if (!container) return;
    if (totalPages <= 1) {
        container.innerHTML = "";
        return;
    }

    let buttons = [];
    
    // Prev Button
    buttons.push(`
        <button class="px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-xs text-slate-300 hover:border-cyan-500 hover:text-white transition-all disabled:opacity-40" 
                onclick="changeProductsPage(${PRODUCTS_PAGE - 1})" ${PRODUCTS_PAGE === 1 ? 'disabled' : ''}>
            ◀
        </button>
    `);

    for (let i = 1; i <= totalPages; i++) {
        const isActive = (i === PRODUCTS_PAGE);
        buttons.push(`
            <button class="px-3 py-1 rounded text-xs transition-all font-tech ${isActive ? 'bg-cyan-600 text-white font-bold shadow-neon-cyan' : 'bg-slate-900 border border-slate-800 text-slate-300 hover:border-cyan-500'}" 
                    onclick="changeProductsPage(${i})">
                ${i}
            </button>
        `);
    }

    // Next Button
    buttons.push(`
        <button class="px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-xs text-slate-300 hover:border-cyan-500 hover:text-white transition-all disabled:opacity-40" 
                onclick="changeProductsPage(${PRODUCTS_PAGE + 1})" ${PRODUCTS_PAGE === totalPages ? 'disabled' : ''}>
            ▶
        </button>
    `);

    container.innerHTML = buttons.join('');
}

function changeProductsPage(page) {
    PRODUCTS_PAGE = page;
    renderProductsTable();
}

function filterProducts(query, pill) {
    // Legacy function replaced by renderProductsTable() flow
    renderProductsTable();
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

function getProductIcon(prodName) {
    if (!prodName) return "📦";
    const name = prodName.toLowerCase();
    if (name.includes("tab") || name.includes("tablet")) {
        return "⚪"; // Round tablet icon
    }
    if (name.includes("cap") || name.includes("capsule") || name.includes("softgel")) {
        return "💊"; // Capsule icon
    }
    if (name.includes("syp") || name.includes("syrup")) {
        return "🍶"; // Syrup bottle
    }
    if (name.includes("susp") || name.includes("suspension")) {
        return "🧪"; // Suspension
    }
    if (name.includes("inj") || name.includes("injection")) {
        return "💉"; // Injection
    }
    if (name.includes("supp") || name.includes("suppository")) {
        return "🕯️"; // Suppository
    }
    return "📦"; // Default icon
}

/* ==========================================================================
   STRATEGIC 6 PRODUCTS // TOP 50 MPO BY UNIT HIERARCHY ENGINE
   ========================================================================== */
let ACTIVE_STRATEGIC_PROD = "MOKAST 10 TAB";
let ACTIVE_STRATEGIC_PRODS = [];
let CURRENT_AGGREGATED_MPOS = [];
let ACTIVE_STRATEGIC_MONTH = "ALL";

// Independent states for FM and SH
let IS_FM_SYNCED = false;
let IS_SH_SYNCED = false;

let ACTIVE_STRATEGIC_PROD_FM = "MOKAST 10 TAB";
let ACTIVE_STRATEGIC_PRODS_FM = [];
let ACTIVE_STRATEGIC_MONTH_FM = "ALL";

let ACTIVE_STRATEGIC_PROD_SH = "MOKAST 10 TAB";
let ACTIVE_STRATEGIC_PRODS_SH = [];
let ACTIVE_STRATEGIC_MONTH_SH = "ALL";

let CURRENT_FILTERED_FMS = [];
let CURRENT_FILTERED_ZONES = [];

function toggleSyncFM() {
    IS_FM_SYNCED = !IS_FM_SYNCED;
    const btn = document.getElementById("btn-sync-fm");
    const cardsWrapper = document.getElementById("fm-cards-container-wrapper");
    const bannerWrapper = document.getElementById("fm-banner-container-wrapper");
    const standaloneBadge = document.getElementById("fm-standalone-badge");

    if (IS_FM_SYNCED) {
        if (btn) {
            btn.className = "px-2.5 py-0.5 rounded border border-purple-400 bg-purple-600 text-white font-bold cursor-pointer shadow-neon-purple";
            btn.innerHTML = "✓ FM Synced";
        }
        if (cardsWrapper) cardsWrapper.classList.add("hidden");
        if (bannerWrapper) bannerWrapper.classList.add("hidden");
        if (standaloneBadge) standaloneBadge.classList.remove("hidden");
    } else {
        if (btn) {
            btn.className = "px-2 py-0.5 rounded border border-purple-500/40 bg-purple-950/40 text-purple-300 hover:bg-purple-900/60 transition-all font-bold cursor-pointer";
            btn.innerHTML = "FM";
        }
        if (cardsWrapper) cardsWrapper.classList.remove("hidden");
        if (bannerWrapper) bannerWrapper.classList.remove("hidden");
        if (standaloneBadge) standaloneBadge.classList.add("hidden");
    }
    renderStrategic6Products();
}

function toggleSyncSH() {
    IS_SH_SYNCED = !IS_SH_SYNCED;
    const btn = document.getElementById("btn-sync-sh");
    const cardsWrapper = document.getElementById("sh-cards-container-wrapper");
    const bannerWrapper = document.getElementById("sh-banner-container-wrapper");
    const standaloneBadge = document.getElementById("sh-standalone-badge");

    if (IS_SH_SYNCED) {
        if (btn) {
            btn.className = "px-2.5 py-0.5 rounded border border-amber-400 bg-amber-600 text-white font-bold cursor-pointer shadow-neon-amber";
            btn.innerHTML = "✓ SH Synced";
        }
        if (cardsWrapper) cardsWrapper.classList.add("hidden");
        if (bannerWrapper) bannerWrapper.classList.add("hidden");
        if (standaloneBadge) standaloneBadge.classList.remove("hidden");
    } else {
        if (btn) {
            btn.className = "px-2 py-0.5 rounded border border-amber-500/40 bg-amber-950/40 text-amber-300 hover:bg-amber-900/60 transition-all font-bold cursor-pointer";
            btn.innerHTML = "SH";
        }
        if (cardsWrapper) cardsWrapper.classList.remove("hidden");
        if (bannerWrapper) bannerWrapper.classList.remove("hidden");
        if (standaloneBadge) standaloneBadge.classList.add("hidden");
    }
    renderStrategic6Products();
}

function renderStrategic6Products() {
    if (!GLOBAL_DATA || !GLOBAL_DATA.strategic_6_products) return;
    const stratData = GLOBAL_DATA.strategic_6_products;
    const container = document.getElementById("strategic-6-buttons-container");
    const containerCopy = document.getElementById("strategic-6-buttons-container-copy");
    const containerCopy2 = document.getElementById("strategic-6-buttons-container-copy2");
    if (!container) return;

    const keys = GLOBAL_DATA._strategic_keys || Object.keys(stratData);
    if (keys.length === 0) {
        container.innerHTML = `<div class="col-span-full text-center py-6 text-cyan-400 font-cyber">NO STRATEGIC PRODUCTS FOUND.</div>`;
        if (containerCopy) containerCopy.innerHTML = `<div class="col-span-full text-center py-6 text-purple-400 font-cyber">NO STRATEGIC PRODUCTS FOUND.</div>`;
        if (containerCopy2) containerCopy2.innerHTML = `<div class="col-span-full text-center py-6 text-amber-400 font-cyber">NO STRATEGIC PRODUCTS FOUND.</div>`;
        return;
    }

    if (ACTIVE_STRATEGIC_PRODS.length === 0 && keys.length > 0) {
        ACTIVE_STRATEGIC_PRODS = [ACTIVE_STRATEGIC_PROD];
    }
    if (ACTIVE_STRATEGIC_PRODS_FM.length === 0 && keys.length > 0) {
        ACTIVE_STRATEGIC_PRODS_FM = [ACTIVE_STRATEGIC_PROD_FM];
    }
    if (ACTIVE_STRATEGIC_PRODS_SH.length === 0 && keys.length > 0) {
        ACTIVE_STRATEGIC_PRODS_SH = [ACTIVE_STRATEGIC_PROD_SH];
    }

    if (!stratData[ACTIVE_STRATEGIC_PROD] && keys.length > 0) {
        ACTIVE_STRATEGIC_PROD = keys[0];
    }

    // Update the dropdown checkboxes selection UI
    updateProdGroupDropdownUI(keys);

    // MPO Card Content
    let selectedKeys = ACTIVE_STRATEGIC_PRODS.filter(k => keys.includes(k));
    let unselectedKeys = keys.filter(k => !ACTIVE_STRATEGIC_PRODS.includes(k));
    const orderedKeys = [...selectedKeys, ...unselectedKeys];

    const htmlContentMPO = orderedKeys.map(prodName => {
        const item = stratData[prodName];
        const isActive = ACTIVE_STRATEGIC_PRODS.includes(prodName);
        const selectedIdx = ACTIVE_STRATEGIC_PRODS.indexOf(prodName);
        const orderBadge = (isActive && ACTIVE_STRATEGIC_PRODS.length > 1) ? `<span class="px-1.5 py-0.5 rounded text-[10px] bg-cyan-500 text-black font-extrabold ml-1.5">#${selectedIdx + 1}</span>` : '';
        
        let displayUnits = item.total_units;
        let displayParties = item.total_parties;
        let displayInvoices = item.total_invoices;
        
        if (ACTIVE_STRATEGIC_MONTH !== "ALL") {
            const monthMpos = (item.mpo_top50_by_month && item.mpo_top50_by_month[ACTIVE_STRATEGIC_MONTH]) ? item.mpo_top50_by_month[ACTIVE_STRATEGIC_MONTH] : [];
            displayUnits = monthMpos.reduce((sum, m) => sum + (m.units || 0), 0);
            displayParties = monthMpos.reduce((sum, m) => sum + (m.parties || 0), 0);
            displayInvoices = monthMpos.reduce((sum, m) => sum + (m.invoices || 0), 0);
        }

        return `
            <button class="strat-btn p-3 rounded-xl border text-left transition-all duration-300 min-w-[200px] max-w-[220px] flex-shrink-0 snap-start ${isActive ? 'active shadow-neon-cyan' : 'bg-slate-900/80 border-slate-800 hover:border-cyan-500/50'}" onclick="selectStrategicProduct('${prodName.replace(/'/g, "\\'")}')">
                <div class="font-cyber font-bold text-sm text-white truncate mb-2 flex items-center justify-between" title="${prodName}">
                    <span class="truncate">${getProductIcon(prodName)} ${prodName}</span>${orderBadge}
                </div>
                <div class="flex items-center justify-between text-[10px] font-tech text-slate-400 border-t border-slate-800/80 pt-1.5 mt-1.5 gap-1.5">
                    <span class="text-emerald-400 font-mono font-bold">📦 ${Number(displayUnits).toLocaleString()} U</span>
                    <span>👥 ${Number(displayParties).toLocaleString()} Parties</span>
                    <span>🧾 ${Number(displayInvoices).toLocaleString()} Inv</span>
                </div>
            </button>
        `;
    }).join('');

    container.innerHTML = htmlContentMPO;

    // FM Card Content (if not synced)
    if (containerCopy && !IS_FM_SYNCED) {
        let selectedKeysFM = ACTIVE_STRATEGIC_PRODS_FM.filter(k => keys.includes(k));
        let unselectedKeysFM = keys.filter(k => !ACTIVE_STRATEGIC_PRODS_FM.includes(k));
        const orderedKeysFM = [...selectedKeysFM, ...unselectedKeysFM];

        containerCopy.innerHTML = orderedKeysFM.map(prodName => {
            const item = stratData[prodName];
            const isActive = ACTIVE_STRATEGIC_PRODS_FM.includes(prodName);
            const selectedIdx = ACTIVE_STRATEGIC_PRODS_FM.indexOf(prodName);
            const orderBadge = (isActive && ACTIVE_STRATEGIC_PRODS_FM.length > 1) ? `<span class="px-1.5 py-0.5 rounded text-[10px] bg-purple-500 text-black font-extrabold ml-1.5">#${selectedIdx + 1}</span>` : '';
            
            let displayUnits = item.total_units;
            let displayParties = item.total_parties;
            let displayInvoices = item.total_invoices;
            
            if (ACTIVE_STRATEGIC_MONTH_FM !== "ALL") {
                const monthMpos = (item.mpo_top50_by_month && item.mpo_top50_by_month[ACTIVE_STRATEGIC_MONTH_FM]) ? item.mpo_top50_by_month[ACTIVE_STRATEGIC_MONTH_FM] : [];
                displayUnits = monthMpos.reduce((sum, m) => sum + (m.units || 0), 0);
                displayParties = monthMpos.reduce((sum, m) => sum + (m.parties || 0), 0);
                displayInvoices = monthMpos.reduce((sum, m) => sum + (m.invoices || 0), 0);
            }

            return `
                <button class="strat-btn p-3 rounded-xl border text-left transition-all duration-300 min-w-[200px] max-w-[220px] flex-shrink-0 snap-start ${isActive ? 'active shadow-neon-purple' : 'bg-slate-900/80 border-slate-800 hover:border-purple-500/50'}" onclick="selectStrategicProductFM('${prodName.replace(/'/g, "\\'")}')">
                    <div class="font-cyber font-bold text-sm text-white truncate mb-2 flex items-center justify-between" title="${prodName}">
                        <span class="truncate">${getProductIcon(prodName)} ${prodName}</span>${orderBadge}
                    </div>
                    <div class="flex items-center justify-between text-[10px] font-tech text-slate-400 border-t border-slate-800/80 pt-1.5 mt-1.5 gap-1.5">
                        <span class="text-emerald-400 font-mono font-bold">📦 ${Number(displayUnits).toLocaleString()} U</span>
                        <span>👥 ${Number(displayParties).toLocaleString()} Parties</span>
                        <span>🧾 ${Number(displayInvoices).toLocaleString()} Inv</span>
                    </div>
                </button>
            `;
        }).join('');
    }

    // SH Card Content (if not synced)
    if (containerCopy2 && !IS_SH_SYNCED) {
        let selectedKeysSH = ACTIVE_STRATEGIC_PRODS_SH.filter(k => keys.includes(k));
        let unselectedKeysSH = keys.filter(k => !ACTIVE_STRATEGIC_PRODS_SH.includes(k));
        const orderedKeysSH = [...selectedKeysSH, ...unselectedKeysSH];

        containerCopy2.innerHTML = orderedKeysSH.map(prodName => {
            const item = stratData[prodName];
            const isActive = ACTIVE_STRATEGIC_PRODS_SH.includes(prodName);
            const selectedIdx = ACTIVE_STRATEGIC_PRODS_SH.indexOf(prodName);
            const orderBadge = (isActive && ACTIVE_STRATEGIC_PRODS_SH.length > 1) ? `<span class="px-1.5 py-0.5 rounded text-[10px] bg-amber-500 text-black font-extrabold ml-1.5">#${selectedIdx + 1}</span>` : '';
            
            let displayUnits = item.total_units;
            let displayParties = item.total_parties;
            let displayInvoices = item.total_invoices;
            
            if (ACTIVE_STRATEGIC_MONTH_SH !== "ALL") {
                const monthMpos = (item.mpo_top50_by_month && item.mpo_top50_by_month[ACTIVE_STRATEGIC_MONTH_SH]) ? item.mpo_top50_by_month[ACTIVE_STRATEGIC_MONTH_SH] : [];
                displayUnits = monthMpos.reduce((sum, m) => sum + (m.units || 0), 0);
                displayParties = monthMpos.reduce((sum, m) => sum + (m.parties || 0), 0);
                displayInvoices = monthMpos.reduce((sum, m) => sum + (m.invoices || 0), 0);
            }

            return `
                <button class="strat-btn p-3 rounded-xl border text-left transition-all duration-300 min-w-[200px] max-w-[220px] flex-shrink-0 snap-start ${isActive ? 'active shadow-neon-amber' : 'bg-slate-900/80 border-slate-800 hover:border-amber-500/50'}" onclick="selectStrategicProductSH('${prodName.replace(/'/g, "\\'")}')">
                    <div class="font-cyber font-bold text-sm text-white truncate mb-2 flex items-center justify-between" title="${prodName}">
                        <span class="truncate">${getProductIcon(prodName)} ${prodName}</span>${orderBadge}
                    </div>
                    <div class="flex items-center justify-between text-[10px] font-tech text-slate-400 border-t border-slate-800/80 pt-1.5 mt-1.5 gap-1.5">
                        <span class="text-emerald-400 font-mono font-bold">📦 ${Number(displayUnits).toLocaleString()} U</span>
                        <span>👥 ${Number(displayParties).toLocaleString()} Parties</span>
                        <span>🧾 ${Number(displayInvoices).toLocaleString()} Inv</span>
                    </div>
                </button>
            `;
        }).join('');
    }

    const monthPillsEl = document.getElementById("strategic-month-pills");
    const monthPillsElCopy = document.getElementById("strategic-month-pills-copy");
    const monthPillsElCopy2 = document.getElementById("strategic-month-pills-copy2");
    if (monthPillsEl && GLOBAL_DATA.monthly_trends) {
        const months = GLOBAL_DATA.monthly_trends.map(t => t.month);
        const sortedMonths = [...months].sort((a, b) => b.localeCompare(a));
        
        const minMonth = sortedMonths[sortedMonths.length - 1];
        const maxMonth = sortedMonths[0];
        const minLabel = (MONTH_MAP[minMonth] || minMonth).toUpperCase();
        const maxLabel = (MONTH_MAP[maxMonth] || maxMonth).toUpperCase();

        // MPO Month Pills
        monthPillsEl.innerHTML = `
            <button class="strat-month-pill ${ACTIVE_STRATEGIC_MONTH === 'ALL' ? 'active bg-cyan-600 text-white shadow-neon-cyan font-bold' : 'bg-slate-900 text-slate-300 hover:bg-slate-800'} px-3 py-1.5 rounded font-tech text-xs" onclick="selectStrategicMonth('ALL')">ALL MONTHS (${minLabel} - ${maxLabel})</button>
            ${sortedMonths.map(m => {
                const monthLabel = MONTH_MAP[m] || m;
                return `
                    <button class="strat-month-pill ${ACTIVE_STRATEGIC_MONTH === m ? 'active bg-cyan-600 text-white shadow-neon-cyan font-bold' : 'bg-slate-900 text-slate-300 hover:bg-slate-800'} px-3 py-1.5 rounded font-tech text-xs" onclick="selectStrategicMonth('${m}')">[ ${monthLabel} ]</button>
                `;
            }).join('')}
        `;

        // FM Month Pills
        if (monthPillsElCopy && !IS_FM_SYNCED) {
            monthPillsElCopy.innerHTML = `
                <button class="strat-month-pill ${ACTIVE_STRATEGIC_MONTH_FM === 'ALL' ? 'active bg-purple-600 text-white shadow-neon-purple font-bold' : 'bg-slate-900 text-slate-300 hover:bg-slate-800'} px-3 py-1.5 rounded font-tech text-xs" onclick="selectStrategicMonthFM('ALL')">ALL MONTHS (${minLabel} - ${maxLabel})</button>
                ${sortedMonths.map(m => {
                    const monthLabel = MONTH_MAP[m] || m;
                    return `
                        <button class="strat-month-pill ${ACTIVE_STRATEGIC_MONTH_FM === m ? 'active bg-purple-600 text-white shadow-neon-purple font-bold' : 'bg-slate-900 text-slate-300 hover:bg-slate-800'} px-3 py-1.5 rounded font-tech text-xs" onclick="selectStrategicMonthFM('${m}')">[ ${monthLabel} ]</button>
                    `;
                }).join('')}
            `;
        }

        // SH Month Pills
        if (monthPillsElCopy2 && !IS_SH_SYNCED) {
            monthPillsElCopy2.innerHTML = `
                <button class="strat-month-pill ${ACTIVE_STRATEGIC_MONTH_SH === 'ALL' ? 'active bg-amber-600 text-white shadow-neon-amber font-bold' : 'bg-slate-900 text-slate-300 hover:bg-slate-800'} px-3 py-1.5 rounded font-tech text-xs" onclick="selectStrategicMonthSH('ALL')">ALL MONTHS (${minLabel} - ${maxLabel})</button>
                ${sortedMonths.map(m => {
                    const monthLabel = MONTH_MAP[m] || m;
                    return `
                        <button class="strat-month-pill ${ACTIVE_STRATEGIC_MONTH_SH === m ? 'active bg-amber-600 text-white shadow-neon-amber font-bold' : 'bg-slate-900 text-slate-300 hover:bg-slate-800'} px-3 py-1.5 rounded font-tech text-xs" onclick="selectStrategicMonthSH('${m}')">[ ${monthLabel} ]</button>
                    `;
                }).join('')}
            `;
        }
    }

    renderStrategicMPOTable();
}

function selectStrategicProduct(prodName) {
    ACTIVE_STRATEGIC_PROD = prodName;
    ACTIVE_STRATEGIC_PRODS = [prodName];
    STRATEGIC_PAGE = 1;
    STRATEGIC_FILTERS_SELECTIONS = { rank: null, zone: null, fm: null, code: null, market: null, units: null, parties: null, invoices: null, sales: null };
    TEMP_FILTERS_SELECTIONS = {};
    renderStrategic6Products();
}

function selectStrategicProductFM(prodName) {
    ACTIVE_STRATEGIC_PROD_FM = prodName;
    ACTIVE_STRATEGIC_PRODS_FM = [prodName];
    STRATEGIC_PAGE_COPY = 1;
    STRATEGIC_FILTERS_SELECTIONS_COPY = { rank: null, zone: null, fm: null, code: null, market: null, units: null, parties: null, invoices: null, sales: null };
    TEMP_FILTERS_SELECTIONS_COPY = {};
    renderStrategic6Products();
}

function selectStrategicProductSH(prodName) {
    ACTIVE_STRATEGIC_PROD_SH = prodName;
    ACTIVE_STRATEGIC_PRODS_SH = [prodName];
    STRATEGIC_PAGE_COPY2 = 1;
    STRATEGIC_FILTERS_SELECTIONS_COPY2 = { rank: null, zone: null, fm: null, code: null, market: null, units: null, parties: null, invoices: null, sales: null };
    TEMP_FILTERS_SELECTIONS_COPY2 = {};
    renderStrategic6Products();
}

function selectStrategicMonth(monthVal) {
    ACTIVE_STRATEGIC_MONTH = monthVal;
    STRATEGIC_PAGE = 1;
    STRATEGIC_FILTERS_SELECTIONS = { rank: null, zone: null, fm: null, code: null, market: null, units: null, parties: null, invoices: null, sales: null };
    TEMP_FILTERS_SELECTIONS = {};
    renderStrategic6Products();
}

function selectStrategicMonthFM(monthVal) {
    ACTIVE_STRATEGIC_MONTH_FM = monthVal;
    STRATEGIC_PAGE_COPY = 1;
    STRATEGIC_FILTERS_SELECTIONS_COPY = { rank: null, zone: null, fm: null, code: null, market: null, units: null, parties: null, invoices: null, sales: null };
    TEMP_FILTERS_SELECTIONS_COPY = {};
    renderStrategic6Products();
}

function selectStrategicMonthSH(monthVal) {
    ACTIVE_STRATEGIC_MONTH_SH = monthVal;
    STRATEGIC_PAGE_COPY2 = 1;
    STRATEGIC_FILTERS_SELECTIONS_COPY2 = { rank: null, zone: null, fm: null, code: null, market: null, units: null, parties: null, invoices: null, sales: null };
    TEMP_FILTERS_SELECTIONS_COPY2 = {};
    renderStrategic6Products();
}

function setStrategicPage(page) {
    STRATEGIC_PAGE = page;
    renderStrategicMPOTable();
}

function setStrategicPageCopy(page) {
    STRATEGIC_PAGE_COPY = page;
    renderStrategicMPOTable();
}

function setStrategicPageCopy2(page) {
    STRATEGIC_PAGE_COPY2 = page;
    renderStrategicMPOTable();
}

function renderStrategicMPOTable() {
    if (!GLOBAL_DATA || !GLOBAL_DATA.strategic_6_products) return;
    const stratData = GLOBAL_DATA.strategic_6_products;
    const prodItem = stratData[ACTIVE_STRATEGIC_PROD];
    if (!prodItem) return;

    const titleEl = document.getElementById("strategic-active-title");
    const subEl = document.getElementById("strategic-active-subtitle");
    const titleElCopy = document.getElementById("strategic-active-title-copy");
    const subElCopy = document.getElementById("strategic-active-subtitle-copy");
    const titleElCopy2 = document.getElementById("strategic-active-title-copy2");
    const subElCopy2 = document.getElementById("strategic-active-subtitle-copy2");
    
    const displayMonth = ACTIVE_STRATEGIC_MONTH === "ALL" ? "ALL" : (MONTH_MAP[ACTIVE_STRATEGIC_MONTH] || ACTIVE_STRATEGIC_MONTH);
    const titleText = `${getProductIcon(prodItem.product_name)} ${prodItem.product_name} [ MONTH: ${displayMonth} ]`;
    const subtitleText = `Merged Product Codes: ${(prodItem.merged_codes || []).join(', ')} // Total Units Sold: ${Number(prodItem.total_units).toLocaleString()} Units`;
    
    if (titleEl) titleEl.textContent = titleText;
    if (subEl) subEl.textContent = subtitleText;
    if (titleElCopy) titleElCopy.textContent = `${titleText} (Field Manager)`;
    if (subElCopy) subElCopy.textContent = subtitleText;
    if (titleElCopy2) titleElCopy2.textContent = `${titleText} (Sector Head)`;
    if (subElCopy2) subElCopy2.textContent = subtitleText;

    // Aggregate MPOs across all active products (multi-select)
    if (!ACTIVE_STRATEGIC_PRODS || ACTIVE_STRATEGIC_PRODS.length === 0) {
        ACTIVE_STRATEGIC_PRODS = [ACTIVE_STRATEGIC_PROD];
    }
    
    // 1. Aggregate MPOs for MPO Table
    const mpoMap = {};
    ACTIVE_STRATEGIC_PRODS.forEach(prodName => {
        const item = stratData[prodName];
        if (!item) return;
        
        let list = [];
        if (ACTIVE_STRATEGIC_MONTH === "ALL") {
            list = item.mpo_top50_all || [];
        } else {
            list = (item.mpo_top50_by_month && item.mpo_top50_by_month[ACTIVE_STRATEGIC_MONTH]) ? item.mpo_top50_by_month[ACTIVE_STRATEGIC_MONTH] : [];
        }
        
        list.forEach(m => {
            const code = m.mpo_code;
            if (!mpoMap[code]) {
                mpoMap[code] = {
                    mpo_code: code,
                    fm_name: m.fm_name || 'Unknown',
                    zone: m.zone || 'Unknown',
                    market: m.market || 'Unknown',
                    units: 0,
                    parties: 0,
                    invoices: 0,
                    sales: 0,
                    is_vacant: m.is_vacant,
                    monthly_breakdown: {}
                };
            }
            mpoMap[code].units += m.units || 0;
            mpoMap[code].parties += m.parties || 0;
            mpoMap[code].invoices += m.invoices || 0;
            mpoMap[code].sales += m.sales || 0;
            if (!m.is_vacant) {
                mpoMap[code].is_vacant = false;
            }
            
            (m.monthly_breakdown || []).forEach(mb => {
                const mo = mb.month;
                if (!mpoMap[code].monthly_breakdown[mo]) {
                    mpoMap[code].monthly_breakdown[mo] = { month: mo, units: 0, parties: 0, invoices: 0, sales: 0 };
                }
                mpoMap[code].monthly_breakdown[mo].units += mb.units || mb.quantity || 0;
                mpoMap[code].monthly_breakdown[mo].parties += mb.parties || 0;
                mpoMap[code].monthly_breakdown[mo].invoices += mb.invoices || 0;
                mpoMap[code].monthly_breakdown[mo].sales += mb.sales || 0;
            });
        });
    });

    let mpos = Object.values(mpoMap).map(m => {
        m.monthly_breakdown = Object.values(m.monthly_breakdown);
        return m;
    });

    // Sort and set Rank
    mpos.sort((a, b) => b.units - a.units);
    mpos.forEach((m, idx) => {
        m.rank = idx + 1;
    });

    CURRENT_AGGREGATED_MPOS = mpos;

    // 2. Aggregate MPOs for FM Table (either synced with MPO or independent FM selections)
    let mposFM = mpos;
    if (!IS_FM_SYNCED) {
        const activeProdsFM = (ACTIVE_STRATEGIC_PRODS_FM && ACTIVE_STRATEGIC_PRODS_FM.length > 0) ? ACTIVE_STRATEGIC_PRODS_FM : [ACTIVE_STRATEGIC_PROD_FM];
        const mpoMapFM = {};
        activeProdsFM.forEach(prodName => {
            const item = stratData[prodName];
            if (!item) return;
            let list = ACTIVE_STRATEGIC_MONTH_FM === "ALL" ? (item.mpo_top50_all || []) : ((item.mpo_top50_by_month && item.mpo_top50_by_month[ACTIVE_STRATEGIC_MONTH_FM]) ? item.mpo_top50_by_month[ACTIVE_STRATEGIC_MONTH_FM] : []);
            list.forEach(m => {
                const code = m.mpo_code;
                if (!mpoMapFM[code]) {
                    mpoMapFM[code] = { mpo_code: code, fm_name: m.fm_name || 'Unknown', zone: m.zone || 'Unknown', market: m.market || 'Unknown', units: 0, parties: 0, invoices: 0, sales: 0, is_vacant: m.is_vacant };
                }
                mpoMapFM[code].units += m.units || 0;
                mpoMapFM[code].parties += m.parties || 0;
                mpoMapFM[code].invoices += m.invoices || 0;
                mpoMapFM[code].sales += m.sales || 0;
                if (!m.is_vacant) mpoMapFM[code].is_vacant = false;
            });
        });
        mposFM = Object.values(mpoMapFM);
    }

    // 3. Aggregate MPOs for SH Table (either synced with MPO or independent SH selections)
    let mposSH = mpos;
    if (!IS_SH_SYNCED) {
        const activeProdsSH = (ACTIVE_STRATEGIC_PRODS_SH && ACTIVE_STRATEGIC_PRODS_SH.length > 0) ? ACTIVE_STRATEGIC_PRODS_SH : [ACTIVE_STRATEGIC_PROD_SH];
        const mpoMapSH = {};
        activeProdsSH.forEach(prodName => {
            const item = stratData[prodName];
            if (!item) return;
            let list = ACTIVE_STRATEGIC_MONTH_SH === "ALL" ? (item.mpo_top50_all || []) : ((item.mpo_top50_by_month && item.mpo_top50_by_month[ACTIVE_STRATEGIC_MONTH_SH]) ? item.mpo_top50_by_month[ACTIVE_STRATEGIC_MONTH_SH] : []);
            list.forEach(m => {
                const code = m.mpo_code;
                if (!mpoMapSH[code]) {
                    mpoMapSH[code] = { mpo_code: code, fm_name: m.fm_name || 'Unknown', zone: m.zone || 'Unknown', market: m.market || 'Unknown', units: 0, parties: 0, invoices: 0, sales: 0, is_vacant: m.is_vacant };
                }
                mpoMapSH[code].units += m.units || 0;
                mpoMapSH[code].parties += m.parties || 0;
                mpoMapSH[code].invoices += m.invoices || 0;
                mpoMapSH[code].sales += m.sales || 0;
                if (!m.is_vacant) mpoMapSH[code].is_vacant = false;
            });
        });
        mposSH = Object.values(mpoMapSH);
    }

    // Apply Excel-like column filters for original table
    const filteredMpos = mpos.filter(m => {
        if (STRATEGIC_FILTERS_SELECTIONS.rank && !STRATEGIC_FILTERS_SELECTIONS.rank.includes(String(m.rank))) return false;
        if (STRATEGIC_FILTERS_SELECTIONS.zone && !STRATEGIC_FILTERS_SELECTIONS.zone.includes(m.zone)) return false;
        if (STRATEGIC_FILTERS_SELECTIONS.fm && !STRATEGIC_FILTERS_SELECTIONS.fm.includes(m.fm_name || 'Unknown')) return false;
        if (STRATEGIC_FILTERS_SELECTIONS.code && !STRATEGIC_FILTERS_SELECTIONS.code.includes(m.mpo_code)) return false;
        if (STRATEGIC_FILTERS_SELECTIONS.market && !STRATEGIC_FILTERS_SELECTIONS.market.includes(m.market)) return false;
        if (STRATEGIC_FILTERS_SELECTIONS.units) {
            const unitsLabel = `${m.units} U`;
            if (!STRATEGIC_FILTERS_SELECTIONS.units.includes(unitsLabel)) return false;
        }
        if (STRATEGIC_FILTERS_SELECTIONS.parties && !STRATEGIC_FILTERS_SELECTIONS.parties.includes(String(m.parties))) return false;
        if (STRATEGIC_FILTERS_SELECTIONS.invoices && !STRATEGIC_FILTERS_SELECTIONS.invoices.includes(String(m.invoices))) return false;
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
    if (tbody) {
        if (!paginatedMpos || paginatedMpos.length === 0) {
            tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding: 20px;">No MPO records found for this selection.</td></tr>`;
        } else {
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
        }
    }

    const pagContainer = document.getElementById("strategic-mpo-pagination");
    if (pagContainer) {
        if (!paginatedMpos || paginatedMpos.length === 0) {
            pagContainer.innerHTML = "";
        } else {
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

    // Apply Grouping by Field Manager for copy table (Copy 1)
    const fmsMap = {};
    mposFM.forEach(m => {
        const f = m.fm_name || 'Unknown';
        if (!fmsMap[f]) {
            fmsMap[f] = {
                fm_name: f,
                zone: m.zone || 'Unknown',
                total_mpos: 0,
                vacant_count: 0,
                actual_market: 0,
                units: 0,
                parties: 0,
                invoices: 0,
                sales: 0,
                mpos: []
            };
        }
        fmsMap[f].mpos.push(m);
        fmsMap[f].total_mpos += 1;
        if (m.is_vacant) {
            fmsMap[f].vacant_count += 1;
        } else {
            fmsMap[f].units += m.units || 0;
            fmsMap[f].parties += m.parties || 0;
            fmsMap[f].invoices += m.invoices || 0;
            fmsMap[f].sales += m.sales || 0;
        }
    });

    const fmsList = Object.values(fmsMap).map(f => {
        f.actual_market = f.total_mpos - f.vacant_count;
        const divisor = f.actual_market > 0 ? f.actual_market : 1;
        f.per_mpo_units = f.actual_market > 0 ? (f.units / divisor) : 0;
        f.per_mpo_parties = f.actual_market > 0 ? (f.parties / divisor) : 0;
        f.per_mpo_invoices = f.actual_market > 0 ? (f.invoices / divisor) : 0;
        f.per_mpo_sales = f.actual_market > 0 ? (f.sales / divisor) : 0;
        return f;
    });

    // Sort FMs by per_mpo_units (highest per_mpo_units first)
    fmsList.sort((a, b) => b.per_mpo_units - a.per_mpo_units);
    fmsList.forEach((f, idx) => {
        f.rank = idx + 1;
    });

    const filteredFMs = fmsList.filter(f => {
        if (STRATEGIC_FILTERS_SELECTIONS_COPY.rank && !STRATEGIC_FILTERS_SELECTIONS_COPY.rank.includes(String(f.rank))) return false;
        if (STRATEGIC_FILTERS_SELECTIONS_COPY.zone && !STRATEGIC_FILTERS_SELECTIONS_COPY.zone.includes(f.zone)) return false;
        if (STRATEGIC_FILTERS_SELECTIONS_COPY.fm && !STRATEGIC_FILTERS_SELECTIONS_COPY.fm.includes(f.fm_name)) return false;
        if (STRATEGIC_FILTERS_SELECTIONS_COPY.total_mpos && !STRATEGIC_FILTERS_SELECTIONS_COPY.total_mpos.includes(String(f.total_mpos))) return false;
        if (STRATEGIC_FILTERS_SELECTIONS_COPY.vacant_count && !STRATEGIC_FILTERS_SELECTIONS_COPY.vacant_count.includes(String(f.vacant_count))) return false;
        if (STRATEGIC_FILTERS_SELECTIONS_COPY.actual_market && !STRATEGIC_FILTERS_SELECTIONS_COPY.actual_market.includes(String(f.actual_market))) return false;
        if (STRATEGIC_FILTERS_SELECTIONS_COPY.units) {
            const unitsLabel = `${Math.round(f.units).toLocaleString()} U`;
            if (!STRATEGIC_FILTERS_SELECTIONS_COPY.units.includes(unitsLabel)) return false;
        }
        if (STRATEGIC_FILTERS_SELECTIONS_COPY.parties && !STRATEGIC_FILTERS_SELECTIONS_COPY.parties.includes(String(f.parties))) return false;
        if (STRATEGIC_FILTERS_SELECTIONS_COPY.invoices && !STRATEGIC_FILTERS_SELECTIONS_COPY.invoices.includes(String(f.invoices))) return false;
        if (STRATEGIC_FILTERS_SELECTIONS_COPY.sales) {
            const salesLabel = formatBDTRound(f.sales);
            if (!STRATEGIC_FILTERS_SELECTIONS_COPY.sales.includes(salesLabel)) return false;
        }
        return true;
    });

    CURRENT_FILTERED_FMS = filteredFMs;

    const totalRecordsCopy = filteredFMs.length;
    const totalPagesCopy = Math.ceil(totalRecordsCopy / STRATEGIC_PER_PAGE_FM) || 1;
    if (STRATEGIC_PAGE_COPY > totalPagesCopy) STRATEGIC_PAGE_COPY = totalPagesCopy;

    const startIdxCopy = (STRATEGIC_PAGE_COPY - 1) * STRATEGIC_PER_PAGE_FM;
    const paginatedFMs = filteredFMs.slice(startIdxCopy, startIdxCopy + STRATEGIC_PER_PAGE_FM);

    const tbodyCopy = document.getElementById("tbody-strategic-mpos-copy");
    if (tbodyCopy) {
        if (!paginatedFMs || paginatedFMs.length === 0) {
            tbodyCopy.innerHTML = `<tr><td colspan="14" style="text-align:center; padding: 20px;">No records found.</td></tr>`;
        } else {
            tbodyCopy.innerHTML = paginatedFMs.map(f => `
                <tr class="hover:bg-purple-950/20 transition-colors">
                    <td><div class="cell-clip">${f.rank}</div></td>
                    <td><div class="cell-clip" title="${f.zone}">${f.zone}</div></td>
                    <td><div class="cell-clip" title="${f.fm_name}">${f.fm_name}</div></td>
                    <td><div class="cell-clip" title="${f.total_mpos}">${f.total_mpos}</div></td>
                    <td><div class="cell-clip" title="${f.vacant_count}">${f.vacant_count}</div></td>
                    <td><div class="cell-clip" title="${f.actual_market}">${f.actual_market}</div></td>
                    <td><div class="cell-clip">📦 ${Math.round(f.units).toLocaleString()} U</div></td>
                    <td><div class="cell-clip text-purple-300 font-bold">📦 ${Math.round(f.per_mpo_units).toLocaleString()} U</div></td>
                    <td><div class="cell-clip">${Number(f.parties).toLocaleString()} Parties 👥</div></td>
                    <td><div class="cell-clip text-purple-300 font-bold">${Math.round(f.per_mpo_parties).toLocaleString()} Parties 👥</div></td>
                    <td><div class="cell-clip">${Number(f.invoices).toLocaleString()} Inv 🧾</div></td>
                    <td><div class="cell-clip text-purple-300 font-bold">${Math.round(f.per_mpo_invoices).toLocaleString()} Inv 🧾</div></td>
                    <td><div class="cell-clip">${formatBDTRound(f.sales)}</div></td>
                    <td><div class="cell-clip text-purple-300 font-bold">${formatBDTRound(f.per_mpo_sales)}</div></td>
                    <td>
                        <div class="cell-clip">
                            <button class="btn-action text-[10px] py-0.5 px-2 bg-purple-900/60 hover:bg-purple-800 border border-purple-400" onclick="openFMDrillModal('${f.fm_name}')">
                                📈 GRAPH
                            </button>
                        </div>
                    </td>
                </tr>
            `).join('');
        }
    }

    const pagContainerCopy = document.getElementById("strategic-mpo-pagination-copy");
    if (pagContainerCopy) {
        if (!paginatedFMs || paginatedFMs.length === 0) {
            pagContainerCopy.innerHTML = "";
        } else {
            let pagesHtmlCopy = "";
            for (let i = 1; i <= totalPagesCopy; i++) {
                const isActive = (i === STRATEGIC_PAGE_COPY);
                pagesHtmlCopy += `
                    <button class="px-3 py-1.5 rounded text-xs font-tech font-bold transition-all ${isActive ? 'bg-purple-600 text-white shadow-neon-purple border border-purple-400' : 'bg-slate-900 border border-slate-800 text-slate-300 hover:bg-slate-800'}" onclick="setStrategicPageCopy(${i})">${i}</button>
                `;
            }
            pagContainerCopy.innerHTML = pagesHtmlCopy;
        }
    }

    // Apply Grouping by Zone/Sector Head for copy 2 table
    const zonesMap = {};
    mposSH.forEach(m => {
        const z = m.zone || 'Unknown';
        if (!zonesMap[z]) {
            zonesMap[z] = {
                zone: z,
                total_mpos: 0,
                vacant_count: 0,
                actual_market: 0,
                units: 0,
                parties: 0,
                invoices: 0,
                sales: 0,
                mpos: []
            };
        }
        zonesMap[z].mpos.push(m);
        zonesMap[z].total_mpos += 1;
        if (m.is_vacant) {
            zonesMap[z].vacant_count += 1;
        } else {
            zonesMap[z].units += m.units || 0;
            zonesMap[z].parties += m.parties || 0;
            zonesMap[z].invoices += m.invoices || 0;
            zonesMap[z].sales += m.sales || 0;
        }
    });

    const zonesList = Object.values(zonesMap).map(z => {
        z.actual_market = z.total_mpos - z.vacant_count;
        const divisor = z.actual_market > 0 ? z.actual_market : 1;
        z.per_mpo_units = z.actual_market > 0 ? (z.units / divisor) : 0;
        z.per_mpo_parties = z.actual_market > 0 ? (z.parties / divisor) : 0;
        z.per_mpo_invoices = z.actual_market > 0 ? (z.invoices / divisor) : 0;
        z.per_mpo_sales = z.actual_market > 0 ? (z.sales / divisor) : 0;
        return z;
    });

    // Sort zones by per_mpo_units (highest per_mpo_units first)
    zonesList.sort((a, b) => b.per_mpo_units - a.per_mpo_units);
    zonesList.forEach((z, idx) => {
        z.rank = idx + 1;
    });

    const filteredZones = zonesList.filter(z => {
        if (STRATEGIC_FILTERS_SELECTIONS_COPY2.rank && !STRATEGIC_FILTERS_SELECTIONS_COPY2.rank.includes(String(z.rank))) return false;
        if (STRATEGIC_FILTERS_SELECTIONS_COPY2.zone && !STRATEGIC_FILTERS_SELECTIONS_COPY2.zone.includes(z.zone)) return false;
        if (STRATEGIC_FILTERS_SELECTIONS_COPY2.total_mpos && !STRATEGIC_FILTERS_SELECTIONS_COPY2.total_mpos.includes(String(z.total_mpos))) return false;
        if (STRATEGIC_FILTERS_SELECTIONS_COPY2.vacant_count && !STRATEGIC_FILTERS_SELECTIONS_COPY2.vacant_count.includes(String(z.vacant_count))) return false;
        if (STRATEGIC_FILTERS_SELECTIONS_COPY2.actual_market && !STRATEGIC_FILTERS_SELECTIONS_COPY2.actual_market.includes(String(z.actual_market))) return false;
        if (STRATEGIC_FILTERS_SELECTIONS_COPY2.units) {
            const unitsLabel = `${Math.round(z.units).toLocaleString()} U`;
            if (!STRATEGIC_FILTERS_SELECTIONS_COPY2.units.includes(unitsLabel)) return false;
        }
        if (STRATEGIC_FILTERS_SELECTIONS_COPY2.parties && !STRATEGIC_FILTERS_SELECTIONS_COPY2.parties.includes(String(z.parties))) return false;
        if (STRATEGIC_FILTERS_SELECTIONS_COPY2.invoices && !STRATEGIC_FILTERS_SELECTIONS_COPY2.invoices.includes(String(z.invoices))) return false;
        if (STRATEGIC_FILTERS_SELECTIONS_COPY2.sales) {
            const salesLabel = formatBDTRound(z.sales);
            if (!STRATEGIC_FILTERS_SELECTIONS_COPY2.sales.includes(salesLabel)) return false;
        }
        return true;
    });

    CURRENT_FILTERED_ZONES = filteredZones;

    const totalRecordsCopy2 = filteredZones.length;
    const totalPagesCopy2 = Math.ceil(totalRecordsCopy2 / STRATEGIC_PER_PAGE_SH) || 1;
    if (STRATEGIC_PAGE_COPY2 > totalPagesCopy2) STRATEGIC_PAGE_COPY2 = totalPagesCopy2;

    const startIdxCopy2 = (STRATEGIC_PAGE_COPY2 - 1) * STRATEGIC_PER_PAGE_SH;
    const paginatedZones = filteredZones.slice(startIdxCopy2, startIdxCopy2 + STRATEGIC_PER_PAGE_SH);

    const tbodyCopy2 = document.getElementById("tbody-strategic-mpos-copy2");
    if (tbodyCopy2) {
        if (!paginatedZones || paginatedZones.length === 0) {
            tbodyCopy2.innerHTML = `<tr><td colspan="14" style="text-align:center; padding: 20px;">No records found.</td></tr>`;
        } else {
            tbodyCopy2.innerHTML = paginatedZones.map(z => `
                <tr class="hover:bg-amber-950/20 transition-colors">
                    <td><div class="cell-clip">${z.rank}</div></td>
                    <td><div class="cell-clip" title="${z.zone}">${z.zone}</div></td>
                    <td><div class="cell-clip" title="${z.total_mpos}">${z.total_mpos}</div></td>
                    <td><div class="cell-clip" title="${z.vacant_count}">${z.vacant_count}</div></td>
                    <td><div class="cell-clip" title="${z.actual_market}">${z.actual_market}</div></td>
                    <td><div class="cell-clip">📦 ${Math.round(z.units).toLocaleString()} U</div></td>
                    <td><div class="cell-clip text-amber-300 font-bold">📦 ${Math.round(z.per_mpo_units).toLocaleString()} U</div></td>
                    <td><div class="cell-clip">${Number(z.parties).toLocaleString()} Parties 👥</div></td>
                    <td><div class="cell-clip text-amber-300 font-bold">${Math.round(z.per_mpo_parties).toLocaleString()} Parties 👥</div></td>
                    <td><div class="cell-clip">${Number(z.invoices).toLocaleString()} Inv 🧾</div></td>
                    <td><div class="cell-clip text-amber-300 font-bold">${Math.round(z.per_mpo_invoices).toLocaleString()} Inv 🧾</div></td>
                    <td><div class="cell-clip">${formatBDTRound(z.sales)}</div></td>
                    <td><div class="cell-clip text-amber-300 font-bold">${formatBDTRound(z.per_mpo_sales)}</div></td>
                    <td>
                        <div class="cell-clip">
                            <button class="btn-action text-[10px] py-0.5 px-2 bg-amber-900/60 hover:bg-amber-800 border border-amber-400" onclick="openZoneDrillModal('${z.zone}')">
                                📈 GRAPH
                            </button>
                        </div>
                    </td>
                </tr>
            `).join('');
        }
    }

    const pagContainerCopy2 = document.getElementById("strategic-mpo-pagination-copy2");
    if (pagContainerCopy2) {
        if (!paginatedZones || paginatedZones.length === 0) {
            pagContainerCopy2.innerHTML = "";
        } else {
            let pagesHtmlCopy2 = "";
            for (let i = 1; i <= totalPagesCopy2; i++) {
                const isActive = (i === STRATEGIC_PAGE_COPY2);
                pagesHtmlCopy2 += `
                    <button class="px-3 py-1.5 rounded text-xs font-tech font-bold transition-all ${isActive ? 'bg-amber-600 text-white shadow-neon-amber border border-amber-400' : 'bg-slate-900 border border-slate-800 text-slate-300 hover:bg-slate-800'}" onclick="setStrategicPageCopy2(${i})">${i}</button>
                `;
            }
            pagContainerCopy2.innerHTML = pagesHtmlCopy2;
        }
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

    // Month label converter: "2026-01" → "JAN' 26"
    const MONTH_NAMES = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
    const fmtMonth = (m) => {
        if (!m) return "";
        const s = String(m);
        const parts = s.includes("-") ? s.split("-") : null;
        if (parts && parts.length === 2) {
            const yr = parts[0].slice(-2);
            const mi = parseInt(parts[1], 10);
            if (mi >= 1 && mi <= 12) return `${MONTH_NAMES[mi - 1]}' ${yr}`;
        }
        return s;
    };

    let item = null;
    if (type === "product") {
        item = GLOBAL_DATA.top_50_products.find(p => p.product_code === code);
        if (item) {
            title.innerHTML = `${getProductIcon(item.product_name)} <span class="text-white">${item.product_name}</span> <span class="text-cyan-400 font-mono">(${item.product_code})</span> // 📍 MARKET: <span class="text-emerald-400">${item.market || 'ALL MARKETS'}</span> // ZONE: <span class="text-cyan-400">${item.zone || 'ALL ZONES'}</span>`;
            const totalUnits = item.total_units || item.total_quantity || 0;
            subtitle.innerHTML = `<span class="text-emerald-400 font-bold">🔒 STRICT CODE ANCHOR</span> // TOTAL UNITS: <span class="text-white font-cyber">${Number(totalUnits).toLocaleString()}</span> // UNIQUE PARTIES: <span class="text-purple-300 font-bold">${item.total_parties}</span>`;
        }
    } else if (type === "mpo") {
        const aggMpo = CURRENT_AGGREGATED_MPOS.find(m => m.mpo_code === code);
        if (aggMpo) {
            item = aggMpo;
        } else {
            item = GLOBAL_DATA.top_50_mpos.find(m => m.mpo_code === code);
        }

        if (item) {
            // Title shows active strategic product name (e.g. "💊 MOKAST 10 TAB") + market + zone
            const productName = ACTIVE_STRATEGIC_PROD || 'PRODUCT';
            title.innerHTML = `${getProductIcon(productName)} <span class="text-cyan-300">${productName}</span> // 📍 MARKET: <span class="text-emerald-400 font-bold">${item.market||'Unknown'}</span> // ZONE: <span class="text-purple-300 font-bold">${item.zone}</span>`;
            subtitle.innerHTML = `<span class="text-purple-300 font-bold">👔 MPO ${item.mpo_code}</span> ${item.is_vacant ? '<span class="bg-amber-900/80 text-amber-300 text-xs px-2 py-0.5 rounded border border-amber-500/40 ml-1 font-mono">VACANT</span>' : ''}`;
        }
    }

    if (!item || !item.monthly_breakdown) {
        alert("Monthly breakdown telemetry not available for this selection.");
        return;
    }

    // Reverse so newest month is on top (Jul at top, Jan at bottom)
    const reversed = [...item.monthly_breakdown].reverse();

    // Populate Modal Table — MONTH / UNITS / INVOICES / PARTIES / SALES
    tbody.innerHTML = reversed.map(mb => {
        const units = mb.units || mb.quantity || 0;
        const sales = mb.sales || 0;
        return `
        <tr class="hover:bg-cyan-950/30 transition-colors border-b border-slate-800/40">
            <td><strong class="font-cyber text-cyan-300">${fmtMonth(mb.month)}</strong></td>
            <td class="font-cyber text-emerald-300"><span class="inline-block px-2 py-0.5 rounded font-bold text-emerald-300 bg-emerald-950/60 border-l-4 border-emerald-500">📦 ${Number(units).toLocaleString()} U</span></td>
            <td><span class="inline-block px-2 py-0.5 rounded text-xs font-bold text-cyan-300 bg-cyan-950/60 border-l-4 border-cyan-500">${Number(mb.invoices).toLocaleString()} Inv 🧾</span></td>
            <td><span class="inline-block px-2 py-0.5 rounded text-xs font-bold text-purple-300 bg-purple-950/60 border-l-4 border-purple-500">${Number(mb.parties).toLocaleString()} Parties 👥</span></td>
            <td class="font-cyber text-amber-300"><span class="inline-block px-2 py-0.5 rounded font-bold text-amber-300 bg-amber-950/60 border-l-4 border-amber-500">৳ ${Number(sales).toLocaleString()}</span></td>
        </tr>`;
    }).join('');

    // Render Modal Chart
    const ctxModal = document.getElementById("modal-chart");
    if (charts.modal) charts.modal.destroy();

    if (ctxModal && window.Chart) {
        const monthLabels = reversed.map(mb => fmtMonth(mb.month));
        const unitsData = reversed.map(mb => mb.units || mb.quantity || 0);
        const invoicesData = reversed.map(mb => mb.invoices || 0);
        const partiesData = reversed.map(mb => mb.parties || 0);
        const salesData = reversed.map(mb => mb.sales || 0);

        charts.modal = new Chart(ctxModal, {
            type: "bar",
            data: {
                labels: monthLabels,
                datasets: [
                    {
                        label: "Units 📦",
                        data: unitsData,
                        backgroundColor: "rgba(16, 185, 129, 0.85)",
                        borderColor: "#10b981",
                        borderWidth: 2,
                        borderRadius: 4,
                        yAxisID: 'yCount'
                    },
                    {
                        label: "Invoices 🧾",
                        data: invoicesData,
                        backgroundColor: "rgba(6, 182, 212, 0.85)",
                        borderColor: "#06b6d4",
                        borderWidth: 2,
                        borderRadius: 4,
                        yAxisID: 'yCount'
                    },
                    {
                        label: "Parties 👥",
                        data: partiesData,
                        backgroundColor: "rgba(168, 85, 247, 0.85)",
                        borderColor: "#a855f7",
                        borderWidth: 2,
                        borderRadius: 4,
                        yAxisID: 'yCount'
                    },
                    {
                        label: "Sales (৳)",
                        data: salesData,
                        backgroundColor: "rgba(251, 191, 36, 0.8)",
                        borderColor: "#fbbf24",
                        borderWidth: 2,
                        borderRadius: 4,
                        yAxisID: 'ySales'
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
                        borderColor: '#fbbf24',
                        borderWidth: 2,
                        titleFont: { family: 'Orbitron', size: 13 }
                    }
                },
                scales: {
                    yCount: {
                        type: 'linear', position: 'left',
                        title: { display: true, text: 'UNITS / INV / PARTIES', color: '#10b981', font: { family: 'Orbitron', size: 11, weight: 'bold' } },
                        grid: { color: "rgba(100, 116, 139, 0.2)" },
                        ticks: {
                            color: '#10b981',
                            precision: 0,
                            font: { family: 'Rajdhani', size: 11, weight: 'bold' }
                        },
                        beginAtZero: true
                    },
                    ySales: {
                        type: 'linear', position: 'right',
                        title: { display: true, text: 'SALES (৳)', color: '#fbbf24', font: { family: 'Orbitron', size: 11, weight: 'bold' } },
                        grid: { display: false },
                        ticks: {
                            color: '#fbbf24',
                            precision: 0,
                            font: { family: 'Rajdhani', size: 11, weight: 'bold' },
                            callback: function(value) {
                                if (value >= 100000) return (value / 1000).toFixed(0) + 'K';
                                if (value >= 1000) return (value / 1000).toFixed(1) + 'K';
                                return value;
                            }
                        },
                        beginAtZero: true
                    },
                    x: { grid: { display: false }, ticks: { color: '#fff', font: { family: 'Rajdhani', size: 13, weight: 'bold' } } }
                }
            },
            plugins: [{
                id: 'inlineBarLabels',
                afterDatasetsDraw(chart) {
                    const { ctx } = chart;
                    ctx.save();
                    ctx.font = 'bold 11px Rajdhani, sans-serif';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'bottom';
                    chart.data.datasets.forEach((dataset, datasetIndex) => {
                        const meta = chart.getDatasetMeta(datasetIndex);
                        if (!meta || meta.hidden) return;
                        const color = dataset.borderColor || '#fff';
                        meta.data.forEach((bar, index) => {
                            const value = dataset.data[index];
                            if (value === 0 || value == null) return;
                            let label;
                            if (datasetIndex === 3) {
                                // Sales (৳) — show in K format
                                if (value >= 100000) label = (value / 1000).toFixed(0) + 'K';
                                else if (value >= 1000) label = (value / 1000).toFixed(1) + 'K';
                                else label = Math.round(value).toString();
                            } else {
                                label = Math.round(value).toString();
                            }
                            ctx.fillStyle = color;
                            ctx.fillText(label, bar.x, bar.y - 4);
                        });
                    });
                    ctx.restore();
                }
            }]
        });
    }

    modal.classList.add("active");
}

function openZoneDrillModal(zoneName) {
    const modal = document.getElementById("drill-modal");
    const title = document.getElementById("modal-title");
    const subtitle = document.getElementById("modal-subtitle");
    const tbody = document.getElementById("modal-tbody");

    if (!modal) return;

    // Month label converter
    const MONTH_NAMES = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
    const fmtMonth = (m) => {
        if (!m) return "";
        const s = String(m);
        const parts = s.includes("-") ? s.split("-") : null;
        if (parts && parts.length === 2) {
            const yr = parts[0].slice(-2);
            const mi = parseInt(parts[1], 10);
            if (mi >= 1 && mi <= 12) return `${MONTH_NAMES[mi - 1]}' ${yr}`;
        }
        return s;
    };

    const zoneMpos = CURRENT_AGGREGATED_MPOS.filter(m => (m.zone || 'Unknown') === zoneName);
    const totalMposCount = zoneMpos.length;
    const vacantMposCount = zoneMpos.filter(m => m.is_vacant).length;
    const actualMposCount = totalMposCount - vacantMposCount;
    const divisor = actualMposCount > 0 ? actualMposCount : 1;

    // Group monthly breakdowns of all non-vacant MPOs in this zone
    const monthlyMap = {};
    zoneMpos.forEach(m => {
        if (m.is_vacant) return;
        (m.monthly_breakdown || []).forEach(mb => {
            const month = mb.month;
            if (!monthlyMap[month]) {
                monthlyMap[month] = { month: month, units: 0, parties: 0, invoices: 0, sales: 0 };
            }
            monthlyMap[month].units += mb.units || mb.quantity || 0;
            monthlyMap[month].parties += mb.parties || 0;
            monthlyMap[month].invoices += mb.invoices || 0;
            monthlyMap[month].sales += mb.sales || 0;
        });
    });

    const months = Object.keys(monthlyMap).sort();
    const monthlyBreakdown = months.map(month => {
        const mb = monthlyMap[month];
        return {
            month: month,
            units: actualMposCount > 0 ? (mb.units / divisor) : 0,
            parties: actualMposCount > 0 ? (mb.parties / divisor) : 0,
            invoices: actualMposCount > 0 ? (mb.invoices / divisor) : 0,
            sales: actualMposCount > 0 ? (mb.sales / divisor) : 0
        };
    });

    const productName = ACTIVE_STRATEGIC_PROD || 'PRODUCT';
    title.innerHTML = `${getProductIcon(productName)} <span class="text-cyan-300">${productName}</span> // 📍 SH/Zone (ZONE column): <span class="text-emerald-400 font-bold">${zoneName}</span>`;
    subtitle.innerHTML = `<span class="text-amber-400 font-bold">📊 PER MPO TELEMETRY (Excludes Vacant Markets)</span> // Actual MPOs: <span class="text-white font-cyber">${actualMposCount}</span> (Total: ${totalMposCount}, Vacant: ${vacantMposCount})`;

    const reversed = [...monthlyBreakdown].reverse();

    tbody.innerHTML = reversed.map(mb => {
        return `
        <tr class="hover:bg-cyan-950/30 transition-colors border-b border-slate-800/40">
            <td><strong class="font-cyber text-cyan-300">${fmtMonth(mb.month)}</strong></td>
            <td class="font-cyber text-emerald-300"><span class="inline-block px-2 py-0.5 rounded font-bold text-emerald-300 bg-emerald-950/60 border-l-4 border-emerald-500">📦 ${Math.round(mb.units).toLocaleString()} U</span></td>
            <td><span class="inline-block px-2 py-0.5 rounded text-xs font-bold text-cyan-300 bg-cyan-950/60 border-l-4 border-cyan-500">${Math.round(mb.invoices).toLocaleString()} Inv 🧾</span></td>
            <td><span class="inline-block px-2 py-0.5 rounded text-xs font-bold text-purple-300 bg-purple-950/60 border-l-4 border-purple-500">${Math.round(mb.parties).toLocaleString()} Parties 👥</span></td>
            <td class="font-cyber text-amber-300"><span class="inline-block px-2 py-0.5 rounded font-bold text-amber-300 bg-amber-950/60 border-l-4 border-amber-500">৳ ${Math.round(mb.sales).toLocaleString()}</span></td>
        </tr>`;
    }).join('');

    const ctxModal = document.getElementById("modal-chart");
    if (charts.modal) charts.modal.destroy();

    if (ctxModal && window.Chart) {
        const monthLabels = reversed.map(mb => fmtMonth(mb.month));
        const unitsData = reversed.map(mb => mb.units);
        const invoicesData = reversed.map(mb => mb.invoices);
        const partiesData = reversed.map(mb => mb.parties);
        const salesData = reversed.map(mb => mb.sales);

        charts.modal = new Chart(ctxModal, {
            type: "bar",
            data: {
                labels: monthLabels,
                datasets: [
                    {
                        label: "Units 📦",
                        data: unitsData,
                        backgroundColor: "rgba(16, 185, 129, 0.85)",
                        borderColor: "#10b981",
                        borderWidth: 2,
                        borderRadius: 4,
                        yAxisID: 'yCount'
                    },
                    {
                        label: "Invoices 🧾",
                        data: invoicesData,
                        backgroundColor: "rgba(6, 182, 212, 0.85)",
                        borderColor: "#06b6d4",
                        borderWidth: 2,
                        borderRadius: 4,
                        yAxisID: 'yCount'
                    },
                    {
                        label: "Parties 👥",
                        data: partiesData,
                        backgroundColor: "rgba(168, 85, 247, 0.85)",
                        borderColor: "#a855f7",
                        borderWidth: 2,
                        borderRadius: 4,
                        yAxisID: 'yCount'
                    },
                    {
                        label: "Sales (৳)",
                        data: salesData,
                        backgroundColor: "rgba(251, 191, 36, 0.8)",
                        borderColor: "#fbbf24",
                        borderWidth: 2,
                        borderRadius: 4,
                        yAxisID: 'ySales'
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
                        borderColor: '#fbbf24',
                        borderWidth: 2,
                        titleFont: { family: 'Orbitron', size: 13 }
                    }
                },
                scales: {
                    yCount: {
                        type: 'linear', position: 'left',
                        title: { display: true, text: 'UNITS / INV / PARTIES', color: '#10b981', font: { family: 'Orbitron', size: 11, weight: 'bold' } },
                        grid: { color: "rgba(100, 116, 139, 0.2)" },
                        ticks: {
                            color: '#10b981',
                            precision: 0,
                            font: { family: 'Rajdhani', size: 11, weight: 'bold' }
                        },
                        beginAtZero: true
                    },
                    ySales: {
                        type: 'linear', position: 'right',
                        title: { display: true, text: 'SALES (৳)', color: '#fbbf24', font: { family: 'Orbitron', size: 11, weight: 'bold' } },
                        grid: { display: false },
                        ticks: {
                            color: '#fbbf24',
                            precision: 0,
                            font: { family: 'Rajdhani', size: 11, weight: 'bold' },
                            callback: function(value) {
                                if (value >= 100000) return (value / 1000).toFixed(0) + 'K';
                                if (value >= 1000) return (value / 1000).toFixed(1) + 'K';
                                return value;
                            }
                        },
                        beginAtZero: true
                    },
                    x: { grid: { display: false }, ticks: { color: '#fff', font: { family: 'Rajdhani', size: 13, weight: 'bold' } } }
                }
            },
            plugins: [{
                id: 'inlineBarLabels',
                afterDatasetsDraw(chart) {
                    const { ctx } = chart;
                    ctx.save();
                    ctx.font = 'bold 11px Rajdhani, sans-serif';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'bottom';
                    chart.data.datasets.forEach((dataset, datasetIndex) => {
                        const meta = chart.getDatasetMeta(datasetIndex);
                        if (!meta || meta.hidden) return;
                        const color = dataset.borderColor || '#fff';
                        meta.data.forEach((bar, index) => {
                            const value = dataset.data[index];
                            if (value === 0 || value == null) return;
                            let label;
                            if (datasetIndex === 3) {
                                if (value >= 100000) label = (value / 1000).toFixed(0) + 'K';
                                else if (value >= 1000) label = (value / 1000).toFixed(1) + 'K';
                                else label = Math.round(value).toString();
                            } else {
                                label = Math.round(value).toString();
                            }
                            ctx.fillStyle = color;
                            ctx.fillText(label, bar.x, bar.y - 4);
                        });
                    });
                    ctx.restore();
                }
            }]
        });
    }

    modal.classList.add("active");
}

function openFMDrillModal(fmName) {
    const modal = document.getElementById("drill-modal");
    const title = document.getElementById("modal-title");
    const subtitle = document.getElementById("modal-subtitle");
    const tbody = document.getElementById("modal-tbody");

    if (!modal) return;

    // Month label converter
    const MONTH_NAMES = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
    const fmtMonth = (m) => {
        if (!m) return "";
        const s = String(m);
        const parts = s.includes("-") ? s.split("-") : null;
        if (parts && parts.length === 2) {
            const yr = parts[0].slice(-2);
            const mi = parseInt(parts[1], 10);
            if (mi >= 1 && mi <= 12) return `${MONTH_NAMES[mi - 1]}' ${yr}`;
        }
        return s;
    };

    const fmMpos = CURRENT_AGGREGATED_MPOS.filter(m => (m.fm_name || 'Unknown') === fmName);
    const totalMposCount = fmMpos.length;
    const vacantMposCount = fmMpos.filter(m => m.is_vacant).length;
    const actualMposCount = totalMposCount - vacantMposCount;
    const divisor = actualMposCount > 0 ? actualMposCount : 1;

    // Group monthly breakdowns of all non-vacant MPOs for this FM
    const monthlyMap = {};
    fmMpos.forEach(m => {
        if (m.is_vacant) return;
        (m.monthly_breakdown || []).forEach(mb => {
            const month = mb.month;
            if (!monthlyMap[month]) {
                monthlyMap[month] = { month: month, units: 0, parties: 0, invoices: 0, sales: 0 };
            }
            monthlyMap[month].units += mb.units || mb.quantity || 0;
            monthlyMap[month].parties += mb.parties || 0;
            monthlyMap[month].invoices += mb.invoices || 0;
            monthlyMap[month].sales += mb.sales || 0;
        });
    });

    const months = Object.keys(monthlyMap).sort();
    const monthlyBreakdown = months.map(month => {
        const mb = monthlyMap[month];
        return {
            month: month,
            units: actualMposCount > 0 ? (mb.units / divisor) : 0,
            parties: actualMposCount > 0 ? (mb.parties / divisor) : 0,
            invoices: actualMposCount > 0 ? (mb.invoices / divisor) : 0,
            sales: actualMposCount > 0 ? (mb.sales / divisor) : 0
        };
    });

    const productName = ACTIVE_STRATEGIC_PROD || 'PRODUCT';
    title.innerHTML = `${getProductIcon(productName)} <span class="text-cyan-300">${productName}</span> // 📍 FM: <span class="text-emerald-400 font-bold">${fmName}</span>`;
    subtitle.innerHTML = `<span class="text-purple-300 font-bold">📊 PER MPO TELEMETRY (Excludes Vacant Markets)</span> // Actual MPOs: <span class="text-white font-cyber">${actualMposCount}</span> (Total: ${totalMposCount}, Vacant: ${vacantMposCount})`;

    const reversed = [...monthlyBreakdown].reverse();

    tbody.innerHTML = reversed.map(mb => {
        return `
        <tr class="hover:bg-cyan-950/30 transition-colors border-b border-slate-800/40">
            <td><strong class="font-cyber text-cyan-300">${fmtMonth(mb.month)}</strong></td>
            <td class="font-cyber text-emerald-300"><span class="inline-block px-2 py-0.5 rounded font-bold text-emerald-300 bg-emerald-950/60 border-l-4 border-emerald-500">📦 ${Math.round(mb.units).toLocaleString()} U</span></td>
            <td><span class="inline-block px-2 py-0.5 rounded text-xs font-bold text-cyan-300 bg-cyan-950/60 border-l-4 border-cyan-500">${Math.round(mb.invoices).toLocaleString()} Inv 🧾</span></td>
            <td><span class="inline-block px-2 py-0.5 rounded text-xs font-bold text-purple-300 bg-purple-950/60 border-l-4 border-purple-500">${Math.round(mb.parties).toLocaleString()} Parties 👥</span></td>
            <td class="font-cyber text-amber-300"><span class="inline-block px-2 py-0.5 rounded font-bold text-amber-300 bg-amber-950/60 border-l-4 border-amber-500">৳ ${Math.round(mb.sales).toLocaleString()}</span></td>
        </tr>`;
    }).join('');

    const ctxModal = document.getElementById("modal-chart");
    if (charts.modal) charts.modal.destroy();

    if (ctxModal && window.Chart) {
        const monthLabels = reversed.map(mb => fmtMonth(mb.month));
        const unitsData = reversed.map(mb => mb.units);
        const invoicesData = reversed.map(mb => mb.invoices);
        const partiesData = reversed.map(mb => mb.parties);
        const salesData = reversed.map(mb => mb.sales);

        charts.modal = new Chart(ctxModal, {
            type: "bar",
            data: {
                labels: monthLabels,
                datasets: [
                    {
                        label: "Units 📦",
                        data: unitsData,
                        backgroundColor: "rgba(16, 185, 129, 0.85)",
                        borderColor: "#10b981",
                        borderWidth: 2,
                        borderRadius: 4,
                        yAxisID: 'yCount'
                    },
                    {
                        label: "Invoices 🧾",
                        data: invoicesData,
                        backgroundColor: "rgba(6, 182, 212, 0.85)",
                        borderColor: "#06b6d4",
                        borderWidth: 2,
                        borderRadius: 4,
                        yAxisID: 'yCount'
                    },
                    {
                        label: "Parties 👥",
                        data: partiesData,
                        backgroundColor: "rgba(168, 85, 247, 0.85)",
                        borderColor: "#a855f7",
                        borderWidth: 2,
                        borderRadius: 4,
                        yAxisID: 'yCount'
                    },
                    {
                        label: "Sales (৳)",
                        data: salesData,
                        backgroundColor: "rgba(251, 191, 36, 0.8)",
                        borderColor: "#fbbf24",
                        borderWidth: 2,
                        borderRadius: 4,
                        yAxisID: 'ySales'
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
                        borderColor: '#fbbf24',
                        borderWidth: 2,
                        titleFont: { family: 'Orbitron', size: 13 }
                    }
                },
                scales: {
                    yCount: {
                        type: 'linear', position: 'left',
                        title: { display: true, text: 'UNITS / INV / PARTIES', color: '#10b981', font: { family: 'Orbitron', size: 11, weight: 'bold' } },
                        grid: { color: "rgba(100, 116, 139, 0.2)" },
                        ticks: {
                            color: '#10b981',
                            precision: 0,
                            font: { family: 'Rajdhani', size: 11, weight: 'bold' }
                        },
                        beginAtZero: true
                    },
                    ySales: {
                        type: 'linear', position: 'right',
                        title: { display: true, text: 'SALES (৳)', color: '#fbbf24', font: { family: 'Orbitron', size: 11, weight: 'bold' } },
                        grid: { display: false },
                        ticks: {
                            color: '#fbbf24',
                            precision: 0,
                            font: { family: 'Rajdhani', size: 11, weight: 'bold' },
                            callback: function(value) {
                                if (value >= 100000) return (value / 1000).toFixed(0) + 'K';
                                if (value >= 1000) return (value / 1000).toFixed(1) + 'K';
                                return value;
                            }
                        },
                        beginAtZero: true
                    },
                    x: { grid: { display: false }, ticks: { color: '#fff', font: { family: 'Rajdhani', size: 13, weight: 'bold' } } }
                }
            },
            plugins: [{
                id: 'inlineBarLabels',
                afterDatasetsDraw(chart) {
                    const { ctx } = chart;
                    ctx.save();
                    ctx.font = 'bold 11px Rajdhani, sans-serif';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'bottom';
                    chart.data.datasets.forEach((dataset, datasetIndex) => {
                        const meta = chart.getDatasetMeta(datasetIndex);
                        if (!meta || meta.hidden) return;
                        const color = dataset.borderColor || '#fff';
                        meta.data.forEach((bar, index) => {
                            const value = dataset.data[index];
                            if (value === 0 || value == null) return;
                            let label;
                            if (datasetIndex === 3) {
                                if (value >= 100000) label = (value / 1000).toFixed(0) + 'K';
                                else if (value >= 1000) label = (value / 1000).toFixed(1) + 'K';
                                else label = Math.round(value).toString();
                            } else {
                                label = Math.round(value).toString();
                            }
                            ctx.fillStyle = color;
                            ctx.fillText(label, bar.x, bar.y - 4);
                        });
                    });
                    ctx.restore();
                }
            }]
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
            // Portal: move popover to body and position fixed
            _portalPopover(popover, event.currentTarget);
        } else {
            popover.classList.add("hidden");
        }
    }
}

/** Portal helper: moves a popover to document.body with fixed positioning */
function _portalPopover(popover, triggerBtn) {
    // Move to body if not already there
    if (popover.parentElement !== document.body) {
        document.body.appendChild(popover);
    }
    // Store reference to trigger for click-outside detection
    popover._triggerBtn = triggerBtn;
    // Position relative to trigger button
    const rect = triggerBtn.getBoundingClientRect();
    popover.style.position = 'fixed';
    popover.style.top = (rect.bottom + 4) + 'px';
    popover.style.left = rect.left + 'px';
    popover.style.zIndex = '99999';
    popover.classList.remove('absolute');
    popover.classList.remove('hidden');
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

function printFullStrategicTable() {
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

    const filteredMpos = mpos.filter(m => {
        if (STRATEGIC_FILTERS_SELECTIONS.rank && !STRATEGIC_FILTERS_SELECTIONS.rank.includes(String(m.rank))) return false;
        if (STRATEGIC_FILTERS_SELECTIONS.zone && !STRATEGIC_FILTERS_SELECTIONS.zone.includes(m.zone)) return false;
        if (STRATEGIC_FILTERS_SELECTIONS.fm && !STRATEGIC_FILTERS_SELECTIONS.fm.includes(m.fm_name || 'Unknown')) return false;
        if (STRATEGIC_FILTERS_SELECTIONS.code && !STRATEGIC_FILTERS_SELECTIONS.code.includes(m.mpo_code)) return false;
        if (STRATEGIC_FILTERS_SELECTIONS.market && !STRATEGIC_FILTERS_SELECTIONS.market.includes(m.market)) return false;
        if (STRATEGIC_FILTERS_SELECTIONS.units) {
            const unitsLabel = `${m.units} U`;
            if (!STRATEGIC_FILTERS_SELECTIONS.units.includes(unitsLabel)) return false;
        }
        if (STRATEGIC_FILTERS_SELECTIONS.parties && !STRATEGIC_FILTERS_SELECTIONS.parties.includes(String(m.parties))) return false;
        if (STRATEGIC_FILTERS_SELECTIONS.invoices && !STRATEGIC_FILTERS_SELECTIONS.invoices.includes(String(m.invoices))) return false;
        if (STRATEGIC_FILTERS_SELECTIONS.sales) {
            const salesLabel = formatBDT(m.sales);
            if (!STRATEGIC_FILTERS_SELECTIONS.sales.includes(salesLabel)) return false;
        }
        return true;
    });

    const displayMonth = ACTIVE_STRATEGIC_MONTH === "ALL" ? "ALL" : (MONTH_MAP[ACTIVE_STRATEGIC_MONTH] || ACTIVE_STRATEGIC_MONTH);

    let printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <html>
        <head>
            <title>Strategic Product Performance: ${prodItem.product_name} - ${displayMonth}</title>
            <style>
                body { font-family: 'Segoe UI', Arial, sans-serif; padding: 20px; color: #1e293b; background-color: #ffffff; }
                h1 { margin-bottom: 5px; font-size: 20px; color: #0f172a; }
                h2 { margin-top: 0; font-size: 13px; color: #64748b; font-weight: normal; margin-bottom: 15px; }
                table { width: 100%; border-collapse: collapse; margin-top: 10px; }
                th, td { border: 1px solid #cbd5e1; padding: 4px 8px; text-align: left; font-size: 10px; white-space: nowrap; line-height: 1.2; height: 18px; }
                th { background-color: #f1f5f9; font-weight: 600; color: #334155; text-transform: uppercase; letter-spacing: 0.05em; }
                tr:nth-child(even) { background-color: #f8fafc; }
                tr { height: 22px; }
                .text-right { text-align: right; }
                @media print {
                    button { display: none; }
                    body { padding: 0; }
                    @page { margin: 1cm; }
                }
            </style>
        </head>
        <body>
            <h1>🏆 Strategic Product Performance: ${prodItem.product_name}</h1>
            <h2>Month: ${displayMonth} | Merged Codes: ${(prodItem.merged_codes || []).join(', ')} | Total Records: ${filteredMpos.length}</h2>
            <table>
                <thead>
                    <tr>
                        <th>RANK</th>
                        <th>ZONE</th>
                        <th>FIELD MANAGER</th>
                        <th>MPO MARKET NAME</th>
                        <th class="text-right">QUANTITY (UNIT)</th>
                        <th class="text-right">PARTIES</th>
                        <th class="text-right">INVOICES</th>
                        <th class="text-right">NET SALES (BDT)</th>
                    </tr>
                </thead>
                <tbody>
                    ${filteredMpos.map(m => `
                        <tr>
                            <td>${m.rank}</td>
                            <td>${m.zone}</td>
                            <td>${m.fm_name || 'Unknown'}</td>
                            <td>${m.market}${m.is_vacant ? ' (VACANT)' : ''}</td>
                            <td class="text-right">${Number(m.units).toLocaleString()}</td>
                            <td class="text-right">${Number(m.parties).toLocaleString()}</td>
                            <td class="text-right">${Number(m.invoices).toLocaleString()}</td>
                            <td class="text-right">${formatBDT(m.sales)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
            <script>
                window.onload = function() {
                    window.print();
                    setTimeout(function() { window.close(); }, 500);
                };
            <\/script>
        </body>
        </html>
    `);
    printWindow.document.close();
}

function exportStrategicToCSV() {
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

    const filteredMpos = mpos.filter(m => {
        if (STRATEGIC_FILTERS_SELECTIONS.rank && !STRATEGIC_FILTERS_SELECTIONS.rank.includes(String(m.rank))) return false;
        if (STRATEGIC_FILTERS_SELECTIONS.zone && !STRATEGIC_FILTERS_SELECTIONS.zone.includes(m.zone)) return false;
        if (STRATEGIC_FILTERS_SELECTIONS.fm && !STRATEGIC_FILTERS_SELECTIONS.fm.includes(m.fm_name || 'Unknown')) return false;
        if (STRATEGIC_FILTERS_SELECTIONS.code && !STRATEGIC_FILTERS_SELECTIONS.code.includes(m.mpo_code)) return false;
        if (STRATEGIC_FILTERS_SELECTIONS.market && !STRATEGIC_FILTERS_SELECTIONS.market.includes(m.market)) return false;
        if (STRATEGIC_FILTERS_SELECTIONS.units) {
            const unitsLabel = `${m.units} U`;
            if (!STRATEGIC_FILTERS_SELECTIONS.units.includes(unitsLabel)) return false;
        }
        if (STRATEGIC_FILTERS_SELECTIONS.parties && !STRATEGIC_FILTERS_SELECTIONS.parties.includes(String(m.parties))) return false;
        if (STRATEGIC_FILTERS_SELECTIONS.invoices && !STRATEGIC_FILTERS_SELECTIONS.invoices.includes(String(m.invoices))) return false;
        if (STRATEGIC_FILTERS_SELECTIONS.sales) {
            const salesLabel = formatBDT(m.sales);
            if (!STRATEGIC_FILTERS_SELECTIONS.sales.includes(salesLabel)) return false;
        }
        return true;
    });

    const displayMonth = ACTIVE_STRATEGIC_MONTH === "ALL" ? "ALL" : (MONTH_MAP[ACTIVE_STRATEGIC_MONTH] || ACTIVE_STRATEGIC_MONTH);

    let csvContent = "\uFEFF"; // Add BOM for Excel UTF-8 support
    csvContent += "Rank,Zone,Field Manager,MPO Code,MPO Market Name,Depot,Quantity (Unit),Parties,Invoices,Net Sales (BDT)\n";

    filteredMpos.forEach(m => {
        const row = [
            m.rank,
            `"${m.zone.replace(/'/g, "''").replace(/"/g, '""')}"`,
            `"${(m.fm_name || 'Unknown').replace(/'/g, "''").replace(/"/g, '""')}"`,
            `"${m.mpo_code.replace(/'/g, "''").replace(/"/g, '""')}"`,
            `"${m.market.replace(/'/g, "''").replace(/"/g, '""')}"`,
            `"${(m.depot || 'Unknown').replace(/'/g, "''").replace(/"/g, '""')}"`,
            m.units,
            m.parties,
            m.invoices,
            m.sales
        ].join(",");
        csvContent += row + "\n";
    });

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", `Strategic_Product_${prodItem.product_name.replace(/\s+/g, '_')}_${displayMonth}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function printFMStrategicTable() {
    const list = CURRENT_FILTERED_FMS || [];
    if (list.length === 0) return;
    const activeProd = IS_FM_SYNCED ? ACTIVE_STRATEGIC_PROD : ACTIVE_STRATEGIC_PROD_FM;
    const activeMonth = IS_FM_SYNCED ? ACTIVE_STRATEGIC_MONTH : ACTIVE_STRATEGIC_MONTH_FM;
    const displayMonth = activeMonth === "ALL" ? "ALL" : (MONTH_MAP[activeMonth] || activeMonth);

    let printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <html>
        <head>
            <title>Field Manager Performance Report: ${activeProd} - ${displayMonth}</title>
            <style>
                body { font-family: 'Segoe UI', Arial, sans-serif; padding: 20px; color: #1e293b; background-color: #ffffff; }
                h1 { margin-bottom: 5px; font-size: 20px; color: #0f172a; }
                h2 { margin-top: 0; font-size: 13px; color: #64748b; font-weight: normal; margin-bottom: 15px; }
                table { width: 100%; border-collapse: collapse; margin-top: 10px; }
                th, td { border: 1px solid #cbd5e1; padding: 4px 6px; text-align: left; font-size: 9.5px; white-space: nowrap; height: 18px; line-height: 1.2; }
                th { background-color: #f3e8ff; color: #581c87; font-weight: 600; text-transform: uppercase; }
                tr:nth-child(even) { background-color: #faf5ff; }
                .text-right { text-align: right; }
                @media print {
                    button { display: none; }
                    body { padding: 0; }
                    @page { margin: 1cm; }
                }
            </style>
        </head>
        <body>
            <h1>👔 Field Manager Performance Report: ${activeProd}</h1>
            <h2>Month: ${displayMonth} | Total FMs: ${list.length}</h2>
            <table>
                <thead>
                    <tr>
                        <th>RANK</th>
                        <th>ZONE</th>
                        <th>FIELD MANAGER</th>
                        <th>TOTAL MPOS</th>
                        <th>VACANT</th>
                        <th>ACTUAL MPOS</th>
                        <th class="text-right">TOTAL UNITS</th>
                        <th class="text-right">PER MPO UNITS</th>
                        <th class="text-right">TOTAL PARTIES</th>
                        <th class="text-right">PER MPO PARTIES</th>
                        <th class="text-right">TOTAL INVOICES</th>
                        <th class="text-right">PER MPO INVOICES</th>
                        <th class="text-right">TOTAL VALUE (TK)</th>
                        <th class="text-right">PER MPO VALUE (TK)</th>
                    </tr>
                </thead>
                <tbody>
                    ${list.map(f => `
                        <tr>
                            <td>${f.rank}</td>
                            <td>${f.zone}</td>
                            <td>${f.fm_name}</td>
                            <td>${f.total_mpos}</td>
                            <td>${f.vacant_count}</td>
                            <td>${f.actual_market}</td>
                            <td class="text-right">${Math.round(f.units).toLocaleString()} U</td>
                            <td class="text-right">${Math.round(f.per_mpo_units).toLocaleString()} U</td>
                            <td class="text-right">${Number(f.parties).toLocaleString()}</td>
                            <td class="text-right">${Math.round(f.per_mpo_parties).toLocaleString()}</td>
                            <td class="text-right">${Number(f.invoices).toLocaleString()}</td>
                            <td class="text-right">${Math.round(f.per_mpo_invoices).toLocaleString()}</td>
                            <td class="text-right">${formatBDTRound(f.sales)}</td>
                            <td class="text-right">${formatBDTRound(f.per_mpo_sales)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
            <script>
                window.onload = function() {
                    window.print();
                    setTimeout(function() { window.close(); }, 500);
                };
            <\/script>
        </body>
        </html>
    `);
    printWindow.document.close();
}

function exportFMStrategicToCSV() {
    const list = CURRENT_FILTERED_FMS || [];
    if (list.length === 0) return;
    const activeProd = IS_FM_SYNCED ? ACTIVE_STRATEGIC_PROD : ACTIVE_STRATEGIC_PROD_FM;
    const activeMonth = IS_FM_SYNCED ? ACTIVE_STRATEGIC_MONTH : ACTIVE_STRATEGIC_MONTH_FM;
    const displayMonth = activeMonth === "ALL" ? "ALL" : (MONTH_MAP[activeMonth] || activeMonth);

    let csvContent = "\uFEFF";
    csvContent += "Rank,Zone,Field Manager,Total MPOs,Vacant,Actual MPOs,Total Units,Per MPO Units,Total Parties,Per MPO Parties,Total Invoices,Per MPO Invoices,Total Value (Tk),Per MPO Value (Tk)\n";

    list.forEach(f => {
        const row = [
            f.rank,
            `"${f.zone.replace(/"/g, '""')}"`,
            `"${f.fm_name.replace(/"/g, '""')}"`,
            f.total_mpos,
            f.vacant_count,
            f.actual_market,
            f.units,
            Math.round(f.per_mpo_units),
            f.parties,
            Math.round(f.per_mpo_parties),
            f.invoices,
            Math.round(f.per_mpo_invoices),
            f.sales,
            Math.round(f.per_mpo_sales)
        ].join(',');
        csvContent += row + "\n";
    });

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `Field_Manager_Report_${activeProd.replace(/\s+/g, '_')}_${displayMonth}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function printSHStrategicTable() {
    const list = CURRENT_FILTERED_ZONES || [];
    if (list.length === 0) return;
    const activeProd = IS_SH_SYNCED ? ACTIVE_STRATEGIC_PROD : ACTIVE_STRATEGIC_PROD_SH;
    const activeMonth = IS_SH_SYNCED ? ACTIVE_STRATEGIC_MONTH : ACTIVE_STRATEGIC_MONTH_SH;
    const displayMonth = activeMonth === "ALL" ? "ALL" : (MONTH_MAP[activeMonth] || activeMonth);

    let printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <html>
        <head>
            <title>Sector Head Performance Report: ${activeProd} - ${displayMonth}</title>
            <style>
                body { font-family: 'Segoe UI', Arial, sans-serif; padding: 20px; color: #1e293b; background-color: #ffffff; }
                h1 { margin-bottom: 5px; font-size: 20px; color: #0f172a; }
                h2 { margin-top: 0; font-size: 13px; color: #64748b; font-weight: normal; margin-bottom: 15px; }
                table { width: 100%; border-collapse: collapse; margin-top: 10px; }
                th, td { border: 1px solid #cbd5e1; padding: 4px 6px; text-align: left; font-size: 9.5px; white-space: nowrap; height: 18px; line-height: 1.2; }
                th { background-color: #fef3c7; color: #78350f; font-weight: 600; text-transform: uppercase; }
                tr:nth-child(even) { background-color: #fffbeb; }
                .text-right { text-align: right; }
                @media print {
                    button { display: none; }
                    body { padding: 0; }
                    @page { margin: 1cm; }
                }
            </style>
        </head>
        <body>
            <h1>🏆 Sector Head Performance Report: ${activeProd}</h1>
            <h2>Month: ${displayMonth} | Total Sectors/Zones: ${list.length}</h2>
            <table>
                <thead>
                    <tr>
                        <th>RANK</th>
                        <th>ZONE / SECTOR</th>
                        <th>TOTAL MPOS</th>
                        <th>VACANT</th>
                        <th>ACTUAL MPOS</th>
                        <th class="text-right">TOTAL UNITS</th>
                        <th class="text-right">PER MPO UNITS</th>
                        <th class="text-right">TOTAL PARTIES</th>
                        <th class="text-right">PER MPO PARTIES</th>
                        <th class="text-right">TOTAL INVOICES</th>
                        <th class="text-right">PER MPO INVOICES</th>
                        <th class="text-right">TOTAL VALUE (TK)</th>
                        <th class="text-right">PER MPO VALUE (TK)</th>
                    </tr>
                </thead>
                <tbody>
                    ${list.map(z => `
                        <tr>
                            <td>${z.rank}</td>
                            <td>${z.zone}</td>
                            <td>${z.total_mpos}</td>
                            <td>${z.vacant_count}</td>
                            <td>${z.actual_market}</td>
                            <td class="text-right">${Math.round(z.units).toLocaleString()} U</td>
                            <td class="text-right">${Math.round(z.per_mpo_units).toLocaleString()} U</td>
                            <td class="text-right">${Number(z.parties).toLocaleString()}</td>
                            <td class="text-right">${Math.round(z.per_mpo_parties).toLocaleString()}</td>
                            <td class="text-right">${Number(z.invoices).toLocaleString()}</td>
                            <td class="text-right">${Math.round(z.per_mpo_invoices).toLocaleString()}</td>
                            <td class="text-right">${formatBDTRound(z.sales)}</td>
                            <td class="text-right">${formatBDTRound(z.per_mpo_sales)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
            <script>
                window.onload = function() {
                    window.print();
                    setTimeout(function() { window.close(); }, 500);
                };
            <\/script>
        </body>
        </html>
    `);
    printWindow.document.close();
}

function exportSHStrategicToCSV() {
    const list = CURRENT_FILTERED_ZONES || [];
    if (list.length === 0) return;
    const activeProd = IS_SH_SYNCED ? ACTIVE_STRATEGIC_PROD : ACTIVE_STRATEGIC_PROD_SH;
    const activeMonth = IS_SH_SYNCED ? ACTIVE_STRATEGIC_MONTH : ACTIVE_STRATEGIC_MONTH_SH;
    const displayMonth = activeMonth === "ALL" ? "ALL" : (MONTH_MAP[activeMonth] || activeMonth);

    let csvContent = "\uFEFF";
    csvContent += "Rank,Zone / Sector,Total MPOs,Vacant,Actual MPOs,Total Units,Per MPO Units,Total Parties,Per MPO Parties,Total Invoices,Per MPO Invoices,Total Value (Tk),Per MPO Value (Tk)\n";

    list.forEach(z => {
        const row = [
            z.rank,
            `"${z.zone.replace(/"/g, '""')}"`,
            z.total_mpos,
            z.vacant_count,
            z.actual_market,
            z.units,
            Math.round(z.per_mpo_units),
            z.parties,
            Math.round(z.per_mpo_parties),
            z.invoices,
            Math.round(z.per_mpo_invoices),
            z.sales,
            Math.round(z.per_mpo_sales)
        ].join(',');
        csvContent += row + "\n";
    });

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `Sector_Head_Report_${activeProd.replace(/\s+/g, '_')}_${displayMonth}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function printProductsTable() {
    if (!GLOBAL_DATA || !GLOBAL_DATA.top_50_products) return;
    const products = GLOBAL_DATA.top_50_products;
    const searchQuery = (document.getElementById("search-product")?.value || "").toLowerCase();
    
    let activePill = "all";
    const pills = document.querySelectorAll("[data-filter-prod]");
    pills.forEach(p => {
        if (p.classList.contains("active")) {
            activePill = p.getAttribute("data-filter-prod");
        }
    });

    const filtered = products.filter(p => {
        const code = (p.product_code || "").toLowerCase();
        const name = (p.product_name || "").toLowerCase();
        const matchesQuery = code.includes(searchQuery) || name.includes(searchQuery);
        
        let matchesPill = true;
        if (activePill === "top10") matchesPill = p.rank <= 10;
        if (activePill === "top25") matchesPill = p.rank <= 25;
        
        return matchesQuery && matchesPill;
    });

    let printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <html>
        <head>
            <title>Top Products Performance Report</title>
            <style>
                body { font-family: 'Segoe UI', Arial, sans-serif; padding: 30px; color: #1e293b; background-color: #ffffff; }
                h1 { margin-bottom: 5px; font-size: 24px; color: #0f172a; }
                h2 { margin-top: 0; font-size: 14px; color: #64748b; font-weight: normal; margin-bottom: 25px; }
                table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                th, td { border: 1px solid #e2e8f0; padding: 10px 12px; text-align: left; font-size: 11px; }
                th { background-color: #f8fafc; font-weight: 600; color: #475569; text-transform: uppercase; letter-spacing: 0.05em; }
                tr:nth-child(even) { background-color: #f8fafc; }
                .text-right { text-align: right; }
                .badge { font-family: monospace; font-size: 9px; padding: 2px 4px; border: 1px solid #e2e8f0; border-radius: 4px; background: #f8fafc; margin-left: 5px; text-transform: uppercase; }
                @media print {
                    button { display: none; }
                }
            </style>
        </head>
        <body>
            <h1>🏆 Top Products Performance Report</h1>
            <h2>Total Unique Products: ${filtered.length} | Generated: ${new Date().toLocaleDateString()}</h2>
            <table>
                <thead>
                    <tr>
                        <th>RANK</th>
                        <th>PRODUCT NAME</th>
                        <th>QUANTITY SOLD</th>
                        <th>TOTAL INVOICES</th>
                        <th>UNIQUE PARTIES</th>
                        <th>CONTRIBUTION %</th>
                        <th>SALES VALUE</th>
                    </tr>
                </thead>
                <tbody>
                    ${filtered.map(p => {
                        const codes = p.product_code.split(',').map(c => c.trim().toUpperCase());
                        const tagMap = {
                            "ACO1": "Standard", "ACQ1": "Bonus", "ZA03": "100mg",
                            "ALK1": "60's", "ALM1": "Bonus", "ZA04": "12's", "ZA05": "30's",
                            "ALN1": "30's", "ALP1": "Bonus", "AMK3": "Standard", "AMM3": "Bonus",
                            "ZA11": "10's", "DEJ1": "50mg", "DEM1": "150mg", "MON1": "60's", "MOP1": "Bonus"
                        };
                        const tags = codes.map(c => tagMap[c] || (c.includes('B') ? 'Bonus' : '')).filter(Boolean);
                        const tagsStr = tags.length ? tags.map(t => `<span class="badge">${t}</span>`).join('') : '';

                        return `
                            <tr>
                                <td>#${p.rank}</td>
                                <td><strong>${p.product_name}</strong> ${tagsStr}</td>
                                <td class="text-right">${Number(p.total_quantity).toLocaleString()}</td>
                                <td class="text-right">${Number(p.total_invoices).toLocaleString()}</td>
                                <td class="text-right">${Number(p.total_parties).toLocaleString()}</td>
                                <td class="text-right">${p.contribution_pct}%</td>
                                <td class="text-right">${formatBDT(p.total_sales)}</td>
                            </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
            <script>
                window.onload = function() {
                    window.print();
                    setTimeout(function() { window.close(); }, 500);
                };
            <\/script>
        </body>
        </html>
    `);
    printWindow.document.close();
}

let ACTIVE_PRODUCT_MONTH = "ALL";
let PRODUCT_COLUMNS_LOCKED = true;

function toggleColumnLockProd() {
    PRODUCT_COLUMNS_LOCKED = !PRODUCT_COLUMNS_LOCKED;
    const btn = document.getElementById("btn-lock-columns-prod");
    if (!btn) return;
    if (PRODUCT_COLUMNS_LOCKED) {
        btn.innerHTML = "🔒 Columns Locked";
        btn.classList.remove("bg-slate-800", "border-slate-700");
        btn.classList.add("bg-amber-600/80", "border-amber-500/50");
    } else {
        btn.innerHTML = "🔓 Columns Unlocked";
        btn.classList.remove("bg-amber-600/80", "border-amber-500/50");
        btn.classList.add("bg-slate-800", "border-slate-700");
    }
}

function selectProductMonth(monthVal) {
    ACTIVE_PRODUCT_MONTH = monthVal;
    
    // Update active month title
    const titleEl = document.getElementById("product-active-month-title");
    if (titleEl) {
        titleEl.textContent = monthVal === "ALL" ? "ALL MONTHS" : (MONTH_MAP[monthVal] || monthVal).toUpperCase();
    }
    
    // Re-render Top 50 Products table
    renderProductsTable(GLOBAL_DATA.top_50_products);
    
    // Re-apply any active search or top 10/25 filters
    const searchQuery = (document.getElementById("search-product")?.value || "").toLowerCase();
    let activePill = "all";
    const pills = document.querySelectorAll("[data-filter-prod]");
    pills.forEach(p => {
        if (p.classList.contains("active")) {
            activePill = p.getAttribute("data-filter-prod");
        }
    });
    filterProducts(searchQuery, activePill);
}

function renderProductMonthPills() {
    const monthPillsEl = document.getElementById("product-month-pills");
    if (!monthPillsEl || !GLOBAL_DATA || !GLOBAL_DATA.monthly_trends) return;
    
    // Avoid re-rendering pills if they are already populated to prevent losing focus/flickering
    if (monthPillsEl.children.length > 1) {
        // Just update active state
        const pills = monthPillsEl.querySelectorAll(".prod-month-pill");
        pills.forEach(pill => {
            const m = pill.getAttribute("data-month");
            if (ACTIVE_PRODUCT_MONTH === m) {
                pill.classList.add("active", "bg-cyan-600", "text-white", "shadow-neon-cyan", "font-bold");
                pill.classList.remove("bg-slate-900", "text-slate-300");
            } else {
                pill.classList.remove("active", "bg-cyan-600", "text-white", "shadow-neon-cyan", "font-bold");
                pill.classList.add("bg-slate-900", "text-slate-300");
            }
        });
        return;
    }
    
    const months = GLOBAL_DATA.monthly_trends.map(t => t.month);
    const sortedMonths = [...months].sort((a, b) => b.localeCompare(a));
    
    const minMonth = sortedMonths[sortedMonths.length - 1];
    const maxMonth = sortedMonths[0];
    const minLabel = (MONTH_MAP[minMonth] || minMonth).toUpperCase();
    const maxLabel = (MONTH_MAP[maxMonth] || maxMonth).toUpperCase();
    
    monthPillsEl.innerHTML = `
        <button class="prod-month-pill ${ACTIVE_PRODUCT_MONTH === 'ALL' ? 'active bg-cyan-600 text-white shadow-neon-cyan font-bold' : 'bg-slate-900 text-slate-300 hover:bg-slate-800'} px-3 py-1.5 rounded font-tech text-xs" data-month="ALL" onclick="selectProductMonth('ALL')">ALL MONTHS (${minLabel} - ${maxLabel})</button>
        ${sortedMonths.map(m => {
            const monthLabel = MONTH_MAP[m] || m;
            return `
                <button class="prod-month-pill ${ACTIVE_PRODUCT_MONTH === m ? 'active bg-cyan-600 text-white shadow-neon-cyan font-bold' : 'bg-slate-900 text-slate-300 hover:bg-slate-800'} px-3 py-1.5 rounded font-tech text-xs" data-month="${m}" onclick="selectProductMonth('${m}')">[ ${monthLabel} ]</button>
            `;
        }).join('')}
    `;
}

/* ==========================================================================
   COPIED STRATEGIC TABLE HANDLERS & FILTERS
   ========================================================================== */
function toggleFilterPopoverCopy(event, colName) {
    event.stopPropagation();
    
    // Hide all other popovers
    const allPopovers = document.querySelectorAll('[id^="popover-"]');
    allPopovers.forEach(p => {
        if (p.id !== `popover-${colName}-copy`) {
            p.classList.add("hidden");
        }
    });

    const popover = document.getElementById(`popover-${colName}-copy`);
    if (popover) {
        const isHidden = popover.classList.contains("hidden");
        if (isHidden) {
            if (STRATEGIC_FILTERS_SELECTIONS_COPY[colName]) {
                TEMP_FILTERS_SELECTIONS_COPY[colName] = new Set(STRATEGIC_FILTERS_SELECTIONS_COPY[colName]);
            } else {
                TEMP_FILTERS_SELECTIONS_COPY[colName] = null;
            }
            populateFilterOptionsCopy(colName);
            _portalPopover(popover, event.currentTarget);
        } else {
            popover.classList.add("hidden");
        }
    }
}

function populateFilterOptionsCopy(colName) {
    const optionsDiv = document.getElementById(`options-${colName}-copy`);
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

    // Group by FM first
    const fmsMap = {};
    mpos.forEach(m => {
        const f = m.fm_name || 'Unknown';
        if (!fmsMap[f]) {
            fmsMap[f] = {
                fm_name: f,
                zone: m.zone || 'Unknown',
                total_mpos: 0,
                vacant_count: 0,
                actual_market: 0,
                units: 0,
                parties: 0,
                invoices: 0,
                sales: 0
            };
        }
        fmsMap[f].total_mpos += 1;
        if (m.is_vacant) {
            fmsMap[f].vacant_count += 1;
        } else {
            fmsMap[f].units += m.units || 0;
            fmsMap[f].parties += m.parties || 0;
            fmsMap[f].invoices += m.invoices || 0;
            fmsMap[f].sales += m.sales || 0;
        }
    });

    const fmsList = Object.values(fmsMap).map(f => {
        f.actual_market = f.total_mpos - f.vacant_count;
        return f;
    });

    fmsList.sort((a, b) => b.units - a.units);
    fmsList.forEach((f, idx) => {
        f.rank = idx + 1;
    });

    const uniqueValues = new Set();
    fmsList.forEach(f => {
        let val = "";
        if (colName === "rank") val = String(f.rank);
        else if (colName === "zone") val = f.zone;
        else if (colName === "fm") val = f.fm_name;
        else if (colName === "total_mpos") val = String(f.total_mpos);
        else if (colName === "vacant_count") val = String(f.vacant_count);
        else if (colName === "actual_market") val = String(f.actual_market);
        else if (colName === "units") val = `${Math.round(f.units).toLocaleString()} U`;
        else if (colName === "parties") val = `${f.parties}`;
        else if (colName === "invoices") val = `${f.invoices}`;
        else if (colName === "sales") val = formatBDTRound(f.sales);
        
        if (val) uniqueValues.add(val);
    });

    const valuesArray = Array.from(uniqueValues).sort((a, b) => {
        const numA = parseFloat(a.replace(/[^0-9.]/g, ''));
        const numB = parseFloat(b.replace(/[^0-9.]/g, ''));
        if (!isNaN(numA) && !isNaN(numB)) return numA - numB;
        return a.localeCompare(b);
    });

    if (!TEMP_FILTERS_SELECTIONS_COPY[colName]) {
        if (STRATEGIC_FILTERS_SELECTIONS_COPY[colName]) {
            TEMP_FILTERS_SELECTIONS_COPY[colName] = new Set(STRATEGIC_FILTERS_SELECTIONS_COPY[colName]);
        } else {
            TEMP_FILTERS_SELECTIONS_COPY[colName] = new Set(valuesArray);
        }
    }

    optionsDiv.innerHTML = valuesArray.map(val => {
        const isChecked = TEMP_FILTERS_SELECTIONS_COPY[colName].has(val);
        return `
            <label class="flex items-center gap-2 cursor-pointer py-0.5 hover:bg-slate-900 rounded px-1 w-full text-slate-300 hover:text-white">
                <input type="checkbox" class="option-chk-item" value="${val}" ${isChecked ? 'checked' : ''} onchange="handleOptionCheckboxChangeCopy('${colName}', '${val}', this.checked)">
                <span class="truncate" title="${val}">${val}</span>
            </label>
        `;
    }).join('');
}

function handleOptionCheckboxChangeCopy(colName, value, checked) {
    if (!TEMP_FILTERS_SELECTIONS_COPY[colName]) {
        TEMP_FILTERS_SELECTIONS_COPY[colName] = new Set();
    }
    if (checked) {
        TEMP_FILTERS_SELECTIONS_COPY[colName].add(value);
    } else {
        TEMP_FILTERS_SELECTIONS_COPY[colName].delete(value);
    }
}

function searchFilterOptionsCopy(colName, searchVal) {
    const optionsDiv = document.getElementById(`options-${colName}-copy`);
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

function selectAllFilterOptionsCopy(colName, selectAll) {
    const optionsDiv = document.getElementById(`options-${colName}-copy`);
    if (!optionsDiv) return;
    const checkboxes = optionsDiv.querySelectorAll('input[type="checkbox"]');
    
    checkboxes.forEach(chk => {
        const label = chk.closest('label');
        if (label && label.style.display !== "none") {
            chk.checked = selectAll;
            handleOptionCheckboxChangeCopy(colName, chk.value, selectAll);
        }
    });
}

function applyFilterCopy(colName) {
    STRATEGIC_FILTERS_SELECTIONS_COPY[colName] = TEMP_FILTERS_SELECTIONS_COPY[colName] ? Array.from(TEMP_FILTERS_SELECTIONS_COPY[colName]) : null;
    
    const popover = document.getElementById(`popover-${colName}-copy`);
    if (popover) popover.classList.add("hidden");

    STRATEGIC_PAGE_COPY = 1;
    renderStrategicMPOTable();
}

function cancelFilterCopy(colName) {
    const popover = document.getElementById(`popover-${colName}-copy`);
    if (popover) popover.classList.add("hidden");
}

function clearColumnFilterCopy(colName) {
    STRATEGIC_FILTERS_SELECTIONS_COPY[colName] = null;
    TEMP_FILTERS_SELECTIONS_COPY[colName] = null;
    const popover = document.getElementById(`popover-${colName}-copy`);
    if (popover) popover.classList.add("hidden");
    STRATEGIC_PAGE_COPY = 1;
    renderStrategicMPOTable();
}

function toggleColumnLockCopy() {
    COLUMNS_LOCKED_COPY = !COLUMNS_LOCKED_COPY;
    const btn = document.getElementById("btn-lock-columns-copy");
    if (btn) {
        if (COLUMNS_LOCKED_COPY) {
            btn.innerHTML = "🔒 Columns Locked";
            btn.className = "px-3.5 py-2 rounded bg-amber-600/80 border border-amber-500/50 text-white font-tech text-xs font-bold hover:bg-amber-700 transition-all flex items-center gap-1.5";
            removeResizersCopy();
        } else {
            btn.innerHTML = "🔓 Resizing Unlocked";
            btn.className = "px-3.5 py-2 rounded bg-emerald-600/80 border border-emerald-500/50 text-white font-tech text-xs font-bold hover:bg-emerald-700 transition-all flex items-center gap-1.5 shadow-neon-cyan";
            createResizersCopy();
        }
    }
}

function createResizersCopy() {
    const table = document.getElementById("table-strategic-mpos-copy");
    if (!table) return;
    const cols = table.querySelectorAll("th");
    cols.forEach(col => {
        const resizer = document.createElement("div");
        resizer.classList.add("resizer");
        resizer.style.height = table.offsetHeight + "px";
        col.appendChild(resizer);
        col.style.position = "relative";
        
        let x = 0;
        let w = 0;
        
        const mouseDownHandler = function(e) {
            x = e.clientX;
            const styles = window.getComputedStyle(col);
            w = parseInt(styles.width, 10);
            document.addEventListener("mousemove", mouseMoveHandler);
            document.addEventListener("mouseup", mouseUpHandler);
            resizer.classList.add("resizing");
        };
        
        const mouseMoveHandler = function(e) {
            const dx = e.clientX - x;
            col.style.width = `${w + dx}px`;
        };
        
        const mouseUpHandler = function() {
            document.removeEventListener("mousemove", mouseMoveHandler);
            document.removeEventListener("mouseup", mouseUpHandler);
            resizer.classList.remove("resizing");
        };
        
        resizer.addEventListener("mousedown", mouseDownHandler);
    });
}

function removeResizersCopy() {
    const table = document.getElementById("table-strategic-mpos-copy");
    if (!table) return;
    const resizers = table.querySelectorAll(".resizer");
    resizers.forEach(r => r.remove());
}

// Global click outside popovers handler for all sections
// (Handled by the unified listener in initializeDashboard)

/* ==========================================================================
   COPIED STRATEGIC TABLE 2 HANDLERS & FILTERS (Copy 2)
   ========================================================================== */
function toggleFilterPopoverCopy2(event, colName) {
    event.stopPropagation();
    
    // Hide all other popovers
    const allPopovers = document.querySelectorAll('[id^="popover-"]');
    allPopovers.forEach(p => {
        if (p.id !== `popover-${colName}-copy2`) {
            p.classList.add("hidden");
        }
    });

    const popover = document.getElementById(`popover-${colName}-copy2`);
    if (popover) {
        const isHidden = popover.classList.contains("hidden");
        if (isHidden) {
            if (STRATEGIC_FILTERS_SELECTIONS_COPY2[colName]) {
                TEMP_FILTERS_SELECTIONS_COPY2[colName] = new Set(STRATEGIC_FILTERS_SELECTIONS_COPY2[colName]);
            } else {
                TEMP_FILTERS_SELECTIONS_COPY2[colName] = null;
            }
            populateFilterOptionsCopy2(colName);
            _portalPopover(popover, event.currentTarget);
        } else {
            popover.classList.add("hidden");
        }
    }
}

function populateFilterOptionsCopy2(colName) {
    const optionsDiv = document.getElementById(`options-${colName}-copy2`);
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

    if (!TEMP_FILTERS_SELECTIONS_COPY2[colName]) {
        if (STRATEGIC_FILTERS_SELECTIONS_COPY2[colName]) {
            TEMP_FILTERS_SELECTIONS_COPY2[colName] = new Set(STRATEGIC_FILTERS_SELECTIONS_COPY2[colName]);
        } else {
            TEMP_FILTERS_SELECTIONS_COPY2[colName] = new Set(valuesArray);
        }
    }

    optionsDiv.innerHTML = valuesArray.map(val => {
        const isChecked = TEMP_FILTERS_SELECTIONS_COPY2[colName].has(val);
        return `
            <label class="flex items-center gap-2 cursor-pointer py-0.5 hover:bg-slate-900 rounded px-1 w-full text-slate-300 hover:text-white">
                <input type="checkbox" class="option-chk-item" value="${val}" ${isChecked ? 'checked' : ''} onchange="handleOptionCheckboxChangeCopy2('${colName}', '${val}', this.checked)">
                <span class="truncate" title="${val}">${val}</span>
            </label>
        `;
    }).join('');
}

function handleOptionCheckboxChangeCopy2(colName, value, checked) {
    if (!TEMP_FILTERS_SELECTIONS_COPY2[colName]) {
        TEMP_FILTERS_SELECTIONS_COPY2[colName] = new Set();
    }
    if (checked) {
        TEMP_FILTERS_SELECTIONS_COPY2[colName].add(value);
    } else {
        TEMP_FILTERS_SELECTIONS_COPY2[colName].delete(value);
    }
}

function searchFilterOptionsCopy2(colName, searchVal) {
    const optionsDiv = document.getElementById(`options-${colName}-copy2`);
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

function selectAllFilterOptionsCopy2(colName, selectAll) {
    const optionsDiv = document.getElementById(`options-${colName}-copy2`);
    if (!optionsDiv) return;
    const checkboxes = optionsDiv.querySelectorAll('input[type="checkbox"]');
    
    checkboxes.forEach(chk => {
        const label = chk.closest('label');
        if (label && label.style.display !== "none") {
            chk.checked = selectAll;
            handleOptionCheckboxChangeCopy2(colName, chk.value, selectAll);
        }
    });
}

function applyFilterCopy2(colName) {
    STRATEGIC_FILTERS_SELECTIONS_COPY2[colName] = TEMP_FILTERS_SELECTIONS_COPY2[colName] ? Array.from(TEMP_FILTERS_SELECTIONS_COPY2[colName]) : null;
    
    const popover = document.getElementById(`popover-${colName}-copy2`);
    if (popover) popover.classList.add("hidden");

    STRATEGIC_PAGE_COPY2 = 1;
    renderStrategicMPOTable();
}

// Fixed function reference in HTML
function selectAllFilterOptionsCopy2Helper(colName, selectAll) {
    selectAllFilterOptionsCopy2(colName, selectAll);
}

function cancelFilterCopy2(colName) {
    const popover = document.getElementById(`popover-${colName}-copy2`);
    if (popover) popover.classList.add("hidden");
}

function clearColumnFilterCopy2(colName) {
    STRATEGIC_FILTERS_SELECTIONS_COPY2[colName] = null;
    TEMP_FILTERS_SELECTIONS_COPY2[colName] = null;
    const popover = document.getElementById(`popover-${colName}-copy2`);
    if (popover) popover.classList.add("hidden");
    STRATEGIC_PAGE_COPY2 = 1;
    renderStrategicMPOTable();
}

function toggleColumnLockCopy2() {
    COLUMNS_LOCKED_COPY2 = !COLUMNS_LOCKED_COPY2;
    const btn = document.getElementById("btn-lock-columns-copy2");
    if (btn) {
        if (COLUMNS_LOCKED_COPY2) {
            btn.innerHTML = "🔒 Columns Locked";
            btn.className = "px-3.5 py-2 rounded bg-amber-600/80 border border-amber-500/50 text-white font-tech text-xs font-bold hover:bg-amber-700 transition-all flex items-center gap-1.5";
            removeResizersCopy2();
        } else {
            btn.innerHTML = "🔓 Resizing Unlocked";
            btn.className = "px-3.5 py-2 rounded bg-emerald-600/80 border border-emerald-500/50 text-white font-tech text-xs font-bold hover:bg-emerald-700 transition-all flex items-center gap-1.5 shadow-neon-cyan";
            createResizersCopy2();
        }
    }
}

function createResizersCopy2() {
    const table = document.getElementById("table-strategic-mpos-copy2");
    if (!table) return;
    const cols = table.querySelectorAll("th");
    cols.forEach(col => {
        const resizer = document.createElement("div");
        resizer.classList.add("resizer");
        resizer.style.height = table.offsetHeight + "px";
        col.appendChild(resizer);
        col.style.position = "relative";
        
        let x = 0;
        let w = 0;
        
        const mouseDownHandler = function(e) {
            x = e.clientX;
            const styles = window.getComputedStyle(col);
            w = parseInt(styles.width, 10);
            document.addEventListener("mousemove", mouseMoveHandler);
            document.addEventListener("mouseup", mouseUpHandler);
            resizer.classList.add("resizing");
        };
        
        const mouseMoveHandler = function(e) {
            const dx = e.clientX - x;
            col.style.width = `${w + dx}px`;
        };
        
        const mouseUpHandler = function() {
            document.removeEventListener("mousemove", mouseMoveHandler);
            document.removeEventListener("mouseup", mouseUpHandler);
            resizer.classList.remove("resizing");
        };
        
        resizer.addEventListener("mousedown", mouseDownHandler);
    });
}

function removeResizersCopy2() {
    const table = document.getElementById("table-strategic-mpos-copy2");
    if (!table) return;
    const resizers = table.querySelectorAll(".resizer");
    resizers.forEach(r => r.remove());
}

/* ==========================================================================
   STRATEGIC PRODUCT MULTI-SELECT DROPDOWN FILTER
   ========================================================================== */
function toggleProdGroupDropdown(event, suffix) {
    if (event) event.stopPropagation();
    const panel = document.getElementById(`prod-group-dropdown-panel${suffix}`);
    if (panel) {
        const isHidden = panel.classList.contains("hidden");
        if (isHidden) {
            // Portal: move to body with fixed positioning
            const triggerBtn = event ? event.currentTarget : null;
            if (triggerBtn) {
                if (panel.parentElement !== document.body) {
                    document.body.appendChild(panel);
                }
                panel._triggerBtn = triggerBtn;
                panel._wrapperSuffix = suffix;
                const rect = triggerBtn.getBoundingClientRect();
                panel.style.position = 'fixed';
                panel.style.top = (rect.bottom + 8) + 'px';
                panel.style.maxWidth = '280px';
                panel.style.width = '280px';
                
                // Keep dropdown within viewport bounds on small mobile screens
                let rightPos = (window.innerWidth - rect.right);
                if (rightPos < 10) rightPos = 10;
                panel.style.left = '';
                panel.style.right = rightPos + 'px';
                panel.style.zIndex = '99999';
                panel.classList.remove('absolute');
            }
            panel.classList.remove("hidden");
        } else {
            panel.classList.add("hidden");
        }
    }
}

// Global click handler to close dropdown when clicking outside
document.addEventListener("click", function(event) {
    ["", "-copy", "-copy2"].forEach(suffix => {
        const panel = document.getElementById(`prod-group-dropdown-panel${suffix}`);
        if (panel && !panel.classList.contains("hidden")) {
            // Check if click is inside the panel
            if (panel.contains(event.target)) return;
            // Check if click is on the trigger button
            if (panel._triggerBtn && panel._triggerBtn.contains(event.target)) return;
            panel.classList.add("hidden");
        }
    });
});

function updateProdGroupDropdownUI(keys) {
    ["", "-copy", "-copy2"].forEach(suffix => {
        const checkboxesDiv = document.getElementById(`prod-group-checkboxes${suffix}`);
        const labelSpan = document.getElementById(`selected-prod-group-label${suffix}`);
        if (!checkboxesDiv) return;

        // Build list of checkboxes
        checkboxesDiv.innerHTML = keys.map(k => {
            const isChecked = ACTIVE_STRATEGIC_PRODS.includes(k);
            return `
                <label class="flex items-center gap-2 cursor-pointer py-1 hover:bg-slate-900 rounded px-1.5 transition-colors">
                    <input type="checkbox" class="prod-group-chk${suffix}" value="${k}" ${isChecked ? 'checked' : ''}>
                    <span class="truncate" title="${k}">${k}</span>
                </label>
            `;
        }).join('');

        // Update label
        if (labelSpan) {
            if (ACTIVE_STRATEGIC_PRODS.length === keys.length) {
                labelSpan.textContent = "ALL PRODUCTS SELECTED";
                if (suffix === "") labelSpan.className = "truncate max-w-[200px] text-cyan-400 font-bold";
                else if (suffix === "-copy") labelSpan.className = "truncate max-w-[200px] text-purple-400 font-bold";
                else labelSpan.className = "truncate max-w-[200px] text-amber-400 font-bold";
            } else if (ACTIVE_STRATEGIC_PRODS.length === 1) {
                labelSpan.textContent = ACTIVE_STRATEGIC_PRODS[0];
                labelSpan.className = "truncate max-w-[200px] text-slate-200";
            } else {
                labelSpan.textContent = `${ACTIVE_STRATEGIC_PRODS.length} PRODUCTS SELECTED`;
                if (suffix === "") labelSpan.className = "truncate max-w-[200px] text-cyan-400 font-bold";
                else if (suffix === "-copy") labelSpan.className = "truncate max-w-[200px] text-purple-400 font-bold";
                else labelSpan.className = "truncate max-w-[200px] text-amber-400 font-bold";
            }
        }
    });
}

function selectAllProdGroups(status, suffix) {
    const chks = document.querySelectorAll(`.prod-group-chk${suffix}`);
    chks.forEach(chk => {
        chk.checked = status;
    });
}

function applyProdGroupSelection(suffix) {
    const chks = document.querySelectorAll(`.prod-group-chk${suffix}`);
    const selected = [];
    chks.forEach(chk => {
        if (chk.checked) selected.push(chk.value);
    });

    if (selected.length === 0) {
        alert("Please select at least one product group.");
        return;
    }

    ACTIVE_STRATEGIC_PRODS = selected;
    if (selected.length > 0) {
        ACTIVE_STRATEGIC_PROD = selected[0];
    }

    // Hide dropdown panel
    const panel = document.getElementById(`prod-group-dropdown-panel${suffix}`);
    if (panel) panel.classList.add("hidden");

    // Reset pagination
    STRATEGIC_PAGE = 1;
    STRATEGIC_PAGE_COPY = 1;
    STRATEGIC_PAGE_COPY2 = 1;

    // Reset all column filters
    STRATEGIC_FILTERS_SELECTIONS = { rank: null, zone: null, fm: null, code: null, market: null, units: null, parties: null, invoices: null, sales: null };
    STRATEGIC_FILTERS_SELECTIONS_COPY = { rank: null, zone: null, fm: null, code: null, market: null, units: null, parties: null, invoices: null, sales: null };
    STRATEGIC_FILTERS_SELECTIONS_COPY2 = { rank: null, zone: null, fm: null, code: null, market: null, units: null, parties: null, invoices: null, sales: null };
    TEMP_FILTERS_SELECTIONS = {};
    TEMP_FILTERS_SELECTIONS_COPY = {};
    TEMP_FILTERS_SELECTIONS_COPY2 = {};

    renderStrategic6Products();
}

function toggleLightTheme() {
    document.body.classList.toggle("light-theme");
    const isLight = document.body.classList.contains("light-theme");
    const btn = document.getElementById("btn-theme-toggle");
    if (btn) {
        if (isLight) {
            btn.innerHTML = "<span>🌙</span> Dark Theme";
            localStorage.setItem("dashboard-theme", "light");
        } else {
            btn.innerHTML = "<span>💡</span> Light Theme";
            localStorage.setItem("dashboard-theme", "dark");
        }
    }
}

// Load theme on startup
document.addEventListener("DOMContentLoaded", () => {
    const savedTheme = localStorage.getItem("dashboard-theme");
    if (savedTheme === "light") {
        document.body.classList.add("light-theme");
        const btn = document.getElementById("btn-theme-toggle");
        if (btn) btn.innerHTML = "<span>🌙</span> Dark Theme";
    }
});


