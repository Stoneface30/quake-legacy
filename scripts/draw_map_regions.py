"""Draw the learned regions of a map, one panel per height layer.

WHY A PICTURE. The regions are derived from millions of recorded positions
and named REGION_01..N, which is honest but unreadable. The user has played
these maps for ten years; a top-down plate per floor lets them check the
model against the thing they actually remember, and say "REGION_04 is the
RA room" -- which is a mapping we are not allowed to invent, and are very
happy to be told.

Cells are drawn at their real footprint, shaded by how busy they are, and
each region is labelled at its centre. No player names, no server text and
no demo filenames appear anywhere in the output.

    python scripts/draw_map_regions.py [map ...]
"""
from __future__ import annotations

import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                # noqa: E402
from matplotlib.patches import Rectangle                       # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from engine.pantheon import map_context as mc                  # noqa: E402
from engine.pantheon import map_geography as mg                # noqa: E402

OUT_DIR = REPO_ROOT / "docs" / "visual-record" / date.today().isoformat()

# PANTHEON is grey and silver; the regions want to read as a technical plate
# rather than a heat map, so colour distinguishes regions and value carries
# density.
PALETTE = ["#8ab4f8", "#e8c46a", "#7fd1ae", "#e08f8f", "#b79cd8", "#7fc4d1",
           "#d1a17f", "#a8c98a", "#d68fb8", "#9aa7d6", "#c9b98a", "#8fd6c4"]


def draw(map_name: str) -> Path | None:
    idx = mg.load_index(map_name)
    if idx is None:
        print(f"  {map_name}: no geography")
        return None

    with mg.conn() as c:
        cells = [(r["layer"], r["cx"], r["cy"], r["region_id"])
                 for r in c.execute(
                     "SELECT layer, cx, cy, region_id FROM "
                     "map_region_cells_v1 WHERE map=?", (map_name,))]
        combat = {r["region_id"]: (r["deaths"], r["shots"]) for r in c.execute(
            "SELECT region_id, deaths, shots FROM map_region_combat_v1 "
            "WHERE map=?", (map_name,))}

    by_layer: dict[int, list[tuple[int, int, str]]] = defaultdict(list)
    for lay, cx, cy, rid in cells:
        by_layer[lay].append((cx, cy, rid))

    order = sorted(idx.regions)
    colour = {rid: PALETTE[i % len(PALETTE)] for i, rid in enumerate(order)}

    layers = sorted(by_layer)
    fig, axes = plt.subplots(1, len(layers), squeeze=False,
                             figsize=(5.2 * len(layers), 5.6))
    all_x = [cx for _l, cx, _cy, _r in cells]
    all_y = [cy for _l, _cx, cy, _r in cells]
    xlim = (min(all_x) - 1, max(all_x) + 2)
    ylim = (min(all_y) - 1, max(all_y) + 2)

    for ax, lay in zip(axes[0], layers):
        word = mc.layer_word(idx, lay)
        zs = [la for la in idx.layers if la.layer == lay]
        z = zs[0] if zs else None
        for cx, cy, rid in by_layer[lay]:
            ax.add_patch(Rectangle((cx, cy), 1, 1, facecolor=colour[rid],
                                   edgecolor="#2a2a30", linewidth=0.4))
        seen: set[str] = set()
        for cx, cy, rid in sorted(by_layer[lay]):
            if rid in seen:
                continue
            seen.add(rid)
            own = [(c, y) for c, y, r in by_layer[lay] if r == rid]
            mx = sum(c for c, _ in own) / len(own)
            my = sum(y for _, y in own) / len(own)
            # ANCHOR THE LABEL ON A REAL CELL. A C-shaped region -- the
            # upper walkway on campgrounds is one -- has its centroid in
            # the hole in the middle, where dark text lands on the dark
            # background and the region silently loses its number.
            lx, ly = min(own, key=lambda c: (c[0] - mx) ** 2
                                            + (c[1] - my) ** 2)
            ax.text(lx + 0.5, ly + 0.5, rid.replace("REGION_", ""),
                    ha="center", va="center", fontsize=9,
                    color="#15151a", weight="bold")
        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)
        ax.set_aspect("equal")
        ax.set_facecolor("#15151a")
        title = f"{word.title()} — layer {lay}"
        if z is not None:
            title += f"  (z {z.z_lo:.0f}..{z.z_hi:.0f})"
        ax.set_title(title, fontsize=10, color="#d8d8de")
        ax.tick_params(colors="#55555e", labelsize=7)

    deaths = sum(v[0] for v in combat.values())
    fig.suptitle(
        f"{map_name} — {len(idx.regions)} regions, {len(layers)} height "
        f"layers, {deaths:,} deaths observed\n"
        f"learned from recorded play; region ids are machine labels",
        color="#d8d8de", fontsize=11)
    fig.patch.set_facecolor("#0e0e12")
    fig.tight_layout()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"map_regions_{map_name}.png"
    fig.savefig(out, dpi=130, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  {map_name}: {len(idx.regions)} regions -> {out.name}")
    return out


if __name__ == "__main__":
    names = sys.argv[1:] or mg.dominant_maps()
    print(f"drawing {len(names)} maps into {OUT_DIR}")
    for n in names:
        draw(n)
