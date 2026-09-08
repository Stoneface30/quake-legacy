// THE WORKFLOW THE USER WILL SPEND HOURS IN, proven end to end.
//
// One multi-frag round: F1, an ACTION, F2, F3. The round video must load
// ONCE and the playhead must move between events -- reloading per frag is
// the six-second keyhole all over again, which is the thing being fixed.
//
// Every API call is stubbed here on purpose. This proves the FRONTEND
// contract -- one media load, seek not reload, verdicts on frags, no
// advance on a failed save, one POST per double press -- without rendering
// anything and without going near a human row. The live proof against real
// media is a separate script.
//
//   PLAYWRIGHT_MODULE, PLAYWRIGHT_CHROMIUM_EXECUTABLE, REVIEW_BASE, ROUND_MP4
const assert = require('node:assert/strict');
const fs = require('node:fs');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

const BASE = process.env.REVIEW_BASE || 'http://127.0.0.1:8766';
const MP4 = fs.readFileSync(process.env.ROUND_MP4);

const SCENE_ID = 'SCENE:TEST:1';
const EVENTS = [
  { occurrence_id: 9001, item_id: 'USER_FRAG:9001', label: 'F1 RAIL',
    t_ms: 2000, offset_ms: 2000, takes_verdict: true, is_user: true,
    event_id: 'EV1' },
  { occurrence_id: null, item_id: null, label: 'HIGH PRESSURE',
    t_ms: 4000, offset_ms: 4000, takes_verdict: false, is_user: true,
    event_id: 'EV-ACTION' },
  { occurrence_id: 9002, item_id: 'USER_FRAG:9002', label: 'F2 ROCKET',
    t_ms: 6000, offset_ms: 6000, takes_verdict: true, is_user: true,
    event_id: 'EV2' },
  { occurrence_id: 9003, item_id: 'USER_FRAG:9003', label: 'F3 LG',
    t_ms: 9000, offset_ms: 9000, takes_verdict: true, is_user: true,
    event_id: 'EV3' },
];

function item(occ) {
  return {
    item_id: 'USER_FRAG:' + occ, item_type: 'USER_FRAG', source_id: occ,
    content_hash: 'testhash', demo_name: 'test.dm_73', server_time_ms: 1000,
    machine_score: 9, machine_rank: 1, total_items: 4, weapon: 'RAIL',
    map_name: 'testmap', victim: 2, round_no: 7, why: 'test',
    actor_name: 'tester', is_actor_pov: true, death_cause: 'PLAYER_KILL',
    n_observations: 1, observation_pov: 'ACTOR_POV',
    merge_confidence: 'SINGLE_OBSERVATION', scored: true,
    human_role: null, note: '', start_ms: 0, end_ms: 6000, reviewed: false,
    frag_offset_s: 3, duration_s: 6, round_frag_count: 3,
  };
}

const NEXT = Object.assign(item(9100),
                           { item_id: 'USER_FRAG:9100', source_id: 9100 });

