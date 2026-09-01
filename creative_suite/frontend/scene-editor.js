/* PANTHEON Scene Editor — the cinematic workspace.
 *
 * THREE CLOCKS, NEVER COLLAPSED (§19-20)
 * --------------------------------------
 *   demo_us --TimeMap--> edit_us --MusicPlacement--> music_us
 *
 * `edit_us` is the ONE authoritative playhead and it is an integer number of
 * microseconds in this file, everywhere, without exception. Floats appear
 * only inside pixel math and inside the human-readable clock strings; a
 * float never round-trips back into state. Both projections used here are
 * the backend's own arithmetic, restated so the playhead can move at 60 Hz
 * without a network hop — every value that is PERSISTED still comes from,
 * and goes back to, the server.
 *
 * UI-1: no innerHTML with data. Every node is built with el()/textContent.
 * §52: zoom / scroll / expanded lanes / panel widths are UI state and are
 * PUT to the draft's UI keys, which the backend keeps out of both hashes.
 */
"use strict";

/* ============================== constants ============================== */

const LANE_H = {
  GAME_EVENTS: 52, TIME: 34, CAMERA: 26, FX: 26, LOOK: 18, TRANSITION: 24,
  MUSIC_WAVEFORM: 56, MUSIC_EVENTS: 30, MUSIC_STRUCTURE: 22,
};
const MUSIC_LANES = new Set(["MUSIC_WAVEFORM", "MUSIC_EVENTS", "MUSIC_STRUCTURE"]);

const EVENT_COLOR = {
  PROJECTILE_LAUNCH: "#5a8fc0", PROJECTILE_IMPACT: "#d4af37",
  FRAG: "#c05050", LG_BURST: "#4caf7d", LG_CONTACT: "#2f6a4c",
  FIRE: "#3d5f7d", MULTIKILL: "#c9a227", DODGE_HERO: "#8a6fc0",
  NEAR_MISS: "#6b5590", ROUND_WIN: "#d4af37", MOVEMENT_PEAK: "#7d7d86",
};
const MUSIC_EVENT_COLOR = {
  BEAT: "#3a3a46", BAR_GRID_ESTIMATE: "#55556a", ACCENT: "#8a6fc0",
  DROP_CANDIDATE: "#c05050", BUILD_CANDIDATE: "#c9a227",
  PHRASE_BOUNDARY_ESTIMATE: "#4d6f8f", SECTION_BOUNDARY_ESTIMATE: "#5a8fc0",
};
const SPAN_KINDS = new Set(["LG_BURST", "MULTIKILL"]);

// When two captions collide, the more editorially important one wins the
// space. Losing "PROJECTILE IMPACT" to a "MOVEMENT PEAK" that happened to
// be drawn first would hide the money shot.
const EVENT_LABEL_PRIORITY = {
  PROJECTILE_IMPACT: 100, FRAG: 95, ROUND_WIN: 92, MULTIKILL: 88,
  DODGE_HERO: 80, LG_BURST: 70, PROJECTILE_LAUNCH: 60, NEAR_MISS: 50,
  MOVEMENT_PEAK: 30, FIRE: 20, LG_CONTACT: 10,
};

/* ============================== tiny DOM =============================== */

const $ = (id) => document.getElementById(id);

function el(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text !== undefined && text !== null) n.textContent = String(text);
  return n;
}

function clear(node) { node.replaceChildren(); }

/** Integer microseconds -> "m:ss.mmm". Presentation only — never parsed back. */
function fmtUs(us) {
  if (us === null || us === undefined) return "–";
  const neg = us < 0;
  const abs = Math.abs(us);
  const ms = Math.floor(abs / 1000);
  const s = Math.floor(ms / 1000);
  return `${neg ? "−" : ""}${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}` +
         `.${String(ms % 1000).padStart(3, "0")}`;
}

/** Signed delta in ms, the way a director says it out loud: "+18ms". */
function fmtDelta(us) {
  const ms = Math.round(us / 1000);
  return `${ms >= 0 ? "+" : "−"}${Math.abs(ms)}ms`;
}

/* ================================ state ================================ */

const state = {
  fragId: null,
  projection: null,
  draft: null,
  auditions: [],
  why: null,
  schema: null,
  view: { zoom: 1, scrollUs: 0, playheadUs: 0 },
  selection: null,
  showGuides: true,
  showMicro: false,
  snap: false,
  drag: null,
  laneRects: [],
  previewKey: null,
  previewTimer: null,
  uiSaveTimer: null,
  toastTimer: null,
};

/* =============================== the API =============================== */

async function api(path, options) {
  const res = await fetch(path, options);
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail || detail; } catch (err) { /* not json */ }
    throw new Error(`${res.status} ${detail}`);
  }
  return res.json();
}

const jsonBody = (body) => ({
  method: "PUT", headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});
const postBody = (body) => ({
  method: "POST", headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body || {}),
});

/* --------------------------------------------------------------- loading */

/** The URL carries IDENTITY only — "frag-5979" / "recipe-<sha>". */
function sceneKeyFromUrl() {
  const parts = window.location.pathname.split("/").filter(Boolean);
  return parts.length > 1 ? decodeURIComponent(parts[1]) : "";
}

/** Resolve the URL's identity to a frag. The server owns the mapping so a
 *  saved scene's `recipe-<sha>` link keeps working after any re-rank. */
async function resolveSceneKey(key) {
  const m = String(key).match(/^frag-(\d+)$/);
  if (m) return Number(m[1]);
  try {
    const res = await api(`/api/scene-editor/resolve/${encodeURIComponent(key)}`);
    return res.frag_id;
  } catch (err) {
    banner(`Scene key "${key}" could not be resolved: ${err.message}`);
    return null;
  }
}

async function boot() {
  const key = sceneKeyFromUrl();
  if (!key) {
    banner("No scene in the URL. Open one from /frags with OPEN IN EDITOR.");
    return;
  }
  const fragId = await resolveSceneKey(key);
  if (fragId === null) return;
  state.fragId = fragId;
  try {
    state.schema = await api("/api/scene-editor/schema");
  } catch (err) {
    banner(`Scene editor schema unavailable: ${err.message}`);
  }
  await reload();
  wireControls();
  window.addEventListener("resize", draw);
}

async function reload() {
  try {
    applyState(await api(`/api/scene-editor/${state.fragId}`));
  } catch (err) {
    banner(`Could not load scene #${state.fragId}: ${err.message}`);
  }
}

function applyState(data) {
  state.projection = data.projection;
  state.draft = data.draft;
  state.auditions = data.auditions || [];
  state.why = data.why_this_matches || null;
  // Restore the workspace from the draft's UI keys (§52) on first load only.
  if (state.view.zoom === 1 && state.view.scrollUs === 0) {
    state.view.zoom = data.draft.zoom || 1;
    state.view.scrollUs = data.draft.scroll_us || 0;
    state.view.playheadUs = data.draft.playhead_us || 0;
    state.snap = !!data.draft.snap_enabled;
  }
  renderAll();
}

function applyDraft(draft) {
  state.draft = draft;
  renderStatus();
  renderInspector();
  draw();
}

/* ============================== chrome ================================= */

function banner(text) {
  const node = $("banner");
  node.textContent = text;
  node.classList.add("show");
}

function toast(text) {
  const node = $("tl-toast");
  node.textContent = text;
  node.classList.add("show");
  clearTimeout(state.toastTimer);
  state.toastTimer = setTimeout(() => node.classList.remove("show"), 2400);
}

function renderStatus() {
  const pill = $("draft-status");
  const unsaved = state.draft && state.draft.status === "UNSAVED";
  pill.textContent = unsaved ? "DRAFT · UNSAVED" : "DRAFT · CLEAN";
  pill.className = `status-pill ${unsaved ? "unsaved" : "clean"}`;
  $("btn-undo").disabled = !state.draft || !state.draft.undo_depth;
  $("btn-undo").textContent = state.draft && state.draft.undo_next
    ? `UNDO · ${String(state.draft.undo_next).toUpperCase()}` : "UNDO";
  const p = state.projection;
  if (p) {
    $("scene-title").textContent =
      `#${p.frag_id} · ${p.weapon || "?"} · ${p.demo.name} · ` +
      `recipe ${p.recipe_id.slice(0, 12)}`;
  }
}

