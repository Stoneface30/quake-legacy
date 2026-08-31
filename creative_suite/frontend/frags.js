/* PANTHEON Frag Control Room — vanilla JS, UI-1 compliant (no innerHTML with data). */
"use strict";

const state = {
  limit: 100, offset: 0, total: 0,
  selectedId: null, detail: null,
  loopIn: null, loopOut: null,
  pollTimer: null, notesTimer: null,
};

const $ = (id) => document.getElementById(id);
const player = $("player");

function el(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text !== undefined && text !== null) n.textContent = String(text);
  return n;
}

function fmtClock(ms) {
  if (ms == null) return "–";
  const s = Math.floor(ms / 1000);
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

function demoShort(name) {
  return (name || "").replace(/\.dm_73$/, "").slice(0, 46);
}

/* ============================= list ============================= */

function currentFilters() {
  const p = new URLSearchParams();
  p.set("limit", state.limit);
  p.set("offset", state.offset);
  const minScore = $("f-min-score").value.trim();
  if (minScore !== "") p.set("min_score", minScore);
  if ($("f-weapon").value) p.set("weapon", $("f-weapon").value);
  if ($("f-class").value) p.set("class", $("f-class").value);
  const demo = $("f-demo").value.trim();
  if (demo) p.set("demo", demo);
  p.set("mode_pool", $("f-pool").value);
  if ($("f-master").checked) p.set("has_master", "true");
  p.set("sort", $("f-sort").value);
  return p;
}

function masterBadge(master) {
  const qa = master.qa_status || "?";
  const known = ["PASS", "PASSED", "APPROVED", "PENDING", "FAIL", "FAILED", "REJECTED"];
  const cls = known.includes(qa) ? `qa-${qa}` : "qa-other";
  const b = el("span", `badge ${cls}`, `${master.tier || "?"}`);
  b.title = `clip #${master.generated_clip_id} · ${master.class || ""} · QA ${qa}` +
    (master.avi_on_disk ? " · AVI on disk" : " · AVI missing");
  return b;
}

async function loadList() {
  const res = await fetch(`/api/frags?${currentFilters()}`);
  const data = await res.json();
  state.total = data.total;
  $("total-count").textContent = `${data.total.toLocaleString()} frags`;
  $("pg-label").textContent =
    `${data.total ? data.offset + 1 : 0}–${Math.min(data.offset + data.items.length, data.total)} / ${data.total.toLocaleString()}`;
  $("pg-prev").disabled = data.offset === 0;
  $("pg-next").disabled = data.offset + data.items.length >= data.total;

  const rows = data.items.map((it) => {
    const row = el("div", "frag-row");
    row.dataset.id = it.id;
    if (it.id === state.selectedId) row.classList.add("selected");
    const l1 = el("div", "line1");
    l1.appendChild(el("span", "score", (it.highlight_score ?? 0).toFixed(1)));
    l1.appendChild(el("span", "weapon", it.weapon_name || "–"));
    l1.appendChild(el("span", "demo-short",
      `${demoShort(it.demo_name)} · r${it.round ?? "?"} · ${fmtClock(it.server_time_ms)}`));
    row.appendChild(l1);
    const l2 = el("div", "line2");
    (it.classes || []).slice(0, 3).forEach((c) => l2.appendChild(el("span", "chip", c)));
    if (it.master) l2.appendChild(masterBadge(it.master));
    if (it.review && it.review.verdict) {
      l2.appendChild(el("span", `badge verdict-${it.review.verdict}`, it.review.verdict));
    }
    if (it.review && it.review.user_tier) {
      l2.appendChild(el("span", "badge qa-other",
        it.review.user_tier === "S_PLUS" ? "S+" : it.review.user_tier));
    }
    row.appendChild(l2);
    row.addEventListener("click", () => selectFrag(it.id));
    return row;
  });
  $("list-scroll").replaceChildren(...rows);
}

/* ========================= evidence formatting ========================= */

function fmtNum(v, digits = 1) {
  return Number(v).toFixed(digits).replace(/\.0$/, digits === 1 ? "" : ".0");
}

function metricsForClass(name, attrs) {
  const a = attrs || {};
  const out = [];
  const upper = (name || "").toUpperCase();
  if (upper.includes("FLICK")) {
    const deg = a.flick_true_deg ?? a.flick_deg_v2 ?? a.flick_degrees;
    const ms = a.flick_true_ms ?? a.flick_ms_v2 ?? a.flick_duration_ms;
    const dps = a.flick_peak_dps ?? a.flick_dps_v2 ?? a.deg_per_sec;
    if (deg != null) out.push(`${fmtNum(deg, 0)}° / ${fmtNum(ms, 0)}ms / ${fmtNum(dps, 0)}°/s`);
  }
  if (upper.includes("DIRECT")) {
    if (a.projectile_direct_expansion_u != null) {
      out.push(`${fmtNum(a.projectile_direct_expansion_u)}u expansion`);
    }
    if (a.projectile_flight_ms != null) out.push(`flight ${fmtNum(a.projectile_flight_ms, 0)}ms`);
  }
  if (upper.startsWith("LG")) {
    if (a.lg_contact_rate != null) out.push(`contact rate ${fmtNum(a.lg_contact_rate, 2)}`);
    if (a.lg_dodge_rating != null) out.push(`dodge ${fmtNum(a.lg_dodge_rating, 2)}`);
  }
  if (upper.includes("AIR")) {
    if (a.victim_air_height != null) out.push(`air ${fmtNum(a.victim_air_height, 0)}u`);
    if (a.victim_vertical_speed != null) out.push(`vspeed ${fmtNum(a.victim_vertical_speed, 0)}u/s`);
  }
  if (upper.includes("SPEED")) {
    if (a.killer_speed != null) out.push(`attacker ${fmtNum(a.killer_speed, 0)}u/s`);
    if (a.victim_speed != null) out.push(`victim ${fmtNum(a.victim_speed, 0)}u/s`);
  }
  if (upper.includes("MULTIKILL") && a.multikill && a.multikill.count != null) {
    out.push(`${a.multikill.count} kills / ${fmtNum(a.multikill.duration_ms, 0)}ms`);
  }
  if (upper.includes("CLUTCH") && a.health_at_frag != null) {
    out.push(`${a.health_at_frag}hp at frag`);
  }
  if (!out.length && a.distance != null) out.push(`${fmtNum(a.distance, 0)}u range`);
  return out.join(" · ");
}

/* ============================= inspector ============================= */

function kvGrid(obj) {
  const grid = el("div", "kv");
  Object.keys(obj).forEach((k) => {
    const v = obj[k];
    if (v === undefined || v === null) return;
    grid.appendChild(el("span", "k", k));
    grid.appendChild(el("span", "v",
      typeof v === "object" ? JSON.stringify(v) : String(v)));
  });
  return grid;
}

async function selectFrag(id) {
  state.selectedId = id;
  state.loopIn = state.loopOut = null;
  document.querySelectorAll(".frag-row.selected").forEach((r) => r.classList.remove("selected"));
  const row = document.querySelector(`.frag-row[data-id="${CSS.escape(String(id))}"]`);
  if (row) row.classList.add("selected");
  const res = await fetch(`/api/frags/${id}`);
  if (!res.ok) return;
  state.detail = await res.json();
  renderInspector();
  setupVideo();
  renderEventStrip();
  schedulePoll();
}

function renderInspector() {
  const d = state.detail;
  const pane = $("inspector");
  const frag = document.createDocumentFragment();

  frag.appendChild(el("h2", "",
    `#${d.id} · ${d.weapon_name || "?"} · ${(d.highlight_score ?? 0).toFixed(1)}`));
  frag.appendChild(kvGrid({
    demo: d.demo_name,
    round: d.round,
    time: `${fmtClock(d.server_time_ms)} (${d.server_time_ms} ms)`,
    pool: (d.attributes || {}).mode_pool,
    scene: (d.attributes || {}).scene_score,
  }));

  /* --- evidence --- */
  frag.appendChild(el("h3", "", "Evidence"));
  const classes = Array.isArray(d.classes) ? d.classes : [];
  if (!classes.length) frag.appendChild(el("div", "evidence", "no classes"));
  classes.forEach((c) => {
    const name = typeof c === "string" ? c : (c.name || "?");
    const box = el("div", "evidence");
    const head = el("div", "ev-head");
    head.appendChild(el("span", "ev-name", name));
    if (typeof c === "object" && c && c.confidence) {
      head.appendChild(el("span", "ev-conf", c.confidence));
    }
    box.appendChild(head);
    if (typeof c === "object" && c && c.detail) {
      box.appendChild(el("div", "ev-detail", c.detail));
    }
    const metrics = metricsForClass(name, d.attributes);
    if (metrics) box.appendChild(el("div", "ev-metrics", metrics));
    frag.appendChild(box);
  });

  frag.appendChild(el("h3", "", "Reasons"));
  const reasons = Array.isArray(d.reasons) ? d.reasons.join("\n") : String(d.reasons ?? "–");
  frag.appendChild(el("pre", "", reasons || "–"));

  /* --- editorial --- */
  frag.appendChild(el("h3", "", "Editorial"));
  const review = d.review || {};
  const vRow = el("div", "verdict-btns");
  ["LOVE", "KEEP", "MAYBE", "DROP"].forEach((v) => {
    const b = el("button", "", v);
    if (review.verdict === v) b.classList.add(`on-${v}`);
    b.addEventListener("click", () => saveReview({ verdict: v }));
    vRow.appendChild(b);
  });
  frag.appendChild(vRow);
  const tRow = el("div", "tier-btns");
  [["S_PLUS", "S+"], ["S", "S"], ["A", "A"], ["", "none"]].forEach(([val, label]) => {
    const b = el("button", "", label);
    if ((review.user_tier || "") === val && review.user_tier != null) b.classList.add("on");
    b.addEventListener("click", () => saveReview({ user_tier: val }));
    tRow.appendChild(b);
  });
  frag.appendChild(tRow);
  const notes = document.createElement("textarea");
  notes.id = "notes";
  notes.placeholder = "notes… (autosaves)";
  notes.value = review.notes || "";
  notes.addEventListener("input", () => {
    clearTimeout(state.notesTimer);
    $("save-state").textContent = "typing…";
    state.notesTimer = setTimeout(() => saveReview({ notes: notes.value }), 800);
  });
  frag.appendChild(el("h3", "", "Notes"));
  frag.appendChild(notes);
  const saveState = el("div", "save-state", "");
  saveState.id = "save-state";
  frag.appendChild(saveState);

  /* --- proxy --- */
  frag.appendChild(el("h3", "", "Review capture"));
  const proxyBox = el("div", "");
  proxyBox.id = "proxy-box";
  frag.appendChild(proxyBox);

  /* --- master --- */
  frag.appendChild(el("h3", "", "Master clip"));
  if (d.master) {
    const m = d.master;
    frag.appendChild(kvGrid({
      clip: `#${m.generated_clip_id} · ${m.tier || "?"} · ${m.class || ""}`,
      qa: m.qa_status,
      map: m.map,
      window: `${m.capture_start_ms}–${m.capture_end_ms} ms`,
      avi_on_disk: m.avi_on_disk,
    }));
    if (m.avi_path) {
      const rowP = el("div", "path-row");
      const code = el("code", "", m.avi_path);
      code.title = m.avi_path;
      const btn = el("button", "", "copy path");
      btn.addEventListener("click", () => {
        navigator.clipboard.writeText(m.avi_path).then(() => {
          btn.textContent = "copied!";
          setTimeout(() => { btn.textContent = "copy path"; }, 1200);
        });
      });
      rowP.appendChild(code);
      rowP.appendChild(btn);
      frag.appendChild(rowP);
      frag.appendChild(el("div", "hint",
        "Master is MJPEG AVI — plays in MPC/VLC. Use the review capture for in-browser playback."));
    }
  } else {
    frag.appendChild(el("div", "hint", "No master clip captured for this frag."));
  }

  frag.appendChild(el("h3", "", "Attributes"));
  frag.appendChild(el("pre", "", JSON.stringify(d.attributes || {}, null, 1)));

  pane.replaceChildren(frag);
  renderProxyBox(d.proxy || { state: "MISSING" });
}

async function saveReview(patch) {
  const id = state.selectedId;
  if (id == null) return;
  const ss = $("save-state");
  if (ss) ss.textContent = "saving…";
  const res = await fetch(`/api/frags/${id}/review`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patch),
  });
  if (res.ok && state.detail && state.detail.id === id) {
    state.detail.review = await res.json();
    // Re-render buttons without nuking the notes focus for note saves.
    if (!("notes" in patch)) renderInspector();
    else {
      const ss2 = $("save-state");
      if (ss2) ss2.textContent = "saved";
    }
    loadList();
  } else if (ss) {
    ss.textContent = "save failed";
  }
}

