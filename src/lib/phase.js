import { growthParameters, growthSteady } from './models.js';

const { alpha, A, delta, rho, sigma } = growthParameters;
export const steady = growthSteady;
export const limits = { k: 19.5, c: 2.55 };
export const netOutput = k => A * Math.max(0, k) ** alpha - delta * k;
export function velocity(k, c) {
  const kk = Math.max(k, 1e-9);
  return { dk: netOutput(kk) - c, dc: c * (alpha * A * kk ** (alpha - 1) - delta - rho) / sigma };
}
function step(point, dt) {
  const { k, c } = point;
  const a = velocity(k, c);
  const b = velocity(k + dt * a.dk / 2, c + dt * a.dc / 2);
  const d = velocity(k + dt * b.dk / 2, c + dt * b.dc / 2);
  const e = velocity(k + dt * d.dk, c + dt * d.dc);
  return { k: k + dt * (a.dk + 2*b.dk + 2*d.dk + e.dk) / 6,
    c: c + dt * (a.dc + 2*b.dc + 2*d.dc + e.dc) / 6 };
}
const fpp = alpha * (alpha - 1) * A * steady.k ** (alpha - 2);
const stableEigenvalue = (rho - Math.sqrt(rho * rho - 4 * steady.c * fpp / sigma)) / 2;
const stableSlope = rho - stableEigenvalue;

// Trace the nonlinear stable manifold backwards from the stable eigenvector.
function arm(sign) {
  let point = { k: steady.k + sign * 1e-6, c: steady.c + sign * stableSlope * 1e-6 };
  const points = [{ ...point, backTime: 0 }];
  for (let i = 1; i <= 24000; i++) {
    const next = step(point, -.02);
    if (!Number.isFinite(next.k + next.c) || next.k < .08 || next.k > limits.k || next.c < .01 || next.c > limits.c) break;
    point = next;
    points.push({ ...point, backTime: i * .02 });
  }
  return points;
}
export const saddleArms = { left: arm(-1), right: arm(1) };
export function saddleConsumption(k) {
  const points = k < steady.k ? saddleArms.left : saddleArms.right;
  const exact = points.findIndex(p => (k < steady.k ? p.k <= k : p.k >= k));
  if (exact < 1) return exact === 0 ? points[0].c : steady.c;
  const a = points[exact - 1], b = points[exact];
  return a.c + (b.c - a.c) * (k - a.k) / (b.k - a.k);
}
export function simulate(k0, c0, onSaddle = false) {
  if (onSaddle) {
    // Forward integration of a saddle is numerically unstable. Traverse the
    // backwards-computed arm toward the steady state instead.
    const sign = k0 < steady.k ? -1 : 1;
    const points = sign < 0 ? saddleArms.left : saddleArms.right;
    let j = points.findIndex(p => sign < 0 ? p.k <= k0 : p.k >= k0);
    if (j < 1) j = 1;
    const startBack = points[j].backTime;
    const trajectory = [];
    for (let t = 0; t <= 100.0001; t += .1) {
      const target = startBack - t;
      if (target <= 0) {
        const decay = Math.exp(stableEigenvalue * (t - startBack));
        trajectory.push({ t, k: steady.k + sign * 1e-6 * decay, c: steady.c + sign * stableSlope * 1e-6 * decay });
      } else {
        const index = Math.min(points.length - 1, Math.max(0, Math.floor(target / .02)));
        const a = points[index], b = points[Math.min(index + 1, points.length - 1)];
        const weight = (target - a.backTime) / Math.max(.02, b.backTime - a.backTime);
        trajectory.push({ t, k: a.k + weight * (b.k - a.k), c: a.c + weight * (b.c - a.c) });
      }
    }
    trajectory[0] = { t: 0, k: k0, c: c0 };
    return { trajectory, outcome: 'stable', exitTime: null };
  }
  let point = { k: k0, c: c0 };
  const trajectory = [{ t: 0, ...point }];
  let outcome = 'horizon', exitTime = null;
  const dt = .05;
  for (let i = 1; i <= 2000; i++) {
    const next = step(point, dt);
    const t = i * dt;
    if (!Number.isFinite(next.k + next.c) || next.k <= .08 || next.c >= limits.c) {
      outcome = 'exhaustion'; exitTime = t; break;
    }
    if (next.c <= .01 || next.k >= limits.k) {
      outcome = 'overaccumulation'; exitTime = t; break;
    }
    point = next;
    trajectory.push({ t, ...point });
  }
  return { trajectory, outcome, exitTime };
}
