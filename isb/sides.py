"""Left side handling.

ISB defines the right side. For the left side the site uses the "Z to the right on both sides" practice:
1. mirror the right-side construction through the sagittal plane (M = diag(1, 1, -1));
2. the mirror image of a right-handed frame is left-handed (X anterior, Y superior, Z lateral = left),
   so Z is flipped to point to the right again: R_left = M @ R_right @ M.
Joint angles then satisfy R_rel_left = M @ R_rel_right @ M, i.e. rotations about Z keep their sign while
rotations about X and Y flip (rotations.left_side_signs). Multiplying the raw left angles by those signs
gives clinically symmetric values; this equals "mirror the left data, then process it as a right side".
"""

import numpy as np

M = np.diag([1.0, 1.0, -1.0])


def mirror_point(p: np.ndarray) -> np.ndarray:
    return M @ p


def left_frame(R_right: np.ndarray) -> np.ndarray:
    return M @ R_right @ M


def mirrored_positions(positions: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    return {k: M @ v for k, v in positions.items()}
