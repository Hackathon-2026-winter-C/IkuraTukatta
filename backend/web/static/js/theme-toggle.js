// ダークモードのテスト

const root = document.documentElement;
const toggle = document.querySelector('input[type="checkbox"]');

// 初期反映（data-theme に合わせる）
// 4行目のdata-themeがdarkならチェックをいれる
toggle.checked = root.getAttribute("data-theme") === "dark";

// トグルを押すイベントでdata-themeに入るものを変更
// checkedがtrueならdark, falseならlightを入れる
toggle.addEventListener("change", (event) => {
  root.setAttribute("data-theme", event.target.checked ? "dark" : "light");
});
