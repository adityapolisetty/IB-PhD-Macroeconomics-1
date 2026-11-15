<script>
  import { onMount } from 'svelte';
  import { ticks } from 'd3';
  import { renderToString } from 'katex';
  import { makeVfi } from '../lib/vfi.js';

  const W = 1040, H = 560;
  const matrixPlot = { left: 58, top: 62, size: 405 };
  const valuePlot = { left: 575, top: 62, width: 410, height: 405 };
  const model = makeVfi({ N: 150, maxIteration: 120 });
  const { grid, values, matrices, gaps, N, maxIteration, steady } = model;
  const cell = matrixPlot.size / N;
  const kMin = grid[0], kMax = grid.at(-1);
  const valueMin = Math.floor(model.valueRange[0] / 5) * 5;
  const valueMax = Math.ceil(model.valueRange[1] / 5) * 5;
  const kTicks = [0, steady, 2 * steady];
  const valueTicks = ticks(valueMin, valueMax, 5);
  const steadyRow = grid.reduce((best, k, i) => Math.abs(k - steady) < Math.abs(grid[best] - steady) ? i : best, 0);

  const texBeta = renderToString(String.raw`\beta`);
  const texAlpha = renderToString(String.raw`\alpha`);
  const texDelta = renderToString(String.raw`\delta`);
  const texK = renderToString('k');
  const texKp = renderToString(String.raw`k'`);
  const texCurrent = renderToString(String.raw`\log c_{ij}`);
  const texContinuation = renderToString(String.raw`\beta V_n(k'_j)`);
  const texCandidate = renderToString(String.raw`M_n(i,j)`);
  const fmt = (x, digits = 3) => Number.isFinite(x) ? x.toFixed(digits) : 'infeasible';

  let shown = 0;
  let sliderValue = 0;
  let playing = false;
  let speed = 4;
  let lastFrame = 0;
  let animationId;
  let chart;
  let matrixCanvas;
  let matrixImage;
  let hover = null;

  const interpolateVector = (a, b, w) => a.map((v, i) => v + w * (b[i] - v));
  const interpolateMatrix = (a, b, w) => a.map((row, i) => row.map((v, j) => {
    if (!Number.isFinite(v) || !Number.isFinite(b[i][j])) return -Infinity;
    return v + w * (b[i][j] - v);
  }));
  const argmax = row => {
    let best = -Infinity, index = 0;
    row.forEach((v, i) => { if (v > best) { best = v; index = i; } });
    return index;
  };

  $: lo = Math.min(maxIteration, Math.max(0, Math.floor(Number(shown))));
  $: hi = Math.min(maxIteration, lo + 1);
  $: weight = hi === lo ? 0 : Number(shown) - lo;
  $: matrix = interpolateMatrix(matrices[lo], matrices[hi], weight);
  $: inputValue = interpolateVector(values[lo], values[hi], weight);
  $: outputValue = interpolateVector(values[lo + 1], values[hi + 1], weight);
  $: policy = matrix.map(argmax);
  $: gap = gaps[lo] + weight * (gaps[hi] - gaps[lo]);
  $: activeRow = hover ? hover.i : steadyRow;
  $: activeColumn = hover ? hover.j : policy[activeRow];
  $: activeFlow = model.flow[activeRow][activeColumn];
  $: activeContinuation = Number.isFinite(activeFlow) ? matrix[activeRow][activeColumn] - activeFlow : -Infinity;
  $: activeBest = policy[activeRow];

  const MX = k => matrixPlot.left + (k - kMin) / (kMax - kMin) * matrixPlot.size;
  const MY = k => matrixPlot.top + matrixPlot.size - (k - kMin) / (kMax - kMin) * matrixPlot.size;
  const VX = k => valuePlot.left + (k - kMin) / (kMax - kMin) * valuePlot.width;
  const VY = v => valuePlot.top + valuePlot.height - (v - valueMin) / (valueMax - valueMin) * valuePlot.height;
  const valuePath = series => series.map((v, i) => `${i ? 'L' : 'M'}${VX(grid[i]).toFixed(2)},${VY(v).toFixed(2)}`).join(' ');
  const heatRgb = value => {
    if (!Number.isFinite(value)) return [241, 242, 245];
    const [min, max] = model.matrixRange;
    const t = Math.max(0, Math.min(1, (value - min) / (max - min)));
    const eased = .08 + .92 * t;
    const mix = (a, b) => Math.round(a + eased * (b - a));
    return [mix(238, 0), mix(238, 0), mix(255, 205)];
  };

  function paintMatrix(current, currentPolicy) {
    if (!matrixCanvas) return;
    const context = matrixCanvas.getContext('2d');
    if (!matrixImage) matrixImage = context.createImageData(N, N);
    const pixels = matrixImage.data;
    for (let i = 0; i < N; i++) {
      for (let j = 0; j < N; j++) {
        const offset = ((N - 1 - i) * N + j) * 4;
        const color = j === currentPolicy[i] ? [255, 255, 255] : heatRgb(current[i][j]);
        pixels[offset] = color[0];
        pixels[offset + 1] = color[1];
        pixels[offset + 2] = color[2];
        pixels[offset + 3] = 255;
      }
    }
    context.putImageData(matrixImage, 0, 0);
  }

  $: paintMatrix(matrix, policy);

  function setIteration(event) {
    playing = false;
    sliderValue = Number(event.currentTarget.value);
    shown = sliderValue;
  }
  function togglePlay() {
    if (shown >= maxIteration) { shown = 0; sliderValue = 0; }
    playing = !playing;
  }
  function reset() {
    playing = false;
    shown = 0;
    sliderValue = 0;
    hover = null;
  }
  function pointer(event) {
    if (!chart) return;
    const p = chart.createSVGPoint();
    p.x = event.clientX; p.y = event.clientY;
    const q = p.matrixTransform(chart.getScreenCTM().inverse());
    const inside = q.x >= matrixPlot.left && q.x <= matrixPlot.left + matrixPlot.size
      && q.y >= matrixPlot.top && q.y <= matrixPlot.top + matrixPlot.size;
    if (!inside) { hover = null; return; }
    const j = Math.max(0, Math.min(N - 1, Math.floor((q.x - matrixPlot.left) / cell)));
    const fromTop = Math.max(0, Math.min(N - 1, Math.floor((q.y - matrixPlot.top) / cell)));
    hover = { i: N - 1 - fromTop, j };
  }
  function frame(now) {
    if (playing && lastFrame) {
      shown = Math.min(maxIteration, Number(shown) + Math.min((now - lastFrame) / 1000, .1) * Number(speed));
      sliderValue = shown;
      if (shown >= maxIteration) playing = false;
    }
    lastFrame = now;
    animationId = requestAnimationFrame(frame);
  }
  onMount(() => {
    animationId = requestAnimationFrame(frame);
    return () => cancelAnimationFrame(animationId);
  });
