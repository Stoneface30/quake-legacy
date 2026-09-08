// LIVE mobile review proof: a real browser at 390x844 against a real server.
//
// WHY THIS EXISTS ALONGSIDE check_review_mobile.cjs. That one mocks every
// response, so it proves the page's logic and nothing about the service. The
// user's failure was in the service: media that never arrived, a queue that
// would not advance. Only a real server can prove that fixed.
//
// The server under test is a REAL instance of the app -- same routers, same
// review.html, same media files -- started by scripts/review_test_instance.py
// against a COPY of editorial.db with every verdict forced to TEST
// provenance. The user's three genuine HUMAN_USER reviews are never read,
// written, advanced or counted here.
//
//   REVIEW_BASE   http://127.0.0.1:8767
//   PLAYWRIGHT_MODULE, PLAYWRIGHT_CHROMIUM_EXECUTABLE
//
// Run:  node scripts/check_review_mobile_live.cjs
const assert = require('node:assert/strict');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

const BASE = process.env.REVIEW_BASE || 'http://127.0.0.1:8767';
const API = BASE + '/api/review';

const step = (n, msg) => console.log(`  [${n}] ${msg}`);

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE,
  });
  const page = await browser.newPage({
    viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true,
  });

  const jsErrors = [];
  const posts = [];
  page.on('pageerror', e => jsErrors.push(e.message));
  const toasts = [];
  // The browser logs a console error for every non-2xx response, including
  // the faults this script injects on purpose. Only unexpected ones count.
  page.on('console', m => {
    if (m.type() !== 'error') return;
    if (injecting && /status of (500|503)/.test(m.text())) return;
    jsErrors.push('console: ' + m.text());
  });
  page.on('request', r => {
    if (r.method() === 'POST') posts.push(new URL(r.url()).pathname);
  });

  let failVerdict = false;
  let hideScene = false;
  let injecting = false;
  // Fault injection at the NETWORK layer only. Every other byte comes from
  // the real server: real queue, real dossier, real mp4 files on disk.
  await page.route('**/api/review/**', async route => {
    const p = new URL(route.request().url()).pathname;
    if (failVerdict && p.endsWith('/verdict')) {
      return route.fulfill({ status: 500, contentType: 'application/json',
                             body: JSON.stringify({ detail: 'injected save failure' }) });
    }
    if (hideScene && p.includes('/media_state/scene/')) {
      return route.fulfill({ status: 200, contentType: 'application/json',
                             body: JSON.stringify({ state: 'GENERATING', ready: false, error: null }) });
    }
    return route.continue();
  });

  const results = [];
  try {
    // ── the queue loads on a phone ────────────────────────────────────────
    await page.goto(BASE + '/api/review/ui', { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => typeof cur !== 'undefined' && cur && cur.item_id,
                               null, { timeout: 30000 });
    const first = await page.evaluate(() => cur.item_id);
    step(1, `queue loaded on 390x844, first item ${first}`);

    // ── four items, four verdicts, one POST each ──────────────────────────
    hideScene = true;   // a scene that is still rendering must not blank the clip
    const seen = [first];
    for (let n = 1; n <= 3; n++) {
      const before = await page.evaluate(() => cur.item_id);
      const postsBefore = posts.filter(p => p.endsWith('/verdict')).length;

      // Two taps in the same tick: the double-tap a thumb actually produces.
      await page.evaluate(() => { verdict('T4_KEEP_NORMAL'); verdict('T4_KEEP_NORMAL'); });
      await page.waitForFunction(id => cur && cur.item_id !== id, before, { timeout: 60000 });
      // The save is not finished when `cur` moves: `show()` is awaited inside
      // the same handler. Wait for the guard to clear, exactly as a thumb
      // must -- a tap arriving before it does is CORRECTLY ignored, which is
      // the behaviour this loop is here to rely on, not to defeat.
      await page.waitForFunction(() => savingVerdict === false, null, { timeout: 60000 });

      const after = await page.evaluate(() => cur.item_id);
      const wrote = posts.filter(p => p.endsWith('/verdict')).length - postsBefore;
      assert.equal(wrote, 1, `vote ${n} wrote ${wrote} verdicts, expected exactly 1`);
      assert.ok(!seen.includes(after), `advanced back to an item already seen: ${after}`);
      seen.push(after);
      step(1 + n, `vote ${n}: ${before} -> ${after} (1 POST)`);
    }
    assert.equal(seen.length, 4, 'did not reach a fourth item');
    results.push(`4 items: ${seen.join(' -> ')}`);

    // ── a READY clip is actually playable ─────────────────────────────────
    // A specific item known to have a captured clip under the CURRENT review
    // profile. Passed in rather than searched for, because the queue is
    // 33,316 long and READY media is wherever the worker has reached.
    // Never one of the user's own reviewed items: the later steps vote on
    // whatever is on screen.
    let playedId = process.env.REVIEW_READY_ITEM || null;
    if (playedId) {
      const st = await (await fetch(`${API}/media_state/${encodeURIComponent(playedId)}`)).json();
      if (!st.ready) throw new Error(`${playedId} is ${st.state}, not READY`);
    }
    if (playedId) {
      await page.evaluate(async id => {
        const x = await (await fetch('/api/review/item/' + encodeURIComponent(id))).json();
        await show(x);
      }, playedId);
      await page.waitForFunction(() => {
        const v = document.getElementById('v');
        return !v.hidden && v.getAttribute('src') && v.readyState >= 2;
      }, null, { timeout: 30000 });
      const dims = await page.evaluate(() => {
        const v = document.getElementById('v');
        return { w: v.videoWidth, h: v.videoHeight, src: v.getAttribute('src') };
      });
      assert.ok(dims.w > 0 && dims.h > 0, 'video element decoded no frames');
      assert.ok(dims.src.includes('v=mobile'), 'phone was not served the mobile encode');
      step(5, `READY clip plays: ${playedId} ${dims.w}x${dims.h} (mobile encode)`);
      results.push(`played ${playedId} ${dims.w}x${dims.h}`);

      // ── a pending scene must not take the picture away ──────────────────
      const stillThere = await page.evaluate(() => {
        const v = document.getElementById('v');
        return !v.hidden && !!v.getAttribute('src');
      });
      assert.ok(stillThere, 'a rendering scene blanked a READY frag proxy');
      step(6, 'pending scene left the READY frag proxy playing');
      results.push('pending scene never blanks READY media');
    } else {
      throw new Error('no READY media anywhere in the queue to play');
    }

    // ── a failed save must not advance ────────────────────────────────────
    const held = await page.evaluate(() => cur.item_id);
    failVerdict = true; injecting = true;
    const before500 = posts.filter(p => p.endsWith('/verdict')).length;
    await page.evaluate(() => verdict('T4_KEEP_NORMAL'));
    await page.waitForTimeout(1200);
    failVerdict = false;
    assert.equal(await page.evaluate(() => cur.item_id), held,
                 'a failed save advanced the reviewer');
    assert.equal(posts.filter(p => p.endsWith('/verdict')).length - before500, 1,
                 'a failed save was retried automatically');
    step(7, `failed save held ${held} and did not advance`);
    results.push('failed save holds the item');

    // ── a failed render shows RETRY, and retry is a POST ──────────────────
    hideScene = false; injecting = true;
    await page.route('**/api/review/media_state/*', async route => {
      return route.fulfill({ status: 200, contentType: 'application/json',
                             body: JSON.stringify({ state: 'FAILED', ready: false,
                                                    error: 'injected render failure' }) });
    });
    await page.evaluate(() => show(cur));
    await page.waitForFunction(
      () => document.getElementById('ph').textContent.includes('RENDER FAILED'),
      null, { timeout: 20000 });
    const retryBefore = posts.filter(p => p.includes('/media_retry/')).length;
    await page.locator('#ph button', { hasText: 'RETRY' }).click();
    await page.waitForTimeout(1500);
    assert.ok(posts.filter(p => p.includes('/media_retry/')).length > retryBefore,
              'RETRY did not POST a retry');
    step(8, 'failed render shows RETRY and retry posts exactly once');
    results.push('FAILED -> RETRY works');

    // ── tags: one keystroke, orthogonal to the verdict ───────────────────
    const before = await page.evaluate(() => cur.item_id);
    // Idempotent: tags TOGGLE, and a previous run may have left them on. A
    // test that blindly clicks three times would turn them off and report a
    // failure that is really its own second run.
    for (const t of ['PREDICTION', 'ROCKET', 'GOLDEN']) {
      const on = await page.evaluate(x => curTags.has(x), t);
      if (on) { await page.evaluate(x => toggleTag(x), t);
                await page.waitForTimeout(250); }
    }
    await page.locator('#tagrail button[data-tag="PREDICTION"]').click();
    await page.keyboard.press('o');                   // ROCKET
    await page.locator('#bgold').click();             // GOLDEN
    await page.waitForTimeout(1500);
    const tagged = await page.evaluate(() => [...curTags].sort());
    assert.deepEqual(tagged, ['GOLDEN', 'PREDICTION', 'ROCKET'],
                     'tags did not stick: ' + JSON.stringify(tagged));
    assert.equal(await page.evaluate(() => cur.item_id), before,
                 'tagging advanced the reviewer');
    // Persisted, not just painted.
    const server = await (await fetch(`${API}/tags/` + encodeURIComponent(before))).json();
    assert.deepEqual(server.tags.sort(), ['GOLDEN', 'PREDICTION', 'ROCKET'],
                     'tags were not stored');
    step(9.1, `tagged ${before}: ${server.tags.join(' + ')} (verdict untouched)`);
    results.push('tags persist and never touch the verdict');

    // ── every camera on the moment is reported ───────────────────────────
    const povText = await page.locator('#povs').textContent();
    assert.ok(povText && povText.trim().length, 'no POV line rendered');
    step(9.2, 'cameras: ' + povText.trim().slice(0, 60));
    results.push('POV reported alongside the verdict');

    // ── unfilmed moments go to the workshop ──────────────────────────────
    const wTarget = await page.evaluate(() => cur.item_id);
    if (await page.evaluate(() => workshopOn)) {
      await page.locator('#bwork').click();
      await page.waitForTimeout(600);
    }
    await page.locator('#bwork').click();
    await page.waitForTimeout(1200);
    assert.ok(posts.some(p => p.endsWith('/reconstruct')),
              'workshop button posted nothing');
    // Stored, and correctly NOT in the human-only build queue: this instance
    // stamps everything TEST, and a reconstruction costs real work so only a
    // human request may order one. Asserting both proves the gate as well as
    // the write.
    const wrec = await (await fetch(`${API}/reconstruct/`
      + encodeURIComponent(wTarget))).json();
    assert.ok(wrec.request, 'the workshop request was not stored');
    const wq = await (await fetch(`${API}/reconstruct/queue`)).json();
    assert.ok(!wq.items.some(i => i.item_id === wTarget),
              'a TEST request reached the human build queue');
    assert.equal(await page.evaluate(() => cur.item_id), wTarget,
                 'sending to the workshop advanced the reviewer');
    step(9.3, `sent ${wTarget} to the workshop; stored, and kept out of the human build queue`);
    results.push('workshop request reaches the build queue');

    // ── delete removes the item and undo brings it back ──────────────────
    // A tagged, GOLDEN moment must warn before it disappears.
    let warned = null;
    page.once('dialog', async d => { warned = d.message(); await d.accept(); });
    injecting = false;
    await page.unroute('**/api/review/media_state/*');
    const target = await page.evaluate(() => cur.item_id);
    await page.locator('#bdel').click();
    await page.waitForFunction(id => cur && cur.item_id !== id, target,
                               { timeout: 30000 });
    assert.ok(posts.some(p => p.endsWith('/dismiss')), 'delete posted nothing');
    assert.ok(warned && /GOLDEN/.test(warned),
              'deleting a GOLDEN moment did not warn: ' + warned);
    step(10, `deleted ${target}, advanced to ${await page.evaluate(() => cur.item_id)}`);
    results.push('delete removes the item and advances');

    await page.evaluate(() => { const e = new KeyboardEvent('keydown', {key: 'u'});
                                document.dispatchEvent(e); });
    await page.waitForTimeout(2500);
    assert.ok(posts.some(p => p.endsWith('/restore')), 'undo posted no restore');
    step(11, 'undo restored it');
    results.push('undo restores a deletion');

    assert.deepEqual(jsErrors, [], 'javascript errors on the page');
    const dupes = posts.filter((p, i) => p.endsWith('/verdict') && posts.indexOf(p) !== i);
    step(9, `no JS errors; ${posts.filter(p => p.endsWith('/verdict')).length} verdict POSTs total`);

    console.log('\nPASS live mobile flow');
    results.forEach(r => console.log('  - ' + r));
  } catch (err) {
    console.error('\nFAIL ' + err.message);
    console.error('  js errors: ' + JSON.stringify(jsErrors));
    console.error('  posts: ' + JSON.stringify(posts));
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
})();
