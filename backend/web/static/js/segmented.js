window.initSegmented = function initSegmented({
  rootId,
  sliderId,
  radioName,
  durationMs = 300,
  longJumpMs = null,
}) {
  const root = document.getElementById(rootId);
  const slider = document.getElementById(sliderId);
  if (!root || !slider) return;

  const radios = Array.from(root.querySelectorAll(`input[name="${radioName}"]`));
  if (!radios.length) return;

  const toMs = (value, fallback) => {
    const n = Number(value);
    return Number.isFinite(n) ? Math.max(0, n) : fallback;
  };

  const singleMs = toMs(durationMs, 300);
  const totalLongMs = toMs(longJumpMs, singleMs * 2);
  const longStepMs = Math.round(totalLongMs / 2);

  let prevIndex = 0;
  let animSeq = 0;

  const move = (opts = {}) => {
    const checkedIndex = radios.findIndex((r) => r.checked);
    const idx = checkedIndex >= 0 ? checkedIndex : 0;

    const rootW = root.clientWidth;
    const padding = 4; // p-1 (=4px) 前提
    const innerW = rootW - padding * 2;

    const count = radios.length || 1;
    const w = innerW / count;

    const targetLeft = padding + w * idx;

    if (opts.instant) {
      slider.style.transitionDuration = "0ms";
      slider.style.width = `${w}px`;
      slider.style.left = `${targetLeft}px`;
      prevIndex = idx;
      return;
    }

    const delta = Math.abs(idx - prevIndex);
    if (delta <= 1) {
      slider.style.transitionDuration = `${singleMs}ms`;
      slider.style.width = `${w}px`;
      slider.style.left = `${targetLeft}px`;
      prevIndex = idx;
      return;
    }

    const midIdx = prevIndex + Math.sign(idx - prevIndex);
    const midLeft = padding + w * midIdx;
    const seq = ++animSeq;

    slider.style.transitionDuration = `${longStepMs}ms`;
    slider.style.width = `${w}px`;
    slider.style.left = `${midLeft}px`;
    prevIndex = idx;

    slider.addEventListener(
      "transitionend",
      (e) => {
        if (e.propertyName !== "left" || seq !== animSeq) return;
        slider.style.transitionDuration = `${longStepMs}ms`;
        slider.style.left = `${targetLeft}px`;
      },
      { once: true }
    );
  };

  move();
  radios.forEach((r) => r.addEventListener("change", move));
  window.addEventListener("resize", () => move({ instant: true }));
};
