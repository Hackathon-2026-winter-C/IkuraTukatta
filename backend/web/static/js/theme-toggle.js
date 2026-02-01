document.addEventListener("DOMContentLoaded", () => {
  const root = document.documentElement;
  const toggles = document.querySelectorAll("[data-theme-toggle]");
  if (!toggles.length) return;

  const mq = window.matchMedia("(prefers-color-scheme: dark)");
  const STORAGE_KEY = "theme"; // "dark" | "light" を保存

  const applyTheme = (isDark) => {
    root.setAttribute("data-theme", isDark ? "dark" : "light");
    toggles.forEach((t) => (t.checked = !isDark));
    //cookieにtheme=dark or lightを保存（ライト ダークを早く認識させるため）
    document.cookie = `theme=${isDark ? "dark" : "light"}; Max-Age=31536000; Path=/; SameSite=Lax`;
  };

  const saved = localStorage.getItem(STORAGE_KEY); // null | "dark" | "light"

  // ① 初期：保存があればそれ優先。なければOSに合わせる
  if (saved === "dark" || saved === "light") {
    applyTheme(saved === "dark");
  } else {
    applyTheme(mq.matches); // OSがdarkならtrue
  }

  // ② トグル操作：手動設定として保存（以降OS追従しない）
  toggles.forEach((t) => {
    t.addEventListener("change", (e) => {
      const isDark = !e.target.checked;
      applyTheme(isDark);
      localStorage.setItem(STORAGE_KEY, isDark ? "dark" : "light");
    });
  });
});
