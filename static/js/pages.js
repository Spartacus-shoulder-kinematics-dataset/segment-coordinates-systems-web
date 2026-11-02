// Page entry point: theme toggle, then whichever widgets the page contains.
import { mountJointCard } from "./jcs_playground.js";
import { mountSegmentCard } from "./lcs_builder.js";
import { mountSequenceTool } from "./sequence_tool.js";

function initTheme() {
  const button = document.querySelector("[data-theme-toggle]");
  let saved = null;
  try {
    saved = localStorage.getItem("isb-theme");
  } catch {}
  if (saved) document.documentElement.dataset.theme = saved;
  button?.addEventListener("click", () => {
    const dark =
      document.documentElement.dataset.theme === "dark" ||
      (!document.documentElement.dataset.theme && matchMedia("(prefers-color-scheme: dark)").matches);
    const next = dark ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try {
      localStorage.setItem("isb-theme", next);
    } catch {}
    window.dispatchEvent(new Event("themechange"));
  });
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => window.dispatchEvent(new Event("themechange")));
}

function initRegion() {
  const node = document.getElementById("isb-data");
  if (!node) return;
  const data = JSON.parse(node.textContent);
  const sided = data.region.sided;
  document.querySelectorAll(".seg-card").forEach((card) => mountSegmentCard(card, data, sided));
  document.querySelectorAll(".joint-card").forEach((card) => mountJointCard(card, data, sided));
}

function initTools() {
  document.querySelectorAll("[data-sequence-tool]").forEach((root) => {
    const cfg = JSON.parse(root.dataset.sequenceTool || "{}");
    mountSequenceTool(root, cfg);
  });
}

function initFilter() {
  const input = document.querySelector("[data-filter]");
  if (!input) return;
  const rows = [...document.querySelectorAll("[data-filter-row]")];
  input.addEventListener("input", () => {
    const q = input.value.trim().toLowerCase();
    rows.forEach((r) => (r.hidden = q && !r.textContent.toLowerCase().includes(q)));
  });
}

initTheme();
initRegion();
initTools();
initFilter();
