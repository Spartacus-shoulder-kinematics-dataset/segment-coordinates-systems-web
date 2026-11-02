"""Intrinsic Euler / Cardan sequences (the 12 of them), on top of scipy.

Convention: an intrinsic sequence "ZXY" means R = Rz(a) @ Rx(b) @ Ry(c), where R maps child-frame
coordinates to parent-frame coordinates (R = R_parent.T @ R_child). Upper-case letters are intrinsic in scipy.
static/js/rotations.js implements the same maths and is tested against this module.
"""

import warnings

import numpy as np
from scipy.spatial.transform import Rotation

SEQUENCES = ("XYZ", "XZY", "YXZ", "YZX", "ZXY", "ZYX", "XYX", "XZX", "YXY", "YZY", "ZXZ", "ZYZ")
AXIS_INDEX = {"X": 0, "Y": 1, "Z": 2}
GIMBAL_WARNING = np.sin(np.deg2rad(10))  # warn when the margin drops below sin(10 deg)


def is_proper_euler(seq: str) -> bool:
    """True for proper Euler sequences (first and last axis identical, e.g. YXY)."""
    return seq[0] == seq[2]


def elementary(axis: str, angle: float) -> np.ndarray:
    c, s = np.cos(angle), np.sin(angle)
    if axis == "X":
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    if axis == "Y":
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def matrix_from_euler(seq: str, angles) -> np.ndarray:
    return Rotation.from_euler(seq, np.asarray(angles, dtype=float)).as_matrix()


def wrap(angle: float) -> float:
    """Wrap to (-pi, pi]."""
    a = (angle + np.pi) % (2 * np.pi) - np.pi
    return np.pi if np.isclose(a, -np.pi) else a


def euler_from_matrix(seq: str, matrix: np.ndarray, middle_sign: int = 1) -> np.ndarray:
    """Decompose a rotation matrix. For proper Euler sequences scipy returns the middle angle in [0, pi];
    `middle_sign=-1` selects the equivalent solution (a + pi, -b, c + pi), as used by ISB for YXY
    (glenohumeral elevation is negative). Cardan sequences ignore `middle_sign`."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # scipy warns at gimbal lock and sets the third angle to 0
        a, b, c = Rotation.from_matrix(matrix).as_euler(seq)
    if middle_sign < 0 and is_proper_euler(seq) and b > 0:
        a, b, c = wrap(a + np.pi), -b, wrap(c + np.pi)
    return np.array([a, b, c])


def gimbal_margin(seq: str, angles) -> float:
    """1 far from gimbal lock, 0 at gimbal lock: |cos b| for Cardan, |sin b| for proper Euler."""
    b = angles[1]
    return float(abs(np.sin(b)) if is_proper_euler(seq) else abs(np.cos(b)))


def middle_sign(seq: str, middle_negative: bool, side: str) -> int:
    """Preferred sign of the middle angle. On the left side a rotation about X or Y flips, so the
    preferred sign flips with it."""
    sign = -1 if middle_negative else 1
    if side == "L" and seq[1] != "Z":
        sign = -sign
    return sign


def left_side_signs(seq: str) -> np.ndarray:
    """Mirroring through the sagittal plane (z -> -z) keeps rotations about Z and flips rotations about
    X and Y. With frames defined "Z to the right" on both sides, left angles = signs * mirrored right angles."""
    return np.array([1.0 if letter == "Z" else -1.0 for letter in seq])