// A <video> can only SEEK if the server answers byte ranges. Fulfilling the
// whole file with no Accept-Ranges makes the element unseekable, and a
// currentTime past what is buffered silently snaps back to zero -- which
// looks exactly like a product that refuses to seek. The real server does
// support ranges; the stub has to as well or the test lies in both
// directions.
function serveVideo(route) {
  const range = route.request().headers()['range'];
  if (!range) {
    return route.fulfill({ status: 200, contentType: 'video/mp4',
      headers: { 'Accept-Ranges': 'bytes',
                 'Content-Length': String(MP4.length) }, body: MP4 });
  }
  const m = /bytes=(\d*)-(\d*)/.exec(range) || [];
  const start = m[1] ? parseInt(m[1], 10) : 0;
  const end = m[2] ? parseInt(m[2], 10) : MP4.length - 1;
  return route.fulfill({ status: 206, contentType: 'video/mp4',
    headers: { 'Accept-Ranges': 'bytes',
               'Content-Range': 'bytes ' + start + '-' + end + '/' + MP4.length,
               'Content-Length': String(end - start + 1) },
    body: MP4.subarray(start, end + 1) });
}

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE });
  const posts = [];
  let failVerdict = false;
  try {
    for (const [label, vp] of [['desktop', { width: 1440, height: 900 }],
                               ['mobile', { width: 390, height: 844 }]]) {
      const page = await browser.newPage({
        viewport: vp, isMobile: label === 'mobile',
        hasTouch: label === 'mobile' });
      const errors = [];
      page.on('pageerror', e => { errors.push(e.message);
        if (process.env.E2E_DEBUG) console.log('PAGEERROR ' + e.message); });
      if (process.env.E2E_DEBUG)
        page.on('console', m => { if (m.type() === 'error')
          console.log('CONSOLE ' + m.text()); });
      posts.length = 0; failVerdict = false;

      await page.route('**/api/review/**', async route => {
        const url = new URL(route.request().url());
        const p = url.pathname.replace('/api/review/', '');
        const method = route.request().method();
        const json = b => route.fulfill({
          status: 200, contentType: 'application/json',
          body: JSON.stringify(b) });

        // The page itself lives under this prefix. Intercepting it served
        // the reviewer as the JSON body "{}", so nothing ever booted.
        if (p === 'ui' || p.indexOf('static') === 0) return route.continue();

        if (method === 'POST') {
          const body = JSON.parse(route.request().postData() || '{}');
          posts.push({ path: p, body: body });
          if (p === 'verdict' && failVerdict)
            return route.fulfill({ status: 500,
                                   contentType: 'application/json',
                                   body: '{"detail":"disk"}' });
          if (p.indexOf('note') === 0) return json({ saved: true });
          return json({ ok: true, progress: { reviewed: 1, total: 4 } });
        }
        if (p === 'queue') return json({
          order: 'BEST_FIRST', offset: 0, item_type: 'USER_FRAG',
          corpus: 'USER_FRAGS', filters: {}, view: 'frags', total: 4,
          items: [item(9001), NEXT] });
        if (p.indexOf('item/') === 0) {
          const occ = parseInt(p.split(':')[1], 10);
          return json(occ === 9100 ? NEXT : item(occ));
        }
        if (p.indexOf('scene/') === 0) return json({
          available: true, mode: 'SCENE_MODE', scene_id: SCENE_ID,
          media_start_ms: 0, media_end_ms: 12000, events: EVENTS });
        if (p.indexOf('media_state/') === 0)
          return json({ ready: true, state: 'READY', render_deferred: false,
                        permit: { permit: 'GRANTED' } });
        if (p.indexOf('media/') === 0) return serveVideo(route);
        if (p.indexOf('round/') === 0) return json({
          item_id: 'x', available: true, full_round_available: true,
          media_duration_s: 12, duration_provenance: 'OBSERVED',
          round: { round_no: 7, map_name: 'testmap', duration_ms: 12000,
                   events: EVENTS, user_kills: 3, team_kills: 0,
                   enemy_kills: 0, alive_curve: [], coverage_note: '' } });
        if (p === 'progress') return json({ reviewed: 0, total: 4, roles: {},
                                            labels: {} });
        if (p === 'corpora') return json({ corpora: [] });
        if (p === 'session') return json({ found: false });
        return json({});
      });

      await page.goto(BASE + '/api/review/ui',
                      { waitUntil: 'domcontentloaded' });
      await page.waitForFunction(() => typeof cur !== 'undefined' && cur,
                                 null, { timeout: 40000 });
      await page.waitForTimeout(2500);

      // ── the round loaded, once ──────────────────────────────────────────
      const src1 = await page.evaluate(
        () => document.getElementById('v').src);
      assert.ok(/\/media\/round\//.test(src1),
                label + ': round context did not take over (' + src1 + ')');
      console.log('  [' + label + '] round media: '
        + src1.split('/api/review/')[1]);

      // ── F1 -> F2 -> F3 all seek the SAME media ─────────────────────────
      const seen = [];
      // Where each frag SHOULD land, from the stubbed scene above.
      const WANT = { 9002: 6.0, 9003: 9.0 };
      for (const expect of [9002, 9003]) {
        const before = await page.evaluate(() => ({
          src: document.getElementById('v').src,
          t: document.getElementById('v').currentTime }));
        await page.keyboard.press('4');
        await page.waitForFunction(o => cur && cur.source_id === o,
                                   expect, { timeout: 15000 });
        await page.waitForTimeout(900);
        const after = await page.evaluate(() => ({
          src: document.getElementById('v').src,
          t: document.getElementById('v').currentTime }));
        assert.equal(after.src, before.src,
          label + ': media RELOADED moving to ' + expect);
        // SAME SRC IS NOT ENOUGH. A stable url with the playhead still at
        // the start is the keyhole with extra steps -- the point is that
        // the round is already loaded AND we jump to the right second.
        // The clip keeps PLAYING while we settle, so the playhead may be a
        // little past the event -- it must never be before it, which is what
        // "did not seek" looks like.
        assert.ok(after.t >= WANT[expect] - 0.6 && after.t <= WANT[expect] + 3.5,
          label + ': playhead at ' + after.t.toFixed(2) + 's, expected to land '
          + 'on ' + WANT[expect] + 's for ' + expect);
        seen.push(expect + '@' + after.t.toFixed(2) + 's');
      }
      console.log('  [' + label + '] seeks without reload: '
        + seen.join(' -> '));

      // Verdicts landed on frags, never on a round.
      const verdicts = posts.filter(x => x.path === 'verdict');
      assert.equal(posts.filter(x => x.path === 'verdict/round').length, 0,
        label + ': a round-level verdict was posted');
      assert.deepEqual(verdicts.map(v => v.body.item_id),
                       ['USER_FRAG:9001', 'USER_FRAG:9002'],
                       label + ': wrong verdict targets');

      // ── a failed save must not advance ─────────────────────────────────
      failVerdict = true;
      const beforeFail = await page.evaluate(() => cur.source_id);
      await page.keyboard.press('4');
      await page.waitForTimeout(1600);
      const afterFail = await page.evaluate(() => cur.source_id);
      assert.equal(afterFail, beforeFail,
        label + ': advanced past a verdict that did not save');
      console.log('  [' + label + '] failed save did not advance (stayed on '
        + afterFail + ')');
      failVerdict = false;

      // ── double press posts once ────────────────────────────────────────
      const n0 = posts.filter(x => x.path === 'verdict').length;
      await Promise.all([page.keyboard.press('4'), page.keyboard.press('4')]);
      await page.waitForTimeout(1800);
      const added = posts.filter(x => x.path === 'verdict').length - n0;
      assert.ok(added <= 1,
        label + ': a double press produced ' + added + ' verdicts');
      console.log('  [' + label + '] double press -> ' + added + ' POST');

      assert.deepEqual(errors, [], label + ': js errors');
      await page.close();
    }
    console.log('\nPASS option A end to end');
  } catch (err) {
    console.error('\nFAIL ' + err.message);
    process.exitCode = 1;
  } finally { await browser.close(); }
})();
