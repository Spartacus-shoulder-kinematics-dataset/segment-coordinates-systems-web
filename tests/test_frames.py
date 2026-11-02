import numpy as np
import pytest

from isb.definitions import SEGMENTS
from isb.export import build_dataset

DATA = build_dataset()
GLOBAL = {"X": [1, 0, 0], "Y": [0, 1, 0], "Z": [0, 0, 1]}
# Segments that are not near the neutral posture in the BodyParts3D subject (relaxed, flexed index finger)
NOT_NEUTRAL = {"MP2"}


@pytest.mark.parametrize("side", ["R", "L"])
@pytest.mark.parametrize("key", list(SEGMENTS))
def test_frames_are_right_handed_and_isb_oriented(key, side):
    geo = DATA["segments"][key]["geometry"][side]
    R = np.column_stack([geo["axes"][a] for a in "XYZ"])
    np.testing.assert_allclose(R.T @ R, np.eye(3), atol=1e-4)
    assert np.linalg.det(R) == pytest.approx(1, abs=1e-4)
    # X anterior, Y superior, Z to the right, on both sides: each axis is closest to its global direction.
    # Real anatomy is not aligned (tibial torsion, scapular protraction), hence no tighter bound.
    if key in NOT_NEUTRAL:
        return
    for i, a in enumerate("XYZ"):
        dots = R[:, i]
        assert np.argmax(np.abs(dots)) == i and dots[i] > 0.5, f"{key} {side}: {a} = {R[:, i]}"


@pytest.mark.parametrize("key", list(SEGMENTS))
def test_left_literal_axes_are_signed_copies_of_final_axes(key):
    """Applying right-side formulas to mirrored landmarks gives the final left axes up to a sign flip,
    which the site shows as the "left-side rule" step."""
    geo = DATA["segments"][key]["geometry"]["L"]
    for a in "XYZ":
        lit, fin = np.array(geo["literal_axes"][a]), np.array(geo["axes"][a])
        expected = -fin if a in geo["flipped"] else fin
        np.testing.assert_allclose(lit, expected, atol=1e-4)


@pytest.mark.parametrize("key", list(SEGMENTS))
def test_origin_matches_origin_step(key):
    seg = DATA["segments"][key]
    geo = seg["geometry"]["R"]
    np.testing.assert_allclose(geo["origin"], geo["steps"]["o"]["value"], atol=1e-3)
