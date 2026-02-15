document.addEventListener("DOMContentLoaded", () => {
  // 右側の更新アイコン
  const openBtn = document.getElementById("open-user-logout-modal");
  // ログアウトURLは行全体ボタンの data 属性から取得
  const logoutRowBtn = document.querySelector("[data-logout]");
  const modal = document.getElementById("user-logout-modal");
  const bg = document.getElementById("user-logout-modal-bg");
  const closeBtns = modal?.querySelectorAll("[data-close-logout-modal]") || [];
  const submitBtn = document.getElementById("submit-logout");

  if (!openBtn || !logoutRowBtn || !modal || !bg || !submitBtn) return;

  const open = () => {
    modal.classList.remove("hidden");
    document.body.classList.add("overflow-hidden");
  };

  const close = () => {
    modal.classList.add("hidden");
    document.body.classList.remove("overflow-hidden");
  };

  // 右側アイコンのクリックで確認モーダルを開く
  openBtn.addEventListener("click", (e) => {
    e.preventDefault();
    open();
  });

  // 背景・キャンセルで閉じる
  bg.addEventListener("click", close);
  closeBtns.forEach((btn) => btn.addEventListener("click", close));

  // Escでも閉じる
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !modal.classList.contains("hidden")) {
      close();
    }
  });

  // 「ログアウト」確定時のみ実行
  submitBtn.addEventListener("click", () => {
    const url = logoutRowBtn.dataset.logoutUrl;
    if (!url) return;
    submitBtn.disabled = true;
    window.location.href = url; // GETで/logoutへ → view側でloginへリダイレクト
  });
});
