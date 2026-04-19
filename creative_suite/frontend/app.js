/**
 * PANTHEON REVIEW CONSOLE v2 — app.js
 *
 * HOW TO RUN (full JSON auto-load):
 *   cd G:\QUAKE_LEGACY
 *   python -m http.server 8000
 *   open http://localhost:8000/creative_suite/frontend/
 *
 * Serving from frontend dir: use "FLOW JSON" / "EVENT JSON" buttons to load files.
 */

import * as THREE from 'three';

// ─── CONSTANTS ───────────────────────────────────────────────────────────────

const OUTPUT_BASE = '/output';
const PARTS = [4, 5, 6, 7, 8, 9, 10, 11, 12];

const EV = {
  player_death:    { icon: '☠', lbl: 'KILL',    col: '#e74c3c', w: 1.00 },
  rocket_impact:   { icon: '✦', lbl: 'RKT↓',    col: '#f5a623', w: 0.95 },
  rail_fire:       { icon: '⊕', lbl: 'RAIL',    col: '#5dade2', w: 0.90 },
  grenade_direct:  { icon: '◉', lbl: 'NADE!',   col: '#e67e22', w: 0.90 },
  grenade_explode: { icon: '◎', lbl: 'NADE',    col: '#d35400', w: 0.90 },
  rocket_fire:     { icon: '↗', lbl: 'RKT↑',    col: '#e67e22', w: 0.70 },
  lg_hit:          { icon: '⚡', lbl: 'LG',      col: '#f4d03f', w: 0.60 },
  plasma_impact:   { icon: '◯', lbl: 'PLS',     col: '#a855f7', w: 0.55 },
  plasma_hit:      { icon: '◯', lbl: 'PLS',     col: '#a855f7', w: 0.55 },
  shotgun_fire:    { icon: '⋮', lbl: 'SG',       col: '#95a5a6', w: 0.50 },
  grenade_throw:   { icon: '⬤', lbl: 'NADE↑',  col: '#7f8c8d', w: 0.40 },
};

const SECTION_COL = {
  drop:  '#f5a623', build: '#2980b9',
  break: '#3a3a3a', intro: '#1e8449', outro: '#6c3483',
};
const TIER_COL = { T1: '#f5a623', T2: '#7f8c8d', T3: '#2c2c2c' };

// ─── STATE ───────────────────────────────────────────────────────────────────

const S = {
  part: 4, flowData: null, eventData: null,
  vidA: null, vidB: null,
  synced: true, playing: false, scrubDrag: false,
  zoom: 1, evSort: 'count', selEvent: null,
};

// ─── UTILS ───────────────────────────────────────────────────────────────────

const $ = id => document.getElementById(id);

/** Escape HTML entities to prevent XSS from JSON values. */
function esc(s) {
  return String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function fmt(s) {
  if (!isFinite(s) || s == null) return '--:--';
  const m = Math.floor(s / 60), ss = Math.floor(s % 60);
  return `${m}:${ss.toString().padStart(2, '0')}`;
}

function pct(v) { return (v * 100).toFixed(1) + '%'; }

function baseName(p) {
  return (p || '').split(/[/\\]/).pop().replace(/\.(mp4|avi)$/i, '');
}

function setStatus(txt, type = '') {
  $('status-txt').textContent = txt.toUpperCase();
  $('status-led').className = 'status-led ' + type;
}

async function fetchJSON(url) {
  try {
    const r = await fetch(url);
    if (!r.ok) throw new Error(r.status);
    return r.json();
  } catch { return null; }
}

/** Create a div with class + optional css text (no innerHTML). */
function el(tag, cls, css) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (css) e.style.cssText = css;
  return e;
}

// ─── THREE.JS HEADER PARTICLES ───────────────────────────────────────────────

