document.addEventListener("DOMContentLoaded", () => {
  const root = document.documentElement;
  const toggles = document.querySelectorAll("[data-theme-toggle]");
  if (!toggles.length) return;

  const mq = window.matchMedia("(prefers-color-scheme: dark)");
  const STORAGE_KEY = "theme"; // "dark" | "light" を保存

  const applyTheme = (isDark) => {
    root.setAttribute("data-theme", isDark ? "dark" : "light");
    toggles.forEach((t) => (t.checked = !isDark));
    // cookieにtheme=dark or lightを保存（ライト/ダークを即反映させるため）
    document.cookie = `theme=${isDark ? "dark" : "light"}; Max-Age=31536000; Path=/; SameSite=Lax`;
  };

  // localStorage の保存値（明示的に切り替えた場合）
  const saved = localStorage.getItem(STORAGE_KEY); // null | "dark" | "light"
  // サーバー側で埋め込まれている data-theme（cookie由来）
  const current = root.getAttribute("data-theme");

  // ① 初期：保存があればそれ優先
  if (saved === "dark" || saved === "light") {
    applyTheme(saved === "dark");
    // ② 保存がなければ、サーバーが指定した data-theme を尊重
  } else if (current === "dark" || current === "light") {
    applyTheme(current === "dark");
    // ③ それも無ければOSの配色に合わせる
  } else {
    applyTheme(mq.matches); // OSがdarkならtrue
  }

  // トグル操作：手動設定として保存（以降OS追従しない）
  toggles.forEach((t) => {
    t.addEventListener("change", (e) => {
      const isDark = !e.target.checked;
      applyTheme(isDark);
      localStorage.setItem(STORAGE_KEY, isDark ? "dark" : "light");
    });
  });
});
