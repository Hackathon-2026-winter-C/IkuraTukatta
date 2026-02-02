// charts.js で計算されたグローバル変数にアクセスする
// charts.js が先に実行されていることを前提とする
const labels = window.globalChartLabels || []; // アリスのカテゴリー名
const values = window.globalChartValues || []; // アリスの金額データ
const bg = window.globalChartBackgroundColors || []; // アリスのカテゴリー色

const categoriesContainer = document.getElementById('chart-categories');

// データがない場合は「No data」を表示
if (labels.length === 0) {
  // 1. 新しい div 要素を作成する
  const noDataMessage = document.createElement('div');

  // 2. 作成した div 要素にクラスを設定する
  noDataMessage.className = 'text-sm text-slate-500';

  // 3. 作成した div 要素にテキストコンテンツを設定する
  noDataMessage.textContent = 'No data';

  // 4. categoriesContainer の子要素として、作成した div 要素を追加する
  categoriesContainer.appendChild(noDataMessage);

} else {
  // コンテナの中身を一度クリアする
  // whileループを使って、categoriesContainerの最初の子要素が存在する限り削除を繰り返す
  while (categoriesContainer.firstChild) {
    categoriesContainer.removeChild(categoriesContainer.firstChild);
  }

  // 各カテゴリーを動的に追加
  labels.forEach((label, index) => {
    const categoryItem = document.createElement('div');
    // カテゴリー名と金額を左右に配置するためにjustify-betweenを追加
    categoryItem.className = 'flex items-center justify-between mb-2'; 

    const leftSide = document.createElement('div');
    leftSide.className = 'flex items-center';

    const colorBox = document.createElement('span');
    colorBox.className = 'inline-block w-3 h-3 rounded-full mr-2';
    colorBox.style.backgroundColor = bg[index]; 

    const categoryText = document.createElement('span');
    categoryText.textContent = label;

    leftSide.appendChild(colorBox);
    leftSide.appendChild(categoryText);

    const amountText = document.createElement('span');
    // 金額データを取得して表示。
    amountText.textContent = `¥${values[index].toLocaleString()}`; 
    amountText.className = 'font-semibold text-slate-800'; // 金額を少し強調

    categoryItem.appendChild(leftSide);
    categoryItem.appendChild(amountText);
    categoriesContainer.appendChild(categoryItem);
  });
}