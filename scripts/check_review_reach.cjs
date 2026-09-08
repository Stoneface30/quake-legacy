// Can you reach the decision without scrolling?
//
// "the buttons are too far down to be used while looking". That is a
// measurement, not an opinion: the verdict row either fits inside the
// viewport under the video or it does not.
const assert = require('node:assert/strict');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const BASE = process.env.REVIEW_BASE || 'http://127.0.0.1:8766';

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE });
  try {
    for (const [label, vp] of [['laptop', { width: 1440, height: 820 }],
                               ['phone', { width: 390, height: 844 }]]) {
      const page = await browser.newPage({
        viewport: vp, isMobile: label === 'phone',
        hasTouch: label === 'phone' });
      const errors = [];
      page.on('pageerror', e => errors.push(e.message));
      await page.goto(BASE + '/api/review/ui', { waitUntil: 'domcontentloaded' });
      await page.waitForFunction(() => typeof cur !== 'undefined' && cur,
                                 null, { timeout: 40000 });
      await page.waitForTimeout(1500);

      const m = await page.evaluate(() => {
        const b = document.querySelector('.buttons button');
        const last = document.querySelector('#b5');
        const v = document.getElementById('v');
        const r = b.getBoundingClientRect(), l = last.getBoundingClientRect();
        const vr = v.getBoundingClientRect();
        // The decisions may sit BESIDE the video (wide) or under it
        // (narrow). Either is fine; landing on top of it is not.
        const overlaps = !(r.right <= vr.left || r.left >= vr.right
                           || r.bottom <= vr.top || r.top >= vr.bottom);
        return { firstTop: Math.round(r.top), lastBottom: Math.round(l.bottom),
                 videoBottom: Math.round(vr.bottom), overlaps,
                 vh: window.innerHeight,
                 hintsVisible: getComputedStyle(
                   document.querySelector('.buttons .h')).display !== 'none',
                 tooltip: b.getAttribute('title') };
      });
      console.log(`  [${label}] video ends ${m.videoBottom}px, verdicts `
        + `${m.firstTop}-${m.lastBottom}px, viewport ${m.vh}px`);
      assert.ok(m.lastBottom <= m.vh,
        `${label}: verdict row runs past the fold (${m.lastBottom} > ${m.vh})`);
      assert.equal(m.overlaps, false, `${label}: verdicts cover the video`);
      assert.equal(m.hintsVisible, false, `${label}: hint lines still shown`);
      assert.ok(m.tooltip, `${label}: hint not preserved as a tooltip`);
      assert.deepEqual(errors, [], `${label}: js errors`);
      await page.close();
    }
    console.log('\nPASS decisions reachable without scrolling');
  } catch (err) {
    console.error('\nFAIL ' + err.message);
    process.exitCode = 1;
  } finally { await browser.close(); }
})();
