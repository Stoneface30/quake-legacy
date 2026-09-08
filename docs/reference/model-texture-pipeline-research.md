# Player Model / Skin / Texture Pipeline — Research (Blender + ComfyUI, pk3 Override Path)

> Research date: 2026-08-31 | Research task only — no code or assets modified.
> Scope: how to change the Xaero-based cinematic identity model, and other skins/textures,
> using (a) Blender for geometry and (b) the existing ComfyUI pipeline for AI-generated
> texture art — landing everything through the **same pk3 override mechanism already used**
> by `creative_suite/engine/pantheon_ads.py` (ad-board textures) and the Phase-5 ComfyUI
> photoreal pipeline (`PH5-1..PH5-10` in `CLAUDE.md`). **No wolfcamql/Q3 engine rebuild is
> required or proposed anywhere in this document** — MD3 models, `.skin` files, and shader
> textures are all data files the stock engine already loads from pk3s at runtime, exactly
> like `zzz_uhd_*.pk3` and `zzz_zz_pantheon_ads.pk3` do today.

Related prior art in this repo: `docs/reference/comfyui-texture-pipeline.md` (2026-04-16,
weapon-texture focused — this doc extends the same ComfyUI approach to player-skin textures
and adds the model/geometry side that the earlier doc didn't cover).

---

## 1. Effort-tier summary

| Tier | What changes | Tooling | Realistic time cost | Automatable? |
|---|---|---|---|---|
| **T1 — Texture-only reskin** | Replace the diffuse texture(s) a `.skin` file points at. Geometry, UVs, tags, animation all untouched. | ComfyUI (existing pipeline) or hand-painting. **No Blender needed.** | Minutes per variant once the ComfyUI workflow is built; the workflow build itself is a few hours (one-time). | **Yes — this is the tier worth fully automating first.** Pick style → run img2img → repack pk3. |
| **T2 — Geometry edit via Blender** | Reshape/reproportion the existing Xaero mesh (e.g. bulk up shoulders, change helmet silhouette) while preserving the per-frame vertex-animation contract. | Blender + an MD3 import/export addon (below). Manual sculpting/retopo per surface, then re-export. | Realistically **1–3 focused sessions per body part** (upper/lower/head) even for an experienced Blender user, because every animation frame's vertex count and topology must stay identical (see §2) — you're editing a base pose and Blender's shape-key re-bake has to survive across all ~173–216 frames. | Not automatable per-variant; each geometry variant is bespoke modeling work. Could be scripted as a one-time pipeline (e.g. a Blender Python batch that applies a fixed deformation to all shape keys), but that's an engineering project in itself, not "click a button per skin." |
| **T3 — Full custom model replacement** | Throw out Xaero's mesh entirely; use a text-to-3D or image-to-3D generated mesh as the new player model. | Text/image-to-3D generator → Blender (retopo, decimate, rig-to-animation retarget) → MD3 export addon → new `animation.cfg` tuning → tag placement (`tag_head`, `tag_torso`, `tag_weapon`) → in-game verification of all ~30 animation states. | **Significant, multi-session project** — likely 1–2+ weeks of iteration for a single production-quality custom model, not a quick pk3 swap. The AI mesh gets you a static shape; everything about making it animate correctly in Q3's fixed 30-state contract is manual, expert Blender work. | No — this is a one-off asset-creation project per model, same as commissioning a custom Q3 player model has always been in the mod community. |

**Bottom line for "truly automatic":** T1 (texture-only reskin through ComfyUI) is the tier
that actually fits the "pick a style → apply → capture footage" loop with minimal manual
work per variant. T2 and T3 are legitimate but are Blender *projects*, not pipeline steps —
each one produces a new static asset that then *feeds into* the same automatic pk3-packing
step T1 uses, it just isn't itself something you can loop over N style variants cheaply.

---

## 2. MD3 format — confirmed against the actual asset chain

Verified directly against `output/demo_v2/_wolfcam_staging/baseq3/pak00.pk3` in this repo
(read-only `zipfile` inspection — pak not modified) — this is a real, present pak00 with a
full `models/players/xaero/` tree, not a hypothetical.

### 2.1 What's actually in the pak

```
models/players/xaero/
  animation.cfg                       ← frame ranges + fps per animation state
  upper.md3  upper_1.md3  upper_2.md3 ← 3 LOD levels (upper.md3 = LOD0, full detail)
  lower.md3  lower_1.md3  lower_2.md3
  head.md3   head_1.md3   head_2.md3
  upper_default.skin  upper_blue.skin  upper_red.skin
  upper_bright.skin   upper_sport.skin upper_sport_blue.skin upper_sport_red.skin
  lower_*.skin (same variant set)     head_*.skin (same variant set)
  xaero.png / xaero_a.png / xaero_h.png / xaero_q.png   ← default skin textures
  blue.png / blue_h.png   red.png / red_h.png            ← team-color textures
  bright.png / bright2.jpg / brightglow*.tga/jpg          ← "bright" skin variant textures
  sport.tga / sport_h.tga / sport_blue.tga / sport_red.tga
  icon_*.png / icon_sport.tga                             ← inventory/scoreboard icons
sound/player/xaero/  ← death/pain/jump/taunt wavs (unrelated to visuals, listed for completeness)
```

91 xaero-prefixed entries total (91 files/dirs under `models/players/xaero/` + `sound/player/xaero/` + 4 bot AI script files `botfiles/bots/xaero_*.c`, which are gameplay bot logic, not visual assets, and out of scope here).

This confirms the standard Q3 player-model convention exactly: **three MD3 body parts**
(`upper`/`lower`/`head`) each with **3 LOD variants**, **one `animation.cfg`** shared by
upper+lower, and **a family of `.skin` files** (one per selectable skin: default, red, blue,
bright, sport, sport_blue, sport_red) that map surface names to texture files rather than
textures being baked into the `.md3` itself.

### 2.2 MD3 binary structure (from direct header parse of `upper.md3` / `lower.md3` / `head.md3`)

MD3 (`IDP3`, version 15) is a **flat, skeleton-free vertex-animation format** — there is no
bone hierarchy. Every animation frame stores the *absolute* vertex position of every vertex
in the mesh for that frame (a full "morph target" per frame, quantized to a compressed
16-bit format: X/Y/Z at 1/64-unit precision + a 2-byte lat/long-encoded normal). This is the
single most important constraint for any geometry edit (see §2.3).

File layout, per surface:
- **Header**: ident, version, internal name, flags, frame/tag/surface/skin counts, offsets.
- **Frames[]**: bounding box, origin, radius, name — one entry per animation frame (no vertex
  data here; that lives per-surface).
- **Tags[]**: named attachment points, *one full set per frame* (name + origin + 3×3 rotation
  matrix). This is how Q3 attaches head→torso, weapon→hand, and torso→legs every frame
  without a skeleton — each tag's transform is just re-read per frame like everything else.
- **Surfaces[]**: each surface (a mesh chunk, e.g. `u_torso`, `u_arm`, `l_legs`, `l_sash_back`,
  `h_head`) has its own vertex/triangle data and **its own per-frame vertex array**. A model
  can have multiple surfaces; each is independently skinned via the `.skin` file.
- Per surface: shader name slots (usually unused — `num_skins` on the whole model is `0` in
  this pak, meaning **texture assignment is delegated entirely to the external `.skin` file**,
  not embedded in the `.md3`), triangle index list, UV (ST) coordinates (**one UV set, shared
  across all frames** — UVs don't animate, only vertex positions do), and the per-frame vertex
  array (`num_frames × num_verts` entries).

Confirmed concretely from this pak:

| File | Frames | Tags | Surfaces (verts/tris) |
|---|---|---|---|
| `upper.md3` | 173 | `tag_weapon`, `tag_torso`, `tag_head` | `u_armbase` (71/47), plus `u_torso`, `u_arm` (and, in team-skin variants that reference them via `.skin`, quill surfaces `u_quill01..08`) |
| `lower.md3` | 216 | `tag_torso` | `l_legs` (274/324), `l_sash_back` (13/19), `l_sash_front` (25/29) |
| `head.md3` | 1 | `tag_head` | `h_head` (73/96) — head is a static mesh; it moves only via the `tag_head` transform read from `upper.md3` each frame |

### 2.3 `animation.cfg` — the fixed 30-state animation contract

```
sex m
footsteps flesh
0    49  0   20   // BOTH_DEATH1
48   1   0   20   // BOTH_DEAD1
...
150  6   0   15   // TORSO_ATTACK   (MUST NOT CHANGE -- hand animation is synced to this)
156  6   0   15   // TORSO_ATTACK2  (MUST NOT CHANGE -- hand animation is synced to this)
162  5   0   20   // TORSO_DROP     (MUST NOT CHANGE -- hand animation is synced to this)
167  4   0   20   // TORSO_RAISE    (MUST NOT CHANGE -- hand animation is synced to this)
171  1   0   15   // TORSO_STAND
...
173  8   8   20   // LEGS_WALKCR
181  12  12  20   // LEGS_WALK
...
265  7   7   15   // LEGS_TURN
```

Each line is `first_frame  num_frames  looping_frames  fps` for one named animation state
(`BOTH_*` = shared death sequences, `TORSO_*` = upper body, `LEGS_*` = lower body). This file
is the contract the engine's `cgame` uses to slice a model's flat frame array into named
animations — it is **not** something you get to redefine loosely: the id-software source
comment baked into the file itself (`MUST NOT CHANGE`) exists because `TORSO_ATTACK`/
`TORSO_ATTACK2`/`TORSO_DROP`/`TORSO_RAISE` frame counts are hardcoded assumptions elsewhere in
the game code for weapon-hand sync. `upper.md3`'s 173 frames match the `BOTH_*` + `TORSO_*`
range (0–172) exactly; `lower.md3`'s 216 frames cover `BOTH_*` (0–116, shared for shared death
poses) plus the `LEGS_*` range (173–271, renumbered internally to 117–215) — the classic Q3
"legs frame skip" quirk, where the engine recalculates an offset so the legs model's own
frame array lines up with the `LEGS_*` labels in the same `animation.cfg` despite storing
fewer total frames than the label numbers imply. Any replacement model must reproduce this
same frame-count/label relationship or player animation breaks in-game.

### 2.4 `.skin` files — the actual texture-assignment layer

```
# upper_default.skin
u_armbase,models/players/xaero/xaero_a.tga
u_torso,models/players/xaero/xaero.tga
u_arm,models/players/xaero/xaero_a.tga
tag_weapon,
tag_torso,
tag_head,
```

A `.skin` file is a plain-text `surface_name,texture_path` map (tags are listed with an empty
value — they're not textured, just documented). This is the layer T1 reskins operate on: **the
file extension in the `.skin` line doesn't have to match what's actually on disk** — this pak's
`.skin` files reference `xaero.tga` while the real files shipped are `.png`/`.jpg` (`xaero.png`,
`bright2.jpg`, etc.); the Q3 engine's texture loader tries multiple extensions when resolving a
shader/image path. Practically: a texture-only reskin can either (a) overwrite the referenced
image file directly with new pixel data, or (b) add a brand-new `.skin` variant file
(`upper_pantheon.skin` etc.) pointing at new files and expose it as a new selectable skin —
both are pure data changes, zero MD3/geometry work, and both slot into the existing pk3
override pattern (`zzz_*.pk3`, per `ENG-2`).

---

## 3. Blender MD3 workflow — addon findings

### 3.1 Available addons (checked for current maintenance)

| Addon | Repo | Blender compat | Notes |
|---|---|---|---|
| **blender-md3** (neumond) | https://github.com/neumond/blender-md3 | ≥ 2.7.2, Python 3 | Import + export. Animation represented as **Shape Keys**; MD3 tags imported as **Empty objects**. This is the most commonly cited "up to date" MD3 addon in current tutorials. |
| **blender-md3_2.7-3.2** (hypov8) | https://github.com/hypov8/blender-md3_2.7-3.2 | 2.7–3.2 (tested on 2.79/2.80/2.92/3.2) | Also Shape-Key based, tags as Empties. Adds texture node setup + multi-file batch import. README explicitly flags: **exporter is incomplete, and rigged models have animation issues** — treat re-export as needing manual verification per model, not a solved pipeline. |
| **Blender_BSP_Importer** (SomaZ) | https://github.com/SomaZ/Blender_BSP_Importer | 2.93–4.2 | Primarily a `.bsp` map importer for id Tech 3, but bundles a full MD3 importer/exporter and a `.tan` (tiki) importer/exporter as a side feature. Actively maintained as of the 2024–2025 Blender 4.x line — the best bet if you're on a recent Blender. |
| **md3blender** (TheLinker) | https://github.com/TheLinker/md3blender | Older (pre-2.8 era scripts referenced in search results) | Listed for completeness; less current than the above three. |

There is no first-party or "official" MD3 addon — this is entirely community tooling, as has
been true for the ~25-year life of the format. All of the maintained options converge on the
same representation: **Shape Keys for the per-frame vertex morph animation, Empty objects for
tags.** That convergence isn't a stylistic choice — it's forced by the format itself (§2.2):
MD3 has no bones, so the only way to represent "vertex position changes every frame" in
Blender is a stack of shape keys, one per MD3 frame.

### 3.2 Workflow by tier, mapped to §1

**T1 — texture-only reskin: confirmed, no Blender needed at all.** You never touch the
`.md3` files. Replace/add texture files + `.skin` file as in §2.4. This is the ComfyUI-fed
path (§4).

**T2 — geometry edit (Blender required):**
1. Import `upper.md3` (or `lower.md3`/`head.md3`) via one of the addons above → lands as a
   mesh object with N shape keys (N = frame count: 173 for upper, 216 for lower, 1 for head)
   and 3 Empty objects for tags.
2. Edit the **base shape** (shape key "Basis" / frame 0 reference, or whichever frame is used
   as the sculpting target) — reshape, retexture UVs if needed, adjust proportions.
3. **The hard constraint**: every other shape key (every other animation frame) must be
   updated to be topologically identical (same vertex count, same vertex order) to the edited
   base, or export will fail or produce garbage. Blender doesn't propagate a base-mesh edit
   across existing shape keys automatically — a change to vertex count/topology has to be
   done *before* any shape keys are relative-blended, or via a script that reapplies the same
   deformation to every keyframe. This is the single biggest source of friction in Q3
   character remodeling and is exactly why hypov8's own README calls out "rigged models have
   animation issues" as an open problem.
4. Tag empties (`tag_weapon`, `tag_torso`, `tag_head`) must keep sensible positions/orientations
   per frame relative to the new geometry, or weapon-in-hand and head/torso attachment will
   look wrong in-game even if the mesh itself exports cleanly.
5. Export back to `.md3` via the same addon, matching `animation.cfg`'s frame-count-per-surface
   expectations exactly (§2.3).

**Realistic scope**: a *pure texture/UV touch-up with a tiny geometry nudge on the base pose
only* (e.g., slightly wider shoulders, kept rigid across the whole pose) is a same-day task
for someone comfortable in Blender. A *genuine reproportion that must look right through all
~30 animation states* (walk, run, jump, attack, death) is realistically several sessions of
iterate-export-test-in-engine, because you only find broken frames by watching the animation
play in Q3/WolfcamQL, not by looking at Blender's viewport.

**T3 — full model replacement**: everything in T2, plus building the entire mesh + all 173/216/1
frames of animation from scratch (or via retargeting, see §5) and getting tag placement right
with no reference geometry to diff against. Treat as a from-scratch character-animation project.

---

## 4. ComfyUI → player-skin texture — recommended concrete workflow

This is a direct extension of the pipeline already validated for weapon textures in
`docs/reference/comfyui-texture-pipeline.md` and formalized as hard rules in `CLAUDE.md`
`PH5-1..PH5-10`. The category-routing logic in `PH5-7` already draws exactly the distinction
this task asked about — apply it to player skins the same way it's applied to weapon/HUD
textures today:

- **Player skin diffuse textures** (`xaero.png`, `blue.png`, `red.png`, `bright.png`, `sport.tga`,
  and their `_h` head-texture and `_a`/`_q` arm/quill variants) are **UV-mapped surface
  textures painted onto a fixed-topology mesh**, structurally the same category as the
  weapon surface textures `PH5-7` already classifies as **SURFACE** (diffusion-viable,
  denoise up to the tile-controlnet ladder) rather than **FX / shape-critical** (icons, HUD,
  sprites — upscale-only, diffusion destroys these). The same "UV sheets don't survive
  high-denoise diffusion" caution `PH5-7` states for UV body sheets (cap at `tile_d35`,
  d50+ destroys layout) applies directly: a player skin *is* a UV body sheet.

- **Recommended node-graph pattern** (matches `PH5-1`'s validated pipeline, i.e. don't use
  plain SDXL img2img — it destroys UV layout above ~0.10 denoise):
  1. `LoadImage` (existing `xaero.png`/`.tga` skin texture as source — always start from the
     real texture, not a blank canvas, so UV-critical seams/boundaries are baked into the
     starting pixels).
  2. `TTPlanet_TileGF_Preprocessor` (mandatory per `PH5-10` — without it, Tile ControlNet
     hallucinates detail instead of following the source at any denoise above ~0.30).
  3. `ControlNetLoader` → `control_v11f1e_sd15_tile.pth`, applied to an SD1.5 checkpoint
     (`dreamshaper_8.safetensors` per `PH5-2`, or `realisticVision_v60B1VAE` as used in the
     weapon-texture doc — **not** `RealVisXL_V5.0` / any SDXL checkpoint, which is
     incompatible with SD1.5 Tile ControlNet per `PH5-1`).
  4. `KSampler` at **denoise 0.30–0.40** (skin textures are lower-res and simpler than weapon
     hero surfaces, so stay at the conservative end of the `PH5-1`/`comfyui-texture-pipeline.md`
     0.25–0.45 range rather than pushing toward 0.45). If seams visibly drift, drop to 0.25 and
     raise ControlNet weight to 0.85, exactly as the existing doc's "UV Verification" section
     already prescribes.
  5. Optional: an SDXL LoRA restyle pass (`PH5-9` — cel-shade, photoreal-slider, etc.) is a
     *separate* pipeline (`tile_sdxl_lora.json`) and should be treated as a distinct "style
     variant" output, not mixed into the same graph as the SD1.5 tile pass.
  6. `SaveImage` → re-pack to the exact filename `.skin` expects (`xaero.png` overwrite for an
     in-place default-skin restyle, or a new filename for a new named skin variant, e.g.
     `models/players/xaero/pantheon.png` + a matching new `.skin` file).

- **UV-critical regions to protect**: team-color patch boundaries, the sash front/back seam,
  and the head texture's face UV island — same verification step as
  `comfyui-texture-pipeline.md` already describes (overlay the model's UV layout on the
  processed output and confirm no seam drift before accepting a batch).

- **Packing into a pk3**: identical mechanism to `pantheon_ads.py` and the Phase-5 weapon
  pipeline — write the new/overwritten PNG/TGA files at
  `models/players/xaero/<name>.png` inside a zip named `zzz_<something>.pk3` (or into the
  wolfcam gamedir the way `pantheon_ads.py` does for ad boards, whichever search path this
  asset needs to win over — same "gamedir beats baseq3, zzz_zz sorts last" logic already
  documented for ad boards applies to skin textures too). No new code pattern is needed here;
  it's the same `zipfile.ZipFile(..., "w", ...)` call already used in this repo, pointed at a
  new texture rather than a new banner JPEG.

- **Automation loop this actually supports** (the "pick a style variant → apply → capture"
  goal from the brief): a batch script analogous to `full_overnight.py` that (1) takes a style
  name, (2) runs the fixed ComfyUI graph above against each of `xaero.png`/`blue.png`/
  `red.png`/`bright.png`/`sport.tga`/head textures, (3) writes outputs into a
  `photoreal/pipelines/<style>/models/players/xaero/` tree exactly like the existing weapon
  pipeline's `photoreal/pipelines/{pipeline_name}/{rel_path}.png` convention (`PH5-8`), and
  (4) packs the result into a `zzz_skin_<style>.pk3` is a same-shape extension of code that
  already exists and already ships — this is genuinely close to "truly automatic" for T1.

---

## 5. Full custom model replacement (T3) — what it needs, and open tools

For an ambitious ask — replacing Xaero's mesh entirely with an AI/3D-generated mesh — the
realistic pipeline is:

1. **Generate a mesh** from a text prompt or reference image using a text-to-3D / image-to-3D
   model. As of my knowledge, actively discussed open tools in this space include:
   - **TripoSR** — MIT-licensed, single-image → mesh, very fast (seconds), but known for
     baking lighting into the output texture and being lower-fidelity — treat speed as the
     selling point, not final quality.
   - **InstantMesh** — sparse-view large-reconstruction-model approach (multi-view diffusion
     → mesh), produces a connected-polygon mesh suitable as a starting point for
     texturing/animation work (as opposed to point-cloud-only output).
   - **Hunyuan3D** (Tencent, open-weights releases) — two-stage (mesh generation, then a
     separate texture/PBR-paint pass), pitched as locally runnable with commodity VRAM,
     competitive quality among open options as of recent releases.
   - This is a genuinely fast-moving space (new models/checkpoints landing every few months)
     — treat the above as "known names to start evaluating from," not a settled
     recommendation, and re-check current leaderboards/community consensus before committing
     engineering time to one.
2. **Retopologize** the raw generated mesh in Blender to a game-appropriate low-poly topology
   — AI mesh output is essentially never animation-ready or Q3-appropriate-density as
   generated; this is a full manual (or semi-automated retopo-tool-assisted) modeling pass.
3. **Decimate/budget to Q3-era poly counts.** The actual counts in this pak are a useful
   reference target: `upper.md3`'s largest surface (`u_armbase`) is 71 verts/47 tris;
   `lower.md3`'s `l_legs` is 274 verts/324 tris. A full custom player model in the same spirit
   should land in a comparable low-hundreds-of-triangles-per-surface range, not a modern
   high-poly scan/generation output (which can be 10,000+ triangles).
4. **Rig and animate to the fixed contract.** MD3 has no bones (§2.2), so "rigging" here means
   either (a) rig conventionally in Blender, bake all 30 `animation.cfg` states, then bake the
   armature deformation down into per-frame Shape Keys for MD3 export, or (b) retarget motion
   from the existing Xaero shape-key animation onto the new topology (harder, since retargeting
   vertex-morph animation across differing topology isn't a standard supported workflow the
   way skeletal retargeting is — this would likely require a custom Blender script, not an
   off-the-shelf tool).
5. **Rebuild tag placement** (`tag_head`, `tag_torso`, `tag_weapon`) per frame so weapon-in-hand
   and head/torso attachment look correct through the whole animation set.
6. **Export via one of the addons in §3.1** and verify every animation state in-engine.

**Effort rating**: this is correctly scoped as a **significant, multi-session project** —
realistically measured in weeks, comparable to producing an original custom Q3 player model
from scratch (which the mod community has always treated as a serious undertaking, AI mesh
generation notwithstanding — AI shortens step 1, it does not shorten steps 2–6).

---

## 6. Existing precedent in the Q3 modding community

- **AI-upscaled Quake 3 texture pack** (ModDB) — an existing released mod using 4x-ESRGAN
  texture upscaling (Manga109 model) on Quake 3 Arena's stock textures. Confirms ESRGAN-class
  upscaling is an established, already-shipped technique for this exact game, not a novel
  idea for this project. https://www.moddb.com/mods/ai-upscaled-texture-pack-for-quake-3-arena
- **AI-enhanced HD texture packs for Quake 1 and Blood: Fresh Supply** by modders
  'phredreeke' and 'The Awesome Sponge' — same id-Tech-era engine family, same
  upscale-then-repack approach. Referenced via DSOGaming coverage:
  https://www.dsogaming.com/news/ai-enhanced-hd-texture-packs-released-for-quake-1-blood-fresh-supply/
- **Quake 1 community retexture projects reportedly using ComfyUI directly** (SUPIR upscaler
  node) plus Automatic1111 for spot touch-ups, per community search results — i.e. the exact
  tool (ComfyUI) this project already has running is independently established in the wider
  Quake retexture community, not just internal to this repo.
- **Quake 2 Neural Upscale** and **Quake 4 4X AI Textures** (Topaz Gigapixel-based) — further
  confirmation that "run an AI upscaler over stock id-Tech texture packs and repack" is a
  mature, repeated pattern across the whole Quake engine family, going back further than this
  project's own Phase-5 work.
- **Generic Q3 skin-creation tutorials** (ModDB "Skinning For Newbies," atoolbox.wordpress.com
  walkthrough, Podcentral's tutorial) — all describe exactly the T1 mechanism confirmed in §2.4:
  edit/replace the texture file(s), write or copy a `.skin` file pointing at them, pack into
  `models/players/<name>/` inside a `.pk3`, drop in `baseq3/`. This is 20+-year-old, extremely
  well-trodden ground — there is no engine-level obstacle to what this project wants to do at
  the T1 tier.
- I found **no specific published tutorial combining Blender MD3 geometry edits with an
  AI-generated mesh source** (T3) for Quake 3 specifically — that combination appears to be
  ahead of documented community practice, consistent with §5's "significant project, not a
  quick swap" rating. The MD3 Blender tooling (§3.1) and the image/text-to-3D tooling (§5)
  are each independently mature; nobody appears to have publicly written up chaining them for
  a Q3 player model.

---

## Sources

- [neumond/blender-md3](https://github.com/neumond/blender-md3) — MD3 Blender addon, Shape-Key animation, Empty-object tags
- [hypov8/blender-md3_2.7-3.2](https://github.com/hypov8/blender-md3_2.7-3.2) — MD3 Blender addon, notes incomplete exporter / rigged-model animation issues
- [SomaZ/Blender_BSP_Importer](https://github.com/SomaZ/Blender_BSP_Importer) — id Tech 3 BSP importer bundling MD3 import/export, Blender 2.93–4.2
- [MD3 Import/Export Using Blender 3.3 — JKHub](https://jkhub.org/tutorials/modeling/md3-importexport-using-blender-33-r185/)
- [Importing Q3A MD3 into Blender — icculus.org](https://www.icculus.org/~phaethon/q3/md3import/md3import.html)
- [TripoSR](https://triposr.org/) — MIT-licensed single-image-to-mesh
- [InstantMesh paper (arXiv 2404.07191)](https://arxiv.org/pdf/2404.07191)
- [Hunyuan3D 1.0 paper (arXiv 2411.02293)](https://arxiv.org/pdf/2411.02293)
- [AI upscaled texture pack for Quake 3 Arena — ModDB](https://www.moddb.com/mods/ai-upscaled-texture-pack-for-quake-3-arena)
- [AI-enhanced HD Texture Packs for Quake 1 & Blood: Fresh Supply — DSOGaming](https://www.dsogaming.com/news/ai-enhanced-hd-texture-packs-released-for-quake-1-blood-fresh-supply/)
- [Skinning For Newbies: Part 1 — ModDB](https://www.moddb.com/games/quake-iii-arena/tutorials/skinning-for-newbies-part-1)
- [How to make and use a skin for Quake 3 Arena — atoolbox.wordpress.com](https://atoolbox.wordpress.com/2011/02/14/how-to-make-and-use-a-skin-for-quake-3-arena/)
- In-repo: `output/demo_v2/_wolfcam_staging/baseq3/pak00.pk3` (direct binary/zip inspection, read-only, this session)
- In-repo: `docs/reference/comfyui-texture-pipeline.md`, `CLAUDE.md` §Phase 5 (PH5-1..PH5-10), `creative_suite/engine/pantheon_ads.py`
