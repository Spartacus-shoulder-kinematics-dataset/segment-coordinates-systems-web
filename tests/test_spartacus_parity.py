"""Cross-check the shoulder definitions against SPARTACUS (../shoulder-kinematics), when available."""

import sys
from pathlib import Path

import numpy as np
import pytest

from isb.definitions import JOINTS, SEGMENTS
from isb.rotations import SEQUENCES, matrix_from_euler
from isb.sides import M

SPARTACUS = Path(__file__).resolve().parents[2] / "shoulder-kinematics"
if not SPARTACUS.exists():
    pytest.skip("shoulder-kinematics not found next to isb-web", allow_module_level=True)
sys.path.insert(0, str(SPARTACUS))
spartacus = pytest.importorskip("spartacus")
from spartacus.src.corrections.angle_conversion_callbacks import to_left_handed_frame  # noqa: E402
from spartacus.src.enums_biomech import AnatomicalLandmark, EulerSequence, JointType  # noqa: E402


@pytest.mark.parametrize(
    "joint_type, key",
    [
        (JointType.STERNO_CLAVICULAR, "sc"),
        (JointType.ACROMIO_CLAVICULAR, "ac"),
        (JointType.SCAPULO_THORACIC, "st"),
        (JointType.GLENO_HUMERAL, "gh"),
        (JointType.THORACO_HUMERAL, "th"),
    ],
)
def test_sequences(joint_type, key):
    assert EulerSequence.isb_from_joint_type(joint_type).value.upper() == JOINTS[key].sequence


@pytest.mark.parametrize(
    "landmark_enum, segment, origin",
    [
        (AnatomicalLandmark.Thorax, "thorax", "IJ"),
        (AnatomicalLandmark.Clavicle, "clavicle", "SC"),
        (AnatomicalLandmark.Scapula, "scapula", "AA"),
        (AnatomicalLandmark.Humerus, "humerus", "GH"),
    ],
)
def test_origins(landmark_enum, segment, origin):
    origin_step = next(s for s in SEGMENTS[segment].steps if s.name == "o")
    assert origin_step.expr == origin
    assert AnatomicalLandmark.from_string(origin) == landmark_enum.origin_isb()


@pytest.mark.parametrize("seq", SEQUENCES)
def test_left_rule_matches_spartacus(seq):
    R = matrix_from_euler(seq, [0.3, 0.4, -0.5])
    np.testing.assert_allclose(to_left_handed_frame(R), M @ R @ M, atol=1e-12)
