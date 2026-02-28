document.addEventListener("DOMContentLoaded", () => {
  // signup画面の要素を取得
  const button = document.getElementById("pick-profile-image");
  const input = document.getElementById("profile-image-input");
  const preview = document.getElementById("profile-image-preview");
  const form = document.getElementById("signup-form");

  // sessionStorageに使うキー
  const imageKey = "signup.profile.preview";
  const filenameKey = "signup.profile.filename";

  // サーバー再描画時、formエラーがある時だけキャッシュを維持するフラグ
  const keepCacheOnLoad = form?.dataset.keepImageCache === "true";

  if (!button || !input || !preview || !form) {
    return;
  }

  // 画像キャッシュ削除（成功時や通常遷移時に使う）
  const clearCache = () => {
    sessionStorage.removeItem(imageKey);
    sessionStorage.removeItem(filenameKey);
  };

  // プレビュー画像を差し替え
  const setPreview = (src) => {
    preview.src = src;
    preview.classList.add("rounded-[18px]");
  };

  // sessionStorage容量対策:
  // 元画像が大きすぎる時は軽量JPEGにして保存する
  const compressForCache = (file) =>
    new Promise((resolve, reject) => {
      const objectUrl = URL.createObjectURL(file);
      const img = new Image();
      img.onload = () => {
        try {
          const maxSide = 1024;
          const scale = Math.min(1, maxSide / Math.max(img.width, img.height));
          const width = Math.max(1, Math.round(img.width * scale));
          const height = Math.max(1, Math.round(img.height * scale));
          const canvas = document.createElement("canvas");
          canvas.width = width;
          canvas.height = height;
          const ctx = canvas.getContext("2d");
          if (!ctx) throw new Error("canvas context unavailable");
          ctx.drawImage(img, 0, 0, width, height);
          resolve(canvas.toDataURL("image/jpeg", 0.82));
        } catch (error) {
          reject(error);
        } finally {
          URL.revokeObjectURL(objectUrl);
        }
      };
      img.onerror = () => {
        URL.revokeObjectURL(objectUrl);
        reject(new Error("image load failed"));
      };
      img.src = objectUrl;
    });

  // まず元画像で保存を試し、失敗したら圧縮版で再保存する
  const cacheImage = async (file, src) => {
    try {
      sessionStorage.setItem(imageKey, src);
      sessionStorage.setItem(filenameKey, file.name || "profile-image.jpg");
      return;
    } catch (_) {
      // 元画像で容量超過した時は、復元用途として軽量版を保存する。
    }

    try {
      const compressed = await compressForCache(file);
      sessionStorage.setItem(imageKey, compressed);
      sessionStorage.setItem(filenameKey, "profile-image.jpg");
      setPreview(compressed);
    } catch (_) {
      // 圧縮キャッシュも失敗したら表示のみで続行。
    }
  };

  // DataURL文字列 -> Fileオブジェクトへ戻す
  // （再送信時にinput.filesへ戻せるブラウザ向け）
  const dataUrlToFile = (dataUrl, fileName) => {
    const parts = dataUrl.split(",");
    if (parts.length !== 2) return null;
    const mimeMatch = parts[0].match(/data:(.*?);base64/);
    if (!mimeMatch) return null;
    const mime = mimeMatch[1] || "image/jpeg";
    const binary = atob(parts[1]);
    const length = binary.length;
    const bytes = new Uint8Array(length);
    for (let i = 0; i < length; i += 1) {
      bytes[i] = binary.charCodeAt(i);
    }
    return new File([bytes], fileName || "profile-image.jpg", { type: mime });
  };

  // 保存済みDataURLから、可能なら file input を復元する
  const restoreFileInput = () => {
    const cachedDataUrl = sessionStorage.getItem(imageKey);
    if (!cachedDataUrl || typeof DataTransfer === "undefined") {
      return;
    }
    try {
      const cachedName =
        sessionStorage.getItem(filenameKey) || "profile-image.jpg";
      const cachedFile = dataUrlToFile(cachedDataUrl, cachedName);
      if (!cachedFile) return;
      const dt = new DataTransfer();
      dt.items.add(cachedFile);
      input.files = dt.files;
    } catch (_) {
      // ブラウザ実装差で files 代入不可なケースはプレビューのみ保持する。
    }
  };

  // 初回表示（通常遷移）は古いキャッシュを破棄
  // formエラーで再描画された場合のみキャッシュ維持
  if (!keepCacheOnLoad) {
    clearCache();
  }

  // キャッシュがあればプレビュー復元 + file input復元を試行
  const cached = sessionStorage.getItem(imageKey);
  if (cached) {
    setPreview(cached);
    restoreFileInput();
  }

  // 画像ボタンクリックで hidden file input を開く
  button.addEventListener("click", () => input.click());

  // 画像選択時:
  // 1) プレビュー更新 2) sessionStorageへ保存
  input.addEventListener("change", () => {
    const file = input.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (e) => {
      const src = e.target?.result;
      if (typeof src !== "string") return;
      setPreview(src);
      await cacheImage(file, src);
    };
    reader.readAsDataURL(file);
  });

  // 送信直前に file input が空なら復元を再試行
  // （ブラウザ差異/再描画後の再送信に備える）
  form.addEventListener("submit", () => {
    // エラー再表示に備えて、送信直前に復元可能状態を保証する。
    if (!input.files?.length) {
      restoreFileInput();
    }
    window.loadingOverlay?.show();
  });
});

// document.addEventListener("DOMContentLoaded", initProfileImageChange);