function renderAll() {
  renderStatus();
  renderLaneLabels();
  renderInspector();
  renderClocks();
  draw();
}

/* ============================ the three clocks ========================= */

/** edit_us -> demo_us, walking the SAME TimeMap the backend hashed. */
function editToDemo(editUs) {
  const segments = (state.projection.lanes.TIME || {}).segments || [];
  for (const s of segments) {
    if (editUs < s.edit_start_us || editUs > s.edit_end_us) continue;
    if (s.kind === "freeze") return s.demo_start_us;   // zero demo span
    return s.demo_start_us +
           Math.round((editUs - s.edit_start_us) * s.rate_num / s.rate_den);
  }
  return null;
}

/** edit_us -> music_us via MusicPlacement. Null when no track is placed. */
function editToMusic(editUs) {
  const p = state.draft && state.draft.music_placement;
  if (!p) return null;
  return p.source_start_us + editUs - (p.program_edit_start_us || 0);
}

function renderClocks() {
  const editUs = state.view.playheadUs;
  $("clk-edit").textContent = fmtUs(editUs);
  $("clk-edit-sub").textContent = `${editUs} µs`;
  const demoUs = state.projection ? editToDemo(editUs) : null;
  $("clk-demo").textContent = fmtUs(demoUs);
  $("clk-demo-sub").textContent = demoUs === null
    ? "outside the scene window" : `${demoUs} µs · demo absolute`;
  const musicUs = editToMusic(editUs);
  $("clk-music").textContent = fmtUs(musicUs);
  const music = state.projection && state.projection.lanes.MUSIC_WAVEFORM;
  $("clk-music-sub").textContent = musicUs === null
    ? "no track placed" : `${musicUs} µs · ${music ? music.track_label : ""}`;
}

/* ============================= lane labels ============================= */

function laneCount(lane) {
  const lanes = state.projection.lanes;
  switch (lane) {
    case "GAME_EVENTS": return visibleGameEvents().length;
    case "TIME": return (lanes.TIME.segments || []).length;
    case "CAMERA": return (lanes.CAMERA.stages || []).length;
    case "FX": return (lanes.FX.cues || []).length;
    case "LOOK": return 1;
    case "TRANSITION": return state.projection.lanes.TRANSITION ? 1 : 0;
    case "MUSIC_WAVEFORM": return lanes.MUSIC_WAVEFORM ? 1 : 0;
    case "MUSIC_EVENTS": return (lanes.MUSIC_EVENTS || []).length;
    case "MUSIC_STRUCTURE": return (lanes.MUSIC_STRUCTURE || []).length;
    default: return 0;
  }
}

function renderLaneLabels() {
  const box = $("lane-labels");
  clear(box);
  for (const lane of state.projection.lane_order) {
    const row = el("div", "lane-label");
    row.style.height = `${LANE_H[lane]}px`;
    if (state.selection && state.selection.lane === lane) row.classList.add("sel");
    row.appendChild(el("span", "", lane.replace(/_/g, " ")));
    row.appendChild(el("span", "cnt", laneCount(lane)));
    row.addEventListener("click", () => {
      state.selection = { lane };
      renderLaneLabels();
      renderInspector();
      draw();
    });
    box.appendChild(row);
  }
}

/* ========================== canvas geometry ============================ */

function canvasMetrics() {
  const rect = $("tl-canvas").getBoundingClientRect();
  const duration = Math.max(1, state.projection.duration_us);
  // A collapsed or hidden pane reports width 0. Left unguarded that makes
  // pxPerUs 0, and every `x / pxPerUs` becomes Infinity — which is how a
  // drag once wrote `source_start_us: null` into the placement and got a
  // 422 back. Scale is never allowed to be zero.
  const width = Math.max(1, rect.width);
  return { width, height: rect.height, duration, usable: rect.width >= 1,
           pxPerUs: (width / duration) * state.view.zoom };
}

const xOf = (editUs, m) => (editUs - state.view.scrollUs) * m.pxPerUs;
const usOf = (x, m) => Math.round(x / m.pxPerUs) + state.view.scrollUs;

function visibleGameEvents() {
  const events = state.projection.lanes.GAME_EVENTS.events || [];
  if (state.showMicro) return events;
  const hidden = new Set(state.draft ? state.draft.hidden_event_kinds || [] : []);
  return events.filter((e) => !hidden.has(e.kind));
}

/* ============================== drawing ================================ */

function draw() {
  const canvas = $("tl-canvas");
  const wrap = $("canvas-wrap");
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.max(1, Math.floor(wrap.clientWidth * dpr));
  canvas.height = Math.max(1, Math.floor(wrap.clientHeight * dpr));
  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  if (!state.projection) return;
  const m = canvasMetrics();
  ctx.clearRect(0, 0, m.width, m.height);

  state.laneRects = [];
  let top = 0;
  for (const lane of state.projection.lane_order) {
    const h = LANE_H[lane];
    state.laneRects.push({ lane, top, height: h });
    ctx.fillStyle = MUSIC_LANES.has(lane) ? "#131318" : "#101013";
    ctx.fillRect(0, top, m.width, h);
    ctx.strokeStyle = "#232329";
    ctx.beginPath();
    ctx.moveTo(0, top + h - 0.5); ctx.lineTo(m.width, top + h - 0.5);
    ctx.stroke();
    drawLane(ctx, lane, top, h, m);
    top += h;
  }
  drawGuides(ctx, m);
  drawPlayhead(ctx, m, top);
}

function laneRect(lane) {
  return state.laneRects.find((x) => x.lane === lane) || null;
}

function drawLane(ctx, lane, top, h, m) {
  const lanes = state.projection.lanes;
  switch (lane) {
    case "GAME_EVENTS": return drawGameEvents(ctx, top, h, m);
    case "TIME": return drawTime(ctx, top, h, m);
    case "CAMERA": return drawSpans(ctx, top, h, m, "CAMERA",
      (lanes.CAMERA.stages || []).filter((s) => s.resolved),
      (s) => s.stage, "#4d6f8f");
    case "FX": return drawSpans(ctx, top, h, m, "FX",
      (lanes.FX.cues || []).filter((c) => c.resolved),
      (c) => `${c.effect_type} · ${c.intensity_level}`, "#8a6fc0");
    case "LOOK": return drawLook(ctx, top, h, m);
    case "TRANSITION": return drawTransition(ctx, top, h, m);
    case "MUSIC_WAVEFORM": return drawWaveform(ctx, top, h, m);
    case "MUSIC_EVENTS": return drawMusicEvents(ctx, top, h, m);
    case "MUSIC_STRUCTURE": return drawStructure(ctx, top, h, m);
    default: return undefined;
  }
}

/** Draw a label only if it clears the last one on this row.
 *  Overlapping captions read as a single garbled word ("LG BURSTNEAR MISS"),
 *  which is worse than no caption — the mark itself is still there. */
function labelGuard() {
  const taken = [];
  return (ctx, text, x, y) => {
    const right = x + ctx.measureText(text).width + 6;
    if (taken.some(([a, b]) => x < b && right > a)) return;
    ctx.fillText(text, x, y);
    taken.push([x, right]);
  };
}

