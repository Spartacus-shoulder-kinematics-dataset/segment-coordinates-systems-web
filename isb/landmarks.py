"""Landmarks: names, descriptions and positions.

Coordinates are in millimetres, expressed in the ISB global frame: X anterior, Y superior, Z to the right.
Only the right side is stored; the left side is its mirror image (z -> -z), see sides.py.

Positions come from isb/data/landmarks.json, detected on the BodyParts3D bone meshes by
tools/prepare_meshes.py (one subject standing in the anatomical position). The hand-written values below are a
fallback used only when that file is missing.
"""

import json
from pathlib import Path

import numpy as np

from .model import Landmark

POSITIONS: dict[str, np.ndarray] = {}
LANDMARKS: dict[str, Landmark] = {}


def _add(key: str, pos, name: str, description: str, bone: str, mirror_label: str | None = None):
    POSITIONS[key] = np.asarray(pos, dtype=float)
    LANDMARKS[key] = Landmark(key, name, description, bone, mirror_label)


def _rotation(axis: np.ndarray, angle: float) -> np.ndarray:
    """Rodrigues rotation matrix about a unit axis."""
    axis = axis / np.linalg.norm(axis)
    k = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + np.sin(angle) * k + (1 - np.cos(angle)) * k @ k


# --- pelvis and femur (Wu et al. 2002) ----------------------------------------------------------
_add("RASIS", (65, 985, 125), "RASIS", "Right anterior superior iliac spine", "pelvis", "LASIS")
_add("LASIS", (65, 985, -125), "LASIS", "Left anterior superior iliac spine", "pelvis", "RASIS")
_add("RPSIS", (-95, 1000, 45), "RPSIS", "Right posterior superior iliac spine", "pelvis", "LPSIS")
_add("LPSIS", (-95, 1000, -45), "LPSIS", "Left posterior superior iliac spine", "pelvis", "RPSIS")
_add("HJC", (18, 910, 88), "HJC", "Hip joint centre (estimated, e.g. functional or regression method)", "pelvis")
_add("LFE", (8, 495, 128), "FE₁ (lateral)", "Lateral femoral epicondyle", "femur")
_add("MFE", (2, 495, 40), "FE₂ (medial)", "Medial femoral epicondyle", "femur")

# --- tibia / fibula and foot (Wu et al. 2002) ---------------------------------------------------
_add("LC", (0, 455, 130), "LC", "Most lateral point on the border of the lateral tibial condyle", "tibia")
_add("MC", (0, 455, 42), "MC", "Most medial point on the border of the medial tibial condyle", "tibia")
_add("TT", (38, 420, 84), "TT", "Most anterior prominence of the tibial tuberosity", "tibia")
_add("HF", (-18, 440, 128), "HF", "Most proximal point of the head of the fibula (display only)", "fibula")
_add("MM", (8, 85, 55), "MM", "Tip of the medial malleolus", "tibia")
_add("LM", (-14, 68, 118), "LM", "Tip of the lateral malleolus", "fibula")
_add("CAL", (-65, 35, 88), "CAL", "Posterior point of the calcaneal tuberosity (display only)", "calcaneus")
_add("MH1", (140, 22, 58), "MH1", "First metatarsal head (display only)", "foot")
_add("MH5", (115, 18, 128), "MH5", "Fifth metatarsal head (display only)", "foot")
_add("TAH", (55, 60, 72), "TAH", "Head of the talus (display only)", "talus")


# --- spine (Wu et al. 2002) ---------------------------------------------------------------------
def _vertebra(v: str, centre, tilt_deg: float, height: float, depth: float, half_width: float):
    """Vertebral body centroid, endplate centres and pedicle bases, tilted about Z by `tilt_deg`."""
    c = np.asarray(centre, dtype=float)
    r = _rotation(np.array([0.0, 0.0, 1.0]), np.deg2rad(tilt_deg))
    _add(f"{v}_c", c, f"{v} c", f"Centroid of the {v} vertebral body", v)
    _add(f"{v}_ue", c + r @ [0, height / 2, 0], f"{v} ue", f"Centre of the superior endplate of {v}", v)
    _add(f"{v}_le", c + r @ [0, -height / 2, 0], f"{v} le", f"Centre of the inferior endplate of {v}", v)
    _add(f"{v}_rp", c + r @ [-depth, 0, half_width], f"{v} rp", f"Base of the right pedicle of {v}", v)
    _add(f"{v}_lp", c + r @ [-depth, 0, -half_width], f"{v} lp", f"Base of the left pedicle of {v}", v)


