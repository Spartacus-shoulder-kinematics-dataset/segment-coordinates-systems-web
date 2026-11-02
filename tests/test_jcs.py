import numpy as np
import pytest

from isb.definitions import JOINTS, SEGMENTS
from isb.geometry import Evaluator, evaluate_expr, floating_axis_by_cross, jcs_angles, jcs_axes
from isb.landmarks import POSITIONS
from isb.rotations import is_proper_euler, matrix_from_euler

EV = Evaluator(SEGMENTS, POSITIONS)
RNG = np.random.default_rng(1)


def random_angles(joint):
    a, c = RNG.uniform(-np.pi, np.pi, 2)
    if is_proper_euler(joint.sequence):
        b = RNG.uniform(0.1, np.pi - 0.1) * (-1 if joint.middle_negative else 1)
    else:
        b = RNG.uniform(-1.4, 1.4)
    return np.array([a, b, c])


@pytest.mark.parametrize("key", list(JOINTS))
def test_angles_round_trip_and_axes(key):
    joint = JOINTS[key]
    R_p = EV.frame(joint.parent).R
    for _ in range(30):
        angles = random_angles(joint)
        R_c = R_p @ matrix_from_euler(joint.sequence, angles)
        np.testing.assert_allclose(jcs_angles(joint, R_p, R_c), angles, atol=1e-9)
        e = jcs_axes(joint, R_p, angles)
        assert abs(e[:, 0] @ e[:, 1]) < 1e-9 and abs(e[:, 2] @ e[:, 1]) < 1e-9
        from_cross = floating_axis_by_cross(joint, e[:, 0], e[:, 2])
        sign = np.sign(np.sin(angles[1])) if is_proper_euler(joint.sequence) else 1
        np.testing.assert_allclose(from_cross * sign, e[:, 1], atol=1e-9)


def _pose(joint, angles_deg, point):
    """Global position of a child point when the child is posed at `angles_deg` (rotating about the
    joint pivot, as the site's playground does)."""
    child = EV.frame(joint.child)
    pivot = child.origin if joint.pivot is None else evaluate_expr(joint.pivot, {}, EV.resolve)
    R_child = EV.frame(joint.parent).R @ matrix_from_euler(joint.sequence, np.deg2rad(angles_deg))
    return pivot + R_child @ child.R.T @ (point - pivot)


def mid(a, b):
    return (POSITIONS[a] + POSITIONS[b]) / 2


# (joint, base angles, angle index, child point, expected displacement direction, meaning)
X, Y, Z = np.eye(3)
SIGN_CHECKS = [
    ("hip", (0, 0, 0), 0, mid("LFE", "MFE"), X, "flexion moves the knee forward"),
    ("hip", (0, 0, 0), 1, mid("LFE", "MFE"), -Z, "adduction moves the knee medially"),
    ("hip", (0, 0, 0), 2, POSITIONS["LFE"], X, "internal rotation moves the lateral epicondyle forward"),
    ("knee", (0, 0, 0), 0, mid("MM", "LM"), X, "positive e1 rotation (extension) moves the ankle forward"),
    ("knee", (0, 0, 0), 1, mid("MM", "LM"), -Z, "adduction (varus) moves the ankle medially"),
    ("ankle_complex", (0, 0, 0), 0, POSITIONS["MH1"], Y, "dorsiflexion lifts the forefoot"),
    ("ankle_complex", (0, 0, 0), 1, ("MH5", "MH1"), -Y, "inversion lowers the lateral border relative to the medial"),
    ("ankle_complex", (0, 0, 0), 2, POSITIONS["MH1"], -Z, "internal rotation turns the toes medially"),
    ("L4_L5", (0, 0, 0), 0, POSITIONS["L4_ue"], -X, "extension tilts the upper vertebra backward"),
    ("L4_L5", (0, 0, 0), 1, POSITIONS["L4_ue"], Z, "right lateral bending"),
    ("L4_L5", (0, 0, 0), 2, POSITIONS["L4_rp"], X, "left axial rotation brings the right side forward"),
    ("sc", (0, 0, 0), 0, POSITIONS["AC"], X, "protraction moves AC forward"),
    ("sc", (0, 0, 0), 1, POSITIONS["AC"], -Y, "depression lowers AC"),
    ("st", (0, 0, 0), 0, ("AA", "TS"), X, "protraction brings AA forward relative to TS"),
    ("st", (0, 0, 0), 1, POSITIONS["AI"], -Z, "medial (downward) rotation moves AI medially"),
    ("st", (0, 0, 0), 2, POSITIONS["AI"], X, "posterior tilt moves AI forward"),
    ("gh", (0, -30, 0), 1, mid("EL", "EM"), -Z, "less elevation (positive step) brings the elbow back medially"),
    ("th", (0, -30, 0), 1, mid("EL", "EM"), -Z, "less elevation (positive step) brings the elbow back medially"),
    ("th", (0, 0, 0), 2, POSITIONS["EL"], X, "internal rotation moves the lateral epicondyle forward"),
    ("elbow", (0, 0, 0), 0, POSITIONS["US"], X, "flexion moves the wrist forward"),
    ("elbow", (0, 0, 0), 1, POSITIONS["US"], -Z, "adduction (varus) moves the wrist medially"),
    ("elbow", (0, 0, 0), 2, POSITIONS["RS"], X, "pronation moves the radial styloid forward"),
    ("wrist", (0, 0, 0), 0, POSITIONS["MC3_h"], X, "flexion moves the hand volarly"),
    ("wrist", (0, 0, 0), 1, POSITIONS["MC3_h"], -Z, "ulnar deviation moves the hand to the ulnar side"),
    ("mcp2", (0, 0, 0), 0, POSITIONS["PP2_h"], X, "flexion moves the finger volarly"),
]


@pytest.mark.parametrize("key, base, index, point, direction, meaning", SIGN_CHECKS)
def test_positive_rotation_has_the_documented_clinical_meaning(key, base, index, point, direction, meaning):
    joint = JOINTS[key]
    step = np.array(base, dtype=float)
    step[index] += 5

    def where(angles):
        if isinstance(point, tuple):  # a landmark-to-landmark vector
            return _pose(joint, angles, POSITIONS[point[0]]) - _pose(joint, angles, POSITIONS[point[1]])
        return _pose(joint, angles, point)

    displacement = where(step) - where(base)
    assert displacement @ direction > 0.5 * np.linalg.norm(displacement), meaning


@pytest.mark.parametrize("plane, direction", [(0, Z), (90, X)])
def test_plane_of_elevation(plane, direction):
    """Plane of elevation 0 deg = abduction (elbow moves laterally), 90 deg = forward flexion."""
    joint = JOINTS["th"]
    moved = _pose(joint, (plane, -60, 0), mid("EL", "EM")) - _pose(joint, (plane, 0, 0), mid("EL", "EM"))
    horizontal = moved * [1, 0, 1]  # the elbow also rises; compare the horizontal direction only
    assert horizontal @ direction > 0.9 * np.linalg.norm(horizontal)
