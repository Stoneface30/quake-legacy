// creative_suite/frontend/panel-preview.js
// Tier A: DRAFT PREVIEW kicks a /preview job, streams SSE, shows mp4.
// Tier B: wireEngine() — WebSocket thumbnail stream (Task D5).

import { api } from "/cinema-static/api-client.js";

export function wirePreviewA({ logEl, box, btn, getSelection, getPart }) {
  btn.addEventListener("click", async () => {
    const chunks = getSelection();
    if (chunks.length === 0) return;
    logEl.replaceChildren();
    btn.disabled = true;
    let mp4Path = null;
    try {
      const { job_id } = await api.preview(getPart(), chunks, "A");
      const es = api.subscribeJob(job_id, (ev) => {
        const ln = document.createElement("div");
        ln.textContent = `[${ev.phase} ${ev.pct}%] ${ev.msg}`;
        logEl.append(ln);
        logEl.scrollTop = logEl.scrollHeight;
        if (ev.phase === "done") mp4Path = ev.msg;
        if (ev.phase === "done" || ev.phase === "failed") {
          es.close();
          btn.disabled = false;
          if (mp4Path) renderMp4(box, mp4Path);
        }
      }, (err) => {
        const ln = document.createElement("div");
        ln.textContent = `[error] ${err?.message ?? err}`;
        ln.style.color = "#ef4444";
        logEl.append(ln);
        btn.disabled = false;
      });
    } catch (err) {
      btn.disabled = false;
      const ln = document.createElement("div");
      ln.textContent = err?.code === 409 ? "Busy — another job running." : `failed: ${err.message}`;
      logEl.append(ln);
    }
  });
}

function renderMp4(box, mp4Path) {
  box.replaceChildren();
  const v = document.createElement("video");
  v.controls = true;
  v.preload = "auto";
  const rel = mp4Path.split(/[\\/]/).slice(-3).map(encodeURIComponent).join("/");
  v.src = `/media/phase1/${rel}`;
  box.append(v);
}
