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
}

function wireFilter() {
  const f = document.getElementById("filter");
  f.addEventListener("input", () => {
    state.filter = f.value.trim();
    renderTree();
  });
}

loadTree();
wireFilter();
