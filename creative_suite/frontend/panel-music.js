// creative_suite/frontend/panel-music.js
// Draws the waveform + downbeat grid + drop markers + section bands.
// All dynamic DOM built via createElement + textContent. No innerHTML.

export function renderMusic({ canvas, overlay, metaEl, waveform, musicStructure }) {
  drawWave(canvas, waveform);
  overlay.replaceChildren();
  const bodyDur = musicStructure?.body_duration_s ?? waveform?.duration_s ?? 0;
  if (!bodyDur) {
    const p = document.createElement("p");
    p.className = "hint";
    p.textContent = "No music structure available for this part.";
    overlay.append(p);
    return;
  }
  const W = canvas.clientWidth;
  for (const sec of musicStructure.sections ?? []) {
    const band = document.createElement("div");
    band.className = `sec-band sec-${sec.shape ?? "build"}`;
    band.style.left = `${(sec.start / bodyDur) * W}px`;
    band.style.width = `${((sec.end - sec.start) / bodyDur) * W}px`;
    band.title = `${sec.shape} ${sec.start.toFixed(1)}–${sec.end.toFixed(1)}s`;
    overlay.append(band);
  }
  for (const db of musicStructure.downbeats ?? []) {
    const line = document.createElement("div");
    line.className = "downbeat-line";
    line.style.left = `${(db.t / bodyDur) * W}px`;
    line.style.opacity = String(0.2 + 0.8 * (db.salience ?? 0.5));
    line.dataset.tMs = String(Math.round(db.t * 1000));
    overlay.append(line);
  }
  for (const d of musicStructure.drops ?? []) {
    const tri = document.createElement("div");
    tri.className = "drop-marker";
    tri.style.left = `${(d.t / bodyDur) * W - 4}px`;
    tri.title = `drop strength ${(d.strength ?? 0).toFixed(2)}`;
    overlay.append(tri);
  }
  metaEl.replaceChildren();
  const bpmSpan = document.createElement("span");
  bpmSpan.textContent = `BPM ${(musicStructure.bpm_global ?? 0).toFixed(1)} · `;
  const countSpan = document.createElement("span");
  countSpan.textContent =
    `${(musicStructure.sections ?? []).length} sections · ` +
    `${(musicStructure.downbeats ?? []).length} downbeats · ` +
    `${(musicStructure.drops ?? []).length} drops`;
  metaEl.append(bpmSpan, countSpan);
}

function drawWave(canvas, waveform) {
  const ctx = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height;
  ctx.fillStyle = "#0b0b0d";
  ctx.fillRect(0, 0, W, H);
  const peaks = waveform?.peaks ?? [];
  if (peaks.length === 0) {
    ctx.fillStyle = "#52525b";
    ctx.font = "13px sans-serif";
    ctx.fillText("no waveform", 12, H / 2);
    return;
  }
  const mid = H / 2;
  const step = W / peaks.length;
  ctx.strokeStyle = "#60a5fa";
  ctx.lineWidth = 1;
  ctx.beginPath();
  for (let i = 0; i < peaks.length; i++) {
    const [mn, mx] = peaks[i];
    const x = i * step;
    ctx.moveTo(x, mid - mx * mid);
    ctx.lineTo(x, mid - mn * mid);
  }
  ctx.stroke();
}
