document.addEventListener("DOMContentLoaded", () => {
  const openBtn = document.getElementById("open-user-email-modal");
  const modal = document.getElementById("user-email-modal");
  const bg = document.getElementById("user-email-modal-bg");
  const closeBtns =
    modal?.querySelectorAll("[data-close-user-email-modal]") || [];
  const input = document.getElementById("user-email-input");
  const submitBtn = document.getElementById("user-email-submit");
  const errEl = document.getElementById("user-email-error");
  const displayEl = document.getElementById("account-user-email-text");

  if (!openBtn || !modal || !bg || !input || !submitBtn || !errEl) return;

  const open = () => {
    modal.classList.remove("hidden");
    document.body.classList.add("overflow-hidden");
    errEl.classList.add("hidden");
    input.focus();
  };

  const close = () => {
    modal.classList.add("hidden");
    document.body.classList.remove("overflow-hidden");
    modal.dispatchEvent(new CustomEvent("user-email-modal:closed"));
  };

  const getCookie = (name) => {
    const v = `; ${document.cookie}`;
    const p = v.split(`; ${name}=`);
    if (p.length === 2) return p.pop().split(";").shift();
    return "";
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
    errEl.classList.add("hidden");
    const email = (input.value || "").trim();
    if (!email) {
      errEl.textContent = "メールアドレスを入力してください";
      errEl.classList.remove("hidden");
      return;
    }

    submitBtn.disabled = true;
    try {
      const res = await fetch("/api/account/email/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({ email }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data.ok) {
        throw new Error(data.error || "更新に失敗しました");
      }

      if (displayEl) displayEl.textContent = email;
      close();
    } catch (err) {
      errEl.textContent = err?.message || "エラーが発生しました";
      errEl.classList.remove("hidden");
    } finally {
      submitBtn.disabled = false;
    }
  });
});
