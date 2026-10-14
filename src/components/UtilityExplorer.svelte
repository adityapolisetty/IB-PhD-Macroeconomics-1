<script>
  import { oneVariable, oneVariableFacts } from '../lib/utility.js';
  import { withBase } from '../lib/lessons.js';
  import { renderToString } from 'katex';

  const oneFamilies = [
    { id: 'linear', name: 'Linear', tag: 'constant slope', parameter: 1, formula: 'u(c)=c', derivative: "u'(c)=1", second: "u''(c)=0" },
    { id: 'log', name: 'Logarithmic', tag: 'steep near zero', parameter: 1, formula: 'u(c)=\\ln c', derivative: "u'(c)=1/c", second: "u''(c)=-1/c^2" },
    { id: 'crra', name: 'CRRA', tag: 'curvature matters', parameter: 2, formula: 'u(c)=1-1/c\\quad(\\sigma=2)', derivative: "u'(c)=c^{-2}", second: "u''(c)=-2c^{-3}" },
    { id: 'cara', name: 'CARA', tag: 'finite ceiling', parameter: 0.6, formula: 'u(c)=(1-e^{-0.6c})/0.6', derivative: "u'(c)=e^{-0.6c}", second: "u''(c)=-0.6e^{-0.6c}" },
    { id: 'quadratic', name: 'Quadratic', tag: 'satiation', parameter: 0.35, formula: 'u(c)=c-0.175c^2', derivative: "u'(c)=1-0.35c", second: "u''(c)=-0.35" },
    { id: 'ak', name: 'AK production', tag: 'constant returns', parameter: 1, formula: 'f(k)=Ak', derivative: "f'(k)=A", second: "f''(k)=0" },
  ];
  let oneId = 'log';
  let c = 2;
  let productivity = 1;
  let oneVideo;
  let onePlaying = false;

  $: one = oneFamilies.find(f => f.id === oneId);
  $: isAk = oneId === 'ak';
  $: amountSymbol = isAk ? 'k' : 'c';
  $: oneValues = oneVariable(oneId, Number(c), isAk ? Number(productivity) : one.parameter);
  $: facts = oneVariableFacts(oneId, isAk ? Number(productivity) : one.parameter);
  $: oneSource = withBase(isAk ? `utility/one-ak-${Number(productivity).toFixed(2)}.mp4` : `utility/one-${oneId}.mp4`);
  $: oneFormula = renderToString(isAk ? `f(k)=${Number(productivity).toFixed(2)}k` : one.formula, { throwOnError: false });
  $: oneDerivative = renderToString(isAk ? `f'(k)=${Number(productivity).toFixed(2)}` : one.derivative, { throwOnError: false });
  $: oneSecond = renderToString(one.second, { throwOnError: false });
  $: growthRate = 0.2 * Number(productivity) - 0.25;

  function fmt(value) {
    if (!Number.isFinite(value)) return '∞';
    if (Math.abs(value) < 0.005) return '0.00';
    return value.toFixed(2).replace('-', '−');
  }
  function seekOne() {
    if (oneVideo && Number.isFinite(oneVideo.duration) && oneVideo.duration > 0) {
      oneVideo.currentTime = ((Number(c) - 0.5) / 7) * Math.max(0, oneVideo.duration - 0.04);
    }
  }
  function selectOne(id) {
    oneVideo?.pause();
    onePlaying = false;
    oneId = id;
  }
  function changeProductivity() { oneVideo?.pause(); onePlaying = false; }
  async function toggleOne() {
    if (!oneVideo) return;
    if (oneVideo.paused) {
      if (oneVideo.currentTime >= oneVideo.duration - 0.1) oneVideo.currentTime = 0;
      await oneVideo.play();
      onePlaying = true;
    } else { oneVideo.pause(); onePlaying = false; }
  }
  function syncOneFromVideo() {
    if (oneVideo && onePlaying && oneVideo.duration) c = Math.min(7.5, 0.5 + 7 * oneVideo.currentTime / oneVideo.duration);
  }
</script>

