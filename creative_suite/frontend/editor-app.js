// editor-app.js — PANTHEON Editor bootstrap.
// Wires the three-pane shell to the /api/editor/* backend.

import { editorApi } from "/cinema-static/editor-api.js";
import { renderTimeline, markSelected, reorderClips, bodyDurationS }
  from "/cinema-static/editor-timeline.js";
import { renderInspector } from "/cinema-static/editor-inspector.js";

const S = {
  part: null,
  state: null,
  selectedIdx: null,
  parts: [],
  dirty: false,
};

// ── DOM refs ─────────────────────────────
const els = {
  status:     document.getElementById("status-pill"),
  partSelect: document.getElementById("part-select"),
  partsList:  document.getElementById("parts-list"),
  videoStrip: document.getElementById("track-video-strip"),
  audioGame:  document.getElementById("track-audio-game-strip"),
  audioMusic: document.getElementById("track-audio-music-strip"),
  monitorV:   document.getElementById("monitor-video"),
  monitorMeta:document.getElementById("monitor-meta"),
  clipLabel:  document.querySelector("#monitor-meta .clip-label"),
  clipTier:   document.querySelector("#monitor-meta .clip-tier"),
  clipSection:document.querySelector("#monitor-meta .clip-section"),
  clipDur:    document.querySelector("#monitor-meta .clip-dur"),
  clipCount:  document.getElementById("clip-count"),
  removedCount: document.getElementById("removed-count"),
  bodyDuration: document.getElementById("body-duration"),
  dirtyFlag:  document.getElementById("dirty-flag"),
  inspector:  document.getElementById("inspector"),
  previewBtn: document.getElementById("render-preview"),
  shipBtn:    document.getElementById("render-ship"),
  renderLog:  document.getElementById("render-log"),
  srcBanner:  document.getElementById("source-banner"),
  srcBannerText: document.getElementById("source-banner-text"),
  srcBannerBtn:  document.getElementById("source-banner-prepare"),
};

function setStatus(text, state) {
  els.status.textContent = text;
  if (state) els.status.dataset.state = state;
  else delete els.status.dataset.state;
}

function logLine(msg, color) {
  const line = document.createElement("div");
  line.textContent = msg;
  if (color) line.style.color = color;
  els.renderLog.append(line);
  els.renderLog.scrollTop = els.renderLog.scrollHeight;
}

// ── Part discovery ───────────────────────
async function loadParts() {
  setStatus("loading parts…");
  try {
    S.parts = await editorApi.listParts();
  } catch (e) {
    setStatus("parts failed", "err");
    logLine(`listParts: ${e.message}`, "#ef4444");
    return;
  }
  // Populate the <select> and the left-pane parts list
  els.partSelect.replaceChildren();
  els.partsList.replaceChildren();
  for (const p of S.parts) {
    const opt = document.createElement("option");
    opt.value = String(p.part);
    opt.textContent = `Part ${p.part}`;
    els.partSelect.append(opt);

    const li = document.createElement("li");
    const nm = document.createElement("span");
    nm.textContent = `Part ${p.part}`;
    const ct = document.createElement("span");
    ct.className = "pl-count";
    ct.textContent = p.has_flow_plan ? "✓" : "·";
    li.append(nm, ct);
    li.dataset.part = String(p.part);
    li.addEventListener("click", () => loadPart(p.part));
    els.partsList.append(li);
  }
  if (S.parts.length > 0) {
    const first = S.parts[0].part;
    els.partSelect.value = String(first);
    await loadPart(first);
  } else {
    setStatus("no parts", "err");
  }
}

els.partSelect.addEventListener("change", () =>
  loadPart(parseInt(els.partSelect.value, 10)));

// ── Part state load ──────────────────────
async function loadPart(n) {
  S.part = n;
  S.selectedIdx = null;
  setStatus(`loading part ${n}…`);
  for (const li of els.partsList.querySelectorAll("li")) {
    li.dataset.active = li.dataset.part === String(n) ? "1" : "0";
  }
  try {
    S.state = await editorApi.getState(n);
  } catch (e) {
    setStatus("state failed", "err");
    logLine(`getState(${n}): ${e.message}`, "#ef4444");
    return;
  }
  S.dirty = false;
  els.dirtyFlag.textContent = "";
  paintAll();
  setStatus(`part ${n} ready`, "ok");
  els.previewBtn.disabled = false;
  els.shipBtn.disabled = false;
  // Check source-chunk availability (missing = run preview render to populate)
  checkChunksAvailability(n).catch((e) =>
    logLine(`chunks check: ${e.message}`, "#ef4444"));
}

async function checkChunksAvailability(n) {
  let rows;
  try {
    const res = await editorApi.listChunks(n);
    rows = res?.chunks ?? [];
  } catch (e) {
    // Fall through — not fatal.
    return;
  }
  const total = rows.length;
  const missing = rows.filter((r) => !r.exists).length;
  if (missing === 0) {
    els.srcBanner.hidden = true;
    return;
  }
  els.srcBanner.hidden = false;
  els.srcBannerText.textContent =
    `${missing}/${total} source chunks not on disk — proxies + preview are unavailable ` +
    `until chunks are built. Build chunks once via a preview render; they persist after.`;
}

