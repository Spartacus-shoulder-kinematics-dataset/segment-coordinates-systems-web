"""Build the bone meshes and the landmark set from BodyParts3D.

BodyParts3D, © The Database Center for Life Science (DBCLS), https://lifesciencedb.jp/bp3d/
The DBCLS licence page specifies CC BY 4.0; the OBJ headers cite CC BY-SA 2.1 JP. The derived meshes written by
this script are attributed and shared under the same terms (see static/meshes/LICENSE.txt).

All bones come from one subject in the same standing posture, so the landmarks detected on them form a
consistent skeleton. Run once (downloads ~62 MB into .cache/bodyparts3d):

    conda run -n spartacus python tools/prepare_meshes.py

Outputs
    isb/data/landmarks.json     landmark positions (mm, ISB global frame, right side)
    isb/data/meshes.json        manifest of the mesh groups
    static/meshes/<group>.bin   float32 xyz positions followed by uint32 triangle indices
"""

import json
import sys
import urllib.request
import zipfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache" / "bodyparts3d"
sys.path.insert(0, str(ROOT / ".cache" / "pydeps"))  # fast-simplification (pip install --target .cache/pydeps)

BASE_URL = "https://dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/"
ZIP = "partof_BP3D_4.0_obj_99.zip"
PARTS = "partof_element_parts.txt"
ATTRIBUTION = "BodyParts3D, © The Database Center for Life Science, licensed under CC Attribution 4.0 International"

ORDINALS = ["first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth", "eleventh", "twelfth"]
THORACIC = [f"{o} thoracic vertebra" for o in ORDINALS]

# mesh group -> (BodyParts3D part names, maximum number of vertices after decimation)
GROUPS = {
    "pelvis": (["right hip bone", "left hip bone", "sacrum"], 6000),
    "femur": (["right femur"], 2500),
    "tibia": (["right tibia"], 2000),
    "fibula": (["right fibula"], 1000),
    "patella": (["right patella"], 600),
    "talus": (["right talus"], 1200),
    "foot": (
        ["right calcaneus", "navicular bone of right foot", "right cuboid bone", "right medial cuneiform bone",
         "right intermediate cuneiform bone", "right lateral cuneiform bone"]
        + [f"right {o} metatarsal bone" for o in ORDINALS[:5]],
        5000,
    ),
    "C4": (["fourth cervical vertebra"], 1500),
    "C5": (["fifth cervical vertebra"], 1500),
    "T7": (["seventh thoracic vertebra"], 1500),
    "T8": (["eighth thoracic vertebra"], 1500),
    "L4": (["fourth lumbar vertebra"], 1800),
    "L5": (["fifth lumbar vertebra"], 1800),
    "thorax": (
        ["manubrium", "body of sternum", "xiphoid process", "seventh cervical vertebra"]
        + THORACIC
        + [f"{s} {o} rib" for s in ("right", "left") for o in ORDINALS]
        + [f"{s} {o} costal cartilage" for s in ("right", "left") for o in ORDINALS[:7]],
        16000,
    ),
    "clavicle": (["right clavicle"], 1500),
    "scapula": (["right scapula"], 3500),
    "humerus": (["right humerus"], 2500),
    "ulna": (["right ulna"], 1500),
    "radius": (["right radius"], 1500),
    "carpus": (
        ["right scaphoid", "right lunate", "right triquetral", "right pisiform", "right trapezium", "right trapezoid",
         "right capitate", "right hamate", "right first metacarpal bone", "right fourth metacarpal bone",
         "right fifth metacarpal bone"],
        3500,
    ),
    "MC3": (["right third metacarpal bone"], 800),
    "MC2": (["right second metacarpal bone"], 800),
    "PP2": (["proximal phalanx of right index finger"], 500),
    "MP2": (["middle phalanx of right index finger"], 500),
    "DP2": (["distal phalanx of right index finger"], 400),
}


# --- data access --------------------------------------------------------------------------------------
def ensure_data() -> dict[str, list[str]]:
    CACHE.mkdir(parents=True, exist_ok=True)
    for name in (PARTS, ZIP):
        if not (CACHE / name).exists():
            print(f"downloading {name} ...")
            urllib.request.urlretrieve(BASE_URL + name, CACHE / name)
    ids: dict[str, list[str]] = {}
    for line in (CACHE / PARTS).read_text().splitlines()[1:]:
        _, name, fj = line.split("\t")
        ids.setdefault(name.strip().lower(), []).append(fj.strip())
    return ids