/* ============================= proxy ============================= */

function renderProxyBox(proxy) {
  const box = $("proxy-box");
  if (!box) return;
  const frag = document.createDocumentFragment();
  const line = el("div", "");
  line.id = "proxy-state";
  line.appendChild(el("span", "", "state: "));
  line.appendChild(el("span", `st-${proxy.state}`, proxy.state));
  frag.appendChild(line);
  if (proxy.error) frag.appendChild(el("div", "hint", proxy.error));
  const btn = el("button", "");
  btn.id = "btn-proxy";
  if (proxy.state === "QUEUED" || proxy.state === "GENERATING") {
    btn.textContent = proxy.state === "QUEUED" ? "Queued…" : "Generating…";
    btn.disabled = true;
  } else if (proxy.state === "READY") {
    btn.textContent = "Review capture ready";
    btn.disabled = true;
  } else {
    btn.textContent = proxy.state === "FAILED"
      ? "Retry review capture" : "Generate review capture";
    btn.addEventListener("click", requestProxy);
  }
  frag.appendChild(btn);
  box.replaceChildren(frag);
}

async function requestProxy() {
  const id = state.selectedId;
  if (id == null) return;
  const res = await fetch(`/api/frags/${id}/proxy`, { method: "POST" });
  if (!res.ok) return;
  const proxy = await res.json();
  if (state.selectedId !== id) return;
  state.detail.proxy = proxy;
  renderProxyBox(proxy);
  schedulePoll();
}

