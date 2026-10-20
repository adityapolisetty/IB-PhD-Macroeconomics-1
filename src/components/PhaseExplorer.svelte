<script>
  import { onMount } from 'svelte';
  import { steady, limits, netOutput, velocity, saddleArms, saddleConsumption, simulate } from '../lib/phase.js';
  export let film;

  const W = 960, H = 590;
  const plot = { left: 74, top: 42, width: 826, height: 480 };
  const X = k => plot.left + k / limits.k * plot.width;
  const Y = c => plot.top + plot.height - c / limits.c * plot.height;
  const path = points => points.map((p, i) => `${i ? 'L' : 'M'}${X(p.k).toFixed(2)},${Y(p.c).toFixed(2)}`).join(' ');
  const curve = Array.from({ length: 321 }, (_, i) => ({ k: limits.k * i / 320, c: netOutput(limits.k * i / 320) }));
  const arms = [saddleArms.left, saddleArms.right].map(points => path([...points].reverse()));
  const ticksK = [0, 4, 8, 12, 16, 19];
  const ticksC = [0, .5, 1, 1.5, 2, 2.5];
  const arrows = [];
  for (let k = 1.05; k <= 18.6; k += 1.35) {
    for (let c = .24; c <= 2.38; c += .32) {
      const v = velocity(k, c);
      const dx = v.dk / limits.k * plot.width;
      const dy = -v.dc / limits.c * plot.height;
      const length = Math.hypot(dx, dy);
      if (length > .001) arrows.push({ x: X(k), y: Y(c), dx: 13 * dx / length, dy: 13 * dy / length });
    }
  }
  const presets = [
    { label: 'Upper left', k: 5.1, c: 2.12 },
    { label: 'Lower left', k: 5.1, c: .64 },
    { label: 'Upper right', k: 12.4, c: 2.20 },
    { label: 'Lower right', k: 12.4, c: .70 },
  ];
  let k0 = 4.25;
  let c0 = saddleConsumption(k0);
  let onSaddle = true;
  let year = 0;
  let playing = false;
  let speed = 8;
  let drag = false;
  let chart;
  let lastFrame = 0;
  let result;
  let position;
  let visible;
  let local;
  $: result = simulate(Number(k0), Number(c0), onSaddle);
  $: position = atYear(result.trajectory, Number(year));
  $: visible = result.trajectory.filter(p => p.t <= Number(year));
  $: local = velocity(position.k, position.c);

  function atYear(points, t) {
    if (t >= points[points.length - 1].t) return points[points.length - 1];
    let lo = 0, hi = points.length - 1;
    while (hi - lo > 1) { const m = (lo + hi) >> 1; if (points[m].t <= t) lo = m; else hi = m; }
    const a = points[lo], b = points[hi], w = (t - a.t) / (b.t - a.t);
    return { t, k: a.k + w * (b.k - a.k), c: a.c + w * (b.c - a.c) };
  }
  function choose(k, c, stable = false) {
    playing = false; year = 0;
    k0 = Math.max(.25, Math.min(limits.k - .3, k));
    c0 = stable ? saddleConsumption(k0) : Math.max(.05, Math.min(limits.c - .05, c));
    onSaddle = stable;
  }
  function pointer(event) {
    if (!drag || !chart) return;
    const p = chart.createSVGPoint(); p.x = event.clientX; p.y = event.clientY;
    const q = p.matrixTransform(chart.getScreenCTM().inverse());
    choose((q.x - plot.left) / plot.width * limits.k, (plot.top + plot.height - q.y) / plot.height * limits.c);
    drag = true;
  }
  function frame(now) {
    if (playing && lastFrame) {
      const limit = result.exitTime ?? 100;
      year = Math.min(limit, Number(year) + Math.min((now - lastFrame) / 1000, .1) * speed);
      if (year >= limit) playing = false;
    }
    lastFrame = now;
    animationId = requestAnimationFrame(frame);
  }
  let animationId;
  onMount(() => { animationId = requestAnimationFrame(frame); return () => cancelAnimationFrame(animationId); });
  $: outcomeText = onSaddle ? 'On the saddle path: both variables approach the unique steady state.'
    : result.outcome === 'exhaustion' ? `This path heads toward capital exhaustion and leaves the visible frame after ${result.exitTime.toFixed(1)} years. It is infeasible.`
    : result.outcome === 'overaccumulation' ? `This path heads toward overaccumulation and leaves the visible frame after ${result.exitTime.toFixed(1)} years. It fails the transversality condition.`
    : 'This path has not exited the frame within 100 years. Its direction is shown by the local arrows.';
</script>