function drawGameEvents(ctx, top, h, m) {
  ctx.save();
  ctx.font = "9px Consolas, monospace";
  const label = labelGuard();
  const events = visibleGameEvents();
  const captions = [...events].sort((a, b) =>
    (EVENT_LABEL_PRIORITY[b.kind] || 0) - (EVENT_LABEL_PRIORITY[a.kind] || 0));
  for (const e of events) {
    const x = xOf(e.edit_us, m);
    if (x < -90 || x > m.width + 90) continue;
    const color = EVENT_COLOR[e.kind] || "#7d7d86";
    if (SPAN_KINDS.has(e.kind) && e.edit_end_us !== undefined) {
      const x2 = xOf(e.edit_end_us, m);
      ctx.fillStyle = `${color}33`;
      ctx.fillRect(x, top + 6, Math.max(2, x2 - x), h - 22);
      ctx.strokeStyle = color;
      ctx.strokeRect(x + 0.5, top + 6.5, Math.max(2, x2 - x), h - 22);
    } else {
      ctx.fillStyle = color;
      ctx.fillRect(x - 1, top + 6, 2.5, h - 22);
      ctx.beginPath();
      ctx.arc(x, top + 6, 3, 0, Math.PI * 2);
      ctx.fill();
    }
  }
  // Second pass: captions, highest priority first, so a crowded stretch
  // keeps the name of the event that actually matters.
  for (const e of captions) {
    const x = xOf(e.edit_us, m);
    if (x < -90 || x > m.width + 90) continue;
    const selected = state.selection && state.selection.id === e.id;
    ctx.fillStyle = selected ? "#d4af37" : "#8f8f99";
    label(ctx, e.kind.replace(/_/g, " "), x + 5, top + h - 6);
  }
  ctx.restore();
}

function drawTime(ctx, top, h, m) {
  ctx.save();
  ctx.font = "9px Consolas, monospace";
  for (const s of state.projection.lanes.TIME.segments) {
    const x = xOf(s.edit_start_us, m);
    const w = Math.max(1, xOf(s.edit_end_us, m) - x);
    // A FREEZE has zero demo duration and positive EDIT duration. It is
    // drawn at its true edit width, hatched, because that width is exactly
    // what the viewer will sit through.
    const freeze = s.kind === "freeze";
    ctx.fillStyle = freeze ? "#2a2233" : (s.kind === "slow" ? "#1e2a33" : "#191a1e");
    ctx.fillRect(x, top + 4, w, h - 10);
    if (freeze) {
      ctx.strokeStyle = "#8a6fc0";
      ctx.lineWidth = 1;
      for (let hx = x; hx < x + w; hx += 4) {
        ctx.beginPath();
        ctx.moveTo(hx, top + h - 6); ctx.lineTo(hx + 5, top + 4);
        ctx.stroke();
      }
    }
    const sel = state.selection && state.selection.lane === "TIME" &&
                state.selection.index === s.index;
    ctx.strokeStyle = sel ? "#d4af37" : (freeze ? "#8a6fc0" : "#3a3a46");
    ctx.strokeRect(x + 0.5, top + 4.5, w, h - 10);
    if (w > 26) {
      ctx.fillStyle = freeze ? "#b9a2d6" : "#9a9aa4";
      ctx.fillText(freeze ? "FREEZE" : s.rate_label, x + 4, top + h - 10);
    }
  }
  ctx.restore();
}

function drawSpans(ctx, top, h, m, lane, items, labelOf, color) {
  ctx.save();
  ctx.font = "9px Consolas, monospace";
  for (const item of items) {
    const x = xOf(item.edit_start_us, m);
    const w = Math.max(2, xOf(item.edit_end_us, m) - x);
    ctx.fillStyle = `${color}2e`;
    ctx.fillRect(x, top + 4, w, h - 9);
    const sel = state.selection && state.selection.lane === lane &&
                state.selection.index === item.index;
    ctx.strokeStyle = sel ? "#d4af37" : color;
    ctx.strokeRect(x + 0.5, top + 4.5, w, h - 9);
    if (w > 40) {
      ctx.fillStyle = "#a8a8b2";
      ctx.fillText(labelOf(item), x + 5, top + h - 9);
    }
  }
  ctx.restore();
}

function drawTransition(ctx, top, h, m) {
  // A real block, not a music marker: it spans from where the outgoing
  // scene starts handing over to the cut itself, and the cut is drawn as a
  // hard edge because that is what the viewer sees.
  const tr = state.projection.lanes.TRANSITION;
  if (!tr) return;
  const x0 = xOf(tr.start_edit_us, m);
  const xc = xOf(tr.cut_edit_us, m);
  ctx.save();
  const w = Math.max(2, xc - x0);
  ctx.fillStyle = "#3b2f18";
  ctx.fillRect(x0, top + 3, w, h - 7);
  ctx.strokeStyle = "#d4af37";
  ctx.lineWidth = 1;
  ctx.strokeRect(x0 + 0.5, top + 3.5, w, h - 7);
  ctx.beginPath();                       // the cut
  ctx.moveTo(xc + 0.5, top + 1);
  ctx.lineTo(xc + 0.5, top + h - 2);
  ctx.lineWidth = 2;
  ctx.strokeStyle = "#e8c451";
  ctx.stroke();
  ctx.font = "9px Consolas, monospace";
  ctx.fillStyle = "#e8c451";
  const label = `${tr.type} → ${tr.visual_variant}`;
  ctx.fillText(label, Math.max(x0 + 5, 5), top + h - 7);
  ctx.restore();
}

function drawLook(ctx, top, h, m) {
  const look = state.projection.lanes.LOOK.visual_look;
  const x = xOf(0, m);
  const w = m.duration * m.pxPerUs;
  ctx.save();
  ctx.fillStyle = "#1b1a24";
  ctx.fillRect(x, top + 3, w, h - 7);
  ctx.strokeStyle = "#3a3a46";
  ctx.strokeRect(x + 0.5, top + 3.5, w, h - 7);
  ctx.font = "9px Consolas, monospace";
  ctx.fillStyle = "#9a9aa4";
  ctx.fillText(`LOOK · ${look}`, x + 6, top + h - 6);
  ctx.restore();
}

function drawWaveform(ctx, top, h, m) {
  const music = state.projection.lanes.MUSIC_WAVEFORM;
  if (!music) {
    ctx.save();
    ctx.font = "10px Consolas, monospace";
    ctx.fillStyle = "#55555e";
    ctx.fillText("no track placed", 8, top + h / 2 + 3);
    ctx.restore();
    return;
  }
  const env = music.envelope || [];
  if (!env.length) return;
  const x0 = xOf(music.envelope_edit_start_us, m);
  const x1 = xOf(music.envelope_edit_end_us, m);
  const span = Math.max(1, x1 - x0);
  const mid = top + h / 2 + 3;
  const half = (h - 18) / 2;
  ctx.save();
  ctx.fillStyle = state.drag ? "#a888e0" : "#6b5590";
  const bw = Math.max(1, span / env.length);
  for (let i = 0; i < env.length; i++) {
    const bx = x0 + (i * span) / env.length;
    if (bx < -4 || bx > m.width + 4) continue;
    const hi = env[i][1];
    ctx.fillRect(bx, mid - hi * half, bw, Math.max(1, hi * half * 2));
  }
  ctx.strokeStyle = "#2a2a33";
  ctx.beginPath(); ctx.moveTo(0, mid); ctx.lineTo(m.width, mid); ctx.stroke();
  ctx.font = "9px Consolas, monospace";
  ctx.fillStyle = "#b9a2d6";
  ctx.fillText(`${music.track_label}  ·  drag to move music only`, 6, top + 11);
  ctx.restore();
}

function drawMusicEvents(ctx, top, h, m) {
  ctx.save();
  ctx.font = "8px Consolas, monospace";
  const label = labelGuard();
  for (const e of state.projection.lanes.MUSIC_EVENTS || []) {
    const x = xOf(e.edit_us, m);
    if (x < -70 || x > m.width + 70) continue;
    const tall = e.kind !== "BEAT" && e.kind !== "BAR_GRID_ESTIMATE";
    ctx.fillStyle = MUSIC_EVENT_COLOR[e.kind] || "#55556a";
    ctx.fillRect(x, top + (tall ? 4 : h - 16), 1.6, tall ? h - 16 : 11);
    // The full name is drawn or not drawn — never truncated. An
    // "ESTIMATE" suffix clipped to "ESTIM" would quietly become a claim.
    if (tall) label(ctx, e.kind.replace(/_/g, " "), x + 3, top + 11);
  }
  ctx.restore();
}

