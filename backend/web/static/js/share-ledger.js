// backend/web/static/js/share-ledger.js

const csrftoken = window.appUtils.getCookie("csrftoken");

function show(el) {
  el?.classList.remove("hidden");
}
function hide(el) {
  el?.classList.add("hidden");
}

function setMsg(okEl, errEl, okMsg, errMsg) {
  if (okMsg) {
    okEl.textContent = okMsg;
    okEl.classList.remove("hidden");
  } else {
    okEl.classList.add("hidden");
  }
  if (errMsg) {
    errEl.textContent = errMsg;
    errEl.classList.remove("hidden");
  } else {
    errEl.classList.add("hidden");
  }
}

// XSS対策：ユーザー名/メールをHTMLに差し込む前にエスケープ
function escapeHtml(s) {
  return String(s ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

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

document.addEventListener("DOMContentLoaded", () => {
  const openBtn = document.getElementById("open-share-modal");
  const modal = document.getElementById("share-modal");
  const bg = document.getElementById("share-modal-bg");
  const cancelBtn = document.getElementById("share-cancel");

  const listEl = document.getElementById("share-list");
  const emailEl = document.getElementById("share-email");
  const addBtn = document.getElementById("share-add");
  const errEl = document.getElementById("share-error");
  const okEl = document.getElementById("share-ok");

  const rmModal = document.getElementById("share-remove-modal");
  const rmBg = document.getElementById("share-remove-bg");
  const rmTitle = document.getElementById("share-remove-title");
  const rmConfirm = document.getElementById("share-remove-confirm");
  const rmCancel = document.getElementById("share-remove-cancel");

  // 必要なDOMが無ければ何もしない（他ページでも読み込めるように）
  if (!openBtn || !modal) return;

  let pendingRemoveViewerId = null;
  let pendingRemoveLabel = "";
  let isRefreshing = false;

  async function refreshList() {
    if (!listEl) return;
    if (isRefreshing) return;
    isRefreshing = true;

    listEl.innerHTML = `<p class="text-xs text-black/50">読み込み中…</p>`;
    setMsg(okEl, errEl, "", "");

    try {
      const data = await apiGet("/api/ledger/share/list/");
      const viewers = data.viewers || [];

      if (viewers.length === 0) {
        listEl.innerHTML = `<p class="text-xs text-black/50">まだ共有メンバーがいないよ</p>`;
        return;
      }

      listEl.innerHTML = viewers
        .map((v) => {
          const labelRaw = v.username && v.username.trim() ? v.username : v.email;
          const label = escapeHtml(labelRaw);
          const email = escapeHtml(v.email);

          return `
            <button type="button"
              class="w-full h-11 rounded-2xl px-4 flex items-center justify-between bg-white/70"
              style="box-shadow: var(--app-mainbutton-shadow);"
              data-viewer-id="${v.id}"
              data-viewer-label="${escapeHtml(labelRaw)}"
            >
              <span class="text-sm font-semibold text-[#111]">${label}</span>
              <span class="text-[11px] text-black/50">${email}</span>
            </button>
          `;
        })
        .join("");

      // 削除確認モーダルを開く
      listEl.querySelectorAll("button[data-viewer-id]").forEach((btn) => {
        btn.addEventListener("click", () => {
          pendingRemoveViewerId = parseInt(btn.dataset.viewerId, 10);
          pendingRemoveLabel = btn.dataset.viewerLabel || "このユーザー";
          if (rmTitle) rmTitle.textContent = `${pendingRemoveLabel}を削除しますか？`;
          show(rmModal);
        });
      });
    } catch (e) {
      listEl.innerHTML = `<p class="text-xs text-red-500">一覧の取得に失敗したよ</p>`;
    } finally {
      isRefreshing = false;
    }
  }

  function openModal() {
    show(modal);
    if (emailEl) emailEl.value = "";
    setMsg(okEl, errEl, "", "");
    refreshList();

    // 開いたら入力にフォーカス
    setTimeout(() => {
      emailEl?.focus?.();
    }, 50);
  }

  function closeModal() {
    hide(modal);
  }

  function closeRemoveModal() {
    hide(rmModal);
    pendingRemoveViewerId = null;
    pendingRemoveLabel = "";
  }

  // open/close
  openBtn.addEventListener("click", openModal);
  bg?.addEventListener("click", closeModal);
  cancelBtn?.addEventListener("click", closeModal);

  rmBg?.addEventListener("click", closeRemoveModal);
  rmCancel?.addEventListener("click", closeRemoveModal);

  // Enterキーで追加
  emailEl?.addEventListener("keydown", (ev) => {
    if (ev.key === "Enter") {
      ev.preventDefault();
      addBtn?.click();
    }
  });

  // add
  addBtn?.addEventListener("click", async () => {
    const email = (emailEl?.value || "").trim();
    if (!email) {
      setMsg(okEl, errEl, "", "メールアドレスを入れてね");
      return;
    }

    addBtn.disabled = true;
    setMsg(okEl, errEl, "", "");

    try {
      const data = await apiPost("/api/ledger/share/add/", { email });

      if (data.created) setMsg(okEl, errEl, "追加したよ！", "");
      else setMsg(okEl, errEl, "すでに共有済みだよ", "");

      if (emailEl) emailEl.value = "";
      await refreshList();
    } catch (e) {
      const code = e?.data?.error;
      if (code === "user_not_found") setMsg(okEl, errEl, "", "そのメールのユーザーが見つからないよ");
      else if (code === "cannot_share_to_self") setMsg(okEl, errEl, "", "自分には共有できないよ");
      else setMsg(okEl, errEl, "", "追加に失敗したよ");
    } finally {
      addBtn.disabled = false;
    }
  });

  // remove confirm
  rmConfirm?.addEventListener("click", async () => {
    if (!pendingRemoveViewerId) return;

    rmConfirm.disabled = true;

    try {
      await apiPost("/api/ledger/share/remove/", { viewer_id: pendingRemoveViewerId });
      closeRemoveModal();
      await refreshList();
      setMsg(okEl, errEl, "削除したよ", "");
    } catch (e) {
      closeRemoveModal();
      setMsg(okEl, errEl, "", "削除に失敗したよ");
    } finally {
      rmConfirm.disabled = false;
    }
  });
});
