// creative_suite/frontend/panel-versions.js
// Phase A: list + mp4 metadata only. REBUILD form + SSE live log wired in Phase B.
// ALL dynamic DOM via createElement + textContent. No innerHTML assignment.

export function renderVersions({ listEl, rows, onLoadA, onLoadB }) {
  listEl.replaceChildren();
  if (!rows || rows.length === 0) {
    const empty = document.createElement("p");
    empty.className = "hint";
    empty.textContent = "No renders yet.";
    listEl.append(empty);
    return;
  }
  for (const r of rows) {
    const row = document.createElement("div");
    row.className = "ver-row";
    row.dataset.id = String(r.id);
    row.dataset.pass = String(r.level_pass ?? "");

    const tag = document.createElement("div");
    tag.className = "ver-tag";
    tag.textContent = r.tag;

    const size = document.createElement("div");
    size.className = "ver-size";
    size.textContent = fmtMp4(r.mp4_path);

    const gate = document.createElement("div");
    gate.className = "ver-gate";
    gate.textContent = r.level_pass === 1 ? "✓" : r.level_pass === 0 ? "✗" : "—";
    gate.title = r.level_delta_lu != null ? `Δ ${r.level_delta_lu.toFixed(1)} LU` : "";

    const drift = document.createElement("div");
    drift.className = "ver-drift";
    drift.textContent = r.max_drift_ms != null ? `${r.max_drift_ms.toFixed(0)}ms` : "—";

    const notes = document.createElement("div");
    notes.className = "ver-notes";
    notes.textContent = r.notes ?? "";

    const actions = document.createElement("div");
    actions.className = "ver-actions";
    const btnA = document.createElement("button");
    btnA.textContent = "Load A";
    btnA.addEventListener("click", () => onLoadA?.(r));
    const btnB = document.createElement("button");
    btnB.textContent = "Load B";
    btnB.addEventListener("click", () => onLoadB?.(r));
    actions.append(btnA, btnB);

    row.append(tag, size, gate, drift, notes, actions);
    listEl.append(row);
  }
}

function fmtMp4(mp4Path) {
  if (!mp4Path) return "—";
  const base = mp4Path.split(/[\\/]/).pop();
  return base.length > 20 ? base.slice(0, 17) + "…" : base;
}