function drawStructure(ctx, top, h, m) {
  ctx.save();
  ctx.font = "8px Consolas, monospace";
  for (const r of state.projection.lanes.MUSIC_STRUCTURE || []) {
    const x = xOf(r.edit_start_us, m);
    const w = Math.max(2, xOf(r.edit_end_us, m) - x);
    ctx.fillStyle = "#241f30";
    ctx.fillRect(x, top + 3, w, h - 7);
    ctx.strokeStyle = "#4a3d64";
    ctx.strokeRect(x + 0.5, top + 3.5, w, h - 7);
    if (w > 60) {
      ctx.fillStyle = "#9b8bbd";
      ctx.fillText(r.kind, x + 4, top + h - 7);
    }
  }
  ctx.restore();
}

function drawGuides(ctx, m) {
  if (!state.showGuides) return;
  const guides = state.projection.guides || [];
  const gRect = laneRect("GAME_EVENTS");
  const mRect = laneRect("MUSIC_EVENTS");
  if (!gRect || !mRect || !guides.length) return;
  ctx.save();
  ctx.setLineDash([3, 3]);
  ctx.font = "8.5px Consolas, monospace";
  for (const g of guides) {
    const gx = xOf(g.game_edit_us, m);
    const mx = xOf(g.music_edit_us, m);
    if (Math.max(gx, mx) < 0 || Math.min(gx, mx) > m.width) continue;
    const aligned = Math.abs(g.delta_us) <= 40000;
    ctx.strokeStyle = aligned ? "#4caf7d" : "#6b5590";
    ctx.beginPath();
    ctx.moveTo(gx, gRect.top + gRect.height - 4);
    ctx.lineTo(mx, mRect.top + 6);
    ctx.stroke();
    ctx.fillStyle = aligned ? "#4caf7d" : "#8a7ba8";
    ctx.fillText(fmtDelta(g.delta_us), (gx + mx) / 2 + 3,
                 (gRect.top + gRect.height + mRect.top) / 2);
  }
  ctx.restore();
}

function drawPlayhead(ctx, m, bottom) {
  const x = xOf(state.view.playheadUs, m);
  ctx.save();
  ctx.strokeStyle = "#d4af37";
  ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(x + 0.5, 0); ctx.lineTo(x + 0.5, bottom); ctx.stroke();
  ctx.fillStyle = "#d4af37";
  ctx.beginPath();
  ctx.moveTo(x - 4, 0); ctx.lineTo(x + 4, 0); ctx.lineTo(x, 6);
  ctx.closePath(); ctx.fill();
  ctx.restore();
}

/* ============================ interaction ============================== */

/** Keep the whole scene window inside the track's real duration. */
function clampSourceStart(sourceStartUs) {
  const music = state.projection.lanes.MUSIC_WAVEFORM;
  if (!music || !music.track_duration_us) return sourceStartUs;
  const offset = (state.draft.music_placement || {}).program_edit_start_us || 0;
  const latest = music.track_duration_us - state.projection.duration_us;
  return Math.max(offset, Math.min(offset + Math.max(0, latest), sourceStartUs));
}

function laneAt(y) {
  return state.laneRects.find((r) => y >= r.top && y < r.top + r.height) || null;
}

function hitGameEvent(x, m) {
  let best = null;
  for (const e of visibleGameEvents()) {
    const d = Math.abs(xOf(e.edit_us, m) - x);
    if (d < 7 && (best === null || d < best.d)) best = { e, d };
  }
  return best && best.e;
}

function wireControls() {
  const canvas = $("tl-canvas");

  canvas.addEventListener("mousedown", (ev) => {
    const rect = canvas.getBoundingClientRect();
    const x = ev.clientX - rect.left, y = ev.clientY - rect.top;
    const m = canvasMetrics();
    const lane = laneAt(y);
    if (!lane) return;
    if (MUSIC_LANES.has(lane.lane) && state.draft.music_placement) {
      // §29/§35: dragging music edits MusicPlacement. The TimeMap is not
      // reachable from here — gameplay timing cannot move by accident.
      state.drag = { startX: x, appliedUs: 0,
                     placement: Object.assign({}, state.draft.music_placement),
                     startSourceUs: state.draft.music_placement.source_start_us };
      canvas.style.cursor = "grabbing";
      return;
    }
    selectAt(lane, x, m);
    setPlayhead(usOf(x, m));
  });

  window.addEventListener("mousemove", (ev) => {
    if (!state.drag) return;
    const rect = canvas.getBoundingClientRect();
    const m = canvasMetrics();
    let deltaUs = Math.round((ev.clientX - rect.left - state.drag.startX) / m.pxPerUs);
    // Belt and braces: an integer microsecond or nothing. State never takes
    // a NaN/Infinity, so a degenerate viewport can only stall the drag —
    // it can never corrupt the placement.
    if (!Number.isFinite(deltaUs)) return;
    // Moving the music LATER on the timeline means starting EARLIER in the
    // track, hence the minus. Integer microseconds throughout.
    // Clamped so the scene window stays inside the actual audio: the drag
    // simply stops at the track's edges rather than producing a placement
    // the server has to refuse.
    const wanted = state.drag.startSourceUs - deltaUs;
    const next = clampSourceStart(wanted);
    deltaUs = state.drag.startSourceUs - next;
    state.draft.music_placement = Object.assign({}, state.draft.music_placement,
      { source_start_us: next });
    // `deltaUs` is measured from the mousedown, but reprojectMusicLocally
    // MUTATES the lanes in place. Feeding it the cumulative figure every
    // frame would shift an already-shifted lane, so the waveform would race
    // away from the cursor. Apply only what has not been applied yet.
    reprojectMusicLocally(deltaUs - state.drag.appliedUs);
    state.drag.appliedUs = deltaUs;
    draw();
    renderClocks();
  });

  window.addEventListener("mouseup", async () => {
    if (!state.drag) return;
    const placement = state.draft.music_placement;
    const original = state.drag.placement;
    state.drag = null;
    canvas.style.cursor = "crosshair";
    try {
      applyDraft(await api(`/api/scene-editor/${state.fragId}/music/placement`,
                           jsonBody({ placement })));
      await refreshProjection();
      toast("MUSIC PLACEMENT MOVED · gameplay timing unchanged");
    } catch (err) {
      // Never leave an unsaved placement on screen looking authoritative:
      // put the pre-drag value back and re-sync with the server.
      state.draft.music_placement = original;
      banner(`Could not save placement — reverted: ${err.message}`);
      await refreshProjection();
    }
  });

  canvas.addEventListener("wheel", (ev) => {
    ev.preventDefault();
    const rect = canvas.getBoundingClientRect();
    const m = canvasMetrics();
    const cursorX = ev.clientX - rect.left;
    setZoom(state.view.zoom * (ev.deltaY < 0 ? 1.18 : 1 / 1.18),
            usOf(cursorX, m), cursorX);
  }, { passive: false });

  $("zoom-in").addEventListener("click", () => setZoom(state.view.zoom * 1.4));
  $("zoom-out").addEventListener("click", () => setZoom(state.view.zoom / 1.4));
  $("zoom-fit").addEventListener("click", () => {
    state.view.scrollUs = 0;
    setZoom(1);
  });
  $("snap-toggle").addEventListener("click", (ev) => {
    state.snap = !state.snap;
    ev.currentTarget.textContent = `SNAP · ${state.snap ? "ON" : "OFF"}`;
    ev.currentTarget.classList.toggle("on", state.snap);
    // Optional by design (§36). Forced alignment is what made the previous
    // matcher saturate 32 tracks at max score.
    saveUiState({ snap_enabled: state.snap });
    toast(state.snap ? "SNAP ON · optional assist, never enforced" : "SNAP OFF");
  });
  $("guides-toggle").addEventListener("click", (ev) => {
    state.showGuides = !state.showGuides;
    ev.currentTarget.classList.toggle("on", state.showGuides);
    draw();
  });
  $("micro-toggle").addEventListener("click", (ev) => {
    state.showMicro = !state.showMicro;
    ev.currentTarget.classList.toggle("on", state.showMicro);
    renderLaneLabels();
    renderInspector();
    draw();
  });

  $("btn-save").addEventListener("click", saveRecipe);
  $("btn-undo").addEventListener("click", undo);
  $("btn-reset").addEventListener("click", resetDraft);
  $("btn-preview").addEventListener("click", requestPreview);

  document.addEventListener("keydown", (ev) => {
    if (ev.target && /INPUT|TEXTAREA/.test(ev.target.tagName)) return;
    const m = canvasMetrics();
    const step = Math.max(1, Math.round(1 / m.pxPerUs)) * (ev.shiftKey ? 20 : 1);
    if (ev.key === "ArrowLeft") { setPlayhead(state.view.playheadUs - step); ev.preventDefault(); }
    if (ev.key === "ArrowRight") { setPlayhead(state.view.playheadUs + step); ev.preventDefault(); }
    if (ev.key === "z" && (ev.ctrlKey || ev.metaKey)) { undo(); ev.preventDefault(); }
  });
}