def load_obj(fj: str) -> tuple[np.ndarray, np.ndarray]:
    with zipfile.ZipFile(CACHE / ZIP) as z:
        text = z.read(f"partof_BP3D_4.0_obj_99/{fj}.obj").decode()
    v, f = [], []
    for line in text.splitlines():
        if line.startswith("v "):
            v.append(line.split()[1:4])
        elif line.startswith("f "):
            f.append([int(t.split("/")[0]) - 1 for t in line.split()[1:4]])
    v = np.array(v, dtype=float)
    # BodyParts3D: +X left, +Y posterior, +Z up (mm)  ->  ISB: X anterior, Y up, Z right
    return np.column_stack([-v[:, 1], v[:, 2], -v[:, 0]]), np.array(f, dtype=np.int64)


def load_part(ids, name) -> tuple[np.ndarray, np.ndarray]:
    if name not in ids:
        raise KeyError(f"BodyParts3D has no part named {name!r}")
    vs, fs, n = [], [], 0
    for fj in ids[name]:
        v, f = load_obj(fj)
        vs.append(v)
        fs.append(f + n)
        n += len(v)
    return np.vstack(vs), np.vstack(fs)


def decimate(v, f, max_vertices):
    if len(v) <= max_vertices:
        return v, f
    import fast_simplification

    reduction = 1 - max_vertices / len(v)
    v2, f2 = fast_simplification.simplify(v.astype(np.float32), f.astype(np.int32), target_reduction=reduction)
    return v2.astype(float), f2.astype(np.int64)


# --- geometric helpers ----------------------------------------------------------------------------------
def sphere_fit(p: np.ndarray) -> tuple[np.ndarray, float]:
    A = np.column_stack([2 * p, np.ones(len(p))])
    b = (p**2).sum(1)
    x, *_ = np.linalg.lstsq(A, b, rcond=None)
    c = x[:3]
    return c, float(np.sqrt(x[3] + c @ c))


def robust_sphere(v: np.ndarray, seed: np.ndarray, radius: float, iterations: int = 6):
    """Sphere through the vertices near `seed`, iteratively discarding non-spherical parts (neck, fovea)."""
    pts = v[np.linalg.norm(v - seed, axis=1) < radius * 1.3]
    c, r = sphere_fit(pts)
    for _ in range(iterations):
        d = np.abs(np.linalg.norm(v - c, axis=1) - r)
        pts = v[(d < 1.5) & (np.linalg.norm(v - seed, axis=1) < radius * 2)]
        c, r = sphere_fit(pts)
    return c, r


def extreme(v: np.ndarray, direction, mask=None) -> np.ndarray:
    """Vertex furthest along `direction` (optionally among the vertices selected by `mask`)."""
    w = v if mask is None else v[mask]
    return w[np.argmax(w @ np.asarray(direction, dtype=float))]


def band(v, axis: int, lo: float, hi: float):
    """Mask of vertices whose coordinate along `axis` lies in [min + lo*extent, min + hi*extent]."""
    x = v[:, axis]
    a, b = x.min(), x.max()
    return (x >= a + lo * (b - a)) & (x <= a + hi * (b - a))


def long_bone_ends(v: np.ndarray, tip: float = 4.0):
    """Base (proximal) and head (distal) centres of a small long bone (hand bones), along its main axis."""
    c = v.mean(0)
    _, _, vt = np.linalg.svd(v - c)
    axis = vt[0] if vt[0][1] > 0 else -vt[0]  # pointing proximally (up)
    t = (v - c) @ axis
    base = v[t > t.max() - tip].mean(0)
    head = v[t < t.min() + tip].mean(0)
    return base, head, axis


# --- landmarks ------------------------------------------------------------------------------------------
X, Y, Z = np.eye(3)


