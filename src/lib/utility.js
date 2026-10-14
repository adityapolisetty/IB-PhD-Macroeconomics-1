// Normalisations fix a convenient vertical origin; they do not change marginal utility.
export function oneGood(id, c, parameter = 2) {
  if (c < 0 || (id === 'log' && c === 0) || (id === 'crra' && c === 0 && parameter >= 1)) return null;
  switch (id) {
    case 'linear': return { value: c, marginal: 1, second: 0 };
    case 'log': return { value: Math.log(c), marginal: 1 / c, second: -1 / c ** 2 };
    case 'crra': {
      const sigma = parameter;
      if (Math.abs(sigma - 1) < 1e-9) return oneGood('log', c);
      return { value: (c ** (1 - sigma) - 1) / (1 - sigma), marginal: c ** -sigma, second: -sigma * c ** (-sigma - 1) };
    }
    case 'cara': return { value: (1 - Math.exp(-parameter * c)) / parameter, marginal: Math.exp(-parameter * c), second: -parameter * Math.exp(-parameter * c) };
    case 'quadratic': return { value: c - parameter * c ** 2 / 2, marginal: 1 - parameter * c, second: -parameter };
    default: throw new Error(`Unknown utility function: ${id}`);
  }
}

export function oneGoodFacts(id, parameter = 2) {
  switch (id) {
    case 'linear': return { domain: 'c ≥ 0', minimum: 'u(0) = 0, attained', maximum: 'None; utility rises without bound', shape: 'Constant marginal utility; no diminishing returns.', use: 'A benchmark with perfect willingness to trade consumption across units.' };
    case 'log': return { domain: 'c > 0', minimum: 'None; u → −∞ as c → 0⁺', maximum: 'None; u → ∞ as c → ∞', shape: 'Increasing and strictly concave. The curve is steep near zero.', use: 'A standard consumption payoff in growth and dynamic programming.' };
    case 'crra': return parameter < 1
      ? { domain: 'c ≥ 0', minimum: `u(0) = ${(-1 / (1 - parameter)).toFixed(2)}, attained`, maximum: 'None; utility rises without bound', shape: 'Increasing and strictly concave for σ > 0.', use: 'The curvature parameter σ also governs consumption smoothing in macro models.' }
      : parameter === 1
        ? oneGoodFacts('log')
        : { domain: 'c > 0', minimum: 'None; u → −∞ as c → 0⁺', maximum: `No attained maximum; ceiling ${ (1 / (parameter - 1)).toFixed(2) } as c → ∞`, shape: 'Increasing and strictly concave for σ > 0.', use: 'The curvature parameter σ also governs consumption smoothing in macro models.' };
    case 'cara': return { domain: 'c ≥ 0', minimum: 'u(0) = 0, attained', maximum: `No attained maximum; ceiling ${(1 / parameter).toFixed(2)} as c → ∞`, shape: 'Increasing and strictly concave; slope falls exponentially.', use: 'A common risk preference example with constant absolute risk aversion.' };
    case 'quadratic': return { domain: 'c ≥ 0', minimum: 'None; utility falls without bound as c → ∞', maximum: `u = ${(1 / (2 * parameter)).toFixed(2)} at c = ${(1 / parameter).toFixed(2)}`, shape: 'Concave, but marginal utility turns negative beyond the bliss point.', use: 'A simple way to see a finite satiation point and an interior peak.' };
    default: throw new Error(`Unknown utility function: ${id}`);
  }
}

export function twoGood(id, x, y, alpha = 0.5, elasticity = 2) {
  if (x < 0 || y < 0) return NaN;
  switch (id) {
    case 'substitutes': return alpha * x + (1 - alpha) * y;
    case 'cobb': return x ** alpha * y ** (1 - alpha);
    case 'complements': return Math.min(x, y);
    case 'ces': {
      if (x === 0 || y === 0) return elasticity < 1 ? 0 : (alpha * x ** (1 - 1 / elasticity) + (1 - alpha) * y ** (1 - 1 / elasticity)) ** (1 / (1 - 1 / elasticity));
      if (elasticity === 1) return twoGood('cobb', x, y, alpha);
      const rho = 1 - 1 / elasticity;
      return (alpha * x ** rho + (1 - alpha) * y ** rho) ** (1 / rho);
    }
    default: throw new Error(`Unknown two-good utility function: ${id}`);
  }
}

export function marginalRateOfSubstitution(id, x, y, alpha = 0.5, elasticity = 2) {
  switch (id) {
    case 'substitutes': return alpha / (1 - alpha);
    case 'cobb': return alpha * y / ((1 - alpha) * x);
    case 'complements': return x < y ? Infinity : x > y ? 0 : null; // Vertical arm, horizontal arm, kink.
    case 'ces': return (alpha / (1 - alpha)) * (x / y) ** (-1 / elasticity);
    default: throw new Error(`Unknown two-good utility function: ${id}`);
  }
}

export function indifferenceY(id, x, level, alpha = 0.5, elasticity = 2) {
  if (x < 0 || level <= 0) return NaN;
  switch (id) {
    case 'substitutes': return (level - alpha * x) / (1 - alpha);
    case 'cobb': return x > 0 ? (level / x ** alpha) ** (1 / (1 - alpha)) : NaN;
    case 'ces': {
      if (elasticity === 1) return indifferenceY('cobb', x, level, alpha);
      const rho = 1 - 1 / elasticity;
      const inner = (level ** rho - alpha * x ** rho) / (1 - alpha);
      return inner > 0 ? inner ** (1 / rho) : NaN;
    }
    default: return NaN;
  }
}
