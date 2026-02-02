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

  window.globalChartLabels = labels;
  window.globalChartValues = values;
  window.globalChartBackgroundColors = bg;

  // 1. 合計金額を計算
  const totalAmount = values.reduce((sum, current) => sum + current, 0);
  const formattedTotalAmount = `¥${totalAmount.toLocaleString()}`; // フォーマット済み

  // 2. カスタムプラグインを定義
  const centerTextPlugin = {
    id: 'centerText', // プラグインのID
    beforeDraw: (chart) => { // グラフが描画される前に実行されるフック
      const { ctx, width, height } = chart; // キャンバスのコンテキストとサイズを取得

      ctx.restore(); // 描画状態
      const fontSize = (height / 180).toFixed(2); // キャンバスの高さに基づいてフォントサイズを調整
      ctx.font = `bold ${fontSize}em sans-serif`; // フォントスタイルを設定
      ctx.textBaseline = 'middle'; // テキストのベースラインを中央に設定

      const text = formattedTotalAmount; // 表示するテキスト
      const textX = Math.round((width - ctx.measureText(text).width) / 2); // テキストのX座標を計算（中央揃え）
      const textY = height / 2; // テキストのY座標を計算（中央揃え）

      ctx.fillStyle = '#333'; // テキストの色を設定
      ctx.fillText(text, textX, textY); // テキストを描画
      ctx.save(); // 現在の描画状態を保存
    }
  };

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
      responsive: false, // レスポンシブを無効にする★
      maintainAspectRatio: false, // アスペクト比の維持を無効にする★
      cutout: "60%",
      plugins: {
        legend: { display: false },
        // カスタムプラグインを登録する★
        centerText: centerTextPlugin // 定義したプラグインをChart.jsに渡す
      },
    },
    // プラグインの配列にカスタムプラグインを追加する★
    plugins: [centerTextPlugin] 
  });
}

