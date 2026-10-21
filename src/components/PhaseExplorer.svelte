<script>
  import { onMount } from 'svelte';
  import { ticks } from 'd3';
  import { renderToString } from 'katex';
  import { makePhase } from '../lib/phase.js';
  import { growthParameters } from '../lib/models.js';

  const W = 960, H = 540;
  const plot = { left: 74, top: 14, width: 860, height: 470 };
  // alpha, delta and sigma stay at their defaults; only A and rho move.
  const fixed = [
    { key: 'alpha', tex: renderToString(String.raw`\alpha`), digits: 2 },
    { key: 'delta', tex: renderToString(String.raw`\delta`), digits: 2 },
    { key: 'sigma', tex: renderToString(String.raw`\sigma`), digits: 0 },
  ];
  const sliders = [
    { key: 'A', label: 'A', min: .5, max: 2, step: .05 },
    { key: 'rho', label: 'ρ', min: .01, max: .1, step: .005 },
  ];
  const texK = renderToString('k');
  const texC = renderToString('c');
  const texF = renderToString('y = f(k)');
  const texFp = renderToString("f'(k)");
  const texGap = renderToString(String.raw`\delta + \rho`);
  const texUse = renderToString(String.raw`\delta k + c`);
  const fmt = x => Number.isFinite(x) ? x.toFixed(3) : '-';
  let params = { ...growthParameters };
  let m, X, Y, path, curve, arms, ticksK, ticksC, arrows;
  $: m = makePhase(params);
  $: X = k => plot.left + k / m.limits.k * plot.width;
  $: Y = c => plot.top + plot.height - c / m.limits.c * plot.height;
  $: path = points => points.map((p, i) => `${i ? 'L' : 'M'}${X(p.k).toFixed(2)},${Y(p.c).toFixed(2)}`).join(' ');
  $: curve = Array.from({ length: 321 }, (_, i) => ({ k: m.limits.k * i / 320, c: m.netOutput(m.limits.k * i / 320) }));
  $: quads = quadrants(m, curve);

  // The two nullclines split the plane into four regions; dx, dy give the direction of k and c in each.
  let showQuads = false, showVectors = true;
  function quadrants(m, curve) {
    const ks = m.steady.k, kMax = m.limits.k, cMax = m.limits.c;
    const clamp = p => ({ k: p.k, c: Math.min(Math.max(p.c, 0), cMax) });
    const mid = { k: ks, c: m.netOutput(ks) };
    const left = [...curve.filter(p => p.k < ks), mid].map(clamp), right = [mid, ...curve.filter(p => p.k > ks)].map(clamp);
    const anchor = (k, above) => { const c = clamp({ k, c: m.netOutput(k) }).c; return { k, c: above ? (c + cMax) / 2 : c / 2 }; };
    return [
      { color: '#3f74d1', dx: -1, dy: 1, poly: [{ k: 0, c: cMax }, { k: ks, c: cMax }, ...[...left].reverse()], at: anchor(.5 * ks, true) },
      { color: '#d9545e', dx: 1, dy: 1, poly: [...left, { k: ks, c: 0 }, { k: 0, c: 0 }], at: anchor(.5 * ks, false) },
      { color: '#9a1f2a', dx: -1, dy: -1, poly: [...right, { k: kMax, c: cMax }, { k: ks, c: cMax }], at: anchor((ks + kMax) / 2, true) },
      { color: '#173f8f', dx: 1, dy: -1, poly: [...right, { k: kMax, c: 0 }, { k: ks, c: 0 }], at: anchor((ks + kMax) / 2, false) },
    ];
  }
  // A joined pair of arrows from one corner: one horizontal (k), one vertical (c).
  function cross(q) {
    const L = 24, x = X(q.at.k) - q.dx * L / 2, y = Y(q.at.c) + q.dy * L / 2, ex = x + q.dx * L, ey = y - q.dy * L;
    return `M${ex},${y} L${x},${y} L${x},${ey} M${ex - q.dx * 7},${y - 5} L${ex},${y} L${ex - q.dx * 7},${y + 5} M${x - 5},${ey + q.dy * 7} L${x},${ey} L${x + 5},${ey + q.dy * 7}`;
  }
  $: arms = [m.saddleArms.left, m.saddleArms.right].map(points => path([...points].reverse()));
  // Twice the usual tick density on the capital axis: halve the standard step.
  $: stepK = (ticks(0, m.limits.k, 6)[1] - ticks(0, m.limits.k, 6)[0]) / 2;
  $: ticksK = Array.from({ length: Math.floor(m.limits.k / stepK + 1e-9) + 1 }, (_, i) => +(i * stepK).toFixed(6));
  $: ticksC = ticks(0, m.limits.c, 6);
  $: arrows = field(m, X, Y);

  // Unit direction of motion on an evenly spaced 15 x 8 grid, with a staggered flow timing per arrow.
  function field(m, X, Y) {
    const out = [];
    for (let i = 0; i < 15; i++) {
      for (let j = 0; j < 8; j++) {
        const k = m.limits.k * (i + .5) / 15, c = m.limits.c * (j + .5) / 8;
        const v = m.velocity(k, c);
        const dx = v.dk / m.limits.k * plot.width, dy = -v.dc / m.limits.c * plot.height;
        const length = Math.hypot(dx, dy);
        if (length > .001) out.push({
          x: X(k), y: Y(c), ux: dx / length, uy: dy / length,
          duration: Math.max(1.1, Math.min(3.2, 42 / (length + 5))),
          delay: -(((i * 7 + j * 5) % 13) / 13) * 2.7,
        });
      }
    }
    return out;
  }
  // Small arrow (shaft and open head) pointing along the flow, drawn around the origin.
  const pt = (a, along, across) => `${(along * a.ux - across * a.uy).toFixed(2)},${(along * a.uy + across * a.ux).toFixed(2)}`;
  const head = a => `M${pt(a, -4.2, 0)} L${pt(a, 4.2, 0)} M${pt(a, 1.4, 2.45)} L${pt(a, 4.2, 0)} L${pt(a, 1.4, -2.45)}`;

  // The start is stored relative to the steady state so it survives parameter changes.
  let kRel = .3, cRel = null;
  let year = 0;
  let playing = false;
  let speed = 4;
  let drag = false;
  let chart;
  let lastFrame = 0;
  let k0, c0, result, position, visible, markerC, plotK, plotC;
  $: k0 = kRel * m.steady.k;
  $: c0 = cRel === null ? m.saddleConsumption(k0) : cRel * m.steady.c;
  $: result = m.simulate(k0, c0, cRel === null);
  $: position = atYear(result.trajectory, Number(year));
  $: visible = result.trajectory.filter(p => p.t <= Number(year) && p.c !== null);
  // Marginal product of capital at the current point.
  $: mpk = params.alpha * params.A * position.k ** (params.alpha - 1);
  $: markerC = position.c === null ? result.exhaustionC : position.c;
  $: plotK = k => Math.max(plot.left, Math.min(plot.left + plot.width, X(k)));
  $: plotC = c => Math.max(plot.top, Math.min(plot.top + plot.height, Y(c)));

  function atYear(points, t) {
    if (t >= points[points.length - 1].t) return points[points.length - 1];
    let lo = 0, hi = points.length - 1;
    while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (points[mid].t <= t) lo = mid; else hi = mid; }
    const a = points[lo], b = points[hi], w = (t - a.t) / (b.t - a.t);
    return { t, k: a.k + w * (b.k - a.k), c: a.c === null || b.c === null ? null : a.c + w * (b.c - a.c) };
  }
  function choose(k, c, stable = false) {
    playing = false; year = 0;
    // k stays just above 0, where the marginal product is infinite; c may sit exactly on the axis.
    kRel = Math.max(1e-4 * m.limits.k, Math.min(m.limits.k, k)) / m.steady.k;
    cRel = stable ? null : Math.max(0, Math.min(m.limits.c, c)) / m.steady.c;
  }
  function setParam(key, value) {
    playing = false; year = 0;
    params = { ...params, [key]: value };
  }
  let hover = null;
  function pointer(event) {
    if (!chart) return;
    const p = chart.createSVGPoint(); p.x = event.clientX; p.y = event.clientY;
    const q = p.matrixTransform(chart.getScreenCTM().inverse());
    const inside = q.x >= plot.left && q.x <= plot.left + plot.width && q.y >= plot.top && q.y <= plot.top + plot.height;
    const k = (q.x - plot.left) / plot.width * m.limits.k, c = (plot.top + plot.height - q.y) / plot.height * m.limits.c;
    // Hover readout of the coordinates under the cursor; dragging also moves the start.
    hover = inside ? { x: q.x, y: q.y, k, c } : null;
    if (drag) choose(k, c);
  }
  function frame(now) {
    if (playing && lastFrame) {
      year = Math.min(100, Number(year) + Math.min((now - lastFrame) / 1000, .1) * Number(speed));
      if (year >= 100) playing = false;
    }
    lastFrame = now;
    animationId = requestAnimationFrame(frame);
  }
  let animationId;
  onMount(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) chart?.pauseAnimations();
    animationId = requestAnimationFrame(frame);
    return () => cancelAnimationFrame(animationId);
  });
