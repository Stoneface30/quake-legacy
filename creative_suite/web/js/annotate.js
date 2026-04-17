// annotate.js — Track 2 client.
// DOM-safety rule: every user/DB string goes through textContent or value.
// Never set innerHTML with a string that came from the network.

const qs = (sel, root = document) => root.querySelector(sel);

const partSelect = qs("#part-select");
const player = qs("#player");
const form = qs("#ann-form");
const tbody = qs("#ann-table tbody");
const fTime = qs("#f-time");
const fDesc = qs("#f-desc");
const fAvi = qs("#f-avi");
const fDream = qs("#f-dream");
const fTags = qs("#f-tags");
const cancelBtn = qs("#cancel-btn");

let editingId = null;

// --- data loaders --------------------------------------------------------

async function loadParts() {
  const r = await fetch("/api/parts");
  const parts = await r.json();
  // Clear existing children safely.
  while (partSelect.firstChild) partSelect.removeChild(partSelect.firstChild);
  for (const p of parts) {
    const opt = document.createElement("option");
    opt.value = String(p.part);                     // safe: numeric
    opt.textContent = `Part ${p.part}` +            // safe: numeric
      (p.has_manifest ? "" : " (no manifest)");
    partSelect.append(opt);
  }
  if (parts.length > 0) {
    partSelect.value = String(parts[0].part);
    onPartChange();
  }
}

function onPartChange() {
  const part = Number(partSelect.value);
  player.src = `/media/Part${part}.mp4`;            // safe: numeric
  loadAnnotations(part);
}

async function loadAnnotations(part) {
  const r = await fetch(`/api/annotations?part=${part}`);
  const rows = await r.json();
  while (tbody.firstChild) tbody.removeChild(tbody.firstChild);
  for (const a of rows) renderRow(a);
}

// --- row rendering (safe DOM only) --------------------------------------

function td(text) {
  const el = document.createElement("td");
  el.textContent = text == null ? "" : String(text);
  return el;
}

function renderRow(a) {
  const tr = document.createElement("tr");
  tr.dataset.id = a.id;                              // safe: server-generated id
  tr.append(
    td(a.mp4_time.toFixed(2)),
    td(a.description),
    td(a.avi_effect),
    td(a.dream_effect),
    td(Array.isArray(a.tags) ? a.tags.join(", ") : ""),
    td(a.clip_filename ? `#${a.clip_index} ${a.clip_filename}` : "—"),
  );
  const actions = document.createElement("td");
  const editBtn = document.createElement("button");
  editBtn.type = "button";
  editBtn.textContent = "edit";
  editBtn.addEventListener("click", (ev) => {
    ev.stopPropagation();
    beginEdit(a);
  });
  const delBtn = document.createElement("button");
  delBtn.type = "button";
  delBtn.textContent = "del";
  delBtn.addEventListener("click", async (ev) => {
    ev.stopPropagation();
    if (!confirm("Delete this annotation?")) return;
    await fetch(`/api/annotations/${encodeURIComponent(a.id)}`, {
      method: "DELETE",
    });
    loadAnnotations(Number(partSelect.value));
  });
  actions.append(editBtn, delBtn);
  tr.append(actions);
  tr.addEventListener("click", () => { player.currentTime = a.mp4_time; });
  tbody.append(tr);
}

// --- form actions -------------------------------------------------------

function beginEdit(a) {
  editingId = a.id;
  fTime.value = a.mp4_time;
  fDesc.value = a.description || "";
  fAvi.value = a.avi_effect || "";
  fDream.value = a.dream_effect || "";
  fTags.value = Array.isArray(a.tags) ? a.tags.join(", ") : "";
}

function resetForm() {
  editingId = null;
  form.reset();
}

cancelBtn.addEventListener("click", resetForm);

form.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const part = Number(partSelect.value);
  const body = {
    part,
    mp4_time: Number(fTime.value),
    description: fDesc.value,
    avi_effect: fAvi.value || null,
    dream_effect: fDream.value || null,
    tags: fTags.value
      .split(",").map((s) => s.trim()).filter((s) => s.length > 0),
  };
  if (editingId) {
    await fetch(`/api/annotations/${encodeURIComponent(editingId)}`, {
      method: "PATCH",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
    });
  } else {
    await fetch("/api/annotations", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
    });
  }
  resetForm();
  loadAnnotations(part);
});

// --- keyboard -----------------------------------------------------------

function markMoment() {
  fTime.value = player.currentTime.toFixed(2);
  fDesc.focus();
}

document.addEventListener("keydown", (ev) => {
  if (ev.target instanceof HTMLInputElement ||
      ev.target instanceof HTMLTextAreaElement) {
    if (ev.key === "Escape") ev.target.blur();
    return;
  }
  if (ev.key === " ") {
    ev.preventDefault();
    if (player.paused) player.play(); else player.pause();
  } else if (ev.key === "ArrowLeft") {
    player.currentTime -= ev.shiftKey ? 0.1 : 1.0;
  } else if (ev.key === "ArrowRight") {
    player.currentTime += ev.shiftKey ? 0.1 : 1.0;
  } else if (ev.key === "m" || ev.key === "M") {
    markMoment();
  }
});

partSelect.addEventListener("change", onPartChange);

loadParts();
