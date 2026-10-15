<script>
  import { onDestroy } from 'svelte';
  import { oneVariable, oneVariableFacts } from '../lib/utility.js';
  import { renderToString } from 'katex';
  import LineChart from './LineChart.svelte';

  export let kind = 'utility';

  // start: lowest input drawn; log and CRRA diverge at zero. scaled: the A slider sets the parameter.
  const kinds = {
    utility: { title: 'Utility functions', x: 'c', fn: 'u', xLabel: 'Consumption c', yLabel: 'Utility u(c)', ticked: ['log', 'crra'], families: [
      { id: 'log', name: 'Logarithmic', tag: 'steep near zero', parameter: 1, start: 0.25, formula: 'u(c)=\\ln c', derivative: "u'(c)=1/c", second: "u''(c)=-1/c^2" },
      { id: 'crra', name: 'CRRA', tag: 'curvature matters', parameter: 2, start: 0.25, formula: 'u(c)=1-1/c\\quad(\\sigma=2)', derivative: "u'(c)=c^{-2}", second: "u''(c)=-2c^{-3}" },
      { id: 'cara', name: 'CARA', tag: 'finite ceiling', parameter: 0.6, start: 0, formula: 'u(c)=(1-e^{-0.6c})/0.6', derivative: "u'(c)=e^{-0.6c}", second: "u''(c)=-0.6e^{-0.6c}" },
      { id: 'quadratic', name: 'Quadratic', tag: 'satiation', parameter: 0.35, start: 0, formula: 'u(c)=c-0.175c^2', derivative: "u'(c)=1-0.35c", second: "u''(c)=-0.35" },
    ] },
    production: { title: 'Production functions', x: 'k', fn: 'f', xLabel: 'Capital per worker k', yLabel: 'Output per worker f(k)', ticked: ['ak', 'cobb-douglas', 'ces'], families: [
      { id: 'ak', name: 'AK', tag: 'constant returns', scaled: true, start: 0, formula: 'f(k)=Ak', derivative: "f'(k)=A", second: "f''(k)=0" },
      { id: 'cobb-douglas', name: 'Cobb-Douglas', tag: 'diminishing returns', scaled: true, start: 0, formula: 'f(k)=Ak^{1/3}', derivative: "f'(k)=\\tfrac{A}{3}k^{-2/3}", second: "f''(k)=-\\tfrac{2A}{9}k^{-5/3}" },
      { id: 'ces', name: 'CES', tag: 'elasticity σ = 2', scaled: true, start: 0, formula: 'f(k)=A\\left(\\tfrac13\\sqrt{k}+\\tfrac23\\right)^2', derivative: "f'(k)=\\tfrac{A}{9}\\left(1+2/\\sqrt{k}\\right)", second: "f''(k)=-\\tfrac{A}{9}k^{-3/2}" },
    ] },
  };
  const setup = kinds[kind];
  if (!setup) throw new Error(`Unknown explorer kind: ${kind}`);
  const families = setup.families;
  const X_MAX = 8;
  const PLAY_MS = 5000;
  let ticked = [...setup.ticked];
  let c = 2;
  let productivity = 1;
  let playing = false;
  let frame = null;

  $: curves = families.filter(f => ticked.includes(f.id)).map(f => buildCurve(f, f.scaled ? Number(productivity) : f.parameter));
  $: rows = curves.map(curve => ({ ...curve, at: oneVariable(curve.family.id, Number(c), curve.parameter) }));
  // Grey dotted guides from each point to both axes; the chart clips the long downward leg.
  $: guides = rows.flatMap(row => [
    { id: `${row.family.id}-guide-x`, label: '', points: [{ x: Number(c), y: yDomain[0] - 1000 }, { x: Number(c), y: row.at.value }], color: 'fn-guide', width: 1.3, dasharray: '2 4' },
    { id: `${row.family.id}-guide-y`, label: '', points: [{ x: 0, y: row.at.value }, { x: Number(c), y: row.at.value }], color: 'fn-guide', width: 1.3, dasharray: '2 4' },
  ]);
  $: series = [...guides, ...rows.flatMap(row => [
    { id: row.family.id, label: row.family.name, points: row.points, color: row.color, width: 3 },
    { id: `${row.family.id}-tangent`, label: `${row.family.name} tangent`, points: tangentPoints(row.at, Number(c)), color: row.color, width: 2, dash: true },
  ])];
  $: markers = rows.map(row => ({ x: Number(c), y: row.at.value, color: row.color }));
  $: yDomain = fitDomain(curves);
  $: akTicked = ticked.includes('ak');
  $: amountSymbol = setup.x;
  $: growthRate = 0.2 * Number(productivity) - 0.25;

  function buildCurve(family, parameter) {
    const points = [];
    for (let i = 0; i <= 160; i++) {
      const x = family.start + (X_MAX - family.start) * i / 160;
      points.push({ x, y: oneVariable(family.id, x, parameter).value });
    }
    const tex = [family.formula, family.derivative, family.second].map(t => renderToString(t, { throwOnError: false }));
    return { family, parameter, color: `fn-${family.id}`, points, tex, facts: oneVariableFacts(family.id, parameter) };
  }
  // Fixed half-width in c, as in the earlier Manim films.
  function tangentPoints(at, x) {
    const half = 0.47;
    return [{ x: x - half, y: at.value - half * at.marginal }, { x: x + half, y: at.value + half * at.marginal }];
  }
  // Fit the curves only, so the axis stays still while the tangents move.
  function fitDomain(list) {
    const ys = list.flatMap(curve => curve.points.map(p => p.y));
    if (!ys.length) return [0, 1];
    const low = Math.min(...ys);
    const high = Math.max(...ys);
    return [Math.min(low, 0), high];
  }
  function fmt(value) {
    if (!Number.isFinite(value)) return '∞';
    if (Math.abs(value) < 0.005) return '0.00';
    return value.toFixed(2).replace('-', '−');
  }
  function stop() {
    playing = false;
    if (frame !== null) cancelAnimationFrame(frame);
    frame = null;
  }
  function togglePlay() {
    if (playing) { stop(); return; }
    if (Number(c) >= 7.45) c = 0.5;
    playing = true;
    let last = null;
    const tick = now => {
      if (last !== null) c = Math.min(7.5, Number(c) + 7 * (now - last) / PLAY_MS);
      last = now;
      if (Number(c) >= 7.5) { stop(); return; }
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
  }
  onDestroy(stop);
</script>

<section class="lab" id="function-explorer" aria-label={setup.title}>
  <h1 class="explorer-title">{setup.title} visualised</h1>
  <div class="family-picks" role="group" aria-label="Choose the functions to draw" style={`--count: ${families.length}`}>
    {#each families as family}
      <label class="pick" class:on={ticked.includes(family.id)} style={`--swatch: var(--fn-${family.id})`}><input type="checkbox" bind:group={ticked} value={family.id} /><span><span class="pick-name">{family.name}</span><small>{family.tag}</small></span></label>
    {/each}
  </div>
  <div class="stage-grid">
    <div class="stage-main">
      <div class="chart-frame">
        {#if rows.length}
          <LineChart {series} {markers} {yDomain} xDomain={[0, X_MAX]} title="Selected functions and their tangents" description="Each selected function is drawn on shared axes with its tangent at the chosen input." xLabel={setup.xLabel} xLabelShort={setup.x} yLabel={setup.yLabel} showLegend={false} interactive={false} animate={false} scaleCues={false} heightScale={1.2} grid={false} />
        {:else}
          <p class="empty-chart">Tick at least one function above to draw it.</p>
        {/if}
      </div>
      <div class="transport">
        <button class="play" type="button" on:click={togglePlay} aria-label={playing ? 'Pause tangent animation' : 'Play tangent animation'}>{playing ? '❚❚' : '▶'}</button>
        <label for="input-slider"><span>Move the tangents</span><strong>{amountSymbol} = {fmt(Number(c))}</strong></label>
        <input id="input-slider" aria-label={setup.xLabel} type="range" min="0.5" max="7.5" step="0.05" bind:value={c} on:input={stop} style={`--progress:${((Number(c) - 0.5) / 7) * 100}%`} />
        <div class="range-ends"><span>0.5</span><span>7.5</span></div>
      </div>
      {#if kind === 'production'}
        <div class="parameter-control">
          <label for="productivity-slider"><span>Productivity A</span><strong>{fmt(Number(productivity))}</strong></label>
          <input id="productivity-slider" aria-label="Productivity, A" type="range" min="0.5" max="2" step="0.25" bind:value={productivity} style={`--progress:${((Number(productivity) - 0.5) / 1.5) * 100}%`} />
          <div class="range-ends"><span>0.50</span><span>2.00</span></div>
        </div>
      {/if}
    </div>
    <aside class="readout" aria-live="polite">
      <p class="readout-kicker">At {amountSymbol} = {fmt(Number(c))}</p>
      {#if rows.length}
        <table class="values">
          <thead><tr><th scope="col">Function</th><th scope="col">{setup.fn}({setup.x})</th><th scope="col">{setup.fn}′({setup.x})</th><th scope="col">{setup.fn}″({setup.x})</th></tr></thead>
          <tbody>{#each rows as row}<tr style={`--swatch: var(--${row.color})`}><th scope="row"><i aria-hidden="true"></i>{row.family.name}</th><td>{fmt(row.at.value)}</td><td>{fmt(row.at.marginal)}</td><td>{fmt(row.at.second)}</td></tr>{/each}</tbody>
        </table>
      {:else}
        <p class="value-note">Tick a function to read its values.</p>
      {/if}
      {#if akTicked}<p class="growth-note"><strong>AK growth check</strong><span>With saving s = 0.20, depreciation δ = 0.20 and population growth n = 0.05:</span><span>k̇/k = sA − (δ + n) = <b>{growthRate > 0 ? '+' : ''}{fmt(growthRate)}</b></span><span>{growthRate > 0 ? 'Capital per worker grows.' : growthRate < 0 ? 'Capital per worker shrinks.' : 'Capital per worker stays constant.'}</span></p>{/if}
    </aside>
  </div>
  {#if rows.length}
    <div class="fact-cards" style={`--count: ${families.length}`}>
      {#each rows as row}
        <article style={`--swatch: var(--${row.color})`}>
          <h3>{row.family.name}</h3>
          <div class="math-stack">{#each row.tex as html}<div class="math">{@html html}</div>{/each}</div>
          <dl><div><dt>Domain</dt><dd>{row.facts.domain}</dd></div><div><dt>Minimum</dt><dd>{row.facts.minimum}</dd></div><div><dt>Maximum</dt><dd>{row.facts.maximum}</dd></div></dl>
          <p><strong>What to notice.</strong> {row.facts.shape}</p>
          <p><strong>{row.family.id === 'ak' ? 'Why it matters in AK.' : 'Where it appears.'}</strong> {row.facts.use}</p>
        </article>
      {/each}
    </div>
  {/if}
</section>

<style>
  .lab { --fn-log: #0000cd; --fn-crra: #cb622d; --fn-cara: #00897b; --fn-quadratic: #a23b8f; --fn-ak: #cb622d; --fn-cobb-douglas: #0000cd; --fn-ces: #00897b; --fn-guide: #9a9da6; padding: 36px 0 70px; }
  .explorer-title { font-size: clamp(1.52rem, 2.56vw, 2.16rem); line-height: 1.1; letter-spacing: -.035em; margin: 0 0 38px; }
  .family-picks { display: grid; grid-template-columns: repeat(var(--count), minmax(0, 1fr)); gap: 8px; margin-bottom: 16px; }
  .pick { display: flex; gap: 11px; align-items: flex-start; min-width: 0; padding: 13px 15px 11px; background: #f7f8fd; border: 1px solid #e1e3ee; border-radius: 8px; cursor: pointer; transition: border-color .2s, background .2s, transform .2s; }
  .pick:hover { border-color: var(--swatch); transform: translateY(-2px); }
  .pick.on { background: color-mix(in srgb, var(--swatch) 7%, #fff); border-color: var(--swatch); box-shadow: inset 0 3px 0 var(--swatch); }
  .pick:focus-within { outline: 2px solid var(--swatch); outline-offset: 2px; }
  .pick input { accent-color: var(--swatch); width: 17px; height: 17px; margin: 2px 0 0; flex: none; cursor: pointer; }
  .pick-name, .pick small { display: block; white-space: normal; }
  .pick-name { font-size: .96rem; font-weight: 700; line-height: 1.2; }
  .pick small { font-size: .75rem; line-height: 1.35; color: var(--muted); margin-top: 4px; }
  .stage-grid { display: grid; grid-template-columns: minmax(0, 1.7fr) minmax(270px, .75fr); gap: 16px; align-items: stretch; }
  .stage-main, .readout { border: 1px solid var(--rule); border-radius: 12px; background: #fff; overflow: hidden; }
  .chart-frame { --chart-tick-size: 1rem; --chart-title-size: 1.0625rem; padding: 20px 22px 4px; border-bottom: 1px solid var(--rule); }
  .empty-chart { min-height: 350px; display: grid; place-items: center; color: var(--muted); margin: 0; }
  .transport { display: grid; grid-template-columns: 42px 1fr; column-gap: 16px; padding: 18px 22px 20px; align-items: center; }
  .play { grid-row: 1 / 4; width: 42px; height: 42px; border: 1px solid var(--accent); border-radius: 50%; background: var(--accent); color: #fff; font-size: .8rem; display: grid; place-items: center; transition: transform .2s, box-shadow .2s; }
  .play:hover { transform: scale(1.06); box-shadow: 0 3px 12px #0000cd24; }
  .transport label { display: flex; justify-content: space-between; gap: 12px; align-items: baseline; font-size: .86rem; font-weight: 600; }
  .transport label strong { font-variant-numeric: tabular-nums; color: var(--accent); white-space: nowrap; }
  input[type='range'] { margin: 11px 0 0; appearance: none; width: 100%; height: 5px; background: linear-gradient(to right, var(--accent) var(--progress), #dfe2f2 var(--progress)); border-radius: 5px; cursor: pointer; }
  input[type='range']::-webkit-slider-thumb { appearance: none; width: 19px; height: 19px; border-radius: 50%; background: #fff; border: 3px solid var(--accent); box-shadow: 0 2px 5px #0002; }
  input[type='range']::-moz-range-thumb { width: 14px; height: 14px; border-radius: 50%; background: #fff; border: 3px solid var(--accent); box-shadow: 0 2px 5px #0002; }
  .range-ends { margin-top: 12px; display: flex; justify-content: space-between; color: var(--muted); font-size: .72rem; font-variant-numeric: tabular-nums; line-height: 1.3; }
  .parameter-control { margin: 0 22px 20px 80px; padding-top: 15px; border-top: 1px solid var(--rule); }
  .parameter-control label { display: flex; justify-content: space-between; gap: 12px; font-size: .86rem; font-weight: 600; }
  .parameter-control label strong { color: var(--accent); font-variant-numeric: tabular-nums; }
  .parameter-control input { margin-top: 12px; }
  .readout { padding: 22px; display: flex; flex-direction: column; }
  .readout-kicker { font-size: .71rem; font-weight: 700; letter-spacing: .13em; text-transform: uppercase; color: var(--accent); margin: 0 0 14px; }
  .values { width: 100%; border-collapse: collapse; font-size: .86rem; font-variant-numeric: tabular-nums; }
  .values th, .values td { padding: 8px 0 8px 8px; text-align: right; border-bottom: 1px solid var(--rule); white-space: nowrap; }
  .values th:first-child { text-align: left; padding-left: 0; }
  .values thead th { font-size: .72rem; font-weight: 600; color: var(--muted); }
  .values tbody th { font-weight: 600; }
  .values i { display: inline-block; width: 14px; height: 3px; border-radius: 2px; background: var(--swatch); vertical-align: middle; margin-right: 8px; }
  .values td { color: var(--swatch); font-weight: 600; }
  .value-note { font-size: .74rem; line-height: 1.45; color: var(--muted); margin: 10px 0 0; }
  .growth-note { display: grid; gap: 4px; margin: 20px 0 0; padding: 13px 14px; border-left: 3px solid var(--accent); background: var(--accent-soft); font-size: .8rem; line-height: 1.4; }
  .growth-note strong { font-size: .75rem; text-transform: uppercase; letter-spacing: .07em; color: var(--accent); }
  .growth-note b { color: var(--accent); font-variant-numeric: tabular-nums; }
  .fact-cards { display: grid; grid-template-columns: repeat(var(--count), minmax(0, 1fr)); gap: 8px; margin-top: 15px; }
  .fact-cards article { display: grid; gap: 12px; align-content: start; padding: 17px 20px; background: #fafaff; border: 1px solid var(--rule); border-top: 3px solid var(--swatch); border-radius: 9px; }
  .fact-cards h3 { margin: 0; font-size: 1.05rem; line-height: 1.3; }
  .math-stack { display: grid; gap: 4px; }
  .math-stack .math { overflow-x: auto; font-size: .88rem; line-height: 1.5; }
  .fact-cards dl { display: grid; gap: 8px; margin: 0; }
  .fact-cards dt { font-size: .69rem; font-weight: 700; letter-spacing: .11em; text-transform: uppercase; color: var(--muted); }
  .fact-cards dd { margin: 2px 0 0; font-size: .88rem; font-weight: 600; line-height: 1.35; }
  .fact-cards p { margin: 0; font-size: .88rem; line-height: 1.45; color: var(--muted); }
  .fact-cards p strong { color: var(--ink); }
  @media (max-width: 1050px) { .stage-grid { grid-template-columns: minmax(0, 1.4fr) minmax(250px, .8fr); } .family-picks, .fact-cards { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
  @media (max-width: 760px) { .lab { padding: 24px 0 54px; } .stage-grid { grid-template-columns: 1fr; } .family-picks { grid-template-columns: repeat(2, minmax(0, 1fr)); } .fact-cards { grid-template-columns: 1fr; } }
  @media (max-width: 430px) { .family-picks { gap: 5px; } .pick { padding: 11px 10px; gap: 8px; } .pick-name { font-size: .84rem; } .pick small { font-size: .7rem; } .chart-frame { padding: 14px 10px 0; } .transport { padding: 15px 14px 16px; grid-template-columns: 37px 1fr; gap: 10px; } .play { width: 37px; height: 37px; } .transport label { font-size: .78rem; } .parameter-control { margin-left: 61px; margin-right: 14px; } .parameter-control label { font-size: .78rem; } .readout { padding: 18px; } }
  @media (prefers-reduced-motion: reduce) { .pick, .play { transition: none; } }
</style>
