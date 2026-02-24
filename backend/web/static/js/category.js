console.log("category.js loaded ✅");

document.addEventListener("DOMContentLoaded", () => {
  // Cookie から指定した名前の値を取得する（CSRFトークン取得用）
  const getCookie = (name) => {
    const viaUtils = window.appUtils?.getCookie?.(name);
    if (viaUtils !== undefined && viaUtils !== null) return viaUtils;
    const m = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
    return m ? decodeURIComponent(m[2]) : null;
  };
  const csrftoken = getCookie("csrftoken");

  // モーダル関連のDOM要素
  const modal = document.getElementById("cat-modal");
  const bg = document.getElementById("cat-modal-bg");

  const titleEl = document.getElementById("cat-modal-title");
  const nameEl = document.getElementById("cat-name");
  const errEl = document.getElementById("cat-error");
  const submitBtn = document.getElementById("cat-submit");
  const submitText = document.getElementById("cat-submit-text");
  const cancelBtn = document.getElementById("cat-cancel");
  const deleteBtn = document.getElementById("cat-delete"); // ★追加

  const colorRow = document.getElementById("cat-color-row");
  const colorEl = document.getElementById("cat-color");

  const iconCircle = document.getElementById("cat-modal-iconcircle");
  const iconBox = document.getElementById("cat-modal-icon");
  const defaultIconHtml = iconBox?.innerHTML || "";

  // 削除確認モーダル
  const deleteModal = document.getElementById("cat-delete-modal");
  const deleteBg = document.getElementById("cat-delete-bg");
  const deleteTitleEl = document.getElementById("cat-delete-title");
  const deleteConfirmBtn = document.getElementById("cat-delete-confirm");
  const deleteCancelBtn = document.getElementById("cat-delete-cancel");

  // 必要な要素が存在しないページでは何もしない
  if (!modal || !bg || !titleEl || !nameEl || !errEl || !submitBtn || !submitText || !cancelBtn || !deleteBtn || !colorRow || !colorEl || !iconCircle || !iconBox || !deleteModal || !deleteBg || !deleteTitleEl || !deleteConfirmBtn || !deleteCancelBtn) {
    return;
  }

  let mode = null; // "create" or "rename"
  let currentId = null; // 編集/削除対象カテゴリID
  let currentIo = null; // 作成時の収支区分（0:支出 / 1:収入）
  let currentName = ""; // 表示用
  let currentBuiltin = false; // ★ builtinフラグ

  function openModal(nextMode, payload, sourceBtn = null) {
    mode = nextMode;
    errEl.classList.add("hidden");

    const accent = payload?.color || "#FF9400";
    iconCircle.style.setProperty("--cat-accent", accent);

    if (mode === "create") {
      currentId = null;
      currentIo = payload.io;
      currentBuiltin = false;
      currentName = "";

      titleEl.textContent = "カテゴリ追加";
      submitText.textContent = "登　録";
      nameEl.value = "";

      colorRow.classList.remove("hidden");
      colorEl.value = "#FF9400";

      // ★ create時はアイコンを「＋」に戻す
      if (iconBox) {
        iconBox.innerHTML = defaultIconHtml;
        iconBox.style.color = "";
      }

      // ★ create時は削除ボタンを必ず隠す
      deleteBtn.classList.add("hidden");
    } else {
      currentId = payload.id;
      currentIo = null;
      currentBuiltin = !!payload.is_builtin;
      currentName = payload.name || "";

      titleEl.textContent = "カテゴリ名変更";
      submitText.textContent = "カテゴリ名を変更";
      nameEl.value = payload.name || "";

      colorRow.classList.add("hidden");

      // ★ builtinなら削除ボタンを出さない
      if (currentBuiltin) {
        deleteBtn.classList.add("hidden");
      } else {
        deleteBtn.classList.remove("hidden");
      }

      // アイコン反映（一覧からSVGを拾ってモーダルへ）
      if (sourceBtn) {
        const svg = sourceBtn.querySelector("svg");
        if (svg) {
          iconBox.innerHTML = svg.outerHTML;

          const modalSvg = iconBox.querySelector("svg");
          if (modalSvg) {
            // 一覧と同じく「線の色」をアクセントに
            modalSvg.style.color = "var(--cat-accent)";

            // stroke を currentColor に寄せる
            modalSvg.querySelectorAll("*").forEach((el) => {
              const stroke = el.getAttribute("stroke");
              if (stroke && stroke !== "none") {
                el.setAttribute("stroke", "currentColor");
              }
            });
          }
        }
      }
    }

    modal.classList.remove("hidden");
    nameEl.focus();
  }

  function closeModal() {
    modal.classList.add("hidden");
  }
  function openDeleteModal() {
    const label = currentName || "このカテゴリ";
    deleteTitleEl.textContent = `${label}を削除しますか？`;
    deleteModal.classList.remove("hidden");
  }
  function closeDeleteModal() {
    deleteModal.classList.add("hidden");
  }

  bg.addEventListener("click", closeModal);
  cancelBtn.addEventListener("click", closeModal);
  deleteBg.addEventListener("click", () => {
    closeDeleteModal();
    modal.classList.remove("hidden");
  });
  deleteCancelBtn.addEventListener("click", () => {
    closeDeleteModal();
    modal.classList.remove("hidden");
  });

  // 画面上のカテゴリボタンのクリック処理
  document.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-open]");
    if (!btn) return;

    if (btn.dataset.open === "create") {
      openModal("create", { io: Number(btn.dataset.io), color: "#FF9400" }, btn);
      return;
    }

    if (btn.dataset.open === "rename") {
      // DjangoのBooleanは "True"/"False" が来がちなので両対応
      const builtinStr = (btn.dataset.builtin || "").toLowerCase();
      const isBuiltin = builtinStr === "true";

      openModal(
        "rename",
        {
          id: Number(btn.dataset.id),
          name: btn.dataset.name,
          color: btn.style.getPropertyValue("--c").trim(),
          is_builtin: isBuiltin,
        },
        btn,
      );
    }
  });

  // 登録（保存）ボタン処理（create/rename）
  submitBtn.addEventListener("click", async () => {
    errEl.classList.add("hidden");
    const name = nameEl.value.trim();

    if (!name) {
      errEl.textContent = "カテゴリ名を入力してね";
      errEl.classList.remove("hidden");
      return;
    }

    if (!csrftoken) {
    errEl.textContent = "CSRFトークンが取得できてないから（ページを再読み込み/ログインしてね）";
    errEl.classList.remove("hidden");
    return;
  }


    try {
      if (mode === "create") {
        const res = await fetch("/api/categories/create/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrftoken,
          },
          body: JSON.stringify({
            name,
            color: colorEl.value,
            is_io_type: currentIo,
          }),
        });

        const data = await res.json();
        if (!res.ok || !data.ok) throw new Error(data.error || "作成に失敗したよ");
      }

      if (mode === "rename") {
        const res = await fetch(`/api/categories/${currentId}/rename/`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrftoken,
          },
          body: JSON.stringify({ name }),
        });

        const data = await res.json();
        if (!res.ok || !data.ok) throw new Error(data.error || "変更に失敗したよ");
      }

      closeModal();
      location.reload();
    } catch (err) {
      errEl.textContent = err?.message || "エラーが起きたよ";
      errEl.classList.remove("hidden");
    }
  });

  // ★ 削除ボタン処理
  deleteBtn.addEventListener("click", async () => {
    errEl.classList.add("hidden");

    // builtinはここでもガード（二重防衛）
    if (currentBuiltin) return;

    if (!currentId) return;
    closeModal();
    openDeleteModal();

    return;
  });

  deleteConfirmBtn.addEventListener("click", async () => {
    errEl.classList.add("hidden");

    if (!currentId) return;
    try {
      const res = await fetch(`/api/categories/${currentId}/delete/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrftoken,
        },
        body: JSON.stringify({}),
      });

      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error(data.error || "削除に失敗したよ");

      closeModal();
      closeDeleteModal();
      location.reload();
    } catch (err) {
      errEl.textContent = err?.message || "エラーが起きたよ";
      errEl.classList.remove("hidden");
      closeDeleteModal();
      modal.classList.remove("hidden");
    }
  });
});
