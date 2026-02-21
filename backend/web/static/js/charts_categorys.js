// static/js/charts_categorys.js

const categoriesContainer = document.getElementById("chart-categories");

// カテゴリリストを更新する関数
// 外部から呼び出せるようにグローバルに定義
window.updateCategoryList = function (labels, values, bg) {
  // 関数化
  if (!categoriesContainer) return;

  // コンテナの中身を一度クリアする
  while (categoriesContainer.firstChild) {
    categoriesContainer.removeChild(categoriesContainer.firstChild);
  }

  // データがない場合は「No data」を表示
  if (labels.length === 0) {
    // labels は引数から受け取る
    const noDataMessage = document.createElement("div");
    noDataMessage.className = "text-sm text-slate-500";
    noDataMessage.textContent = "No data";
    categoriesContainer.appendChild(noDataMessage);
    return;
  }

  // 各カテゴリーを動的に追加
  labels.forEach((label, index) => {
    const categoryItem = document.createElement("div");
    categoryItem.className = "flex items-center justify-between mb-3 ";

    const leftSide = document.createElement("div");
    leftSide.className = "flex items-center ";

    const colorBox = document.createElement("span");
    colorBox.className = "inline-block w-3 h-3 rounded-full mr-2";
    colorBox.style.backgroundColor = bg[index];

    const categoryText = document.createElement("span");
    categoryText.textContent = label;

    leftSide.appendChild(colorBox);
    leftSide.appendChild(categoryText);

    const amountText = document.createElement("span");
    amountText.textContent = `¥${values[index].toLocaleString()}`;
    amountText.className = "font-semibold";

    categoryItem.appendChild(leftSide);
    categoryItem.appendChild(amountText);
    categoriesContainer.appendChild(categoryItem);
  });
};
