"""Declarative description of ISB segment (LCS) and joint (JCS) coordinate systems.

An axis construction is a list of `Step`s. Each step binds a name to an expression built from
landmark keys, names of previous steps, references to another segment's axes ("thorax.Y") and the
operators below. The same expression tree is evaluated numerically (geometry.py) and rendered as
an HTML formula (export.py), so what the site shows is exactly what is computed.
"""

from dataclasses import dataclass, field
from typing import Union

Expr = Union[str, tuple]


# --- expression constructors -------------------------------------------------------------------
def mid(a: Expr, b: Expr) -> tuple:
    """Midpoint of two points."""
    return ("mid", a, b)


def sub(end: Expr, start: Expr) -> tuple:
    """Vector from `start` to `end`."""
    return ("sub", end, start)


def unit(v: Expr) -> tuple:
    return ("unit", v)


def cross(a: Expr, b: Expr) -> tuple:
    return ("cross", a, b)


def reject(v: Expr, n: Expr) -> tuple:
    """Component of `v` orthogonal to the unit vector `n`: v - (v.n) n."""
    return ("reject", v, n)


def neg(v: Expr) -> tuple:
    return ("neg", v)


@dataclass(frozen=True)
class Reference:
    key: str
    short: str
    full: str
    doi: str


@dataclass(frozen=True)
class Landmark:
    key: str
    name: str
    description: str
    bone: str
    mirror_label: str | None = None  # label to show on the left side (e.g. RASIS -> LASIS)


@dataclass(frozen=True)
class Step:
    name: str
    expr: Expr
    text: str
    kind: str = "vector"  # "point" | "vector" | "axis" | "origin"
    anchor: str | None = None  # point name the vector is drawn from (default: inferred)


@dataclass(frozen=True)
class SegmentCS:
    key: str
    name: str
    region: str
    reference: str
    section: str
    axes_text: dict  # {"o": ..., "X": ..., "Y": ..., "Z": ...} paraphrase of the recommendation
    steps: tuple
    landmarks: tuple  # landmark keys drawn with this segment
    links: tuple = ()  # (a, b) landmark pairs drawn as bone sticks
    planes: tuple = ()  # (a, b, c) landmark triples drawn as translucent triangles
    option_group: str | None = None  # segments sharing a group are shown as tabs of one card
    option_label: str | None = None
    notes: tuple = ()
    needs_check: tuple = ()  # items to verify against the paper
    view: tuple = (1.0, 0.35, 0.8)  # default camera direction (right side; mirrored for the left)
    meshes: tuple = ()  # bone mesh groups drawn with this segment (static/meshes/<group>.bin)


@dataclass(frozen=True)
class AngleDef:
    label: str  # e.g. "Flexion / extension"
    positive: str  # clinical name of a positive rotation (right side, right-hand rule)
    negative: str
    range: tuple = (-180.0, 180.0)  # slider range in degrees
    note: str = ""


@dataclass(frozen=True)
class JointCS:
    key: str
    name: str
    region: str
    reference: str
    section: str
    parent: str
    child: str
    sequence: str  # intrinsic sequence of the child relative to the parent, e.g. "ZXY"
    angles: tuple  # three AngleDef, in sequence order (about e1, e2, e3)
    axes_text: dict  # {"e1": ..., "e2": ..., "e3": ...}
    translations: str = ""
    middle_negative: bool = False  # proper Euler sequences: pick the solution with the middle angle <= 0
    pivot: Expr | None = None  # point the playground rotates the child about (default: child origin)
    notes: tuple = ()
    needs_check: tuple = ()
    view: tuple = (1.0, 0.35, 0.8)


@dataclass(frozen=True)
class Region:
    key: str
    title: str
    references: tuple
    intro: str
    segments: tuple
    joints: tuple
    notes: tuple = field(default_factory=tuple)
    status: str = "ISB recommendation"
    sided: bool = True  # False for midline structures (spine): no left/right toggle
