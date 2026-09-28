const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const output = path.join(root, '.verification');
fs.mkdirSync(path.join(output, 'tmp'), { recursive: true });
process.env.TEMP = path.join(output, 'tmp');
process.env.TMP = process.env.TEMP;
process.env.TMPDIR = process.env.TEMP;
const { chromium } = require(process.env.PLAYWRIGHT_MODULE_PATH || 'playwright');
const base = (process.env.PREVIEW_URL || 'http://127.0.0.1:4321/').replace(/\/?$/, '/');
const slugs = ['solow', 'household', 'saddle-path', 'bellman', 'extraction', 'investment', 'rbc'];
const numbers = [1, 2, 3, 6, 7, 9, 10];
const errors = [];
async function setRange(page, label, value) {
  await page.getByLabel(label, { exact: true }).evaluate((element, v) => {
    element.value = v;
    element.dispatchEvent(new Event('input', { bubbles: true }));
    element.dispatchEvent(new Event('change', { bubbles: true }));
  }, String(value));
}
async function waitForHydration(page) {
  await page.waitForFunction(() => document.querySelectorAll('astro-island[ssr]').length === 0);
}
async function checkLayout(page) {
  const measurements = await page.evaluate(() => ({
    width: window.innerWidth,
    documentWidth: document.documentElement.scrollWidth,
    labels: Array.from(document.querySelectorAll('.line-chart svg')).flatMap(svg => {
      const box = svg.getBoundingClientRect();
      return Array.from(svg.querySelectorAll('.tick, .axis-title, .reference-label, .region-label')).map(label => {
        const r = label.getBoundingClientRect();
        return { text: label.textContent, clipped: r.left < box.left - 3 || r.right > box.right + 3 || r.top < box.top - 3 || r.bottom > box.bottom + 3 };
      });
    })
  }));
  assert.ok(measurements.documentWidth <= measurements.width + 1, `Page overflows at ${measurements.width}px: ${measurements.documentWidth}`);
  assert.deepEqual(measurements.labels.filter(l => l.clipped), [], 'A chart label extends outside its SVG');
}
(async () => {
  const context = await chromium.launchPersistentContext(path.join(output, 'browser-profile'), {
    headless: true,
    executablePath: process.env.CHROME_PATH || undefined,
    viewport: { width: 1440, height: 1000 },
    args: ['--no-first-run', '--no-default-browser-check', '--disable-background-networking', '--disable-component-update', '--disable-breakpad', '--disable-crash-reporter']
  });
  try {
    const page = await context.newPage();
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
    page.on('response', response => { if (response.status() >= 400 && response.url().startsWith(base)) errors.push(`${response.status()}: ${response.url()}`); });
    await page.goto(base, { waitUntil: 'networkidle' });
    assert.equal(await page.locator('.lesson-row').count(), 7);
    await checkLayout(page);
    await page.screenshot({ path: path.join(output, 'home-desktop.png'), fullPage: true });
    for (let i = 0; i < slugs.length; i++) {
      const slug = slugs[i];
      await page.setViewportSize({ width: 1440, height: 1000 });
      await page.goto(`${base}tutorials/${slug}/`, { waitUntil: 'networkidle' });
      await waitForHydration(page);
      assert.equal(await page.locator('h1').count(), 1);
      assert.ok(await page.locator('.katex').count() > 2, `${slug}: equations not rendered`);
      assert.ok(await page.getByRole('heading', { name: 'The intuition', exact: true }).isVisible());
      const notebook = await context.request.get(`${base}notebooks/Tutorial_${numbers[i]}.ipynb`);
      assert.equal(notebook.status(), 200);
      assert.ok((await notebook.json()).cells.length > 10);
      if (slug === 'solow') {
        const before = await page.locator('.live-insight').innerText();
        await setRange(page, 'Saving rate', .35);
        await page.waitForFunction(text => document.querySelector('.live-insight').textContent !== text, before);
        await page.getByRole('button', { name: 'Saving & depreciation', exact: true }).click();
        assert.ok((await page.locator('.line-chart').innerText()).includes('gap between the curves'));
        await page.getByRole('button', { name: 'Capital over time', exact: true }).click();
        await page.getByLabel('Euler time step', { exact: true }).selectOption('5');
      } else if (slug === 'household') {
        await setRange(page, 'Consumption deviation', 1);
        await page.waitForFunction(() => document.querySelector('.live-insight').textContent.includes('Assets reach zero'));
        await page.getByRole('button', { name: 'Wealth in levels', exact: true }).click();
      } else if (slug === 'saddle-path') {
        await page.getByRole('button', { name: 'Bisect the bracket', exact: true }).click();
        assert.ok((await page.locator('.bracket').innerText()).includes('1 bracket updates'));
        await page.getByRole('button', { name: 'Use the stable guess', exact: true }).click();
        await page.waitForFunction(() => document.querySelector('.live-insight').textContent.includes('stable path'));
      } else if (slug === 'bellman') {
        await page.getByRole('button', { name: 'Apply this Bellman update', exact: true }).click();
        assert.ok((await page.locator('.matrix-heading').innerText()).includes('update 2'));
        await page.getByLabel('Current capital state', { exact: true }).selectOption('4');
        assert.ok((await page.locator('.live-insight').innerText()).includes('2.25'));
      } else if (slug === 'extraction') {
        await page.getByLabel('Capacity cost', { exact: true }).selectOption('0.0');
        await page.getByLabel('Current price', { exact: true }).selectOption('5');
        await page.waitForFunction(() => document.querySelector('.live-insight').textContent.includes('every plotted stock'));
      } else if (slug === 'investment') {
        await page.getByLabel('Fixed adjustment cost', { exact: true }).selectOption('.1');
        await page.getByLabel('Resale price', { exact: true }).selectOption('.8');
        await page.waitForFunction(() => document.querySelector('.live-insight').textContent.includes('6.16'));
      } else if (slug === 'rbc') {
        await page.getByLabel('Productivity shock', { exact: true }).selectOption('0.20');
        await page.waitForFunction(() => document.querySelector('.gap strong').textContent.includes('0.999'));
      }
      await checkLayout(page);
      if (slug !== 'bellman' && slug !== 'saddle-path') {
        const group = page.locator('.chart-interaction');
        await group.focus();
        await page.keyboard.press('ArrowRight');
        assert.equal(await page.locator('.chart-tooltip').count(), 1);
        await page.keyboard.press('Escape');
        assert.equal(await page.locator('.chart-tooltip').count(), 0);
      }
      await page.screenshot({ path: path.join(output, `${slug}-desktop.png`), fullPage: true });
      await page.setViewportSize({ width: 360, height: 900 });
      await page.goto(`${base}tutorials/${slug}/`, { waitUntil: 'networkidle' });
      await waitForHydration(page);
      await checkLayout(page);
      await page.locator('.mobile-menu summary').click();
      assert.ok(await page.locator('.mobile-menu nav').isVisible());
      await page.locator('.mobile-menu summary').click();
      await page.screenshot({ path: path.join(output, `${slug}-mobile.png`), fullPage: true });
      console.log(`PASS ${slug}: controls, equations, notebook, desktop and mobile`);
    }
    assert.deepEqual(errors, [], 'Browser errors were reported');
    fs.writeFileSync(path.join(output, 'browser-result.json'), JSON.stringify({ passed: true, lessons: 7, viewports: [1440, 360], errors }, null, 2));
    console.log('All seven lessons passed browser verification.');
  } finally { await context.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