function schedulePoll() {
  clearTimeout(state.pollTimer);
  const proxy = state.detail && state.detail.proxy;
  if (!proxy || (proxy.state !== "QUEUED" && proxy.state !== "GENERATING")) return;
  state.pollTimer = setTimeout(pollProxy, 3000);
}

async function pollProxy() {
  const id = state.selectedId;
  if (id == null) return;
  const res = await fetch(`/api/frags/${id}/proxy`);
  if (!res.ok) return;
  const proxy = await res.json();
  if (state.selectedId !== id) return;
  const prev = state.detail.proxy && state.detail.proxy.state;
  state.detail.proxy = proxy;
  renderProxyBox(proxy);
  if (proxy.state === "READY" && prev !== "READY") {
    setupVideo();
    renderEventStrip();
  }
  schedulePoll();
}

/* ============================= player ============================= */

function setupVideo() {
  const d = state.detail;
  const placeholder = $("video-placeholder");
  player.pause();
  player.removeAttribute("src");
  player.load();
  let src = null;
  if (d.proxy && d.proxy.state === "READY") {
    src = `/api/frags/${d.id}/proxy/video`;
  } else if (d.master && d.master.avi_on_disk) {
    src = `/api/frags/${d.id}/video`; // MJPEG AVI — will likely error; hint shown
  }
  if (src) {
    player.hidden = false;
    placeholder.hidden = true;
    player.src = src;
    player.playbackRate = Number($("rate-sel").value);
  } else {
    player.hidden = true;
    placeholder.hidden = false;
  }
  updateTransport();
}

