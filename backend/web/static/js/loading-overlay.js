const overlayEl = document.getElementById("upload-loading-overlay");

window.loadingOverlay = {
  show() {
    if (!overlayEl) return;
    overlayEl.classList.remove("hidden");
    overlayEl.classList.add("flex");
  },
  hide() {
    if (!overlayEl) return;
    overlayEl.classList.add("hidden");
    overlayEl.classList.remove("flex");
  },
};
