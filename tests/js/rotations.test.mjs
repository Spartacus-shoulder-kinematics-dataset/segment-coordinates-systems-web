// Usage: node tests/js/rotations.test.mjs <vectors.json>
// Compares static/js/rotations.js with scipy-generated vectors (see tests/test_js_parity.py).
import { readFileSync } from "node:fs";
import { eulerFromMatrix, matrixFromEuler } from "../../static/js/rotations.js";

const cases = JSON.parse(readFileSync(process.argv[2], "utf8"));
let failures = 0;
const close = (a, b, tol = 1e-9) => a.every((x, i) => Math.abs(x - b[i]) < tol);

for (const c of cases) {
  const R = matrixFromEuler(c.seq, c.angles);
  if (!close(R.flat(), c.R.flat())) {
    failures++;
    console.error("matrixFromEuler", c.seq, c.angles);
  }
  const got = eulerFromMatrix(c.seq, c.R, c.middle_sign);
  if (!close(got, c.expected)) {
    failures++;
    console.error("eulerFromMatrix", c.seq, c.middle_sign, "got", got, "expected", c.expected);
  }
}
console.log(`${cases.length} cases, ${failures} failures`);
process.exit(failures ? 1 : 0);