</script>

<section class="phase-page">
  <div class="hero"><h1>Phase diagram</h1></div>

  <div class="visual-shell">
    <div class="controls">
    <h2 class="panel-head">Parameters</h2>
    <div class="fixed">{#each fixed as p}<span>{@html p.tex} = <strong>{Number(params[p.key]).toFixed(p.digits)}</strong></span>{/each}</div>
    <div class="params">{#each sliders as s}<label><span><em>{s.label}</em><strong>{Number(params[s.key]).toFixed(s.step < .01 ? 3 : 2)}</strong></span><input aria-label={`Parameter ${s.key}`} type="range" min={s.min} max={s.max} step={s.step} value={params[s.key]} on:input={event => setParam(s.key, Number(event.currentTarget.value))} /></label>{/each}</div>
    <div class="transport"><button class="play" on:click={() => { if (year >= 100) year = 0; playing = !playing; }} aria-label={playing ? 'Pause animation' : 'Play animation'}>{#if playing}<svg class="icon" viewBox="0 0 16 16" aria-hidden="true"><rect x="3.5" y="2.5" width="3" height="11" rx="1" /><rect x="9.5" y="2.5" width="3" height="11" rx="1" /></svg>{:else}<svg class="icon" viewBox="0 0 16 16" aria-hidden="true"><path d="M5 2.8 L13 8 L5 13.2 Z" /></svg>{/if}</button><label class="timeline"><span>Time</span><input aria-label="Year" type="range" min="0" max="100" step="0.1" bind:value={year} on:input={() => playing = false} /></label></div>
    <div class="year"><span>TIME <strong>{Math.floor(Math.min(100, Number(year)))}</strong></span><span class="row"><span><em>Capital</em> {@html texK} <strong>{position.k.toFixed(2)}</strong></span><span><em>Consumption</em> {@html texC} <strong>{position.c === null ? '-' : position.c.toFixed(2)}</strong></span></span><span><em>Output</em> {@html texF} <strong>{fmt(params.A * position.k ** params.alpha)}</strong></span><span>{@html texUse} <strong>{position.c === null ? '-' : fmt(params.delta * position.k + position.c)}</strong></span><span>{@html texFp} <strong>{fmt(mpk)}</strong></span><span>{@html texGap} <strong>{fmt(params.delta + params.rho)}</strong></span></div>
    <div class="buttons"><button class="snap" class:active={cRel === null} on:click={() => choose(k0, 0, true)}>Place on saddle path</button><button class="reset" on:click={() => { year = 0; playing = false; }}>Reset time</button></div>
    <label class="speed">Speed <select bind:value={speed} aria-label="Playback speed"><option value={0.5}>0.5 yr/s</option><option value={1}>1 yr/s</option><option value={2}>2 yr/s</option><option value={4}>4 yr/s</option><option value={8}>8 yr/s</option></select></label>
    <label class="speed"><input type="checkbox" bind:checked={showQuads} /> Highlight quadrants</label>
    <label class="speed"><input type="checkbox" bind:checked={showVectors} /> Show vectors</label>
    {#if result.depletionTime !== null && Number(year) >= result.depletionTime}<span class="status-note">Capital exhausted at year {result.depletionTime.toFixed(1)} · consumption is no longer defined</span>{:else if position.k > m.limits.k || position.c > m.limits.c}<span class="status-note">Economy is beyond the visible chart</span>{/if}
    <span class="hint">Click or drag on the plot to set the start</span>
    </div>
    <svg bind:this={chart} viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Interactive phase diagram with capital on the horizontal axis, consumption on the vertical axis, vector field, nullclines, saddle path and moving economy marker" on:pointermove={pointer} on:pointerup={() => drag = false} on:pointercancel={() => drag = false} on:pointerleave={() => hover = null}>
      <defs><clipPath id="phase-clip"><rect x={plot.left} y={plot.top} width={plot.width} height={plot.height} /></clipPath><marker id="phase-arrow" markerWidth="3.5" markerHeight="3.5" refX="2.8" refY="1.75" orient="auto"><path d="M0,0 L3.5,1.75 L0,3.5" fill="none" stroke="#111318" stroke-width="1.3" /></marker></defs>
      <rect x={plot.left} y={plot.top} width={plot.width} height={plot.height} fill="#fbfcff" />
      {#each ticksK as tick}<line x1={X(tick)} x2={X(tick)} y1={plot.top} y2={plot.top + plot.height} class="grid" /><text x={X(tick)} y={plot.top + plot.height + 22} class="tick" text-anchor="middle">{tick}</text>{/each}
      {#each ticksC as tick}<line x1={plot.left} x2={plot.left + plot.width} y1={Y(tick)} y2={Y(tick)} class="grid" /><text x={plot.left - 12} y={Y(tick) + 4} class="tick" text-anchor="end">{tick.toFixed(1)}</text>{/each}
      <g clip-path="url(#phase-clip)">
        {#if showQuads}{#each quads as q}<path d={path(q.poly) + ' Z'} fill={q.color} fill-opacity=".16" />{/each}{/if}
        {#if showVectors}{#each arrows as a}
          <line x1={a.x-4.55*a.ux} y1={a.y-4.55*a.uy} x2={a.x+4.55*a.ux} y2={a.y+4.55*a.uy} class="vector" marker-end="url(#phase-arrow)" />
          <path class="flow-arrow" d={head(a)} opacity="0">
            <animateTransform attributeName="transform" type="translate" from={`${a.x-5.0*a.ux} ${a.y-5.0*a.uy}`} to={`${a.x+5.0*a.ux} ${a.y+5.0*a.uy}`} dur={`${a.duration}s`} begin={`${a.delay}s`} repeatCount="indefinite" />
            <animate attributeName="opacity" values="0;.45;.45;0" keyTimes="0;.18;.78;1" dur={`${a.duration}s`} begin={`${a.delay}s`} repeatCount="indefinite" />
          </path>
        {/each}{/if}
        <path d={path(curve)} class="nullcline" />
        <line x1={X(m.steady.k)} x2={X(m.steady.k)} y1={plot.top} y2={plot.top+plot.height} class="consumption-line" />
        {#each arms as arm}<path d={arm} class="saddle" />{/each}
        {#if showQuads}{#each quads as q}<path d={cross(q)} fill="none" stroke={q.color} stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" />{/each}{/if}
        {#if visible.length > 1}<path d={path(visible)} class="trail" />{/if}
        <circle cx={X(k0)} cy={Y(c0)} r="5" fill="#fff" stroke="#191b20" stroke-width="2" />
        <circle cx={plotK(position.k)} cy={plotC(markerC)} r="14" fill="#171923" opacity=".12" />
        <circle cx={X(m.steady.k)} cy={Y(m.steady.c)} r="5" fill="#bf3441" stroke="#fff" stroke-width="1.5" />
        <circle cx={plotK(position.k)} cy={plotC(markerC)} r="7.5" fill="#111318" stroke="#fff" stroke-width="2" />
      </g>
      <rect x={plot.left} y={plot.top} width={plot.width} height={plot.height} fill="transparent" class="interaction" on:pointerdown={event => { drag = true; event.currentTarget.setPointerCapture(event.pointerId); pointer(event); }} on:pointerup={() => drag = false} />
      <rect x={plot.left} y={plot.top} width={plot.width} height={plot.height} class="frame" />
      {#if hover}
        <g class="hover" pointer-events="none">
          <line x1={plot.left} x2={plot.left + plot.width} y1={hover.y} y2={hover.y} /><line x1={hover.x} x2={hover.x} y1={plot.top} y2={plot.top + plot.height} />
          <text x={hover.x + (hover.x > plot.left + plot.width - 130 ? -10 : 10)} y={hover.y + (hover.y < plot.top + 30 ? 22 : -10)} text-anchor={hover.x > plot.left + plot.width - 130 ? 'end' : 'start'}>k = {hover.k.toFixed(2)}, c = {hover.c.toFixed(2)}</text>
        </g>
      {/if}
      <text x={plot.left+plot.width/2} y={H-8} class="axis-label" text-anchor="middle">Capital per worker, k</text>
      <text transform={`translate(19 ${plot.top+plot.height/2}) rotate(-90)`} class="axis-label" text-anchor="middle">Consumption per worker, c</text>
      <text x={X(m.steady.k)+9} y={plot.top+21} class="label blue">ċ = 0</text>
      <text x={X(.77 * m.limits.k)} y={Y(m.netOutput(.77 * m.limits.k))+26} class="label slate">k̇ = 0</text>
      <text x={X(.35 * m.steady.k)} y={Y(m.saddleConsumption(.35 * m.steady.k))+34} class="label">saddle path</text>
      <text x={X(m.steady.k)+14} y={Y(m.steady.c)-14} class="label red">steady state</text>
    </svg>
  </div>
</section>

<style>
  .phase-page { padding: 36px 0 10px; color: #1d263c; line-height: 1.5; }
  .hero { display: flex; align-items: baseline; flex-wrap: wrap; gap: 4px 16px; margin-bottom: 10px; }
  .hero h1 { font-size: calc(clamp(1.2rem, 2.25vw, 2.2rem) - 2pt); margin: 0; letter-spacing: -.04em; line-height: 1.1; }
  .visual-shell { display: grid; grid-template-columns: 320px minmax(0, 1fr); align-items: center; border: 1px solid #dce3f0; border-radius: 18px; box-shadow: 0 16px 45px rgba(37,58,102,.055); overflow: hidden; background: white; }
  .controls { display: grid; grid-template-columns: minmax(0, 1fr); gap: 14px; align-content: start; padding: 18px 18px 18px 22px; border-right: 1px solid #e6eaf1; }
  .controls input[type=range] { accent-color: #111318; }
  .params { display: grid; grid-template-columns: minmax(0, 1fr); gap: 12px; padding-bottom: 14px; border-bottom: 1px solid #e3e6ec; }
  .panel-head { margin: 0 0 -6px; font-size: 1.05rem; font-weight: 700; color: #111318; letter-spacing: 0; }
  .params label { display: grid; gap: 2px; color: #111318; font-size: .77rem; }
  .params label span { display: flex; align-items: baseline; gap: 6px; }
  .params em { font-style: italic; color: #111318; font-size: .95rem; }
  .params strong { margin-left: auto; color: #111318; font-size: .85rem; font-variant-numeric: tabular-nums; }
  .year { display: grid; gap: 4px; font-size: .76rem; color: #111318; letter-spacing: .11em; font-variant-numeric: tabular-nums; white-space: nowrap; }
  .year .row { display: flex; gap: 18px; }
  .year em { font-style: normal; letter-spacing: 0; font-size: .8rem; margin-right: 2px; }
  .year strong { color: #111318; font-size: 1.05rem; letter-spacing: -.03em; }
  .fixed { display: flex; gap: 22px; align-items: baseline; font-size: .85rem; }.fixed strong { font-weight: 600; margin-left: 2px; }
  svg { width: 100%; height: auto; max-height: calc(100vh - 185px); min-height: 300px; display: block; touch-action: none; }
  .grid { stroke: #edf1f8; stroke-width: 1; }
  .tick { font: 14px 'Source Sans Pro', sans-serif; fill: #111318; }
  .frame { fill: none; stroke: #8691a7; stroke-width: 1.5; pointer-events: none; }
  .axis-label { font: 16px 'Source Sans Pro', sans-serif; fill: #111318; }
  .vector { stroke: #111318; stroke-width: 1.35; opacity: .35; }
  .flow-arrow { fill: none; stroke: #111318; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; pointer-events: none; }
  .nullcline { fill: none; stroke: #6e8699; stroke-width: 3.2; }
  .consumption-line { stroke: #7388a5; stroke-width: 2.5; stroke-dasharray: 7 6; }
  .saddle { fill: none; stroke: #111318; stroke-width: 4; opacity: .9; }
  .trail { fill: none; stroke: #e49350; stroke-width: 4; stroke-linecap: round; stroke-linejoin: round; }
  .label { font: 600 16px 'Source Sans Pro', sans-serif; paint-order: stroke; stroke: #fbfcff; stroke-width: 5; }
  .label.blue { fill: #184199; }.label.slate { fill: #60758b; }.label.red { fill: #bf3441; }
  .interaction { cursor: crosshair; }
  .hover line { stroke: #111318; stroke-width: 1; stroke-dasharray: 3 4; opacity: .45; }
  .hover text { font: 600 14px 'Source Sans Pro', sans-serif; fill: #111318; paint-order: stroke; stroke: #fbfcff; stroke-width: 4; }
  .transport { display: flex; align-items: center; gap: 12px; }
  .buttons { display: flex; gap: 8px; }
  .hint { color: #111318; font-size: .72rem; font-style: italic; }
  button { transition: transform .18s ease, background .18s ease, color .18s ease, border-color .18s ease; }.transport button:hover { transform: translateY(-2px); }
  .play { border: 0; background: #111318; color: white; width: 40px; height: 40px; flex: 0 0 auto; border-radius: 50%; display: grid; place-items: center; padding: 0; }
  .play .icon { width: 16px; height: 16px; min-height: 0; fill: white; }
  .play:focus { outline: none; }.play:focus-visible { outline: 2px solid #111318; outline-offset: 3px; }
  .timeline { flex: 1; display: flex; align-items: center; gap: 13px; color: #111318; font-size: .75rem; white-space: nowrap; }.timeline input { flex: 1; min-width: 0; }
  .reset { border: 1px solid #d8dfed; background: white; border-radius: 8px; padding: 7px 12px; font-size: .75rem; white-space: nowrap; }
  .snap { border: 1px solid #c9ccd3; background: #fff; color: #111318; border-radius: 999px; font-size: .74rem; padding: 7px 12px; white-space: nowrap; }.snap.active { background: #eceef2; border-color: #9ea3ad; }
  .speed { display: flex; align-items: center; gap: 7px; font-size: .75rem; color: #111318; }.speed select { width: auto; border-radius: 7px; background: white; border-color: #d8dfed; color: #1d263c; font-size: .75rem; }
  .status-note { display: block; color: #9b4a4f; font-size: .72rem; line-height: 1.4; }
  @media(max-width:850px) { .visual-shell { grid-template-columns: 1fr; }.controls { border-right: 0; border-bottom: 1px solid #e6eaf1; } }
  @media(max-width:550px) { .label { font-size: 14px; } }
  @media(prefers-reduced-motion:reduce) { button { transition: none; } }
</style>
