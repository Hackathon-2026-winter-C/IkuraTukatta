// static/js/moneyflow_form.js

  // ----- segmented (Record) -----
  initSegmented({
    rootId: "record-seg",
    sliderId: "seg-slider",
    radioName: "record-mode",
  });

  // ---------- amount ----------
  const amountDisplay = document.getElementById("amount_display");
  const amountHidden = document.getElementById("amount");

  const formatJPY = (digits) => {
    if (!digits) return "";
    digits = digits.replace(/^0+(?=\d)/, "");
    return digits.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  };

  const syncAmount = () => {
    const digits = amountDisplay.value.replace(/[^\d]/g, "");
    amountHidden.value = digits;
    amountDisplay.value = formatJPY(digits);
  };

  if (amountDisplay && amountHidden) {
    if (amountHidden.value) {
      amountDisplay.value = formatJPY(amountHidden.value.replace(/[^\d]/g, ""));
    }
    amountDisplay.addEventListener("input", syncAmount);
    amountDisplay.addEventListener("blur", syncAmount);
  }

  // ---------- error helpers ----------
  const showError = (el, msg) => {
    el.textContent = msg;
    el.classList.remove("hidden");
  };
  const clearError = (el) => {
    el.textContent = "";
    el.classList.add("hidden");
  };

  const amountError = document.getElementById("amount-error");
  const dateError = document.getElementById("date-error");
  const categoryError = document.getElementById("category-error");

  // ✅ FIX: メインフォームをidで取得（削除フォームに誤爆しない）
  const form = document.getElementById("record-form");
  const submitBtn = document.getElementById("submit-btn");

  const categoryHidden = document.getElementById("category_id");

  // ✅ FIX: date inputもidで取得（安全）
  const dateInput = document.getElementById("date-input");
  const dateWrap = document.getElementById("date-wrap");
  const dateText = document.getElementById("date-text");

  // ---------- date picker ----------
  if (dateWrap && dateInput) {
    const openDatePicker = () => {
      try {
        if (typeof dateInput.showPicker === "function") {
          dateInput.showPicker();
          return;
        }
      } catch (_) {}
      dateInput.focus({ preventScroll: true });
      dateInput.click();
    };

    dateWrap.addEventListener("click", () => openDatePicker());

    if (dateText) {
      dateInput.addEventListener("change", () => {
        if (dateInput.value) dateText.textContent = dateInput.value;
      });
    }
  }

  // ---------- submit state ----------
  const syncHiddenCategoryFromSelected = () => {
    if (!categoryHidden) return "";
    const hiddenCategoryId = String(categoryHidden.value || "").trim();
    if (hiddenCategoryId) return hiddenCategoryId;

    const selected = document.querySelector(".cat-pick.is-selected");
    const selectedId = selected ? String(selected.dataset.id || "").trim() : "";
    if (selectedId) {
      categoryHidden.value = selectedId;
      return selectedId;
    }
    return "";
  };

  const updateSubmitState = () => {
    const hasCategory = syncHiddenCategoryFromSelected() !== "";
    if (submitBtn) submitBtn.disabled = !hasCategory;
  };
  window.updateRecordSubmitState = updateSubmitState;

  updateSubmitState();

  // ---------- category ----------
  const picks = document.querySelectorAll(".cat-pick");

  if (categoryHidden) {
    const initial = categoryHidden.value;

    categoryHidden.addEventListener("change", () => {
      if (categoryError) clearError(categoryError);
      updateSubmitState();
    });

    if (initial) {
      picks.forEach((btn) => {
        if (btn.dataset.id === String(initial)) btn.classList.add("is-selected");
      });
    }

    picks.forEach((btn) => {
      btn.addEventListener("click", () => {
        categoryHidden.value = btn.dataset.id;
        picks.forEach((x) => x.classList.remove("is-selected"));
        btn.classList.add("is-selected");
        categoryHidden.dispatchEvent(new Event("change", { bubbles: true }));
      });
    });

    // レシート解析側で class だけ先に変わった場合にも submit 状態を同期する。
    const observer = new MutationObserver(() => updateSubmitState());
    picks.forEach((btn) => {
      observer.observe(btn, { attributes: true, attributeFilter: ["class"] });
    });
  }

  // ---------- validation ----------
  let isSubmitting = false;

  if (form) {
    form.addEventListener("submit", (e) => {
      if (isSubmitting) {
        e.preventDefault();
        return;
      }

      if (amountError) clearError(amountError);
      if (dateError) clearError(dateError);
      if (categoryError) clearError(categoryError);

      const amount = amountHidden ? amountHidden.value : "";
      if (!amount || Number(amount) <= 0) {
        e.preventDefault();
        if (amountError) showError(amountError, "金額は1円以上にしてね");
        return;
      }

      const ds = dateInput ? dateInput.value : "";
      if (!ds) {
        e.preventDefault();
        if (dateError) showError(dateError, "日付を入れてね");
        return;
      }

      const catId = syncHiddenCategoryFromSelected();
      if (!catId) {
        e.preventDefault();
        if (categoryError) showError(categoryError, "カテゴリを選んでね");
        updateSubmitState();
        return;
      }

      isSubmitting = true;
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = "保存中…";
      }
    });
  }

  // ---------- mode switch ----------
  const modeMap = {
    "rec-exp": "expense",
    "rec-inc": "income",
    "rec-receipt": "receipt",
  };

  document.querySelectorAll('input[name="record-mode"]').forEach((radio) => {
    radio.addEventListener("change", () => {
      const mode = modeMap[radio.id];
      if (!mode) return;

      const url = new URL(window.location.href);
      url.searchParams.set("mode", mode);

      if (window.IS_ENTRY_MODE) {
        url.searchParams.set("id", window.ENTRY_ID);
      }
      window.location.href = url.toString();
    });
  });

