/* PANTHEON Frag Control Room — vanilla JS, UI-1 compliant (no innerHTML with data). */
"use strict";

const state = {
  limit: 100, offset: 0, total: 0,
  selectedId: null, detail: null,
  category: null,
  loopIn: null, loopOut: null,
  pollTimer: null, notesTimer: null,
  director: null,   // {sessionId, since, count, keybind, recipeId, pollTimer}
  groupSelections: { skill: new Set(), context: new Set(), movement: new Set(), craft: new Set() },
  customWeights: {},       // {CLASS_NAME: nonzero weight}
  customSortActive: false, // true only right after "Apply weights" was clicked
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
  const minSpeed = $("f-min-speed").value.trim();
  if (minSpeed !== "") p.set("min_speed", minSpeed);
  if ($("f-weapon").value) p.set("weapon", $("f-weapon").value);
  if ($("f-class").value) p.set("class", $("f-class").value);
  if (state.category) p.set("category", state.category);
  const demo = $("f-demo").value.trim();
  if (demo) p.set("demo", demo);
  p.set("mode_pool", $("f-pool").value);
  if ($("f-master").checked) p.set("has_master", "true");
  Object.entries(state.groupSelections).forEach(([groupId, set]) => {
    if (set.size) p.set(`${groupId}_group`, [...set].join(","));
  });
  const nonzeroWeights = Object.fromEntries(
    Object.entries(state.customWeights).filter(([, w]) => w !== 0)
  );
  const hasWeights = Object.keys(nonzeroWeights).length > 0;
  if (hasWeights) p.set("custom_weights", JSON.stringify(nonzeroWeights));
  p.set("sort", state.customSortActive && hasWeights ? "custom" : $("f-sort").value);
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

function mapFromDemo(name) {
  const clean = (name || "").replace(/\.dm_73$/, "");
  const parts = clean.split("-");
  if (parts.length < 3) return "UNKNOWN MAP";
  return parts.slice(2, -2).join("-").replace(/^pTnTr4sH-?/i, "") || "UNKNOWN MAP";
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
    if (it.custom_score != null) {
      l1.appendChild(el("span", "custom-score", `→ ${it.custom_score.toFixed(1)}`));
    }
    l1.appendChild(el("span", "weapon", it.weapon_name || "–"));
    if (it.review && it.review.user_tier) {
      l1.appendChild(el("span", "badge qa-other",
        it.review.user_tier === "S_PLUS" ? "S+" : it.review.user_tier));
    }
    row.appendChild(l1);
    row.appendChild(el("div", "map-line",
      (it.map_name || mapFromDemo(it.demo_name)) + " · round " +
      (it.round ?? "?") + " · " + fmtClock(it.server_time_ms)));
    const l2 = el("div", "line2");
    (it.classes || []).slice(0, 4).forEach((c) => l2.appendChild(el("span", "chip", c)));
    row.appendChild(l2);
    const l3 = el("div", "line3");
    const proxyState = (it.proxy && it.proxy.state) || "MISSING";
    l3.appendChild(el("span", "media-state " + proxyState,
      proxyState === "READY" ? "▶ READY" : "● " + proxyState));
    if (it.master) l3.appendChild(masterBadge(it.master));
    if (it.review && it.review.verdict) {
      l3.appendChild(el("span", "badge verdict-" + it.review.verdict, it.review.verdict));
    }
    l3.appendChild(el("span", "demo-short", demoShort(it.demo_name)));
    row.appendChild(l3);
    row.addEventListener("click", () => selectFrag(it.id));
    return row;
  });
  $("list-scroll").replaceChildren(...rows);
}

async function loadTaxonomy() {
  const res = await fetch("/api/frags/taxonomy");
  if (!res.ok) return;
  const data = await res.json();
  const groups = data.families.map((family) => {
    const group = el("section", "tax-family");
    group.appendChild(el("h2", "", family.label));
    family.categories.forEach((category) => {
      const button = el("button", "tax-item");
      button.dataset.category = category.id;
      button.appendChild(el("span", "", category.label));
      button.appendChild(el("span", "tax-count", category.count.toLocaleString()));
      button.addEventListener("click", () => {
        const same = state.category === category.id;
        state.category = same ? null : category.id;
        state.offset = 0;
        document.querySelectorAll(".tax-item.active").forEach(
          (node) => node.classList.remove("active")
        );
        if (!same) button.classList.add("active");
        loadList();
      });
      group.appendChild(button);
    });
    return group;
  });
  $("taxonomy").replaceChildren(...groups);
}