_vertebra("C4", (-22, 1545, 0), 10, 12, 14, 12)
_vertebra("C5", (-25, 1530, 0), 8, 12, 14, 12)
_vertebra("T7", (-48, 1305, 0), -8, 20, 20, 14)
_vertebra("T8", (-52, 1283, 0), -6, 20, 20, 14)
_vertebra("L4", (-18, 1088, 0), 5, 27, 24, 18)
_vertebra("L5", (-14, 1050, 0), 12, 27, 24, 18)

# --- shoulder (Wu et al. 2005) ------------------------------------------------------------------
_add("IJ", (50, 1440, 0), "IJ", "Deepest point of the incisura jugularis (suprasternal notch)", "thorax")
_add("PX", (82, 1255, 0), "PX", "Processus xiphoideus, most caudal point on the sternum", "thorax")
_add("C7", (-92, 1482, 0), "C7", "Processus spinosus of the 7th cervical vertebra", "thorax")
_add("T8", (-112, 1272, 0), "T8", "Processus spinosus of the 8th thoracic vertebra", "thorax")
_add("SC", (40, 1438, 22), "SC", "Most ventral point on the sternoclavicular joint", "clavicle")
_add("AC", (-8, 1450, 162), "AC", "Most dorsal point on the acromioclavicular joint (shared with the scapula)", "clavicle")
_add("AA", (-38, 1446, 182), "AA", "Angulus acromialis, most laterodorsal point of the scapula", "scapula")
_add("TS", (-100, 1402, 72), "TS", "Trigonum spinae scapulae, midpoint of the triangular surface on the medial border", "scapula")
_add("AI", (-92, 1272, 92), "AI", "Angulus inferior, most caudal point of the scapula", "scapula")
_add("GC", (2, 1418, 168), "GC", "Glenoid centre (display only)", "scapula")
_add("GH", (8, 1412, 188), "GH", "Glenohumeral rotation centre (estimated by regression or motion recordings)", "humerus")
_add("EL", (0, 1110, 228), "EL", "Most caudal point on the lateral epicondyle", "humerus")
_add("EM", (4, 1108, 150), "EM", "Most caudal point on the medial epicondyle", "humerus")

# --- forearm (Wu et al. 2005) -------------------------------------------------------------------
_add("US", (16, 858, 222), "US", "Most caudal-medial point on the ulnar styloid", "ulna")
_add("RS", (19, 862, 282), "RS", "Most caudal-lateral point on the radial styloid", "radius")



# --- hand (Wu et al. 2005) ----------------------------------------------------------------------
def _hand_bone(b: str, name: str, base, head, half_width: float = 7.0):
    base, head = np.asarray(base, dtype=float), np.asarray(head, dtype=float)
    _add(f"{b}_b", base, f"{b} base", f"Centre of the base of the {name}", b)
    _add(f"{b}_h", head, f"{b} head", f"Centre of the head of the {name}", b)
    _add(f"{b}_hr", head + [0, 0, half_width], f"{b} hr", f"Radial side of the head of the {name}", b)
    _add(f"{b}_hu", head - [0, 0, half_width], f"{b} hu", f"Ulnar side of the head of the {name}", b)


_hand_bone("MC3", "third metacarpal", (22, 838, 258), (30, 772, 264))
_hand_bone("MC2", "second metacarpal", (22, 840, 274), (30, 776, 286))
_hand_bone("PP2", "proximal phalanx of the index", (31, 773, 287), (36, 733, 291), 6.0)
_hand_bone("MP2", "middle phalanx of the index", (36.5, 731, 291.5), (39, 706, 293), 5.0)


# --- positions detected on the meshes -------------------------------------------------------------------
_DETECTED = Path(__file__).parent / "data" / "landmarks.json"
FROM_MESHES = _DETECTED.exists()
if FROM_MESHES:
    for _key, _pos in json.loads(_DETECTED.read_text()).items():
        if _key in POSITIONS:
            POSITIONS[_key] = np.asarray(_pos, dtype=float)

# Ulnar styloid with the elbow flexed 90 deg (forearm pointing forward), used by humerus option 2.
_elbow_centre = (POSITIONS["EL"] + POSITIONS["EM"]) / 2
_flex = _rotation(POSITIONS["EL"] - POSITIONS["EM"], np.deg2rad(90))
_add(
    "US90",
    _elbow_centre + _flex @ (POSITIONS["US"] - _elbow_centre),
    "US (90°)",
    "Ulnar styloid with the elbow flexed 90° (humerus option 2 posture)",
    "ulna",
)
