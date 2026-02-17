document.addEventListener("DOMContentLoaded", () => {
  const openBtn = document.getElementById("open-account-delete-modal");
  const modal = document.getElementById("account-delete-modal");
  const bg = document.getElementById("account-delete-modal-bg");
  const confirmBtn = document.getElementById("account-delete-confirm");
  const closeBtns =
    modal?.querySelectorAll("[data-close-account-delete-modal]") || [];

  if (!openBtn || !modal || !bg || !confirmBtn) return;

  const getCookie = (name) => {
    const v = `; ${document.cookie}`;
    const p = v.split(`; ${name}=`);
    if (p.length === 2) return p.pop().split(";").shift();
    return "";
  };

  const open = () => {
    modal.classList.remove("hidden");
    document.body.classList.add("overflow-hidden");
  };

  const close = () => {
    modal.classList.add("hidden");
    document.body.classList.remove("overflow-hidden");
  };

  openBtn.addEventListener("click", open);
  bg.addEventListener("click", close);
  closeBtns.forEach((btn) => btn.addEventListener("click", close));

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !modal.classList.contains("hidden")) close();
  });

  confirmBtn.addEventListener("click", async () => {
    confirmBtn.disabled = true;
    try {
      const res = await fetch("/api/account/delete/", {
        method: "POST",
        headers: { "X-CSRFToken": getCookie("csrftoken") },
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data.ok) {
        throw new Error(data.error || "削除に失敗しました");
      }
      window.location.href = "/login/";
    } catch (err) {
      alert(err?.message || "エラーが発生しました");
    } finally {
      confirmBtn.disabled = false;
    }
  });
});
