// creative_suite/frontend/app-cinema.js
import { api } from "/cinema-static/api-client.js";
import { renderMusic } from "/cinema-static/panel-music.js";
import { renderLevels } from "/cinema-static/panel-levels.js";

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
  });
  renderLevels({
    barsEl: document.getElementById("levels-bars"),
    canvas: document.getElementById("drift-canvas"),
    gateEl: document.getElementById("levels-gate"),
    levels: S.artifacts?.levels,
    syncAudit: S.artifacts?.sync_audit,
  });
  // panel modules are wired in later tasks; loadPart stays the dispatch point
}

loadParts().catch((err) => {
  document.getElementById("status-pill").textContent = "load failed";
  console.error(err);
});