</script>

<section class="vfi-page">
  <div class="visual-shell">
    <div class="controls">
      <h2 class="panel-head">Bellman updates</h2>
      <div class="fixed">
        <span>{@html texBeta} = <strong>{model.parameters.beta.toFixed(1)}</strong></span>
        <span>{@html texAlpha} = <strong>{model.parameters.alpha.toFixed(1)}</strong></span>
        <span>{@html texDelta} = <strong>{model.parameters.delta.toFixed(1)}</strong></span>
        <span>N = <strong>{N}</strong></span>
      </div>

      <div class="transport">
        <button class="play" on:click={togglePlay} aria-label={playing ? 'Pause iteration animation' : 'Play iteration animation'}>
          {#if playing}
            <svg class="icon" viewBox="0 0 16 16" aria-hidden="true"><rect x="3.5" y="2.5" width="3" height="11" rx="1" /><rect x="9.5" y="2.5" width="3" height="11" rx="1" /></svg>
          {:else}
            <svg class="icon" viewBox="0 0 16 16" aria-hidden="true"><path d="M5 2.8 L13 8 L5 13.2 Z" /></svg>
          {/if}
        </button>
        <label class="timeline">
          <span>Iteration</span>
          <input aria-label="Value function iteration" type="range" min="0" max={maxIteration} step=".05" value={sliderValue} on:input={setIteration} />
        </label>
      </div>

      <div class="iteration">
        <span><em>Bellman update</em> <strong>{lo} → {lo + 1}</strong></span>
        <span class="divided"><em>Largest value change</em> <strong>{gap.toExponential(2)}</strong></span>
        <span><em>Error bound</em> <strong>{(gap / (1 - model.parameters.beta)).toExponential(2)}</strong></span>
        <span class="note">Row maxima of the matrix become the next value function.</span>
        <span class="divided"><em>Current state</em> {@html texK} <strong>{grid[activeRow].toFixed(2)}</strong></span>
        <span><em>Candidate choice</em> {@html texKp} <strong>{grid[activeColumn].toFixed(2)}</strong></span>
        {#if Number.isFinite(activeFlow)}
          <span><em>Current utility</em> {@html texCurrent} <strong>{fmt(activeFlow)}</strong></span>
          <span><em>Continuation</em> {@html texContinuation} <strong>{fmt(activeContinuation)}</strong></span>
          <span class:best-choice={activeColumn === activeBest}><em>Cell value</em> {@html texCandidate} <strong>{fmt(matrix[activeRow][activeColumn])}</strong></span>
        {:else}
          <span class="note">This choice implies non-positive consumption and is infeasible.</span>
        {/if}
        <span class="note last">This row chooses {@html texKp} = <strong>{grid[activeBest].toFixed(2)}</strong>.</span>
      </div>

      <div class="buttons"><button class="reset" on:click={reset}>Reset iteration</button></div>
      <label class="speed">Speed
        <select bind:value={speed} aria-label="Playback speed">
          <option value={1}>1 update/s</option>
          <option value={2}>2 updates/s</option>
          <option value={4}>4 updates/s</option>
          <option value={8}>8 updates/s</option>
        </select>
      </label>
      <span class="hint">Move across matrix cells to inspect one candidate choice</span>
    </div>

    <div class="chart-stage">
      <canvas bind:this={matrixCanvas} class="matrix-canvas" width={N} height={N} aria-hidden="true"></canvas>
      <svg bind:this={chart} viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Value function iteration ${lo} to ${lo + 1}, with an N by N choice-value matrix and converging value functions`} on:pointermove={pointer} on:pointerleave={() => hover = null}>
      <defs>
        <clipPath id="vfi-value-clip"><rect x={valuePlot.left} y={valuePlot.top} width={valuePlot.width} height={valuePlot.height} /></clipPath>
      </defs>

      <text x={matrixPlot.left} y="30" class="chart-title">Candidate matrix</text>
      <text x={matrixPlot.left} y="49" class="chart-subtitle">Rows: current k · columns: candidate k′ · white cells: row maxima</text>
      <text x={valuePlot.left} y="30" class="chart-title">Value-function convergence</text>
      <text x={valuePlot.left} y="49" class="chart-subtitle">Input Vₙ, row maxima Vₙ₊₁, and the converged function</text>

      <rect x={matrixPlot.left} y={matrixPlot.top + (N - 1 - activeRow) * cell} width={matrixPlot.size} height={cell} class="selected-row" />
      <rect x={matrixPlot.left + activeColumn * cell + 1} y={matrixPlot.top + (N - 1 - activeRow) * cell + 1} width={cell - 2} height={cell - 2} class="selected-cell" />
      <rect x={matrixPlot.left} y={matrixPlot.top} width={matrixPlot.size} height={matrixPlot.size} class="frame" />

      {#each kTicks as tick}
        <text x={MX(Math.max(kMin, Math.min(kMax, tick)))} y={matrixPlot.top + matrixPlot.size + 23} class="tick" text-anchor="middle">{tick.toFixed(1)}</text>
        <text x={matrixPlot.left - 11} y={MY(Math.max(kMin, Math.min(kMax, tick))) + 4} class="tick" text-anchor="end">{tick.toFixed(1)}</text>
      {/each}
      <text x={matrixPlot.left + matrixPlot.size / 2} y={H - 15} class="axis-label" text-anchor="middle">Next capital, k′</text>
      <text transform={`translate(17 ${matrixPlot.top + matrixPlot.size / 2}) rotate(-90)`} class="axis-label" text-anchor="middle">Current capital, k</text>

      {#each valueTicks as tick}
        <line x1={valuePlot.left} x2={valuePlot.left + valuePlot.width} y1={VY(tick)} y2={VY(tick)} class="grid" />
        <text x={valuePlot.left - 11} y={VY(tick) + 4} class="tick" text-anchor="end">{tick}</text>
      {/each}
      {#each kTicks as tick}
        <line x1={VX(Math.max(kMin, Math.min(kMax, tick)))} x2={VX(Math.max(kMin, Math.min(kMax, tick)))} y1={valuePlot.top} y2={valuePlot.top + valuePlot.height} class="grid" />
        <text x={VX(Math.max(kMin, Math.min(kMax, tick)))} y={valuePlot.top + valuePlot.height + 23} class="tick" text-anchor="middle">{tick.toFixed(1)}</text>
      {/each}
      <g clip-path="url(#vfi-value-clip)">
        <path d={valuePath(values.at(-1))} class="value-limit" />
        <path d={valuePath(inputValue)} class="value-input" />
        <path d={valuePath(outputValue)} class="value-output" />
      </g>
      <rect x={valuePlot.left} y={valuePlot.top} width={valuePlot.width} height={valuePlot.height} class="frame" />
      <text x={valuePlot.left + valuePlot.width / 2} y={H - 15} class="axis-label" text-anchor="middle">Capital, k</text>
      <text transform={`translate(524 ${valuePlot.top + valuePlot.height / 2}) rotate(-90)`} class="axis-label" text-anchor="middle">Value</text>

      <g class="legend" transform={`translate(${valuePlot.left + 10} ${valuePlot.top + 19})`}>
        <line x1="0" x2="25" y1="0" y2="0" class="value-output" /><text x="32" y="4">Vₙ₊₁</text>
        <line x1="95" x2="120" y1="0" y2="0" class="value-input" /><text x="127" y="4">Vₙ</text>
        <line x1="173" x2="198" y1="0" y2="0" class="value-limit" /><text x="205" y="4">limit</text>
      </g>
      </svg>
    </div>
  </div>
</section>

<style>
  .vfi-page { padding: 36px 0 10px; color: #1d263c; line-height: 1.5; }
  .visual-shell { display: grid; grid-template-columns: 310px minmax(0, 1fr); align-items: center; border: 1px solid #dce3f0; border-radius: 18px; box-shadow: 0 16px 45px rgba(37,58,102,.055); overflow: hidden; background: white; }
  .controls { display: grid; grid-template-columns: minmax(0, 1fr); gap: 14px; align-content: start; padding: 18px 18px 18px 22px; border-right: 1px solid #e6eaf1; }
  .controls input[type=range] { accent-color: #111318; }
  .panel-head { margin: 0 0 -6px; font-size: 1.05rem; font-weight: 700; color: #111318; letter-spacing: 0; }
  .fixed { display: flex; gap: 15px; align-items: baseline; flex-wrap: wrap; padding-bottom: 12px; border-bottom: 1px solid #e3e6ec; font-size: .82rem; }
  .fixed strong { font-weight: 600; margin-left: 2px; }
  .transport { display: flex; align-items: center; gap: 12px; }
  .play { border: 0; background: #111318; color: white; width: 40px; height: 40px; flex: 0 0 auto; border-radius: 50%; display: grid; place-items: center; padding: 0; transition: transform .18s ease; }
  .play:hover { transform: translateY(-2px); }
  .play .icon { width: 16px; height: 16px; min-height: 0; fill: white; }
  .play:focus { outline: none; }.play:focus-visible { outline: 2px solid #111318; outline-offset: 3px; }
  .timeline { flex: 1; display: flex; align-items: center; gap: 13px; color: #111318; font-size: .75rem; white-space: nowrap; }
  .timeline input { flex: 1; min-width: 0; }
  .iteration { display: grid; gap: 4px; font-size: .76rem; color: #111318; letter-spacing: .08em; font-variant-numeric: tabular-nums; }
  .iteration span { display: flex; justify-content: space-between; align-items: baseline; gap: 10px; }
  .iteration .divided { margin-top: 4px; padding-top: 8px; border-top: 1px solid #e3e6ec; }
  .iteration .note { display: block; color: #8f1d27; letter-spacing: 0; line-height: 1.4; }
  .iteration .note.last { padding-bottom: 10px; border-bottom: 1px solid #e3e6ec; }
  .iteration em { font-style: normal; letter-spacing: 0; font-size: .79rem; }
  .iteration strong { color: #111318; font-size: .95rem; letter-spacing: -.02em; }
  .iteration .best-choice { color: #0000cd; }
  .buttons { display: flex; gap: 8px; }
  .reset { border: 1px solid #d8dfed; background: white; border-radius: 8px; padding: 7px 12px; font-size: .75rem; white-space: nowrap; transition: border-color .18s ease, transform .18s ease; }
  .reset:hover { border-color: #111318; transform: translateY(-1px); }
  .speed { display: flex; align-items: center; gap: 7px; font-size: .75rem; color: #111318; }
  .speed select { width: auto; border-radius: 7px; background: white; border-color: #d8dfed; color: #1d263c; font-size: .75rem; }
  .hint { color: #111318; font-size: .72rem; font-style: italic; }
  .chart-stage { position: relative; min-width: 0; }
  .matrix-canvas { position: absolute; z-index: 0; left: 5.576923%; top: 11.071429%; width: 38.942308%; height: 72.321429%; image-rendering: pixelated; pointer-events: none; }
  svg { position: relative; z-index: 1; width: 100%; height: auto; max-height: calc(100vh - 185px); min-height: 330px; display: block; touch-action: none; }
  .chart-title { font: 700 17px 'Source Sans Pro', sans-serif; fill: #111318; }
  .chart-subtitle { font: 13px 'Source Sans Pro', sans-serif; fill: #606b7d; }
  .selected-row { fill: none; stroke: #e49350; stroke-width: 2; pointer-events: none; }
  .selected-cell { fill: none; stroke: #111318; stroke-width: 2; pointer-events: none; }
  .grid { stroke: #edf1f8; stroke-width: 1; }
  .frame { fill: none; stroke: #8691a7; stroke-width: 1.4; pointer-events: none; }
  .tick { font: 13px 'Source Sans Pro', sans-serif; fill: #111318; }
  .axis-label { font: 15px 'Source Sans Pro', sans-serif; fill: #111318; }
  .value-input { fill: none; stroke: #6e8699; stroke-width: 2.2; stroke-dasharray: 6 5; }
  .value-output { fill: none; stroke: #0000cd; stroke-width: 3.2; }
  .value-limit { fill: none; stroke: #111318; stroke-width: 1.7; stroke-dasharray: 2 5; opacity: .65; }
  .legend text { font: 13px 'Source Sans Pro', sans-serif; fill: #111318; }
  @media(max-width:1000px) { .visual-shell { grid-template-columns: 280px minmax(0, 1fr); } }
  @media(max-width:850px) { .visual-shell { grid-template-columns: 1fr; }.controls { border-right: 0; border-bottom: 1px solid #e6eaf1; } svg { max-height: none; } }
  @media(max-width:550px) { .chart-subtitle { display: none; }.chart-title { font-size: 15px; }.tick { font-size: 12px; } }
  @media(prefers-reduced-motion:reduce) { .play, .reset { transition: none; } }
</style>
