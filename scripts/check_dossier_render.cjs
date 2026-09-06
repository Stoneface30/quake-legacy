// Does the dossier actually SHOW accuracy, and is the round honest?
//
// The user's screenshot showed a round of 0.0s, a "WATCH FULL ROUND (0.0s)"
// button, and no accuracy anywhere. This drives the real page against the
// real server at both widths and reads what is on screen.
//
//   REVIEW_BASE, REVIEW_LG_ITEM, REVIEW_RAIL_ITEM
//   PLAYWRIGHT_MODULE, PLAYWRIGHT_CHROMIUM_EXECUTABLE
const assert = require('node:assert/strict');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

const BASE = process.env.REVIEW_BASE || 'http://127.0.0.1:8767';
const LG = process.env.REVIEW_LG_ITEM || 'USER_FRAG:495';
const RAIL = process.env.REVIEW_RAIL_ITEM || 'USER_FRAG:47689';

async function readDossier(page, itemId) {
  await page.evaluate(async id => {
    const x = await (await fetch('/api/review/item/' + encodeURIComponent(id))).json();
    await show(x);
  }, itemId);
  await page.waitForFunction(id => cur && cur.item_id === id, itemId,
                             { timeout: 20000 });
  await page.waitForTimeout(1400);
  return page.evaluate(() => {
    const rows = {};
    document.querySelectorAll('#dossier .dgrid').forEach(g => {
      const kids = [...g.children];
      for (let i = 0; i < kids.length - 1; i += 2) {
        if (kids[i].classList.contains('k'))
          rows[kids[i].textContent.trim()] = kids[i + 1].textContent.trim();
      }
    });
    return { rows, round: (document.getElementById('d-round') || {}).textContent || '',
             text: (document.getElementById('dossier') || {}).textContent || '' };
  });
}

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE });
  const results = [];
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

      // 1. LG: accuracy must be present and say NOT DERIVABLE.
      const lg = await readDossier(page, LG);
      assert.ok('accuracy' in lg.rows,
                `${label}: no accuracy row at all — ${JSON.stringify(Object.keys(lg.rows))}`);
      assert.equal(lg.rows.accuracy, 'NOT DERIVABLE',
                   `${label}: LG accuracy shows ${lg.rows.accuracy}`);
      assert.ok(/attack ticks/.test(Object.keys(lg.rows).join(' ')),
                `${label}: LG shots not labelled as attack ticks`);
      console.log(`  [${label}] LG accuracy = NOT DERIVABLE, `
        + `${lg.rows['attack ticks']} attack ticks`);

      // 2. The round is no longer 0.0s, and no 0s full-round offer.
      // Only the ROUND DURATION matters here; an event offset of +0.0s is a
      // legitimate thing to print.
      const dur = /round \d+ · ([\d.]+)s/.exec(lg.round);
      assert.ok(dur, `${label}: no round duration on screen`);
      assert.ok(parseFloat(dur[1]) > 0,
                `${label}: round still shows ${dur[1]}s`);
      const btn = await page.locator('#watchround').count();
      if (btn) {
        const t = await page.locator('#watchround').textContent();
        assert.ok(!/\(0\.0s\)/.test(t), `${label}: full-round button says ${t}`);
        console.log(`  [${label}] full round offered: ${t.trim()}`);
      } else {
        console.log(`  [${label}] full round correctly not offered`);
      }

      // 3. Rail: a real accuracy number is shown.
      const rail = await readDossier(page, RAIL);
      assert.ok('accuracy' in rail.rows, `${label}: rail has no accuracy row`);
      assert.ok(/%/.test(rail.rows.accuracy),
                `${label}: rail accuracy is ${rail.rows.accuracy}`);
      console.log(`  [${label}] rail accuracy = ${rail.rows.accuracy}`);

      // 4. The clip is still playing — nothing blanked it.
      const playing = await page.evaluate(() => {
        const v = document.getElementById('v');
        return { hidden: v.hidden, src: !!v.getAttribute('src') };
      });
      assert.ok(!playing.hidden && playing.src,
                `${label}: the video was blanked`);
      assert.deepEqual(errors, [], `${label}: js errors`);
      results.push(`${label}: accuracy visible, round honest, clip intact`);
      await page.close();
    }
    console.log('\nPASS dossier accuracy + round honesty');
    results.forEach(r => console.log('  - ' + r));
  } catch (err) {
    console.error('\nFAIL ' + err.message);
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
})();
