"""A Roman PANTHEON column, parametric, built in Blender headlessly.

    "<blender>" --background --python assets/pantheon_world/build_pillar_v1.py -- \
        --height 256 --out assets/pantheon_world/generated/pantheon_pillar.obj

Quake's own architecture is industrial: square metal supports and riveted
plate. A Pantheon is not that. This is the piece that changes the room --
a fluted shaft with entasis, a moulded base and a capital -- so the temple
reads as a temple rather than as a Quake map with a logo in it.

Everything is in Quake units and proportioned off the real thing rather than
off taste. The Pantheon's portico columns are ~11.8 m tall with a ~1.48 m
lower diameter, a ratio near 8:1, and the shafts are monolithic and
UNFLUTED. Fluting is offered because at Quake's texture resolution flutes are
what read as "column" at 500 units, and it is a deliberate departure recorded
here rather than a mistake.

  * `--flutes 20` is the canonical Doric/Corinthian count; 0 gives the
    Pantheon's own smooth monolith.
  * `--entasis` is the swelling that keeps a tall shaft from looking pinched:
    the radius follows a shallow sine, widest around a third of the way up.
  * The column stands on z = 0 with its axis on the origin, so a colonnade is
    a list of x positions and nothing has to be measured afterwards.
"""
import argparse
import math
import sys
from pathlib import Path

import bmesh
import bpy

MAT_STONE = "textures/pantheon/pillar"
MAT_ACCENT = "textures/pantheon/accent"


def ring(bm, z, radius, segments, flutes, flute_depth):
    """One horizontal loop of the shaft, scalloped by the flute count."""
    verts = []
    for i in range(segments):
        a = 2 * math.pi * i / segments
        r = radius
        if flutes:
            # a scallop per flute: cosine dipping into the shaft
            r -= flute_depth * (0.5 - 0.5 * math.cos(a * flutes))
        verts.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
    return verts


def bridge(bm, lower, upper):
    n = len(lower)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((lower[i], lower[j], upper[j], upper[i]))


def cap(bm, loop, z, up=True):
    """Close a loop with a fan to its centre."""
    c = bm.verts.new((0.0, 0.0, z))
    n = len(loop)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((loop[i], loop[j], c) if up else (loop[j], loop[i], c))


def drum(bm, z0, z1, r0, r1, segments):
    """A plain tapered drum -- base plinth, torus, echinus, abacus."""
    lo = ring(bm, z0, r0, segments, 0, 0.0)
    hi = ring(bm, z1, r1, segments, 0, 0.0)
    bridge(bm, lo, hi)
    return lo, hi


def build(height, flutes, entasis, segments, shaft_ratio):
    bpy.ops.wm.read_factory_settings(use_empty=True)

    base_h = height * 0.075
    cap_h = height * 0.105
    shaft_h = height - base_h - cap_h
    r_shaft = height / shaft_ratio / 2.0          # 8:1 height:diameter by default
    r_base = r_shaft * 1.34
    r_cap = r_shaft * 1.42
    flute_depth = r_shaft * 0.10

    bm = bmesh.new()

    # base: square plinth read as a wide drum, then a torus moulding
    lo, hi = drum(bm, 0.0, base_h * 0.55, r_base, r_base, segments)
    cap(bm, lo, 0.0, up=False)
    lo2, hi2 = drum(bm, base_h * 0.55, base_h, r_base, r_shaft * 1.06, segments)

    # shaft, in rings, with entasis: widest about a third up
    rings = []
    steps = 14
    for i in range(steps + 1):
        t = i / steps
        swell = math.sin(math.pi * min(1.0, t * 0.85 + 0.08)) * entasis
        r = r_shaft * (1.0 + swell) * (1.0 - 0.10 * t)     # slight taper to the top
        rings.append(ring(bm, base_h + shaft_h * t, r, segments, flutes, flute_depth))
    for a, b in zip(rings, rings[1:]):
        bridge(bm, a, b)

    # capital: echinus flaring out, then the square abacus as a wide drum
    z = base_h + shaft_h
    e0, e1 = drum(bm, z, z + cap_h * 0.55, r_shaft * 0.9, r_cap, segments)
    a0, a1 = drum(bm, z + cap_h * 0.55, z + cap_h, r_cap, r_cap * 1.03, segments)
    cap(bm, a1, z + cap_h, up=True)

    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])

    me = bpy.data.meshes.new("pantheon_pillar")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("pantheon_pillar", me)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)

    # UVs: cylindrical round the shaft, so stone runs vertically and does not
    # smear round the flutes. One tile per 128 units of height.
    bm = bmesh.new()
    bm.from_mesh(me)
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        for loop in f.loops:
            v = loop.vert.co
            ang = math.atan2(v.y, v.x)
            bm.faces.ensure_lookup_table()
            loop[uv].uv = ((ang / (2 * math.pi)) % 1.0 * 4.0, v.z / 128.0)
    bm.to_mesh(me)
    bm.free()
    return ob


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--height", type=float, default=256.0)
    ap.add_argument("--flutes", type=int, default=20)
    ap.add_argument("--entasis", type=float, default=0.035)
    ap.add_argument("--segments", type=int, default=64)
    ap.add_argument("--shaft-ratio", type=float, default=8.0,
                    help="height : lower diameter; the Pantheon's own is ~8")
    ap.add_argument("--out", default="assets/pantheon_world/generated/pantheon_pillar.obj")
    a = ap.parse_args(argv)

    ob = build(a.height, a.flutes, a.entasis, a.segments, a.shaft_ratio)
    ob.data.materials.append(bpy.data.materials.new(MAT_STONE))
    out = Path(a.out).absolute()
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.obj_export(filepath=str(out), export_selected_objects=False,
                          export_uv=True, export_normals=True,
                          export_materials=True, export_triangulated_mesh=True,
                          forward_axis="Y", up_axis="Z", global_scale=1.0)
    d = ob.dimensions
    print(f"PANTHEON_PILLAR verts={len(ob.data.vertices)} tris={len(ob.data.polygons)} "
          f"size=({d.x:.1f},{d.y:.1f},{d.z:.1f}) flutes={a.flutes} out={out}")


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    main(argv)
