"""static/js/rotations.js must match isb/rotations.py (scipy) for every sequence."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from isb.rotations import SEQUENCES, euler_from_matrix, is_proper_euler, matrix_from_euler

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_js_rotations_match_scipy(tmp_path):
    rng = np.random.default_rng(2)
    cases = []
    for seq in SEQUENCES:
        for _ in range(40):
            a, c = rng.uniform(-np.pi, np.pi, 2)
            b = rng.uniform(0.05, np.pi - 0.05) if is_proper_euler(seq) else rng.uniform(-1.5, 1.5)
            R = matrix_from_euler(seq, [a, b, c])
            for sign in (1, -1) if is_proper_euler(seq) else (1,):
                cases.append(
                    {
                        "seq": seq,
                        "angles": [a, b, c],
                        "R": R.tolist(),
                        "middle_sign": sign,
                        "expected": euler_from_matrix(seq, R, sign).tolist(),
                    }
                )
    path = tmp_path / "vectors.json"
    path.write_text(json.dumps(cases))
    out = subprocess.run(
        ["node", str(ROOT / "tests/js/rotations.test.mjs"), str(path)], capture_output=True, text=True
    )
    assert out.returncode == 0, out.stdout + out.stderr
