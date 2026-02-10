// static/js/charts.js

const chartEl = document.getElementById("expense-chart");
const chartEmptyMessage = document.getElementById("chart-empty");
let myChartInstance; // Chart.jsのインスタンスを保持する変数

// Chart.jsのカスタムプラグイン定義（合計金額表示）
const centerTextPlugin = {
  id: 'centerText',
  beforeDraw: (chart, args, options) => {
    const { ctx, width, height } = chart;
    ctx.restore();
    const fontSize = (height / 180).toFixed(2);
    ctx.font = `bold ${fontSize}em sans-serif`;
    ctx.textBaseline = 'middle';

    const text = options.totalAmountText;
    if (text) {
      const textX = Math.round((width - ctx.measureText(text).width) / 2);
      const textY = height / 2;
      // 変更点: 現在のテーマに応じてテキスト色を切り替える！
      const htmlElement = document.documentElement; // <html>要素を取得
      const isDarkMode = htmlElement.getAttribute('data-theme') === 'dark'; // data-theme属性を確認
      ctx.fillStyle = isDarkMode ? '#FFFFFF' : '#333333'; // ダークモードなら白、ライトモードなら濃いグレー
      ctx.fillText(text, textX, textY);
    }
    ctx.save();
  }
};

// チャートを更新する関数
// 外部から呼び出せるようにグローバルに定義
window.updateChart = function(labels, values, bg, formattedTotalAmount) {
  if (!chartEl || typeof Chart === "undefined") return;

  if (labels.length === 0) {
    if (chartEmptyMessage) chartEmptyMessage.hidden = false;
    if (myChartInstance) myChartInstance.destroy(); // チャートを破棄
    myChartInstance = null; // インスタンスをクリア
    return;
  } else {
    if (chartEmptyMessage) chartEmptyMessage.hidden = true;
  }

  if (myChartInstance) {
    // 既存のチャートを更新
    myChartInstance.data.labels = labels;
    myChartInstance.data.datasets[0].data = values;
    myChartInstance.data.datasets[0].backgroundColor = bg;
    myChartInstance.options.plugins.centerText.totalAmountText = formattedTotalAmount; // プラグインオプションを更新
    myChartInstance.update();
  } else {
    // 新しいチャートを作成
    myChartInstance = new Chart(chartEl, {
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
        responsive: false,
        maintainAspectRatio: false,
        cutout: "60%",
        plugins: {
          legend: { display: false },
          centerText: { // プラグインオプションとしてtotalAmountTextを渡す
            totalAmountText: formattedTotalAmount
          }
        },
      },
      plugins: [centerTextPlugin]
    });
  }
};

// 初期表示は charts_period_switcher.js で行うため、ここでは何もしない
