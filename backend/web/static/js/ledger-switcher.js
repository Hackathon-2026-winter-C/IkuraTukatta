// backend/web/static/js/ledger-switcher.js

const csrftoken = window.appUtils.getCookie("csrftoken");

async function apiGet(url) {
  const res = await fetch(url, { credentials: "same-origin" });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw { status: res.status, data };
  return data;
}

async function apiPost(url, body) {
  const csrftoken = getCookie("csrftoken");
  const res = await fetch(url, {
    method: "POST",
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrftoken || "",
    },
    body: JSON.stringify(body || {}),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw { status: res.status, data };
  return data;
}

function escapeHtml(s) {
  return String(s ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

document.addEventListener("DOMContentLoaded", () => {
  const root = document.getElementById("ledger-switcher");
  if (!root) return;

  const btn = document.getElementById("ledger-switcher-btn");
  const menu = document.getElementById("ledger-switcher-menu");
  const labelEl = document.getElementById("ledger-switcher-label");
  const subEl = document.getElementById("ledger-switcher-sub");
  const chevronEl = document.getElementById("ledger-switcher-chevron");

  let isOpen = false;

  function openMenu() {
    isOpen = true;
    menu.classList.remove("hidden");
    chevronEl?.classList.add("rotate-180");
  }
  function closeMenu() {
    isOpen = false;
    menu.classList.add("hidden");
    chevronEl?.classList.remove("rotate-180");
  }
  function toggleMenu() {
    isOpen ? closeMenu() : openMenu();
  }

  // 外側クリックで閉じる
  document.addEventListener("click", (e) => {
    if (!isOpen) return;
    if (!root.contains(e.target)) closeMenu();
  });

  btn?.addEventListener("click", toggleMenu);

  async function loadOwners() {
    // 初期状態
    labelEl.textContent = "読み込み中…";
    subEl.textContent = "";

    try {
      const data = await apiGet("/api/ledger/available/");
      const owners = data.owners || [];
      const currentOwnerId = data.current_owner_id;

      // 現在選択中表示
      const current = owners.find((o) => o.id === currentOwnerId) || owners[0];
      const currentName = (current?.username || "").trim() || current?.email || "My";
      labelEl.textContent = currentName;
      subEl.textContent = current && current.id !== currentOwnerId ? "" : "";

      // 選択肢メニュー
      menu.innerHTML = owners
        .map((o) => {
          const name = (o.username || "").trim() || o.email;
          const isActive = o.id === currentOwnerId;
          return `
            <button type="button"
              class="w-full text-left px-4 py-3 rounded-2xl bg-white/40 app-shadow flex items-center justify-between"
              data-owner-id="${o.id}"
              ${isActive ? 'aria-current="true"' : ""}
            >
              <span class="text-sm font-semibold text-[rgb(var(--app-text))]">${escapeHtml(name)}</span>
              ${isActive ? `<span class="text-[11px] opacity-60 text-[rgb(var(--app-text))]">選択中</span>` : `<span class="text-[11px] opacity-60 text-[rgb(var(--app-text))]">${escapeHtml(o.email || "")}</span>`}
            </button>
          `;
        })
        .join("");

      // クリック時：owner切替 → session保存 → reload
      menu.querySelectorAll("button[data-owner-id]").forEach((b) => {
        b.addEventListener("click", async () => {
          const ownerId = parseInt(b.dataset.ownerId, 10);
          if (!ownerId) return;

          // すでに選択中なら閉じるだけ
          const cur = owners.find((x) => x.id === currentOwnerId);
          if (cur && cur.id === ownerId) {
            closeMenu();
            return;
          }

          // UI: 一時的に無効化
          menu.querySelectorAll("button").forEach((x) => (x.disabled = true));
          labelEl.textContent = "切替中…";

          try {
            await apiPost("/api/ledger/select/", { owner_id: ownerId });
            window.location.reload();
          } catch (e) {
            // 失敗したら戻す
            const fallbackName = (current?.username || "").trim() || current?.email || "My";
            labelEl.textContent = fallbackName;
            menu.querySelectorAll("button").forEach((x) => (x.disabled = false));
            closeMenu();
            alert("切替に失敗したよ（権限がない/通信エラー）");
          }
        });
      });

      // 候補が1人しかいないなら、ボタン押せないように
      if (owners.length <= 1) {
        btn.disabled = true;
        btn.classList.add("opacity-70");
        chevronEl?.classList.add("opacity-40");
      }
    } catch (e) {
      labelEl.textContent = "読み込み失敗";
      menu.innerHTML = `
        <div class="px-4 py-3 text-sm text-red-500">
          owner一覧の取得に失敗したよ
        </div>
      `;
    }
  }

  loadOwners();
});
