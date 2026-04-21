// Task 7 — Side-by-side compare canvas.
//
// openTextureCompare(originalUrl, variantUrl)
//   Two <canvas> side by side, shared {x, y, zoom}. Wheel zooms, drag pans,
//   both canvases re-render in lockstep. Optional 1-px pixel ruler overlay.
//
// openMd3Compare(md3UrlA, md3UrlB)
//   Two MD3Viewer instances. Master is A — its OrbitControls fire 'change'
//   and we mirror camera.position + controls.target onto B every frame.
//
// Both openers mount a <dialog> overlay. Close via the × button, Esc key,
// or clicking the backdrop.

import { MD3Viewer } from "/web/js/md3viewer.js";

const DEFAULT_CAM = { x: 0, y: 0, zoom: 1.0 };
const MIN_ZOOM = 0.1;
const MAX_ZOOM = 32.0;

function $mk(tag, opts = {}) {
  const el = document.createElement(tag);
  if (opts.cls) el.className = opts.cls;
  if (opts.text != null) el.textContent = opts.text;
  if (opts.attrs) for (const [k, v] of Object.entries(opts.attrs)) el.setAttribute(k, v);
  return el;
}

function ensureDialogHost() {
  let host = document.getElementById("compare-dialog");
  if (host) return host;
  host = $mk("dialog", { attrs: { id: "compare-dialog" } });
  host.addEventListener("click", (ev) => {
    // Click on the backdrop closes; click on the inner card does not.
    if (ev.target === host) host.close();
  });
  host.addEventListener("cancel", () => host.close());  // Esc
  document.body.appendChild(host);
  return host;
}

function resetDialog(host) {
  while (host.firstChild) host.removeChild(host.firstChild);
  const card = $mk("div", { cls: "compare-card" });
  const head = $mk("div", { cls: "compare-head" });
  head.appendChild($mk("strong", { text: "Compare" }));
  const closeBtn = $mk("button", { cls: "compare-close", text: "×" });
  closeBtn.addEventListener("click", () => host.close());
  head.appendChild(closeBtn);
  card.appendChild(head);
  host.appendChild(card);
  return card;
}

// ---------------------------------------------------------------------- //
// Texture compare
// ---------------------------------------------------------------------- //

async function loadImage(url) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error(`failed to load ${url}`));
    img.src = url;
  });
}

function drawTexture(canvas, img, cam, showRuler) {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  const w = canvas.width;
  const h = canvas.height;
  ctx.fillStyle = "#050505";
  ctx.fillRect(0, 0, w, h);
  ctx.imageSmoothingEnabled = false;

  const drawW = img.width * cam.zoom;
  const drawH = img.height * cam.zoom;
  const drawX = (w - drawW) / 2 + cam.x;
  const drawY = (h - drawH) / 2 + cam.y;
  ctx.drawImage(img, drawX, drawY, drawW, drawH);

  if (showRuler) drawPixelRuler(ctx, w, h, cam);
}

function drawPixelRuler(ctx, w, h, cam) {
  ctx.strokeStyle = "rgba(255,120,0,0.25)";
  ctx.lineWidth = 1;
  // Only draw if zoomed in enough that 1-px cells are ≥ 4 screen px.
  if (cam.zoom < 4) return;
  const step = cam.zoom;
  const originX = (w / 2 + cam.x) % step;
  const originY = (h / 2 + cam.y) % step;
  ctx.beginPath();
  for (let x = originX; x < w; x += step) {
    ctx.moveTo(x + 0.5, 0); ctx.lineTo(x + 0.5, h);
  }
  for (let y = originY; y < h; y += step) {
    ctx.moveTo(0, y + 0.5); ctx.lineTo(w, y + 0.5);
  }
  ctx.stroke();
}

