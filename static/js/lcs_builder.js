// Segment card: definition, step-by-step construction and a 3D view of each step.
import { BONE_MODES, boneGeometry, boneOpacity, lazyViewer, meshCorners } from "./scene.js";
import { el, landmarkLabel, needsCheck, notesList, refChip, segmented, toggle } from "./ui.js";

const AXIS_NAMES = { o: "Origin", X: "X", Y: "Y", Z: "Z" };

/** Construction steps plus the pseudo steps "left-side rule" and "final frame". */
function stepsFor(seg, side) {
  const steps = seg.steps.map((s) => ({ ...s, type: "step" }));
  const flipped = seg.geometry[side].flipped;
  if (side === "L" && flipped.length) {
    steps.push({
      type: "left",
      label: "Left side",
      html: `flip ${flipped.map((a) => `<var class="ax-${a.toLowerCase()}">${a}</var>`).join(", ")}`,
      text:
        "The formulas above, applied to the mirrored (left) landmarks, give a frame whose " +
        `${flipped.join(" and ")} ${flipped.length > 1 ? "axes point" : "axis points"} the opposite way to the ` +
        "ISB orientation. Flipping them restores X anterior, Y superior and Z to the right: R_left = M R_right M " +
        "with M = diag(1, 1, −1).",
    });
  }
  steps.push({
    type: "frame",
    label: "Frame",
    html: "(O; X, Y, Z)",
    text: "The segment coordinate system: origin and orthonormal, right-handed axes.",
  });
  return steps;
}

