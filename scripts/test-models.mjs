import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { solow, household, shoot, bisectShooting, stableConsumption, growthSteady, bellman, bellmanGrid } from '../src/lib/models.js';
const near = (actual, expected, tolerance = 1e-10) => assert.ok(Math.abs(actual - expected) < tolerance, `${actual} differs from ${expected}`);
const cases = [];
function check(name, fn) { fn(); cases.push(name); }
check('Solow dynamics, steady state and Euler accuracy', () => {
  const base = solow(.2, 1), above = solow(.2, 16);
  near(base.exact[0].y, 1);
  assert.ok(base.drift > 0 && above.drift < 0);
  assert.ok(solow(.3).steady > base.steady);
  const error = dt => Math.abs(solow(.2, 1, dt).euler.at(-1).y - base.exact.at(-1).y);
  assert.ok(error(.1) < error(1) && error(1) < error(5));
  assert.ok(Math.abs(base.exact.at(-1).y - base.steady) < Math.abs(1 - base.steady));
});
check('Household budget, discounted limit and exhaustion event', () => {
  const optimal = household(), low = household(-.005), high = household(.005);
  near(optimal.optimal, .84);
  near(optimal.optimalAssets[0].y, 1);
  assert.ok(optimal.optimalAssets.at(-1).y > 1 && optimal.optimalDiscounted.at(-1).y < .002);
  near(low.discountedLimit, .105);
  assert.ok(Math.abs(low.guessDiscounted.at(-1).y - low.discountedLimit) < .002);
  assert.ok(high.exhaustion > 0 && high.exhaustion < 240);
  assert.ok(high.guessAssets.at(-1).y < 1e-6);
});
check('Shooting failures, bracket halving and stable trajectory', () => {
  assert.equal(shoot(.4).status, 'low');
  assert.equal(shoot(1.1).status, 'high');
  const step = bisectShooting(.4, 1.1);
  near(step.hi - step.lo, .35);
  const c0 = stableConsumption(), path = shoot(c0).trajectory;
  assert.ok(c0 > .94 && c0 < .95);
  assert.ok(Math.abs(path.at(-1).x - growthSteady.k) < .02);
  assert.ok(Math.abs(path.at(-1).y - growthSteady.c) < .003);
});
check('Bellman feasibility, maximisers and contraction', () => {
  const initial = bellman();
  assert.ok(initial.candidates[0].some(v => v === -Infinity));
  assert.ok(initial.policy.every(i => i === 0));
  let values = bellmanGrid.map(() => 0), gap = Infinity;
  for (let i = 0; i < 150; i++) {
    const next = bellman(values);
    assert.ok(next.gap <= .9 * gap + 1e-10);
    values = next.nextValues; gap = next.gap;
    assert.ok(values.every(Number.isFinite));
  }
  assert.ok(gap < 1e-6);
});
const data = JSON.parse(await readFile(new URL('../src/data/model-data.json', import.meta.url), 'utf8'));
check('Extraction homogeneity and capacity costs', () => {
  for (const price of ['1', '3', '5']) {
    const flat = data.extraction.curves['0.0'][price];
    assert.ok(Math.max(...flat) - Math.min(...flat) < 1e-5);
    const cost = data.extraction.curves['0.5'][price];
    assert.ok(cost[0] > cost.at(-1));
    assert.ok(cost.every(v => v >= 0 && v < 100));
  }
});
check('Investment thresholds, inaction and friction removal', () => {
  for (const resale of ['0.80', '0.95', '1.00']) {
    const low = data.investment.curves[`0.05:${resale}`].band;
    const high = data.investment.curves[`0.10:${resale}`].band;
    assert.ok(high[0] <= low[0] && high[1] >= low[1]);
    assert.ok(data.investment.curves[`0.05:${resale}`].rate.every(Number.isFinite));
  }
  assert.equal(data.investment.curves['0.00:1.00'].band, null);
});
check('RBC common start, finite paths and shock-size comparison', () => {
  let previous = -1;
  for (const shock of ['0.01', '0.05', '0.10', '0.20']) {
    const path = data.rbc.paths[shock];
    near(path.linear[0], 0); near(path.numerical[0], 0);
    assert.equal(path.linear.length, path.numerical.length);
    assert.ok(path.linear.every(Number.isFinite) && path.numerical.every(Number.isFinite));
    assert.ok(path.gap > previous); previous = path.gap;
    const gap = Math.max(...path.linear.map((v, i) => Math.abs(path.numerical[i] - v) / (100 + v) * 100));
    near(gap, path.gap, 2e-6);
  }
});
for (const name of cases) console.log(`PASS ${name}`);
console.log(`${cases.length} economic and numerical checks passed.`);
