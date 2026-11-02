"""Numerical evaluation of segment constructions and joint coordinate systems."""

from dataclasses import dataclass

import numpy as np

from .model import JointCS, SegmentCS
from .rotations import AXIS_INDEX, elementary, euler_from_matrix, middle_sign


@dataclass
class SegmentFrame:
    values: dict  # step name -> np.ndarray (point or vector), in global coordinates
    origin: np.ndarray
    R: np.ndarray  # columns are X, Y, Z of the segment, in global coordinates


def evaluate_expr(expr, env: dict, resolve):
    """Evaluate an expression tree. Strings are step names, landmark keys or "segment.AXIS" references."""
    if isinstance(expr, str):
        if expr in env:
            return env[expr]
        return resolve(expr)
    op, *args = expr
    vals = [evaluate_expr(a, env, resolve) for a in args]
    if op == "mid":
        return (vals[0] + vals[1]) / 2
    if op == "sub":
        return vals[0] - vals[1]
    if op == "unit":
        return vals[0] / np.linalg.norm(vals[0])
    if op == "cross":
        return np.cross(vals[0], vals[1])
    if op == "reject":
        return vals[0] - np.dot(vals[0], vals[1]) * vals[1]
    if op == "neg":
        return -vals[0]
    raise ValueError(f"unknown operator {op!r}")


def expr_leaves(expr) -> list[str]:
    if isinstance(expr, str):
        return [expr]
    return [leaf for arg in expr[1:] for leaf in expr_leaves(arg)]


class Evaluator:
    """Evaluates every segment of a registry on one set of landmark positions, resolving cross-segment
    references such as "thorax.Y". `reference_frame(key) -> (origin, R)` overrides the frame used for such
    references (the left side refers to the final, rule-applied frames, not the literal ones)."""

    def __init__(self, segments: dict[str, SegmentCS], positions: dict[str, np.ndarray], reference_frame=None):
        self.segments = segments
        self.positions = positions
        self.reference_frame = reference_frame
        self._cache: dict[str, SegmentFrame] = {}

    def resolve(self, name: str) -> np.ndarray:
        if name in self.positions:
            return self.positions[name]
        if "." in name:
            seg, axis = name.split(".")
            if self.reference_frame is not None:
                origin, R = self.reference_frame(seg)
            else:
                frame = self.frame(seg)
                origin, R = frame.origin, frame.R
            return origin if axis == "o" else R[:, AXIS_INDEX[axis]]
        raise KeyError(f"unknown name {name!r}")

    def frame(self, key: str) -> SegmentFrame:
        if key not in self._cache:
            seg = self.segments[key]
            env: dict[str, np.ndarray] = {}
            for step in seg.steps:
                env[step.name] = evaluate_expr(step.expr, env, self.resolve)
            R = np.column_stack([env["X"], env["Y"], env["Z"]])
            self._cache[key] = SegmentFrame(values=env, origin=env["o"], R=R)
        return self._cache[key]


def relative_rotation(R_parent: np.ndarray, R_child: np.ndarray) -> np.ndarray:
    """Orientation of the child expressed in the parent: R_parent.T @ R_child."""
    return R_parent.T @ R_child


def jcs_angles(joint: JointCS, R_parent: np.ndarray, R_child: np.ndarray, side: str = "R") -> np.ndarray:
    """Raw JCS angles (radians) of the child relative to the parent."""
    sign = middle_sign(joint.sequence, joint.middle_negative, side)
    return euler_from_matrix(joint.sequence, relative_rotation(R_parent, R_child), sign)


def jcs_axes(joint: JointCS, R_parent: np.ndarray, angles) -> np.ndarray:
    """e1 (fixed in the parent), e2 (floating: the second rotation axis after the first rotation) and
    e3 (fixed in the child), as columns, in global coordinates."""
    seq = joint.sequence
    R1 = R_parent @ elementary(seq[0], angles[0])
    R2 = R1 @ elementary(seq[1], angles[1])
    R_child = R2 @ elementary(seq[2], angles[2])
    e1 = R_parent[:, AXIS_INDEX[seq[0]]]
    e2 = R1[:, AXIS_INDEX[seq[1]]]
    e3 = R_child[:, AXIS_INDEX[seq[2]]]
    return np.column_stack([e1, e2, e3])


def floating_axis_by_cross(joint: JointCS, e1: np.ndarray, e3: np.ndarray) -> np.ndarray:
    """Grood & Suntay floating axis as a normalized cross product of e1 and e3.
    For cyclic Cardan sequences (XYZ, YZX, ZXY) it is e3 x e1, otherwise e1 x e3. For proper Euler
    sequences the sign depends on the sign of the middle angle, which is why jcs_axes() is preferred."""
    cyclic = joint.sequence in ("XYZ", "YZX", "ZXY")
    v = np.cross(e3, e1) if cyclic else np.cross(e1, e3)
    return v / np.linalg.norm(v)
