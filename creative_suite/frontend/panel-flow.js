// creative_suite/frontend/panel-flow.js
// Drag-reorder using HTML5 drag API. All DOM via createElement / textContent.

export function renderFlow({ gridEl, flowPlan, onReorder, onClipOverride, onSeamDrag }) {
  gridEl.replaceChildren();
  if (!flowPlan?.clips?.length) {
    const p = document.createElement("p");
    p.className = "hint";
    p.textContent = "No flow plan for this part.";
    gridEl.append(p);
    return;
  }
  flowPlan.clips.forEach((clip, idx) => {
    const card = document.createElement("div");
    card.className = "clip-card";
    if (clip.override?.removed) card.dataset.removed = "1";
    card.draggable = true;
    card.dataset.idx = String(idx);

    const pos = document.createElement("div");
    pos.className = "clip-pos";
    pos.textContent = String(idx + 1);

    const tier = document.createElement("div");
    tier.className = `clip-tier tier-${clip.tier ?? "x"}`;
    tier.textContent = (clip.tier ?? "?").toUpperCase();

    const name = document.createElement("div");
    name.className = "clip-name";
    name.textContent = clip.chunk ?? clip.src ?? `clip ${idx}`;

    const dur = document.createElement("div");
    dur.className = "clip-dur";
    dur.textContent = `${(clip.duration ?? 0).toFixed(2)}s`;

    // Tier 1: REMOVE / KEEP toggle. Stored as clip.override.removed.
    // Wired through onClipOverride(clip, "removed", bool) → PUT /overrides.
    const removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.className = "clip-remove-btn";
    const syncRemoveLabel = () => {
      const r = !!clip.override?.removed;
      removeBtn.textContent = r ? "↻ KEEP" : "× REMOVE";
      removeBtn.title = r ? "Restore this clip to the render" : "Drop from render";
      card.dataset.removed = r ? "1" : "0";
    };
    removeBtn.addEventListener("click", (ev) => {
      ev.stopPropagation();
      const next = !clip.override?.removed;
      clip.override = { ...(clip.override ?? {}), removed: next };
      syncRemoveLabel();
      onClipOverride?.(clip, "removed", next);
    });
    syncRemoveLabel();

    card.append(pos, tier, name, dur, removeBtn);

    // Clip-reorder drag
    card.addEventListener("dragstart", (ev) => {
      ev.dataTransfer.setData("text/plain", `clip:${idx}`);
      card.classList.add("dragging");
    });
    card.addEventListener("dragend", () => card.classList.remove("dragging"));
    card.addEventListener("dragover", (ev) => {
      ev.preventDefault();
      card.classList.add("drop-target");
    });
    card.addEventListener("dragleave", () => card.classList.remove("drop-target"));
    card.addEventListener("drop", (ev) => {
      ev.preventDefault();
      card.classList.remove("drop-target");
      const data = ev.dataTransfer.getData("text/plain");
      if (data.startsWith("clip:")) {
        const from = parseInt(data.slice(5), 10);
        const to = parseInt(card.dataset.idx, 10);
        if (from !== to) onReorder?.(from, to);
      }
    });

    // Hover overrides
    const ctrls = document.createElement("div");
    ctrls.className = "clip-ctrls";
    ctrls.append(
      makeOverrideInput("slow", 0.25, 1.0, 0.1, clip.override?.slow,
                        (v) => onClipOverride?.(clip, "slow", v)),
      makeOverrideInput("head", 0, 5, 0.1, clip.override?.head_trim,
                        (v) => onClipOverride?.(clip, "head_trim", v)),
      makeOverrideInput("tail", 0, 5, 0.1, clip.override?.tail_trim,
                        (v) => onClipOverride?.(clip, "tail_trim", v)),
    );
    card.append(ctrls);

    // Seam handle (except after last clip)
    if (idx < flowPlan.clips.length - 1) {
      const seam = document.createElement("div");
      seam.className = "seam-handle";
      seam.draggable = true;
      seam.dataset.seamIdx = String(idx);
      seam.title = `seam ${idx} — drag onto a downbeat`;
      seam.addEventListener("dragstart", (ev) => {
        ev.stopPropagation();
        ev.dataTransfer.setData("text/plain", `seam:${idx}`);
        onSeamDrag?.(idx);
      });
      card.append(seam);
    }

    // Selection (ctrl/shift click) — for Preview
    card.addEventListener("click", (ev) => {
      if (!(ev.ctrlKey || ev.shiftKey)) return;
      card.dataset.selected = card.dataset.selected === "1" ? "0" : "1";
      card.dispatchEvent(new CustomEvent("clip-select-changed", { bubbles: true }));
    });

    gridEl.append(card);
  });
}

function makeOverrideInput(name, min, max, step, initial, onChange) {
  const lbl = document.createElement("label");
  lbl.textContent = name;
  const input = document.createElement("input");
  input.type = "number";
  input.min = String(min); input.max = String(max); input.step = String(step);
  input.value = initial ?? "";
  input.addEventListener("change", () => {
    const v = input.value === "" ? null : parseFloat(input.value);
    onChange?.(v);
  });
  lbl.append(input);
  return lbl;
}

export function reorderClips(clips, from, to) {
  const next = clips.slice();
  const [item] = next.splice(from, 1);
  next.splice(to, 0, item);
  return next;
}