<section class="lab" id="function-explorer" aria-labelledby="one-heading">
  <div class="lab-head"><span class="chapter">One input / six functions</span><div><h2 id="one-heading">How the slope shapes the model</h2><p>The orange line is the tangent. For utility, its slope is marginal utility; for AK production, it is the marginal product of capital.</p></div></div>
  <div class="family-tabs" role="group" aria-label="Choose an economic function">
    {#each oneFamilies as family}
      <button type="button" class:active={oneId === family.id} aria-pressed={oneId === family.id} on:click={() => selectOne(family.id)}><span>{family.name}</span><small>{family.tag}</small></button>
    {/each}
  </div>
  <div class="stage-grid">
    <div class="stage-main">
      <div class="film-frame">
        <video bind:this={oneVideo} src={oneSource} muted playsinline preload="auto" aria-label={`Manim graph of ${one.name} and its moving tangent`} on:loadedmetadata={seekOne} on:timeupdate={syncOneFromVideo} on:ended={() => onePlaying = false}></video>
        <span class="film-tag">MANIM / TANGENT EXPLORER</span>
      </div>
      <div class="transport">
        <button class="play" type="button" on:click={toggleOne} aria-label={onePlaying ? 'Pause tangent animation' : 'Play tangent animation'}>{onePlaying ? '❚❚' : '▶'}</button>
        <label for="input-slider"><span>Move the tangent</span><strong>{amountSymbol} = {fmt(Number(c))}</strong></label>
        <input id="input-slider" aria-label={isAk ? 'Capital, k' : 'Consumption, c'} type="range" min="0.5" max="7.5" step="0.05" bind:value={c} on:input={seekOne} style={`--progress:${((Number(c) - 0.5) / 7) * 100}%`} />
        <div class="range-ends"><span>0.5</span><span>7.5</span></div>
      </div>
      {#if isAk}
        <div class="parameter-control">
          <label for="productivity-slider"><span>Productivity A · changes the line's slope</span><strong>{fmt(Number(productivity))}</strong></label>
          <input id="productivity-slider" aria-label="Productivity, A" type="range" min="0.5" max="2" step="0.25" bind:value={productivity} on:input={changeProductivity} style={`--progress:${((Number(productivity) - 0.5) / 1.5) * 100}%`} />
          <div class="range-ends"><span>0.50</span><span>2.00</span></div>
        </div>
      {/if}
      <p class="film-note">The animation is rendered with Manim. Dragging the slider selects its corresponding frame; the numbers alongside it are calculated from the function.</p>
    </div>
    <aside class="readout" aria-live="polite">
      <p class="readout-kicker">At your chosen {isAk ? 'capital stock' : 'consumption level'}</p>
      <div class="large-number"><span>{isAk ? 'Marginal product of capital' : 'Marginal utility'}</span><strong>{fmt(oneValues.marginal)}</strong><small>the tangent's slope, {isAk ? 'f′(k)' : 'u′(c)'}</small></div>
      <div class="readout-pair"><div><span>{isAk ? 'Output' : 'Utility'}</span><strong>{fmt(oneValues.value)}</strong></div><div><span>Second derivative</span><strong>{fmt(oneValues.second)}</strong></div></div>
      <div class="math-stack"><div><span>Function</span><div class="math">{@html oneFormula}</div></div><div><span>First derivative</span><div class="math">{@html oneDerivative}</div></div><div><span>Second derivative</span><div class="math">{@html oneSecond}</div></div></div>
      {#if isAk}<p class="growth-note"><strong>AK growth check</strong><span>With saving s = 0.20, depreciation δ = 0.20 and population growth n = 0.05:</span><span>k̇/k = sA − (δ + n) = <b>{growthRate > 0 ? '+' : ''}{fmt(growthRate)}</b></span><span>{growthRate > 0 ? 'Capital per worker grows.' : growthRate < 0 ? 'Capital per worker shrinks.' : 'Capital per worker stays constant.'}</span></p>{/if}
    </aside>
  </div>
  <div class="facts-grid"><div><span class="fact-label">Domain</span><strong>{facts.domain}</strong></div><div><span class="fact-label">Minimum</span><strong>{facts.minimum}</strong></div><div><span class="fact-label">Maximum</span><strong>{facts.maximum}</strong></div></div>
  <div class="interpretation"><p><strong>What to notice.</strong> {facts.shape}</p><p><strong>{isAk ? 'Why it matters in AK.' : 'Where it appears.'}</strong> {facts.use}</p></div>
</section>

<style>
  .lab { border-top: 1px solid var(--rule); padding: 76px 0 70px; }
  .lab-head { display: grid; grid-template-columns: 210px minmax(0, 1fr); gap: 36px; margin-bottom: 34px; }
  .chapter { font-size: .77rem; font-weight: 700; letter-spacing: .15em; text-transform: uppercase; color: var(--accent); padding-top: 8px; }
  h2 { font-size: clamp(2rem, 4vw, 3.4rem); line-height: 1.12; letter-spacing: -.045em; margin: 0 0 14px; max-width: 820px; }
  .lab-head p { max-width: 74ch; color: var(--muted); line-height: 1.55; margin: 0; }
  .family-tabs { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 8px; margin-bottom: 16px; }
  .family-tabs button { min-width: 0; text-align: left; padding: 13px 15px 11px; background: #f7f8fd; border: 1px solid #e1e3ee; border-radius: 8px; transition: border-color .2s, background .2s, transform .2s; }
  .family-tabs button:hover { border-color: var(--accent); transform: translateY(-2px); }
  .family-tabs button.active { background: var(--accent-soft); border-color: var(--accent); box-shadow: inset 0 3px 0 var(--accent); }
  .family-tabs span, .family-tabs small { display: block; white-space: normal; }
  .family-tabs span { font-size: .96rem; font-weight: 700; line-height: 1.2; }
  .family-tabs small { font-size: .75rem; line-height: 1.35; color: var(--muted); margin-top: 4px; }
  .stage-grid { display: grid; grid-template-columns: minmax(0, 1.7fr) minmax(270px, .75fr); gap: 16px; align-items: stretch; }
  .stage-main, .readout { border: 1px solid var(--rule); border-radius: 12px; background: #fff; overflow: hidden; }
  .film-frame { position: relative; background: #fff; aspect-ratio: 16 / 9; border-bottom: 1px solid var(--rule); }
  video { display: block; width: 100%; height: 100%; object-fit: contain; }
  .film-tag { position: absolute; top: 13px; left: 15px; pointer-events: none; background: rgba(255,255,255,.93); color: #50546b; font-size: .66rem; font-weight: 700; letter-spacing: .13em; padding: 5px 8px; border: 1px solid #dfe2ef; border-radius: 4px; }
  .transport { display: grid; grid-template-columns: 42px 1fr; column-gap: 16px; padding: 18px 22px 2px; align-items: center; }
  .play { grid-row: 1 / 4; width: 42px; height: 42px; border: 1px solid var(--accent); border-radius: 50%; background: var(--accent); color: #fff; font-size: .8rem; display: grid; place-items: center; transition: transform .2s, box-shadow .2s; }
  .play:hover { transform: scale(1.06); box-shadow: 0 3px 12px #0000cd24; }
  .transport label { display: flex; justify-content: space-between; gap: 12px; align-items: baseline; font-size: .86rem; font-weight: 600; }
  .transport label strong { font-variant-numeric: tabular-nums; color: var(--accent); white-space: nowrap; }
  input[type='range'] { margin: 11px 0 0; appearance: none; width: 100%; height: 5px; background: linear-gradient(to right, var(--accent) var(--progress), #dfe2f2 var(--progress)); border-radius: 5px; cursor: pointer; }
  input[type='range']::-webkit-slider-thumb { appearance: none; width: 19px; height: 19px; border-radius: 50%; background: #fff; border: 3px solid var(--accent); box-shadow: 0 2px 5px #0002; }
  input[type='range']::-moz-range-thumb { width: 14px; height: 14px; border-radius: 50%; background: #fff; border: 3px solid var(--accent); box-shadow: 0 2px 5px #0002; }
  .range-ends { display: flex; justify-content: space-between; color: var(--muted); font-size: .72rem; font-variant-numeric: tabular-nums; line-height: 1.3; }
  .parameter-control { margin: 16px 22px 0 80px; padding-top: 15px; border-top: 1px solid var(--rule); }
  .parameter-control label { display: flex; justify-content: space-between; gap: 12px; font-size: .86rem; font-weight: 600; }
  .parameter-control label strong { color: var(--accent); font-variant-numeric: tabular-nums; }
  .parameter-control input { margin-top: 12px; }
  .film-note { font-size: .75rem; line-height: 1.45; color: var(--muted); padding: 0 22px 17px 80px; margin: 8px 0 0; }
  .readout { padding: 22px; display: flex; flex-direction: column; }
  .readout-kicker { font-size: .71rem; font-weight: 700; letter-spacing: .13em; text-transform: uppercase; color: var(--accent); margin: 0 0 22px; }
  .large-number { display: grid; gap: 1px; padding-bottom: 21px; border-bottom: 1px solid var(--rule); }
  .large-number span { font-size: .88rem; color: var(--muted); }
  .large-number strong { font-size: clamp(2.8rem, 4.5vw, 4.4rem); line-height: 1; font-weight: 400; letter-spacing: -.06em; color: var(--accent); font-variant-numeric: tabular-nums; }
  .large-number small { font-size: .76rem; color: var(--muted); }
  .readout-pair { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; padding: 20px 0; border-bottom: 1px solid var(--rule); }
  .readout-pair div { display: grid; align-content: start; gap: 4px; }
  .readout-pair span, .math-stack span { font-size: .72rem; color: var(--muted); line-height: 1.35; }
  .readout-pair strong { font-size: 1.37rem; line-height: 1.2; font-weight: 600; font-variant-numeric: tabular-nums; }
  .math-stack { display: grid; gap: 13px; padding-top: 20px; }
  .math-stack > div { min-width: 0; }
  .math-stack .math { overflow-x: auto; font-size: .9rem; line-height: 1.55; margin-top: 3px; }
  .growth-note { display: grid; gap: 4px; margin: 20px 0 0; padding: 13px 14px; border-left: 3px solid var(--accent); background: var(--accent-soft); font-size: .8rem; line-height: 1.4; }
  .growth-note strong { font-size: .75rem; text-transform: uppercase; letter-spacing: .07em; color: var(--accent); }
  .growth-note b { color: var(--accent); font-variant-numeric: tabular-nums; }
  .facts-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1px; background: var(--rule); border: 1px solid var(--rule); border-radius: 9px; overflow: hidden; margin-top: 15px; }
  .facts-grid > div { background: #fafaff; padding: 17px 20px; display: grid; align-content: start; gap: 5px; }
  .fact-label { font-size: .69rem; font-weight: 700; letter-spacing: .11em; text-transform: uppercase; color: var(--muted); }
  .facts-grid strong { font-size: .92rem; font-weight: 600; line-height: 1.35; }
  .interpretation { display: grid; grid-template-columns: 1fr 1fr; gap: 25px; font-size: .93rem; line-height: 1.45; color: var(--muted); margin-top: 20px; }
  .interpretation p { margin: 0; }
  .interpretation strong { color: var(--ink); }
  @media (max-width: 1050px) { .stage-grid { grid-template-columns: minmax(0, 1.4fr) minmax(250px, .8fr); } .family-tabs { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
  @media (max-width: 760px) { .lab { padding: 54px 0; } .lab-head { grid-template-columns: 1fr; gap: 6px; } .stage-grid { grid-template-columns: 1fr; } .family-tabs { grid-template-columns: repeat(2, minmax(0, 1fr)); } .facts-grid { grid-template-columns: 1fr; } .interpretation { grid-template-columns: 1fr; gap: 13px; } }
  @media (max-width: 430px) { .family-tabs { gap: 5px; } .family-tabs button { padding: 11px 10px; } .family-tabs span { font-size: .84rem; } .family-tabs small { font-size: .7rem; } .transport { padding: 15px 14px 0; grid-template-columns: 37px 1fr; gap: 10px; } .play { width: 37px; height: 37px; } .transport label { font-size: .78rem; } .parameter-control { margin-left: 61px; margin-right: 14px; } .parameter-control label { font-size: .78rem; } .film-note { padding-left: 61px; padding-right: 12px; } .readout { padding: 18px; } }
  @media (prefers-reduced-motion: reduce) { .family-tabs button, .play { transition: none; } }
</style>