function initParticles() {
  const canvas = $('hdr-canvas');
  const W = canvas.offsetWidth, H = canvas.offsetHeight;
  if (!W || !H) return;
  canvas.width = W; canvas.height = H;

  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: false });
  renderer.setSize(W, H);
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));

  const scene  = new THREE.Scene();
  const camera = new THREE.OrthographicCamera(0, W, H, 0, 0.1, 10);
  camera.position.z = 1;

  const N = 55, pos = new Float32Array(N * 3), vel = [], sz = new Float32Array(N);
  for (let i = 0; i < N; i++) {
    pos[i*3] = Math.random()*W; pos[i*3+1] = Math.random()*H; pos[i*3+2] = 0;
    vel.push({ x: (Math.random()-.5)*.25, y: -(0.15+Math.random()*.45) });
    sz[i] = 1.5 + Math.random() * 2.5;
  }

  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  geo.setAttribute('size', new THREE.BufferAttribute(sz, 1));
  scene.add(new THREE.Points(geo, new THREE.PointsMaterial({
    color: 0xf5a623, sizeAttenuation: false, transparent: true, opacity: .45,
  })));

  (function tick() {
    requestAnimationFrame(tick);
    for (let i = 0; i < N; i++) {
      pos[i*3] += vel[i].x; pos[i*3+1] += vel[i].y;
      if (pos[i*3+1] < -2)  { pos[i*3+1] = H+2; pos[i*3] = Math.random()*W; }
      if (pos[i*3] < 0 || pos[i*3] > W) vel[i].x *= -1;
    }
    geo.attributes.position.needsUpdate = true;
    renderer.render(scene, camera);
  })();
}

// ─── PART SELECTOR ───────────────────────────────────────────────────────────

function buildPartNav() {
  const wrap = $('part-btns');
  PARTS.forEach(p => {
    const b = el('button', 'part-btn' + (p === S.part ? ' active' : ''));
    b.textContent = p;
    b.addEventListener('click', () => selectPart(p));
    wrap.appendChild(b);
  });
}

async function selectPart(p) {
  S.part = p;
  document.querySelectorAll('.part-btn').forEach(b =>
    b.classList.toggle('active', +b.textContent === p));
  await loadPart(p);
}

// ─── DATA LOADING ────────────────────────────────────────────────────────────

async function loadPart(p) {
  const pad = String(p).padStart(2, '0');
  setStatus(`loading part ${p}…`, 'busy');
  const [flow, evDiv] = await Promise.all([
    fetchJSON(`${OUTPUT_BASE}/part${pad}_flow_plan.json`),
    fetchJSON(`${OUTPUT_BASE}/part${pad}_event_diversity.json`),
  ]);
  const flowFinal = flow || await fetchJSON('mock/flow_plan.json');
  S.flowData = flowFinal; S.eventData = evDiv;
  const n = getClips(flowFinal).length;
  setStatus(!flowFinal && !evDiv ? `no data · use load buttons` : `part ${p} · ${n} clips`,
    !flowFinal && !evDiv ? 'err' : 'ok');
  renderFlow(flowFinal);
  renderEventChart(evDiv);
  placeScrubMarkers(flowFinal);
}

function getClips(data) {
  if (!data) return [];
  const arr = data.planned_clips || data.clips || [];
  return arr.map(c => ({
    chunk:        c.chunk || null,
    tier:         c.tier || 'T2',
    section_role: c.section_role || c.section_shape || 'break',
    duration:     c.duration || ((c.end_s ?? 0) - (c.start_s ?? 0)) || 5,
    start_s: c.start_s || 0, end_s: c.end_s || 0,
    top_event: c.top_event || (c.events?.[0]
      ? { type: c.events[0].type, t: c.events[0].t_s,
          confidence: c.events[0].confidence, weight: EV[c.events[0].type]?.w ?? 0.5 }
      : null),
    event_count: c.event_count || c.events?.length || 0,
    target_downbeat: c.target_downbeat || null,
    shift: c.shift ?? 0, tag: c.tag || '', flow_fit: c.flow_fit ?? null,
    id: c.id || baseName(c.chunk || ''), map: c.map || null, angle: c.angle || null,
  }));
}

// ─── FLOW PLAN ───────────────────────────────────────────────────────────────

