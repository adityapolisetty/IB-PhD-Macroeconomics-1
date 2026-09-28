<script>
  import LineChart from './LineChart.svelte';
  import { household } from '../lib/models.js';
  let deviation = -.5, mode = 'discounted';
  $: result = household(Number(deviation) / 100);
  $: series = [
    { id: 'optimal', label: 'Optimal consumption', points: mode === 'discounted' ? result.optimalDiscounted : result.optimalAssets, color: 'series-2', dash: true },
    { id: 'guess', label: 'Your consumption guess', points: mode === 'discounted' ? result.guessDiscounted : result.guessAssets, color: 'series-1' }
  ];
</script>
<section class="experiment" aria-label="Household consumption and wealth">
  <p class="experiment-title">Experiment / The terminal condition</p>
  <div class="controls">
    <label><span class="control-heading"><span>Initial consumption relative to optimum</span><output>{Number(deviation) > 0 ? '+' : ''}{Number(deviation).toFixed(2)}%</output></span><input aria-label="Consumption deviation" type="range" min="-1" max="1" step=".05" bind:value={deviation} /></label>
    <div class="choice-value"><span>Initial consumption, c₀</span><strong>{result.guess.toFixed(4)}</strong><small>Optimal c₀* = {result.optimal.toFixed(4)}</small></div>
  </div>
  <div class="segmented" aria-label="Wealth view"><button aria-pressed={mode === 'discounted'} on:click={() => mode = 'discounted'}>Discounted wealth</button><button aria-pressed={mode === 'levels'} on:click={() => mode = 'levels'}>Wealth in levels</button></div>
  <LineChart {series} title={mode === 'discounted' ? 'Does discounted wealth vanish?' : 'Growing wealth can still satisfy the terminal condition.'} xLabel="Time (years)" yLabel={mode === 'discounted' ? 'Discounted assets, e⁻ʳᵗa(t)' : 'Assets, a(t)'} description="Compare wealth under optimal consumption with a slightly higher or lower initial consumption guess. Discounted optimal wealth tends to zero although asset levels grow." />
  <p class="live-insight" aria-live="polite">
    {#if Number(deviation) < 0}Your guess leaves a positive limiting discounted balance of <strong>{result.discountedLimit.toFixed(3)}</strong>. The household could consume more.
    {:else if Number(deviation) > 0}Consumption is too high. {result.exhaustion === null ? 'Wealth exhaustion occurs beyond the plotted horizon.' : `Assets reach zero at year ${result.exhaustion.toFixed(1)}.`} The curve stops at this diagnostic boundary.
    {:else}Assets grow, yet <strong>discounted assets tend to zero</strong>. Compare both views without changing consumption.{/if}
  </p>
  <p class="chart-footnote">r = 0.05, consumption growth g = 0.01, wage w = 1, initial assets a₀ = 1. The zero-asset event diagnoses an overly high guess; zero assets alone are not the no-Ponzi condition.</p>
</section>
<style>.choice-value { display: grid; gap: 3px; font-size: .875rem; line-height: 1.5; } .choice-value strong { font-family: var(--font-heading); font-size: 1.7rem; font-weight: 400; color: var(--accent); line-height: 1.2; } .choice-value small { font-size: .8125rem; color: var(--muted); }</style>