els.srcBannerBtn?.addEventListener("click", () => {
  if (!S.part) return;
  doRender("preview");
});

function paintAll() {
  renderTimeline({
    stripEl: els.videoStrip,
    state: S.state,
    onSelect: (idx) => selectClip(idx),
    onReorder: (from, to) => reorderAndPatch(from, to),
    onToggleRemoved: (idx) => toggleRemoved(idx),
  });
  paintStatusLine();
  if (S.selectedIdx != null) markSelected(els.videoStrip, S.selectedIdx);
  paintInspector();
}

function paintStatusLine() {
  const n = S.state?.clips?.length ?? 0;
  const r = S.state?.clips?.filter(c => c.removed).length ?? 0;
  const b = bodyDurationS(S.state?.clips ?? []);
  els.clipCount.textContent = `${n} clips`;
  els.removedCount.textContent = `${r} removed`;
  els.bodyDuration.textContent = `body ${b.toFixed(1)}s`;
  els.dirtyFlag.textContent = S.dirty ? " · unsaved-locally" : "";
}

function paintInspector() {
  const clip = S.selectedIdx != null ? S.state.clips[S.selectedIdx] : null;
  renderInspector({
    hostEl: els.inspector,
    clip,
    idx: S.selectedIdx,
    onPatch: async (ops) => patchLocal(ops),
  });
}

// ── Clip actions ─────────────────────────
function selectClip(idx) {
  S.selectedIdx = idx;
  markSelected(els.videoStrip, idx);
  paintInspector();
  const clip = S.state.clips[idx];
  if (!clip) return;
  // Monitor: switch proxy source
  els.monitorV.src = editorApi.proxyUrl(S.part, clip.chunk);
  els.monitorV.load();
  els.clipLabel.textContent = clip.chunk;
  els.clipTier.textContent = clip.tier ?? "";
  els.clipSection.textContent = clip.section_role ?? "";
  const dur = clip.duration != null ? clip.duration.toFixed(2) : "?";
  els.clipDur.textContent = `${dur}s`;
}

async function patchLocal(ops) {
  try {
    S.state = await editorApi.patchState(S.part, ops);
    paintAll();
  } catch (e) {
    setStatus("patch failed", "err");
    logLine(`patch: ${e.message}`, "#ef4444");
  }
}

async function reorderAndPatch(from, to) {
  // Optimistic local reorder → PUT full state (jsonpatch move semantics
  // get awkward for deep reorders; full PUT is simpler).
  S.state.clips = reorderClips(S.state.clips, from, to);
  try {
    S.state = await editorApi.putState(S.part, S.state);
  } catch (e) {
    setStatus("reorder failed", "err");
    logLine(`reorder: ${e.message}`, "#ef4444");
  }
  paintAll();
}

async function toggleRemoved(idx) {
  const clip = S.state.clips[idx];
  if (!clip) return;
  await patchLocal([{
    op: "replace",
    path: `/clips/${idx}/removed`,
    value: !clip.removed,
  }]);
}

// ── Render buttons ───────────────────────
async function doRender(mode) {
  els.previewBtn.disabled = true;
  els.shipBtn.disabled = true;
  setStatus(`starting ${mode}…`, "busy");
  logLine(`──── ${new Date().toLocaleTimeString()} · ${mode} render part ${S.part}`);
  try {
    const res = await editorApi.render(S.part, mode);
    logLine(`job ${res.job_id} · ${res.n_clips} clips · ${res.n_removed} removed`);
    const es = editorApi.subscribeJob(res.job_id, (ev) => {
      logLine(`[${ev.phase} ${ev.pct ?? ""}%] ${ev.msg ?? ""}`);
      if (ev.phase === "done" || ev.phase === "failed") {
        es.close();
        setStatus(ev.phase === "done" ? "render ok" : "render failed",
                  ev.phase === "done" ? "ok" : "err");
        els.previewBtn.disabled = false;
        els.shipBtn.disabled = false;
        // After a successful render, chunks exist. Re-check.
        if (ev.phase === "done" && S.part != null) {
          checkChunksAvailability(S.part).catch(() => {});
        }
      }
    }, (err) => {
      logLine(`[error] ${err?.message ?? err}`, "#ef4444");
      els.previewBtn.disabled = false;
      els.shipBtn.disabled = false;
    });
  } catch (e) {
    const code = e.status;
    if (code === 409) {
      logLine("busy — another render is running", "#ef4444");
      setStatus("busy", "err");
    } else {
      logLine(`render failed: ${e.message}`, "#ef4444");
      setStatus("render failed", "err");
    }
    els.previewBtn.disabled = false;
    els.shipBtn.disabled = false;
  }
}

els.previewBtn.addEventListener("click", () => doRender("preview"));
els.shipBtn.addEventListener("click", () => {
  if (!confirm(`Ship-render Part ${S.part} at final quality? This is the slow path.`)) return;
  doRender("ship");
});

// Kick off
loadParts().catch((err) => {
  setStatus("boot failed", "err");
  logLine(`boot: ${err.message}`, "#ef4444");
});
