document.addEventListener("DOMContentLoaded", () => {
  const openBtn = document.getElementById("receipt-open-btn");
  const fileInput = document.getElementById("receipt-image-input");
  const amountDisplay = document.getElementById("amount_display");
  const amountHidden = document.getElementById("amount");
  const dateInput = document.getElementById("date-input");
  const dateText = document.getElementById("date-text");
  const getCookie = (name) => window.appUtils?.getCookie?.(name) || null;

  if (!openBtn || !fileInput) return;

  const sendReceiptToApi = async (file) => {
    const fd = new FormData();
    fd.append("receipt_image", file);

    const res = await fetch("/api/receipts/analyze/", {
      method: "POST",
      headers: { "X-CSRFToken": getCookie("csrftoken") || "" },
      body: fd,
      credentials: "same-origin",
    });

    const data = await res.json();
    if (!res.ok || !data.ok) {
      const detail = data.detail ? ` (${data.detail})` : "";
      throw new Error(`${data.error || "analyze_failed"}${detail}`);
    }
    return data.result;
  };

  const formatJPY = (value) => {
    const digits = String(value ?? "")
      .replace(/[^\d]/g, "")
      .replace(/^0+(?=\d)/, "");
    if (!digits) return "";
    return digits.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  };

  const normalizeDate = (value) => {
    if (!value || typeof value !== "string") return "";
    const trimmed = value.trim();
    // YYYY-MM-DD のみ受け入れる
    return /^\d{4}-\d{2}-\d{2}$/.test(trimmed) ? trimmed : "";
  };

  const applyReceiptResultToForm = (result) => {
    if (!result || typeof result !== "object") return;

    const amountCandidate = result.total_amount ?? result.amount ?? null;
    const amountDigits = String(amountCandidate ?? "").replace(/[^\d]/g, "");
    if (amountDigits && amountHidden && amountDisplay) {
      amountHidden.value = amountDigits;
      amountDisplay.value = formatJPY(amountDigits);
    }

    const parsedDate = normalizeDate(result.date);
    if (parsedDate && dateInput) {
      dateInput.value = parsedDate;
      if (dateText) dateText.textContent = parsedDate;
    }
  };

  // レシートボタン押下 -> hidden file input を開く
  openBtn.addEventListener("click", () => {
    fileInput.click();
  });

  // 選択後の処理
  fileInput.addEventListener("change", async () => {
    const file = fileInput.files?.[0];
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      alert("画像ファイルを選択してください");
      fileInput.value = "";
      return;
    }

    window.loadingOverlay?.show();
    try {
      const result = await sendReceiptToApi(file);
      console.log("receipt analyze result:", result);
      applyReceiptResultToForm(result);
    } catch (error) {
      console.error(error);
      alert(`レシート解析に失敗しました: ${error.message || "unknown_error"}`);
    } finally {
      window.loadingOverlay?.hide();
      fileInput.value = "";
    }
  });
});