export function mountSegmentCard(card, data, sided) {
  const keys = JSON.parse(card.dataset.segments);
  const state = { key: keys[0], side: "R", step: 0, labels: true, t: 1, bones: "ghost" };
  const seg = () => data.segments[state.key];

  const head = el("header", { class: "card-head" });
  const tabs = keys.length > 1 ? el("div", { class: "tabs" }) : null;
  const text = el("div", { class: "card-text" });
  const viewerBox = el("div", { class: "viewer", "aria-label": "3D view of the segment construction" });
  const stepInfo = el("div", { class: "step-info", "aria-live": "polite" });
  const prev = el("button", { type: "button", class: "btn", onclick: () => go(state.step - 1) }, "◀ Prev");
  const next = el("button", { type: "button", class: "btn primary", onclick: () => go(state.step + 1) }, "Next ▶");
  const controls = el(
    "div",
    { class: "viz-controls" },
    el("div", { class: "stepper" }, prev, stepInfo, next),
    el(
      "div",
      { class: "viz-options" },
      sided
        ? segmented("Side", [{ value: "R", label: "Right" }, { value: "L", label: "Left" }], "R", (v) => {
            state.side = v;
            const n = stepsFor(seg(), v).length;
            state.step = Math.min(state.step, n - 1);
            setView();
            render(true);
          })
        : null,
      segmented("Bones", BONE_MODES, "ghost", (v) => {
        state.bones = v;
        view.redraw();
      }),
      toggle("Labels", true, (v) => {
        state.labels = v;
        view.redraw();
      }),
      el("button", { type: "button", class: "btn ghost", onclick: () => view.refit() }, "Reset view"),
    ),
  );

  if (tabs) {
    tabs.append(
      segmented(
        "Option",
        keys.map((k) => ({ value: k, label: data.segments[k].option_label })),
        keys[0],
        (v) => {
          state.key = v;
          state.step = 0;
          setView();
          render(true);
        },
      ),
    );
  }
  card.append(head, tabs ?? "", el("div", { class: "card-grid" }, text, el("div", { class: "card-viz" }, viewerBox, controls)));

  const viewOpts = { view: seg().view };
  const view = lazyViewer(viewerBox, (v) => draw(v), viewOpts);

  function setView() {
    const [x, y, z] = seg().view;
    viewOpts.view = state.side === "L" ? [x, y, -z] : [x, y, z];
    if (view.viewer) view.viewer.view = viewOpts.view;
  }

  function go(i) {
    const n = stepsFor(seg(), state.side).length;
    state.step = Math.max(0, Math.min(n - 1, i));
    render(false);
    animate();
  }

  function animate() {
    const start = performance.now();
    const tick = (now) => {
      state.t = Math.min(1, (now - start) / 350);
      view.redraw();
      if (state.t < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }

  function render(refit) {
    const s = seg();
    head.replaceChildren(
      el("h3", {}, s.name, s.option_label ? el("span", { class: "muted" }, ` · ${s.option_label}`) : null),
      el("div", { class: "meta" }, refChip(data, s.reference, s.section)),
    );
    const steps = stepsFor(s, state.side);
    const list = el(
      "ol",
      { class: "steps" },
      steps.map((st, i) =>
        el(
          "li",
          {
            class: `${i === state.step ? "current" : ""} ${i > state.step ? "future" : ""}`,
            onclick: () => go(i),
            tabindex: "0",
            onkeydown: (e) => (e.key === "Enter" || e.key === " ") && go(i),
          },
          el("div", { class: "formula", html: `${st.label} = ${st.html}` }),
          el("p", {}, st.text),
        ),
      ),
    );
    text.replaceChildren(
      ...[
      el(
        "table",
        { class: "deftable" },
        el(
          "tbody",
          {},
          ["o", "X", "Y", "Z"].map((a) =>
            el(
              "tr",
              {},
              el("th", { class: a === "o" ? "" : `ax-${a.toLowerCase()}` }, AXIS_NAMES[a]),
              el("td", {}, s.axes_text[a]),
            ),
          ),
        ),
      ),
      el("h4", {}, "Construction"),
      list,
      needsCheck(s.needs_check),
      notesList(s.notes),
      ].filter(Boolean),
    );
    stepInfo.textContent = `Step ${state.step + 1} / ${steps.length}`;
    prev.disabled = state.step === 0;
    next.disabled = state.step === steps.length - 1;
    if (refit) view.refit();
    else view.redraw();
  }

  function draw(v) {
    v.showLabels = state.labels;
    const s = seg();
    const side = state.side;
    const geo = s.geometry[side];
    const steps = stepsFor(s, side);
    const cur = steps[state.step];
    const isFinal = cur.type !== "step";
    const uses = new Set(cur.type === "step" ? cur.uses : []);
    const P = v.palette;

    const pos = (name) => geo.steps[name]?.value ?? data.landmarks[name]?.[side] ?? geo.points[name];
    const lmPts = s.landmarks.map((k) => data.landmarks[k][side]);
    const meshes = s.meshes.map((g) => data.meshes.groups[g]).filter(Boolean);
    v.fit([...lmPts, geo.origin, ...meshCorners(meshes, side)]);

    // bones (meshes, or sticks when the meshes are hidden) and planes
    const opacity = boneOpacity(state.bones);
    for (const m of meshes) {
      const g = opacity > 0 && boneGeometry(m, () => view.redraw());
      if (g) v.bone(g, { opacity, mirror: side === "L" });
    }
    if (opacity === 0 || !meshes.length)
      for (const [a, b] of s.links) if (pos(a) && pos(b)) v.cylinder(pos(a), pos(b), { color: P.bone, opacity: 0.9 });
    for (const [a, b, c] of s.planes) if (pos(a) && pos(b) && pos(c)) v.plane(pos(a), pos(b), pos(c), { color: P.plane });

    // landmarks
    for (const k of new Set([...s.landmarks, ...[...uses].filter((u) => data.landmarks[u])])) {
      const hot = uses.has(k);
      v.point(data.landmarks[k][side], {
        color: hot ? P.highlight : P.landmark,
        radius: hot ? 4.6 : 3.6,
        opacity: isFinal || hot || !uses.size ? 1 : 0.45,
        label: landmarkLabel(data, k, side),
        labelClass: hot ? "hot" : "",
      });
    }

    // construction steps up to the current one
    const upto = isFinal ? s.steps.length : state.step + 1;
    const L = Math.max(30, v.size * 0.32);
    for (let i = 0; i < upto; i++) {
      const st = s.steps[i];
      const g = geo.steps[st.name];
      const now = i === state.step;
      const opacity = isFinal ? 0.3 : now || uses.has(st.name) ? 1 : 0.35;
      if (st.kind === "point" || st.kind === "origin") {
        v.point(g.value, {
          color: st.kind === "origin" ? P.muted : P.derived,
          radius: 3,
          opacity,
          label: now || uses.has(st.name) ? st.label : undefined,
          labelClass: "derived keep",
        });
        continue;
      }
      if (isFinal && st.kind === "axis") continue;
      const val = g.value;
      const len = Math.hypot(...val);
      const dirLen = st.kind === "axis" ? L : L * 1.3;
      const shown = st.draw_as === "segment" ? val : val.map((x) => (x / len) * dirLen);
      const t = now ? state.t : 1;
      v.arrow(g.anchor, shown.map((x) => x * t), {
        color: st.kind === "axis" ? P[st.name] : P.vector,
        opacity,
        radius: st.kind === "axis" ? 1.8 : 1.3,
        label: now || opacity === 1 ? st.label : undefined,
        labelClass: st.kind === "axis" ? `ax-${st.name.toLowerCase()} keep` : "derived keep",
      });
    }

    if (cur.type === "left") {
      v.frame(geo.origin, geo.literal_axes, { length: L, dashed: true, opacity: 0.55, suffix: "<sub>mirrored</sub>" });
      v.frame(geo.origin, geo.axes, { length: L * 1.1 });
    } else if (cur.type === "frame") {
      v.frame(geo.origin, geo.axes, { length: L * 1.15, radius: 2.1 });
    }
  }

  render(true);
}
