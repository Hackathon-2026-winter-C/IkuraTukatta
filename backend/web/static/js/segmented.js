window.initSegmented = function initSegmented({ rootId, sliderId, radioName }) {
  const root = document.getElementById(rootId);
  const slider = document.getElementById(sliderId);
  if (!root || !slider) return;

  const radios = Array.from(root.querySelectorAll(`input[name="${radioName}"]`));
  if (!radios.length) return;

  const move = () => {
    const checkedIndex = radios.findIndex((r) => r.checked);
    const idx = checkedIndex >= 0 ? checkedIndex : 0;

    const rootW = root.clientWidth;
    const padding = 4; // p-1 (=4px) 前提
    const innerW = rootW - padding * 2;

    const count = radios.length || 1;
    const w = innerW / count;

    slider.style.width = `${w}px`;
    slider.style.left = `${padding + w * idx}px`;
  };

  move();
  radios.forEach((r) => r.addEventListener("change", move));
  window.addEventListener("resize", move);
};
