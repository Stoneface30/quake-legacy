# Compiling PANTHEON worlds — the dependency, the sequence, the manifest

q3map2 is a **foundational asset dependency**, not a tool needed for one door.
Without it we have no sealed room, no lightmaps, no VIS, no collision and no
`func_door` — and, as `MATERIALS_V1.md` records, no honest way to judge a
material, because every render is measuring somebody else's light grid.

## Division of geometry

| use | build it as | why |
|---|---|---|
| structural shell — floors, walls, ceilings, portals | **brushes** | collision, VIS, lightmaps, sealing |
| curved detail | **patches**, or compiled model geometry | brushes cannot curve cheaply |
| reusable / movable / separately lit objects | **MD3** | placed by transform, no BSP recompile |
| decorative relief on a door or column | **MD3 or detail brush** | keep visual detail out of collision so a carving never changes how a player moves |

Collision and decoration stay separate. A carved door leaf must not be the
thing a player collides with.

## The compile sequence, and the manifest

`BSP → VIS → LIGHT`, in that order, with the exact options recorded per build:

```
q3map2 -meta            -fs_basepath <ql> -fs_game <mod>  pantheon_temple_v1.map
q3map2 -vis   -saveprt  -fs_basepath <ql> -fs_game <mod>  pantheon_temple_v1.map
q3map2 -light -fast -patchshadows -samples 2 ...          pantheon_temple_v1.map
```

Every compile writes `build_manifest.json` beside the BSP:

* q3map2 build id + sha256 of the binary
* the full argv of each of the three stages
* source `.map` sha256, and the sha256 of every referenced shader/texture
* wall-clock per stage, and the compiler's own warning lines kept verbatim
* the resulting BSP sha256

A render that cannot name the BSP it drew, and a BSP that cannot name the
options that made it, are both unreviewable. Bounce lighting, higher lightmap
resolution and expensive quality settings arrive **after** a sealed room with
real static lights renders correctly — evaluated against *our* renderer, never
copied from a tutorial.

## Getting q3map2 — decided, honestly

Audited 2026-09-07:

* **We have source**: `engine/engines/_canonical/tools/quake3/q3map2` (46 `.c`),
  with `game_quakelive.h` and the GtkRadiant 1.6 `libs/` (cmdlib, mathlib,
  picomodel, ddslib, md5lib, jpeg6).
* **We have a toolchain**: MinGW-w64 i686 gcc 14.2, cmake, ninja, nasm.
* **Three problems.** `_canonical` is a SHA-256 **dedup merge** of every engine
  in the knowledge base, not a project — its q3map2 has no build system and its
  file provenance is mixed. `q3map2.h` includes `png.h`, and `inout.c` wants
  libxml2; neither libpng nor libxml2 is present for MinGW. And the tree is
  **untracked**, so building from it would repeat exactly the mistake the
  renderer bank fixed.

Two honest routes, and this is a director call because one needs a download:

* **R1 — build from a clean upstream q3map2** (NetRadiant-custom source). Known
  provenance, has its own build system. Needs a download and libpng/zlib/
  libxml2 for MinGW (or their bundled equivalents).
* **R2 — build the vendored copy**, banked into this branch first, with PNG
  loading and the XML console stubbed out (we author TGA/JPG, and nothing here
  connects to Radiant). No download; provenance stays "a dedup corpus", which
  must then be stated wherever the compiler's output is claimed.

R1 is the better foundation. R2 is the one that needs nobody's permission.

## The renderer side

Whatever compiles the BSP, the renderer already loads real BSPs, real
lightmaps and inline submodels (`R_LoadSubmodels` names them `*N`,
`RE_RegisterModel` returns them, `R_AddBrushModelSurfaces` draws them). The
only missing piece for movers is a `brush` keyword in our shot script — the
same shape as the `prop` keyword already added.