def vertex_normals(v: np.ndarray, f: np.ndarray) -> np.ndarray:
    fn = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
    n = np.zeros_like(v)
    for i in range(3):
        np.add.at(n, f[:, i], fn)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def vertebra_landmarks(v: np.ndarray, f: np.ndarray, name: str, body_fraction: float) -> dict:
    """Body centroid, endplate centres and pedicle bases of one vertebra."""
    xmax, xmin = v[:, 0].max(), v[:, 0].min()
    body_post = xmax - body_fraction * (xmax - xmin)
    zc = (v[:, 2].max() + v[:, 2].min()) / 2
    in_body = (v[:, 0] > body_post) & (np.abs(v[:, 2] - zc) < 0.25 * np.ptp(v[:, 2]))
    body = v[in_body]
    c = body.mean(0)
    # endplates: the parts of the body surface facing up (superior) and down (inferior)
    n = vertex_normals(v, f)
    central = np.abs(v[:, 2] - zc) < 0.12 * np.ptp(v[:, 2])  # away from the (cervical) uncinate processes
    ue = v[in_body & central & (n[:, 1] > 0.8)].mean(0)
    le = v[in_body & central & (n[:, 1] < -0.8)].mean(0)
    up = (ue - le) / np.linalg.norm(ue - le)
    c = (ue + le) / 2
    h = (ue - le) @ up
    slab = v[(v[:, 0] < body_post + 1.0) & (v[:, 0] > body_post - 6.0) & (np.abs((v - c) @ up) < 0.4 * h)]
    rp = slab[slab[:, 2] > c[2] + 2].mean(0)
    lp = slab[slab[:, 2] < c[2] - 2].mean(0)
    # vertex sampling is not symmetric: share the height and depth of the pair, keep each side's width
    rp[:2] = lp[:2] = (rp[:2] + lp[:2]) / 2
    return {f"{name}_c": c, f"{name}_ue": ue, f"{name}_le": le, f"{name}_rp": rp, f"{name}_lp": lp}


