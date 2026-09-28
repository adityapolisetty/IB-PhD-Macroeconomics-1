export const solowParameters = { alpha: 1 / 3, A: 1, depreciation: .06 };
export function solow(s = .2, initial = 1, step = 1, horizon = 120) {
  const { alpha, A, depreciation: d } = solowParameters;
  const steady = (s * A / d) ** (1 / (1 - alpha));
  const exact = Array.from({ length: 241 }, (_, i) => {
    const t = i * horizon / 240;
    const k = (steady ** (1 - alpha) + (initial ** (1 - alpha) - steady ** (1 - alpha)) * Math.exp(-(1 - alpha) * d * t)) ** (1 / (1 - alpha));
    return { x: t, y: k };
  });
  const euler = [{ x: 0, y: initial }];
  let k = initial, t = 0;
  while (t < horizon - 1e-9) {
    const dt = Math.min(step, horizon - t);
    k += dt * (s * A * k ** alpha - d * k);
    t += dt;
    euler.push({ x: t, y: k });
  }
  const end = Math.max(steady, initial) * 1.35;
  const investment = Array.from({ length: 161 }, (_, i) => ({ x: i * end / 160, y: s * A * (i * end / 160) ** alpha }));
  const depreciation = [{ x: 0, y: 0 }, { x: end, y: d * end }];
  return { steady, exact, euler, investment, depreciation, drift: s * A * initial ** alpha - d * initial };
}

export const householdParameters = { r: .05, g: .01, wage: 1, initialAssets: 1 };
export function household(offset = 0, horizon = 240) {
  const { r, g, wage, initialAssets } = householdParameters;
  const optimal = (r - g) * (initialAssets + wage / r);
  const guess = optimal * (1 + offset);
  const wealth = (c, t) => -wage / r + c / (r - g) * Math.exp(g * t) + (initialAssets + wage / r - c / (r - g)) * Math.exp(r * t);
  let exhaustion = null;
  if (offset > 0) {
    for (let t = .5; t <= horizon; t += .5) {
      if (wealth(guess, t) <= 0) {
        let lo = t - .5, hi = t;
        for (let j = 0; j < 40; j++) { const mid = (lo + hi) / 2; if (wealth(guess, mid) > 0) lo = mid; else hi = mid; }
        exhaustion = (lo + hi) / 2; break;
      }
    }
  }
  const points = c => {
    const end = c === guess && exhaustion !== null ? exhaustion : horizon;
    return Array.from({ length: 241 }, (_, i) => { const t = i * end / 240; return { x: t, y: Math.max(0, wealth(c, t)) }; });
  };
  const optimalAssets = points(optimal), guessAssets = points(guess);
  const discounted = values => values.map(p => ({ x: p.x, y: Math.exp(-r * p.x) * p.y }));
  return { optimal, guess, exhaustion, optimalAssets, guessAssets, optimalDiscounted: discounted(optimalAssets), guessDiscounted: discounted(guessAssets), discountedLimit: initialAssets + wage / r - guess / (r - g) };
}

export const growthParameters = { alpha: 1 / 3, delta: .05, rho: .03, sigma: 2, A: 1 };
export const growthSteady = (() => {
  const { alpha, delta, rho, A } = growthParameters;
  const k = (alpha * A / (delta + rho)) ** (1 / (1 - alpha));
  return { k, c: A * k ** alpha - delta * k, golden: (alpha * A / delta) ** (1 / (1 - alpha)) };
})();
function growthDerivative(k, c) {
  const { alpha, delta, rho, sigma, A } = growthParameters;
  return [A * k ** alpha - c - delta * k, c * (alpha * A * k ** (alpha - 1) - delta - rho) / sigma];
}
export function shoot(c0, horizon = 400) {
  let k = .3 * growthSteady.k, c = c0, time = 0;
  const trajectory = [{ x: k, y: c, t: time }];
  let status = 'horizon';
  while (time < horizon) {
    const a = growthDerivative(k, c);
    const dt = Math.min(.04, .04 * k / (Math.abs(a[0]) + 1e-12), .04 * c / (Math.abs(a[1]) + 1e-12), horizon - time);
    if (dt < 1e-8 || k < 1e-7) { status = 'high'; break; }
    if (c < 1e-8 || k > 1.01 * growthSteady.golden) { status = 'low'; break; }
    const b = growthDerivative(k + dt * a[0] / 2, c + dt * a[1] / 2);
    const d = growthDerivative(k + dt * b[0] / 2, c + dt * b[1] / 2);
    const e = growthDerivative(k + dt * d[0], c + dt * d[1]);
    k += dt * (a[0] + 2 * b[0] + 2 * d[0] + e[0]) / 6;
    c += dt * (a[1] + 2 * b[1] + 2 * d[1] + e[1]) / 6;
    time += dt;
    if (time <= 120 && trajectory.length < 4000) trajectory.push({ x: k, y: c, t: time });
    if (!Number.isFinite(k + c) || k <= 0) { status = 'high'; break; }
    if (c <= 0) { status = 'low'; break; }
  }
  return { status, finalState: { k, c }, trajectory: trajectory.filter(p => Number.isFinite(p.x + p.y) && p.x > 0 && p.y > 0 && p.x < growthSteady.golden * 1.8 && p.y < growthSteady.c * 2), time };
}
export function bisectShooting(lo, hi) {
  const midpoint = (lo + hi) / 2, result = shoot(midpoint);
  const high = result.status === 'high' || (result.status === 'horizon' && result.finalState.c > growthSteady.c);
  return { lo: high ? lo : midpoint, hi: high ? midpoint : hi, midpoint, result };
}
export function stableConsumption() {
  let lo = .4, hi = 1.1;
  for (let i = 0; i < 43; i++) { const next = bisectShooting(lo, hi); lo = next.lo; hi = next.hi; }
  return (lo + hi) / 2;
}

export const bellmanGrid = [.25, .75, 1.25, 1.75, 2.25];
export function bellman(values = bellmanGrid.map(() => 0)) {
  const candidates = bellmanGrid.map(k => bellmanGrid.map((next, j) => {
    const consumption = k ** .3 + .9 * k - next;
    return consumption > 0 ? Math.log(consumption) + .9 * values[j] : -Infinity;
  }));
  const nextValues = candidates.map(row => Math.max(...row));
  const policy = candidates.map(row => row.indexOf(Math.max(...row)));
  return { candidates, nextValues, policy, gap: Math.max(...nextValues.map((v, i) => Math.abs(v - values[i]))) };
}
