<script>
  import LineChart from './LineChart.svelte';
  import modelData from '../data/model-data.json';
  const data = modelData.rbc;
  let shock = '0.01';
  $: chosen = data.paths[shock];
  $: series = [{ id: 'numerical', label: 'Numerical policy', points: chosen.numerical.map((y, x) => ({ x, y })), color: 'series-1' }, { id: 'linear', label: 'Log-linear policy', points: chosen.linear.map((y, x) => ({ x, y })), color: 'series-2', dash: true }];
</script>
<section class="experiment" aria-label="RBC policy approximation experiment">
  <p class="experiment-title">Experiment / One shock, two decision rules</p>
  <div class="controls"><label>Initial shock to log productivity<select aria-label="Productivity shock" bind:value={shock}><option value="0.01">1% · small</option><option value="0.05">5%</option><option value="0.10">10%</option><option value="0.20">20% · large</option></select></label><div class="gap"><span>Maximum relative capital gap</span><strong>{chosen.gap.toFixed(3)}%</strong><small>Shock = {(Number(shock) / .007).toFixed(1)} innovation standard deviations</small></div></div>
  <LineChart {series} title="How far can the tangent rule take us?" xLabel="Time (periods)" yLabel="Capital deviation from steady state (%)" description="Numerical and log-linear RBC decision rules start at the same capital and face an identical decaying productivity shock. Their discrepancy increases with the size of the initial shock." />
  <p class="live-insight" aria-live="polite">{#if Number(shock) <= .01}For this small shock, the two paths are <strong>very close</strong>. A local approximation captures the main response.{:else}The larger shock exposes <strong>curvature in the decision rule</strong>. Both paths face the same productivity sequence, so different shocks cannot explain the gap.{/if}</p>
  <p class="chart-footnote">β = 0.99, α = 0.36, δ = 0.025, ρ = 0.95, σ = 0.007. One initial innovation; subsequent innovations are zero. The 20% log shock is a deliberate stress test. The gap is max |Kⁿᵘᵐ − Kˡⁱⁿ| / Kˡⁱⁿ, expressed as a percent.</p>
</section>
<style>.gap { display: grid; gap: 5px; font-size: .875rem; line-height: 1.5; } .gap strong { color: var(--accent); font: 1.7rem var(--font-heading); } .gap small { color: var(--muted); font-size: .8125rem; }</style>
