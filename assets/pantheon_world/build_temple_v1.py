"""The PANTHEON portico: our own building, not a corner of someone's map.

    "<blender>" --background --python assets/pantheon_world/build_temple_v1.py -- \
        --columns 6 --out assets/pantheon_world/generated/pantheon_temple.obj

Every previous frame dressed a Quake room and fought it -- columns through
ceilings, a lockup swallowed by a wall, a light grid that painted our cold
stone olive. This builds the set instead, so the shot is composed rather than
negotiated.

It is rendered with `--no-world` (id's own `RDF_NOWORLDMODEL`, the way Quake's
main menu draws its banner): no map is loaded at all, the renderer lights the
models on its own, and `r_clear 1` + `r_clearColor 0x000000` gives black
behind them. Nothing can clip us because there is nothing else there.

The plan is the real building, in Quake units:

    stylobate   three steps, each 12 deep and 16 high
    columns     `--columns` across the front, on the step, 8:1 shafts
    architrave  a plain beam on the capitals
    frieze      a taller band above it -- this is where accent colour lives
    cornice     a projecting shelf
    pediment    the gable, with a flat tympanum for the mark to sit in

Materials are two: `textures/pantheon/stone` for the masonry and
`textures/pantheon/accent` for the frieze band and the step nosing, so the
blue reads as architecture rather than as paint.
"""
import argparse
import importlib.util
import math
import sys
from pathlib import Path

import bmesh
import bpy

HERE = Path(__file__).resolve().parent
STONE = "textures/pantheon/stone"
ACCENT = "textures/pantheon/accent"


def _pillar_module():
    spec = importlib.util.spec_from_file_location("pillar", HERE / "build_pillar_v1.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def box(bm, x0, y0, z0, x1, y1, z1):
    quads = [((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)),      # bottom
             ((x0, y0, z1), (x0, y1, z1), (x1, y1, z1), (x1, y0, z1)),      # top
             ((x0, y0, z0), (x0, y0, z1), (x1, y0, z1), (x1, y0, z0)),      # -y
             ((x1, y1, z0), (x1, y1, z1), (x0, y1, z1), (x0, y1, z0)),      # +y
             ((x0, y1, z0), (x0, y1, z1), (x0, y0, z1), (x0, y0, z0)),      # -x
             ((x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0))]      # +x
    for q in quads:
        bm.faces.new([bm.verts.new(v) for v in q])


def wedge(bm, x0, x1, y0, y1, z0, z1):
    """The pediment: a gable whose apex is at the middle of the span."""
    ax = (x0 + x1) / 2
    for y in (y0, y1):
        bm.faces.new([bm.verts.new(v) for v in
                      (((x0, y, z0)), ((x1, y, z0)), ((ax, y, z1)))])
    bm.faces.new([bm.verts.new(v) for v in
                  ((x0, y0, z0), (ax, y0, z1), (ax, y1, z1), (x0, y1, z0))])
    bm.faces.new([bm.verts.new(v) for v in
                  ((ax, y0, z1), (x1, y0, z0), (x1, y1, z0), (ax, y1, z1))])
    bm.faces.new([bm.verts.new(v) for v in
                  ((x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0))])


def mesh_from(bm, name, material):
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(bpy.data.materials.new(material))
    return ob


def build(n_columns, col_height, span, depth):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    pillar = _pillar_module()

    step_h, step_d, steps = 16.0, 12.0, 3
    base_z = steps * step_h
    r = col_height / 8.0 / 2.0 * 1.34             # the base radius of a column
    arch_h, frieze_h, cornice_h = 26.0, 34.0, 18.0
    entab_z = base_z + col_height

    stone = bmesh.new()
    accent = bmesh.new()

    # stylobate: each step wider and deeper than the one above it
    for i in range(steps):
        grow = (steps - i) * step_d
        box(stone, -span / 2 - grow, -depth / 2 - grow, i * step_h,
            span / 2 + grow, depth / 2 + grow, (i + 1) * step_h)
    # a thin accent nosing on the top step
    box(accent, -span / 2 - step_d * 0.98, -depth / 2 - step_d * 0.98, base_z - 2.0,
        span / 2 + step_d * 0.98, depth / 2 + step_d * 0.98, base_z)

    # the colonnade, across the front
    ob_cols = []
    pitch = span / (n_columns - 1) if n_columns > 1 else 0.0
    for i in range(n_columns):
        col = pillar.build(col_height, 20, 0.035, 48, 8.0, reset=False)
        col.location = (-span / 2 + i * pitch, -depth / 2 + r * 1.2, base_z)
        ob_cols.append(col)

    # architrave, frieze (accent), cornice
    box(stone, -span / 2 - r * 1.6, -depth / 2 - r * 1.6, entab_z,
        span / 2 + r * 1.6, depth / 2 + r * 1.6, entab_z + arch_h)
    box(accent, -span / 2 - r * 1.5, -depth / 2 - r * 1.5, entab_z + arch_h,
        span / 2 + r * 1.5, depth / 2 + r * 1.5, entab_z + arch_h + frieze_h)
    box(stone, -span / 2 - r * 2.1, -depth / 2 - r * 2.1, entab_z + arch_h + frieze_h,
        span / 2 + r * 2.1, depth / 2 + r * 2.1,
        entab_z + arch_h + frieze_h + cornice_h)

    # the pediment
    ped_z = entab_z + arch_h + frieze_h + cornice_h
    wedge(stone, -span / 2 - r * 2.1, span / 2 + r * 2.1,
          -depth / 2 - r * 2.1, -depth / 2 - r * 2.1 + 22.0,
          ped_z, ped_z + (span * 0.5 + r * 2.1) * 0.30)

    # the cella wall behind the columns, so the portico has a building
    box(stone, -span / 2 - r, depth / 2 - 40.0, base_z,
        span / 2 + r, depth / 2, entab_z + arch_h)

    obs = [mesh_from(stone, "temple_stone", STONE),
           mesh_from(accent, "temple_accent", ACCENT)] + ob_cols
    for ob in obs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    bpy.ops.object.join()
    temple = bpy.context.object
    temple.name = "pantheon_temple"

    # world-scale box UVs: masonry at one tile per 128 units, everywhere
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.cube_project(cube_size=128.0, correct_aspect=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    return temple


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--columns", type=int, default=6)
    ap.add_argument("--col-height", type=float, default=256.0)
    ap.add_argument("--span", type=float, default=620.0)
    ap.add_argument("--depth", type=float, default=260.0)
    ap.add_argument("--out", default="assets/pantheon_world/generated/pantheon_temple.obj")
    a = ap.parse_args(argv)

    ob = build(a.columns, a.col_height, a.span, a.depth)
    out = Path(a.out).absolute()
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.obj_export(filepath=str(out), export_selected_objects=False,
                          export_uv=True, export_normals=True,
                          export_materials=True, export_triangulated_mesh=True,
                          forward_axis="Y", up_axis="Z", global_scale=1.0)
    d = ob.dimensions
    print(f"PANTHEON_TEMPLE verts={len(ob.data.vertices)} tris={len(ob.data.polygons)} "
          f"size=({d.x:.0f},{d.y:.0f},{d.z:.0f}) columns={a.columns} out={out}")


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    main(argv)
