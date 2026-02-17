// backend/web/static/js/ledger-switcher.js
(() => {
  const escapeHtml = (s) =>
    String(s ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");

  const getCookie = (name) => {
    const m = document.cookie.match(new RegExp("(^|;\\s*)" + name + "=([^;]+)"));
    return m ? decodeURIComponent(m[2]) : "";
  };

  const apiGet = async (url) => {
    const res = await fetch(url, { credentials: "same-origin" });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw { status: res.status, data };
    return data;
  };

  const apiPost = async (url, body) => {
    const csrftoken = getCookie("csrftoken");
    const res = await fetch(url, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrftoken },
      body: JSON.stringify(body || {}),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw { status: res.status, data };
    return data;
  };

  const onReady = (fn) => {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", fn);
    else fn();
  };

  onReady(() => {
    const root = document.getElementById("ledger-switcher");
    if (!root) return;

    const btn = document.getElementById("ledger-switcher-btn");
    const menu = document.getElementById("ledger-switcher-menu");
    const labelEl = document.getElementById("ledger-switcher-label");
    const badgeEl = document.getElementById("ledger-switcher-badge");
    const chevron = document.getElementById("ledger-switcher-chevron");

    if (!btn || !menu || !labelEl) return;

    let currentId = null;
    let items = [];

    const setLabel = (item) => {
      if (!item) {
        labelEl.textContent = "読み込み中…";
        badgeEl?.classList.add("hidden");
        return;
      }

      labelEl.textContent = item.name;
      if (badgeEl) {
        badgeEl.textContent = "表示中";
        badgeEl.classList.remove("hidden");
      }
    };

    const openMenu = () => {
      root.classList.add("is-open");
      btn.setAttribute("aria-expanded", "true");
      menu.setAttribute("aria-hidden", "false");
      chevron?.classList.add("rotate-180");
    };
    const closeMenu = () => {
      root.classList.remove("is-open");
      btn.setAttribute("aria-expanded", "false");
      menu.setAttribute("aria-hidden", "true");
      chevron?.classList.remove("rotate-180");
    };
    const toggleMenu = () => {
      if (root.classList.contains("is-open")) closeMenu();
      else openMenu();
    };

    btn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      toggleMenu();
    });
    menu.addEventListener("click", (e) => e.stopPropagation());
    document.addEventListener("click", closeMenu);

    btn.setAttribute("aria-expanded", "false");
    menu.setAttribute("aria-hidden", "true");

    const renderMenu = () => {
      if (!items.length) {
        menu.innerHTML = `<p class="text-xs px-2 py-2" style="color: rgb(var(--app-text)); opacity: 0.6;">グループがありません</p>`;
        return;
      }

      const activeId = currentId ?? 0;
      const others = items.filter((it) => it.id !== activeId);
      if (!others.length) {
        menu.innerHTML = `<p class="text-xs px-2 py-2" style="color: rgb(var(--app-text)); opacity: 0.6;">他の選択肢がありません</p>`;
        return;
      }

      menu.innerHTML = others
        .map((it) => {
          return `
            <button type="button"
              class="ledger-switcher__option"
              style="color: rgb(var(--app-text));"
              data-gid="${it.id}"
              data-gname="${escapeHtml(it.name)}">
              <span class="text-sm font-semibold">${escapeHtml(it.name)}</span>
            </button>
          `;
        })
        .join("");

      menu.querySelectorAll("button[data-gid]").forEach((b) => {
        b.addEventListener("click", async () => {
          const gid = parseInt(b.dataset.gid, 10);
          if (Number.isNaN(gid)) return;

          try {
            await apiPost("/api/groups/select/", { group_id: gid });
          } catch (_) {
            return;
          }

          const prevId = currentId ?? 0;
          if (gid !== prevId) {
            window.location.reload();
            return;
          }

          currentId = gid === 0 ? null : gid;
          const selected = items.find((it) => it.id === (currentId ?? 0)) || items[0];
          setLabel(selected);
          renderMenu();
          closeMenu();
        });
      });
    };

    const refresh = async () => {
      labelEl.textContent = "読み込み中…";
      menu.innerHTML = `<p class="text-xs px-2 py-2" style="color: rgb(var(--app-text)); opacity: 0.6;">読み込み中…</p>`;

      try {
        const data = await apiGet("/api/groups/available/");
        const personal = data.personal || { id: 0, name: "自分" };
        const groups = data.groups || [];
        currentId = data.current_group_id ?? null;

        items = [{ id: 0, name: personal.name }, ...groups.map((g) => ({ id: g.id, name: g.name }))];

        const selected = items.find((it) => it.id === (currentId ?? 0)) || items[0];
        setLabel(selected);
        renderMenu();
      } catch (_) {
        labelEl.textContent = "読み込み失敗";
        badgeEl?.classList.add("hidden");
        menu.innerHTML = `<p class="text-xs text-red-500 px-2 py-2">読み込みに失敗しました</p>`;
      }
    };

    refresh();
  });
})();
