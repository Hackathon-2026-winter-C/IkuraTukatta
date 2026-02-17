document.addEventListener("DOMContentLoaded", () => {
  const darkBtn = document.getElementById("theme-choice-dark");
  const lightBtn = document.getElementById("theme-choice-light");
  if (!darkBtn || !lightBtn) return;

  const getCookie = (name) => {
    const v = `; ${document.cookie}`;
    const p = v.split(`; ${name}=`);
    if (p.length === 2) return p.pop().split(";").shift();
    return "";
  };

  const applyTheme = (mode) => {
    const isDark = mode === "dark";
    document.documentElement.setAttribute("data-theme", isDark ? "dark" : "light");
    document.cookie = `theme=${isDark ? "dark" : "light"}; Max-Age=31536000; Path=/; SameSite=Lax`;
    localStorage.setItem("theme", isDark ? "dark" : "light");
  };

  const complete = async () => {
    try {
      await fetch("/api/account/theme-choice/complete/", {
        method: "POST",
        headers: { "X-CSRFToken": getCookie("csrftoken") },
        credentials: "same-origin",
      });
    } catch (_) {}
    window.location.href = "/dashboard/";
  };

  darkBtn.addEventListener("click", () => {
    applyTheme("dark");
    complete();
  });

  lightBtn.addEventListener("click", () => {
    applyTheme("light");
    complete();
  });
});
