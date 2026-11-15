export const vfiParameters = {
  A: 1,
  beta: .9,
  delta: .1,
  alpha: .3,
};

export function makeVfi({ A = 1, beta = .9, delta = .1, alpha = .3, N = 25, maxIteration = 120 } = {}) {
  const steady = (alpha * A / (1 / beta - (1 - delta))) ** (1 / (1 - alpha));
  const grid = Array.from({ length: N }, (_, i) => .001 + i * (2 * steady - .001) / (N - 1));
  const consumption = grid.map(k => grid.map(next => A * k ** alpha + (1 - delta) * k - next));
  const flow = consumption.map(row => row.map(c => c > 0 ? Math.log(c) : -Infinity));
  const values = [grid.map(() => 0)];
  const matrices = [];
  const policies = [];
  const gaps = [];

  for (let n = 0; n <= maxIteration; n++) {
    const matrix = flow.map(row => row.map((u, j) => Number.isFinite(u) ? u + beta * values[n][j] : -Infinity));
    const next = [];
    const policy = [];
    let gap = 0;
    for (let i = 0; i < N; i++) {
      let best = -Infinity, bestIndex = 0;
      for (let j = 0; j < N; j++) {
        if (matrix[i][j] > best) { best = matrix[i][j]; bestIndex = j; }
      }
      next.push(best);
      policy.push(bestIndex);
      gap = Math.max(gap, Math.abs(best - values[n][i]));
    }
    matrices.push(matrix);
    policies.push(policy);
    gaps.push(gap);
    values.push(next);
  }

  const finiteMatrixValues = matrices.flat(2).filter(Number.isFinite);
  const finiteValues = values.flat().filter(Number.isFinite);
  return {
    parameters: { A, beta, delta, alpha },
    N,
    maxIteration,
    steady,
    grid,
    consumption,
    flow,
    values,
    matrices,
    policies,
    gaps,
    matrixRange: [Math.min(...finiteMatrixValues), Math.max(...finiteMatrixValues)],
    valueRange: [Math.min(...finiteValues), Math.max(...finiteValues)],
  };
}
