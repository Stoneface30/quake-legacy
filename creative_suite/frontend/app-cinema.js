// creative_suite/frontend/app-cinema.js
import { api } from "/cinema-static/api-client.js";
import { renderMusic, renderMusicSlots } from "/cinema-static/panel-music.js";
import { renderLevels } from "/cinema-static/panel-levels.js";
import { renderVersions } from "/cinema-static/panel-versions.js";
import { renderFlow, reorderClips } from "/cinema-static/panel-flow.js";

export const S = {
  part: null,
  artifacts: null,
  waveform: null,
  flowPlan: null,
  overrides: [],
  dirty: false,
};

async function loadParts() {
  const parts = await api.listParts();
  const sel = document.getElementById("part-select");
  sel.replaceChildren();
  for (const p of parts) {
    const opt = document.createElement("option");
    opt.value = String(p.part);
    opt.textContent = `Part ${p.part}`;
    sel.append(opt);
  }
  sel.addEventListener("change", () => loadPart(parseInt(sel.value, 10)));
  if (parts.length > 0) {
    sel.value = String(parts[0].part);
    await loadPart(parts[0].part);
  }
}

export async function loadPart(n) {
  S.part = n;
  S.artifacts = await api.getArtifacts(n);
  try { S.waveform = await api.getWaveform(n); }
  catch { S.waveform = null; }
  S.flowPlan = S.artifacts?.flow_plan ?? null;
  renderMusic({
    canvas: document.getElementById("wave-canvas"),
    overlay: document.getElementById("wave-overlay"),
    metaEl: document.getElementById("wave-meta"),
    waveform: S.waveform,
    musicStructure: S.artifacts?.music_structure,
    onDownbeatDrop: async (seamIdx, tS) => {
      S.flowPlan.beat_snapped_offsets = S.flowPlan.beat_snapped_offsets ?? [];
      const existing = S.flowPlan.beat_snapped_offsets.findIndex(o => o.seam_idx === seamIdx);
      if (existing >= 0) S.flowPlan.beat_snapped_offsets[existing].target_t_s = tS;
      else S.flowPlan.beat_snapped_offsets.push({ seam_idx: seamIdx, target_t_s: tS });
      await api.putFlowPlan(S.part, S.flowPlan);
      document.getElementById("flow-dirty").textContent = ` · seam ${seamIdx} → ${tS.toFixed(2)}s`;
    },
  });
  const tracks = await api.listTracks();
  const mov = await api.getMusicOverride(n);
  renderMusicSlots({
    slotsEl: document.getElementById("music-slots"),
    tracks,
    override: mov,
    onChange: async (role, path) => {
      const next = { ...mov };
      if (role === "main") next.main = path ? [path] : [];
      else next[role] = path;
      await api.putMusicOverride(S.part, next);
      Object.assign(mov, next);
    },
  });
  renderLevels({
    barsEl: document.getElementById("levels-bars"),
    canvas: document.getElementById("drift-canvas"),
    gateEl: document.getElementById("levels-gate"),
    levels: S.artifacts?.levels,
    syncAudit: S.artifacts?.sync_audit,
  });
  const versions = await api.listVersions(n);
  renderVersions({
    listEl: document.getElementById("versions-list"),
    rows: versions,
    onLoadA: (r) => console.log("load A", r),
    onLoadB: (r) => console.log("load B", r),
  });
  S.overrides = await api.getOverrides(n);
  const byChunk = new Map(S.overrides.map(o => [o.chunk, o]));
  if (S.flowPlan?.clips) {
    for (const c of S.flowPlan.clips) c.override = byChunk.get(c.chunk) ?? {};
  }
  S.dirty = false;
  document.getElementById("flow-save").disabled = true;
  document.getElementById("flow-dirty").textContent = "";
  refreshFlow();
  // panel modules are wired in later tasks; loadPart stays the dispatch point
}

function refreshFlow() {
  renderFlow({
    gridEl: document.getElementById("flow-grid"),
    flowPlan: S.flowPlan,
    onReorder: (from, to) => {
      S.flowPlan.clips = reorderClips(S.flowPlan.clips, from, to);
      markDirty();
      refreshFlow();
    },
    onClipOverride: async (clip, field, value) => {
      const existing = S.overrides.find(o => o.chunk === clip.chunk)
        ?? { chunk: clip.chunk };
      existing[field] = value;
      const idx = S.overrides.findIndex(o => o.chunk === clip.chunk);
      if (idx < 0) S.overrides.push(existing); else S.overrides[idx] = existing;
      clip.override = existing;
      await api.putOverrides(S.part, S.overrides);
    },
    onSeamDrag: null,       // wired in Task C3
  });
}

function markDirty() {
  S.dirty = true;
  document.getElementById("flow-save").disabled = false;
  document.getElementById("flow-dirty").textContent = " · unsaved changes";
}

loadParts().catch((err) => {
  document.getElementById("status-pill").textContent = "load failed";
  console.error(err);
});

document.getElementById("flow-save").addEventListener("click", async () => {
  await api.putFlowPlan(S.part, S.flowPlan);
  S.dirty = false;
  document.getElementById("flow-save").disabled = true;
  document.getElementById("flow-dirty").textContent = " · saved";
});

const rebuildBtn = document.getElementById("rebuild-btn");
rebuildBtn.disabled = false;
rebuildBtn.textContent = "REBUILD";
document.getElementById("rebuild-form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const tag = document.getElementById("rebuild-tag").value.trim();
  const notes = document.getElementById("rebuild-notes").value;
  if (!tag) return;
  const logEl = document.getElementById("rebuild-log");
  logEl.replaceChildren();
  rebuildBtn.disabled = true;
  try {
    const { job_id } = await api.rebuild(S.part, tag, notes, "ship");
    const es = api.subscribeJob(job_id, (ev) => {
      const line = document.createElement("div");
      line.textContent = `[${ev.phase} ${ev.pct}%] ${ev.msg}`;
      logEl.append(line);
      logEl.scrollTop = logEl.scrollHeight;
      if (ev.phase === "done" || ev.phase === "failed") {
        es.close();
        rebuildBtn.disabled = false;
        if (ev.phase === "done") loadPart(S.part);
      }
    }, (err) => {
      const line = document.createElement("div");
      line.textContent = `[error] ${err?.message ?? err}`;
      line.style.color = "#ef4444";
      logEl.append(line);
      rebuildBtn.disabled = false;
    });
  } catch (err) {
    const line = document.createElement("div");
    line.textContent = err?.code === 409
      ? "Another render is running. Wait."
      : `failed: ${err.message}`;
    line.style.color = "#ef4444";
    logEl.append(line);
    rebuildBtn.disabled = false;
  }
});