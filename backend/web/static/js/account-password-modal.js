document.addEventListener("DOMContentLoaded", () => {
  const openBtn = document.getElementById("open-user-password-modal");
  const modal = document.getElementById("user-password-modal");
  const bg = document.getElementById("user-password-modal-bg");
  const closeBtns =
    modal?.querySelectorAll("[data-close-user-password-modal]") || [];
  const currentPasswordInput = document.getElementById("current-password-input");
  const newPasswordInput = document.getElementById("new-password-input");
  const confirmPasswordInput = document.getElementById("confirm-password-input");
  const submitBtn = document.getElementById("submit-user-password");
  const errorEl = document.getElementById("user-password-error");

  if (
    !openBtn ||
    !modal ||
    !bg ||
    !currentPasswordInput ||
    !newPasswordInput ||
    !confirmPasswordInput ||
    !submitBtn
  ) {
    return;
  }

  const getCookie = (name) => {
    const v = `; ${document.cookie}`;
    const p = v.split(`; ${name}=`);
    if (p.length === 2) return p.pop().split(";").shift();
    return "";
  };

  const hideError = () => {
    if (!errorEl) return;
    errorEl.textContent = "";
    errorEl.classList.add("hidden");
  };

  const showError = (message) => {
    if (!errorEl) {
      alert(message);
      return;
    }
    errorEl.textContent = message;
    errorEl.classList.remove("hidden");
  };

  const resetForm = () => {
    currentPasswordInput.value = "";
    newPasswordInput.value = "";
    confirmPasswordInput.value = "";
    hideError();
  };

  const open = () => {
    modal.classList.remove("hidden");
    document.body.classList.add("overflow-hidden");
    hideError();
    currentPasswordInput.focus();
  };

  const close = () => {
    modal.classList.add("hidden");
    document.body.classList.remove("overflow-hidden");
    resetForm();
  };

  openBtn.addEventListener("click", open);
  bg.addEventListener("click", close);
  closeBtns.forEach((btn) => btn.addEventListener("click", close));

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !modal.classList.contains("hidden")) {
      close();
    }
  });

  submitBtn.addEventListener("click", async () => {
    const currentPassword = currentPasswordInput.value;
    const newPassword = newPasswordInput.value;
    const newPasswordConfirm = confirmPasswordInput.value;

    if (!currentPassword || !newPassword || !newPasswordConfirm) {
      showError("すべての項目を入力してください");
      return;
    }

    hideError();
    submitBtn.disabled = true;

    try {
      const res = await fetch("/api/account/password/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
          new_password_confirm: newPasswordConfirm,
        }),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data.ok) {
        throw new Error(data.error || "パスワードの更新に失敗しました");
      }

      close();
      window.location.reload();
    } catch (err) {
      showError(err.message || "エラーが発生しました");
    } finally {
      submitBtn.disabled = false;
    }
  });
});
