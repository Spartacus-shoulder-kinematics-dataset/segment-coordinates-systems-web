// Generic rotation-sequence explorer: pick a sequence and three angles, see the intermediate frames,
// the rotation axes (e1, floating e2, e3) and the same orientation in every other sequence.
import {
  AXIS_INDEX, column, deg, elementary, eulerFromMatrix, gimbalMargin, GIMBAL_WARNING, isProperEuler, matmul, rad, SEQUENCES,
} from "./rotations.js";
import { lazyViewer } from "./scene.js";
import { fillSequenceTable, sequenceTable } from "./sequence_compare.js";
import { el, fmt, toggle } from "./ui.js";

const scale = (a, s) => a.map((x) => x * s);
const I = [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
const cols = (R) => ({ X: column(R, 0), Y: column(R, 1), Z: column(R, 2) });
// a small "limb" attached to the child frame, to make its orientation readable
const BODY = [[0, 0, 0], [0, -90, 0], [18, -90, 0], [0, -90, 12]];

export function mountSequenceTool(root, { sequence = "ZXY", angles = [30, 20, 10], table = true } = {}) {
  const state = { seq: sequence, angles: [...angles], steps: true, labels: true };

  const select = el(
    "select",
    { "aria-label": "Rotation sequence", onchange: (e) => changeSequence(e.target.value) },
    SEQUENCES.map((s) => el("option", { value: s }, `${s} ${isProperEuler(s) ? "(Euler)" : "(Cardan)"}`)),
  );
  select.value = state.seq;
  const sliders = [0, 1, 2].map((i) => {
    const input = el("input", { type: "range", step: 0.5 });
    const out = el("output", { class: "num" });
    const name = el("span");
    input.addEventListener("input", () => {
      state.angles[i] = Number(input.value);
      update();
    });
    return { input, out, name, row: el("div", { class: "slider" }, el("label", {}, el("span", { class: `e-tag e${i + 1}` }, `e${i + 1}`), " ", name), input, out) };
  });
  const lockLine = el("p", { class: "lock-line", "aria-live": "polite" });
  const formula = el("p", { class: "formula small" });
  const { table: seqTable, tbody } = sequenceTable();

  const viewerBox = el("div", { class: "viewer tall" });
  root.append(
    el(
      "div",
      { class: "card-grid" },
      el(
        "div",
        { class: "card-text" },
        el("label", { class: "field" }, "Sequence ", select),
        formula,
        el("div", { class: "sliders" }, sliders.map((s) => s.row)),
        lockLine,
        el(
          "div",
          { class: "btn-row" },
          el("button", { type: "button", class: "btn", onclick: () => set([0, 0, 0]) }, "Zero"),
          el("button", { type: "button", class: "btn", onclick: () => set([30, isProperEuler(state.seq) ? 0 : 90, 20]) }, "Gimbal lock"),
          el("button", { type: "button", class: "btn", onclick: () => set([30, 20, 10]) }, "Example"),
        ),
      ),
      el(
        "div",
        { class: "card-viz" },
        viewerBox,
        el(
          "div",
          { class: "viz-controls" },
          el(
            "div",
            { class: "viz-options" },
            toggle("Intermediate frames", true, (v) => ((state.steps = v), view.redraw())),
            toggle("Labels", true, (v) => ((state.labels = v), view.redraw())),
            el("button", { type: "button", class: "btn ghost", onclick: () => view.refit() }, "Reset view"),
          ),
        ),
      ),
    ),
    table
      ? el(
          "div",
          { class: "seqcmp open" },
          el("h4", {}, "The same orientation in all 12 sequences"),
          el("p", { class: "muted small" }, "Click a row to switch to that sequence without changing the orientation."),
          seqTable,
        )
      : "",
  );
  const view = lazyViewer(viewerBox, (v) => draw(v), { view: [1, 0.45, 0.9] });

  function set(values) {
    state.angles = [...values];
    update();
  }

  function changeSequence(seq) {
    const R = matrices().R;
    state.seq = seq;
    select.value = seq;
    state.angles = eulerFromMatrix(seq, R).map(deg);
    update();
  }

  function matrices() {
    const [a, b, c] = state.angles.map(rad);
    const s = state.seq;
    const R1 = elementary(s[0], a);
    const R2 = matmul(R1, elementary(s[1], b));
    const R = matmul(R2, elementary(s[2], c));
    return { R1, R2, R };
  }

  function update() {
    const s = state.seq;
    const ranges = [[-180, 180], isProperEuler(s) ? [-180, 180] : [-90, 90], [-180, 180]];
    sliders.forEach((sl, i) => {
      sl.input.min = ranges[i][0];
      sl.input.max = ranges[i][1];
      sl.input.value = state.angles[i];
      sl.out.textContent = fmt(state.angles[i]);
      sl.name.innerHTML = `about ${i === 0 ? "" : i === 1 ? "rotated " : "twice-rotated "}<var class="ax-${s[i].toLowerCase()}">${s[i]}</var>${"′".repeat(i)}`;
    });
    formula.innerHTML = `R = R<sub>${s[0]}</sub>(α) · R<sub>${s[1]}</sub>(β) · R<sub>${s[2]}</sub>(γ) &nbsp;— intrinsic: each rotation is about an axis of the frame produced by the previous one.`;
    const margin = gimbalMargin(s, state.angles.map(rad));
    lockLine.className = `lock-line ${margin < GIMBAL_WARNING ? "warn" : ""}`;
    lockLine.textContent =
      margin < GIMBAL_WARNING
        ? `Gimbal lock (margin ${margin.toFixed(2)}): the 1st and 3rd rotation axes coincide, only their sum (or difference) is defined.`
        : `Gimbal margin ${margin.toFixed(2)} (${isProperEuler(s) ? "|sin β|" : "|cos β|"})`;
    fillSequenceTable(tbody, matrices().R, s, 1, changeSequence);
    view.redraw();
  }

  function draw(v) {
    v.showLabels = state.labels;
    const P = v.palette;
    const { R1, R2, R } = matrices();
    const s = state.seq;
    const o = [0, 0, 0];
    v.fit([[-100, -100, -100], [100, 100, 100]]);
    const L = 70;
    v.frame(o, cols(I), { length: L, opacity: 0.4, dashed: true, radius: 1.3, suffix: "<sub>0</sub>" });
    if (state.steps) {
      v.frame(o, cols(R1), { length: L * 0.8, opacity: 0.3, radius: 1.1, suffix: "′" });
      v.frame(o, cols(R2), { length: L * 0.9, opacity: 0.3, radius: 1.1, suffix: "″" });
    }
    v.frame(o, cols(R), { length: L * 1.15, radius: 2, suffix: "‴" });
    const body = BODY.map((p) => [0, 1, 2].map((i) => R[i][0] * p[0] + R[i][1] * p[1] + R[i][2] * p[2]));
    v.cylinder(body[0], body[1], { color: P.bone, radius: 3 });
    v.cylinder(body[1], body[2], { color: P.bone, radius: 2 });
    v.cylinder(body[1], body[3], { color: P.bone, radius: 2 });
    const i0 = AXIS_INDEX[s[0]], i1 = AXIS_INDEX[s[1]], i2 = AXIS_INDEX[s[2]];
    const r = state.angles.map(rad);
    const e1 = column(I, i0), e2 = column(R1, i1), e3 = column(R, i2);
    v.arrow(scale(e1, -L * 1.3), scale(e1, L * 2.9), { color: P[s[0]], radius: 0.9, label: "e1", labelClass: "keep e-lbl" });
    v.arrow(scale(e2, -L * 1.3), scale(e2, L * 2.9), { color: P.e2, radius: 0.9, dashed: true, label: "e2", labelClass: "keep e-lbl" });
    v.arrow(scale(e3, -L * 1.3), scale(e3, L * 2.9), { color: P[s[2]], radius: 0.9, label: "e3", labelClass: "keep e-lbl" });
    v.arc(o, e1, column(I, i1), r[0], L * 0.55, { color: P[s[0]], label: "α", labelClass: "arc-lbl keep" });
    v.arc(o, e2, column(R1, i2), r[1], L * 0.75, { color: P.e2, label: "β", labelClass: "arc-lbl keep" });
    v.arc(o, e3, column(R2, i1), r[2], L * 0.4, { color: P[s[2]], label: "γ", labelClass: "arc-lbl keep" });
  }

  update();
}