function setZoom(zoom, anchorUs, anchorX) {
  state.view.zoom = Math.min(80, Math.max(0.25, zoom));
  $("zoom-label").textContent = `${state.view.zoom.toFixed(1)}×`;
  if (anchorUs !== undefined && anchorX !== undefined) {
    const m = canvasMetrics();
    state.view.scrollUs = Math.round(anchorUs - anchorX / m.pxPerUs);
  }
  saveUiState({ zoom: state.view.zoom, scroll_us: state.view.scrollUs });
  draw();
}

function setPlayhead(editUs) {
  if (!Number.isFinite(editUs)) return;
  state.view.playheadUs = Math.max(
    0, Math.min(state.projection.duration_us, Math.round(editUs)));
  renderClocks();
  draw();
}

function selectAt(lane, x, m) {
  const us = usOf(x, m);
  if (lane.lane === "GAME_EVENTS") {
    const hit = hitGameEvent(x, m);
    state.selection = hit ? { lane: "GAME_EVENTS", id: hit.id, item: hit }
                          : { lane: "GAME_EVENTS" };
  } else if (lane.lane === "TIME") {
    const seg = state.projection.lanes.TIME.segments.find(
      (s) => us >= s.edit_start_us && us <= s.edit_end_us);
    state.selection = { lane: "TIME", index: seg ? seg.index : null, item: seg };
  } else if (lane.lane === "CAMERA" || lane.lane === "FX") {
    const items = lane.lane === "CAMERA"
      ? (state.projection.lanes.CAMERA.stages || [])
      : (state.projection.lanes.FX.cues || []);
    const hit = items.find((i) => i.resolved && us >= i.edit_start_us &&
                                  us <= i.edit_end_us);
    state.selection = { lane: lane.lane, index: hit ? hit.index : null, item: hit };
  } else {
    state.selection = { lane: lane.lane };
  }
  renderLaneLabels();
  renderInspector();
}

/** Shift the music lanes' edit projections client-side during a drag, so the
 *  waveform tracks the cursor at 60 Hz. The authoritative numbers come back
 *  from the server on mouseup. */
function reprojectMusicLocally(deltaUs) {
  const lanes = state.projection.lanes;
  if (lanes.MUSIC_WAVEFORM) {
    lanes.MUSIC_WAVEFORM.envelope_edit_start_us += deltaUs;
    lanes.MUSIC_WAVEFORM.envelope_edit_end_us += deltaUs;
  }
  for (const e of lanes.MUSIC_EVENTS || []) e.edit_us += deltaUs;
  for (const r of lanes.MUSIC_STRUCTURE || []) {
    r.edit_start_us += deltaUs; r.edit_end_us += deltaUs;
  }
  for (const g of state.projection.guides || []) {
    g.music_edit_us += deltaUs;
    g.delta_us = g.game_edit_us - g.music_edit_us;
  }
}

async function refreshProjection() {
  const data = await api(`/api/scene-editor/${state.fragId}`);
  state.projection = data.projection;
  state.auditions = data.auditions || [];
  state.why = data.why_this_matches || null;
  rebindSelection();
  renderAll();
}

/** Re-resolve the selected item against the NEW projection.
 *  Without this the inspector keeps showing the pre-edit numbers for the
 *  very item you just edited, which reads as "the edit did nothing". */
function rebindSelection() {
  const sel = state.selection;
  if (!sel) return;
  const lanes = state.projection.lanes;
  if (sel.lane === "GAME_EVENTS" && sel.id) {
    sel.item = (lanes.GAME_EVENTS.events || []).find((e) => e.id === sel.id);
  } else if (sel.lane === "TIME" && sel.index !== null && sel.index !== undefined) {
    sel.item = (lanes.TIME.segments || []).find((s) => s.index === sel.index);
  } else if ((sel.lane === "CAMERA" || sel.lane === "FX") &&
             sel.index !== null && sel.index !== undefined) {
    const items = sel.lane === "CAMERA" ? (lanes.CAMERA.stages || [])
                                        : (lanes.FX.cues || []);
    sel.item = items.find((i) => i.index === sel.index);
  }
}

/* --------------------------------------------------------- draft actions */

function saveUiState(patch) {
  // UI keys only — the backend keeps these out of BOTH hashes (§52), so a
  // zoom change must never flip the draft to UNSAVED.
  clearTimeout(state.uiSaveTimer);
  state.uiSaveTimer = setTimeout(async () => {
    try {
      state.draft = await api(`/api/scene-editor/${state.fragId}/draft`,
                              jsonBody(patch));
      renderStatus();
    } catch (err) { /* view furniture — never block the editor on it */ }
  }, 350);
}

async function patchRecipe(patch, label) {
  try {
    applyDraft(await api(`/api/scene-editor/${state.fragId}/draft`, jsonBody(patch)));
    await refreshProjection();
    if (label) toast(label);
  } catch (err) {
    banner(`Edit rejected: ${err.message}`);
  }
}

async function setTransition(patch) {
  // The transition lives in the draft alongside camera/fx/look, so it takes
  // the same patch path and the same undo stack. Only fields that reach
  // transition_id are sent; selection and scroll never are.
  await patchRecipe({ transition: patch },
                    `TRANSITION · ${Object.values(patch)[0]}`);
}

async function saveRecipe() {
  try {
    const draft = await api(`/api/scene-editor/${state.fragId}/draft/save`, postBody());
    applyDraft(draft);
    toast(`SAVED · recipe ${draft.recipe_id.slice(0, 12)} · scene ${draft.scene_id.slice(0, 12)}`);
  } catch (err) {
    banner(`Save failed: ${err.message}`);
  }
}

async function undo() {
  if (!state.draft || !state.draft.undo_depth) return;
  try {
    applyDraft(await api(`/api/scene-editor/${state.fragId}/draft/undo`, postBody()));
    await refreshProjection();
  } catch (err) {
    banner(`Undo failed: ${err.message}`);
  }
}

async function resetDraft() {
  try {
    applyDraft(await api(`/api/scene-editor/${state.fragId}/draft/reset`, postBody()));
    await refreshProjection();
    toast("DRAFT RESET");
  } catch (err) {
    banner(`Reset failed: ${err.message}`);
  }
}

/* ------------------------------------------------------------- preview */

