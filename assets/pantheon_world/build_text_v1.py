"""Build the word PANTHEON as real 3-D geometry, in Blender, headlessly.

    "<blender>" --background --python assets/pantheon_world/build_text_v1.py -- \
        --text PANTHEON --font BlackOpsOne-Regular.ttf --height 96 \
        --out assets/pantheon_world/generated/pantheon_text.obj

The point is that the title exists INSIDE the world: it is a mesh the Quake
renderer lights, occludes and reflects the room onto, not a PNG composited
over a frame afterwards. That is what makes a title shot a shot rather than a
lower third.

Units are Quake units. `--height` is the cap height of the letters, so the
word's scale is stated in the same currency as everything else in the temple
(a player is 56 tall). The word is built centred on its own origin with the
front face at y = 0, so placing it is "put the middle of the word here" and
nothing has to be measured afterwards.

UVs are a planar projection of the FRONT face across the whole word, so a
material reads once across PANTHEON rather than repeating per letter -- the
same lesson the door taught: a hero asset must not tile.
"""
import argparse
import sys
from pathlib import Path

import bmesh
import bpy

FONTS = Path("creative_suite/engine/assets/fonts")


def build(text: str, font_file: Path, cap_height: float, depth: float,
          bevel: float, spacing: float, max_width: float = 0.0):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    cur = bpy.data.curves.new(type="FONT", name="pantheon_text")
    cur.body = text
    cur.align_x = "CENTER"
    cur.align_y = "CENTER"
    cur.space_character = spacing
    cur.extrude = 0.5                      # scaled to `depth` below
    cur.bevel_depth = bevel
    cur.bevel_resolution = 2
    if font_file.exists():
        cur.font = bpy.data.fonts.load(str(font_file.absolute()))
    ob = bpy.data.objects.new("pantheon_text", cur)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)

    bpy.ops.object.convert(target="MESH")
    ob = bpy.context.object

    # Stand it up FIRST, then measure. Blender lays text in XY with the cap
    # height along +Y and the extrusion along +Z; Quake wants Z up and the
    # face looking along -Y. Measuring before the rotation is how the first
    # build scaled the extrusion to the cap height and squashed the letters.
    ob.rotation_euler = (1.5707963, 0.0, 0.0)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

    dims = ob.dimensions                       # x = width, y = depth, z = height
    if dims.z > 0 and dims.y > 0:
        s = cap_height / dims.z
        # A word is placed in a ROOM, and a room has a width. When max_width is
        # given the cap height yields to it, so the same script fits the same
        # word to whatever space the shot actually has -- eight letters in a
        # heavy face are 734 units at 96 cap height, and that is wider than
        # most Quake halls.
        if max_width and dims.x * s > max_width:
            s = max_width / dims.x
        ob.scale = (s, depth / dims.y, s)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    # centre on origin, front face at y = 0
    me = ob.data
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    zs = [v.co.z for v in me.vertices]
    dx = -(min(xs) + max(xs)) / 2
    dy = -max(ys)
    dz = -min(zs)
    for v in me.vertices:
        v.co.x += dx
        v.co.y += dy
        v.co.z += dz

    # one planar projection across the whole word, from the front
    bm = bmesh.new()
    bm.from_mesh(me)
    uv = bm.loops.layers.uv.verify()
    xs = [v.co.x for v in bm.verts]
    zs = [v.co.z for v in bm.verts]
    w = max(xs) - min(xs) or 1.0
    h = max(zs) - min(zs) or 1.0
    for f in bm.faces:
        for loop in f.loops:
            loop[uv].uv = ((loop.vert.co.x - min(xs)) / w,
                           (loop.vert.co.z - min(zs)) / h)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    return ob


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--text", default="PANTHEON")
    ap.add_argument("--font", default="BlackOpsOne-Regular.ttf")
    ap.add_argument("--height", type=float, default=96.0, help="cap height, units")
    ap.add_argument("--depth", type=float, default=18.0)
    ap.add_argument("--bevel", type=float, default=0.02)
    ap.add_argument("--spacing", type=float, default=1.0)
    ap.add_argument("--max-width", type=float, default=0.0,
                    help="fit the word into this width, units")
    ap.add_argument("--out", default="assets/pantheon_world/generated/pantheon_text.obj")
    a = ap.parse_args(argv)

    ob = build(a.text, FONTS / a.font, a.height, a.depth, a.bevel, a.spacing,
               a.max_width)
    out = Path(a.out).absolute()
    out.parent.mkdir(parents=True, exist_ok=True)
    mat = bpy.data.materials.new("textures/pantheon/title")
    ob.data.materials.append(mat)
    bpy.ops.wm.obj_export(filepath=str(out), export_selected_objects=False,
                          export_uv=True, export_normals=True,
                          export_materials=True, export_triangulated_mesh=True,
                          forward_axis="Y", up_axis="Z", global_scale=1.0)
    d = ob.dimensions
    print(f"PANTHEON_TEXT verts={len(ob.data.vertices)} tris={len(ob.data.polygons)} "
          f"size=({d.x:.1f},{d.y:.1f},{d.z:.1f}) font={a.font} out={out}")


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    main(argv)
