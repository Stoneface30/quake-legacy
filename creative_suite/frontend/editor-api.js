// editor-api.js — thin wrapper around /api/editor/* endpoints.
const BASE = "/api/editor";

async function j(res) {
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    const err = new Error(`HTTP ${res.status}: ${text}`);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

export const editorApi = {
  async listParts() {
    // Parts are discovered via phase1 list — editor is just a view
    const r = await fetch("/api/phase1/parts");
    return j(r);
  },
  async getState(part) {
    return j(await fetch(`${BASE}/state/${part}`));
  },
  async patchState(part, ops) {
    return j(await fetch(`${BASE}/state/${part}`, {
      method: "PATCH",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ ops }),
    }));
  },
  async putState(part, state) {
    return j(await fetch(`${BASE}/state/${part}`, {
      method: "PUT",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ state }),
    }));
  },
  async listChunks(part) {
    return j(await fetch(`${BASE}/chunks/${part}`));
  },
  chunkUrl(part, name) {
    return `${BASE}/chunk/${part}/${encodeURIComponent(name)}`;
  },
  proxyUrl(part, name) {
    return `${BASE}/proxy/${part}/${encodeURIComponent(name)}`;
  },
  otioUrl(part) {
    return `${BASE}/otio/${part}`;
  },
  async listVersions(part) {
    return j(await fetch(`/api/phase1/parts/${part}/versions`));
  },
  async render(part, mode, tag) {
    const url = new URL(`${BASE}/render/${part}`, location.origin);
    url.searchParams.set("mode", mode);
    if (tag) url.searchParams.set("tag", tag);
    const r = await fetch(url, { method: "POST" });
    return j(r);
  },
  subscribeJob(jobId, onEvent, onError) {
    const es = new EventSource(`/api/phase1/jobs/${jobId}/events`);
    es.addEventListener("phase", (ev) => {
      try { onEvent(JSON.parse(ev.data)); }
      catch (e) { onError?.(e); }
    });
    es.onerror = (err) => onError?.(err);
    return es;
  },
};
