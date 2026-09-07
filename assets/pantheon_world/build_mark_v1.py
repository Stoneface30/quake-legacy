"""The PANTHEON mark as geometry, built from the mark itself.

    "<blender>" --background --python assets/pantheon_world/build_mark_v1.py -- \
        --height 192 --out assets/pantheon_world/generated/pantheon_mark.obj

Not a redesign and not a trace: every coordinate below is read straight out of
`docs/brand/pantheon-mark.svg`, which is a 120x120 viewBox containing a
pediment, an entablature, five columns, three stylobate steps and an oculus.
The SVG is the identity; this file only gives it thickness.

Two conversions, both stated rather than assumed:

  * SVG y runs DOWN, Quake z runs UP, so every y becomes (120 - y).
  * SVG strokes are 1 to 2.5 units wide on a 120 grid. At any sane world size
    that is a wire, so `--weight` multiplies stroke width. The mark stays the
    same drawing; its members just become masonry.

The mark is built centred on x, standing on z = 0, front face at y = 0, so it
places exactly like the title does.
"""
import argparse
import math
import sys
from pathlib import Path

import bmesh
import bpy

VIEW = 120.0

# straight from the SVG: (x1, y1, x2, y2, stroke)
BARS = [
    (8, 46, 112, 46, 2.0),        # entablature
    (22, 48, 22, 90, 2.0),        # columns
    (37, 48, 37, 90, 2.0),
    (60, 48, 60, 90, 2.0),
    (83, 48, 83, 90, 2.0),
    (98, 48, 98, 90, 2.0),
    (10, 90, 110, 90, 2.0),       # stylobate, three steps
    (6, 96, 114, 96, 1.5),
    (4, 102, 116, 102, 1.0),
]
PEDIMENT = [(12, 46), (60, 8), (108, 46)]     # polygon, stroke 2.5
PEDIMENT_STROKE = 2.5
OCULUS = (60, 26, 7.0, 1.5, 3.0)              # cx, cy, r, stroke, filled r


def bar(bm, x1, z1, x2, z2, w, depth):
    """A stroke, as a box: the segment fattened by w and given depth."""
    dx, dz = x2 - x1, z2 - z1
    ln = math.hypot(dx, dz)
    if ln < 1e-6:
        return
    # extend by half a width at each end so joints close
    ex, ez = dx / ln * w / 2, dz / ln * w / 2
    px, pz = -dz / ln * w / 2, dx / ln * w / 2
    a = (x1 - ex, z1 - ez)
    b = (x2 + ex, z2 + ez)
    quad = [(a[0] + px, a[1] + pz), (b[0] + px, b[1] + pz),
            (b[0] - px, b[1] - pz), (a[0] - px, a[1] - pz)]
    front = [bm.verts.new((x, 0.0, z)) for x, z in quad]
    back = [bm.verts.new((x, -depth, z)) for x, z in quad]
    bm.faces.new(front)
    bm.faces.new(list(reversed(back)))
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((front[i], front[j], back[j], back[i]))


def ring(bm, cx, cz, radius, stroke, depth, segments=48):
    """The oculus: an annulus with depth, built as a strip of quads."""
    ro, ri = radius + stroke / 2, radius - stroke / 2
    for i in range(segments):
        a0 = 2 * math.pi * i / segments
        a1 = 2 * math.pi * (i + 1) / segments
        pts = [(cx + r * math.cos(a), cz + r * math.sin(a))
               for r, a in ((ro, a0), (ro, a1), (ri, a1), (ri, a0))]
        f = [bm.verts.new((x, 0.0, z)) for x, z in pts]
        b = [bm.verts.new((x, -depth, z)) for x, z in pts]
        bm.faces.new(f)
        bm.faces.new(list(reversed(b)))
        for k in range(4):
            m = (k + 1) % 4
            bm.faces.new((f[k], f[m], b[m], b[k]))


def disc(bm, cx, cz, radius, depth, segments=32):
    rim = [(cx + radius * math.cos(2 * math.pi * i / segments),
            cz + radius * math.sin(2 * math.pi * i / segments))
           for i in range(segments)]
    f = [bm.verts.new((x, 0.0, z)) for x, z in rim]
    b = [bm.verts.new((x, -depth, z)) for x, z in rim]
    bm.faces.new(f)
    bm.faces.new(list(reversed(b)))
    for i in range(segments):
        j = (i + 1) % segments
        bm.faces.new((f[i], f[j], b[j], b[i]))


def build(height: float, depth: float, weight: float):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scale = height / VIEW
    d = depth / scale                       # depth in SVG units, scaled later
    bm = bmesh.new()
    flip = lambda y: VIEW - y               # noqa: E731  SVG y is down

    for x1, y1, x2, y2, w in BARS:
        bar(bm, x1, flip(y1), x2, flip(y2), w * weight, d)
    for i in range(len(PEDIMENT) - 1):
        (x1, y1), (x2, y2) = PEDIMENT[i], PEDIMENT[i + 1]
        bar(bm, x1, flip(y1), x2, flip(y2), PEDIMENT_STROKE * weight, d)
    cx, cy, r, stroke, fill = OCULUS
    ring(bm, cx, flip(cy), r, stroke * weight, d)
    disc(bm, cx, flip(cy), fill, d * 0.6)

    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])

    me = bpy.data.meshes.new("pantheon_mark")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("pantheon_mark", me)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)

    # to Quake units, centred on x, standing on z = 0
    for v in me.vertices:
        v.co.x = (v.co.x - VIEW / 2) * scale
        v.co.y = v.co.y * scale
        v.co.z = v.co.z * scale
    lo = min(v.co.z for v in me.vertices)
    for v in me.vertices:
        v.co.z -= lo

    # planar UV across the whole mark, like the title
    bm = bmesh.new()
    bm.from_mesh(me)
    uv = bm.loops.layers.uv.verify()
    xs = [v.co.x for v in bm.verts]
    zs = [v.co.z for v in bm.verts]
    w = (max(xs) - min(xs)) or 1.0
    h = (max(zs) - min(zs)) or 1.0
    for f in bm.faces:
        for loop in f.loops:
            loop[uv].uv = ((loop.vert.co.x - min(xs)) / w,
                           (loop.vert.co.z - min(zs)) / h)
    bm.to_mesh(me)
    bm.free()
    return ob


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--height", type=float, default=192.0)
    ap.add_argument("--depth", type=float, default=22.0)
    ap.add_argument("--weight", type=float, default=2.6,
                    help="stroke multiplier: the SVG's lines are wires at world scale")
    ap.add_argument("--out", default="assets/pantheon_world/generated/pantheon_mark.obj")
    a = ap.parse_args(argv)

    ob = build(a.height, a.depth, a.weight)
    ob.data.materials.append(bpy.data.materials.new("textures/pantheon/title"))
    out = Path(a.out).absolute()
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.obj_export(filepath=str(out), export_selected_objects=False,
                          export_uv=True, export_normals=True,
                          export_materials=True, export_triangulated_mesh=True,
                          forward_axis="Y", up_axis="Z", global_scale=1.0)
    d = ob.dimensions
    print(f"PANTHEON_MARK verts={len(ob.data.vertices)} tris={len(ob.data.polygons)} "
          f"size=({d.x:.1f},{d.y:.1f},{d.z:.1f}) out={out}")


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    main(argv)
