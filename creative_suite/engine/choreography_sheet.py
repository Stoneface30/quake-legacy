"""The planning sheet: a whole song's choreography, lane by lane.

Two views of the same plans. The WHOLE view groups the fifteen lanes into
seven readable bands so a several-minute song fits on one page. The ZOOM view
opens one interval and shows every lane separately, with each element's peak
marked, because milliseconds are the thing being planned.

This draws numbers that already exist. It decides nothing.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from creative_suite.engine import choreography as ch

SHEET_VERSION = "choreography-sheet-v1.0.0"

# Grouping for the whole-song view: related lanes share a band.
BANDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("MUSIC", (ch.LANE_GESTURE,)),
    ("NARRATIVE", (ch.LANE_NARRATIVE,)),
    ("GAMEPLAY", (ch.LANE_GAMEPLAY,)),
    ("CAMERA / TIME", (ch.LANE_CAMERA, ch.LANE_TIME)),
    ("TRANSITION / FX", (ch.LANE_TRANSITION, ch.LANE_FX)),
    ("MODEL / MATERIAL / WORLD", (ch.LANE_MODEL, ch.LANE_MATERIAL,
                                  ch.LANE_WORLD, ch.LANE_ANIMATION)),
    ("INFORMATION / PIP / TEXT / SOUND", (ch.LANE_INFORMATION, ch.LANE_PIP,
                                          ch.LANE_TEXT, ch.LANE_SOUND)),
)

LANE_COLOR = {
    ch.LANE_GAMEPLAY: "#ffd24d", ch.LANE_NARRATIVE: "#9ad0ff",
    ch.LANE_CAMERA: "#7fb3ff", ch.LANE_TIME: "#c792ea",
    ch.LANE_TRANSITION: "#ff8c42", ch.LANE_FX: "#ff6b9d",
    ch.LANE_MODEL: "#7ee787", ch.LANE_MATERIAL: "#56d4c4",
    ch.LANE_WORLD: "#48b0a0", ch.LANE_ANIMATION: "#a5d6a7",
    ch.LANE_INFORMATION: "#e6e6e6", ch.LANE_PIP: "#bdbdbd",
    ch.LANE_TEXT: "#f2c14e", ch.LANE_SOUND: "#8fa1b3",
    ch.LANE_GESTURE: "#ff4d6d",
}
BG, FG, GRID = "#101010", "#e6e6e6", "#2a2a2a"

# Capability shown as line style: what we can actually render reads at a glance.
CAPABILITY_ALPHA = {ch.PROVEN_RUNTIME: 1.0, ch.PROTOTYPE: 0.82,
                    ch.DESIGNABLE: 0.6, ch.REQUIRES_NEW_TECH: 0.38,
                    ch.CREATIVE_SEED: 0.22}


def _rows(plans: Sequence[ch.ChoreographyPlan], zoom: bool
          ) -> tuple[tuple[str, tuple[str, ...]], ...]:
    if zoom:
        used = [l for l in ch.LANES if any(e.lane == l for p in plans for e in p.elements)]
        return tuple((l, (l,)) for l in used)
    return tuple(b for b in BANDS
                 if any(e.lane in b[1] for p in plans for e in p.elements))


def render_sheet(plans: Sequence[ch.ChoreographyPlan], dst: Path | str, *,
                 title: str = "", zoom: bool = False, dpi: int = 120,
                 width: float = 17.0, song_duration_us: int | None = None,
                 subtitle: str = "") -> Path:
    """Draw the plans on one time axis. `zoom` opens every lane separately."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    rows = _rows(plans, zoom)
    start = min((p.start_us for p in plans), default=0)
    end = song_duration_us or max((p.end_us for p in plans), default=1)
    height = max(3.0, 0.62 * len(rows) + 2.2)
    fig, ax = plt.subplots(figsize=(width, height), facecolor=BG)
    ax.set_facecolor(BG)

    for i, (name, lanes) in enumerate(rows):
        y = len(rows) - i - 1
        ax.axhspan(y - 0.42, y + 0.42, color="#161616", zorder=0)
        for p in plans:
            for e in p.elements:
                if e.lane not in lanes:
                    continue
                c = LANE_COLOR.get(e.lane, "#888888")
                a = CAPABILITY_ALPHA[e.capability]
                w = max(e.duration_us, (end - start) // 900)
                ax.add_patch(Rectangle((e.start_us, y - 0.3), w, 0.6,
                                       facecolor=c, edgecolor="none",
                                       alpha=a, zorder=2))
                if e.peak_us is not None:
                    ax.plot([e.peak_us], [y], marker="|", color=FG, ms=11,
                            mew=1.4, zorder=4)
                if zoom:
                    ax.text(e.start_us, y + 0.34, e.action, color=c, fontsize=6.4,
                            va="bottom", zorder=5)
    # Slot boundaries and their musical role. Labels alternate height so two
    # adjacent short slots stay readable instead of overprinting each other.
    for i, p in enumerate(plans):
        ax.axvline(p.start_us, color=GRID, lw=0.8, zorder=1)
        label = f"{p.slot_id.replace('PROOF_', '')}\n{p.musical_role}"
        if p.round_result_required:
            label += f"\nneeds {p.round_result_required}"
        ax.text(p.start_us + (end - start) * 0.003,
                len(rows) - 0.48 + (0.42 if i % 2 else 0.0), label,
                color="#9a9a9a", fontsize=6.0, va="bottom", zorder=6)

    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([n for n, _ in reversed(rows)], color=FG, fontsize=8)
    ax.set_xlim(start, end)
    ax.set_ylim(-0.6, len(rows) + 1.35)
    ax.set_xlabel("edit time (s)", color="#9a9a9a")
    ax.set_xticklabels([f"{t/1e6:.0f}" for t in ax.get_xticks()], color="#9a9a9a")
    ax.tick_params(colors="#9a9a9a", labelsize=8)
    for s in ax.spines.values():
        s.set_color(GRID)

    caps = ", ".join(f"{k} {v}" for k, v in _capability_counts(plans).items() if v)
    fig.suptitle(title or "PANTHEON choreography sheet", color=FG, fontsize=12,
                 x=0.012, y=0.99, ha="left", weight="bold")
    fig.text(0.012, 0.935, subtitle or
             f"{len(plans)} slots · opacity = how renderable an element is today",
             color="#9a9a9a", fontsize=8, ha="left")
    fig.text(0.012, 0.898, caps, color="#7a7a7a", fontsize=7.5, ha="left")
    fig.text(0.012, 0.012, f"PLANNING ONLY · nothing consumed · {SHEET_VERSION}",
             color="#666666", fontsize=7)
    fig.tight_layout(rect=(0, 0.03, 1, 0.90))
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(dst, dpi=dpi, facecolor=BG)
    plt.close(fig)
    return dst


def _capability_counts(plans: Sequence[ch.ChoreographyPlan]) -> dict[str, int]:
    out = {c: 0 for c in ch.CAPABILITIES}
    for p in plans:
        for e in p.elements:
            out[e.capability] += 1
    return out


def sheet_summary(plans: Sequence[ch.ChoreographyPlan]) -> dict[str, Any]:
    """The same conclusions in words, so a test can assert them without
    reading an image."""
    elements = [e for p in plans for e in p.elements]
    lanes = {l: sum(1 for e in elements if e.lane == l) for l in ch.LANES}
    return {"version": SHEET_VERSION, "slots": len(plans),
            "elements": len(elements),
            "lanes_in_play": [l for l, n in lanes.items() if n],
            "elements_per_lane": {l: n for l, n in lanes.items() if n},
            "capability_counts": _capability_counts(plans),
            "gated_slots": [p.slot_id for p in plans if p.round_result_required],
            "bands": [b[0] for b in _rows(plans, zoom=False)]}
