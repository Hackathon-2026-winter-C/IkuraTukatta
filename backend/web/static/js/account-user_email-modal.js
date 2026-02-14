document.addEventListener("DOMContentLoaded", () => {
  const openBtn = document.getElementById("open-user-email-modal");
  const modal = document.getElementById("user-email-modal");
  const bg = document.getElementById("user-email-modal-bg");
  const closeBtns =
    modal?.querySelectorAll("[data-close-user-email-modal]") || [];

  if (!openBtn || !modal || !bg) return;

  const open = () => {
    modal.classList.remove("hidden");
    document.body.classList.add("overflow-hidden");
    modal.querySelector("input,button,textarea,select")?.focus();
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
});
