# The PANTHEON material set — and the two things that were actually wrong

Authored: `assets/pantheon_world/build_materials_v1.py` →
`textures/pantheon/*.tga` + `scripts/pantheon.shader`, shipped in
`zzz_pantheon.pk3` (ENG-2 naming). Every texture is generated, tileable by
construction, and reproducible from that one script.

| material | for | mean RGB |
|---|---|---|
| `textures/pantheon/basalt` | the leaf body — cold basalt | 35, 38, 44 |
| `textures/pantheon/metal_deep` | frame and stiles — blue-black metal | 12, 17, 29 |
| `textures/pantheon/carved` | recessed panel relief | 30, 32, 36 |
| `textures/pantheon/glyph` | the mark's energy — narrow core | 55, 91, 195 |
| `textures/pantheon/glyph_halo` | its restrained additive stage | 7, 16, 39 |

Colours are the engine's own: Quake Live `^4` = `#3266FE`, `^7` = `#FEFEFE`
(`g_color_table_ql`, `q_math.c`).

## Finding 1 — a world shader worn by a model is broken by construction

Door v1 borrowed `textures/base_light/proto_lightblue` and
`textures/gothic_block/blocks15` from `pak00.pk3`, and the frames came back
translucent with white neon strips. Reading the shader script explains it in
one line: **the first stage of those shaders is `map $lightmap`.** Brush
surfaces carry lightmap coordinates; MD3 models do not. A model wearing a
world shader is being lit by a lightmap it cannot sample, and no amount of
picking a different texture *by name* fixes a category error.

Quake's own model shaders (`scripts/models.shader`) never do this — they use
plain `map <path>` stages. So does ours, with `rgbGen lightingDiffuse`, which
is what every player and weapon in the game uses.

**Rule:** a PANTHEON prop references a PANTHEON shader. Borrowing a world
texture path for a model is not a shortcut, it is a defect.

## Finding 2 — you cannot judge a material inside someone else's lighting

With the correct shaders the door renders solid — and the cold basalt reads
**olive green** in the frames. It is not the texture: measured means above are
blue-grey. `rgbGen lightingDiffuse` multiplies the diffuse by the **map's
light grid** at the model's origin, and that corridor of `bloodrun` is lit
green-gold.

That is the whole argument for a sealed PANTHEON test room with our own static
lights, and it is why the q3map2 dependency is foundational rather than
door-specific. Until then, material review frames are measuring bloodrun.

Also recorded, for the next pass: these albedos are dark (means 12–44 of 255).
Quake diffuse maps usually sit around 80–120 so that `lightingDiffuse` has
somewhere to go. Expect to raise them once there is a neutral room to judge in
— and raise them *because a lit frame said so*, not because a histogram did.

## What the classic renderer gets, and what it does not

This set is the **baked diffuse/cavity interpretation**: relief lives in the
diffuse, because the fixed-function path has no normal map. `_shade()` bakes a
directional cavity term from the height field for exactly that reason.

Normal, roughness, AO and emissive masks are the *source* form and belong to a
renderer that can consume them. Nothing here declares PBR, and nothing in the
current native pipeline reads it. When high/low-poly baking arrives in
Blender, it feeds this same script rather than replacing it.

## The glyph

Two stages, on purpose:

1. `map glyph.tga`, `rgbGen identity` — unlit. The mark is a light source, not
   a surface; it must not dim when the room does.
2. `map glyph_halo.tga`, `blendfunc GL_ONE GL_ONE`, `rgbGen wave sin` — a
   restrained additive halo with a slow pulse.

The v1 failure was a broad white core; the profile here is narrow
(σ ≈ 0.10 of the face) with a blue body, so the mark reads as carved light
rather than a neon tube. It still has to be judged under **both** dark and
torchlit conditions, in our own room.

Identity comes from `docs/brand/pantheon-mark.svg` — pediment, five columns,
steps, oculus. The door's *geometry* carries the mark; the material only makes
it energy.
