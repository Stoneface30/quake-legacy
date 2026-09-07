# PANTHEON_TEMPLE_V1 — one world, three modules

One environment, reused; not three unrelated scenes. Everything below is a
plan, not a claim about something that exists.

```
            THE DOORS  (module C)
                 |
        +--------+--------+
        |    THE HALL     |   module A -- 26 characters, two colonnades
        |                 |
        |   central aisle |
        |                 |
        +--------+--------+
                 |
        THE EXPLANATION ARENA  (module B -- open floor, frozen history)
```

## Scale (Quake units — player 56 tall, eye 26, 64-unit grid)

| element | size | reason |
|---|---|---|
| hall length | 3072 | 13 plinth bays at 192 + the doors + the apse |
| hall width | 1024 | two colonnades 320 apart from the aisle centre-line |
| ceiling | 512 | monumental without losing a 100° camera's headroom |
| aisle | 384 wide | the signature camera move lives here |
| plinth | 96 × 96 × 48 | a character on it reads above the colonnade base |
| bay pitch | 192 | 13 bays per side = 26 anchors, one per character |
| doors | 256 × 384 | `DOORS_V1.md` |
| arena floor (apse) | 1024 × 1024, +0 | space for a frozen 1v1 and a presenter |

Two colonnades × 13 bays = **26 anchors** — exactly the installed roster, and
that is why the layout is 13 bays, not a round number.

## The three modules on one plan

* **A · THE HALL** — the roster on plinths, an anchor each, facing the aisle.
  Idle poses only; no one runs. Named identities preserved (`ROSTER_MANIFEST.md`).
* **B · THE EXPLANATION ARENA** — the apse floor. Historical action is placed
  here and frozen; the presenter walks in on edit time while history holds.
  Layers stay separate: HISTORICAL · PRESENTER · ANALYSIS · SYNTHETIC.
* **C · THE DOORS** — the entrance, and later a transition primitive.

## Character placement, semantically

Each anchor carries: `anchor_id`, world position, facing, character (model +
skin), pose, light intent, provenance. Placement goes through
`RoundScenario` → `FrameTruth` → `RenderFrame`, never as a literal in the
renderer (HL-1, HL-5). An anchor with no character assigned renders nothing —
it is not filled with a guess.

## Light and colour

Stone and dark metal ground; `^4 #3266FE` for light strips, glyphs, banner
emissives; `^7 #FEFEFE` for inlay and edge light. The characters keep their
own colours. Lighting profile `CINEMATIC` (the proven gamma-bake path), with
`^4` accents doing the separation rather than a coloured global grade.

## The signature camera move

Doors → aisle → roster passes left and right → rise → final composition on
the apse. One continuous path, but **validity is not optional**, and PROOF_02B
is the reason: BSP collision, sight-lines to every subject that must be seen,
frame-edge clearance, and composition sampled **along the path**, not only at
the settle.

**The native renderer has its own projection.** `instruction.project()` is
calibrated to Wolfcam's convention (`cg_fov` = horizontal FOV of a 4:3 frame,
vertical kept on 16:9). The native host computes `fov_y = fov_x · h/w`, which
is a *different* model. Nothing may reuse the Wolfcam-calibrated numbers on a
native frame until we have measured a rendered native frame and calibrated
against it. That measurement is a Phase-4 gate.

## What is authored vs what is not

| element | class |
|---|---|
| hall geometry, plinths, doors, banners | **AUTHORED** (PANTHEON / Blender) |
| characters, weapons, textures, animation | **NATIVE QUAKE** assets from pak00 |
| the frozen fight in module B | **HISTORICAL**, immutable, from a demo |
| presenter walk / gesture | **AUTHORED performance** from a real recording |
| Crash's line | **SYNTHETIC** (TTS), always labelled |
| trajectory lines, prediction geometry | **DERIVED**, labelled, never RECORDED |
| concept boards, texture studies | **ComfyUI**, look development only — never truth |