/* ===================== combinable multi-select groups ===================== */
/* Each group ("skill"/"context"/"movement"/"craft" — see the grouping
 * rationale comment on _FILTER_GROUPS in creative_suite/api/frags.py) is
 * multi-select OR-within; picking from two+ groups ANDs across them.
 * "All" for a group just means "clear this group's selections" — omitting
 * the query param entirely is how the backend reads "no constraint". */

async function loadGroupFilters() {
  let data;
  try {
    data = await (await fetch("/api/frags/filter-groups")).json();
  } catch (e) {
    return;
  }
  const panels = data.groups.map((group) => buildGroupPanel(group));
  $("group-panels").replaceChildren(...panels);
  buildWeightsPanel(data.groups);
}

function buildGroupPanel(group) {
  const panel = el("div", "group-panel");
  const head = el("div", "group-head");
  head.appendChild(el("h3", "", group.label));
  const allBtn = el("button", "group-all-btn", "All");
  allBtn.type = "button";
  const selection = state.groupSelections[group.id];
  const refreshAllBtn = () => allBtn.classList.toggle("active", selection.size === 0);
  allBtn.addEventListener("click", () => {
    if (selection.size === 0) return;
    selection.clear();
    checks.forEach((cb) => { cb.checked = false; });
    refreshAllBtn();
    state.offset = 0;
    loadList();
  });
  head.appendChild(allBtn);
  panel.appendChild(head);

  const checksBox = el("div", "group-checks");
  const checks = group.classes.map((cls) => {
    const row = el("label", "group-check");
    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.checked = selection.has(cls.name);
    cb.addEventListener("change", () => {
      if (cb.checked) selection.add(cls.name); else selection.delete(cls.name);
      refreshAllBtn();
      state.offset = 0;
      loadList();
    });
    row.appendChild(cb);
    row.appendChild(el("span", "", cls.name));
    row.appendChild(el("span", "gc-count", cls.count.toLocaleString()));
    checksBox.appendChild(row);
    return cb;
  });
  refreshAllBtn();
  panel.appendChild(checksBox);
  return panel;
}

/* ================================ weights ================================ */
/* Lightweight custom-scoring panel: custom_score = highlight_score + sum of
 * weights for classes present on the frag, computed per-request on the
 * server (never persisted — the machine highlight_score is immutable). */

function buildWeightsPanel(groups) {
  const allClasses = [];
  const seen = new Set();
  groups.forEach((g) => g.classes.forEach((c) => {
    if (!seen.has(c.name)) { seen.add(c.name); allClasses.push(c.name); }
  }));
  const body = $("weights-body");
  const rows = allClasses.map((name) => {
    const row = el("div", "weight-row");
    row.appendChild(el("label", "", name));
    const input = document.createElement("input");
    input.type = "number";
    input.step = "0.5";
    input.value = state.customWeights[name] || 0;
    input.dataset.className = name;
    input.addEventListener("input", () => {
      row.classList.toggle("nonzero", Number(input.value) !== 0);
    });
    row.classList.toggle("nonzero", Number(input.value) !== 0);
    row.appendChild(input);
    return row;
  });
  body.replaceChildren(...rows);
  updateWeightsActiveHint();
}

function updateWeightsActiveHint() {
  const n = Object.values(state.customWeights).filter((w) => w !== 0).length;
  $("weights-active-hint").textContent = n
    ? `${n} weight${n === 1 ? "" : "s"} active${state.customSortActive ? " · sort=custom" : ""}`
    : "";
}

function applyWeights() {
  const weights = {};
  $("weights-body").querySelectorAll("input[data-class-name]").forEach((input) => {
    const w = Number(input.value);
    if (w) weights[input.dataset.className] = w;
  });
  state.customWeights = weights;
  state.customSortActive = Object.keys(weights).length > 0;
  updateWeightsActiveHint();
  state.offset = 0;
  loadList();
}

function clearWeights() {
  state.customWeights = {};
  state.customSortActive = false;
  $("weights-body").querySelectorAll("input[data-class-name]").forEach((input) => {
    input.value = 0;
    input.closest(".weight-row").classList.remove("nonzero");
  });
  updateWeightsActiveHint();
  state.offset = 0;
  loadList();
}

