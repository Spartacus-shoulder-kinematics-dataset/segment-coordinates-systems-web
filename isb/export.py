"""Serialize the registry and its evaluated geometry for the site (JSON-ready dicts)."""

import json
import re
from dataclasses import asdict
from pathlib import Path

import numpy as np

from .definitions import JOINTS, REFERENCES, REGIONS, SEGMENTS
from .geometry import Evaluator, evaluate_expr, expr_leaves, jcs_angles
from .landmarks import LANDMARKS, POSITIONS
from .model import SegmentCS, Step
from .rotations import left_side_signs
from .sides import M, left_frame, mirrored_positions

SIDES = ("R", "L")
AXES = ("X", "Y", "Z")


def _r(v, nd=3):
    return [round(float(x), nd) for x in np.asarray(v).ravel()]


# --- formula rendering -------------------------------------------------------------------------
def _label(name: str, step_names: set) -> str:
    if name in LANDMARKS:
        base, _, suffix = name.partition("_")
        if name == "LFE":
            return '<span class="f-lm">FE<sub>lat</sub></span>'
        if name == "MFE":
            return '<span class="f-lm">FE<sub>med</sub></span>'
        if name == "US90":
            return '<span class="f-lm">US<sub>90°</sub></span>'
        return f'<span class="f-lm">{base}{f"<sub>{suffix}</sub>" if suffix else ""}</span>'
    if "." in name:
        seg, axis = name.split(".")
        return f'<var class="ax-{axis.lower()}">{axis}</var><sub>{seg}</sub>'
    if name in AXES:
        return f'<var class="ax-{name.lower()}">{name}</var>'
    if name == "o":
        return "<var>O</var>"
    if name in step_names and name.isupper():
        return f'<span class="f-pt">{name}</span>'
    if re.fullmatch(r"[mY][A-Za-z0-9]+", name):
        return f"<var>{name[0]}</var><sub>{name[1:]}</sub>"
    return f"<var>{name}</var>"


def formula(expr, step_names: set) -> tuple[str, int]:
    """HTML of an expression and its precedence (3 atom, 2 product, 1 sum)."""
    if isinstance(expr, str):
        return _label(expr, step_names), 3
    op, *args = expr
    parts = [formula(a, step_names) for a in args]

    def paren(p, level):
        return f"({p[0]})" if p[1] <= level else p[0]

    if op == "mid":
        return f"½({parts[0][0]} + {parts[1][0]})", 3
    if op == "sub":
        return f"{parts[0][0]} − {paren(parts[1], 1)}", 1
    if op == "cross":
        return f"{paren(parts[0], 2)} × {paren(parts[1], 2)}", 2
    if op == "unit":
        num = parts[0][0]
        return f'<span class="frac"><span>{num}</span><span>‖{num}‖</span></span>', 3
    if op == "reject":
        v, n = paren(parts[0], 1), parts[1][0]
        return f"{v} − ({v} · {n}) {n}", 1
    if op == "neg":
        return f"−{paren(parts[0], 2)}", 2
    raise ValueError(op)


# --- segments ------------------------------------------------------------------------------------
def _inferred_anchor(step: Step):
    """Where a vector is drawn from: the start point of a difference, if any."""
    e = step.expr
    while isinstance(e, tuple) and e[0] in ("unit", "reject", "neg"):
        e = e[1]
    if isinstance(e, tuple) and e[0] == "sub":
        return e[2] if isinstance(e[2], str) else None
    return None


def _draw_as(step: Step) -> str:
    e = step.expr
    if isinstance(e, tuple) and e[0] in ("sub", "reject"):
        return "segment"  # drawn with its true length
    return "direction"


def _step_kind(step: Step) -> str:
    if step.name == "o":
        return "origin"
    if step.name in AXES:
        return "axis"
    return step.kind


def _segment_side_geometry(seg: SegmentCS, ev: Evaluator, final_R: np.ndarray, final_o: np.ndarray, positions):
    frame = ev.frame(seg.key)
    values = frame.values

    def point_of(name):
        if name in values:
            return values[name]
        if name in positions:
            return positions[name]
        return ev.resolve(name)

    steps = {}
    for step in seg.steps:
        kind = _step_kind(step)
        entry = {"value": _r(values[step.name])}
        if kind not in ("point", "origin"):
            anchor = step.anchor or _inferred_anchor(step) or ("o" if "o" in values else None)
            anchor_pos = point_of(anchor) if anchor else final_o
            entry["anchor"] = _r(anchor_pos)
        steps[step.name] = entry

    literal = frame.R
    flipped = [a for i, a in enumerate(AXES) if float(np.dot(literal[:, i], final_R[:, i])) < 0]
    points = {n: _r(values[s.name]) for s in seg.steps for n in [s.name] if _step_kind(s) == "point"}
    return {
        "steps": steps,
        "origin": _r(final_o),
        "axes": {a: _r(final_R[:, i], 5) for i, a in enumerate(AXES)},
        "literal_axes": {a: _r(literal[:, i], 5) for i, a in enumerate(AXES)},
        "flipped": flipped,
        "points": points,
    }


