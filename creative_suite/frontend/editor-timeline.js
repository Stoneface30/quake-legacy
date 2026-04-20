// editor-timeline.js — renders the V1 body track as proportional clip
// blocks, handles drag-reorder, selection, and REMOVE toggle inline.

const PX_PER_SECOND = 24; // tweak for density

export function renderTimeline({ stripEl, state, onSelect, onReorder, onToggleRemoved }) {
  stripEl.replaceChildren();
  const clips = state?.clips ?? [];
  clips.forEach((clip, idx) => {
    const w = Math.max(20, (clip.out_s - clip.in_s) * PX_PER_SECOND);
    const block = document.createElement("div");
    block.className = "tl-clip";
    block.dataset.idx = String(idx);
    block.dataset.tier = clip.tier ?? "?";
    block.dataset.removed = clip.removed ? "1" : "0";
    block.style.width = `${w}px`;
    block.draggable = true;
    block.title = `${clip.chunk}\n${clip.tier} · ${clip.section_role ?? "—"} · ${clip.duration?.toFixed?.(2) ?? "?"}s`;

    const name = document.createElement("div");
    name.className = "tl-name";
    name.textContent = clip.chunk.replace(/\.mp4$/, "");

    const meta = document.createElement("div");
    meta.className = "tl-meta";
    const dur = document.createElement("span");
    dur.textContent = `${(clip.out_s - clip.in_s).toFixed(1)}s`;
    meta.append(dur);
    if (clip.slow != null) {
      const s = document.createElement("span");
      s.className = "tl-slow";
      s.textContent = `${clip.slow}×`;
      meta.append(s);
    }
    if (clip.section_role) {
      const r = document.createElement("span");
      r.className = "tl-sect";
      r.textContent = clip.section_role;
      meta.append(r);
    }

    block.append(name, meta);

    block.addEventListener("click", (ev) => {
      if (ev.shiftKey) {
        onToggleRemoved?.(idx);
      } else {
        onSelect?.(idx);
      }
    });

    // Drag-reorder (HTML5)
    block.addEventListener("dragstart", (ev) => {
      ev.dataTransfer.setData("text/plain", `clip:${idx}`);
      block.classList.add("dragging");
    });
    block.addEventListener("dragend", () => block.classList.remove("dragging"));
    block.addEventListener("dragover", (ev) => {
      ev.preventDefault();
      block.classList.add("drop-target");
    });
    block.addEventListener("dragleave", () => block.classList.remove("drop-target"));
    block.addEventListener("drop", (ev) => {
      ev.preventDefault();
      block.classList.remove("drop-target");
      const data = ev.dataTransfer.getData("text/plain");
      if (!data.startsWith("clip:")) return;
      const from = parseInt(data.slice(5), 10);
      const to = idx;
      if (from !== to) onReorder?.(from, to);
    });

    stripEl.append(block);
  });
}

export function markSelected(stripEl, idx) {
  for (const el of stripEl.querySelectorAll(".tl-clip")) {
    el.dataset.selected = el.dataset.idx === String(idx) ? "1" : "0";
  }
}

export function reorderClips(clips, from, to) {
  const next = clips.slice();
  const [item] = next.splice(from, 1);
  next.splice(to, 0, item);
  return next;
}

export function bodyDurationS(clips) {
  let t = 0;
  for (const c of clips) if (!c.removed) t += Math.max(0, c.out_s - c.in_s);
  return t;
}
