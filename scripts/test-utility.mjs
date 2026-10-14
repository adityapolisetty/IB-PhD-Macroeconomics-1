import assert from 'node:assert/strict';
import { oneVariable, oneVariableFacts } from '../src/lib/utility.js';

const close = (a, b, tolerance = 1e-4) => assert.ok(Math.abs(a - b) < tolerance, `${a} ≠ ${b}`);
const h = 1e-5;
for (const [id, parameter] of [['linear', 1], ['log', 1], ['crra', 0.5], ['crra', 1], ['crra', 2], ['cara', 0.6], ['quadratic', 0.35], ['ak', 0.5], ['ak', 2]]) {
  for (const c of [0.8, 2.5, 6]) {
    const value = oneVariable(id, c, parameter);
    close(value.marginal, (oneVariable(id, c + h, parameter).value - oneVariable(id, c - h, parameter).value) / (2 * h));
    close(value.second, (oneVariable(id, c + h, parameter).marginal - oneVariable(id, c - h, parameter).marginal) / (2 * h));
  }
}
close(oneVariable('quadratic', 1 / 0.35, 0.35).marginal, 0);
assert.equal(oneVariable('log', 0), null);
assert.equal(oneVariable('crra', 0, 2), null);
close(oneVariable('ak', 3, 1.5).value, 4.5);
close(oneVariable('ak', 3, 1.5).marginal, 1.5);
assert.match(oneVariableFacts('ak', 1.5).maximum, /without bound/);
close(0.2 * 1.25 - (0.2 + 0.05), 0);
console.log('Utility and AK values, derivatives and extrema pass.');
