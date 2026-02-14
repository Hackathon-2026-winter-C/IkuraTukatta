document.addEventListener("DOMContentLoaded", () => {
  // モーダル開閉に使うトリガー要素
  const openBtn = document.getElementById("open-icon-modal");
  const modal = document.getElementById("icon-modal");
  const bg = document.getElementById("icon-modal-bg");

  // 要素が無いページでは処理しない
  if (!openBtn || !modal || !bg) return;

  // モーダルを開いて背景スクロールを止める
  const open = () => {
    modal.classList.remove("hidden");
    document.body.classList.add("overflow-hidden");
  };

  // モーダルを閉じて、閉じたことを他スクリプトへ通知する
  const close = () => {
    modal.classList.add("hidden");
    document.body.classList.remove("overflow-hidden");
    // account-profile-image.js がこのイベントを受けて選択画像をリセットする
    modal.dispatchEvent(new CustomEvent("icon-modal:closed"));
  };

  openBtn.addEventListener("click", open);
  // 背景クリックで閉じる
  bg.addEventListener("click", (e) => {
    e.preventDefault();
    close();
  });

  // Escキーでも閉じる
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !modal.classList.contains("hidden")) close();
  });
});
