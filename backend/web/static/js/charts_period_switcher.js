// charts_period_switcher.js

// グローバル変数として生データを保持
const dataTag = document.getElementById("expense-data");
const rawExpenseData = dataTag ? JSON.parse(dataTag.textContent) : [];

// 期間に基づいてデータを処理する関数
function processDataForPeriod(period, rawData) {
  const totals = new Map();
  const colors = new Map();

  // 現在の年と月を取得
  const now = new Date();
  const currentYear = now.getFullYear();
  const currentMonth = now.getMonth(); // 0-11

  for (const e of rawData) {
    const expenseDate = new Date(e.date);
    const expenseYear = expenseDate.getFullYear();
    const expenseMonth = expenseDate.getMonth();

    // 期間によるフィルタリング
    let shouldInclude = false;
    if (period === "year" && expenseYear === currentYear) {
      shouldInclude = true;
    } else if (period === "month" && expenseYear === currentYear && expenseMonth === currentMonth) {
      shouldInclude = true;
    }

    if (shouldInclude) {
      const key = e.category || "Unknown";
      const amt = Number(e.amount) || 0;
      totals.set(key, (totals.get(key) || 0) + amt);
      if (!colors.has(key) && e.categoryColor) {
        colors.set(key, e.categoryColor);
      }
    }
  }

  const labels = Array.from(totals.keys());
  const values = labels.map((k) => totals.get(k));
  const bg = labels.map((k) => colors.get(k) || "#999999");
  const totalAmount = values.reduce((sum, current) => sum + current, 0);
  const formattedTotalAmount = `¥${totalAmount.toLocaleString()}`;

  return { labels, values, bg, formattedTotalAmount };
}

// ラジオボタンの変更を処理するメイン関数
function handlePeriodChange() {
  const checked = document.querySelector('input[name="chart-period"]:checked');
  const selectedPeriod = checked ? checked.value : "year";
  const { labels, values, bg, formattedTotalAmount } = processDataForPeriod(selectedPeriod, rawExpenseData);

  // charts.js と charts_categorys.js で定義された関数を呼び出す
  if (window.updateChart) {
    window.updateChart(labels, values, bg, formattedTotalAmount);
  }
  if (window.updateCategoryList) {
    window.updateCategoryList(labels, values, bg);
  }
}

// イベントリスナーの登録
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll('input[name="chart-period"]').forEach((radio) => {
    radio.addEventListener("change", handlePeriodChange);
  });

  handlePeriodChange();
});
