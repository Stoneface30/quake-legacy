# Blender — role, and the blocker

## The blocker, stated first

**Blender is not installed on this machine.** Checked `C:/Program Files`,
`C:/Program Files (x86)`, `D:`, `E:`, `F:`, the shell PATH and the `blendfile`
registry class; no portable copy either. Nothing in this session can produce a
`.blend` until that changes, and no plan should pretend otherwise.

Installing it is a director action, not something to work around silently.

## What Blender is FOR here

Not a second Quake renderer. Native PANTHEON stays the authority for world,
players, weapons and animation. Blender covers what Quake cannot express:

* the PANTHEON door leaf and its ornament — sculpted, then exported
* true pointing, custom arm poses, object interaction. MD3 player animation is
  a fixed frame table: a presenter *cannot* point at an arbitrary spot, and
  substituting an unrelated gesture would be faking it
* impossible geometry and world-transformation transitions
* controlled object IDs / Cryptomatte for compositing

## The export path, once installed

| target | format | consumed by |
|---|---|---|
| hero prop / door leaf, no collision | `.md3` | native renderer, `model` keyword |
| map geometry with collision + lightmaps | `.ase` / `.obj` → q3map2 `misc_model` | compiled BSP |
| animation beyond MD3's frame table | per-frame vertex MD3, or a Blender-rendered element composited | native + post |

MD3 export needs an addon; `.ase`/`.obj` are native. Neither can be verified
here until Blender exists.

## What we do in the meantime

PANTHEON writes the geometry itself. A door leaf, a plinth, a colonnade
segment and a glyph are parametric solids: a small Python MD3 **writer** gives
custom geometry with no external tool, deterministic and reviewable in a way a
hand-modelled asset is not. When Blender arrives it replaces the sculpting,
not the pipeline.
