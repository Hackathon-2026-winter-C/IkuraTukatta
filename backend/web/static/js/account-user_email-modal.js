document.addEventListener("DOMContentLoaded", () => {
  const openBtn = document.getElementById("open-user-email-modal");
  const modal = document.getElementById("user-email-modal");
  const bg = document.getElementById("user-email-modal-bg");
  const closeBtns =
    modal?.querySelectorAll("[data-close-user-email-modal]") || [];
  const emailInput = document.getElementById("user-email-input");
  const submitBtn = document.getElementById("submit-user-email");
  const errorEl = document.getElementById("user-email-error");

  if (!openBtn || !modal || !bg || !emailInput || !submitBtn) return;

  const getCookie = (name) => {
    const v = `; ${document.cookie}`;
    const p = v.split(`; ${name}=`);
    if (p.length === 2) return p.pop().split(";").shift();
    return "";
  };

  const open = () => {
    modal.classList.remove("hidden");
    document.body.classList.add("overflow-hidden");
    emailInput.focus();
  };

  const close = () => {
    modal.classList.add("hidden");
    document.body.classList.remove("overflow-hidden");
    modal.dispatchEvent(new CustomEvent("user-email-modal:closed"));
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
    const email = emailInput.value.trim();
    if (!email) {
      if (errorEl) {
        errorEl.textContent = "メールアドレスを入力してください";
        errorEl.classList.remove("hidden");
      } else {
        alert("メールアドレスを入力してください");
      }
      return;
    }

    if (errorEl) errorEl.classList.add("hidden");
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

      const data = await res.json();
      if (!res.ok || !data.ok) {
        throw new Error(data.error || "メールアドレスの更新に失敗しました");
      }

      // 成功後はページを再読み込みして表示値を最新化
      window.location.reload();
    } catch (err) {
      if (errorEl) {
        errorEl.textContent = err.message || "エラーが発生しました";
        errorEl.classList.remove("hidden");
      } else {
        alert(err.message || "エラーが発生しました");
      }
    } finally {
      submitBtn.disabled = false;
    }
  });
});
