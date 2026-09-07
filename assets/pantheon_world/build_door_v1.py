"""Build the PANTHEON door leaf in Blender, headlessly, and export OBJ.

    "<blender>" --background --python assets/pantheon_world/build_door_v1.py -- \
        --out assets/pantheon_world/generated/pantheon_door_leaf_v1.obj

Run through Blender's own Python, with no add-on and no GUI: the asset is a
program, so it is diffable, re-runnable and reviewable. Blender is the
modeller here, not the renderer -- the frames come from the native PANTHEON
renderer, drawing this geometry as an MD3 like any other Quake model.

Units are Quake units throughout (a player is 56 tall, eyes at 26). The leaf
is authored in its own local frame:

    +X  width   0 .. 128   (hinge at x=0, parting edge at x=128)
    +Y  depth   0 ..  24
    +Z  height  0 .. 384

so a pair of leaves is this mesh and its mirror, and the door's own origin is
the hinge. Materials are real Quake Live texture paths -- PANTHEON authors
the geometry, the game supplies the surfaces, and nothing here invents a
shader we would then have to ship.
"""
import argparse
import math
import sys
from pathlib import Path

import bmesh
import bpy

# ── the design, in one place ──────────────────────────────────────────────
W, D, H = 128.0, 24.0, 384.0        # one leaf
BORDER = 14.0                        # metal frame width
BORDER_PROUD = 3.0                   # how far the frame stands off the face
PANEL_INSET = 3.0                    # how deep the stone panel sits
FLUTE_W, FLUTE_N = 9.0, 3            # vertical ribs on the lower panel
PEDIMENT_Z = 250.0                   # where the mark begins
PEDIMENT_H = 78.0
ENTAB_H = 9.0                        # entablature bar under the pediment
COL_W, COL_N = 9.0, 3                # columns of the mark, per leaf (5 across
                                     # the pair: the centre one splits)
GLYPH_PROUD = 2.5                    # inlay stands proud so it catches light

# PANTHEON's own material set (assets/pantheon_world/build_materials_v1.py).
# NOT Quake Live world textures: those are world shaders whose first stage is
# `map $lightmap`, and a model has no lightmap coordinates to sample.
# PANTHEON material NAMES, wearing Quake's own images at 4x -- see
# engine/pantheon/material_adapter.py. The name is ours so it cannot collide
# with a world shader; the picture is the game's.
STONE = "textures/pantheon/door_body"
METAL = "textures/pantheon/door_metal"
GLYPH = "textures/pantheon/glyph"
CARVED = "textures/pantheon/door_relief"

UV_UNITS_PER_TILE = 64.0             # one texture tile per 64 Quake units


def box(name, x0, y0, z0, x1, y1, z1, material):
    """An axis-aligned box as its own object, with one material."""
    mesh = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(ob)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(x1 - x0, y1 - y0, z1 - z0), verts=bm.verts)
    bmesh.ops.translate(bm, vec=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2),
                        verts=bm.verts)
    bm.to_mesh(mesh)
    bm.free()
    ob.data.materials.append(material)
    return ob