async function requestPreview() {
  const btn = $("btn-preview");
  btn.disabled = true;
  btn.textContent = "PREVIEW…";
  try {
    const res = await api(`/api/frags/${state.fragId}/director/preview`, postBody());
    state.previewKey = res.preview_key;
    pollPreview();
  } catch (err) {
    // The preview service is built by another workstream and may not exist
    // yet. Degrade honestly instead of pretending a picture is coming.
    btn.textContent = "RENDER PREVIEW";
    btn.disabled = false;
    showViewerMessage("PREVIEW ENGINE UNAVAILABLE",
      `The preview service did not answer (${err.message}). The editor is ` +
      `fully usable without it — every lane below is real, mined evidence.`);
  }
}

function pollPreview() {
  clearTimeout(state.previewTimer);
  state.previewTimer = setTimeout(async () => {
    const btn = $("btn-preview");
    try {
      const res = await api(`/api/director/preview/${state.previewKey}`);
      if (res.state === "READY" && res.media_url) {
        showViewerVideo(res.media_url, res.stale);
      } else if (res.state === "FAILED") {
        showViewerMessage("PREVIEW FAILED", String(res.error || "unknown error"));
      } else {
        showViewerMessage("RENDERING PREVIEW",
                          `state ${res.state} · generation ${res.generation}`);
        pollPreview();
        return;
      }
    } catch (err) {
      showViewerMessage("PREVIEW ENGINE UNAVAILABLE", err.message);
    }
    btn.disabled = false;
    btn.textContent = "RENDER PREVIEW";
  }, 1200);
}

function showViewerMessage(title, why) {
  const viewer = $("viewer");
  clear(viewer);
  const box = el("div", "");
  box.id = "viewer-placeholder";
  box.appendChild(el("div", "big", title));
  box.appendChild(el("div", "why", why));
  viewer.appendChild(box);
}

function showViewerVideo(url, stale) {
  const viewer = $("viewer");
  clear(viewer);
  const video = document.createElement("video");
  video.src = url;
  video.controls = true;
  viewer.appendChild(video);
  video.addEventListener("timeupdate", () => {
    setPlayhead(Math.round(video.currentTime * 1000000));
  });
  if (stale) toast("PREVIEW IS STALE · recipe changed since this render");
}

/* ============================== inspector ============================== */

function section(title) {
  const box = el("div", "sect");
  if (title) box.appendChild(el("h3", "", title));
  return box;
}

function kv(pairs) {
  const grid = el("div", "kv");
  for (const [k, v, na] of pairs) {
    grid.appendChild(el("span", "k", k));
    grid.appendChild(el("span", na ? "v na" : "v",
                        v === null || v === undefined ? "–" : v));
  }
  return grid;
}

function buttonRow(options, current, onPick) {
  const row = el("div", "btn-row");
  for (const [value, label] of options) {
    const b = el("button", "", label);
    if (value === current) b.classList.add("on");
    b.addEventListener("click", () => onPick(value));
    row.appendChild(b);
  }
  return row;
}

function renderInspector() {
  const body = $("insp-body");
  clear(body);
  if (!state.projection) return;
  const sel = state.selection;
  $("insp-title").textContent = sel ? `INSPECTOR · ${sel.lane.replace(/_/g, " ")}`
                                    : "INSPECTOR";
  if (!sel) { body.appendChild(sceneSection()); body.appendChild(transitionSection()); }
  else if (sel.lane === "TIME") body.appendChild(timeSection(sel));
  else if (sel.lane === "GAME_EVENTS") body.appendChild(eventSection(sel));
  else if (sel.lane === "CAMERA") body.appendChild(cameraSection(sel));
  else if (sel.lane === "FX") body.appendChild(fxSection());
  else if (sel.lane === "LOOK") body.appendChild(lookSection());
  else if (sel.lane === "TRANSITION") body.appendChild(transitionSection());
  else body.appendChild(musicSection());

  body.appendChild(musicPlacementSection());
  body.appendChild(auditionSection());
  body.appendChild(whySection());
}

function sceneSection() {
  const p = state.projection;
  const box = section("SCENE");
  box.appendChild(kv([
    ["frag", `#${p.frag_id}`],
    ["weapon", p.weapon],
    ["demo", p.demo.name],
    ["window", `${fmtUs(p.demo.window_start_us)} → ${fmtUs(p.demo.window_end_us)}`],
    ["edit length", fmtUs(p.duration_us)],
    ["recipe_id", `${p.recipe_id.slice(0, 24)}…`],
    ["scene_id", `${p.scene_id.slice(0, 24)}…`],
  ]));
  const classes = el("div", "hint");
  classes.appendChild(el("b", "", "classes: "));
  classes.appendChild(document.createTextNode((p.classes || []).join(", ")));
  box.appendChild(classes);
  box.appendChild(el("div", "hint",
    "Click any lane or item to inspect it. Zoom, scroll and lane visibility " +
    "are workspace state — they never enter the recipe hash."));
  return box;
}

function eventSection(sel) {
  const box = section("GAME EVENT");
  if (!sel.item) {
    box.appendChild(el("div", "hint",
      "Game events originate in DEMO time and are projected onto edit time " +
      "through the TimeMap. Click one to see both clocks."));
    box.appendChild(kindToggles());
    return box;
  }
  const e = sel.item;
  box.appendChild(kv([
    ["kind", e.kind],
    ["demo_us", `${e.demo_us}`],
    ["edit_us", `${e.edit_us}`],
    ["at", fmtUs(e.edit_us)],
    ["evidence", e.evidence_source, true],
  ]));
  const detail = Object.entries(e.detail || {})
    .filter(([, v]) => v !== null && v !== undefined);
  if (detail.length) {
    box.appendChild(el("h3", "", "EVIDENCE DETAIL"));
    box.appendChild(kv(detail.map(([k, v]) => [k, String(v)])));
  }
  box.appendChild(kindToggles());
  return box;
}

function kindToggles() {
  const box = el("div", "");
  box.appendChild(el("h3", "", "VISIBILITY"));
  const hidden = new Set(state.draft ? state.draft.hidden_event_kinds || [] : []);
  const row = el("div", "btn-row");
  for (const k of state.projection.lanes.GAME_EVENTS.kinds) {
    if (!k.present) continue;
    const b = el("button", "", `${k.kind.replace(/_/g, " ")} ${k.count}`);
    if (state.showMicro || !hidden.has(k.kind)) b.classList.add("on");
    b.addEventListener("click", () => {
      const next = new Set(hidden);
      if (next.has(k.kind)) next.delete(k.kind); else next.add(k.kind);
      state.draft.hidden_event_kinds = [...next];
      state.showMicro = false;
      $("micro-toggle").classList.remove("on");
      saveUiState({ hidden_event_kinds: [...next] });
      renderInspector(); renderLaneLabels(); draw();
    });
    row.appendChild(b);
  }
  box.appendChild(row);
  const absent = state.projection.lanes.GAME_EVENTS.kinds.filter((k) => !k.present);
  if (absent.length) {
    box.appendChild(el("div", "hint",
      `no evidence in this scene: ${absent.map((k) => k.kind).join(", ")}`));
  }
  return box;
}

