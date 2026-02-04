const getCookie = (name) =>
  document.cookie
    .split("; ")
    .find((row) => row.startsWith(name + "="))
    ?.split("=")[1];

const btn = document.querySelector("[data-logout]");
if (btn) {
  btn.addEventListener("click", () => {
    const url = btn.dataset.logoutUrl;
    window.location.href = url; // GETで/logoutへ → view側でloginへリダイレクト
  });
}
