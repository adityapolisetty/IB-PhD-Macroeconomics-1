import assert from 'node:assert/strict';
import { oneGood, twoGood, marginalRateOfSubstitution, indifferenceY } from '../src/lib/utility.js';

const close = (a, b, tolerance = 1e-4) => assert.ok(Math.abs(a - b) < tolerance, `${a} ≠ ${b}`);
const h = 1e-5;
for (const [id, parameter] of [['linear', 1], ['log', 1], ['crra', 0.5], ['crra', 1], ['crra', 2], ['cara', 0.6], ['quadratic', 0.35]]) {
  for (const c of [0.8, 2.5, 6]) {
    const value = oneGood(id, c, parameter);
    close(value.marginal, (oneGood(id, c + h, parameter).value - oneGood(id, c - h, parameter).value) / (2 * h));
    close(value.second, (oneGood(id, c + h, parameter).marginal - oneGood(id, c - h, parameter).marginal) / (2 * h));
  }
}
close(oneGood('quadratic', 1 / 0.35, 0.35).marginal, 0);
assert.equal(oneGood('log', 0), null);
assert.equal(oneGood('crra', 0, 2), null);
for (const [id, alpha, elasticity] of [['substitutes', 0.6, 1], ['cobb', 0.55, 1], ['ces', 0.5, 2.5], ['ces', 0.5, 0.5]]) {
  const x = 2.2, y = 3.1;
  const ux = (twoGood(id, x + h, y, alpha, elasticity) - twoGood(id, x - h, y, alpha, elasticity)) / (2 * h);
  const uy = (twoGood(id, x, y + h, alpha, elasticity) - twoGood(id, x, y - h, alpha, elasticity)) / (2 * h);
  close(marginalRateOfSubstitution(id, x, y, alpha, elasticity), ux / uy);
  close(indifferenceY(id, x, twoGood(id, x, y, alpha, elasticity), alpha, elasticity), y);
}
assert.equal(marginalRateOfSubstitution('complements', 3, 3), null);
assert.equal(marginalRateOfSubstitution('complements', 2, 3), Infinity);
assert.equal(marginalRateOfSubstitution('complements', 4, 3), 0);
console.log('Utility values, derivatives, substitution rates and contour inverses pass.');
