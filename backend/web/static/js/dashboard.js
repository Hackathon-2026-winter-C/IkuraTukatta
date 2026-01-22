const SELECT_BG = "bg-amber-500";
const SELECT_TEXT = "text-white";
const SELECT_BOLD = "font-bold";

const days = document.querySelectorAll(".calendar-day");
let selected = document.querySelector('.calendar-day[data-selected="1"]');

if (selected && selected.dataset.hover) {
  selected.classList.remove(selected.dataset.hover);
}
if (selected && !selected.classList.contains(SELECT_BOLD)) {
  selected.classList.add(SELECT_BOLD);
}

days.forEach((el) => {
  el.addEventListener("click", () => {
    if (selected) {
      selected.classList.remove(SELECT_BG, SELECT_TEXT, SELECT_BOLD);
      selected.classList.add(
        // htmlのdata-base-bgが"data-"以降がキャメルケースに変更されているためbaseBg
        selected.dataset.baseBg,
        selected.dataset.baseText,
      );
      if (selected.dataset.hover)
        selected.classList.add(selected.dataset.hover);
    }

    if (el.dataset.hover) el.classList.remove(el.dataset.hover);
    el.classList.remove(el.dataset.baseBg, el.dataset.baseText);
    el.classList.add(SELECT_BG, SELECT_TEXT, SELECT_BOLD);
    selected = el;
  });
});