function timeSection(sel) {
  const box = section("TIME");
  const seg = sel.item;
  if (!seg) {
    box.appendChild(el("div", "hint",
      "The TIME lane is the actual TimeMap. Click a segment to retime it."));
    return box;
  }
  box.appendChild(kv([
    ["kind", seg.kind],
    ["rate", seg.rate_label],
    ["demo span", `${seg.demo_duration_us} µs`],
    ["edit span", `${seg.edit_duration_us} µs`],
    ["demo", `${fmtUs(seg.demo_start_us)} → ${fmtUs(seg.demo_end_us)}`],
    ["edit", `${fmtUs(seg.edit_start_us)} → ${fmtUs(seg.edit_end_us)}`],
  ]));
  if (seg.kind === "freeze") {
    box.appendChild(el("div", "hint",
      "A freeze consumes ZERO demo time and occupies POSITIVE edit time — " +
      "that positive width is exactly how long the viewer sits on the frame."));
    box.appendChild(el("h3", "", "HOLD"));
    box.appendChild(buttonRow(
      [[100000, "0.10s"], [250000, "0.25s"], [500000, "0.50s"], [1000000, "1.0s"]],
      seg.edit_duration_us,
      (us) => patchRecipe(
        { time_map: state.draft.time_map.map((s, i) =>
            (i === seg.index ? Object.assign({}, s, { freeze_us: us })
                             : Object.assign({}, s))) },
        `FREEZE HOLD · ${us / 1000}ms`)));
  } else {
    box.appendChild(el("h3", "", "RATE"));
    const rates = (state.schema && state.schema.rates) ||
                  [{ num: 1, den: 1, label: "1.0" }, { num: 3, den: 4, label: "0.75" },
                   { num: 1, den: 2, label: "0.5" }];
    const row = el("div", "btn-row");
    for (const r of rates) {
      const b = el("button", "", r.label);
      if (r.num === seg.rate_num && r.den === seg.rate_den) b.classList.add("on");
      b.addEventListener("click", () => retime(seg.index, r.num, r.den));
      row.appendChild(b);
    }
    box.appendChild(row);
    box.appendChild(el("div", "hint",
      "No reverse — the schema rejects a negative rate outright. Changing a " +
      "rate rebuilds every downstream edit clock from the demo boundaries."));
  }
  return box;
}

function retime(index, num, den) {
  const specs = state.draft.time_map.map((s) => Object.assign({}, s));
  const spec = specs[index];
  const remainder = ((spec.demo_end_us - spec.demo_start_us) * den) % num;
  if (remainder && specs[index + 1] && specs[index + 1].kind !== "freeze") {
    spec.demo_end_us -= remainder;
    specs[index + 1].demo_start_us -= remainder;
  }
  spec.rate_num = num; spec.rate_den = den;
  spec.kind = (num === 1 && den === 1) ? "normal" : "slow";
  patchRecipe({ time_map: specs }, `RATE · ${num}/${den}`);
}

function cameraSection(sel) {
  const box = section("CAMERA");
  const lane = state.projection.lanes.CAMERA;
  box.appendChild(kv([["mode", lane.mode],
                      ["subject", lane.subject_anchor],
                      ["stages", (lane.stages || []).length]]));
  box.appendChild(el("h3", "", "MODE"));
  const modes = (state.schema && state.schema.camera_modes) ||
                ["FPV", "ORBIT", "CHASE", "PROJECTILE", "FREECAM"];
  box.appendChild(buttonRow(modes.map((mode) => [mode, mode]), lane.mode,
    (mode) => patchRecipe(
      { camera_intent: Object.assign({}, state.draft.camera_intent, { mode }) },
      `CAMERA · ${mode}`)));
  if (sel.item) {
    box.appendChild(el("h3", "", "STAGE"));
    box.appendChild(kv([
      ["stage", sel.item.stage],
      ["from", `${sel.item.start_anchor} ${fmtDelta(sel.item.start_offset_us)}`],
      ["to", `${sel.item.end_anchor} ${fmtDelta(sel.item.end_offset_us)}`],
      ["edit", `${fmtUs(sel.item.edit_start_us)} → ${fmtUs(sel.item.edit_end_us)}`],
    ]));
  }
  box.appendChild(el("div", "hint",
    "Stages are anchored SEMANTICALLY (\"impact −200ms\"), never to a raw " +
    "millisecond. Re-run recognition and the camera moves with the evidence."));
  return box;
}

function fxSection() {
  const box = section("FX");
  const cues = state.projection.lanes.FX.cues || [];
  if (!cues.length) box.appendChild(el("div", "hint", "No effects on this scene yet."));
  const types = (state.schema && state.schema.fx_types) ||
                ["ROCKET_TRAIL", "IMPACT_ACCENT", "GHOST_TRAIL"];
  box.appendChild(el("h3", "", "ADD CUE"));
  box.appendChild(buttonRow(types.map((t) => [t, t.replace(/_/g, " ")]), null,
    (effectType) => {
      const anchor = (state.projection.anchors[0] || {}).anchor_id;
      if (!anchor) { banner("This scene has no resolved anchor to attach FX to."); return; }
      patchRecipe({ fx_stack: [...state.draft.fx_stack, {
        effect_type: effectType, semantic_anchor: anchor, offset_us: 0,
        duration_us: 600000, intensity_level: "SUBTLE",
        parameters: { fx_name: effectType.toLowerCase() },
      }] }, `FX ADDED · ${effectType}`);
    }));
  for (const cue of cues) {
    const card = el("div", "sect");
    card.appendChild(kv([
      ["effect", cue.effect_type],
      ["anchor", `${cue.semantic_anchor} ${fmtDelta(cue.offset_us)}`],
      ["duration", `${cue.duration_us} µs (engine time)`],
      ["edit span", `${fmtUs(cue.edit_start_us)} → ${fmtUs(cue.edit_end_us)}`],
    ]));
    card.appendChild(buttonRow(
      [["OFF", "OFF"], ["SUBTLE", "SUBTLE"], ["HERO", "HERO"]],
      cue.intensity_level,
      (level) => patchRecipe(
        { fx_stack: state.draft.fx_stack.map((c, i) =>
            (i === cue.index ? Object.assign({}, c, { intensity_level: level }) : c)) },
        `${cue.effect_type} · ${level}`)));
    const remove = el("div", "btn-row");
    const rb = el("button", "", "REMOVE");
    rb.addEventListener("click", () => patchRecipe(
      { fx_stack: state.draft.fx_stack.filter((_, i) => i !== cue.index) },
      "FX REMOVED"));
    remove.appendChild(rb);
    card.appendChild(remove);
    box.appendChild(card);
  }
  box.appendChild(el("div", "hint",
    "A cue's duration is engine time, so a cue crossing a slow segment draws " +
    "WIDER than its authored length. That is the three clocks, visible."));
  return box;
}

function lookSection() {
  const box = section("LOOK");
  const looks = (state.schema && state.schema.looks) || ["ORIGINAL", "UHD", "PANTHEON"];
  box.appendChild(buttonRow(looks.map((l) => [l, l]),
    state.projection.lanes.LOOK.visual_look,
    (visualLook) => patchRecipe({ visual_look: visualLook }, `LOOK · ${visualLook}`)));
  box.appendChild(el("div", "hint",
    "Look is recipe state: it changes the scene identity, not the timing."));
  return box;
}

function transitionSection() {
  const box = section("TRANSITION");
  const tr = state.projection.lanes.TRANSITION;
  if (!tr) {
    box.appendChild(el("div", "hint",
      "No outgoing transition. This scene ends on a straight cut."));
    return box;
  }
  box.appendChild(kv([
    ["type", tr.type],
    ["scene B", tr.scene_b_recipe_id.slice(0, 12)],
    ["A anchor", tr.scene_a_anchor.replace(/_/g, " ")],
    ["B anchor", tr.scene_b_anchor.replace(/_/g, " ")],
    ["cut", (tr.cut_edit_us / 1e6).toFixed(3) + " s"],
    ["B entry", (tr.scene_b_entry_us / 1e6).toFixed(3) + " s"],
    ["duration", tr.duration_us ? (tr.duration_us / 1e6).toFixed(3) + " s"
                                : "hard cut"],
  ]));
  box.appendChild(el("h3", "", "VISUAL VARIANT"));
  box.appendChild(buttonRow(
    [["HARD_CUT", "HARD"], ["IMPACT_FLASH", "FLASH"], ["GRADE_LERP", "GRADE"]],
    tr.visual_variant, (v) => setTransition({ visual_variant: v })));
  box.appendChild(el("h3", "", "MUSIC STRATEGY"));
  box.appendChild(buttonRow(
    [["CONTINUOUS", "CONTINUOUS"], ["STRUCTURED", "STRUCTURED"],
     ["SAME_TRACK_REGION", "SAME TRACK"]],
    tr.music_strategy, (v) => setTransition({ music_strategy: v })));
  box.appendChild(el("div", "hint",
    "Anchors are recognition evidence, not timestamps: the cut follows the " +
    "projectile impact if the evidence improves. transition_id " +
    tr.transition_id.slice(0, 12) + " covers everything above."));
  return box;
}

