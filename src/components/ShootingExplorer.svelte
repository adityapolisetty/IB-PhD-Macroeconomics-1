<script>
  import LineChart from './LineChart.svelte';
  import { shoot, bisectShooting, stableConsumption, growthSteady } from '../lib/models.js';
  let consumption = .75, lo = .4, hi = 1.1, iterations = 0, stable = null;
  $: result = shoot(Number(consumption));
  $: close = result.status === 'horizon' || (stable !== null && Math.abs(Number(consumption) - stable) < 1e-12);
  const endK = growthSteady.golden * 1.5;
  const nullcline = Array.from({ length: 241 }, (_, i) => { const k = endK * i / 240; return { x: k, y: k ** (1 / 3) - .05 * k }; });
  $: series = [{ id: 'nullcline', label: 'Capital unchanged: k̇ = 0', points: nullcline, color: 'series-2', dash: true }, { id: 'path', label: 'Path from your guess', points: result.trajectory, color: 'series-1' }];
  function bisect() { const next = bisectShooting(lo, hi); consumption = next.midpoint; lo = next.lo; hi = next.hi; iterations += 1; }
  function useStable() { stable = stable ?? stableConsumption(); consumption = stable; }
  function reset() { consumption = .75; lo = .4; hi = 1.1; iterations = 0; stable = null; }
</script>
<section class="experiment" aria-label="Saddle path shooting experiment">
  <p class="experiment-title">Experiment / One guess at a time</p>
  <div class="controls">
    <label><span class="control-heading"><span>Initial consumption, c₀</span><output>{Number(consumption).toFixed(6)}</output></span><input aria-label="Initial consumption" type="range" min=".4" max="1.1" step=".0001" bind:value={consumption} /></label>
    <div class="bracket"><span>Current bisection bracket</span><strong>[{lo.toFixed(6)}, {hi.toFixed(6)}]</strong><small>{iterations} bracket updates · k₀ = {(growthSteady.k * .3).toFixed(3)}</small></div>
  </div>
  <div class="button-row"><button class="button primary" on:click={bisect}>Bisect the bracket</button><button class="button" on:click={useStable}>Use the stable guess</button><button class="button" on:click={reset}>Reset</button></div>
  <LineChart {series} title="A narrow boundary between two failed paths." xLabel="Capital, k" yLabel="Consumption, c" xDomain={[0, endK]} yDomain={[0, growthSteady.c * 1.65]} references={[{ axis: 'x', value: growthSteady.k, label: 'ċ = 0' }]} markers={[{ x: .3 * growthSteady.k, y: Number(consumption), label: 'Start' }, { x: growthSteady.k, y: growthSteady.c, label: 'Steady state', color: 'series-2' }]} interactive={false} description="Phase diagram with a capital nullcline, a vertical consumption nullcline and the trajectory from the selected initial consumption. The stable guess approaches the steady state." />
  <p class="live-insight" aria-live="polite">{#if close}This guess follows the <strong>stable path toward the steady state</strong> over the displayed interval.{:else if result.status === 'high'}The guess is <strong>too high</strong>: consumption drains capital. Keep the lower half when this is the midpoint test.{:else}The guess is <strong>too low</strong>: capital overaccumulates and consumption eventually vanishes. Keep the upper half when this is the midpoint test.{/if}</p>
  <p class="chart-footnote">α = ⅓, δ = 0.05, ρ = 0.03, σ = 2, A = 1. The phase diagram shows at most 120 years; the failure test uses up to 400. Numerical error eventually pushes a saddle trajectory away from its stable path.</p>
</section>
<style>.bracket { display: grid; gap: 5px; font-size: .875rem; line-height: 1.5; } .bracket strong { font-size: 1rem; font-weight: 500; color: var(--accent); font-variant-numeric: tabular-nums; } .bracket small { color: var(--muted); font-size: .8125rem; }</style>
