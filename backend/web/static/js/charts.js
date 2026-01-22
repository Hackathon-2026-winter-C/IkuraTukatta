// backend/web/static/js/charts.js
const dataTag = document.getElementById("expense-data");
const raw = dataTag ? JSON.parse(dataTag.textContent) : [];

const chartEl = document.getElementById("expense-chart");
if (!chartEl) {
  // canvas が無いページなら何もしない
} else if (raw.length === 0) {
  const empty = document.getElementById("chart-empty");
  if (empty) empty.hidden = false;
} else if (typeof Chart === "undefined") {
  console.error("Chart.js is not loaded");
} else {
  const totals = new Map();
  const colors = new Map();

  for (const e of raw) {
    const key = e.category || "Unknown";
    const amt = Number(e.amount) || 0;
    totals.set(key, (totals.get(key) || 0) + amt);
    if (!colors.has(key) && e.categoryColor) {
      colors.set(key, e.categoryColor);
    }
  }

  const labels = Array.from(totals.keys());
  const values = labels.map((k) => totals.get(k));
  const bg = labels.map((k) => colors.get(k) || "#999999");

  new Chart(chartEl, {
    type: "doughnut",
    data: {
      labels,
      datasets: [
        {
          data: values,
          backgroundColor: bg,
          borderWidth: 1,
        },
      ],
    },
    options: {
      cutout: "60%",
      plugins: {
        legend: { position: "bottom" },
      },
    },
  });
}
