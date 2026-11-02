// Small DOM helpers shared by the page scripts.

export function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === undefined || v === null || v === false) continue;
    if (k === "class") node.className = v;
    else if (k === "html") node.innerHTML = v;
    else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v === true ? "" : v);
  }
  for (const c of children.flat()) {
    if (c === null || c === undefined || c === false) continue;
    node.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return node;
}

/** Segmented control. options: [{value, label}] */
export function segmented(name, options, value, onChange) {
  const wrap = el("div", { class: "segmented", role: "radiogroup", "aria-label": name });
  const buttons = options.map((o) =>
    el(
      "button",
      {
        type: "button",
        role: "radio",
        "aria-checked": String(o.value === value),
        onclick: () => {
          buttons.forEach((b) => b.setAttribute("aria-checked", String(b === btn(o))));
          onChange(o.value);
        },
      },
      o.label,
    ),
  );
  const btn = (o) => buttons[options.indexOf(o)];
  wrap.append(...buttons);
  return wrap;
}

export function toggle(label, checked, onChange) {
  const input = el("input", { type: "checkbox", onchange: (e) => onChange(e.target.checked) });
  input.checked = checked;
  return el("label", { class: "toggle" }, input, el("span", {}, label));
}

export const fmt = (v, digits = 1) => `${(Math.abs(v) < 0.05 ? 0 : v).toFixed(digits)}°`;

/** "12.3° flexion" from a signed angle and its AngleDef. */
export function clinical(v, def) {
  if (Math.abs(v) < 0.05) return "0°";
  return `${Math.abs(v).toFixed(1)}° ${v > 0 ? def.positive : def.negative}`;
}

export function refChip(data, key, section) {
  const r = data.references[key];
  return el(
    "a",
    { class: "chip ref", href: `https://doi.org/${r.doi}`, target: "_blank", rel: "noopener", title: r.full },
    r.short,
    section ? el("span", { class: "chip-sub" }, ` · ${section}`) : null,
  );
}

export function needsCheck(items) {
  if (!items || !items.length) return null;
  return el(
    "aside",
    { class: "check" },
    el("strong", {}, "Verify against the paper"),
    el("ul", {}, items.map((t) => el("li", {}, t))),
  );
}

export function notesList(items) {
  if (!items || !items.length) return null;
  return el("ul", { class: "notes" }, items.map((t) => el("li", {}, t)));
}

export function landmarkLabel(data, key, side) {
  const lm = data.landmarks[key];
  if (!lm) return key;
  const k = side === "L" ? lm.label_L : key;
  const [base, suffix] = k.split("_");
  if (k === "LFE") return "FE<sub>lat</sub>";
  if (k === "MFE") return "FE<sub>med</sub>";
  if (k === "US90") return "US<sub>90°</sub>";
  return suffix ? `${base}<sub>${suffix}</sub>` : base;
}