player.addEventListener("error", () => {
  const d = state.detail;
  if (d && (!d.proxy || d.proxy.state !== "READY")) {
    player.hidden = true;
    const ph = $("video-placeholder");
    ph.hidden = false;
    ph.replaceChildren(
      el("div", "big", "Master is MJPEG AVI — browsers can't decode it"),
      el("div", "", "Plays in MPC/VLC. Generate a review capture for in-browser playback."),
    );
  }
});

function updateTransport() {
  $("btn-play").textContent = player.paused ? "Play" : "Pause";
  $("timecode").textContent =
    `${(player.currentTime || 0).toFixed(3)} / ${(player.duration || 0).toFixed(3)}`;
  $("btn-loop-in").classList.toggle("active", state.loopIn != null);
  $("btn-loop-out").classList.toggle("active", state.loopOut != null);
}

function togglePlay() {
  if (player.hidden) return;
  if (player.paused) player.play(); else player.pause();
}

function frameStep(dir) {
  if (player.hidden) return;
  player.pause();
  player.currentTime = Math.max(0, (player.currentTime || 0) + dir / 60);
}

function setLoop(which) {
  if (player.hidden) return;
  if (which === "in") state.loopIn = player.currentTime;
  else state.loopOut = player.currentTime;
  if (state.loopIn != null && state.loopOut != null && state.loopOut <= state.loopIn) {
    const t = state.loopIn; state.loopIn = state.loopOut; state.loopOut = t;
  }
  updateTransport();
  renderEventStrip();
}

function clearLoop() {
  state.loopIn = state.loopOut = null;
  updateTransport();
  renderEventStrip();
}

player.addEventListener("timeupdate", () => {
  if (state.loopIn != null && state.loopOut != null &&
      player.currentTime >= state.loopOut) {
    player.currentTime = state.loopIn;
  }
  updateTransport();
  positionPlayhead();
});
player.addEventListener("play", updateTransport);
player.addEventListener("pause", updateTransport);
player.addEventListener("loadedmetadata", () => { updateTransport(); renderEventStrip(); });

