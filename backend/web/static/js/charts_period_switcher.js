// charts_period_switcher.js
// Pythonから渡された集計済みデータを取得
// HTMLテンプレートで `{{ processed_chart_data|json_script:"processed-chart-data" }}` として渡されることを想定
const processedChartDataTag = document.getElementById("processed-chart-data")

let processedChartData; // まず変数を宣言する
if (processedChartDataTag) { 
  processedChartData = JSON.parse(processedChartDataTag.textContent); // processedChartDataTag が存在する場合
} else {
  processedChartData = { year: {}, month: {} }; // processedChartDataTag が存在しない場合
}
// ラジオボタンの変更を処理するメイン関数
function handlePeriodChange() {
    // 現在選択されている期間（'year' または 'month'）を取得
    const selectedPeriod = document.querySelector('input[name="chart-period"]:checked').value;

    // Pythonから渡されたデータから、選択された期間のデータを直接取得
    // データがない場合のデフォルト値も設定しておくと安心
    let chartDataToUse; // 最終的に使うチャートデータを格納する変数を宣言
    // processedChartData[selectedPeriod] の値を取得
    const dataFromProcessedChart = processedChartData[selectedPeriod];
    if (dataFromProcessedChart) {
      // dataFromProcessedChart が真値（有効なデータオブジェクト）の場合
      chartDataToUse = dataFromProcessedChart;
    } else {
      // dataFromProcessedChart が偽値（null, undefinedなど）の場合
      // デフォルトの空のデータオブジェクトを使用
      chartDataToUse = { labels: [], values: [], bg: [], formattedTotalAmount: "¥0"}
    }

    // 決定された chartDataToUse から分割代入を行う
    const { labels, values, bg, formattedTotalAmount } = chartDataToUse;

    // charts.js (円グラフ) と charts_categorys.js (カテゴリリスト) で定義された関数を呼び出し、データを渡す
    if (window.updateChart) {
      window.updateChart(labels, values, bg, formattedTotalAmount);
    }
    if (window.updateCategoryList) {
      window.updateCategoryList(labels, values, bg);
    }
}

// イベントリスナーの登録
// 'chart-period' という名前のラジオボタンの変更を監視
const radioOptions = document.querySelectorAll('input[name="chart-period');
radioOptions.forEach(radio => {
  radio.addEventListener('change', handlePeriodChange);
});

// ページロード時の初期表示
// DOMContentLoaded イベントが発生したら、初期期間（通常は checked="checked" が付いている 'Year'）でチャートを表示
document.addEventListener('DOMContentLoaded', () => {
  handlePeriodChange();
});