export async function openTextureCompare(originalUrl, variantUrl) {
  const host = ensureDialogHost();
  const card = resetDialog(host);

  const stage = $mk("div", { cls: "compare-stage" });
  const leftWrap = $mk("div", { cls: "compare-pane" });
  const rightWrap = $mk("div", { cls: "compare-pane" });
  const labelA = $mk("span", { cls: "compare-label", text: "Original" });
  const labelB = $mk("span", { cls: "compare-label", text: "Variant" });
  const canvasA = $mk("canvas", { cls: "compare-canvas", attrs: { width: "512", height: "512" } });
  const canvasB = $mk("canvas", { cls: "compare-canvas", attrs: { width: "512", height: "512" } });
  leftWrap.appendChild(labelA); leftWrap.appendChild(canvasA);
  rightWrap.appendChild(labelB); rightWrap.appendChild(canvasB);
  stage.appendChild(leftWrap);
  stage.appendChild(rightWrap);
  card.appendChild(stage);

  const controls = $mk("div", { cls: "compare-controls" });
  const rulerBtn = $mk("button", { text: "Toggle pixel ruler" });
  const resetBtn = $mk("button", { text: "Reset view" });
  const zoomLabel = $mk("span", { cls: "muted" });
  controls.appendChild(rulerBtn);
  controls.appendChild(resetBtn);
  controls.appendChild(zoomLabel);
  card.appendChild(controls);

  host.showModal();

  const cam = { ...DEFAULT_CAM };
  let showRuler = false;
  let imgA, imgB;
  try {
    [imgA, imgB] = await Promise.all([loadImage(originalUrl), loadImage(variantUrl)]);
  } catch (e) {
    const err = $mk("p", { cls: "muted", text: e.message });
    card.appendChild(err);
    return;
  }

  function render() {
    drawTexture(canvasA, imgA, cam, showRuler);
    drawTexture(canvasB, imgB, cam, showRuler);
    zoomLabel.textContent = `zoom ${cam.zoom.toFixed(2)}× · (${cam.x.toFixed(0)}, ${cam.y.toFixed(0)})`;
  }

  // Mouse-wheel zoom — both canvases respond to either canvas's wheel event.
  function onWheel(ev) {
    ev.preventDefault();
    const delta = -ev.deltaY * 0.002;
    const prev = cam.zoom;
    cam.zoom = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, prev * (1 + delta)));
    // Anchor zoom near cursor for intuitive behavior.
    const rect = ev.currentTarget.getBoundingClientRect();
    const cx = ev.clientX - rect.left - rect.width / 2;
    const cy = ev.clientY - rect.top - rect.height / 2;
    const scale = cam.zoom / prev;
    cam.x = cx - (cx - cam.x) * scale;
    cam.y = cy - (cy - cam.y) * scale;
    render();
  }
  canvasA.addEventListener("wheel", onWheel, { passive: false });
  canvasB.addEventListener("wheel", onWheel, { passive: false });

  // Drag pan — mousedown anywhere in the stage, move anywhere.
  let dragging = false;
  let lastX = 0, lastY = 0;
  function onDown(ev) { dragging = true; lastX = ev.clientX; lastY = ev.clientY; }
  function onMove(ev) {
    if (!dragging) return;
    cam.x += (ev.clientX - lastX);
    cam.y += (ev.clientY - lastY);
    lastX = ev.clientX; lastY = ev.clientY;
    render();
  }
  function onUp() { dragging = false; }
  [canvasA, canvasB].forEach(c => {
    c.addEventListener("mousedown", onDown);
    c.addEventListener("mousemove", onMove);
    c.addEventListener("mouseup", onUp);
    c.addEventListener("mouseleave", onUp);
  });

  rulerBtn.addEventListener("click", () => { showRuler = !showRuler; render(); });
  resetBtn.addEventListener("click", () => {
    cam.x = 0; cam.y = 0; cam.zoom = 1.0; render();
  });

  render();
}

// ---------------------------------------------------------------------- //
// MD3 compare — mirror OrbitControls from A onto B every frame.
// ---------------------------------------------------------------------- //

export async function openMd3Compare(md3UrlA, md3UrlB, labelA = "Original", labelB = "Variant") {
  const host = ensureDialogHost();
  const card = resetDialog(host);

  const stage = $mk("div", { cls: "compare-stage" });
  const paneA = $mk("div", { cls: "compare-pane" });
  const paneB = $mk("div", { cls: "compare-pane" });
  paneA.appendChild($mk("span", { cls: "compare-label", text: labelA }));
  paneB.appendChild($mk("span", { cls: "compare-label", text: labelB }));
  const stageA = $mk("div", { cls: "compare-md3" });
  const stageB = $mk("div", { cls: "compare-md3" });
  paneA.appendChild(stageA); paneB.appendChild(stageB);
  stage.appendChild(paneA); stage.appendChild(paneB);
  card.appendChild(stage);
  host.showModal();

  const a = new MD3Viewer(stageA);
  const b = new MD3Viewer(stageB);
  // B mirrors A — disable B's turntable so user-driven pose wins.
  b.setTurntable(false);
  a.setTurntable(false);

  // Sync camera + target on each animation frame. MD3Viewer uses
  // OrbitControls internally; each viewer exposes `camera` and `controls`.
  let rafId = 0;
  function syncLoop() {
    if (a.camera && b.camera && a.controls && b.controls) {
      b.camera.position.copy(a.camera.position);
      b.camera.quaternion.copy(a.camera.quaternion);
      b.controls.target.copy(a.controls.target);
      b.controls.update();
    }
    rafId = requestAnimationFrame(syncLoop);
  }
  rafId = requestAnimationFrame(syncLoop);

  host.addEventListener("close", () => {
    cancelAnimationFrame(rafId);
    try { a.dispose(); } catch (_) {}
    try { b.dispose(); } catch (_) {}
  }, { once: true });

  try {
    await Promise.all([a.loadUrl(md3UrlA), b.loadUrl(md3UrlB)]);
  } catch (e) {
    card.appendChild($mk("p", { cls: "muted", text: `MD3 load failed: ${e.message}` }));
  }
}