<section class="phase-page">
  <div class="hero">
    <div><p class="eyebrow">Chapter 03 / Neoclassical growth</p><h1>Where does the economy go?</h1></div>
    <p>The arrows show the local direction of motion. Place the black economy marker anywhere, or choose the saddle path, and follow the next 100 years.</p>
  </div>

  <div class="visual-shell">
    <div class="visual-heading"><span class="tag">THE PHASE PLANE</span><span class="year">YEAR <strong>{Math.min(100, Number(year)).toFixed(1)}</strong> <span>/ 100</span></span></div>
    <svg bind:this={chart} viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Interactive phase diagram with capital on the horizontal axis, consumption on the vertical axis, vector field, nullclines, saddle path and moving economy marker" on:pointermove={pointer} on:pointerup={() => drag = false} on:pointercancel={() => drag = false}>
      <defs><clipPath id="phase-clip"><rect x={plot.left} y={plot.top} width={plot.width} height={plot.height} /></clipPath><marker id="phase-arrow" markerWidth="5" markerHeight="5" refX="4" refY="2.5" orient="auto"><path d="M0,0 L5,2.5 L0,5" fill="none" stroke="#8793bd" stroke-width="1.3" /></marker></defs>
      <rect x={plot.left} y={plot.top} width={plot.width} height={plot.height} fill="#fbfcff" />
      {#each ticksK as tick}<line x1={X(tick)} x2={X(tick)} y1={plot.top} y2={plot.top + plot.height} class="grid" /><text x={X(tick)} y={plot.top + plot.height + 25} class="tick" text-anchor="middle">{tick}</text>{/each}
      {#each ticksC as tick}<line x1={plot.left} x2={plot.left + plot.width} y1={Y(tick)} y2={Y(tick)} class="grid" /><text x={plot.left - 15} y={Y(tick) + 4} class="tick" text-anchor="end">{tick.toFixed(1)}</text>{/each}
      <g clip-path="url(#phase-clip)">
        {#each arrows as a}<line x1={a.x-a.dx/2} y1={a.y-a.dy/2} x2={a.x+a.dx/2} y2={a.y+a.dy/2} class="vector" marker-end="url(#phase-arrow)" />{/each}
        <path d={path(curve)} class="nullcline" />
        <line x1={X(steady.k)} x2={X(steady.k)} y1={plot.top} y2={plot.top+plot.height} class="consumption-line" />
        {#each arms as arm}<path d={arm} class="saddle" />{/each}
        {#if visible.length > 1}<path d={path(visible)} class="trail" />{/if}
        <circle cx={X(k0)} cy={Y(c0)} r="5" fill="#fff" stroke="#191b20" stroke-width="2" />
        <circle cx={X(steady.k)} cy={Y(steady.c)} r="6" fill="#0000cd" stroke="#fff" stroke-width="2" />
        <circle cx={X(position.k)} cy={Y(position.c)} r="14" fill="#171923" opacity=".12" />
        <circle cx={X(position.k)} cy={Y(position.c)} r="7.5" fill="#111318" stroke="#fff" stroke-width="2" />
      </g>
      <rect x={plot.left} y={plot.top} width={plot.width} height={plot.height} fill="transparent" class="interaction" on:pointerdown={event => { drag = true; event.currentTarget.setPointerCapture(event.pointerId); pointer(event); }} on:pointerup={() => drag = false} />
      <line x1={plot.left} y1={plot.top+plot.height} x2={plot.left+plot.width} y2={plot.top+plot.height} class="axis" /><line x1={plot.left} y1={plot.top} x2={plot.left} y2={plot.top+plot.height} class="axis" />
      <text x={plot.left+plot.width/2} y={H-12} class="axis-label" text-anchor="middle">Capital per worker, k</text>
      <text transform={`translate(19 ${plot.top+plot.height/2}) rotate(-90)`} class="axis-label" text-anchor="middle">Consumption per worker, c</text>
      <text x={X(steady.k)+9} y={plot.top+21} class="label blue">ċ = 0</text>
      <text x={X(15)} y={Y(netOutput(15))+26} class="label slate">k̇ = 0</text>
      <text x={X(3.0)} y={Y(saddleConsumption(3.0))+34} class="label blue">saddle path</text>
      <text x={X(steady.k)+12} y={Y(steady.c)-12} class="label blue">steady state</text>
    </svg>
    <div class="legend"><span><i class="legend-arrow">↗</i> instantaneous motion</span><span><i class="legend-line grey"></i> k̇ = 0</span><span><i class="legend-line dash"></i> ċ = 0</span><span><i class="legend-line blue"></i> saddle path</span><span><i class="legend-dot"></i> economy</span></div>
  </div>

  <div class="transport"><button class="play" on:click={() => { if (year >= (result.exitTime ?? 100)) year = 0; playing = !playing; }} aria-label={playing ? 'Pause animation' : 'Play animation'}>{playing ? 'Ⅱ' : '▶'}</button><label class="timeline"><span>Time</span><input aria-label="Year" type="range" min="0" max="100" step="0.1" bind:value={year} on:input={() => playing = false} /><span>100 years</span></label><button class="reset" on:click={() => { year = 0; playing = false; }}>Reset time</button><label class="speed">Speed <select bind:value={speed} aria-label="Playback speed"><option value={4}>4 yr/s</option><option value={8}>8 yr/s</option><option value={16}>16 yr/s</option></select></label></div>
  <div class="controls-panel"><div class="presets"><span class="panel-label">START IN A REGION</span><div class="preset-buttons">{#each presets as preset}<button on:click={() => choose(preset.k, preset.c)}>{preset.label}</button>{/each}<button class:active={onSaddle} on:click={() => choose(k0, saddleConsumption(k0), true)}>On saddle path</button></div></div><div class="state"><span class="panel-label">CURRENT STATE</span><div class="state-values"><span>k <strong>{position.k.toFixed(2)}</strong></span><span>c <strong>{position.c.toFixed(2)}</strong></span><span>k̇ <strong>{local.dk >= 0 ? '+' : ''}{local.dk.toFixed(3)}</strong></span><span>ċ <strong>{local.dc >= 0 ? '+' : ''}{local.dc.toFixed(3)}</strong></span></div></div></div>
  <div class="explanation" aria-live="polite"><div><span class="panel-label">WHAT THIS PATH MEANS</span><p>{outcomeText}</p></div><div class="math"><span>k̇ = k<sup>1/3</sup> − c − 0.05k</span><span>ċ/c = (k<sup>−2/3</sup>/3 − 0.08)/2</span></div></div>
  <div class="reading"><div><h2>How to read the arrows</h2><p>Above the curved <em>k̇ = 0</em> line, consumption exceeds net output, so capital falls. Below it, capital rises. To the left of the vertical <em>ċ = 0</em> line, consumption rises; to the right, it falls. The direction at a point combines both signs.</p></div><div><h2>Why only one path converges</h2><p>Capital is inherited, while households choose initial consumption. For each starting capital stock, exactly one consumption choice lies on the blue saddle path. That path approaches <em>(k*, c*) ≈ ({steady.k.toFixed(2)}, {steady.c.toFixed(2)})</em>. A guess above it eventually exhausts capital; one below it overaccumulates.</p></div></div>
  <details class="film"><summary>Watch the Manim study clip <span>↗</span></summary><video controls preload="none" playsinline src={film} aria-label="Manim animation of the saddle path approaching the steady state"></video><p>The rendered film shows the geometry once; use the interactive diagram above to test your own starting point and scrub through model time.</p></details>
  <p class="footnote">Chapter 3 calibration: α = ⅓, A = 1, δ = 0.05, ρ = 0.03, σ = 2. Paths stop when they leave the visible feasible range; the chart edges are not equilibria. The saddle path is computed by integrating the nonlinear model backward from its stable eigenvector. The motion is a browser animation of the same equations, so the marker and year slider stay responsive.</p>
</section>

<style>
  .phase-page { padding: 44px 0 70px; color: #1d263c; line-height: 1.5; }
  .hero { display: grid; grid-template-columns: 1.2fr .8fr; align-items: end; gap: 40px; margin-bottom: 32px; }
  .hero h1 { font-size: clamp(2.4rem, 4.5vw, 4.4rem); margin: 8px 0 0; letter-spacing: -.055em; line-height: 1.03; }
  .hero p:last-child { max-width: 470px; margin: 0 0 4px; color: #5a6477; font-size: 1rem; }
  .visual-shell { border: 1px solid #dce3f0; border-radius: 18px; box-shadow: 0 16px 45px rgba(37,58,102,.055); overflow: hidden; background: white; }
  .visual-heading { display: flex; justify-content: space-between; align-items: center; padding: 18px 26px 0; }
  .tag,.panel-label { color: #66718a; font-size: .64rem; font-weight: 700; letter-spacing: .14em; }
  .year { font-size: .76rem; color: #687590; letter-spacing: .11em; font-variant-numeric: tabular-nums; }
  .year strong { color: #0000cd; font-size: 1.28rem; letter-spacing: -.03em; }
  svg { width: 100%; height: auto; display: block; touch-action: none; }
  .grid { stroke: #edf1f8; stroke-width: 1; }
  .tick { font: 14px 'Source Sans Pro', sans-serif; fill: #8790a4; }
  .axis { stroke: #8691a7; stroke-width: 1.5; }
  .axis-label { font: 16px 'Source Sans Pro', sans-serif; fill: #4f5a70; }
  .vector { stroke: #98a5c7; stroke-width: 1.35; opacity: .74; }
  .nullcline { fill: none; stroke: #6e8699; stroke-width: 3.2; }
  .consumption-line { stroke: #7388a5; stroke-width: 2.5; stroke-dasharray: 7 6; }
  .saddle { fill: none; stroke: #0000cd; stroke-width: 4; opacity: .9; }
  .trail { fill: none; stroke: #e49350; stroke-width: 4; stroke-linecap: round; stroke-linejoin: round; }
  .label { font: 600 16px 'Source Sans Pro', sans-serif; paint-order: stroke; stroke: #fbfcff; stroke-width: 5; }
  .label.blue { fill: #0000cd; }.label.slate { fill: #60758b; }
  .interaction { cursor: crosshair; }
  .legend { display: flex; flex-wrap: wrap; gap: 16px 26px; padding: 4px 28px 20px; font-size: .73rem; color: #64708a; }
  .legend span { display: inline-flex; gap: 9px; align-items: center; }.legend-arrow { font-size: 1.3rem; color: #8793bd; font-style: normal; line-height: 0; }
  .legend-line { display: inline-block; width: 22px; border-top: 3px solid; }.legend-line.grey { color: #6e8699; }.legend-line.dash { color: #7388a5; border-style: dashed; }.legend-line.blue { color: #0000cd; }.legend-dot { width: 11px; height: 11px; border-radius: 50%; background: #111318; }
  .transport { display: flex; align-items: center; gap: 19px; padding: 21px 3px; border-bottom: 1px solid #e6eaf1; }
  button { transition: transform .18s ease, background .18s ease, color .18s ease, border-color .18s ease; }.transport button:hover,.preset-buttons button:hover { transform: translateY(-2px); }
  .play { border: 0; background: #0000cd; color: white; width: 48px; height: 48px; flex: 0 0 auto; border-radius: 50%; font-size: 1rem; padding-left: 4px; }
  .timeline { flex: 1; display: flex; align-items: center; gap: 13px; color: #5d6880; font-size: .75rem; white-space: nowrap; }.timeline input { min-width: 0; }
  .reset { border: 1px solid #d8dfed; background: white; border-radius: 8px; padding: 8px 13px; font-size: .75rem; }
  .speed { display: flex; align-items: center; gap: 7px; font-size: .75rem; color: #5d6880; }.speed select { width: auto; border-radius: 7px; background: white; border-color: #d8dfed; color: #1d263c; font-size: .75rem; }
  .controls-panel { display: grid; grid-template-columns: 1.45fr 1fr; gap: 30px; padding: 25px 0; border-bottom: 1px solid #e6eaf1; }.preset-buttons { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }.preset-buttons button { border: 1px solid #d7deec; background: #fff; border-radius: 999px; font-size: .73rem; padding: 8px 12px; }.preset-buttons button.active { color: #0000cd; background: #eeeeff; border-color: #b8bafa; }
  .state-values { display: flex; flex-wrap: wrap; gap: 10px 20px; margin-top: 13px; font-size: .8rem; color: #738095; }.state-values strong { color: #1d263c; margin-left: 4px; font-weight: 600; font-variant-numeric: tabular-nums; }
  .explanation { display: grid; grid-template-columns: 1fr auto; gap: 25px; align-items: center; padding: 24px 26px; margin: 24px 0 42px; border-radius: 12px; background: #f1f3ff; border-left: 3px solid #0000cd; }.explanation p { margin: 7px 0 0; font-size: .91rem; }.math { display: grid; gap: 5px; color: #3f4b69; font-size: .77rem; white-space: nowrap; }
  .reading { display: grid; grid-template-columns: 1fr 1fr; gap: 50px; }.reading h2 { font-size: 1.5rem; margin-bottom: 10px; }.reading p { color: #566177; font-size: .89rem; line-height: 1.65; }.footnote { border-top: 1px solid #e6eaf1; margin-top: 22px; padding-top: 17px; color: #7a8496; font-size: .73rem; line-height: 1.6; }
  .film { margin-top: 25px; border: 1px solid #dce3f0; border-radius: 10px; padding: 14px 18px; }.film summary { font-size: .82rem; font-weight: 600; color: #0000cd; cursor: pointer; }.film summary span { float: right; }.film video { display: block; width: 100%; max-width: 920px; margin: 18px auto 0; border-radius: 8px; border: 1px solid #e4e8f2; }.film p { margin: 10px 0 0; color: #64708a; font-size: .75rem; }
  @media(max-width:850px) { .hero,.controls-panel,.explanation,.reading { grid-template-columns: 1fr; gap: 15px; }.hero { margin-bottom: 23px; }.phase-page { padding-top: 27px; }.math { white-space: normal; } }
  @media(max-width:550px) { .transport { flex-wrap: wrap; }.timeline { order: 3; flex-basis: 100%; }.speed { margin-left: auto; }.legend { gap: 8px 14px; padding: 4px 14px 14px; }.visual-heading { padding: 10px 14px 0; }.label { font-size: 14px; } }
  @media(prefers-reduced-motion:reduce) { button { transition: none; } }
</style>