function renderFlow(data) {
  const clips   = getClips(data);
  const clipsEl = $('flow-clips');
  const axisEl  = $('flow-axis');
  const tlEl    = $('flow-tl');
  clipsEl.textContent = ''; axisEl.textContent = '';
  $('flow-count').textContent = clips.length ? `${clips.length} CLIPS` : '— CLIPS';

  if (!clips.length) {
    const msg = el('div', '', 'padding:20px;color:#333;letter-spacing:.1em');
    msg.textContent = 'NO FLOW DATA';
    clipsEl.appendChild(msg);
    return;
  }

  const PX       = 14 * S.zoom;
  const totalDur = clips.reduce((s, c) => s + c.duration, 0);
  const minW     = ($('flow-scroll').offsetWidth || 600) - 2;
  tlEl.style.width = Math.max(totalDur * PX, minW) + 'px';

  let cumT = 0;
  clips.forEach((clip, idx) => {
    const w  = Math.max(clip.duration * PX, 20);
    const sc = SECTION_COL[clip.section_role] || '#3a3a3a';
    const tc = TIER_COL[clip.tier] || '#333';
    const m  = EV[clip.top_event?.type] || { icon: '·', col: '#555' };
    const conf = clip.top_event?.confidence ?? 0;

    const div = el('div', 'clip-block', `width:${w}px;background:${sc}1a;border-left-color:${sc}55`);
    div.dataset.idx = idx;

    const tier = el('div', 'clip-tier', `background:${tc}`);
    const icon = el('div', 'clip-icon', `color:${m.col}`);
    icon.textContent = m.icon;
    const conf_bar  = el('div', 'clip-conf');
    const conf_fill = el('div', 'clip-conf-fill', `width:${conf*100}%`);
    conf_bar.appendChild(conf_fill);
    div.appendChild(tier); div.appendChild(icon); div.appendChild(conf_bar);

    div.addEventListener('mouseenter', e => showTip(e, clip));
    div.addEventListener('mousemove',  e => moveTip(e));
    div.addEventListener('mouseleave', hideTip);
    div.addEventListener('click', () => { seekVids(clip.top_event?.t ?? 0); hlBlock(idx); });
    clipsEl.appendChild(div);

    // Axis ticks every 30s of content
    const TICK = 30;
    const tickStart = Math.ceil(cumT / TICK) * TICK;
    for (let t = tickStart; t < cumT + clip.duration; t += TICK) {
      const xPx = ((t - cumT) / clip.duration) * w + cumT * PX;
      const tick = el('div', 'axis-tick', `left:${xPx}px`);
      tick.textContent = fmt(t);
      axisEl.appendChild(tick);
    }
    cumT += clip.duration;
  });
}

// ─── FLOW TOOLTIP (DOM-safe) ─────────────────────────────────────────────────

function tipRow(key, val) {
  const row = el('div', 'tip-row');
  const k = el('span', 'tip-k'); k.textContent = key;
  const v = el('span', 'tip-v'); v.textContent = val;
  row.appendChild(k); row.appendChild(v);
  return row;
}

function showTip(e, clip) {
  const tip = $('flow-tip');
  tip.textContent = '';
  const ev = clip.top_event || {};
  const m  = EV[ev.type] || { icon: '·', lbl: ev.type || '?', col: '#888' };

  const header = el('div', 'tip-ev', `color:${m.col}`);
  header.textContent = `${m.icon} ${m.lbl}`;
  tip.appendChild(header);
  tip.appendChild(tipRow('CLIP',    clip.id || baseName(clip.chunk || '')));
  tip.appendChild(tipRow('TIER',    clip.tier));
  tip.appendChild(tipRow('SECTION', (clip.section_role || '').toUpperCase()));
  tip.appendChild(tipRow('DUR',     clip.duration.toFixed(2) + 's'));
  if (ev.t != null) tip.appendChild(tipRow('EVENT@', Number(ev.t).toFixed(2) + 's'));
  tip.appendChild(tipRow('CONF', pct(ev.confidence ?? 0)));
  if (clip.flow_fit != null) tip.appendChild(tipRow('FIT',    clip.flow_fit.toFixed(2)));
  if (clip.tag)              tip.appendChild(tipRow('TAG',    clip.tag));
  if (clip.map)              tip.appendChild(tipRow('MAP',    clip.map));
  if (clip.event_count)      tip.appendChild(tipRow('EVENTS', clip.event_count));

  tip.classList.add('show');
  moveTip(e);
}

