document.addEventListener("DOMContentLoaded", () => {
  // モーダル内の画像変更UI要素を取得
  const modal = document.getElementById("icon-modal");
  const pickBtn = document.getElementById("pick-profile-image");
  const input = document.getElementById("profile-image-input");
  const preview = document.getElementById("profile-image-preview");
  const submitBtn = document.getElementById("submit-profile-image");
  const avatars = document.querySelectorAll("[data-user-avatar]");

  // 要素が揃っていないページでは何もしない
  if (!modal || !pickBtn || !input || !preview || !submitBtn) return;

  // 初期表示時点の画像URLを保持（閉じた時のリセット先）
  preview.dataset.initialSrc = preview.dataset.initialSrc || preview.src;

  // CSRFトークン取得
  const getCookie = (name) => {
    const v = `; ${document.cookie}`;
    const p = v.split(`; ${name}=`);
    if (p.length === 2) return p.pop().split(";").shift();
    return "";
  };

  // 選択中画像を破棄して初期画像へ戻す
  const resetPickedImage = () => {
    input.value = "";
    preview.src = preview.dataset.initialSrc || preview.src;
  };

  // account-icon-modal.js からの close 通知を受けてリセット
  modal.addEventListener("icon-modal:closed", resetPickedImage);

  // プレビュークリックでファイル選択を開く
  pickBtn.addEventListener("click", () => {
    if (pickBtn.tagName === "LABEL") return;
    input.click();
  });

  // 画像選択直後にプレビュー反映
  input.addEventListener("change", () => {
    const file = input.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      if (typeof e.target?.result === "string") {
        preview.src = e.target.result;
      }
    };
    reader.readAsDataURL(file);
  });

  // 「変更する」押下でアップロード
  submitBtn.addEventListener("click", async () => {
    const file = input.files?.[0];
    if (!file) {
      input.click();
      return;
    }

    const fd = new FormData();
    fd.append("profile_image", file);

    submitBtn.disabled = true;

    try {
      const res = await fetch("/api/account/profile-image/", {
        method: "POST",
        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: fd,
      });

      const data = await res.json();

      if (!res.ok || !data.ok) {
        throw new Error(data.error || "更新に失敗しました");
      }

      // 画面内のアバター表示を先に更新
      avatars.forEach((img) => {
        img.src = data.image_url;
      });

      // 次回リセット先を最新URLに更新
      preview.dataset.initialSrc = data.image_url;
      preview.src = data.image_url;
      input.value = "";

      // モーダルを閉じる
      modal.classList.add("hidden");
      document.body.classList.remove("overflow-hidden");

      // サーバー側の最新情報を確実に反映
      window.location.reload();
    } catch (err) {
      alert(err.message || "エラーが発生しました");
    } finally {
      submitBtn.disabled = false;
    }
  });
});