$("btn-play").addEventListener("click", togglePlay);
$("btn-step-back").addEventListener("click", () => frameStep(-1));
$("btn-step-fwd").addEventListener("click", () => frameStep(1));
$("btn-loop-in").addEventListener("click", () => setLoop("in"));
$("btn-loop-out").addEventListener("click", () => setLoop("out"));
$("btn-loop-clear").addEventListener("click", clearLoop);
$("rate-sel").addEventListener("change", () => {
  player.playbackRate = Number($("rate-sel").value);
});

document.addEventListener("keydown", (e) => {
  const tag = (e.target && e.target.tagName) || "";
  if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
  if (e.code === "Space") { e.preventDefault(); togglePlay(); }
  else if (e.key === ",") frameStep(-1);
  else if (e.key === ".") frameStep(1);
  else if (e.key === "[") setLoop("in");
  else if (e.key === "]") setLoop("out");
  else if (e.key === "l" || e.key === "L") clearLoop();
});

/* ============================= event strip ============================= */

function stripWindow() {
  const d = state.detail;
  if (!d) return null;
  const w = d.window || null;
  if (w) return { start: w.start_ms, end: w.end_ms };
  return null;
}

function renderEventStrip() {
  const strip = $("event-strip");
  const d = state.detail;
  const w = stripWindow();
  const frag = document.createDocumentFragment();
  if (d && w && w.end > w.start) {
    const span = w.end - w.start;
    const pct = (ms) => `${(((ms - w.start) / span) * 100).toFixed(2)}%`;
    // loop zone
    if (state.loopIn != null && state.loopOut != null && player.duration) {
      const zone = el("div", "loop-zone");
      zone.style.left = `${(state.loopIn / player.duration) * 100}%`;
      zone.style.width = `${((state.loopOut - state.loopIn) / player.duration) * 100}%`;
      frag.appendChild(zone);
    }
    // frag moment marker
    const m = el("div", "marker");
    m.style.left = pct(d.server_time_ms);
    m.title = `frag @ ${fmtClock(d.server_time_ms)}`;
    frag.appendChild(m);
    // master frag offsets
    if (d.master && Array.isArray(d.master.frag_offsets_ms)) {
      d.master.frag_offsets_ms.forEach((off) => {
        const t = Number(d.master.capture_start_ms) + Number(off);
        if (t === d.server_time_ms) return;
        const mk = el("div", "marker offset");
        mk.style.left = pct(t);
        mk.title = `frag offset +${off}ms`;
        frag.appendChild(mk);
      });
    }
    const ph = el("div", "playhead");
    ph.id = "playhead";
    frag.appendChild(ph);
  }
  strip.replaceChildren(frag);
  positionPlayhead();
  strip.onclick = (e) => {
    if (player.hidden || !player.duration) return;
    const rect = strip.getBoundingClientRect();
    player.currentTime = ((e.clientX - rect.left) / rect.width) * player.duration;
  };
}

function positionPlayhead() {
  const ph = document.getElementById("playhead");
  if (!ph || !player.duration) return;
  ph.style.left = `${(player.currentTime / player.duration) * 100}%`;
}

/* ============================= filters/init ============================= */

async function loadFilters() {
  try {
    const classes = await (await fetch("/api/frags/classes")).json();
    const clsSel = $("f-class");
    classes.forEach((c) => {
      const opt = el("option", "", `${c.name} (${c.count})`);
      opt.value = c.name;
      clsSel.appendChild(opt);
    });
  } catch (e) { /* dropdown stays "all" */ }
  const weapons = [
    "LIGHTNING", "RAILGUN", "ROCKET", "ROCKET_SPLASH", "SHOTGUN",
    "PLASMA", "PLASMA_SPLASH", "GAUNTLET", "GRENADE", "GRENADE_SPLASH",
    "MACHINEGUN", "TELEFRAG",
  ];
  const wSel = $("f-weapon");
  weapons.forEach((w) => {
    const opt = el("option", "", w);
    opt.value = w;
    wSel.appendChild(opt);
  });
}

$("btn-apply").addEventListener("click", () => { state.offset = 0; loadList(); });
$("f-demo").addEventListener("keydown", (e) => {
  if (e.key === "Enter") { state.offset = 0; loadList(); }
});
$("pg-prev").addEventListener("click", () => {
  state.offset = Math.max(0, state.offset - state.limit);
  loadList();
});
$("pg-next").addEventListener("click", () => {
  state.offset += state.limit;
  loadList();
});

loadFilters();
loadList();