function moveTip(e) {
  const tip = $('flow-tip');
  let x = e.clientX + 14, y = e.clientY - 8;
  if (x + 215 > innerWidth)  x = e.clientX - 220;
  if (y + 240 > innerHeight) y = e.clientY - 240;
  tip.style.left = x + 'px'; tip.style.top = y + 'px';
}

function hideTip() { $('flow-tip').classList.remove('show'); }

function hlBlock(idx) {
  document.querySelectorAll('.clip-block').forEach((b, i) =>
    b.classList.toggle('hl', i === idx));
  const b = document.querySelector(`.clip-block[data-idx="${idx}"]`);
  if (b) b.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
}

// ─── FLOW ZOOM ───────────────────────────────────────────────────────────────

function initZoom() {
  $('btn-zoom-in').addEventListener('click', () => { S.zoom = Math.min(S.zoom*1.6, 10); renderFlow(S.flowData); });
  $('btn-zoom-out').addEventListener('click', () => { S.zoom = Math.max(S.zoom/1.6, .25); renderFlow(S.flowData); });
  $('flow-scroll').addEventListener('wheel', e => {
    e.preventDefault(); $('flow-scroll').scrollLeft += e.deltaY * 2.5;
  }, { passive: false });
}

// ─── EVENT DIVERSITY CHART ───────────────────────────────────────────────────

function renderEventChart(data) {
  const canvas = $('ev-canvas');
  const wrap   = canvas.parentElement;
  canvas.width  = Math.floor(wrap.offsetWidth  - 16);
  canvas.height = Math.floor(wrap.offsetHeight - 12);
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  canvas._rects = [];

  if (!data) {
    ctx.fillStyle = '#333'; ctx.font = '10px "IBM Plex Mono", monospace';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText('NO EVENT DATA — use load buttons', canvas.width/2, canvas.height/2);
    return;
  }

  const counts  = data.event_type_counts || {};
  const weights = data.event_weights || {};
  let entries = Object.entries(counts);
  entries.sort((a, b) => S.evSort === 'weight'
    ? (weights[b[0]] ?? 0) - (weights[a[0]] ?? 0)
    : b[1] - a[1]);

  const total = entries.reduce((s, [, v]) => s + v, 0);
  $('ev-total').textContent = `${total} EVENTS`;

  const maxCount = Math.max(...entries.map(([, v]) => v), 1);
  const LABEL_W  = 74, COUNT_W = 36;
  const BAR_W    = canvas.width - LABEL_W - COUNT_W - 6;
  const rowH     = Math.min(30, Math.floor((canvas.height - 16) / entries.length) - 2);
  const GAP      = 3;
  const startY   = Math.max(8, (canvas.height - entries.length*(rowH+GAP)) / 2);

  entries.forEach(([type, count], i) => {
    const m   = EV[type] || { icon: '·', lbl: type.replace(/_/g,' '), col: '#555' };
    const y   = startY + i * (rowH + GAP);
    const bw  = Math.max(3, (count / maxCount) * BAR_W);
    const sel = S.selEvent === type;
    canvas._rects.push({ type, y, h: rowH, count });

    ctx.fillStyle = '#141414'; ctx.fillRect(LABEL_W, y, BAR_W, rowH);
    ctx.globalAlpha = sel ? 1 : 0.8; ctx.fillStyle = m.col;
    ctx.fillRect(LABEL_W, y, bw, rowH); ctx.globalAlpha = 1;

    const wX = LABEL_W + (weights[type] ?? 0) * BAR_W;
    ctx.save();
    ctx.strokeStyle = 'rgba(255,255,255,.2)'; ctx.lineWidth = 1; ctx.setLineDash([2,3]);
    ctx.beginPath(); ctx.moveTo(wX, y); ctx.lineTo(wX, y+rowH); ctx.stroke();
    ctx.restore();

    if (sel) { ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.5; ctx.strokeRect(LABEL_W-.5, y-.5, BAR_W+1, rowH+1); }

    ctx.fillStyle = sel ? '#fff' : '#888';
    ctx.font = `${sel ? '700 ' : ''}10px "IBM Plex Mono", monospace`;
    ctx.textAlign = 'right'; ctx.textBaseline = 'middle';
    ctx.fillText(`${m.icon} ${m.lbl}`, LABEL_W - 6, y + rowH/2);

    ctx.fillStyle = sel ? m.col : '#555'; ctx.font = '9px "IBM Plex Mono", monospace';
    ctx.textAlign = 'left'; ctx.fillText(count, LABEL_W + bw + 5, y + rowH/2);
  });

  renderEventStats(data, entries[0]?.[0]);
}