def export_segment(seg: SegmentCS, evaluators: dict, finals: dict, positions: dict) -> dict:
    step_names = {s.name for s in seg.steps}
    steps = []
    for s in seg.steps:
        leaves = expr_leaves(s.expr) if not isinstance(s.expr, str) else [s.expr]
        html, _ = formula(s.expr, step_names)
        steps.append(
            {
                "name": s.name,
                "label": _label(s.name, step_names),
                "kind": _step_kind(s),
                "draw_as": _draw_as(s),
                "html": html,
                "text": s.text,
                "uses": sorted({leaf for leaf in leaves if "." not in leaf}),
                "refs": sorted({leaf for leaf in leaves if "." in leaf}),
            }
        )
    d = {
        "key": seg.key,
        "name": seg.name,
        "region": seg.region,
        "reference": seg.reference,
        "section": seg.section,
        "axes_text": seg.axes_text,
        "landmarks": list(seg.landmarks),
        "links": [list(p) for p in seg.links],
        "planes": [list(p) for p in seg.planes],
        "option_group": seg.option_group,
        "option_label": seg.option_label,
        "view": list(seg.view),
        "meshes": list(seg.meshes),
        "notes": list(seg.notes),
        "needs_check": list(seg.needs_check),
        "steps": steps,
        "geometry": {},
    }
    for side in SIDES:
        o, R = finals[side](seg.key)
        d["geometry"][side] = _segment_side_geometry(seg, evaluators[side], R, o, positions[side])
    return d


# --- joints --------------------------------------------------------------------------------------
def export_joint(joint, finals: dict, positions: dict, evaluators: dict) -> dict:
    parent, child = SEGMENTS[joint.parent], SEGMENTS[joint.child]
    d = asdict(joint)
    d["pivot"] = None if joint.pivot is None else formula(joint.pivot, set())[0]
    d["angles"] = [asdict(a) for a in joint.angles]
    d["geometry"] = {}
    for side in SIDES:
        o_p, R_p = finals[side](joint.parent)
        o_c, R_c = finals[side](joint.child)
        raw = np.rad2deg(jcs_angles(joint, R_p, R_c, side))
        signs = left_side_signs(joint.sequence) if side == "L" else np.ones(3)
        pos = positions[side]
        child_local = {k: _r(R_c.T @ (pos[k] - o_c)) for k in child.landmarks}
        pivot = o_c if joint.pivot is None else evaluate_expr(joint.pivot, {}, evaluators[side].resolve)
        d["geometry"][side] = {
            "parent_origin": _r(o_p),
            "parent_R": [_r(R_p[:, i], 6) for i in range(3)],  # columns X, Y, Z
            "child_origin": _r(o_c),
            "pivot": _r(pivot),
            "child_R": [_r(R_c[:, i], 6) for i in range(3)],
            "child_local": child_local,
            "parent_landmarks": {k: _r(pos[k]) for k in parent.landmarks},
            "neutral_raw": _r(raw, 2),
            "neutral_clinical": _r(raw * signs, 2),
            "signs": _r(signs, 0),
        }
    return d


# --- everything ------------------------------------------------------------------------------------
def build_dataset() -> dict:
    positions = {"R": POSITIONS, "L": mirrored_positions(POSITIONS)}
    right = Evaluator(SEGMENTS, positions["R"])

    def final_right(key):
        f = right.frame(key)
        return f.origin, f.R

    def final_left(key):
        o, R = final_right(key)
        return M @ o, left_frame(R)

    finals = {"R": final_right, "L": final_left}
    evaluators = {"R": right, "L": Evaluator(SEGMENTS, positions["L"], reference_frame=final_left)}

    landmarks = {
        k: {
            "key": k,
            "name": lm.name,
            "description": lm.description,
            "bone": lm.bone,
            "label_L": lm.mirror_label or k,
            "R": _r(positions["R"][k]),
            "L": _r(positions["L"][k]),
        }
        for k, lm in LANDMARKS.items()
    }
    manifest = Path(__file__).parent / "data" / "meshes.json"
    meshes = json.loads(manifest.read_text()) if manifest.exists() else {"groups": {}}
    return {
        "frame": {"X": "anterior", "Y": "superior", "Z": "right"},
        "meshes": meshes,
        "references": {k: asdict(r) for k, r in REFERENCES.items()},
        "landmarks": landmarks,
        "regions": [asdict(r) for r in REGIONS.values()],
        "segments": {k: export_segment(s, evaluators, finals, positions) for k, s in SEGMENTS.items()},
        "joints": {k: export_joint(j, finals, positions, evaluators) for k, j in JOINTS.items()},
    }


def region_subset(data: dict, region_key: str) -> dict:
    """The data a region page needs: its segments and joints, plus the segments its joints refer to."""
    region = next(r for r in data["regions"] if r["key"] == region_key)
    seg_keys = list(region["segments"])
    for jk in region["joints"]:
        j = data["joints"][jk]
        for k in (j["parent"], j["child"]):
            if k not in seg_keys:
                seg_keys.append(k)
    # segments referenced by constructions ("thorax.Y", "tibia_fibula.X")
    for k in list(seg_keys):
        for step in data["segments"][k]["steps"]:
            for ref in step["refs"]:
                ref_seg = ref.split(".")[0]
                if ref_seg not in seg_keys:
                    seg_keys.append(ref_seg)
    lm_keys = {lm for k in seg_keys for lm in data["segments"][k]["landmarks"]}
    for k in seg_keys:
        for step in data["segments"][k]["steps"]:
            lm_keys.update(u for u in step["uses"] if u in data["landmarks"])
    groups = {g for k in seg_keys for g in data["segments"][k]["meshes"]}
    return {
        "frame": data["frame"],
        "meshes": {
            "attribution": data["meshes"].get("attribution"),
            "source": data["meshes"].get("source"),
            "groups": {g: v for g, v in data["meshes"]["groups"].items() if g in groups},
        },
        "region": region,
        "references": data["references"],
        "landmarks": {k: v for k, v in data["landmarks"].items() if k in lm_keys},
        "segments": {k: data["segments"][k] for k in seg_keys},
        "joints": {k: data["joints"][k] for k in region["joints"]},
    }
