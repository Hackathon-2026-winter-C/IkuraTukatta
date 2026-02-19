document.addEventListener("DOMContentLoaded", () => {
  const openBtn = document.getElementById("open-username-modal");
  const modal = document.getElementById("username-modal");
  const bg = document.getElementById("username-modal-bg");
  const closeBtns =
    modal?.querySelectorAll("[data-close-username-modal]") || [];
  const usernameInput = document.getElementById("username-input");
  const submitBtn = document.getElementById("submit-username");

  if (!openBtn || !modal || !bg || !usernameInput || !submitBtn) return;

  const getCookie = (name) => {
    const v = `; ${document.cookie}`;
    const p = v.split(`; ${name}=`);
    if (p.length === 2) return p.pop().split(";").shift();
    return "";
  };

  const open = () => {
    modal.classList.remove("hidden");
    document.body.classList.add("overflow-hidden");
    usernameInput.focus();
  };

  const close = () => {
    modal.classList.add("hidden");
    document.body.classList.remove("overflow-hidden");
    modal.dispatchEvent(new CustomEvent("username-modal:closed"));
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
    const username = usernameInput.value.trim();
    if (!username) {
      alert("ユーザーネームを入力してください");
      return;
    }

    submitBtn.disabled = true;
    try {
      const res = await fetch("/api/account/username/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({ username }),
      });

      const data = await res.json();
      if (!res.ok || !data.ok) {
        throw new Error(data.error || "ユーザーネームの更新に失敗しました");
      }

      // 成功後はページを再読み込みして表示値を最新化
      window.location.reload();
    } catch (err) {
      alert(err.message || "エラーが発生しました");
    } finally {
      submitBtn.disabled = false;
    }
  });
});