function renderEventStats(data, fallbackType) {
  const type  = S.selEvent || fallbackType;
  const stats = (data?.raw_score_stats_per_type || {})[type];
  const el_   = $('ev-stats');
  el_.textContent = '';
  if (!stats) return;

  [
    ['MAX CONF', pct(stats.max || 0)],
    ['MEAN',     pct(stats.mean || 0)],
    ['P90',      pct(stats.p90 || 0)],
    ['>0.55 GATE', stats.n_over_055 ?? '—'],
  ].forEach(([lbl, val]) => {
    const item = el('div', 'ev-stat');
    const l = el('div', 'ev-stat-lbl'); l.textContent = lbl;
    const v = el('div', 'ev-stat-val'); v.textContent = val;
    item.appendChild(l); item.appendChild(v);
    el_.appendChild(item);
  });
}

function handleEvClick(e) {
  const canvas = $('ev-canvas');
  if (!canvas._rects?.length) return;
  const rect = canvas.getBoundingClientRect();
  const y    = e.clientY - rect.top;
  const hit  = canvas._rects.find(r => y >= r.y && y < r.y + r.h);
  if (!hit) return;
  S.selEvent = hit.type === S.selEvent ? null : hit.type;
  renderEventChart(S.eventData);
  const detailEl = $('ev-detail');
  if (!S.selEvent) {
    detailEl.textContent = '';
    const ph = el('div', 'ev-placeholder');
    ph.textContent = 'click bar → top clips for that event type';
    detailEl.appendChild(ph);
  } else {
    renderTopClips(S.selEvent);
  }
}

function renderTopClips(type) {
  const detailEl = $('ev-detail');
  detailEl.textContent = '';
  const data = S.eventData;
  const top5 = (data?.top_5_per_type || {})[type] || [];
  const m    = EV[type] || { icon: '·', lbl: type, col: '#888' };

  if (!top5.length) {
    const ph = el('div', 'ev-placeholder');
    ph.textContent = `no top-clip data for ${type}`;
    detailEl.appendChild(ph);
    return;
  }

  const lbl = el('div', 'ev-type-label', `color:${m.col}`);
  lbl.textContent = `${m.icon} TOP ${type.replace(/_/g,' ').toUpperCase()}`;
  detailEl.appendChild(lbl);

  const list = el('div', 'top-clips');
  top5.forEach((c, i) => {
    const row  = el('div', 'top-row');
    const rank = el('span', 'top-rank'); rank.textContent = `#${i+1}`;
    const name = el('span', 'top-name'); name.textContent = c.clip;
    const conf = el('span', 'top-conf'); conf.textContent = pct(c.confidence);
    const time = el('span', 'top-time'); time.textContent = `@${Number(c.t).toFixed(2)}s`;
    row.appendChild(rank); row.appendChild(name); row.appendChild(conf); row.appendChild(time);

    row.addEventListener('click', () => {
      seekVids(c.t);
      const clips = getClips(S.flowData);
      const idx = clips.findIndex(cl => (cl.id || baseName(cl.chunk||'')) === c.clip);
      if (idx >= 0) hlBlock(idx);
    });
    list.appendChild(row);
  });
  detailEl.appendChild(list);
}

// ─── VIDEO COMPARE ───────────────────────────────────────────────────────────

