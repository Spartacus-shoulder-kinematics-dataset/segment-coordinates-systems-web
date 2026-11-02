// The same relative orientation expressed in all 12 intrinsic sequences.
import { deg, eulerFromMatrix, gimbalMargin, GIMBAL_WARNING, isProperEuler, SEQUENCES } from "./rotations.js";
import { el, fmt } from "./ui.js";

export function sequenceTable() {
  const tbody = el("tbody");
  const table = el(
    "table",
    { class: "seqtable" },
    el(
      "thead",
      {},
      el("tr", {}, el("th", {}, "Sequence"), el("th", {}, "1st"), el("th", {}, "2nd"), el("th", {}, "3rd"), el("th", {}, "Gimbal margin")),
    ),
    tbody,
  );
  return { table, tbody };
}

/**
 * Fill the table for relative rotation R. `highlight` is the reference (ISB) sequence, decomposed with
 * `highlightMiddleSign`; the others use the default ranges (Cardan middle in ±90°, Euler middle in 0–180°).
 * `onPick(seq)` makes rows clickable.
 */
export function fillSequenceTable(tbody, R, highlight, highlightMiddleSign = 1, onPick = null) {
  tbody.replaceChildren(
    ...SEQUENCES.map((seq) => {
      const angles = eulerFromMatrix(seq, R, seq === highlight ? highlightMiddleSign : 1);
      const margin = gimbalMargin(seq, angles);
      const warn = margin < GIMBAL_WARNING;
      const row = el(
        "tr",
        {
          class: `${seq === highlight ? "isb" : ""} ${warn ? "warn" : ""} ${onPick ? "pickable" : ""}`,
          onclick: onPick ? () => onPick(seq) : null,
          title: warn ? "Close to gimbal lock: 1st and 3rd angles are poorly defined" : "",
        },
        el(
          "td",
          {},
          el("code", {}, seq),
          el("span", { class: "muted" }, isProperEuler(seq) ? " Euler" : " Cardan"),
          seq === highlight ? el("span", { class: "chip small" }, "ISB") : null,
        ),
        ...angles.map((a) => el("td", { class: "num" }, fmt(deg(a)))),
        el(
          "td",
          {},
          el("span", { class: "meter" }, el("span", { style: `width:${(margin * 100).toFixed(0)}%` })),
          warn ? el("span", { class: "warn-text" }, " lock") : null,
        ),
      );
      return row;
    }),
  );
}
