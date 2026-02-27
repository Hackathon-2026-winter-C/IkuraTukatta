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

// views.pyから渡された初期期間タイプを取得
const initialPeriodTypeTag = document.getElementById("initial-period-type");
const initialPeriodType = initialPeriodTypeTag ? JSON.parse(initialPeriodTypeTag.textContent) : 'year'; // デフォルトは'year'

// 新しく追加したナビゲーション要素と表示要素を取得
const yearNavigation = document.getElementById("year-navigation");
const monthNavigation = document.getElementById("month-navigation");
const yearDisplay = document.getElementById("year-display");
const monthDisplay = document.getElementById("month-display");
const monthYear = document.getElementById("month-year");
const monthNum = document.getElementById("month-num");

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

    // ナビゲーションの表示/非表示を切り替える
    if (selectedPeriod === 'year') {
        if (yearNavigation) yearNavigation.style.display = 'flex';
        if (monthNavigation) monthNavigation.style.display = 'none';
        if (yearDisplay) {
            // 年表示はviews.pyから渡されたcurrentYearDisplayをそのまま使う
            yearDisplay.textContent = processedChartData.year.currentYearDisplay;
        }
    } else if (selectedPeriod === 'month') {
        if (yearNavigation) yearNavigation.style.display = 'none';
        if (monthNavigation) monthNavigation.style.display = 'flex';
        if (monthDisplay && monthYear && monthNum) {
            const monthKey = processedChartData.month.currentMonthKey; // views.pyから渡されたキーを取得
            let yearStr;
            let monthStr;
            if (monthKey) {
                [yearStr, monthStr] = monthKey.split('-'); // "YYYY-MM"を分割
            } else {
                // monthKeyがない場合のフォールバック 
                const now = new Date();
                yearStr = String(now.getFullYear());
                monthStr = String(now.getMonth() + 1).padStart(2, "0");
            }

            const monthNumber = parseInt(monthStr, 10);
            monthYear.textContent = `${yearStr}.`;
            monthNum.textContent = `${monthNumber}`;
        }
    }

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
const radioOptions = document.querySelectorAll('input[name="chart-period"]');
radioOptions.forEach(radio => {
  radio.addEventListener('change', handlePeriodChange);
});

document.addEventListener('DOMContentLoaded', () => {
  // URLパラメータに基づいてラジオボタンを選択
  const initialRadio = document.getElementById(`chart-${initialPeriodType}`);
  if (initialRadio) {
    initialRadio.checked = true;
    initialRadio.dispatchEvent(new Event('change'));
  }
  // その後、handlePeriodChangeを呼び出して初期表示を更新
  handlePeriodChange();
});





