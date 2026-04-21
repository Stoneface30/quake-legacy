// editor-inspector.js — right-pane property editor for the selected clip.
// All DOM via createElement / textContent to keep the XSS surface at zero
// (matches panel-flow.js style in the existing cinema suite).

export function renderInspector({ hostEl, clip, idx, onPatch }) {
  hostEl.replaceChildren();
  if (!clip) {
    const p = document.createElement("p");
    p.className = "hint";
    p.textContent = "Click a clip in the timeline to edit.";
    hostEl.append(p);
    return;
  }

  const summary = document.createElement("div");
  summary.className = "ins-summary";
  const name = document.createElement("strong");
  name.textContent = clip.chunk;
  const meta = document.createElement("span");
  meta.style.color = "var(--muted)";
  const durStr = clip.duration != null ? clip.duration.toFixed(2) : "?";
  meta.textContent = `${clip.tier} · ${clip.section_role ?? "—"} · ${durStr}s source`;
  summary.append(name, document.createElement("br"), meta);
  hostEl.append(summary);

  const row = (label, node) => {
    const r = document.createElement("div");
    r.className = "ins-row";
    const l = document.createElement("label");
    l.textContent = label;
    r.append(l, node);
    return r;
  };

  const num = (key, value, step = 0.01) => {
    const inp = document.createElement("input");
    inp.type = "number";
    inp.step = String(step);
    inp.value = value ?? "";
    inp.addEventListener("change", () => {
      const v = inp.value === "" ? null : parseFloat(inp.value);
      onPatch?.([{ op: "replace", path: `/clips/${idx}/${key}`, value: v }]);
    });
    return inp;
  };

  hostEl.append(
    row("in (s)", num("in_s", clip.in_s, 0.05)),
    row("out (s)", num("out_s", clip.out_s, 0.05)),
    row("slow ×", num("slow", clip.slow, 0.05)),
    row("window (s)", num("slow_window_s", clip.slow_window_s, 0.1)),
  );

  // Removed toggle
  const toggleBtn = document.createElement("button");
  toggleBtn.className = "btn";
  toggleBtn.textContent = clip.removed ? "↻ RESTORE" : "× REMOVE from render";
  toggleBtn.addEventListener("click", () => {
    onPatch?.([{
      op: "replace",
      path: `/clips/${idx}/removed`,
      value: !clip.removed,
    }]);
  });

  const actions = document.createElement("div");
  actions.className = "ins-actions";
  actions.append(toggleBtn);
  hostEl.append(actions);

  // Notes
  const notesRow = document.createElement("label");
  notesRow.className = "ins-row";
  notesRow.style.gridTemplateColumns = "1fr";
  const notesLbl = document.createElement("span");
  notesLbl.textContent = "NOTES";
  notesLbl.style.cssText = "color:var(--muted);font-size:10px;letter-spacing:.05em;";
  const notesInp = document.createElement("textarea");
  notesInp.rows = 2;
  notesInp.style.cssText = "background:var(--bg-2);color:var(--text);border:1px solid var(--border);padding:4px;font:inherit;";
  notesInp.value = clip.notes ?? "";
  notesInp.addEventListener("blur", () => {
    if ((clip.notes ?? "") === notesInp.value) return;
    onPatch?.([{ op: "replace", path: `/clips/${idx}/notes`, value: notesInp.value }]);
  });
  notesRow.append(notesLbl, notesInp);
  hostEl.append(notesRow);
}
