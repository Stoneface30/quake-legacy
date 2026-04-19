// creative_suite/frontend/api-client.js
// Thin typed wrapper around /api/phase1/*. Pure fetch + JSON.

const BASE = "/api/phase1";

async function jget(path) {
  const r = await fetch(`${BASE}${path}`);
  if (!r.ok) throw new Error(`GET ${path} → ${r.status}`);
  return r.json();
}

async function jput(path, body) {
  const r = await fetch(`${BASE}${path}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`PUT ${path} → ${r.status}`);
  return r.json();
}

async function jpost(path, body) {
  const r = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (r.status === 409) {
    const e = new Error("busy");
    e.code = 409;
    throw e;
  }
  if (!r.ok) throw new Error(`POST ${path} → ${r.status}`);
  return r.json();
}

export const api = {
  listParts: () => jget("/parts"),
  getArtifacts: (n) => jget(`/parts/${n}/artifacts`),
  getFlowPlan: (n) => jget(`/parts/${n}/flow-plan`),
  putFlowPlan: (n, plan) => jput(`/parts/${n}/flow-plan`, plan),
  listVersions: (n) => jget(`/parts/${n}/versions`),
  getWaveform: (n) => jget(`/parts/${n}/waveform`),
  getOverrides: (n) => jget(`/parts/${n}/overrides`),
  putOverrides: (n, entries) => jput(`/parts/${n}/overrides`, { entries }),
  getMusicOverride: (n) => jget(`/parts/${n}/music-override`),
  putMusicOverride: (n, body) => jput(`/parts/${n}/music-override`, body),
  listTracks: () => jget("/music/tracks"),
  rebuild: (n, tag, notes, mode = "ship") =>
    jpost(`/parts/${n}/rebuild`, { tag, notes, mode }),
  preview: (n, clipChunks, tier = "A") =>
    jpost(`/parts/${n}/preview`, { clip_chunks: clipChunks, tier }),
  subscribeJob(jobId, onEvent, onError) {
    const es = new EventSource(`${BASE}/jobs/${jobId}/events`);
    es.onmessage = (ev) => {
      try { onEvent(JSON.parse(ev.data)); }
      catch (err) { onError?.(err); }
    };
    es.onerror = (err) => onError?.(err);
    return es;
  },
};