function musicSection() {
  const box = section("MUSIC");
  const music = state.projection.lanes.MUSIC_WAVEFORM;
  if (!music) {
    box.appendChild(el("div", "hint", "No track placed on this scene."));
    return box;
  }
  box.appendChild(kv([
    ["track", music.track_label],
    ["bpm", music.bpm === null ? "unavailable" : music.bpm.toFixed(2)],
  ]));
  // §31: these do not exist for migrated tracks and are never faked.
  const conf = el("div", "kv");
  conf.appendChild(el("span", "k", "bpm confidence"));
  conf.appendChild(el("span", music.bpm_confidence === null ? "v na" : "v",
    music.bpm_confidence === null ? "unavailable (migrated track)"
                                  : String(music.bpm_confidence)));
  conf.appendChild(el("span", "k", "beat confidence"));
  conf.appendChild(el("span", music.beat_confidence === null ? "v na" : "v",
    music.beat_confidence === null ? "unavailable (migrated track)"
                                   : String(music.beat_confidence)));
  box.appendChild(conf);
  box.appendChild(el("h3", "", "PROVENANCE"));
  box.appendChild(kv((music.analysis_provenance || []).map(([k, v]) => [k, v])));
  box.appendChild(el("div", "hint",
    "BAR_GRID_ESTIMATE is beats[::4] under a constant-tempo assumption — an " +
    "estimate, not a measured downbeat. The name keeps the suffix on purpose."));
  return box;
}

function musicPlacementSection() {
  const box = section("MUSIC PLACEMENT");
  const p = state.draft.music_placement;
  const rec = state.draft.music_placement_recommended;
  const source = state.draft.music_placement_source;
  if (!p) {
    box.appendChild(el("div", "hint", "No placement on this scene."));
    return box;
  }
  box.appendChild(kv([
    ["state", source],
    ["source_start_us", String(p.source_start_us)],
    ["recommended", rec ? String(rec.source_start_us) : "none", !rec],
  ]));
  if (source === "USER_OVERRIDDEN" && rec) {
    box.appendChild(el("div", "hint",
      `You moved the track ${fmtDelta(p.source_start_us - rec.source_start_us)} ` +
      `from the matcher's pick. Both are kept.`));
    const row = el("div", "btn-row");
    const restore = el("button", "", "RESTORE RECOMMENDED");
    restore.addEventListener("click", async () => {
      try {
        applyDraft(await api(`/api/scene-editor/${state.fragId}/music/placement`,
                             jsonBody({ placement: rec })));
        await refreshProjection();
        toast("RESTORED MATCHER PLACEMENT");
      } catch (err) {
        banner(`Restore failed: ${err.message}`);
      }
    });
    row.appendChild(restore);
    box.appendChild(row);
  }
  box.appendChild(el("div", "hint",
    "Dragging music changes MusicPlacement and nothing else. The TimeMap is " +
    "not reachable from this control — gameplay timing cannot move."));
  return box;
}

function auditionSection() {
  const box = section("A / B / C · SAME EDIT, DIFFERENT MUSIC");
  if (!state.auditions.length) {
    box.appendChild(el("div", "hint", "No ranked auditions for this scene yet."));
    return box;
  }
  const active = state.draft.music_placement
    ? state.draft.music_placement.track_id : null;
  for (const a of state.auditions) {
    const card = el("div", "aud-card");
    if (a.track_hash === active) card.classList.add("active");
    const head = el("div", "aud-head");
    head.appendChild(el("span", "aud-slot", a.display_slot));
    head.appendChild(el("span", "aud-track", a.track_label || a.track_hash.slice(0, 12)));
    head.appendChild(el("span", "aud-score",
      a.score === null || a.score === undefined ? "–" : Number(a.score).toFixed(3)));
    card.appendChild(head);
    card.appendChild(el("div", "aud-meta",
      `${a.region_kind || "?"} · region ${fmtUs(a.region_start_us)} · ${a.matcher_version}`));
    const row = el("div", "btn-row");
    const use = el("button", "", "USE THIS");
    use.addEventListener("click", async () => {
      try {
        applyDraft(await api(`/api/scene-editor/${state.fragId}/music/select`,
                             postBody({ display_slot: a.display_slot })));
        await refreshProjection();
        toast(`${a.display_slot} · only MusicPlacement changed`);
      } catch (err) {
        banner(`Could not switch: ${err.message}`);
      }
    });
    row.appendChild(use);
    card.appendChild(row);
    card.appendChild(el("div", "hint",
      "Display order only. The review is filed against the identity below."));
    card.appendChild(reasonTags(a));
    card.appendChild(el("div", "identity", a.review_identity));
    box.appendChild(card);
  }
  return box;
}

function reasonTags(audition) {
  const box = el("div", "tagbox");
  const vocabulary = (state.schema && state.schema.reason_tags) || [];
  const current = new Set(audition.reason_tags || []);
  for (const tag of vocabulary) {
    const b = el("button", "", tag.replace(/_/g, " "));
    if (current.has(tag)) b.classList.add("on");
    b.addEventListener("click", async () => {
      if (current.has(tag)) current.delete(tag); else current.add(tag);
      try {
        await api(`/api/scene-editor/${state.fragId}/reason-tags`,
                  jsonBody({ review_identity: audition.review_identity,
                             tags: [...current] }));
        audition.reason_tags = [...current];
        b.classList.toggle("on", current.has(tag));
      } catch (err) {
        banner(`Could not save reason tag: ${err.message}`);
      }
    });
    box.appendChild(b);
  }
  return box;
}

function whySection() {
  const box = section("WHY THIS MATCHES");
  const why = state.why;
  if (!why || !why.available) {
    box.appendChild(el("div", "hint",
      why ? why.reason : "No ranking available for this scene."));
    return box;
  }
  box.appendChild(kv([
    ["profile", why.profile_type],
    ["matcher", why.matcher_version],
    ["derivation", why.profile_derivation_version],
  ]));
  const ev = why.scene_evidence || {};
  box.appendChild(el("h3", "", "SCENE EVIDENCE"));
  box.appendChild(kv([
    ["hero anchor", fmtUs(ev.hero_anchor_us)],
    ["length", fmtUs(ev.duration_us)],
    ["frags", ev.frag_count],
    ["hit bursts", ev.hit_burst_count],
    ["contact gaps", ev.contact_gap_count],
    ["projectile flights",
     (ev.projectile_flights_us || []).map(fmtUs).join(", ") || "none"],
  ]));
  const headline = new Set(why.headline_components || []);
  for (const cand of why.candidates) {
    box.appendChild(el("h3", "", `${cand.display_slot} · ${cand.track_label}`));
    for (const [name, value] of Object.entries(cand.components || {})) {
      if (!headline.has(name) && name !== "alignment_cost") continue;
      const comp = el("div", `comp${headline.has(name) ? " headline" : ""}`);
      const line = el("div", "cl");
      line.appendChild(el("span", "cn", name.replace(/_/g, " ")));
      line.appendChild(el("span", "cv", Number(value).toFixed(3)));
      comp.appendChild(line);
      const bar = el("div", "bar");
      const fill = el("i", "");
      fill.style.width = `${Math.max(0, Math.min(1, Number(value))) * 100}%`;
      bar.appendChild(fill);
      comp.appendChild(bar);
      box.appendChild(comp);
    }
  }
  box.appendChild(el("div", "hint", why.authority));
  return box;
}

/* ================================ go =================================== */

boot();