function initCompare() {
  ['a', 'b'].forEach(slot => {
    const dropEl = $(`drop-${slot}`);
    const inpEl  = $(`inp-vid-${slot}`);
    const vidEl  = $(`vid-${slot}`);

    dropEl.addEventListener('dragover',  e => { e.preventDefault(); dropEl.classList.add('over'); });
    dropEl.addEventListener('dragleave', () => dropEl.classList.remove('over'));
    dropEl.addEventListener('drop', e => {
      e.preventDefault(); dropEl.classList.remove('over');
      if (e.dataTransfer.files[0]) loadVid(slot, e.dataTransfer.files[0]);
    });
    inpEl.addEventListener('change', e => { if (e.target.files[0]) loadVid(slot, e.target.files[0]); });

    vidEl.addEventListener('loadedmetadata', () => {
      $(`meta-${slot}`).textContent = `${fmt(vidEl.duration)} · ${vidEl.videoWidth}×${vidEl.videoHeight}`;
      if (slot === 'a') $('scrub-dur').textContent = fmt(vidEl.duration);
    });
    vidEl.addEventListener('timeupdate', () => {
      if (slot !== 'a' || S.scrubDrag) return;
      updateScrub(vidEl.currentTime, vidEl.duration);
    });
  });

  const track = $('scrub-track');
  track.addEventListener('mousedown', e => { S.scrubDrag = true; applyScrub(e); });
  window.addEventListener('mousemove', e => { if (S.scrubDrag) applyScrub(e); });
  window.addEventListener('mouseup',  () => { S.scrubDrag = false; });

  $('btn-play').addEventListener('click', () => {
    S.playing = !S.playing;
    $('btn-play').textContent = S.playing ? '⏸ PAUSE' : '▶ PLAY';
    [S.vidA, S.vidB].forEach(v => { if (v) S.playing ? v.play() : v.pause(); });
  });

  $('btn-sync').addEventListener('click', () => {
    S.synced = !S.synced;
    $('btn-sync').classList.toggle('on', S.synced);
  });

  $('btn-vmaf').addEventListener('click', () => $('inp-vmaf').click());
  $('inp-vmaf').addEventListener('change', e => { if (e.target.files[0]) loadVMAF(e.target.files[0]); });
}

function loadVid(slot, file) {
  const vidEl  = $(`vid-${slot}`);
  const dropEl = $(`drop-${slot}`);
  vidEl.src = URL.createObjectURL(file);
  vidEl.load();
  vidEl.classList.add('loaded');
  dropEl.classList.add('hidden');
  $(`tag-${slot}`).textContent = `VERSION ${slot.toUpperCase()} — ${file.name}`;
  if (slot === 'a') S.vidA = vidEl; else S.vidB = vidEl;
}

function applyScrub(e) {
  const rect  = $('scrub-track').getBoundingClientRect();
  const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
  if (!S.vidA?.duration) return;
  S.vidA.currentTime = ratio * S.vidA.duration;
  if (S.synced && S.vidB?.duration) S.vidB.currentTime = ratio * S.vidB.duration;
  updateScrub(ratio * S.vidA.duration, S.vidA.duration);
}

function updateScrub(t, dur) {
  const p = dur > 0 ? (t / dur * 100).toFixed(3) + '%' : '0%';
  $('scrub-fill').style.width = p;
  $('scrub-thumb').style.left = p;
  $('scrub-cur').textContent  = fmt(t);
}

function seekVids(t) {
  if (S.vidA?.duration) S.vidA.currentTime = Math.min(t, S.vidA.duration);
  if (S.synced && S.vidB?.duration) S.vidB.currentTime = Math.min(t, S.vidB.duration);
  if (S.vidA) updateScrub(t, S.vidA.duration || 1);
}

// ─── SCRUB SEAM MARKERS ──────────────────────────────────────────────────────

