// Does the LOCATION block actually appear in the dossier, and does adding
// it leave everything else alone?
//
// The user is reviewing while this ships, so the second half matters as
// much as the first: the accuracy row, the honest round duration and the
// playing clip must all survive the new section.
//
//   REVIEW_BASE, REVIEW_LOCATED_ITEM
//   PLAYWRIGHT_MODULE, PLAYWRIGHT_CHROMIUM_EXECUTABLE
const assert = require('node:assert/strict');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

const BASE = process.env.REVIEW_BASE || 'http://127.0.0.1:8766';
const LOCATED = process.env.REVIEW_LOCATED_ITEM || 'USER_FRAG:495';

async function readDossier(page, itemId) {
  await page.evaluate(async id => {
    const x = await (await fetch('/api/review/item/' + encodeURIComponent(id))).json();
    await show(x);
  }, itemId);
  await page.waitForFunction(id => cur && cur.item_id === id, itemId,
                             { timeout: 20000 });
  await page.waitForTimeout(2000);
  return page.evaluate(() => {
    const rows = {};
    document.querySelectorAll('#dossier .dgrid, #dloc .dgrid').forEach(g => {
      const kids = [...g.children];
      for (let i = 0; i < kids.length - 1; i += 2) {
        if (kids[i].classList.contains('k'))
          rows[kids[i].textContent.trim()] = kids[i + 1].textContent.trim();
      }
    });
    const heads = [...document.querySelectorAll('#dossier h4, #dloc h4')]
      .map(h => h.textContent.trim());
    return { rows, heads,
             round: (document.getElementById('d-round') || {}).textContent || '' };
  });
}

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE });
  try {
    for (const [label, vp] of [['desktop', { width: 1440, height: 900 }],
                               ['mobile', { width: 390, height: 844 }]]) {
      const page = await browser.newPage({
        viewport: vp, isMobile: label === 'mobile',
        hasTouch: label === 'mobile' });
      const errors = [];
      page.on('pageerror', e => errors.push(e.message));
      await page.goto(BASE + '/api/review/ui', { waitUntil: 'domcontentloaded' });
      await page.waitForFunction(() => typeof cur !== 'undefined' && cur,
                                 null, { timeout: 30000 });

      const d = await readDossier(page, LOCATED);

      // 1. The location block is there, and says something real.
      assert.ok(d.heads.includes('location'),
                `${label}: no location section - ${JSON.stringify(d.heads)}`);
      assert.ok(d.rows.where && /region_\d+/.test(d.rows.where),
                `${label}: where = ${d.rows.where}`);
      assert.ok(/lower|mid|upper|ground/.test(d.rows.layer || ''),
                `${label}: layer = ${d.rows.layer}`);
      console.log(`  [${label}] location: ${d.rows.where} | ${d.rows.layer}`
        + (d.rows.approach ? ` | approach ${d.rows.approach}` : ''));

      // 2. Nothing it was added next to regressed.
      assert.ok('accuracy' in d.rows, `${label}: accuracy row vanished`);
      const dur = /round \d+ . ([\d.]+)s/.exec(d.round);
      assert.ok(dur && parseFloat(dur[1]) > 0,
                `${label}: round duration = ${dur && dur[1]}`);
      console.log(`  [${label}] accuracy = ${d.rows.accuracy}, `
        + `round = ${dur[1]}s`);

      // 3. The clip is still playing.
      const v = await page.evaluate(() => {
        const el = document.getElementById('v');
        return { hidden: el.hidden, src: !!el.getAttribute('src') };
      });
      assert.ok(!v.hidden && v.src, `${label}: the video was blanked`);

      // 4. And the page knows whether it is allowed to render.
      const permit = await page.evaluate(async () =>
        (await (await fetch('/api/review/render_permit')).json()));
      assert.ok(['GRANTED', 'DEFERRED', 'DENIED'].includes(permit.permit),
                `${label}: permit = ${JSON.stringify(permit)}`);
      console.log(`  [${label}] render permit: ${permit.permit}`);

      assert.deepEqual(errors, [], `${label}: js errors`);
      await page.close();
    }
    console.log('\nPASS location in dossier, nothing else moved');
  } catch (err) {
    console.error('\nFAIL ' + err.message);
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
})();
