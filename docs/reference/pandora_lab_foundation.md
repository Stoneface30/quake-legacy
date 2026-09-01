# PANDORA LAB — foundation

*2026-09-01. Directive 30–40. Architecture and four proofs only: no bulk
generation, no corpus-wide conversion, no original asset mutated.*

## What this opens

Twelve independently swappable domains, so a pack may touch one and leave
the rest alone, and two packs touching different domains compose without
either knowing about the other.

| capture-affecting | post-only |
|---|---|
| `WORLD_TEXTURES` `WEAPON_SKINS` `PLAYER_SKINS` `PLAYER_MODELS` `WEAPON_MODELS` `ANIMATION_PRESENTATION` `SHADER_FX` `PARTICLE_FX` `LIGHTING` `HUD_STYLE` | `POST_GRADE` `TRANSITION_STYLE` |

That split is the Pandora echo of `visual_capture_key` /
`preview_assembly_key`, and exists for the same reason: a grade change must
not throw away a capture, and a texture change must. `AssetPack.affects_capture`
answers it per pack, including via enabled effects.

## Three asset tiers, never conflated

`ORIGINAL` (Steam pak, read-only per ENG-4) → `MASTER` (generated, kept,
hashed) → `RUNTIME` (engine-ready derivative, disposable).

`AssetVariant` **cannot be constructed with `tier=ORIGINAL`** and requires
`source_hash`, `workflow_hash` and `master_hash`. An unreproducible variant
is not a result, so it is not representable.

## Effects bind to evidence, never to wall-clock time

`ReactiveEffect.event` must be one of the recognised events
(`PROJECTILE_LAUNCH/IMPACT`, `LG_BURST`, `DODGE_HERO`, `FRAG`, `ROUND_WIN`,
`MULTIKILL`). Anything else raises. This is enforced rather than documented
because the project has already shipped a rule whose only trigger was a
hand-written override line, and it fired for one clip in a hundred and
twenty.

If the evidence is absent the effect is absent: `resolve_effects` never
nudges an effect to a nearby timestamp to make it appear.

## The OFF rule is enforced, not conventional

Every effect defaults to `OFF`, and `AssetPack.with_all_effects_off()`
returns a pack whose effects all resolve to nothing while the domain
overrides survive. The normal movie must render through that, which is what
stops the project becoming dependent on one experimental gimmick.

## Proofs

**1 — texture/skin swap, traced end to end.** A real generated asset, not a
mock:

```
source   anarki.png (117 KB)   065efc63abe64c32
workflow cartoon_sdxl.json     e122f1df3536bb06
master   anarki.png (488 KB)   8eeb0916930810c5
variant  72e1c77b45197aa1      tier=MASTER  domain=PLAYER_SKINS
ORIGINAL untouched: True
```

**2 — reactive FX on the real micro-sequence.** An `impact_flash` bound to
`PROJECTILE_IMPACT` resolved against the actual anchors of
`MICRO_SEQUENCE_V2_REVIEW`, landing on the bridge cut and the trinity hero:

```
impact_flash [SUBTLE] 10.360-10.620s  on PROJECTILE_IMPACT   <- the bridge cut
impact_flash [SUBTLE] 11.710-11.970s  on PROJECTILE_IMPACT   <- trinity hero
OFF -> 0 effects fired; the skin swap survives
```

**3 — model/animation: feasibility recorded, not built.** The
`ANIMATION_PRESENTATION` domain exists and is capture-affecting. Per
directive 34 the replay movement truth stays authoritative and enhancements
are presentation-only; Wolfcam is **not** being upgraded for IQM yet, so
the near-term feasible work is baked MD3 variants and pose interpolation.
No animation asset was produced this cycle.

**4 — the one next transition candidate: `DEPTH_TRANSITION`.**

Chosen from the eleven listed families on the only evidence available: the
runtime already exports depth (`mme_saveDepth`, in `RUNTIME_BASELINE`),
so a depth-driven transition is the single candidate whose prerequisite is
already proven on this engine. Every other family
(`MODEL_MORPH`, `MATERIAL_DISSOLVE`, `TELEPORTER_PASS`, …) needs a
capability that has not yet been demonstrated.

It also directly addresses the finding from the first bridge: the
campgrounds → trinity cut carries a large luminance jump, and a depth-keyed
handover is a way to make that discontinuity read as intentional
punctuation rather than colour-matching it away.

## Not done, deliberately

No bulk generation. No 61-map overhaul. No player-model sweep. One texture
proof, one reactive-FX proof, one recorded feasibility, one next candidate.
