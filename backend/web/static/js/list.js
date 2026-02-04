// charts.js で計算されたグローバル変数ではなく、元の expense_data を直接読み込む
const dataTag = document.getElementById("expense-data");
const rawExpenses = dataTag ? JSON.parse(dataTag.textContent) : []; // 個々の支出データ

const categoriesContainer = document.getElementById('chart-categories');

// データがない場合は「No data」を表示
if (rawExpenses.length === 0) {
  const noDataMessage = document.createElement('div');
  noDataMessage.className = 'text-sm text-slate-500';
  noDataMessage.textContent = 'No data';
  categoriesContainer.appendChild(noDataMessage);
} else {
  // コンテナの中身を一度クリアする
  while (categoriesContainer.firstChild) {
    categoriesContainer.removeChild(categoriesContainer.firstChild);
  }

  // 各支出項目を動的に追加（rawExpensesはviews.pyで日付順に並べられているはず）
  rawExpenses.forEach((expense) => { // expense は個々の支出オブジェクト
    const expenseItem = document.createElement('div');
    // 日付、カテゴリー名、金額を左右に配置するためにjustify-betweenを追加
    expenseItem.className = 'flex items-center justify-between mb-2'; 

    const leftSide = document.createElement('div');
    leftSide.className = 'flex items-center';

    const colorBox = document.createElement('span');
    colorBox.className = 'inline-block w-3 h-3 rounded-full mr-2';
    // 個々の支出のカテゴリー色を適用。色がない場合はデフォルトのグレー
    colorBox.style.backgroundColor = expense.categoryColor || '#999999'; 

    const categoryText = document.createElement('span');
    // 日付とカテゴリー名を結合して表示
    categoryText.textContent = `${expense.date} - ${expense.category}`; 

    leftSide.appendChild(colorBox);
    leftSide.appendChild(categoryText);

    const amountText = document.createElement('span');
    // 金額データを取得して表示。toLocaleString()でカンマ区切りにフォーマット
    amountText.textContent = `¥${Number(expense.amount).toLocaleString()}`; 
    amountText.className = 'font-semibold text-slate-800'; 

    expenseItem.appendChild(leftSide);
    expenseItem.appendChild(amountText);
    categoriesContainer.appendChild(expenseItem);
  });
}