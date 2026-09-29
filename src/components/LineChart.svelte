<script>
  import { onMount } from 'svelte';
  import { extent, scaleLinear, scaleLog, line, curveLinear, bisector } from 'd3';
  export let series = [];
  export let title = '';
  export let description = '';
  export let xLabel = '';
  export let xLabelShort = '';
  export let yLabel = '';
  export let xType = 'linear';
  export let references = [];
  export let bands = [];
  export let markers = [];
  export let includeZero = true;
  export let xDomain = undefined;
  export let yDomain = undefined;
  export let showLegend = true;
  export let interactive = true;
  let container, width = 720, hidden = [], hover = null, pinned = false;
  let previousYAxis = null, scaleChange = null;
  let height = 350;
  $: height = Math.max(350, Math.min(760, Math.round(width / 2.8)));
  $: margin = { top: 30, right: 18, bottom: 61, left: width < 440 ? 62 : 72 };
  $: allPoints = series.flatMap(s => s.points).filter(p => Number.isFinite(p.x + p.y));
  $: xs = [...allPoints.map(p => p.x), ...references.filter(r => r.axis === 'x').map(r => r.value)];
  $: ys = [...allPoints.map(p => p.y), ...references.filter(r => r.axis === 'y').map(r => r.value), ...(includeZero ? [0] : [])];
  $: xExtent = xDomain || extent(xs.length ? xs : [0, 1]);
  $: rawY = yDomain || extent(ys.length ? ys : [0, 1]);
  $: padding = Math.max((rawY[1] - rawY[0]) * .1, .02);
  $: xScale = (xType === 'log' ? scaleLog() : scaleLinear()).domain(xExtent[0] === xExtent[1] ? [xExtent[0], xExtent[0] + 1] : xExtent).range([margin.left, width - margin.right]);
  $: yScale = scaleLinear().domain(yDomain || [rawY[0] === 0 ? 0 : rawY[0] - padding, rawY[1] + padding]).nice(5).range([height - margin.bottom, margin.top]);
  $: trackYAxis(yScale.domain(), yLabel);
  $: xTicks = chartTicks(xScale, xType, width);
  $: yTicks = yScale.ticks(5);
  $: drawLine = line().x(p => xScale(p.x)).y(p => yScale(p.y)).curve(curveLinear);
  $: visibleSeries = series.filter(s => !hidden.includes(s.id));
  $: hoverRows = hover === null ? [] : visibleSeries.map(s => ({ ...s, value: interpolate(s.points, hover) })).filter(s => s.value !== null);
  $: hoverX = hover === null ? null : xScale(hover);
  $: clipId = `plot-${title.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`;
  $: if (series) { hover = null; pinned = false; }
  const formatter = v => Number.isInteger(v) ? String(v) : Math.abs(v) < .01 && v !== 0 ? v.toExponential(1) : Number(v.toFixed(2)).toString();
  function trackYAxis(domain, label) {
    const [min, max] = domain;
    if (previousYAxis && previousYAxis.label === label) {
      const oldSpan = previousYAxis.max - previousYAxis.min;
      const newSpan = max - min;
      const tolerance = Math.max(Math.abs(oldSpan), Math.abs(newSpan), 1) * 1e-9;
      if (newSpan > oldSpan + tolerance) scaleChange = 'expanded';
      else if (newSpan < oldSpan - tolerance) scaleChange = 'narrowed';
      else if (min > previousYAxis.min + tolerance) scaleChange = 'up';
      else if (min < previousYAxis.min - tolerance) scaleChange = 'down';
      else scaleChange = null;
    } else {
      scaleChange = null;
    }
    previousYAxis = { min, max, label };
  }
  function chartTicks(scale, type, availableWidth) {
    const limit = availableWidth < 440 ? 4 : 7;
    let ticks = type === 'log' ? scale.ticks(5).filter(v => [1, 2, 5].includes(Number((v / 10 ** Math.floor(Math.log10(v))).toFixed(8)))) : scale.ticks(availableWidth < 440 ? 3 : 6);
    while (ticks.length > limit) ticks = ticks.filter((_, i) => i % 2 === 0);
    return ticks;
  }
  function interpolate(points, x) {
    if (!points.length || x < points[0].x || x > points.at(-1).x) return null;
    const j = bisector(p => p.x).left(points, x);
    if (j === 0) return points[0].y;
    if (j >= points.length) return points.at(-1).y;
    const a = points[j - 1], b = points[j];
    return a.y + (b.y - a.y) * (x - a.x) / (b.x - a.x || 1);
  }
  function pointer(event) {
    if (pinned && event.type === 'pointermove') return;
    const bounds = event.currentTarget.ownerSVGElement.getBoundingClientRect();
    const x = (event.clientX - bounds.left) * width / bounds.width;
    hover = xScale.invert(Math.max(margin.left, Math.min(width - margin.right, x)));
  }
  function keyboard(event) {
    if (!interactive) return;
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End', 'Escape'].includes(event.key)) return;
    event.preventDefault();
    if (event.key === 'Escape') { hover = null; pinned = false; return; }
    const current = hover === null ? margin.left : xScale(hover);
    const next = event.key === 'Home' ? margin.left : event.key === 'End' ? width - margin.right : current + (event.key === 'ArrowRight' ? 1 : -1) * (width - margin.left - margin.right) / 40;
    hover = xScale.invert(Math.max(margin.left, Math.min(width - margin.right, next)));
  }
  function toggle(id) { hidden = hidden.includes(id) ? hidden.filter(x => x !== id) : [...hidden, id]; }
  onMount(() => {
    const observer = new ResizeObserver(entries => { width = Math.max(240, Math.round(entries[0].contentRect.width)); });
    observer.observe(container);
    return () => observer.disconnect();
  });
