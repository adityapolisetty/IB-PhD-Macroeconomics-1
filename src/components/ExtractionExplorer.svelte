<script>
  import LineChart from './LineChart.svelte';
  import modelData from '../data/model-data.json';
  const data = modelData.extraction;
  let capacity = '0.5', price = '3';
  $: chosen = data.curves[capacity][price];
  $: baseline = data.curves['0.0'][price];
  $: series = [{ id: 'chosen', label: `Capacity cost κ = ${Number(capacity)}`, points: data.stock.map((x, i) => ({ x, y: chosen[i] })), color: 'series-1' }, ...(capacity === '0.0' ? [] : [{ id: 'baseline', label: 'No capacity cost', points: data.stock.map((x, i) => ({ x, y: baseline[i] })), color: 'series-2', dash: true }])];
</script>
<section class="experiment" aria-label="Resource extraction policy experiment">
  <p class="experiment-title">Experiment / Test the scaling argument</p>
  <div class="controls"><label>Capacity cost, κ<select aria-label="Capacity cost" bind:value={capacity}><option value="0.0">0 · no capacity cost</option><option value="0.1">0.1 · moderate</option><option value="0.5">0.5 · high</option></select></label><label>Current price, p<select aria-label="Current price" bind:value={price}>{#each [1, 3, 5] as j}<option value={String(j)}>{j === 1 ? 'Low' : j === 3 ? 'Median' : 'High'} · {data.prices[j].toFixed(2)}</option>{/each}</select></label></div>
  <LineChart {series} title="Same fraction at every scale?" xLabel="Remaining stock, S (log scale)" yLabel="Optimal extraction, q/S (%)" xType="log" description="Without capacity cost the extraction fraction is constant across stock levels. With quadratic capacity cost the optimal fraction declines as stock increases." />
  <p class="live-insight" aria-live="polite">{#if capacity === '0.0'}The optimal fraction is <strong>{baseline[0].toFixed(1)}%</strong> at every plotted stock. Doubling stock doubles extraction, leaving the fraction unchanged.{:else}The fraction falls from <strong>{chosen[0].toFixed(1)}%</strong> at the smallest plotted stock to <strong>{chosen.at(-1).toFixed(1)}%</strong> at the largest. Quadratic capacity cost breaks proportional scaling.{/if}</p>
  <p class="chart-footnote">β = 0.95, log-price persistence ρ = 0.8, innovation standard deviation 0.1. These are precomputed grid policies with V(0,p) = 0. Changing today's price also changes the distribution of expected future prices.</p>
</section>