function placeScrubMarkers(data) {
  const marks = $('scrub-marks');
  marks.textContent = '';
  const clips = getClips(data);
  if (!clips.length) return;
  const totalDur = clips.reduce((s, c) => s + c.duration, 0);
  if (!totalDur) return;
  let cumT = 0;
  clips.forEach((clip, i) => {
    if (i > 0) {
      const mark = el('div', 'scrub-mark',
        `left:${(cumT/totalDur*100).toFixed(3)}%;background:${SECTION_COL[clip.section_role]||'#444'};opacity:.6`);
      marks.appendChild(mark);
    }
    cumT += clip.duration;
  });
}

// ─── VMAF ────────────────────────────────────────────────────────────────────

function loadVMAF(file) {
  const reader = new FileReader();
  reader.onload = e => { try { renderVMAF(JSON.parse(e.target.result)); } catch {} };
  reader.readAsText(file);
}

function renderVMAF(data) {
  const wrap = $('vmaf-wrap');
  wrap.textContent = '';
  const frames = data.frames || data.VMAF?.frames || data.metrics?.frames || [];
  if (!frames.length) {
    const msg = el('span', 'vmaf-empty'); msg.textContent = 'unrecognised vmaf format';
    wrap.appendChild(msg); return;
  }

  const scores = frames.map(f => f.metrics?.vmaf ?? f.VMAF ?? f.vmaf ?? 0);
  const minS = Math.min(...scores), range = (Math.max(...scores) - minS) || 1;
  const avg  = (scores.reduce((a,b) => a+b, 0) / scores.length).toFixed(1);

  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', `0 0 ${scores.length} 100`);
  svg.setAttribute('preserveAspectRatio', 'none');
  svg.style.cssText = 'width:100%;height:100%;position:absolute;inset:0';

  const pl = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
  pl.setAttribute('points', scores.map((s,i) => `${i},${(100-(s-minS)/range*100).toFixed(2)}`).join(' '));
  pl.setAttribute('fill', 'none');
  pl.setAttribute('stroke', '#f5a623');
  pl.setAttribute('stroke-width', '.5');
  svg.appendChild(pl);

  wrap.style.position = 'relative';
  wrap.appendChild(svg);

  const lbl = el('span', '', 'position:absolute;right:4px;top:0;font-size:7px;color:#f5a623;line-height:12px;z-index:1');
  lbl.textContent = `avg ${avg}`;
  wrap.appendChild(lbl);
}

// ─── MANUAL JSON LOAD ────────────────────────────────────────────────────────

function initManualLoad() {
  $('btn-load-flow').addEventListener('click',  () => $('inp-flow').click());
  $('btn-load-event').addEventListener('click', () => $('inp-event').click());

  $('inp-flow').addEventListener('change', e => {
    if (!e.target.files[0]) return;
    const r = new FileReader();
    r.onload = ev => {
      try {
        S.flowData = JSON.parse(ev.target.result);
        renderFlow(S.flowData);
        placeScrubMarkers(S.flowData);
        setStatus(`flow loaded · ${getClips(S.flowData).length} clips`, 'ok');
      } catch { setStatus('flow json parse error', 'err'); }
    };
    r.readAsText(e.target.files[0]);
  });

  $('inp-event').addEventListener('change', e => {
    if (!e.target.files[0]) return;
    const r = new FileReader();
    r.onload = ev => {
      try {
        S.eventData = JSON.parse(ev.target.result);
        renderEventChart(S.eventData);
        setStatus('event data loaded', 'ok');
      } catch { setStatus('event json parse error', 'err'); }
    };
    r.readAsText(e.target.files[0]);
  });
}

// ─── SORT + RESIZE ───────────────────────────────────────────────────────────

function initEvSort() {
  $('btn-ev-sort').addEventListener('click', () => {
    S.evSort = S.evSort === 'count' ? 'weight' : 'count';
    $('btn-ev-sort').textContent = `≡ ${S.evSort.toUpperCase()}`;
    renderEventChart(S.eventData);
  });
}

// ─── INIT ────────────────────────────────────────────────────────────────────

async function init() {
  initParticles();
  buildPartNav();
  initCompare();
  initZoom();
  initEvSort();
  initManualLoad();
  $('ev-canvas').addEventListener('click', handleEvClick);
  window.addEventListener('resize', () => renderEventChart(S.eventData));
  await loadPart(S.part);
}

init();
