// Creative Suite v2 — /creative page wiring.
// Task 4: asset tree + texture preview + MD3 viewer (Three.js turntable).
// Task 5/6/9 will flesh out the prompt + variant panel.

import { MD3Viewer } from "/web/js/md3viewer.js";

const state = {
  tree: null,
  activeAssetId: null,
  filter: "",
  md3: null,  // active MD3Viewer instance (disposed on re-select)
};

async function loadTree() {
  const r = await fetch("/api/assets");
  if (!r.ok) {
    document.getElementById("tree").textContent = `(/api/assets: ${r.status})`;
    return;
  }
  state.tree = await r.json();
  document.getElementById("asset-count").textContent = `(${state.tree.total})`;
  renderTree();
}

function clearChildren(el) { while (el.firstChild) el.removeChild(el.firstChild); }

function renderTree() {
  const host = document.getElementById("tree");
  clearChildren(host);
  const filter = state.filter.toLowerCase();

  for (const cat of state.tree.categories) {
    const catEl = document.createElement("details");
    catEl.open = filter.length > 0;
    const catSum = document.createElement("summary");
    catSum.textContent = cat.name;
    catEl.appendChild(catSum);

    let catHasVisible = false;

    for (const sub of cat.subcategories) {
      const visibleAssets = filter
        ? sub.assets.filter(a => a.internal_path.toLowerCase().includes(filter))
        : sub.assets;
      if (visibleAssets.length === 0) continue;
      catHasVisible = true;

      const subEl = document.createElement("details");
      subEl.open = filter.length > 0;
      const subSum = document.createElement("summary");
      subSum.className = "sub";
      subSum.textContent = `${sub.name ?? "—"} (${visibleAssets.length})`;
      subEl.appendChild(subSum);

      for (const a of visibleAssets) {
        const link = document.createElement("a");
        link.href = "#";
        link.textContent = a.internal_path.split("/").slice(-1)[0];
        link.title = a.internal_path;
        link.dataset.assetId = String(a.id);
        link.dataset.path = a.internal_path;
        link.addEventListener("click", (ev) => {
          ev.preventDefault();
          selectAsset(a.id, a.internal_path);
        });
        subEl.appendChild(link);
      }
      catEl.appendChild(subEl);
    }

    if (filter.length === 0 || catHasVisible) host.appendChild(catEl);
  }
}

function mkEl(tag, opts = {}) {
  const el = document.createElement(tag);
  if (opts.cls) el.className = opts.cls;
  if (opts.text !== undefined) el.textContent = opts.text;
  if (opts.attrs) for (const [k, v] of Object.entries(opts.attrs)) el.setAttribute(k, v);
  return el;
}

function disposeMd3() {
  if (state.md3) {
    try { state.md3.dispose(); } catch (e) { /* ignore */ }
    state.md3 = null;
  }
}

function mountMd3Viewer(body, id) {
  const stage = mkEl("div", { cls: "md3-stage", attrs: { id: "md3-stage" } });
  body.appendChild(stage);

  const controls = mkEl("div", { cls: "md3-controls" });
  const mkSlider = (label, min, max, step, value, onChange) => {
    const wrap = mkEl("label", { cls: "md3-slider" });
    wrap.appendChild(mkEl("span", { text: label }));
    const input = mkEl("input", {
      attrs: {
        type: "range", min: String(min), max: String(max),
        step: String(step), value: String(value),
      },
    });
    input.addEventListener("input", () => onChange(parseFloat(input.value)));
    wrap.appendChild(input);
    controls.appendChild(wrap);
  };

  body.appendChild(controls);

  const viewer = new MD3Viewer(stage);
  state.md3 = viewer;

  mkSlider("Ambient", 0, 2, 0.05, 0.35, v => viewer.setAmbient(v));
  mkSlider("Key",     0, 4, 0.05, 1.00, v => viewer.setKey(v));
  mkSlider("Rim",     0, 4, 0.05, 0.40, v => viewer.setRim(v));

  const toggle = mkEl("label", { cls: "md3-slider" });
  toggle.appendChild(mkEl("span", { text: "Turntable" }));
  const cb = mkEl("input", { attrs: { type: "checkbox", checked: "checked" } });
  cb.addEventListener("change", () => viewer.setTurntable(cb.checked));
  toggle.appendChild(cb);
  controls.appendChild(toggle);

  viewer.loadUrl(`/api/md3/${id}`).catch(err => {
    clearChildren(stage);
    stage.appendChild(mkEl("p", {
      cls: "muted", text: `MD3 load failed: ${err.message}`,
    }));
  });
}

