<script>
  import LineChart from './LineChart.svelte';
  import { solow } from '../lib/models.js';
  let saving = .2, initial = 1, step = 1, mode = 'path';
  $: result = solow(Number(saving), Number(initial), Number(step));
  $: series = mode === 'path' ? [
    { id: 'exact', label: 'Exact path', points: result.exact, color: 'series-2', dash: true },
    { id: 'euler', label: 'Euler steps', points: result.euler, color: 'series-1' }
  ] : [
    { id: 'saving', label: 'Saving s·f(k)', points: result.investment, color: 'series-1' },
    { id: 'depreciation', label: 'Depreciation (δ+n)·k', points: result.depreciation, color: 'series-2', dash: true }
  ];
  $: direction = Math.abs(result.drift) < .001 ? 'is almost unchanged' : result.drift > 0 ? 'rises' : 'falls';
</script>
<section class="experiment" aria-label="Interactive Solow model">
  <p class="experiment-title">Experiment / Growth & convergence</p>
  <div class="controls">
    <label><span class="control-heading"><span>Saving rate, s</span><output>{(Number(saving) * 100).toFixed(0)}%</output></span><input aria-label="Saving rate" type="range" min=".1" max=".4" step=".01" bind:value={saving} /></label>
    <label><span class="control-heading"><span>Initial capital, k₀</span><output>{Number(initial).toFixed(1)}</output></span><input aria-label="Initial capital" type="range" min=".3" max="16" step=".1" bind:value={initial} /></label>
  </div>
  <div class="segmented" aria-label="Solow view"><button aria-pressed={mode === 'path'} on:click={() => mode = 'path'}>Capital over time</button><button aria-pressed={mode === 'diagram'} on:click={() => mode = 'diagram'}>Saving & depreciation</button></div>
  {#if mode === 'path'}<label class="step-control">Euler time step <select aria-label="Euler time step" bind:value={step}><option value={.1}>0.1 years</option><option value={1}>1 year</option><option value={5}>5 years</option></select></label>{/if}
  <LineChart {series} title={mode === 'path' ? 'Different starting points. One destination.' : 'Capital changes by the gap between the curves.'} xLabel={mode === 'path' ? 'Time (years)' : 'Capital per worker, k'} yLabel={mode === 'path' ? 'Capital per worker, k' : 'Flow per worker / year'} references={mode === 'path' ? [{ axis: 'y', value: result.steady, label: `Steady state k* = ${result.steady.toFixed(2)}` }] : [{ axis: 'x', value: result.steady, label: 'k*' }]} markers={mode === 'diagram' ? [{ x: Number(initial), y: Number(saving) * Number(initial) ** (1 / 3), label: 'At k₀' }] : []} description="Capital converges to a stable steady state where saving equals effective depreciation. Compare Euler steps with the exact solution, or inspect the saving and depreciation curves." />
  <p class="live-insight" aria-live="polite">At your starting point, capital <strong>{direction}</strong>. The steady state is <strong>{result.steady.toFixed(2)}</strong>; the initial change is <strong>{result.drift.toFixed(3)}</strong> units per worker per year.</p>
  <p class="chart-footnote">A = 1, α = ⅓, δ + n = 0.06. The exact solution is available for this calibration. Euler uses the current state to take each numerical step.</p>
</section>
<style>.step-control { display: flex; gap: 14px; align-items: center; font-size: .8125rem; margin-bottom: 18px; color: var(--muted); } .step-control select { width: auto; padding: 4px 10px; }</style>