$("btn-apply-weights").addEventListener("click", applyWeights);
$("btn-clear-weights").addEventListener("click", clearWeights);
$("f-sort").addEventListener("change", () => { state.customSortActive = false; updateWeightsActiveHint(); });

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
  clearTimeout(state.director && state.director.pollTimer);
  state.director = null;   // UI-side only; a live backend session (if any)
                            // keeps running until explicitly stopped
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
  [["S_PLUS", "S+"], ["S", "S"], ["A", "A"], ["B", "B"], ["", "none"]].forEach(([val, label]) => {
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

  frag.appendChild(el("h3", "", "Music auditions · edit-time sync"));
  const musicBox = el("div", "music-auditions");
  musicBox.id = "music-auditions";
  frag.appendChild(musicBox);

  /* --- live director --- */
  frag.appendChild(el("h3", "", "Live director"));
  const directorBox = el("div", "");
  directorBox.id = "director-box";
  frag.appendChild(directorBox);

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
  loadMusicAuditions(d.id);
  renderDirectorBox();
}

async function loadMusicAuditions(id) {
  const box = $("music-auditions");
  if (!box) return;
  box.replaceChildren(el("div", "hint", "loading A/B/C…"));
  const res = await fetch(`/api/frags/${id}/music-auditions`);
  if (!res.ok || state.selectedId !== id) return;
  const data = await res.json();
  box.replaceChildren();
  data.items.forEach((item) => {
    const saved = data.reviews.find((r) => r.track_hash === item.track_hash &&
      r.region_start_us === item.region_start_us &&
      (!item.matcher_version || r.matcher_version === item.matcher_version) &&
      (!item.scene_recipe_id || r.scene_recipe_id === item.scene_recipe_id)) || {};
    const card = el("div", "music-card");
    const play = el("button", "music-play", `${item.audition_id} · ${item.track_label}`);
    play.addEventListener("click", () => {
      const video = $("player");
      video.src = item.video_url;
      video.load(); video.play();
    });
    card.appendChild(play);
    card.appendChild(el("div", "music-meta",
      `${item.region_kind} ${(item.region_start_us / 1e6).toFixed(2)}s · edit anchor ${(item.anchor_edit_us / 1e6).toFixed(3)}s`));
    if (item.components && typeof item.components === "object") {
      const why = el("div", "music-why");
      why.appendChild(el("div", "music-why-title", `WHY THIS MATCHES · ${item.profile_type || "SCENE"}`));
      Object.entries(item.components).sort((a, b) => b[1] - a[1]).forEach(([name, value]) => {
        const row = el("div", "music-why-row");
        row.appendChild(el("span", "", name.replaceAll("_", " ").toUpperCase()));
        row.appendChild(el("span", "music-why-value", Number(value).toFixed(2)));
        why.appendChild(row);
      });
      if (Number.isFinite(item.signed_delta_us)) {
        const delta = item.signed_delta_us >= 0 ? `+${item.signed_delta_us}` : String(item.signed_delta_us);
        why.appendChild(el("div", "music-clock-proof", `HERO → MUSIC EVENT ${delta} µs`));
      }
      card.appendChild(why);
    }
    const actions = el("div", "music-review-actions");
    let desiredDecision = saved.decision || "undecided";
    let saveChain = Promise.resolve();
    const enqueueSave = () => {
      const decision = desiredDecision;
      const notes = note.value;
      saveChain = saveChain.then(async () => {
        const response = await fetch(`/api/frags/${id}/music-auditions/${item.audition_id}/review`, {
          method: "PUT", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ decision, notes }),
        });
        if (!response.ok || desiredDecision !== decision) return;
        saved.decision = decision;
        saved.notes = notes;
        actions.querySelectorAll("button").forEach((button) => button.classList.remove("on"));
        const active = Array.from(actions.querySelectorAll("button"))
          .find((button) => button.dataset.decision === decision);
        if (active) active.classList.add("on");
      });
    };
    [["favorite", "FAVORITE"], ["reject", "REJECT"]].forEach(([decision, label]) => {
      const b = el("button", "", label);
      b.dataset.decision = decision;
      if (saved.decision === decision) b.classList.add("on");
      b.addEventListener("click", () => {
        desiredDecision = decision;
        enqueueSave();
      });
      actions.appendChild(b);
    });
    card.appendChild(actions);
    const note = document.createElement("textarea");
    note.className = "music-notes";
    note.placeholder = "Why this region works or fails…";
    note.value = saved.notes || "";
    note.addEventListener("change", enqueueSave);
    card.appendChild(note);
    box.appendChild(card);
  });
  if (!data.items.length) box.appendChild(el("div", "hint", "No audition set for this frag."));
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

/* ============================= live director ============================= */
/* Path A launcher (docs/reference/replay-runtime-feasibility.md): opens a
 * VISIBLE wolfcamql window seeked to this frag with freecam armed. The user
 * flies the camera live in that window, at the keyboard — this panel only
 * shows session status and a captured-keyframe counter, it does not stream
 * any video. */

