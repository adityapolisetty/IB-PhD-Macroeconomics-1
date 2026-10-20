<script>
  import { onMount } from 'svelte';
  import { ticks } from 'd3';
  import { renderToString } from 'katex';
  import { makePhase } from '../lib/phase.js';
  import { growthParameters } from '../lib/models.js';

  const W = 960, H = 540;
  const plot = { left: 74, top: 14, width: 860, height: 470 };
  const sliders = [
    { key: 'alpha', label: 'α', min: .2, max: .5, step: .01 },
    { key: 'A', label: 'A', min: .5, max: 2, step: .05 },
    { key: 'delta', label: 'δ', min: .01, max: .15, step: .005 },
    { key: 'rho', label: 'ρ', min: .01, max: .1, step: .005 },
    { key: 'sigma', label: 'σ', min: .5, max: 5, step: .1 },
  ];
  const texK = renderToString('k');
  const texC = renderToString('c');
  let params = { ...growthParameters };
  let m, X, Y, path, curve, arms, ticksK, ticksC, arrows;
  $: m = makePhase(params);
  $: X = k => plot.left + k / m.limits.k * plot.width;
  $: Y = c => plot.top + plot.height - c / m.limits.c * plot.height;
  $: path = points => points.map((p, i) => `${i ? 'L' : 'M'}${X(p.k).toFixed(2)},${Y(p.c).toFixed(2)}`).join(' ');
  $: curve = Array.from({ length: 321 }, (_, i) => ({ k: m.limits.k * i / 320, c: m.netOutput(m.limits.k * i / 320) }));
  $: arms = [m.saddleArms.left, m.saddleArms.right].map(points => path([...points].reverse()));
  $: ticksK = ticks(0, m.limits.k, 6);
  $: ticksC = ticks(0, m.limits.c, 6);
  $: arrows = field(m, X, Y);

  // Unit direction of motion on an evenly spaced 14 x 7 grid, with a staggered flow timing per arrow.
  function field(m, X, Y) {
    const out = [];
    for (let i = 0; i < 14; i++) {
      for (let j = 0; j < 7; j++) {
        const k = m.limits.k * (i + .5) / 14, c = m.limits.c * (j + .5) / 7;
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
  // Small filled arrowhead pointing along the flow, drawn around the origin.
  const head = a => `M${(5 * a.ux).toFixed(2)},${(5 * a.uy).toFixed(2)} L${(-4 * a.ux - 3.5 * a.uy).toFixed(2)},${(-4 * a.uy + 3.5 * a.ux).toFixed(2)} L${(-4 * a.ux + 3.5 * a.uy).toFixed(2)},${(-4 * a.uy - 3.5 * a.ux).toFixed(2)} Z`;

  // The start is stored relative to the steady state so it survives parameter changes.
  let kRel = .5, cRel = null;
  let year = 0;
  let playing = false;
  let speed = 0.5;
  let drag = false;
  let chart;
  let lastFrame = 0;
  let k0, c0, result, position, visible, markerC, plotK, plotC;
  $: k0 = kRel * m.steady.k;
  $: c0 = cRel === null ? m.saddleConsumption(k0) : cRel * m.steady.c;
  $: result = m.simulate(k0, c0, cRel === null);
  $: position = atYear(result.trajectory, Number(year));
  $: visible = result.trajectory.filter(p => p.t <= Number(year) && p.c !== null);
  $: markerC = position.c === null ? result.exhaustionC : position.c;
  $: plotK = k => Math.max(plot.left + 9, Math.min(plot.left + plot.width - 9, X(k)));
  $: plotC = c => Math.max(plot.top + 9, Math.min(plot.top + plot.height - 9, Y(c)));

  function atYear(points, t) {
    if (t >= points[points.length - 1].t) return points[points.length - 1];
    let lo = 0, hi = points.length - 1;
    while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (points[mid].t <= t) lo = mid; else hi = mid; }
    const a = points[lo], b = points[hi], w = (t - a.t) / (b.t - a.t);
    return { t, k: a.k + w * (b.k - a.k), c: a.c === null || b.c === null ? null : a.c + w * (b.c - a.c) };
  }
  function choose(k, c, stable = false) {
    playing = false; year = 0;
    kRel = Math.max(.02 * m.limits.k, Math.min(.98 * m.limits.k, k)) / m.steady.k;
    cRel = stable ? null : Math.max(.02 * m.limits.c, Math.min(.98 * m.limits.c, c)) / m.steady.c;
  }
  function setParam(key, value) {
    playing = false; year = 0;
    params = { ...params, [key]: value };
  }
  function pointer(event) {
    if (!drag || !chart) return;
    const p = chart.createSVGPoint(); p.x = event.clientX; p.y = event.clientY;
    const q = p.matrixTransform(chart.getScreenCTM().inverse());
    choose((q.x - plot.left) / plot.width * m.limits.k, (plot.top + plot.height - q.y) / plot.height * m.limits.c);
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
  <div class="hero"><h1>Phase diagram - Neo-classical growth</h1></div>

  <div class="visual-shell">
    <div class="controls">
    <div class="params">{#each sliders as s}<label><span><em>{s.label}</em><strong>{Number(params[s.key]).toFixed(s.step < .01 ? 3 : 2)}</strong></span><input aria-label={`Parameter ${s.key}`} type="range" min={s.min} max={s.max} step={s.step} value={params[s.key]} on:input={event => setParam(s.key, Number(event.currentTarget.value))} /></label>{/each}</div>
    <div class="transport"><button class="play" on:click={() => { if (year >= 100) year = 0; playing = !playing; }} aria-label={playing ? 'Pause animation' : 'Play animation'}>{playing ? 'Ⅱ' : '▶'}</button><label class="timeline"><span>Time</span><input aria-label="Year" type="range" min="0" max="100" step="0.1" bind:value={year} on:input={() => playing = false} /></label></div>
    <div class="year"><span>TIME <strong>{Math.floor(Math.min(100, Number(year)))}</strong></span><span>{@html texK} <strong>{position.k.toFixed(2)}</strong></span><span>{@html texC} <strong>{position.c === null ? '-' : position.c.toFixed(2)}</strong></span></div>
    <div class="buttons"><button class="snap" class:active={cRel === null} on:click={() => choose(k0, 0, true)}>Place on saddle path</button><button class="reset" on:click={() => { year = 0; playing = false; }}>Reset time</button></div>
    <label class="speed">Speed <select bind:value={speed} aria-label="Playback speed"><option value={0.5}>0.5 yr/s</option><option value={1}>1 yr/s</option><option value={2}>2 yr/s</option><option value={4}>4 yr/s</option></select></label>
    {#if result.depletionTime !== null && Number(year) >= result.depletionTime}<span class="status-note">Capital exhausted at year {result.depletionTime.toFixed(1)} · consumption is no longer defined</span>{:else if position.k > m.limits.k || position.c > m.limits.c}<span class="status-note">Economy is beyond the visible chart</span>{/if}
    <span class="hint">Click or drag on the plot to set the start</span>
    </div>
    <svg bind:this={chart} viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Interactive phase diagram with capital on the horizontal axis, consumption on the vertical axis, vector field, nullclines, saddle path and moving economy marker" on:pointermove={pointer} on:pointerup={() => drag = false} on:pointercancel={() => drag = false}>
      <defs><clipPath id="phase-clip"><rect x={plot.left} y={plot.top} width={plot.width} height={plot.height} /></clipPath><marker id="phase-arrow" markerWidth="5" markerHeight="5" refX="4" refY="2.5" orient="auto"><path d="M0,0 L5,2.5 L0,5" fill="none" stroke="#8793bd" stroke-width="1.3" /></marker></defs>
      <rect x={plot.left} y={plot.top} width={plot.width} height={plot.height} fill="#fbfcff" />
      {#each ticksK as tick}<line x1={X(tick)} x2={X(tick)} y1={plot.top} y2={plot.top + plot.height} class="grid" /><text x={X(tick)} y={plot.top + plot.height + 22} class="tick" text-anchor="middle">{tick}</text>{/each}
      {#each ticksC as tick}<line x1={plot.left} x2={plot.left + plot.width} y1={Y(tick)} y2={Y(tick)} class="grid" /><text x={plot.left - 12} y={Y(tick) + 4} class="tick" text-anchor="end">{tick.toFixed(1)}</text>{/each}
      <g clip-path="url(#phase-clip)">
        {#each arrows as a}
          <line x1={a.x-6.5*a.ux} y1={a.y-6.5*a.uy} x2={a.x+6.5*a.ux} y2={a.y+6.5*a.uy} class="vector" marker-end="url(#phase-arrow)" />
          <path class="flow-arrow" d={head(a)} opacity="0">
            <animateTransform attributeName="transform" type="translate" from={`${a.x-6.5*a.ux} ${a.y-6.5*a.uy}`} to={`${a.x+6.5*a.ux} ${a.y+6.5*a.uy}`} dur={`${a.duration}s`} begin={`${a.delay}s`} repeatCount="indefinite" />
            <animate attributeName="opacity" values="0;.95;.95;0" keyTimes="0;.18;.78;1" dur={`${a.duration}s`} begin={`${a.delay}s`} repeatCount="indefinite" />
          </path>
        {/each}
        <path d={path(curve)} class="nullcline" />
        <line x1={X(m.steady.k)} x2={X(m.steady.k)} y1={plot.top} y2={plot.top+plot.height} class="consumption-line" />
        {#each arms as arm}<path d={arm} class="saddle" />{/each}
        {#if visible.length > 1}<path d={path(visible)} class="trail" />{/if}
        <circle cx={X(k0)} cy={Y(c0)} r="5" fill="#fff" stroke="#191b20" stroke-width="2" />
        <circle cx={plotK(position.k)} cy={plotC(markerC)} r="14" fill="#171923" opacity=".12" />
        <circle cx={X(m.steady.k)} cy={Y(m.steady.c)} r="10" fill="#d43a48" stroke="#fff" stroke-width="2" />
        <circle cx={plotK(position.k)} cy={plotC(markerC)} r="7.5" fill="#111318" stroke="#fff" stroke-width="2" />
      </g>
      <rect x={plot.left} y={plot.top} width={plot.width} height={plot.height} fill="transparent" class="interaction" on:pointerdown={event => { drag = true; event.currentTarget.setPointerCapture(event.pointerId); pointer(event); }} on:pointerup={() => drag = false} />
      <rect x={plot.left} y={plot.top} width={plot.width} height={plot.height} class="frame" />
      <text x={plot.left+plot.width/2} y={H-8} class="axis-label" text-anchor="middle">Capital per worker, k</text>
      <text transform={`translate(19 ${plot.top+plot.height/2}) rotate(-90)`} class="axis-label" text-anchor="middle">Consumption per worker, c</text>
      <text x={X(m.steady.k)+9} y={plot.top+21} class="label blue">ċ = 0</text>
      <text x={X(.77 * m.limits.k)} y={Y(m.netOutput(.77 * m.limits.k))+26} class="label slate">k̇ = 0</text>
      <text x={X(.35 * m.steady.k)} y={Y(m.saddleConsumption(.35 * m.steady.k))+34} class="label blue">saddle path</text>
      <text x={X(m.steady.k)+14} y={Y(m.steady.c)-14} class="label red">steady state</text>
    </svg>
  </div>
</section>

<style>
  .phase-page { padding: 14px 0 10px; color: #1d263c; line-height: 1.5; }
  .hero { display: flex; align-items: baseline; flex-wrap: wrap; gap: 4px 16px; margin-bottom: 10px; }
  .hero h1 { font-size: calc(clamp(1.2rem, 2.25vw, 2.2rem) - 2pt); margin: 0; letter-spacing: -.04em; line-height: 1.1; }
  .visual-shell { display: grid; grid-template-columns: 320px minmax(0, 1fr); align-items: center; border: 1px solid #dce3f0; border-radius: 18px; box-shadow: 0 16px 45px rgba(37,58,102,.055); overflow: hidden; background: white; }
  .controls { display: grid; grid-template-columns: minmax(0, 1fr); gap: 14px; align-content: start; padding: 18px 18px 18px 22px; border-right: 1px solid #e6eaf1; }
  .controls input[type=range] { accent-color: #111318; }
  .params { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px 18px; }
  .params label { display: grid; gap: 2px; color: #64708a; font-size: .77rem; }
  .params label span { display: flex; align-items: baseline; gap: 6px; }
  .params em { font-style: italic; color: #3b4963; font-size: .95rem; }
  .params strong { margin-left: auto; color: #111318; font-size: .85rem; font-variant-numeric: tabular-nums; }
  .year { display: flex; align-items: baseline; gap: 18px; font-size: .76rem; color: #687590; letter-spacing: .11em; font-variant-numeric: tabular-nums; white-space: nowrap; }
  .year strong { color: #111318; font-size: 1.15rem; letter-spacing: -.03em; min-width: 3.2ch; }
  svg { width: 100%; height: auto; max-height: calc(100vh - 150px); min-height: 300px; display: block; touch-action: none; }
  .grid { stroke: #edf1f8; stroke-width: 1; }
  .tick { font: 14px 'Source Sans Pro', sans-serif; fill: #8790a4; }
  .frame { fill: none; stroke: #8691a7; stroke-width: 1.5; pointer-events: none; }
  .axis-label { font: 16px 'Source Sans Pro', sans-serif; fill: #4f5a70; }
  .vector { stroke: #98a5c7; stroke-width: 1.35; opacity: .74; }
  .flow-arrow { fill: #3348dc; pointer-events: none; }
  .nullcline { fill: none; stroke: #6e8699; stroke-width: 3.2; }
  .consumption-line { stroke: #7388a5; stroke-width: 2.5; stroke-dasharray: 7 6; }
  .saddle { fill: none; stroke: #0000cd; stroke-width: 4; opacity: .9; }
  .trail { fill: none; stroke: #e49350; stroke-width: 4; stroke-linecap: round; stroke-linejoin: round; }
  .label { font: 600 16px 'Source Sans Pro', sans-serif; paint-order: stroke; stroke: #fbfcff; stroke-width: 5; }
  .label.blue { fill: #0000cd; }.label.slate { fill: #60758b; }.label.red { fill: #d43a48; }
  .interaction { cursor: crosshair; }
  .transport { display: flex; align-items: center; gap: 12px; }
  .buttons { display: flex; gap: 8px; }
  .hint { color: #8790a4; font-size: .72rem; font-style: italic; }
  button { transition: transform .18s ease, background .18s ease, color .18s ease, border-color .18s ease; }.transport button:hover { transform: translateY(-2px); }
  .play { border: 0; background: #111318; color: white; width: 40px; height: 40px; flex: 0 0 auto; border-radius: 50%; font-size: .95rem; padding-left: 4px; }
  .timeline { flex: 1; display: flex; align-items: center; gap: 13px; color: #5d6880; font-size: .75rem; white-space: nowrap; }.timeline input { flex: 1; min-width: 0; }
  .reset { border: 1px solid #d8dfed; background: white; border-radius: 8px; padding: 7px 12px; font-size: .75rem; white-space: nowrap; }
  .snap { border: 1px solid #c9ccd3; background: #fff; color: #111318; border-radius: 999px; font-size: .74rem; padding: 7px 12px; white-space: nowrap; }.snap.active { background: #eceef2; border-color: #9ea3ad; }
  .speed { display: flex; align-items: center; gap: 7px; font-size: .75rem; color: #5d6880; }.speed select { width: auto; border-radius: 7px; background: white; border-color: #d8dfed; color: #1d263c; font-size: .75rem; }
  .status-note { display: block; color: #9b4a4f; font-size: .72rem; line-height: 1.4; }
  @media(max-width:850px) { .visual-shell { grid-template-columns: 1fr; }.controls { border-right: 0; border-bottom: 1px solid #e6eaf1; } }
  @media(max-width:550px) { .label { font-size: 14px; } }
  @media(prefers-reduced-motion:reduce) { button { transition: none; } }
</style>