function selectAsset(id, path) {
  state.activeAssetId = id;
  disposeMd3();

  document.querySelectorAll("#tree a.active").forEach(el => el.classList.remove("active"));
  const link = document.querySelector(`#tree a[data-asset-id="${id}"]`);
  if (link) link.classList.add("active");

  document.getElementById("preview-title").textContent = path;
  const body = document.getElementById("preview-body");
  clearChildren(body);

  const lower = path.toLowerCase();
  if (lower.endsWith(".md3")) {
    mountMd3Viewer(body, id);
  } else if (lower.endsWith(".skin")) {
    const card = mkEl("div", { cls: "md3-card" });
    card.appendChild(mkEl("p", { text: "" })).appendChild(mkEl("strong", { text: "skin file" }));
    card.appendChild(mkEl("p", {
      cls: "muted",
      text: "Skin metadata preview — wired alongside MD3 in a later task.",
    }));
    const linkP = mkEl("p");
    linkP.appendChild(mkEl("a", {
      text: "Download raw bytes",
      attrs: { href: `/api/assets/${id}/raw`, download: "" },
    }));
    card.appendChild(linkP);
    body.appendChild(card);
  } else if (
    lower.endsWith(".tga") || lower.endsWith(".jpg") ||
    lower.endsWith(".jpeg") || lower.endsWith(".png")
  ) {
    const img = mkEl("img", { attrs: { src: `/api/assets/${id}/raw`, alt: path } });
    img.onerror = () => {
      clearChildren(body);
      body.appendChild(mkEl("p", {
        cls: "muted",
        text: "Browser can't decode this format directly. Thumbnail:",
      }));
      body.appendChild(mkEl("img", {
        attrs: { src: `/api/assets/${id}/thumbnail`, alt: path },
      }));
    };
    body.appendChild(img);
  } else {
    const card = mkEl("div", { cls: "md3-card" });
    card.appendChild(mkEl("p", { cls: "muted", text: "No preview available." }));
    const linkP = mkEl("p");
    linkP.appendChild(mkEl("a", {
      text: "Download raw bytes",
      attrs: { href: `/api/assets/${id}/raw`, download: "" },
    }));
    card.appendChild(linkP);
    body.appendChild(card);
  }

  // Meta line
  fetch(`/api/assets/${id}`).then(r => r.json()).then(d => {
    const src = d.source_pk3.split(/[\\/]/).slice(-1)[0];
    document.getElementById("preview-meta").textContent =
      `#${d.id} · ${d.category}/${d.subcategory ?? "—"} · source: ${src}`;
  });

  document.getElementById("btn-generate").disabled = false;
  loadVariants(id);
}

function wireFilter() {
  const f = document.getElementById("filter");
  f.addEventListener("input", () => {
    state.filter = f.value.trim();
    renderTree();
  });
}

// ---------------------------------------------------------------------- //
// Variant panel — Task 5 (generate) + Task 6 (approve/reject/reroll)
// ---------------------------------------------------------------------- //

async function loadVariants(assetId) {
  const grid = document.getElementById("variants-grid");
  clearChildren(grid);
  const r = await fetch(`/api/variants?asset_id=${assetId}`);
  if (!r.ok) {
    grid.appendChild(mkEl("p", { cls: "muted", text: `(list failed: ${r.status})` }));
    return;
  }
  const data = await r.json();
  if (!data.variants.length) {
    grid.appendChild(mkEl("p", { cls: "muted", text: "No variants yet. Hit Generate." }));
    return;
  }
  for (const v of data.variants) insertTile(v);
}

function statusBadge(status) {
  const span = mkEl("span", { cls: `badge badge-${status}`, text: status });
  return span;
}

