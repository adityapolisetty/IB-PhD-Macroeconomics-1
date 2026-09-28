<script>
  import LineChart from './LineChart.svelte';
  import modelData from '../data/model-data.json';
  const data = modelData.investment;
  let fixed = '.05', resale = '.95';
  $: chosen = data.curves[`${Number(fixed).toFixed(2)}:${Number(resale).toFixed(2)}`];
  $: baseline = data.curves[`0.00:${Number(resale).toFixed(2)}`];
  $: series = [{ id: 'chosen', label: `Fixed cost ${(Number(fixed) * 100).toFixed(0)}% of profit`, points: data.capital.map((x, i) => ({ x, y: chosen.rate[i] })), color: 'series-1' }, ...(Number(fixed) === 0 ? [] : [{ id: 'baseline', label: 'No fixed cost, same resale price', points: data.capital.map((x, i) => ({ x, y: baseline.rate[i] })), color: 'series-2', dash: true }])];
  $: bands = chosen.band ? [{ x0: chosen.band[0], x1: chosen.band[1], label: 'Inaction' }] : [];
</script>
<section class="experiment" aria-label="Investment adjustment policy experiment">
  <p class="experiment-title">Experiment / Buy, wait or sell</p>
  <div class="controls"><label>Fixed adjustment cost, f<select aria-label="Fixed adjustment cost" bind:value={fixed}><option value="0">0% of current profit</option><option value=".05">5% of current profit</option><option value=".1">10% of current profit</option></select></label><label>Resale price, pₛ<select aria-label="Resale price" bind:value={resale}><option value="1">1.00 · full resale value</option><option value=".95">0.95 · 5% loss</option><option value=".8">0.80 · 20% loss</option></select></label></div>
  <LineChart {series} {bands} title="Waiting can be the best decision." xLabel="Capital / user-cost benchmark (log scale)" xLabelShort="Capital / benchmark (log scale)" yLabel="Investment rate, i/k (%)" xType="log" references={[{ axis: 'y', value: 0, label: 'Zero investment' }]} description="Investment policy at median productivity. The shaded band is the set of capital states where the firm does not adjust. Larger fixed costs widen the band; lower resale prices discourage selling." />
  <p class="live-insight" aria-live="polite">{#if chosen.band}The plant waits for capital between <strong>{chosen.band[0].toFixed(2)}</strong> and <strong>{chosen.band[1].toFixed(2)}</strong> times the benchmark. Inside this band, investment is zero and capital still depreciates.{:else}The grid solution has <strong>no inaction band</strong>. Removing both frictions removes the discrete penalty for adjusting.{/if}</p>
  <p class="chart-footnote">Median productivity z = 1, β = 0.96, δ = 0.10, ν = 0.60. The benchmark solves νzkᵛ⁻¹ = r + δ. Thresholds are approximate grid locations; the fixed cost is paid whenever adjustment occurs, independent of its size.</p>
</section>
