<script>
  import { bellman, bellmanGrid as grid } from '../lib/models.js';
  let values = grid.map(() => 0), iteration = 0, row = 2;
  $: update = bellman(values);
  $: winner = update.policy[row];
  $: consumption = grid[row] ** .3 + .9 * grid[row] - grid[winner];
  function step() { values = update.nextValues; iteration += 1; }
  function reset() { values = grid.map(() => 0); iteration = 0; }
</script>
<section class="experiment" aria-label="Bellman update matrix">
  <p class="experiment-title">Experiment / A Bellman update you can read</p>
  <div class="controls"><label>Inspect a current capital state<select aria-label="Current capital state" bind:value={row}>{#each grid as k, i}<option value={i}>k = {k.toFixed(2)}</option>{/each}</select></label><div class="iteration"><span>Current value function</span><strong>V{iteration === 0 ? '₀' : ` (${iteration})`}</strong><small>Next update changes V by at most {update.gap.toFixed(4)}</small></div></div>
  <div class="button-row"><button class="button primary" on:click={step}>Apply this Bellman update</button><button class="button" on:click={reset}>Start from V₀ = 0</button></div>
  <p class="matrix-heading">Candidate values for update {iteration + 1}</p>
  <div class="matrix-scroll"><table class="payoff-matrix"><caption>Rows: current k. Columns: candidate next k′. Outlined cells maximise each row.</caption><thead><tr><th scope="col">k ↓ / k′ →</th>{#each grid as k}<th scope="col">{k.toFixed(2)}</th>{/each}</tr></thead><tbody>{#each update.candidates as candidates, i}<tr class:active={i === Number(row)}><th scope="row">{grid[i].toFixed(2)}</th>{#each candidates as value, j}<td class:best={j === update.policy[i]} class:infeasible={!Number.isFinite(value)} title={Number.isFinite(value) ? `Current utility ${(Math.log(grid[i] ** .3 + .9 * grid[i] - grid[j])).toFixed(3)} plus continuation value ${(.9 * values[j]).toFixed(3)}${j === update.policy[i] ? '. Best choice in this row.' : ''}` : 'Infeasible: consumption is zero or negative'}>{Number.isFinite(value) ? value.toFixed(2) : '×'}{#if j === update.policy[i]}<span class="sr-only">, row maximum</span>{/if}</td>{/each}</tr>{/each}</tbody></table></div>
  <p class="live-insight" aria-live="polite">At k = <strong>{grid[row].toFixed(2)}</strong>, the next update chooses k′ = <strong>{grid[winner].toFixed(2)}</strong>: current utility <strong>{Math.log(consumption).toFixed(3)}</strong> + continuation value <strong>{(.9 * values[winner]).toFixed(3)}</strong> = <strong>{update.nextValues[row].toFixed(3)}</strong>.</p>
  <p class="chart-footnote">β = 0.9, α = 0.3, δ = 0.1, A = 1. Five capital nodes make the calculation visible. The notebook uses a finer grid to solve the model accurately.</p>
</section>
<style>
  .iteration { display: grid; font-size: .875rem; gap: 5px; line-height: 1.5; } .iteration strong { font: 1.7rem var(--font-heading); color: var(--accent); } .iteration small { color: var(--muted); font-size: .8125rem; }
  .matrix-heading { font: 1.35rem var(--font-heading); margin: 8px 0 12px; }
  .matrix-scroll { overflow-x: auto; }
  .payoff-matrix { width: 100%; border-collapse: separate; border-spacing: 5px; margin: 0; font-size: .875rem; font-variant-numeric: tabular-nums; table-layout: fixed; min-width: 310px; }
  .payoff-matrix caption { text-align: left; font: .8125rem/1.6 var(--font-body); color: var(--muted); margin-bottom: 12px; }
  .payoff-matrix td, .payoff-matrix th { padding: 12px 4px; text-align: center; border: 1px solid transparent; }
  .payoff-matrix td { background: var(--surface); }
  .payoff-matrix th { font-weight: 500; color: var(--muted); }
  .payoff-matrix td.best { border-color: var(--accent); }
  .payoff-matrix .active td { background: var(--accent-soft-strong); }
  .payoff-matrix .active th { color: var(--accent); }
  .payoff-matrix td.infeasible { background: transparent; color: var(--muted); }
  .sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap; border: 0; }
</style>
