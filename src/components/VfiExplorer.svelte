<script>
  import { onMount } from 'svelte';
  import { ticks } from 'd3';
  import { renderToString } from 'katex';
  import { makeVfi } from '../lib/vfi.js';

  const W = 960, H = 600;
  const matrixPlot = { left: 74, top: 70, width: 860, height: 470 };
  const valuePlot = { left: 74, top: 70, width: 860, height: 470 };
  const model = makeVfi({ N: 50, maxIteration: 120 });
  const { grid, values, matrices, policies, gaps, N, maxIteration, steady } = model;
  const cellWidth = matrixPlot.width / N;
  const cellHeight = matrixPlot.height / N;
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
  const texPrevious = renderToString(String.raw`V_{n-1}(k'_j)`);
  const texContinuation = renderToString(String.raw`\beta V_{n-1}(k'_j)`);
  const texCandidate = renderToString(String.raw`M_{n-1}(i,j)`);
  const texNext = renderToString(String.raw`V_n(k_i)`);
  const fmt = (x, digits = 3) => Number.isFinite(x) ? x.toFixed(digits) : 'infeasible';

  let shown = 0;
  let sliderValue = 0;
  let viewMode = 'matrix';
  let playing = false;
  let speed = 4;
  let lastFrame = 0;
  let animationId;
  let chart;
  let matrixCanvas;
  let matrixImage;
  let hover = null;

  $: lo = Math.min(maxIteration, Math.max(0, Math.floor(Number(shown))));
  $: matrix = matrices[lo];
  $: inputValue = values[lo];
  $: outputValue = values[lo + 1];
  $: policy = policies[lo];
  $: gap = gaps[lo];
  $: activeRow = hover ? hover.i : steadyRow;
  $: activeColumn = hover ? hover.j : policy[activeRow];
  $: activeConsumption = model.consumption[activeRow][activeColumn];
  $: activeFlow = model.flow[activeRow][activeColumn];
  $: activePrevious = inputValue[activeColumn];
  $: activeContinuation = Number.isFinite(activeFlow) ? matrix[activeRow][activeColumn] - activeFlow : -Infinity;
  $: activeCell = matrix[activeRow][activeColumn];
  $: activeNext = outputValue[activeRow];
  $: activeBest = policy[activeRow];

  const MX = k => matrixPlot.left + (k - kMin) / (kMax - kMin) * matrixPlot.width;
  const MY = k => matrixPlot.top + matrixPlot.height - (k - kMin) / (kMax - kMin) * matrixPlot.height;
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
  function changeView() {
    hover = null;
  }
  function pointer(event) {
    if (!chart || viewMode !== 'matrix') return;
    const p = chart.createSVGPoint();
    p.x = event.clientX; p.y = event.clientY;
    const q = p.matrixTransform(chart.getScreenCTM().inverse());
    const inside = q.x >= matrixPlot.left && q.x <= matrixPlot.left + matrixPlot.width
      && q.y >= matrixPlot.top && q.y <= matrixPlot.top + matrixPlot.height;
    if (!inside) { hover = null; return; }
    const j = Math.max(0, Math.min(N - 1, Math.floor((q.x - matrixPlot.left) / cellWidth)));
    const fromTop = Math.max(0, Math.min(N - 1, Math.floor((q.y - matrixPlot.top) / cellHeight)));
    hover = { i: N - 1 - fromTop, j };
  }
  function frame(now) {
    if (playing && lastFrame) {
      shown = Math.min(maxIteration, Number(shown) + Math.min((now - lastFrame) / 1000, .1) * Number(speed));
      sliderValue = Math.floor(shown);
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

      <label class="plot-select">
        <span>Show</span>
        <select bind:value={viewMode} on:change={changeView} aria-label="Plot to display">
          <option value="matrix">Candidate matrix</option>
          <option value="value">Value-function convergence</option>
        </select>
      </label>

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
          <input aria-label="Value function iteration" type="range" min="0" max={maxIteration} step="1" value={sliderValue} on:input={setIteration} />
        </label>
      </div>

      <div class="iteration">
        <span><em>Bellman update</em> <strong>{lo}</strong></span>
        <span class="divided"><em>Largest value change</em> <strong>{gap.toExponential(2)}</strong></span>
        <span><em>Error bound</em> <strong>{(gap / (1 - model.parameters.beta)).toExponential(2)}</strong></span>
        {#if viewMode === 'matrix'}
          <span class="note divided last">White cells are row maxima. Hover over any cell to open its Bellman decomposition.</span>
        {:else}
          <span class="note divided last">The row maxima form the blue function (V_{n+1}); repeated updates move it toward the dotted limit.</span>
        {/if}
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
      <span class="hint">{viewMode === 'matrix' ? 'Move across the matrix to inspect a candidate choice' : 'Use the slider to compare successive value functions'}</span>
    </div>

    <div class="chart-stage">
      <svg bind:this={chart} viewBox={`0 0 ${W} ${H}`} role="img" aria-label={viewMode === 'matrix' ? `Value function iteration ${lo} to ${lo + 1}: N by N candidate matrix` : `Value function iteration ${lo} to ${lo + 1}: converging value functions`} on:pointermove={pointer} on:pointerleave={() => hover = null}>
      <defs>
        <clipPath id="vfi-value-clip"><rect x={valuePlot.left} y={valuePlot.top} width={valuePlot.width} height={valuePlot.height} /></clipPath>
      </defs>

      {#if viewMode === 'matrix'}
        <text x={matrixPlot.left} y="32" class="chart-title">Candidate matrix</text>
        <text x={matrixPlot.left} y="55" class="chart-subtitle">Rows: current capital · columns: next capital · white cells: row maxima</text>
        <foreignObject x={matrixPlot.left} y={matrixPlot.top} width={matrixPlot.width} height={matrixPlot.height}>
          <canvas xmlns="http://www.w3.org/1999/xhtml" bind:this={matrixCanvas} class="matrix-canvas" width={N} height={N} aria-hidden="true"></canvas>
        </foreignObject>
        {#if hover}
          <rect x={matrixPlot.left + activeColumn * cellWidth + .5} y={matrixPlot.top + (N - 1 - activeRow) * cellHeight + .5} width={Math.max(1, cellWidth - 1)} height={Math.max(1, cellHeight - 1)} class="selected-cell" />
          <foreignObject class="breakdown-object" x={matrixPlot.left + matrixPlot.width - 385} y={matrixPlot.top + 18} width="365" height="270">
            <div xmlns="http://www.w3.org/1999/xhtml" class="cell-breakdown">
              <div class="breakdown-head">
                <span>Bellman cell</span>
                <strong>update {lo}</strong>
              </div>
              <div class="state-pair">
                <span>{@html texK} = <strong>{grid[activeRow].toFixed(3)}</strong></span>
                <span>{@html texKp} = <strong>{grid[activeColumn].toFixed(3)}</strong></span>
              </div>
              {#if Number.isFinite(activeFlow)}
                <div class="breakdown-line"><span>Consumption</span><strong>{activeConsumption.toFixed(3)}</strong></div>
                <div class="breakdown-line"><span>{@html texPrevious}</span><strong>{fmt(activePrevious)}</strong></div>
                <div class="breakdown-line"><span>{@html texCurrent}</span><strong>{fmt(activeFlow)}</strong></div>
                <div class="breakdown-line"><span>{@html texContinuation}</span><strong>{fmt(activeContinuation)}</strong></div>
                <div class="cell-total"><span>{@html texCandidate}</span><strong>{fmt(activeFlow)} + {fmt(activeContinuation)} = {fmt(activeCell)}</strong></div>
                <div class="next-value"><span>{@html texNext}</span><strong>{fmt(activeNext)}</strong></div>
                <div class:maximum={activeColumn === activeBest} class="max-note">
                  {activeColumn === activeBest ? 'This cell is the row maximum.' : `Row maximum: k′ = ${grid[activeBest].toFixed(3)}`}
                </div>
              {:else}
                <div class="infeasible-cell">Consumption is non-positive, so this cell has value −∞.</div>
              {/if}
            </div>
          </foreignObject>
        {/if}
        <rect x={matrixPlot.left} y={matrixPlot.top} width={matrixPlot.width} height={matrixPlot.height} class="frame" />
        {#each kTicks as tick}
          <line x1={MX(Math.max(kMin, Math.min(kMax, tick)))} x2={MX(Math.max(kMin, Math.min(kMax, tick)))} y1={matrixPlot.top + matrixPlot.height} y2={matrixPlot.top + matrixPlot.height + 7} class="axis-tick" />
          <line x1={matrixPlot.left - 7} x2={matrixPlot.left} y1={MY(Math.max(kMin, Math.min(kMax, tick)))} y2={MY(Math.max(kMin, Math.min(kMax, tick)))} class="axis-tick" />
          <text x={MX(Math.max(kMin, Math.min(kMax, tick)))} y={matrixPlot.top + matrixPlot.height + 27} class="tick" text-anchor="middle">{tick.toFixed(1)}</text>
          <text x={matrixPlot.left - 15} y={MY(Math.max(kMin, Math.min(kMax, tick))) + 5} class="tick" text-anchor="end">{tick.toFixed(1)}</text>
        {/each}
        <text x={matrixPlot.left + matrixPlot.width / 2} y={H - 10} class="axis-label" text-anchor="middle">Next capital, k′</text>
        <text transform={`translate(19 ${matrixPlot.top + matrixPlot.height / 2}) rotate(-90)`} class="axis-label" text-anchor="middle">Current capital, k</text>
      {:else}
        <text x={valuePlot.left} y="32" class="chart-title">Value-function convergence</text>
        <text x={valuePlot.left} y="55" class="chart-subtitle">Input Vₙ, row maxima Vₙ₊₁, and the converged function</text>
        {#each valueTicks as tick}
          <line x1={valuePlot.left} x2={valuePlot.left + valuePlot.width} y1={VY(tick)} y2={VY(tick)} class="grid" />
          <text x={valuePlot.left - 15} y={VY(tick) + 5} class="tick" text-anchor="end">{tick}</text>
        {/each}
        {#each kTicks as tick}
          <line x1={VX(Math.max(kMin, Math.min(kMax, tick)))} x2={VX(Math.max(kMin, Math.min(kMax, tick)))} y1={valuePlot.top} y2={valuePlot.top + valuePlot.height} class="grid" />
          <line x1={VX(Math.max(kMin, Math.min(kMax, tick)))} x2={VX(Math.max(kMin, Math.min(kMax, tick)))} y1={valuePlot.top + valuePlot.height} y2={valuePlot.top + valuePlot.height + 7} class="axis-tick" />
          <text x={VX(Math.max(kMin, Math.min(kMax, tick)))} y={valuePlot.top + valuePlot.height + 27} class="tick" text-anchor="middle">{tick.toFixed(1)}</text>
        {/each}
        <g clip-path="url(#vfi-value-clip)">
          <path d={valuePath(values.at(-1))} class="value-limit" />
          <path d={valuePath(inputValue)} class="value-input" />
          <path d={valuePath(outputValue)} class="value-output" />
        </g>
        <rect x={valuePlot.left} y={valuePlot.top} width={valuePlot.width} height={valuePlot.height} class="frame" />
        <text x={valuePlot.left + valuePlot.width / 2} y={H - 10} class="axis-label" text-anchor="middle">Capital, k</text>
        <text transform={`translate(19 ${valuePlot.top + valuePlot.height / 2}) rotate(-90)`} class="axis-label" text-anchor="middle">Value</text>
        <g class="legend" transform={`translate(${valuePlot.left + 16} ${valuePlot.top + 22})`}>
          <line x1="0" x2="25" y1="0" y2="0" class="value-output" /><text x="32" y="4">Vₙ₊₁</text>
          <line x1="95" x2="120" y1="0" y2="0" class="value-input" /><text x="127" y="4">Vₙ</text>
          <line x1="173" x2="198" y1="0" y2="0" class="value-limit" /><text x="205" y="4">limit</text>
        </g>
      {/if}
      </svg>
    </div>
  </div>
</section>

<style>
  .vfi-page { padding: 36px 0 10px; color: #1d263c; line-height: 1.5; }
  .visual-shell { display: grid; grid-template-columns: 320px minmax(0, 1fr); align-items: center; border: 1px solid #dce3f0; border-radius: 18px; box-shadow: 0 16px 45px rgba(37,58,102,.055); overflow: hidden; background: white; }
  .controls { display: grid; grid-template-columns: minmax(0, 1fr); gap: 14px; align-content: start; padding: 18px 18px 18px 22px; border-right: 1px solid #e6eaf1; }
  .controls input[type=range] { accent-color: #111318; }
  .panel-head { margin: 0 0 -6px; font-size: 1.05rem; font-weight: 700; color: #111318; letter-spacing: 0; }
  .fixed { display: flex; gap: 15px; align-items: baseline; flex-wrap: wrap; padding-bottom: 12px; border-bottom: 1px solid #e3e6ec; font-size: .82rem; }
  .fixed strong { font-weight: 600; margin-left: 2px; }
  .plot-select { display: flex; align-items: center; justify-content: space-between; gap: 12px; color: #111318; font-size: .78rem; }
  .plot-select select { width: 190px; max-width: 70%; border: 1px solid #d8dfed; border-radius: 7px; background: white; color: #1d263c; font-size: .76rem; }
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
  .buttons { display: flex; gap: 8px; }
  .reset { border: 1px solid #d8dfed; background: white; border-radius: 8px; padding: 7px 12px; font-size: .75rem; white-space: nowrap; transition: border-color .18s ease, transform .18s ease; }
  .reset:hover { border-color: #111318; transform: translateY(-1px); }
  .speed { display: flex; align-items: center; gap: 7px; font-size: .75rem; color: #111318; }
  .speed select { width: auto; border-radius: 7px; background: white; border-color: #d8dfed; color: #1d263c; font-size: .75rem; }
  .hint { color: #111318; font-size: .72rem; font-style: italic; }
  .chart-stage { min-width: 0; }
  .matrix-canvas { display: block; width: 100%; height: 100%; image-rendering: pixelated; pointer-events: none; }
  svg { width: 100%; height: auto; max-height: calc(100vh - 185px); min-height: 300px; display: block; touch-action: none; }
  .chart-title { font: 700 17px 'Source Sans Pro', sans-serif; fill: #111318; }
  .chart-subtitle { font: 13px 'Source Sans Pro', sans-serif; fill: #606b7d; }
  .selected-cell { fill: rgba(17,19,24,.22); stroke: #111318; stroke-width: 2.5; pointer-events: none; }
  .breakdown-object { pointer-events: none; }
  .cell-breakdown { box-sizing: border-box; height: 100%; padding: 14px 16px; border: 1px solid #111318; border-radius: 12px; background: rgba(255,255,255,.97); box-shadow: 0 12px 32px rgba(17,19,24,.18); color: #111318; font-family: 'Source Sans Pro', sans-serif; font-variant-numeric: tabular-nums; }
  .breakdown-head, .state-pair, .breakdown-line, .cell-total, .next-value { display: flex; align-items: baseline; justify-content: space-between; gap: 14px; }
  .breakdown-head { padding-bottom: 8px; border-bottom: 1px solid #dfe3eb; font-size: 17px; font-weight: 700; }
  .breakdown-head strong { color: #0000cd; font-size: 15px; }
  .state-pair { padding: 8px 0 6px; color: #4e596d; font-size: 14px; }
  .state-pair strong { color: #111318; font-size: 16px; }
  .breakdown-line { padding: 2px 0; font-size: 14px; }
  .breakdown-line strong { font-size: 17px; }
  .cell-total { margin-top: 7px; padding: 7px 0; border-top: 1px solid #dfe3eb; border-bottom: 1px solid #dfe3eb; font-size: 15px; }
  .cell-total strong { font-size: 17px; }
  .next-value { padding-top: 7px; color: #0000cd; font-size: 16px; font-weight: 700; }
  .next-value strong { font-size: 20px; }
  .max-note { margin-top: 5px; color: #596579; font-size: 13px; }
  .max-note.maximum { color: #0000cd; font-weight: 700; }
  .infeasible-cell { margin-top: 18px; padding: 16px; border-radius: 8px; background: #f1f2f5; font-size: 17px; line-height: 1.4; }
  .grid { stroke: #edf1f8; stroke-width: 1; }
  .axis-tick { stroke: #8691a7; stroke-width: 1.4; }
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
