// Joint card: JCS definition, angle sliders driving the child segment, e1/e2/e3 and the angle arcs.
import {
  AXIS_INDEX, column, deg, elementary, fromColumns, gimbalMargin, GIMBAL_WARNING, matmul, matrixFromEuler, matvec, rad, transpose,
} from "./rotations.js";
import { BONE_MODES, boneGeometry, boneOpacity, lazyViewer, meshCorners } from "./scene.js";
import { fillSequenceTable, sequenceTable } from "./sequence_compare.js";
import { clinical, el, fmt, landmarkLabel, needsCheck, notesList, refChip, segmented, toggle } from "./ui.js";

const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const scale = (a, s) => a.map((x) => x * s);

export function mountJointCard(card, data, sided) {
  const joint = data.joints[card.dataset.joint];
  const seq = joint.sequence;
  const parent = data.segments[joint.parent], child = data.segments[joint.child];
  const state = {
    side: "R",
    angles: [...joint.geometry.R.neutral_clinical],
    show: { parent: true, child: true, jcs: true, arcs: true, labels: true },
    bones: "ghost",
  };
  const viewOpts = { view: [...joint.view] };

  // --- static text -------------------------------------------------------------------------------
  const axisName = (seg, letter) => `<var class="ax-${letter.toLowerCase()}">${letter}</var><sub>${seg.name.toLowerCase()}</sub>`;
  const eRows = [
    ["e1", `${axisName(parent, seq[0])}`, joint.axes_text.e1, joint.angles[0]],
    ["e2", "floating", joint.axes_text.e2, joint.angles[1]],
    ["e3", `${axisName(child, seq[2])}`, joint.axes_text.e3, joint.angles[2]],
  ];
  const head = el(
    "header",
    { class: "card-head" },
    el("h3", {}, joint.name),
    el(
      "div",
      { class: "meta" },
      refChip(data, joint.reference, joint.section),
      el("span", { class: "chip seq" }, `${parent.name} → ${child.name}`),
      el("span", { class: "chip seq", title: "Intrinsic rotation sequence of the child relative to the parent" }, el("code", {}, seq)),
    ),
  );
  const etable = el(
    "table",
    { class: "deftable etable" },
    el("thead", {}, el("tr", {}, el("th", {}, "Axis"), el("th", {}, "Fixed in"), el("th", {}, "Rotation (+ / −)"))),
    el(
      "tbody",
      {},
      eRows.map(([e, fixed, txt, a]) =>
        el(
          "tr",
          {},
          el("th", { class: e === "e2" ? "ax-e2" : "" }, e),
          el("td", {}, el("div", { html: fixed }), el("div", { class: "muted small" }, txt)),
          el("td", {}, el("strong", {}, a.label), el("div", { class: "small" }, `+ ${a.positive} / − ${a.negative}`), a.note ? el("div", { class: "muted small" }, a.note) : null),
        ),
      ),
    ),
  );

  // --- sliders -------------------------------------------------------------------------------------
  const sliderRows = joint.angles.map((a, i) => {
    const lo = Math.min(a.range[0], Math.floor(state.angles[i])), hi = Math.max(a.range[1], Math.ceil(state.angles[i]));
    const input = el("input", { type: "range", min: lo, max: hi, step: 0.5, "aria-label": a.label });
    const out = el("output", { class: "num" });
    input.addEventListener("input", () => {
      state.angles[i] = Number(input.value);
      update();
    });
    return { input, out, row: el("div", { class: "slider" }, el("label", {}, el("span", { class: `e-tag e${i + 1}` }, `e${i + 1}`), " ", a.label), input, out) };
  });
  const rawLine = el("p", { class: "muted small raw-line" });
  const lockLine = el("p", { class: "lock-line", "aria-live": "polite" });
  const buttons = el(
    "div",
    { class: "btn-row" },
    el("button", { type: "button", class: "btn", onclick: () => setAngles(joint.geometry[state.side].neutral_clinical) }, "Anatomical posture"),
    el("button", { type: "button", class: "btn", onclick: () => setAngles([0, 0, 0]) }, "Zero (frames aligned)"),
  );
  const { table: seqTable, tbody: seqBody } = sequenceTable();

  const text = el(
    "div",
    { class: "card-text" },
    etable,
    el("h4", {}, "Playground"),
    el("div", { class: "sliders" }, sliderRows.map((s) => s.row)),
    rawLine,
    lockLine,
    buttons,
    el("p", { class: "muted small" }, `Translations: ${joint.translations || "not reported"}`),
    needsCheck(joint.needs_check),
    notesList(joint.notes),
  );

  const viewerBox = el("div", { class: "viewer", "aria-label": "3D view of the joint coordinate system" });
  const controls = el(
    "div",
    { class: "viz-controls" },
    el(
      "div",
      { class: "viz-options" },
      sided
        ? segmented("Side", [{ value: "R", label: "Right" }, { value: "L", label: "Left" }], "R", (v) => {
            state.side = v;
            viewOpts.view = [joint.view[0], joint.view[1], v === "L" ? -joint.view[2] : joint.view[2]];
            if (view.viewer) view.viewer.view = viewOpts.view;
            view.refit();
            update();
          })
        : null,
      segmented("Bones", BONE_MODES, "ghost", (v) => ((state.bones = v), view.redraw())),
      toggle("Parent frame", true, (v) => ((state.show.parent = v), view.redraw())),
      toggle("Child frame", true, (v) => ((state.show.child = v), view.redraw())),
      toggle("e1 e2 e3", true, (v) => ((state.show.jcs = v), view.redraw())),
      toggle("Arcs", true, (v) => ((state.show.arcs = v), view.redraw())),
      toggle("Labels", true, (v) => ((state.show.labels = v), view.redraw())),
      el("button", { type: "button", class: "btn ghost", onclick: () => view.refit() }, "Reset view"),
    ),
  );
  const details = el(
    "details",
    { class: "seqcmp" },
    el("summary", {}, "Same pose in the 12 rotation sequences"),
    el(
      "p",
      { class: "muted small" },
      "The child orientation relative to the parent, decomposed with every intrinsic sequence of the same parent/child " +
        "axes (raw angles, right-hand rule). Only the ISB row matches the clinical names above. The gimbal margin is " +
        "|cos β| for Cardan and |sin β| for Euler sequences.",
    ),
    seqTable,
  );

  card.append(head, el("div", { class: "card-grid" }, text, el("div", { class: "card-viz" }, viewerBox, controls)), details);
  const view = lazyViewer(viewerBox, (v) => draw(v), viewOpts);

  function setAngles(values) {
    state.angles = [...values];
    update();
  }

  // --- kinematics -------------------------------------------------------------------------------------
  function pose() {
    const g = joint.geometry[state.side];
    const raw = state.angles.map((a, i) => a * g.signs[i]);
    const r = raw.map(rad);
    const Rp = fromColumns(...g.parent_R);
    const R1 = matmul(Rp, elementary(seq[0], r[0]));
    const R2 = matmul(R1, elementary(seq[1], r[1]));
    const Rc = matmul(R2, elementary(seq[2], r[2]));
    const Rc0 = fromColumns(...g.child_R);
    const Q = matmul(Rc, transpose(Rc0));
    const origin = add(g.pivot, matvec(Q, sub(g.child_origin, g.pivot)));
    const childPts = Object.fromEntries(Object.entries(g.child_local).map(([k, p]) => [k, add(origin, matvec(Rc, p))]));
    return { g, raw, r, Rp, R1, R2, Rc, Q, origin, childPts, Rrel: matrixFromEuler(seq, r) };
  }

  function update() {
    const p = pose();
    sliderRows.forEach((s, i) => {
      s.input.value = state.angles[i];
      s.out.textContent = clinical(state.angles[i], joint.angles[i]);
    });
    rawLine.innerHTML =
      state.side === "L"
        ? `Raw left angles (right-hand rule, Z to the right): ${p.raw.map((a) => fmt(a)).join(", ")}. ` +
          `Clinical = raw × (${p.g.signs.map((s) => (s > 0 ? "+1" : "−1")).join(", ")}): rotations about X and Y change sign on the left.`
        : `Raw angles: ${p.raw.map((a) => fmt(a)).join(", ")} (right side: raw = clinical).`;
    const margin = gimbalMargin(seq, p.r);
    lockLine.className = `lock-line ${margin < GIMBAL_WARNING ? "warn" : ""}`;
    lockLine.textContent =
      margin < GIMBAL_WARNING
        ? `Gimbal lock: e1 and e3 are nearly ${seq[0] === seq[2] ? "parallel" : "aligned with the floating axis"} (margin ${margin.toFixed(2)}). The 1st and 3rd angles cannot be separated.`
        : `Gimbal margin ${margin.toFixed(2)}`;
    const mSign = joint.middle_negative ? -1 : 1;
    fillSequenceTable(seqBody, p.Rrel, seq, state.side === "L" && seq[1] !== "Z" ? -mSign : mSign);
    view.redraw();
  }

  function draw(v) {
    v.showLabels = state.show.labels;
    const P = v.palette;
    const p = pose();
    const side = state.side;
    const parentPts = p.g.parent_landmarks;
    const parentMeshes = parent.meshes.map((g) => data.meshes.groups[g]).filter(Boolean);
    const childMeshes = child.meshes.map((g) => data.meshes.groups[g]).filter(Boolean);
    v.fit([...Object.values(parentPts), ...Object.values(p.childPts), p.g.pivot, ...meshCorners([...parentMeshes, ...childMeshes], side)]);
    const L = Math.max(30, v.size * 0.22);

    // segments: bone meshes (the child follows the sliders), or sticks when the meshes are hidden
    const opacity = boneOpacity(state.bones);
    const mirror = side === "L";
    const t = sub(p.g.pivot, matvec(p.Q, p.g.pivot));
    for (const m of parentMeshes) {
      const g = opacity > 0 && boneGeometry(m, () => view.redraw());
      if (g) v.bone(g, { opacity: Math.min(1, opacity * 0.8), mirror });
    }
    for (const m of childMeshes) {
      const g = opacity > 0 && boneGeometry(m, () => view.redraw());
      if (g) v.bone(g, { opacity, rotation: p.Q, translation: t, mirror });
    }
    if (opacity === 0 || !parentMeshes.length)
      for (const [a, b] of parent.links) if (parentPts[a] && parentPts[b]) v.cylinder(parentPts[a], parentPts[b], { color: P.bone, opacity: 0.55 });
    if (opacity === 0 || !childMeshes.length)
      for (const [a, b] of child.links) if (p.childPts[a] && p.childPts[b]) v.cylinder(p.childPts[a], p.childPts[b], { color: P.bone });
    for (const [k, pt] of Object.entries(parentPts)) v.point(pt, { color: P.landmark, radius: 3.2, opacity: 0.6, label: landmarkLabel(data, k, side) });
    for (const [k, pt] of Object.entries(p.childPts)) v.point(pt, { color: P.highlight, radius: 3.8, label: landmarkLabel(data, k, side) });

    const cols = (R) => ({ X: column(R, 0), Y: column(R, 1), Z: column(R, 2) });
    if (state.show.parent) v.frame(p.g.parent_origin, cols(p.Rp), { length: L, opacity: 0.45, radius: 1.5, suffix: "<sub>p</sub>" });
    if (state.show.child) v.frame(p.origin, cols(p.Rc), { length: L, suffix: "<sub>c</sub>" });

    const i0 = AXIS_INDEX[seq[0]], i1 = AXIS_INDEX[seq[1]], i2 = AXIS_INDEX[seq[2]];
    const e1 = column(p.Rp, i0), e2 = column(p.R1, i1), e3 = column(p.Rc, i2);
    const c = p.g.pivot;
    if (state.show.jcs) {
      const E = L * 1.5;
      v.arrow(add(c, scale(e1, -E * 0.35)), scale(e1, E * 1.35), { color: P[seq[0]], radius: 1.2, label: "e1", labelClass: "keep e-lbl" });
      v.arrow(add(c, scale(e2, -E * 0.35)), scale(e2, E * 1.35), { color: P.e2, radius: 1.2, dashed: true, label: "e2", labelClass: "keep e-lbl" });
      v.arrow(add(c, scale(e3, -E * 0.35)), scale(e3, E * 1.35), { color: P[seq[2]], radius: 1.2, label: "e3", labelClass: "keep e-lbl" });
    }
    if (state.show.arcs) {
      v.arc(c, e1, column(p.Rp, i1), p.r[0], L * 0.55, { color: P[seq[0]], label: fmt(p.raw[0]), labelClass: "arc-lbl keep" });
      v.arc(c, e2, column(p.R1, i2), p.r[1], L * 0.75, { color: P.e2, label: fmt(p.raw[1]), labelClass: "arc-lbl keep" });
      v.arc(c, e3, column(p.R2, i1), p.r[2], L * 0.4, { color: P[seq[2]], label: fmt(p.raw[2]), labelClass: "arc-lbl keep" });
    }
    v.point(c, { color: P.e2, radius: 2.6 });
  }

  update();
}