function renderDirectorBox() {
  const box = $("director-box");
  if (!box) return;
  const d = state.director;
  const frag = document.createDocumentFragment();

  if (!d) {
    const btn = el("button", "", "Fly this live (Director)");
    btn.id = "btn-director-launch";
    btn.addEventListener("click", launchDirector);
    frag.appendChild(btn);
    frag.appendChild(el("div", "hint",
      "Opens a real wolfcam window on this machine, seeked to this frag."));
    box.replaceChildren(frag);
    return;
  }

  const status = el("div", "");
  status.id = "director-status";
  if (!d.recipeId) {
    status.classList.add("live");
    status.textContent =
      `Live session running — fly in the wolfcam window, press ${d.keybind} to mark a keyframe.`;
  } else {
    status.textContent = "Session stopped — recipe saved.";
  }
  frag.appendChild(status);

  const countLine = el("div", "");
  countLine.appendChild(el("span", "", "keyframes captured: "));
  countLine.appendChild(el("span", "director-count", String(d.count)));
  frag.appendChild(countLine);

  if (!d.recipeId) {
    const stopBtn = el("button", "", "Stop & Save Recipe");
    stopBtn.id = "btn-director-save";
    stopBtn.disabled = d.saving === true;
    stopBtn.addEventListener("click", stopAndSaveDirector);
    frag.appendChild(stopBtn);
  } else {
    frag.appendChild(el("h3", "", "scene_recipe_id"));
    frag.appendChild(el("div", "", d.recipeId)).id = "director-recipe";
  }
  box.replaceChildren(frag);
}

async function launchDirector() {
  const id = state.selectedId;
  if (id == null) return;
  const btn = $("btn-director-launch");
  if (btn) btn.disabled = true;
  const res = await fetch(`/api/frags/${id}/director/launch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  if (!res.ok) {
    if (btn) btn.disabled = false;
    const err = await res.json().catch(() => ({}));
    alert(err.detail || "could not launch director session");
    return;
  }
  const data = await res.json();
  if (state.selectedId !== id) return;   // user moved on before launch returned
  state.director = {
    sessionId: data.session_id, keybind: data.keybind,
    since: 0, count: 0, recipeId: null, pollTimer: null,
  };
  renderDirectorBox();
  scheduleDirectorPoll();
}

function scheduleDirectorPoll() {
  const d = state.director;
  if (!d || d.recipeId) return;
  clearTimeout(d.pollTimer);
  d.pollTimer = setTimeout(pollDirectorKeyframes, 2000);
}

async function pollDirectorKeyframes() {
  const d = state.director;
  if (!d || d.recipeId) return;
  const res = await fetch(
    `/api/director/${d.sessionId}/keyframes?since=${d.since}`);
  if (res.ok) {
    const data = await res.json();
    if (state.director === d) {
      d.since = data.next_offset;
      d.count += data.count;
      renderDirectorBox();
    }
  }
  scheduleDirectorPoll();
}

async function stopAndSaveDirector() {
  const d = state.director;
  if (!d) return;
  d.saving = true;
  renderDirectorBox();
  clearTimeout(d.pollTimer);
  await fetch(`/api/director/${d.sessionId}/stop`, { method: "POST" });
  const res = await fetch(`/api/director/${d.sessionId}/save_recipe`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  if (state.director !== d) return;
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    d.saving = false;
    alert(err.detail || "could not save recipe");
    renderDirectorBox();
    return;
  }
  const data = await res.json();
  d.recipeId = data.scene_recipe_id;
  d.saving = false;
  renderDirectorBox();
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
  else if ((e.key === "ArrowLeft" || e.key === ",") && e.shiftKey) frameStep(-60);
  else if ((e.key === "ArrowRight" || e.key === ".") && e.shiftKey) frameStep(60);
  else if (e.key === "ArrowLeft" || e.key === ",") frameStep(-1);
  else if (e.key === "ArrowRight" || e.key === ".") frameStep(1);
  else if (e.key === "i" || e.key === "I") setLoop("in");
  else if (e.key === "o" || e.key === "O") setLoop("out");
  else if (e.key === "l" || e.key === "L") {
    if (state.loopIn != null || state.loopOut != null) clearLoop();
    else if (!player.hidden) {
      state.loopIn = 0;
      state.loopOut = player.duration || null;
      updateTransport();
      renderEventStrip();
    }
  }
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
loadTaxonomy();
loadGroupFilters();
loadList();
