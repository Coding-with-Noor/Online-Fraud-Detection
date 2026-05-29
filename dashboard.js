// ============================================================
// dashboard.js — Chart.js charts + table search filter
// All chart data comes from DASH_DATA injected by Flask/Jinja2
// ============================================================

// Shared Chart.js defaults — dark theme
Chart.defaults.color       = "#7d8590";
Chart.defaults.borderColor = "#30363d";
Chart.defaults.font.family = "'Space Grotesk', sans-serif";
Chart.defaults.font.size   = 12;


// ============================================================
// 1. DOUGHNUT CHART  (Fraud vs Safe split)
// ============================================================
function buildDoughnutChart() {
    const ctx = document.getElementById("doughnutChart");
    if (!ctx) return;

    new Chart(ctx, {
        type: "doughnut",
        data: {
            labels:   ["Fraud", "Legitimate"],
            datasets: [{
                data:            [DASH_DATA.fraudCount, DASH_DATA.safeCount],
                backgroundColor: ["#f85149", "#3fb950"],
                borderColor:     ["#f85149", "#3fb950"],
                borderWidth:     2,
                hoverOffset:     6
            }]
        },
        options: {
            cutout: "72%",
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function (ctx) {
                            const total = DASH_DATA.fraudCount + DASH_DATA.safeCount;
                            const pct   = total > 0 ? ((ctx.raw / total) * 100).toFixed(1) : 0;
                            return ` ${ctx.label}: ${ctx.raw} (${pct}%)`;
                        }
                    }
                }
            },
            animation: { duration: 900 }
        }
    });
}


// ============================================================
// 2. BAR CHART  (Fraud count by transaction type)
// ============================================================
function buildTypeBarChart() {
    const ctx = document.getElementById("typeBarChart");
    if (!ctx) return;

    new Chart(ctx, {
        type: "bar",
        data: {
            labels:   DASH_DATA.typeLabels,
            datasets: [
                {
                    label:           "Total",
                    data:            DASH_DATA.typeTotals,
                    backgroundColor: "rgba(96,165,250,0.25)",
                    borderColor:     "#60a5fa",
                    borderWidth:     1.5,
                    borderRadius:    5
                },
                {
                    label:           "Fraud",
                    data:            DASH_DATA.typeFrauds,
                    backgroundColor: "rgba(248,81,73,0.65)",
                    borderColor:     "#f85149",
                    borderWidth:     1.5,
                    borderRadius:    5
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: "top", labels: { boxWidth: 12, padding: 15, color: "#7d8590" } },
                tooltip: { mode: "index", intersect: false }
            },
            scales: {
                x: { grid: { color: "rgba(255,255,255,0.04)" }, ticks: { color: "#7d8590" } },
                y: { grid: { color: "rgba(255,255,255,0.04)" }, ticks: { color: "#7d8590", precision: 0 }, beginAtZero: true }
            },
            animation: { duration: 800 }
        }
    });
}


// ============================================================
// 3. LINE CHART  (7-day trend)
// ============================================================
function buildTrendLineChart() {
    const ctx = document.getElementById("trendLineChart");
    if (!ctx || !DASH_DATA.trendDays || DASH_DATA.trendDays.length === 0) return;

    new Chart(ctx, {
        type: "line",
        data: {
            labels:   DASH_DATA.trendDays,
            datasets: [
                {
                    label: "Total Checks", data: DASH_DATA.trendTotals,
                    borderColor: "#60a5fa", backgroundColor: "rgba(96,165,250,0.1)",
                    borderWidth: 2, pointRadius: 4, pointBackgroundColor: "#60a5fa",
                    tension: 0.3, fill: true
                },
                {
                    label: "Fraud Detected", data: DASH_DATA.trendFrauds,
                    borderColor: "#f85149", backgroundColor: "rgba(248,81,73,0.08)",
                    borderWidth: 2, pointRadius: 4, pointBackgroundColor: "#f85149",
                    tension: 0.3, fill: true
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: "top", labels: { boxWidth: 12, padding: 15, color: "#7d8590" } },
                tooltip: { mode: "index", intersect: false }
            },
            scales: {
                x: { grid: { color: "rgba(255,255,255,0.04)" }, ticks: { color: "#7d8590" } },
                y: { grid: { color: "rgba(255,255,255,0.04)" }, ticks: { color: "#7d8590", precision: 0 }, beginAtZero: true }
            },
            animation: { duration: 900 }
        }
    });
}


// ============================================================
// 4. TABLE SEARCH FILTER
// ============================================================
function setupTableSearch() {
    const input = document.getElementById("tableSearch");
    const table = document.getElementById("txTable");
    if (!input || !table) return;

    input.addEventListener("keyup", function () {
        const query = this.value.toLowerCase().trim();
        const rows  = table.querySelectorAll("tbody tr");
        rows.forEach(function (row) {
            row.style.display = row.textContent.toLowerCase().includes(query) ? "" : "none";
        });
    });
}


// ============================================================
// 5. SIDEBAR ACTIVE LINK on scroll
// ============================================================
function setupSidebarScroll() {
    const sections = document.querySelectorAll("section[id]");
    const links    = document.querySelectorAll(".sidebar-link");

    window.addEventListener("scroll", function () {
        let current = "";
        sections.forEach(function (section) {
            if (section.getBoundingClientRect().top <= 120) current = section.id;
        });
        links.forEach(function (link) {
            link.classList.remove("active");
            if (link.getAttribute("href") === "#" + current) link.classList.add("active");
        });
    });
}


// ============================================================
// INIT
// ============================================================
document.addEventListener("DOMContentLoaded", function () {
    buildDoughnutChart();
    buildTypeBarChart();
    buildTrendLineChart();
    setupTableSearch();
    setupSidebarScroll();
});