function insertTile(v) {
  const grid = document.getElementById("variants-grid");
  // Replace existing tile with same id (used after approve/reject updates).
  const existing = grid.querySelector(`[data-variant-id="${v.id}"]`);
  if (existing) existing.remove();

  const tile = mkEl("div", { cls: "variant-tile" });
  tile.dataset.variantId = String(v.id);
  const thumb = mkEl("div", { cls: "variant-thumb" });
  if (v.png_url) {
    thumb.appendChild(mkEl("img", { attrs: { src: v.png_url, alt: `variant ${v.id}` } }));
  } else {
    thumb.appendChild(mkEl("p", { cls: "muted", text: "rendering…" }));
  }
  tile.appendChild(thumb);

  const meta = mkEl("div", { cls: "variant-meta" });
  meta.appendChild(mkEl("span", { text: `#${v.id}` }));
  meta.appendChild(statusBadge(v.status));
  if (v.seed != null) meta.appendChild(mkEl("span", { cls: "muted", text: `seed ${v.seed}` }));
  tile.appendChild(meta);

  const btnRow = mkEl("div", { cls: "variant-btns" });
  const approveBtn = mkEl("button", { cls: "btn-approve", text: "✓ Approve" });
  const rejectBtn = mkEl("button", { cls: "btn-reject", text: "✗ Reject" });
  const rerollBtn = mkEl("button", { cls: "btn-reroll", text: "⟳ Reroll" });
  approveBtn.addEventListener("click", () => sendVariantAction(v.id, "approve"));
  rejectBtn.addEventListener("click", () => sendVariantAction(v.id, "reject"));
  rerollBtn.addEventListener("click", () => sendVariantAction(v.id, "reroll"));
  if (v.status === "approved") approveBtn.disabled = true;
  if (v.status === "rejected") rejectBtn.disabled = true;
  btnRow.appendChild(approveBtn);
  btnRow.appendChild(rejectBtn);
  btnRow.appendChild(rerollBtn);
  tile.appendChild(btnRow);

  // Prepend newest first.
  if (grid.firstChild) grid.insertBefore(tile, grid.firstChild); else grid.appendChild(tile);
}

async function sendVariantAction(variantId, action) {
  const r = await fetch(`/api/variants/${variantId}/${action}`, { method: "POST" });
  if (!r.ok) {
    console.warn(`${action} failed`, r.status);
    return;
  }
  const body = await r.json();
  if (action === "reroll") {
    // New pending tile. Refresh the whole grid to pick it up.
    if (state.activeAssetId) loadVariants(state.activeAssetId);
    if (body.new_variant_id) watchJob(body.new_variant_id, null);
  } else {
    // approve/reject — re-fetch single row for fresh state.
    const fresh = await fetch(`/api/variants/${variantId}`).then(x => x.json());
    if (fresh.id) insertTile(fresh);
  }
}

async function submitGenerate() {
  if (!state.activeAssetId) return;
  const suffix = document.getElementById("user-suffix").value.trim();
  const btn = document.getElementById("btn-generate");
  btn.disabled = true;
  btn.textContent = "Queuing…";
  try {
    const r = await fetch("/api/comfy/queue", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ asset_id: state.activeAssetId, user_prompt: suffix }),
    });
    if (!r.ok) throw new Error(`queue failed: ${r.status}`);
    const body = await r.json();
    // Insert a skeleton tile immediately.
    insertTile({
      id: body.variant_id, asset_id: body.asset_id, status: "pending",
      seed: body.seed, png_url: null,
    });
    watchJob(body.variant_id, /* jobId unknown yet */ null);
  } catch (e) {
    console.error(e);
  } finally {
    btn.disabled = false;
    btn.textContent = "Generate";
  }
}

/**
 * Poll the variants/{id} endpoint until png_path is populated, then update
 * the tile. We also open a WS to /api/comfy/progress/{job_id} once we know
 * the job id, for live status if the runner is async in production.
 */
async function watchJob(variantId, jobId) {
  const deadline = Date.now() + 5 * 60_000;
  let comfyJobId = jobId;
  while (Date.now() < deadline) {
    await new Promise(r => setTimeout(r, 1000));
    const fresh = await fetch(`/api/variants/${variantId}`).then(x => x.json());
    if (fresh.comfy_job_id && !comfyJobId) {
      comfyJobId = fresh.comfy_job_id;
      openProgressSocket(comfyJobId, variantId);
    }
    if (fresh.png_url) { insertTile(fresh); return; }
    if (fresh.status === "failed") { insertTile(fresh); return; }
  }
}

function openProgressSocket(jobId, variantId) {
  try {
    const ws = new WebSocket(
      `${location.protocol === "https:" ? "wss:" : "ws:"}//${location.host}/api/comfy/progress/${jobId}`
    );
    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        if (msg.type === "done" && msg.png_url) {
          fetch(`/api/variants/${variantId}`).then(r => r.json()).then(insertTile);
        }
      } catch (_) { /* ignore */ }
    };
  } catch (_) { /* WS not available — polling keeps it alive */ }
}

function wireGenerate() {
  const btn = document.getElementById("btn-generate");
  btn.addEventListener("click", submitGenerate);
}

loadTree();
wireFilter();
wireGenerate();
