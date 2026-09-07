"""Turn a Blender OBJ export into a Quake MD3 the native renderer can draw.

    python scripts/obj_to_md3.py assets/pantheon_world/generated/leaf.obj \
        --out <gamedir>/models/pantheon/door_leaf_v1.md3

The seam between "authored geometry" and "game asset". It reports what it
wrote -- surfaces, shaders, vertex and triangle counts, bounds in Quake units
-- because a model that silently comes out 8x too big is a model that renders
once and wastes a review pass.
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.pantheon.md3_writer import (read_md3, read_obj,  # noqa: E402
                                        split_by_vertex_limit, write_md3)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("obj", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--name", default="")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--mirror-x", action="store_true",
                    help="mirror across X for the opposite leaf of a pair "
                         "(winding and normals flip with it, or the leaf "
                         "renders inside-out and lit from behind)")
    a = ap.parse_args()

    surfaces = read_obj(a.obj, scale=a.scale)
    if not surfaces:
        print("no geometry in", a.obj)
        return 1
    if a.mirror_x:
        for sf in surfaces:
            sf.verts = [(-x, y, z) for (x, y, z) in sf.verts]
            sf.normals = [(-x, y, z) for (x, y, z) in sf.normals]
            sf.tris = [(c, b, aa) for (aa, b, c) in sf.tris]
    # MD3 caps a surface at 4096 vertices; a bevelled word is far past that
    surfaces = [part for s in surfaces for part in split_by_vertex_limit(s)]
    out = write_md3(a.out, surfaces, name=a.name or a.out.stem)

    back = read_md3(out)
    f = back["frames"][0]
    size = tuple(round(f["maxs"][i] - f["mins"][i], 1) for i in range(3))
    print(f"{out}  {out.stat().st_size} bytes")
    print(f"  surfaces {len(back['surfaces'])}  "
          f"verts {sum(len(s['verts']) for s in back['surfaces'])}  "
          f"tris {sum(len(s['tris']) for s in back['surfaces'])}")
    print(f"  bounds   {tuple(round(v, 1) for v in f['mins'])} .. "
          f"{tuple(round(v, 1) for v in f['maxs'])}   size {size} Quake units")
    print(f"  a player is 56 tall: this is {size[2] / 56:.1f} players high")
    for s in back["surfaces"]:
        print(f"  shader   {s['shader'] or '(EMPTY -- a prop needs one)'}"
              f"   [{s['name']}] {len(s['tris'])} tris")
    return 0


if __name__ == "__main__":                      # pragma: no cover - CLI
    raise SystemExit(main())
