// Utility normalisations fix a convenient vertical origin; AK measures output.
export function oneVariable(id, c, parameter = 2) {
  if (c < 0 || (id === 'log' && c === 0) || (id === 'crra' && c === 0 && parameter >= 1)) return null;
  switch (id) {
    case 'linear': return { value: c, marginal: 1, second: 0 };
    case 'log': return { value: Math.log(c), marginal: 1 / c, second: -1 / c ** 2 };
    case 'crra': {
      const sigma = parameter;
      if (Math.abs(sigma - 1) < 1e-9) return oneVariable('log', c);
      return { value: (c ** (1 - sigma) - 1) / (1 - sigma), marginal: c ** -sigma, second: -sigma * c ** (-sigma - 1) };
    }
    case 'cara': return { value: (1 - Math.exp(-parameter * c)) / parameter, marginal: Math.exp(-parameter * c), second: -parameter * Math.exp(-parameter * c) };
    case 'quadratic': return { value: c - parameter * c ** 2 / 2, marginal: 1 - parameter * c, second: -parameter };
    case 'ak': return { value: parameter * c, marginal: parameter, second: 0 };
    default: throw new Error(`Unknown function: ${id}`);
  }
}

export function oneVariableFacts(id, parameter = 2) {
  switch (id) {
    case 'linear': return { domain: 'c ≥ 0', minimum: 'u(0) = 0, attained', maximum: 'None; utility rises without bound', shape: 'Constant marginal utility; no diminishing returns.', use: 'A benchmark with perfect willingness to trade consumption across units.' };
    case 'log': return { domain: 'c > 0', minimum: 'None; u → −∞ as c → 0⁺', maximum: 'None; u → ∞ as c → ∞', shape: 'Increasing and strictly concave. The curve is steep near zero.', use: 'A standard consumption payoff in growth and dynamic programming.' };
    case 'crra': return parameter < 1
      ? { domain: 'c ≥ 0', minimum: `u(0) = ${(-1 / (1 - parameter)).toFixed(2)}, attained`, maximum: 'None; utility rises without bound', shape: 'Increasing and strictly concave for σ > 0.', use: 'The curvature parameter σ also governs consumption smoothing in macro models.' }
      : parameter === 1
        ? oneVariableFacts('log')
        : { domain: 'c > 0', minimum: 'None; u → −∞ as c → 0⁺', maximum: `No attained maximum; ceiling ${ (1 / (parameter - 1)).toFixed(2) } as c → ∞`, shape: 'Increasing and strictly concave for σ > 0.', use: 'The curvature parameter σ also governs consumption smoothing in macro models.' };
    case 'cara': return { domain: 'c ≥ 0', minimum: 'u(0) = 0, attained', maximum: `No attained maximum; ceiling ${(1 / parameter).toFixed(2)} as c → ∞`, shape: 'Increasing and strictly concave; slope falls exponentially.', use: 'A common risk preference example with constant absolute risk aversion.' };
    case 'quadratic': return { domain: 'c ≥ 0', minimum: 'None; utility falls without bound as c → ∞', maximum: `u = ${(1 / (2 * parameter)).toFixed(2)} at c = ${(1 / parameter).toFixed(2)}`, shape: 'Concave, but marginal utility turns negative beyond the bliss point.', use: 'A simple way to see a finite satiation point and an interior peak.' };
    case 'ak': return { domain: 'k ≥ 0', minimum: 'f(0) = 0, attained', maximum: 'None; output rises without bound', shape: 'A straight line with constant marginal product A. Raising A rotates the line upward.', use: 'With saving rate s, depreciation δ and population growth n, per-worker capital grows at sA − (δ + n).' };
    default: throw new Error(`Unknown function: ${id}`);
  }
}
