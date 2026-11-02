// Intrinsic Euler / Cardan sequences, same conventions as isb/rotations.py (scipy, upper-case sequences).
// Matrices are arrays of 3 rows. R = R_i(a) R_j(b) R_k(c) maps child coordinates to parent coordinates.

export const SEQUENCES = ["XYZ", "XZY", "YXZ", "YZX", "ZXY", "ZYX", "XYX", "XZX", "YXY", "YZY", "ZXZ", "ZYZ"];
export const AXIS_INDEX = { X: 0, Y: 1, Z: 2 };
export const GIMBAL_WARNING = Math.sin((10 * Math.PI) / 180);
const EPS = 1e-9;

export const deg = (r) => (r * 180) / Math.PI;
export const rad = (d) => (d * Math.PI) / 180;

export function isProperEuler(seq) {
  return seq[0] === seq[2];
}

export function elementary(axis, a) {
  const c = Math.cos(a), s = Math.sin(a);
  if (axis === "X") return [[1, 0, 0], [0, c, -s], [0, s, c]];
  if (axis === "Y") return [[c, 0, s], [0, 1, 0], [-s, 0, c]];
  return [[c, -s, 0], [s, c, 0], [0, 0, 1]];
}

export function matmul(A, B) {
  const C = [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
  for (let i = 0; i < 3; i++)
    for (let j = 0; j < 3; j++) C[i][j] = A[i][0] * B[0][j] + A[i][1] * B[1][j] + A[i][2] * B[2][j];
  return C;
}

export function transpose(A) {
  return [0, 1, 2].map((i) => [A[0][i], A[1][i], A[2][i]]);
}

export function matvec(A, v) {
  return [0, 1, 2].map((i) => A[i][0] * v[0] + A[i][1] * v[1] + A[i][2] * v[2]);
}

/** Matrix whose columns are the three given vectors. */
export function fromColumns(c0, c1, c2) {
  return [0, 1, 2].map((i) => [c0[i], c1[i], c2[i]]);
}

export function column(A, j) {
  return [A[0][j], A[1][j], A[2][j]];
}

export function matrixFromEuler(seq, angles) {
  return matmul(matmul(elementary(seq[0], angles[0]), elementary(seq[1], angles[1])), elementary(seq[2], angles[2]));
}

function wrap(a) {
  let w = ((((a + Math.PI) % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI)) - Math.PI;
  if (Math.abs(w + Math.PI) < 1e-12) w = Math.PI;
  return w;
}

const clamp1 = (x) => Math.max(-1, Math.min(1, x));

/**
 * Decompose R into the intrinsic sequence `seq`. Ranges follow scipy: Cardan middle angle in [-pi/2, pi/2],
 * proper Euler middle angle in [0, pi]; at gimbal lock the third angle is set to 0.
 * middleSign = -1 selects the proper-Euler solution with a negative middle angle (ISB YXY elevation).
 */
export function eulerFromMatrix(seq, R, middleSign = 1) {
  const i = AXIS_INDEX[seq[0]], j = AXIS_INDEX[seq[1]];
  let a, b, c;
  if (!isProperEuler(seq)) {
    const k = AXIS_INDEX[seq[2]];
    const s = (j - i + 3) % 3 === 1 ? 1 : -1; // +1 when (i, j, k) is cyclic
    b = Math.asin(clamp1(s * R[i][k]));
    if (Math.abs(Math.cos(b)) > EPS * 1e3) {
      a = Math.atan2(-s * R[j][k], R[k][k]);
      c = Math.atan2(-s * R[i][j], R[i][i]);
    } else {
      c = 0;
      a = Math.atan2(s * R[k][j], R[j][j]);
    }
  } else {
    const m = 3 - i - j;
    const s = (j - i + 3) % 3 === 1 ? 1 : -1; // +1 when (i, j, m) is cyclic
    b = Math.acos(clamp1(R[i][i]));
    if (Math.abs(Math.sin(b)) > EPS * 1e3) {
      a = Math.atan2(R[j][i], -s * R[m][i]);
      c = Math.atan2(R[i][j], s * R[i][m]);
    } else {
      c = 0;
      a = Math.atan2(s * R[m][j], R[j][j]);
    }
    if (middleSign < 0 && b > 0) {
      a = wrap(a + Math.PI);
      b = -b;
      c = wrap(c + Math.PI);
    }
  }
  return [a, b, c];
}

/** 1 far from gimbal lock, 0 at gimbal lock. */
export function gimbalMargin(seq, angles) {
  return isProperEuler(seq) ? Math.abs(Math.sin(angles[1])) : Math.abs(Math.cos(angles[1]));
}

/** Preferred middle sign on a given side (rotations about X and Y flip sign on the left). */
export function middleSign(seq, middleNegative, side) {
  let s = middleNegative ? -1 : 1;
  if (side === "L" && seq[1] !== "Z") s = -s;
  return s;
}

/** Left side: rotations about Z keep their sign, rotations about X and Y flip. */
export function sideSigns(seq, side) {
  return [...seq].map((l) => (side === "L" && l !== "Z" ? -1 : 1));
}
