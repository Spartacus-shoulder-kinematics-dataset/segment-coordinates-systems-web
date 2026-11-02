import numpy as np
import pytest

from isb.rotations import SEQUENCES, euler_from_matrix, is_proper_euler, left_side_signs, matrix_from_euler, middle_sign
from isb.sides import M

RNG = np.random.default_rng(0)


def random_angles(seq):
    a, c = RNG.uniform(-np.pi, np.pi, 2)
    b = RNG.uniform(0.1, np.pi - 0.1) if is_proper_euler(seq) else RNG.uniform(-1.4, 1.4)
    return np.array([a, b, c])


@pytest.mark.parametrize("seq", SEQUENCES)
def test_round_trip(seq):
    for _ in range(50):
        angles = random_angles(seq)
        R = matrix_from_euler(seq, angles)
        np.testing.assert_allclose(euler_from_matrix(seq, R), angles, atol=1e-9)


@pytest.mark.parametrize("seq", [s for s in SEQUENCES if s[0] == s[2]])
def test_middle_negative_is_the_same_rotation(seq):
    for _ in range(20):
        R = matrix_from_euler(seq, random_angles(seq))
        neg = euler_from_matrix(seq, R, middle_sign=-1)
        assert neg[1] < 0
        np.testing.assert_allclose(matrix_from_euler(seq, neg), R, atol=1e-12)


@pytest.mark.parametrize("seq", SEQUENCES)
def test_mirroring_flips_rotations_about_x_and_y(seq):
    """M R(a, b, c) M = R(signs * (a, b, c)): the rule used for the left side."""
    for _ in range(20):
        angles = random_angles(seq)
        mirrored = M @ matrix_from_euler(seq, angles) @ M
        np.testing.assert_allclose(mirrored, matrix_from_euler(seq, left_side_signs(seq) * angles), atol=1e-12)
        sign = middle_sign(seq, angles[1] < 0, "L")
        np.testing.assert_allclose(
            euler_from_matrix(seq, mirrored, sign) * left_side_signs(seq),
            euler_from_matrix(seq, matrix_from_euler(seq, angles), -1 if angles[1] < 0 else 1),
            atol=1e-9,
        )
