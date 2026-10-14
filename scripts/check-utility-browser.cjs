const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE_PATH || 'playwright');
const root = path.resolve(__dirname, '..');
const out = path.join(root, '.verification');
fs.mkdirSync(out, { recursive: true });
const url = process.env.PREVIEW_URL || 'http://127.0.0.1:4321/';

async function setRange(page, label, value) {
  await page.getByRole('slider', { name: label }).evaluate((el, v) => {
    el.value = String(v);
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
  }, value);
}

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || undefined, headless: true, args: ['--no-sandbox'] });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    assert.ok(await page.getByRole('link', { name: /Utility functions/ }).isVisible());
    assert.equal(await page.getByRole('link', { name: /Solow/ }).count(), 0);
    assert.equal((await page.request.get(new URL('tutorials/solow/', url).href)).status(), 404);
    await page.getByRole('link', { name: /Utility functions/ }).click();
    await page.waitForFunction(() => document.querySelectorAll('astro-island[ssr]').length === 0);
    assert.equal(await page.locator('video').count(), 2);
    await page.waitForFunction(() => [...document.querySelectorAll('video')].every(v => Number.isFinite(v.duration) && v.duration > 4));
    await setRange(page, 'Consumption, c', 5);
    await page.waitForFunction(() => Math.abs(document.querySelector('video').currentTime - 3.2) < 0.4);
    assert.equal(await page.locator('.lab').first().locator('.large-number strong').innerText(), '0.20');
    await page.getByRole('button', { name: /Quadratic satiation/ }).click();
    await setRange(page, 'Consumption, c', 2.85);
    assert.equal(await page.locator('.lab').first().locator('.large-number strong').innerText(), '0.00');
    await page.getByRole('button', { name: /Perfect substitutes/ }).click();
    assert.equal(await page.locator('.lab').nth(1).locator('.large-number strong').innerText(), '1.50');
    await page.screenshot({ path: path.join(out, 'utility-desktop.png'), fullPage: true });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.screenshot({ path: path.join(out, 'utility-mobile.png'), fullPage: true });
    const sizes = await page.evaluate(() => ({ viewport: innerWidth, document: document.documentElement.scrollWidth }));
    assert.ok(sizes.document <= sizes.viewport + 1, `Mobile overflow: ${JSON.stringify(sizes)}`);
    assert.deepEqual(errors, []);
    console.log('Utility page, Manim media, slider seeking, live mathematics and mobile layout pass.');
  } finally {
    await browser.close();
  }
})().catch(e => { console.error(e); process.exitCode = 1; });
