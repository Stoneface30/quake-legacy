# PANTHEON world assets

Geometry PANTHEON authors, as programs rather than binaries.

    "<blender>" --background --python assets/pantheon_world/build_door_v1.py -- \
        --blend assets/pantheon_world/generated/pantheon_doors_v1.blend
    python scripts/obj_to_md3.py assets/pantheon_world/generated/pantheon_door_leaf_v1.obj \
        --out <gamedir>/models/pantheon/door_leaf_v1.md3
    python scripts/obj_to_md3.py ... --mirror-x --out .../door_leaf_v1_mirror.md3

`generated/` is not committed: every file in it is reproducible from the two
commands above, and a `.blend` is not reviewable in a diff.

Provenance: geometry authored by PANTHEON in Blender 5.2.1 (headless, no
add-on). Surfaces are Quake Live's own textures, referenced by path and never
redistributed -- `textures/gothic_block/blocks15`,
`textures/base_wall/bluemetal3b`, `textures/base_light/proto_lightblue`.