</script>

<figure class="line-chart" bind:this={container} aria-label={title}>
  <figcaption>{title}</figcaption>
  {#if showLegend}<div class="legend" aria-label="Chart series">{#each series as s}<button type="button" aria-pressed={!hidden.includes(s.id)} on:click={() => toggle(s.id)}><span class:dash={s.dash} style={`--series-color: var(--${s.color || 'series-1'})`}></span>{s.label}</button>{/each}</div>{/if}
  {#if scaleChange}
    <div class="scale-cue" role="status" aria-live="polite">
      <svg class="scale-cue-icon" viewBox="0 0 24 28" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        {#if scaleChange === 'expanded'}
          <path d="M12 12V3m-4 4 4-4 4 4M12 16v9m-4-4 4 4 4-4" />
        {:else if scaleChange === 'narrowed'}
          <path d="M12 3v9m-4-4 4 4 4-4M12 25v-9m-4 4 4-4 4 4" />
        {:else if scaleChange === 'up'}
          <path d="M12 24V4m-5 5 5-5 5 5" />
        {:else}
          <path d="M12 4v20m-5-5 5 5 5-5" />
        {/if}
      </svg>
      <span>Y-axis {scaleChange === 'expanded' ? 'range expanded' : scaleChange === 'narrowed' ? 'range narrowed' : scaleChange === 'up' ? 'shifted up' : 'shifted down'}</span>
    </div>
  {/if}
  <div class="chart-interaction" tabindex={interactive ? 0 : undefined} role="group" aria-label={`${title}.${interactive ? ' Use left and right arrows to inspect values. Escape clears the selection.' : ''}`} on:keydown={keyboard}>
    <svg viewBox={`0 0 ${width} ${height}`} width="100%" height={height} role="img" aria-label={title}>
      <title>{title}</title><desc>{description || `${yLabel} against ${xLabel}.`}</desc>
      <defs><clipPath id={clipId}><rect x={margin.left} y={margin.top} width={width - margin.left - margin.right} height={height - margin.top - margin.bottom} /></clipPath></defs>
      {#each bands as band}<rect class="region" x={xScale(band.x0)} y={margin.top} width={Math.max(0, xScale(band.x1) - xScale(band.x0))} height={height - margin.bottom - margin.top} /><text class="region-label" x={(xScale(band.x0) + xScale(band.x1)) / 2} y={margin.top + 16} text-anchor="middle">{band.label}</text>{/each}
      {#each yTicks as tick}<line class="grid" x1={margin.left} x2={width - margin.right} y1={yScale(tick)} y2={yScale(tick)} /><text class="tick" x={margin.left - 12} y={yScale(tick) + 4} text-anchor="end">{formatter(tick)}</text>{/each}
      <line class="axis" x1={margin.left} x2={width - margin.right} y1={height - margin.bottom} y2={height - margin.bottom} />
      {#each xTicks as tick}<line class="axis" x1={xScale(tick)} x2={xScale(tick)} y1={height - margin.bottom} y2={height - margin.bottom + 5} /><text class="tick" x={xScale(tick)} y={height - margin.bottom + 23} text-anchor={xScale(tick) > width - 35 ? 'end' : xScale(tick) < margin.left + 10 ? 'start' : 'middle'}>{formatter(tick)}</text>{/each}
      <text class="axis-title" x={(margin.left + width - margin.right) / 2} y={height - 9} text-anchor="middle">{width < 440 && xLabelShort ? xLabelShort : xLabel}</text>
      <text class="axis-title" transform={`translate(16 ${(margin.top + height - margin.bottom) / 2}) rotate(-90)`} text-anchor="middle">{yLabel}</text>
      {#each references as r}
        {#if r.axis === 'y'}<line class="reference" x1={margin.left} x2={width - margin.right} y1={yScale(r.value)} y2={yScale(r.value)} /><text class="reference-label" x={width - margin.right - 5} y={yScale(r.value) - 8} text-anchor="end">{r.label}</text>
        {:else}<line class="reference" x1={xScale(r.value)} x2={xScale(r.value)} y1={margin.top} y2={height - margin.bottom} /><text class="reference-label" x={xScale(r.value) + 6} y={margin.top + 15}>{r.label}</text>{/if}
      {/each}
      <g clip-path={`url(#${clipId})`}>{#each visibleSeries as s}<path class="data-line" d={drawLine(s.points)} fill="none" stroke={`var(--${s.color || 'series-1'})`} stroke-width={s.width || 2.5} stroke-dasharray={s.dash ? '6 5' : undefined} />{/each}</g>
      {#each markers as m}<circle cx={xScale(m.x)} cy={yScale(m.y)} r="4.5" fill={`var(--${m.color || 'series-1'})`} stroke="var(--paper)" stroke-width="2" />{#if m.label}<text class="reference-label" x={xScale(m.x) + 9} y={yScale(m.y) - 9}>{m.label}</text>{/if}{/each}
      {#if hover !== null}<line class="hover-guide" x1={hoverX} x2={hoverX} y1={margin.top} y2={height - margin.bottom} />{#each hoverRows as row}<circle cx={hoverX} cy={yScale(row.value)} r="4.5" fill={`var(--${row.color || 'series-1'})`} stroke="var(--paper)" stroke-width="2" />{/each}{/if}
      {#if interactive}<rect class="pointer-area" x={margin.left} y={margin.top} width={width - margin.left - margin.right} height={height - margin.top - margin.bottom} fill="transparent" aria-hidden="true" on:pointermove={pointer} on:pointerleave={() => { if (!pinned) hover = null; }} on:pointerdown={event => { pointer(event); pinned = !pinned; }} />{/if}
    </svg>
    {#if hover !== null}<div class="chart-tooltip" role="status" style={`left: ${Math.max(margin.left, Math.min(width - 225, hoverX + 12))}px`}><div class="tooltip-x">{xLabel}: {formatter(hover)}</div>{#each hoverRows as row}<div><span>{row.label}</span><strong>{formatter(row.value)}</strong></div>{/each}</div>{/if}
  </div>
</figure>

<style>
  figure { margin: 0; width: 100%; }
  figcaption { font-family: var(--font-heading); font-size: 1.35rem; line-height: 1.4; margin-bottom: 10px; }
  .legend { display: flex; gap: 10px 23px; flex-wrap: wrap; margin-bottom: 7px; }
  .legend button { background: var(--accent); border: 1px solid var(--accent); padding: 4px 9px; font-size: .8125rem; display: inline-flex; align-items: center; gap: 8px; color: var(--paper); }
  .legend button[aria-pressed='false'] { opacity: 1; text-decoration: line-through; }
  .legend button:focus-visible { outline: 2px solid var(--paper); outline-offset: -4px; }
  .legend span { width: 20px; height: 5px; background: var(--paper); border-top: 2px solid var(--series-color); }
  .legend .dash { border-top-style: dashed; }
  .scale-cue { display: inline-flex; align-items: center; gap: 10px; max-width: 100%; margin: 5px 0 8px; padding: 5px 14px 5px 8px; border-left: 3px solid var(--accent); background: var(--accent-soft-strong); color: var(--accent); font-size: .9375rem; font-weight: 600; line-height: 1.35; }
  .scale-cue-icon { width: 29px; height: 34px; flex: none; }
  .chart-interaction { position: relative; }
  svg { display: block; overflow: visible; }
  .tick { font: 13px var(--font-body); fill: var(--muted); font-variant-numeric: tabular-nums; }
  .axis-title { font: 14px var(--font-body); fill: var(--ink); }
  .grid { stroke: var(--rule); stroke-width: .65; }
  .axis { stroke: var(--muted); stroke-width: .8; }
  .reference { stroke: var(--muted); stroke-width: 1; stroke-dasharray: 3 5; opacity: .6; }
  .reference-label, .region-label { font: 13px var(--font-body); fill: var(--muted); paint-order: stroke; stroke: var(--paper); stroke-width: 4px; }
  .region { fill: var(--accent-soft); opacity: .7; }
  .data-line { transition: d .22s ease; }
  .hover-guide { stroke: var(--muted); stroke-width: 1; opacity: .5; }
  .pointer-area { cursor: crosshair; touch-action: pan-y; }
  .chart-tooltip { position: absolute; top: 28px; width: 215px; background: var(--accent-soft); border: 1px solid var(--accent); padding: 10px 13px; font-size: .8125rem; line-height: 1.7; pointer-events: none; box-shadow: 0 4px 14px #2628240a; }
  .chart-tooltip > div { display: flex; gap: 10px; justify-content: space-between; }
  .chart-tooltip .tooltip-x { color: var(--muted); padding-bottom: 3px; }
  .chart-tooltip strong { font-weight: 500; font-variant-numeric: tabular-nums; }
  @media (prefers-reduced-motion: reduce) { .data-line { transition: none; } }
</style>
