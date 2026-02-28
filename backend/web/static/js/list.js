// static/js/list.js

  (() => {
    const url = new URL(window.location.href);

    const focus = url.searchParams.get("focus");
    if (!focus) return;

    const el = document.getElementById(`mf-${focus}`);
    if (!el) return;

    el.style.scrollMarginTop = "96px";
    el.scrollIntoView({ behavior: "smooth", block: "start" });

    el.classList.add("ring-2", "ring-[#FF9400]", "rounded-xl");
    setTimeout(() => {
      el.classList.remove("ring-2", "ring-[#FF9400]", "rounded-xl");
    }, 1200);

    url.searchParams.delete("focus");
    history.replaceState(null, "", url.toString());
  })();

  (() => {
    const url = new URL(window.location.href);
    const date = url.searchParams.get("date");
    if (!date) return;

    const el = document.getElementById(`date-${date}`);
    if (!el) return;

    el.style.scrollMarginTop = "96px";
    el.scrollIntoView({ behavior: "smooth", block: "start" });

    el.classList.add("ring-2", "ring-[#FF9400]", "rounded-3xl");
    setTimeout(() => {
      el.classList.remove("ring-2", "ring-[#FF9400]", "rounded-3xl");
    }, 1200);

    url.searchParams.delete("date");
    history.replaceState(null, "", url.toString());
  })();