def detect_landmarks(parts: dict[str, np.ndarray], faces: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    L = {}
    # pelvis: spines are the most anterior / posterior points of the upper ilium
    for side, bone in (("R", "right hip bone"), ("L", "left hip bone")):
        v = parts[bone]
        upper = band(v, 1, 0.6, 1.0)
        L[f"{side}ASIS"] = extreme(v, X, upper)
        L[f"{side}PSIS"] = extreme(v, -X, upper & band(v, 1, 0.6, 0.85))

    # femur: head centre by sphere fitting, epicondyles as the most medial/lateral distal points
    v = parts["right femur"]
    L["HJC"], _ = robust_sphere(v, extreme(v, Y), 24)
    distal = band(v, 1, 0.0, 0.12)
    L["LFE"], L["MFE"] = extreme(v, Z, distal), extreme(v, -Z, distal)

    v = parts["right tibia"]
    prox = band(v, 1, 0.9, 1.0)
    L["MC"], L["LC"] = extreme(v, -Z, prox), extreme(v, Z, prox)
    L["TT"] = extreme(v, X, band(v, 1, 0.78, 0.93))
    distal = band(v, 1, 0.0, 0.12)
    medial = distal & (v[:, 2] < v[distal, 2].mean())
    L["MM"] = extreme(v, -Y, medial)
    v = parts["right fibula"]
    L["LM"], L["HF"] = extreme(v, -Y), extreme(v, Y)
    L["TAH"] = extreme(parts["right talus"], X)
    L["CAL"] = extreme(parts["right calcaneus"], -X)
    L["MH1"] = extreme(parts["right first metatarsal bone"], X)
    L["MH5"] = extreme(parts["right fifth metatarsal bone"], X)

    for name, part, frac in (
        ("C4", "fourth cervical vertebra", 0.30), ("C5", "fifth cervical vertebra", 0.30),
        ("T7", "seventh thoracic vertebra", 0.36), ("T8", "eighth thoracic vertebra", 0.36),
        ("L4", "fourth lumbar vertebra", 0.40), ("L5", "fifth lumbar vertebra", 0.40),
    ):
        L.update(vertebra_landmarks(parts[part], faces[part], name, frac))

    # thorax
    v = parts["manubrium"]
    L["IJ"] = extreme(v, Y, np.abs(v[:, 2] - v[:, 2].mean()) < 2.5)
    L["PX"] = extreme(parts["xiphoid process"], -Y)
    L["C7"] = extreme(parts["seventh cervical vertebra"], -X)
    L["T8"] = extreme(parts["eighth thoracic vertebra"], -X)

    v = parts["right clavicle"]
    L["SC"] = extreme(v, X, v[:, 2] < v[:, 2].min() + 8)
    L["AC"] = extreme(v, -X, v[:, 2] > v[:, 2].max() - 8)

    v = parts["right scapula"]
    L["AI"] = extreme(v, -Y)
    acromion = v[:, 1] > v[:, 1].max() - 25
    L["AA"] = extreme(v, Z - X, acromion)
    # trigonum spinae: medial end of the scapular spine, the ridge standing out behind the blade
    blade = v[(v[:, 1] < L["AA"][1] - 40) & (v[:, 2] < L["AA"][2] - 40)]
    c = blade.mean(0)
    _, _, vt = np.linalg.svd(blade - c)
    n = vt[2] if vt[2][0] < 0 else -vt[2]  # blade normal, pointing backwards
    behind = (v - c) @ n
    spine = (behind > np.percentile(behind, 90)) & (v[:, 1] > L["AI"][1] + 0.5 * (L["AA"][1] - L["AI"][1]))
    spine_end = extreme(v, -Z, spine)
    # ... carried along the same height to the medial border
    L["TS"] = extreme(v, -Z, np.abs(v[:, 1] - spine_end[1]) < 4)
    # glenoid centre: mean of the most lateral vertices below the acromion
    below = (v[:, 1] < L["AA"][1] - 20) & (v[:, 1] > L["AA"][1] - 70)
    zmax = v[below, 2].max()
    L["GC"] = v[below & (v[:, 2] > zmax - 6)].mean(0)

    v = parts["right humerus"]
    L["GH"], _ = robust_sphere(v, extreme(v, Y - Z - 0.5 * X, band(v, 1, 0.85, 1.0)), 22)
    distal = band(v, 1, 0.0, 0.12)
    L["EL"], L["EM"] = extreme(v, Z, distal), extreme(v, -Z, distal)
    L["US"] = extreme(parts["right ulna"], -Y)
    L["RS"] = extreme(parts["right radius"], -Y)

    for key, part in (
        ("MC3", "right third metacarpal bone"), ("MC2", "right second metacarpal bone"),
        ("PP2", "proximal phalanx of right index finger"), ("MP2", "middle phalanx of right index finger"),
    ):
        v = parts[part]
        base, head, axis = long_bone_ends(v)
        L[f"{key}_b"], L[f"{key}_h"] = base, head
        t = (v - v.mean(0)) @ axis
        distal = v[t < t.min() + 8]
        L[f"{key}_hr"], L[f"{key}_hu"] = extreme(distal, Z), extreme(distal, -Z)
    return L


# --- main -------------------------------------------------------------------------------------------------
def main():
    ids = ensure_data()
    needed = {n for names, _ in GROUPS.values() for n in names}
    needed |= {"right first metatarsal bone", "right fifth metatarsal bone"}
    parts, faces = {}, {}
    for name in sorted(needed):
        parts[name], faces[name] = load_part(ids, name)

    landmarks = detect_landmarks(parts, faces)
    (ROOT / "isb" / "data").mkdir(exist_ok=True)
    (ROOT / "isb" / "data" / "landmarks.json").write_text(
        json.dumps({k: [round(float(x), 2) for x in p] for k, p in sorted(landmarks.items())}, indent=1)
    )

    out = ROOT / "static" / "meshes"
    out.mkdir(parents=True, exist_ok=True)
    manifest = {"attribution": ATTRIBUTION, "source": "https://lifesciencedb.jp/bp3d/", "groups": {}}
    for group, (names, max_v) in GROUPS.items():
        vs, fs, n = [], [], 0
        for name in names:
            vs.append(parts[name])
            fs.append(faces[name] + n)
            n += len(parts[name])
        v, f = decimate(np.vstack(vs), np.vstack(fs), max_v)
        blob = v.astype("<f4").tobytes() + f.astype("<u4").tobytes()
        (out / f"{group}.bin").write_bytes(blob)
        manifest["groups"][group] = {
            "file": f"static/meshes/{group}.bin",
            "vertices": int(len(v)),
            "triangles": int(len(f)),
            "min": [round(float(x), 1) for x in v.min(0)],
            "max": [round(float(x), 1) for x in v.max(0)],
            "parts": names,
        }
        print(f"{group:9s} {len(v):6d} v {len(f):6d} f  {len(blob) / 1024:6.0f} kB")
    (ROOT / "isb" / "data" / "meshes.json").write_text(json.dumps(manifest, indent=1))
    (out / "LICENSE.txt").write_text(
        f"Bone meshes derived (axis change to the ISB frame, decimation) from {ATTRIBUTION}.\n"
        "Source: https://lifesciencedb.jp/bp3d/ — licence: https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html\n"
        "The original OBJ files cite CC BY-SA 2.1 JP; these derived meshes are shared under the same terms.\n"
    )


if __name__ == "__main__":
    main()
