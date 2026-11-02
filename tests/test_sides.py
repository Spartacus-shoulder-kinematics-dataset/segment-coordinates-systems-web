import numpy as np
import pytest

from isb.definitions import JOINTS
from isb.export import build_dataset

DATA = build_dataset()


@pytest.mark.parametrize("key", list(JOINTS))
def test_left_clinical_angles_equal_right_angles(key):
    """With mirrored landmarks, the sign-corrected left angles equal the right angles."""
    geo = DATA["joints"][key]["geometry"]
    np.testing.assert_allclose(geo["L"]["neutral_clinical"], geo["R"]["neutral_raw"], atol=0.02)