def wedge(name, x0, x1, z0, z1, y0, y1, material, apex_at_x1=True):
    """A triangular prism: the pediment's rake. Apex on one side so that a
    mirrored pair forms one gable across the closed doors."""
    mesh = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(ob)
    ax = x1 if apex_at_x1 else x0
    tri = [(x0, z0), (x1, z0), (ax, z1)]
    verts = [(x, y0, z) for (x, z) in tri] + [(x, y1, z) for (x, z) in tri]
    faces = [(0, 1, 2), (5, 4, 3),
             (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]
    mesh.from_pydata(verts, [], faces)
    mesh.validate()
    ob.data.materials.append(material)
    return ob


def material(name):
    m = bpy.data.materials.get(name)
    return m if m else bpy.data.materials.new(name)


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    stone, metal, glyph = material(STONE), material(METAL), material(GLYPH)
    carved = material(CARVED)
    parts = []

    # the slab: stone, recessed relative to the frame
    parts.append(box("leaf_panel", 0, PANEL_INSET, 0, W, D, H, stone))

    # metal frame: hinge stile, parting stile, head and sill, standing proud
    parts.append(box("stile_hinge", 0, 0, 0, BORDER, D + BORDER_PROUD, H, metal))
    parts.append(box("stile_meet", W - BORDER, 0, 0, W, D + BORDER_PROUD, H, metal))
    parts.append(box("rail_sill", 0, 0, 0, W, D + BORDER_PROUD, BORDER, metal))
    parts.append(box("rail_head", 0, 0, H - BORDER, W, D + BORDER_PROUD, H, metal))
    parts.append(box("rail_mid", 0, 0, PEDIMENT_Z - ENTAB_H - BORDER,
                     W, D + BORDER_PROUD, PEDIMENT_Z - ENTAB_H, metal))

    # lower panel: vertical stone flutes
    span = W - 2 * BORDER
    pitch = span / (FLUTE_N + 1)
    for i in range(FLUTE_N):
        x = BORDER + pitch * (i + 1) - FLUTE_W / 2
        parts.append(box(f"flute_{i}", x, PANEL_INSET, BORDER + 8,
                         x + FLUTE_W, D + 1.0, PEDIMENT_Z - ENTAB_H - BORDER - 8,
                         carved))

    # the mark: entablature, columns, and half a pediment per leaf
    parts.append(box("entablature", 0, PANEL_INSET, PEDIMENT_Z - ENTAB_H,
                     W, D + 2.0, PEDIMENT_Z, glyph))
    cpitch = span / COL_N
    for i in range(COL_N):
        x = BORDER + cpitch * i + (cpitch - COL_W) / 2
        parts.append(box(f"column_{i}", x, PANEL_INSET,
                         PEDIMENT_Z - ENTAB_H - BORDER - 8 + 4,
                         x + COL_W, D + GLYPH_PROUD, PEDIMENT_Z - ENTAB_H, glyph))
    parts.append(wedge("pediment", BORDER, W, PEDIMENT_Z, PEDIMENT_Z + PEDIMENT_H,
                       PANEL_INSET, D + GLYPH_PROUD, glyph, apex_at_x1=True))
    parts.append(box("stylobate", 0, PANEL_INSET, BORDER,
                     W, D + GLYPH_PROUD, BORDER + 6, glyph))

    # one object
    for ob in parts:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    leaf = bpy.context.object
    leaf.name = "pantheon_door_leaf_v1"

    # a small bevel so edges catch the light instead of reading as cardboard
    bpy.ops.object.mode_set(mode="EDIT")
    bm = bmesh.from_edit_mesh(leaf.data)
    bmesh.ops.bevel(bm, geom=list(bm.edges) + list(bm.verts), offset=0.9,
                    segments=1, affect="EDGES")
    bmesh.update_edit_mesh(leaf.data)

    # UVs at a fixed world density, so the stone reads at Quake's own scale
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.cube_project(cube_size=UV_UNITS_PER_TILE, correct_aspect=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    return leaf


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="assets/pantheon_world/generated/"
                                     "pantheon_door_leaf_v1.obj")
    ap.add_argument("--blend", default="")
    ap.add_argument("--uv-units", type=float, default=UV_UNITS_PER_TILE,
                    help="Quake units per texture tile (the study sweeps this)")
    a = ap.parse_args(argv)

    global UV_UNITS_PER_TILE
    UV_UNITS_PER_TILE = a.uv_units
    leaf = build()
    out = Path(a.out).absolute()
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.obj_export(filepath=str(out), export_selected_objects=False,
                          export_uv=True, export_normals=True,
                          export_materials=True, export_triangulated_mesh=True,
                          forward_axis="Y", up_axis="Z", global_scale=1.0)
    if a.blend:
        bpy.ops.wm.save_as_mainfile(filepath=str(Path(a.blend).absolute()))
    v = len(leaf.data.vertices)
    f = len(leaf.data.polygons)
    print(f"PANTHEON_DOOR_LEAF verts={v} faces={f} out={out} bytes={out.stat().st_size}")


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    main(argv)
