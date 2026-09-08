# ComfyUI Asset Pipeline — Disk Audit

> Audit date: 2026-08-31 | **Read-only audit.** No database was written, no image was
> generated, no file was modified. All SQLite access used `file:...?mode=ro` URIs.
> Scope: audit what actually exists on disk against `CLAUDE.md` §Phase 5 (`PH5-1..PH5-10`)
> and `docs/reference/model-texture-pipeline-research.md`.

**Verdict summary**

| Check | Result |
|---|---|
| PH5-7 category routing (FX categories must be `upscale_only` only) | **PASS on disk** — zero style-pipeline output under any FX category |
| Output dimensions vs originals | **PASS** — 40/40 sampled at exact 4× original, 0 deviations |
| File corruption / black / wrong-format | **PASS** — 0 corrupt, 0 flat, 0 near-black in sampled sweep |
| Structural fidelity (UV layout survival) | **PASS** — all 10 style pipelines ≥ 0.87 mean structural correlation |
| Alpha-channel preservation | **FAIL** — 90/90 alpha-bearing assets lost alpha (100% failure rate) |
| DB ↔ disk consistency | **FAIL** — 189 `renders` rows point at files that no longer exist |
| Source-parameter consistency within a pipeline | **FAIL** — 16 rows mixed `upscaled` source into otherwise `original` runs |
| Asset index coverage | **GAP** — 437 staged files present on disk but absent from `assets.db` |
| `CLAUDE.md` PH5-2 model table vs shipped workflows | **STALE** — production models are not the ones documented |

---

## 1. What exists

### 1.1 Workflows — 21 JSON files, not the "8" in `CLAUDE.md`

`creative_suite/comfy/workflows/` holds **21** workflow JSONs. `CLAUDE.md`'s folder map says
"8 workflow JSONs (upscale_only, tile_*, img2img_*)" — that count is stale by 13 files.
Model bindings extracted directly from each JSON (`ckpt_name` / `control_net_name` /
`lora_name` / `model_name` inputs), with the file's SHA-256 prefix:

| Workflow file | sha256[:12] | Checkpoint | ControlNet | LoRA | Upscaler | TTPlanet pre? | Powers pipeline |
|---|---|---|---|---|---|---|---|
| `upscale_only.json` | `2fa6cd70de68` | — | — | — | `4x-UltraSharp.pth` | n/a | `upscale_only` |
| `style_photoreal.json` | `495a0287f062` | `juggernautXL_ragnarokBy` | `TTPLANET_..._Tile_realistic_v2_fp16` | — | — | yes | `photoreal` |
| `style_chromatic.json` | `b5fecede54b1` | `zavychromaxl_v100` | `TTPLANET_..._Tile_realistic_v2_fp16` | — | — | yes | `chromatic` |
| `style_edge_chrome.json` | `5d08a1ce9c58` | `zavychromaxl_v100` | `controlnet-canny-sdxl-1.0` | — | — | no | `edge_chrome` |
| `style_depth_realism.json` | `42b96f7447e3` | `juggernautXL_ragnarokBy` + `depth_anything_v2_vitl` | `controlnet-depth-sdxl-1.0` | — | — | no | `depth_realism` |
| `style_zavy_depth.json` | `0dc9ce9060ef` | `zavychromaxl_v100` + `depth_anything_v2_vitl` | `controlnet-depth-sdxl-1.0` | — | — | no | `zavy_depth` |
| `style_isometric.json` | `41e771a395a2` | `stylized-isometric-sdxl` (**actually SD1.5**) | `control_v11f1e_sd15_tile.pth` | — | — | no | `isometric` |
| `style_painterly.json` | `78fbf8c000b1` | `dreamshaper_8` | `control_v11f1e_sd15_tile.pth` | — | — | no | `painterly` + `dreamlike` |
| `style_pixel_art.json` | `9ae34663a751` | `juggernautXL_ragnarokBy` | `TTPLANET_..._Tile_realistic_v2_fp16` | `pixel-art-xl` | — | yes | `pixel_art` |
| `style_neon.json` | `e36523106ffb` | `zavychromaxl_v100` | `controlnet-canny-sdxl-1.0` | `NeonifyV2-4Extreme` | — | no | `neon` |
| `tile_controlnet_sdxl.json` | `3c968d4338cc` | `juggernautXL_ragnarokBy` | `TTPLANET_..._Tile_realistic_v2_fp16` | — | `4x-UltraSharp.pth` | yes | `tile_d35..d80` (E2E) |
| `tile_controlnet_sd15.json` | `5d509a54fe91` | `dreamshaper_8` | `control_v11f1e_sd15_tile.pth` | — | `4x-UltraSharp.pth` | no | (PH5-1 reference graph) |
| `tile_sdxl_lora.json` | `6c262ad6ebe2` | `juggernautXL_ragnarokBy` | `TTPLANET_..._Tile_realistic_v2_fp16` | `{{lora_name}}` | `4x-UltraSharp.pth` | yes | LoRA suite (PH5-9) |
| `tile_refine_sdxl.json` | `f616051de941` | `juggernautXL_ragnarokBy` | `TTPLANET_..._Tile_realistic_v2_fp16` | — | — | no | unused |
| `tile_refine_sd15.json` | `7c3d88d89178` | `dreamshaper_8` | `control_v11f1e_sd15_tile.pth` | — | — | no | unused |
| `cartoon_sdxl.json` | `e122f1df3536` | `juggernautXL_ragnarokBy` | `TTPLANET_..._Tile_realistic_v2_fp16` | — | `4x-UltraSharp.pth` | yes | `cartoon` (E2E) |
| `cel_shade_sdxl.json` | `9e50ac55d909` | `juggernautXL_ragnarokBy` | `controlnet-canny-sdxl-1.0` | — | `4x-UltraSharp.pth` | no | `cel_shade` (E2E) |
| `ink_etching_sdxl.json` | `22e5ae4ccaf1` | `juggernautXL_ragnarokBy` | `controlnet-canny-sdxl-1.0` | — | `4x-UltraSharp.pth` | no | `ink_etching` (E2E) |
| `concept_art_sdxl.json` | `687ec41fa307` | `RealVisXL_V5.0_fp16` | — | — | `4x-UltraSharp.pth` | no | `concept_art` (E2E) |
| `img2img_sdxl.json` | `3a3f5bfe46b5` | `RealVisXL_V5.0_fp16` | — | — | — | no | unused (PH5-1 "wrong" ref) |
| `img2img_sdxl_canny.json` | `227b6de93960` | `RealVisXL_V5.0_fp16` | `controlnet-canny-sdxl-1.0` | — | — | no | unused |

**Rule-compliance notes on the above:**

- **`PH5-1` is respected.** No workflow pairs an SDXL checkpoint with the SD1.5 Tile
  ControlNet. `style_isometric.json` looks like a violation at a glance
  (`stylized-isometric-sdxl.safetensors` + `control_v11f1e_sd15_tile.pth`) but its own
  `_description` records that this was found and fixed at template v4: *the model is SD1.5
  despite the "sdxl" in its filename.* This is a genuine trap — a checkpoint filename that
  lies about its architecture — and is the reason the proposed manifest carries an explicit
  `architecture` field rather than inferring it from the filename.
- **`PH5-2`'s model table is stale.** It documents `dreamshaper_8` + `control_v11f1e_sd15_tile`
  as the correct SD1.5 tile pairing. That pairing now powers only `painterly` and `dreamlike`
  (1,600 of 8,637 style renders). The production majority runs **`juggernautXL_ragnarokBy` or
  `zavychromaxl_v100` against `TTPLANET_Controlnet_Tile_realistic_v2_fp16`** — an SDXL tile
  ControlNet that does not appear anywhere in `PH5-2`. Neither `zavychromaxl_v100`,
  `TTPLANET_Controlnet_Tile_realistic_v2_fp16`, `depth_anything_v2_vitl`,
  `controlnet-depth-sdxl-1.0`, `controlnet-canny-sdxl-1.0`, `stylized-isometric-sdxl`, nor
  `pixel-art-xl` is listed in the `PH5-2` "Models on disk" table.
- **`PH5-10` over-generalizes.** It states `TTPlanet_TileGF_Preprocessor` is *mandatory for
  tile workflows*. In practice only 6 of 21 workflows carry it, and the split is principled,
  not accidental: every workflow using the **SDXL** `TTPLANET_*` tile ControlNet includes the
  preprocessor; every workflow using the **SD1.5** `control_v11f1e_sd15_tile` deliberately
  omits it (`style_isometric.json` states "No preprocessor needed for SD1.5 tile"). The rule
  should be narrowed to "mandatory for the TTPLANET SDXL tile ControlNet", which is what the
  code actually enforces.

### 1.2 LoRA manifest — 6 styles confirmed, but only 2 are on disk

`creative_suite/comfy/loras/manifest.json` declares exactly **6 styles**, matching `CLAUDE.md`:

| Style | Status | File |
|---|---|---|
| `photoreal_boost` | `DOWNLOADED` | `sdxl_photorealistic_slider_v1-0.safetensors` |
| `cel_shade` | `DOWNLOADED` | `NeonifyV2-4Extreme.safetensors` |
| `extremely_detailed` | `DOWNLOAD_NEEDED` | `extremely detailed.safetensors` |
| `painterly` | `DOWNLOAD_NEEDED` | (no repo pinned — value is a literal `search:` string) |
| `anime` | `DOWNLOAD_NEEDED` | (no repo pinned — value is a literal `search:` string) |
| `retro_quake` | `TRAIN_NEEDED` | needs custom training on the pak00 corpus |

Two gaps worth recording:

1. **The manifest is not the source of truth for LoRAs actually in use.** `style_pixel_art.json`
   loads `pixel-art-xl.safetensors`, which appears nowhere in `manifest.json`, yet it produced
   956 renders. Conversely `manifest.json`'s `pipeline_combos` block references
   `tile_sdxl_lora.json` with `extremely_detailed` — a LoRA that has never been downloaded, so
   that combo has never run.
2. **Two entries have unresolvable `hf_repo` values.** `painterly` and `anime` carry
   `"search:huggingface.co ..."` placeholder strings rather than repo IDs, so
   `download_loras.py` cannot resolve them.

### 1.3 `photoreal/assets.db` — 3 tables, and already ~70% of the requested manifest

This is the key finding for the schema task: **the manifest the spec asks for largely exists
already.** Actual schema on disk (5.4 MB DB):

```sql
CREATE TABLE assets (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    rel_path  TEXT    NOT NULL UNIQUE,
    category  TEXT    NOT NULL,
    route     TEXT    NOT NULL,          -- 'surface' | 'fx'  (PH5-7 routing decision)
    width     INTEGER,
    height    INTEGER,
    sha256    TEXT,
    source    TEXT    NOT NULL DEFAULT '',
    file_size INTEGER
);
CREATE TABLE renders (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id    INTEGER NOT NULL REFERENCES assets(id),
    pipeline    TEXT    NOT NULL,
    denoise     REAL,
    style       TEXT,                    -- present but 100% NULL (14,413/14,413)
    output_path TEXT    NOT NULL UNIQUE,
    created_at  TEXT    DEFAULT (datetime('now')),
    status      TEXT    DEFAULT 'ok',
    source_type TEXT    NOT NULL DEFAULT 'original'   -- 'original' | 'upscaled'
);
CREATE TABLE category_config (
    id INTEGER PRIMARY KEY, category TEXT NOT NULL, pipeline TEXT NOT NULL,
    denoise REAL, enabled INTEGER NOT NULL DEFAULT 1, notes TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(category, pipeline)
);
```

Note the live schema has **drifted from `full_overnight.py::_init_db`**, which declares
`denoise REAL NOT NULL`, `style TEXT NOT NULL DEFAULT 'photoreal'`, `output_path` without
`UNIQUE`, a `UNIQUE(asset_id, pipeline, style)` constraint, and an `added_at` /`generated_at`
pair. The DB on disk has none of those constraints and instead carries `status` and
`source_type` columns the initializer never creates. A fresh `assets.db` built by
`full_overnight.py` today would **not** match the one in the repo — `build_uhd_pk3.py` queries
`r.status='ok'`, which would fail on a freshly initialized DB. This is a latent breakage,
independent of the new workstream.

`category_config` holds exactly **one row**: `('players', 'cel_shade', 0.5, enabled=0,
'face distorts; try cfg=6.5 str=0.65 if enabled')`. The table is a working per-category
override mechanism but is effectively unused.

### 1.4 Assets and renders — inventory

**5,776 assets indexed**, routed per `PH5-7`:

| Category | Route | Count | | Category | Route | Count |
|---|---|---:|---|---|---|---:|
| `textures` | surface | 3,742 | | `mapobjects` | fx | 124 |
| `players` | surface | 903 | | `powerups` | fx | 87 |
| `ui` | fx | 454 | | `icons` | fx | 63 |
| `gfx` | fx | 157 | | `weaphits` | fx | 43 |
| `phase5` | surface | 107 | | `weapons2` | surface | 39 |
| `sprites` | fx | 34 | | `wolfcam_hud` | fx | 23 |

**14,413 render rows across 20 pipelines**, all `status='ok'`. DB count vs actual files on disk:

| Pipeline | denoise | DB rows | Files on disk | Delta |
|---|---:|---:|---:|---:|
| `upscale_only` | 1.0 | 5,776 | 5,776 | 0 |
| `photoreal` | 0.35 | 1,000 | 932 | **−68** |
| `depth_realism` | 0.40 | 1,000 | 932 | **−68** |
| `pixel_art` | 0.55 | 956 | 903 | **−53** |
| `chromatic` | 0.35 | 800 | 800 | 0 |
| `dreamlike` | 0.55 | 800 | 800 | 0 |
| `edge_chrome` | 0.45 | 800 | 800 | 0 |
| `isometric` | 0.45 | 800 | 800 | 0 |
| `neon` | 0.50 | 800 | 800 | 0 |
| `painterly` | 0.35 | 800 | 800 | 0 |
| `zavy_depth` | 0.40 | 800 | 800 | 0 |
| `tile_d35` / `tile_d50` | 0.35 / 0.50 | 11 / 11 | 11 / 11 | 0 |
| `tile_d60` / `d70` / `d80` | 0.6/0.7/0.8 | 7 each | 7 each | 0 |
| `ink_etching` | 0.70 | 11 | 11 | 0 |
| `cartoon` | 0.65 | 10 | 10 | 0 |
| `concept_art` | 0.75 | 10 | 10 | 0 |
| `cel_shade` | 0.65 | 7 | 7 | 0 |

The `tile_d*` ladder ran on **11 `players` textures only** (the `anarki` set) — it is an
E2E-scale experiment, not a shipped pipeline. The 10 named style pipelines are the production
batch (`PH5-8`'s documented pipeline-name list — `upscale_only`, `tile_d35..d80` — is stale;
the shipped names are `photoreal`, `chromatic`, `edge_chrome`, `depth_realism`, `isometric`,
`painterly`, `dreamlike`, `zavy_depth`, `pixel_art`, `neon`).

### 1.5 E2E gallery — real, but under-reporting and stale

`photoreal/e2e/index.html` (16.8 KB) is a **genuine** before/after comparison: 11 category
directories × 14 real PNGs each = 154 files, each row showing the true original from
`../assets/...` beside its generated variants. `PH5-4`'s requirement ("must show before/after
for all 11 categories") is met. Three defects:

1. **Stale prose.** The header text describes "Pipeline B: ControlNet-Tile denoise=0.15 —
   dreamshaper8 SD1.5" and "Pipeline C: denoise=0.30". The table columns actually rendered
   say "JuggernautXL + TTPLanet, denoise=0.35" and "denoise=0.50". A reviewer signing off on
   this gallery is reading a description of a pipeline that did not produce the images.
2. **Duplicate row.** `texture_wall` / `authors.png` appears twice, as the last two identical
   `<tr>` blocks. 12 rows render for 11 categories.
3. **Under-reports by 10/14.** Each category directory holds 14 variants
   (`cartoon`, `cel_shade`, `concept_art`, `ink_etching`, `tile_d35`, `tile_d35_cel_shade`,
   `tile_d35_photoreal`, `tile_d35_ultra_det`, `tile_d50`, `tile_d60`, `tile_d70`, `tile_d80`,
   `upscale_only`, `original`) but the gallery displays only 4 of them. The LoRA-variant
   outputs (`tile_d35_*`) and the high-denoise ladder (`d60/d70/d80`) were generated and have
   never been shown for sign-off.

---

## 2. Spot-check findings

Sample sizes are stated per check. Nothing was fixed; this section reports only.

### 2.1 Dimensions vs originals — **PASS**

40 randomly sampled assets, comparing `upscale_only` output to the staged original:
**40/40 at exactly 4× the source in both axes, 0 deviations, 0 corrupt files.**

A 3-file × 6-pipeline cross-sweep (`hunter/bright2_f.png`, `janet/brightglow2.png`,
`hunter/red_h.png`) confirms every style pipeline emits at the same 4× resolution as
`upscale_only` — i.e. `--twopass` was used correctly for the production batch, feeding the
CNN-upscaled image into the diffusion pass rather than the raw original.

No file in any sample was flat-colour, near-black, or unreadable by PIL.

### 2.2 Structural fidelity — **PASS**

Because "does diffusion destroy the UV layout" is the question `PH5-7` exists to answer, I
measured it rather than eyeballing it: Pearson correlation of 64×64 grayscale downsamples,
each style output against its own `upscale_only` sibling, on 12 random `players` textures.
1.0 = structurally identical; below ~0.6 would indicate the ControlNet lost the source.

| Pipeline | mean | min | Pipeline | mean | min |
|---|---:|---:|---|---:|---:|
| `photoreal` | 0.986 | 0.943 | `isometric` | 0.959 | 0.873 |
| `chromatic` | 0.985 | 0.949 | `dreamlike` | 0.948 | 0.871 |
| `painterly` | 0.983 | 0.946 | `depth_realism` | 0.924 | 0.759 |
| `pixel_art` | 0.973 | 0.911 | `zavy_depth` | 0.916 | 0.737 |
| | | | `edge_chrome` | 0.897 | 0.724 |
| | | | `neon` | 0.875 | 0.728 |

Every pipeline holds ≥ 0.87 mean. The tile/canny/depth ControlNets are doing their job and
UV layout survives across the board. Notably `dreamlike` (denoise 0.55, SD1.5 tile, **no**
TTPlanet preprocessor — the theoretically riskiest shipped combination per `PH5-10`) scores
0.948, so the preprocessor's absence on the SD1.5 path is not causing hallucination in
practice. The lowest scores (`neon`, `edge_chrome`) are canny-ControlNet pipelines where
lower structural correlation is the intended stylistic effect, not a defect.

### 2.3 Alpha channel — **FAIL (100% loss rate)**

Every asset whose staged source carries an alpha channel loses it in the render:

| Category | Assets | Alpha-bearing sources | Alpha lost |
|---|---:|---:|---:|
| `phase5` | 107 | 69 | **69** |
| `wolfcam_hud` | 23 | 21 | **21** |
| all others | 5,646 | 0 | 0 |
| **TOTAL** | **5,776** | **90** | **90** |

Every `RGBA` source became `RGB` in `upscale_only`. There is no partial failure — the rate is
90/90.

**The loss compounds at a second, earlier point.** The `pak00` categories show 0 alpha-bearing
sources, which is itself the bug: sampling 400 TGAs directly from
`output/demo_v2/_wolfcam_staging/baseq3/pak00.pk3` finds **257 of 400 are RGBA**
(e.g. `gfx/2d/crosshair20.tga`…`crosshair25.tga`). The staged PNG copies of those exact files —
`photoreal/assets/pak00/gfx/2d/crosshair20.png`, `crosshair24.png`,
`pak00/sprites/balloon4.png` — are all `RGB`. **Alpha was already discarded during the
pak00 → PNG extraction step, before ComfyUI ever saw the images.** pak00 holds 497 TGAs
overall (plus 3,768 JPG and 1,819 PNG).

**Why this matters for the pk3 delivery path:** `build_uhd_pk3.py::convert()` writes each
replacement back at the *original* in-pak extension. Its RGBA branch
(`img.convert("RGBA") if img.mode in ("RGBA","LA","P")`) can never fire, because no render is
ever RGBA — so an alpha-bearing `.tga` would ship as an opaque TGA and render as a solid
block in-game. The consequence is currently contained only because `build_uhd_pk3.py` defaults
to `--categories textures players weapons2` and its docstring deliberately leaves FX sheets
stock ("alpha-edge fidelity on explosions and beams outranks resolution"). That containment is
a default argument, not an enforced guard: `--categories gfx sprites` would ship broken
transparency today with no error. Any broadening of pack scope must fix extraction first.

### 2.4 DB ↔ disk divergence — **FAIL (189 orphan rows)**

189 `renders` rows reference `output_path` values with no file on disk. Their distribution is
completely diagnostic:

| Orphan path prefix | Count |
|---|---:|
| `phase5_png/icons/...` | 174 |
| `phase5_png/gfx/...` | 15 |

**Every single orphan is a `phase5_png/gfx/*` or `phase5_png/icons/*` path** — precisely the
set that `full_overnight.py`'s `_PHASE5_FX_SUBDIRS = frozenset(["gfx", "icons"])` rule
(labelled "PH5-7 subdir split 2026-06-04") later reclassified as FX/shape-critical. The
sequence is clear: those files were style-rendered before the phase5 subdir rule existed, the
offending output files were deleted from disk when the rule landed, **and the DB rows were
left behind**.

So the process-drift check has a two-part answer:

- **On disk: clean.** Every FX-routed category (`weaphits`, `gfx`, `icons`, `ui`,
  `wolfcam_hud`, `powerups`, `mapobjects`, `sprites`) has `upscale_only` output and nothing
  else. Zero stale `tile_d50`+ output is sitting around. The cleanup was done correctly.
- **In the DB: 189 stale rows still assert PH5-7 violations that no longer exist.** Any
  consumer that trusts `assets.db` — including `build_uhd_pk3.py`, which does
  `SELECT ... JOIN renders` — sees renders that aren't there. `build_uhd_pk3.py` happens to
  survive this because it re-checks `src.exists()` and files the row under
  `skipped: "render missing on disk"`, but that is defensive luck, not integrity.

The inverse direction is clean: **0** `assets` rows point at a missing source file.

### 2.5 Mixed generation parameters inside one pipeline — **FAIL (16 rows)**

`renders.source_type` is `'original'` for 14,397 rows and `'upscaled'` for 16. Those 16 are
not spread evenly — they are 3–4 specific files repeated across 5 pipelines:

```
tile_d35 / tile_d50 / cartoon / concept_art / ink_etching
  → anarki/bright_b.png, anarki/bright_g.png, anarki/bright_h.png (+ bright2_h for ink_etching)
```

The dimension evidence confirms the mismatch. Within the *same* `tile_d35` run, on the *same*
category, in the *same* directory:

| Asset | original | `upscale_only` | `tile_d35` | scale vs original |
|---|---|---|---|---|
| `anarki/anarki.png` | 256×256 | 1024×1024 | 512×512 | 2× (from original) |
| `anarki/bright.png` | 512×512 | 2048×2048 | 1024×1024 | 2× (from original) |
| `anarki/bright_b.png` | 256×256 | 1024×1024 | **2048×2048** | **8× (from upscaled)** |
| `anarki/bright_h.png` | 256×256 | 1024×1024 | **2048×2048** | **8× (from upscaled)** |

8 of the 11 files in that pipeline ran single-pass from the original; 3 ran two-pass from the
CNN-upscaled image. **This is a resumability artifact.** `full_overnight.py` skips work when
the output file already exists — a check that cannot detect that the *parameters* changed. A
later `--twopass` run resumed a non-twopass run, found 8 files already present, skipped them,
and generated only the 3 missing ones under the new regime. The DB faithfully recorded the
divergence in `source_type`; nothing flagged it.

This single finding is the strongest argument for the schema in
`asset_manifest_schema.md`: **resume keyed on output-path existence silently mixes parameter
regimes, and only a stored `workflow_hash` + `generation_parameters` digest can detect it.**

A secondary artifact of the same run: non-power-of-two sources are rounded to the latent
grid. `anarki_g_fx.png` at 54×32 becomes 104×64 in `tile_d35` (54×2 = 108, floored to the
nearest multiple of 8), shifting aspect from 1.6875 to 1.625 — a ~3.7% horizontal squeeze.
The `upscale_only` CNN path is exact (216×128) and unaffected.

### 2.6 Index coverage gap — 437 staged files unindexed

`photoreal/assets/` holds **6,213** files; `assets.db` indexes **5,776**. The 437-file gap:

| Unindexed tree | Count |
|---|---:|
| `pak00/levelshots` | 323 |
| `pak00/models` (not under a routed subdir) | 54 |
| `pak00/menu` | 48 |
| `pak00/env` | 12 |

`levelshots`, `menu`, and `env` have no entry in either `_FX_LABELS` or `_SURFACE_LABELS`, so
`full_overnight.py`'s scanner never picked them up. For the "PANTHEON Engine & AI Asset
Overhaul" these are not negligible: `levelshots` are the map-preview images and `env` is the
**skybox** set — both are high-visibility on-screen surfaces for a cinematic overhaul, and
skyboxes are the classic case where seam-aware (tileable) generation is mandatory. Note also
`CLAUDE.md` cites the pak00 corpus as 6,190 files; 6,213 are staged.

---

## 3. pk3 packing — does the ad-board pattern generalize?

There are **two** pk3 packers in the repo, and the audit answer is that the one named in the
brief is the less general of the pair.

### 3.1 `creative_suite/engine/pantheon_ads.py::build_pack` — proven, but ad-board-specific

```python
PK3 = REPO_ROOT/"output"/"demo_v2"/"_wolfcam_staging"/"wolfcam-ql"/"zzz_zz_pantheon_ads.pk3"
with zipfile.ZipFile(PK3, "w", zipfile.ZIP_STORED) as zf:
    for aspect, bid in banner_set.items():
        zf.write(jpg, f"textures/ad_content/ad{aspect}.jpg")
```

The *mechanism* is exactly right and is the pattern to keep: build a zip, name it `zzz_*`,
drop it in the wolfcam gamedir, let search-path precedence do the rest. Its search-path
reasoning is documented in the module docstring and is the most valuable part:

> gamedir beats baseq3, and `zzz_zz` sorts after the `zzz_uhd_*` packs whose upscaled house
> ads otherwise win. The pack contains ONLY the four ad_content jpgs — it cannot override
> unrelated map textures.

That is a real, working **two-axis priority scheme** (gamedir over baseq3; lexicographic
`zzz_zz` over `zzz_uhd`) plus a deliberate **minimal-blast-radius** rule. Both generalize.

Four things in it do **not** generalize, all ad-board-specific:

1. `PK3` is a module-level constant — one hardcoded destination, one pack per process.
2. The zip contents are a fixed 4-entry map (`ad1x1/2x1/4x1/8x1`) derived from the `FINAL`
   aspect dict; there is no general "asset → in-pak path" resolution.
3. Everything upstream (`CATALOG`, `assign_set`, `BY_ASPECT`, `ASSIGN_LOG`) is banner
   *generation* logic, not packing logic, and the two are fused in one module.
4. It is **not a ComfyUI pipeline at all** — banners are drawn procedurally with PIL. Any
   registry that must cover `BANNER_GENERATION` alongside the ComfyUI pipelines has to model
   a non-ComfyUI generator kind. This is a real constraint on the registry design, not an
   afterthought.

### 3.2 `creative_suite/comfy/build_uhd_pk3.py::run` — the actually-general packer

This is the one to build on. It already solves the hard problems:

- **DB-driven**, not hardcoded: `SELECT a.rel_path, r.output_path FROM assets a JOIN renders r
  WHERE r.pipeline='upscale_only' AND r.status='ok' AND a.category IN (...)`.
- **Extension-priority trap handled.** Its docstring names the exact failure it avoids —
  shipping a `.png` where the original was `.jpg`/`.tga` means the asset "exists" but never
  loads. `pak00_index()` builds an extension-stripped map of real pak00 names and every
  replacement is written back at the original filename and extension.
- **Size splitting** at 1.8 GB per pk3, because the engine's zip reader has no zip64.
- **`MAX_DIM = 2048`** clamp with LANCZOS downscale, matching the engine texture cap.
- **Emits a manifest** (`output/demo_v2/uhd_pk3_manifest.json`) with `included` / `skipped` /
  `pk3s` and per-skip reasons.
- **`--offset`** so successive runs don't clobber earlier pack numbering.

**Verdict: it generalizes cleanly to multiple asset families in one or several packs**, with
three gaps to close:

1. **Pack identity is not persisted.** `MANIFEST_OUT` is a single fixed path and its own
   comment says *"overwritten per run; offset keeps pk3 names distinct."* Run it twice for two
   families and the first family's manifest is gone, even though its `.pk3` files still sit in
   the gamedir. There is no record anywhere of which pack a given render shipped in. This is
   the single strongest argument for a persisted `packs` + `pack_members` pair in the schema.
2. **Pack selection is a category filter, not a family concept.** `--categories` maps directly
   onto `assets.category`, which is a *source-tree* label (`models/players/…` → `players`). A
   pack like `XAERO_PANTHEON` is a slice *within* `players`, and `WORLD_TILEABLE` spans
   `textures` + `env`. The schema needs `asset_family` as a separate axis from `category`.
3. **Only `pipeline='upscale_only'` is hardcoded in the query.** Any pack built from a style
   pipeline needs that to become a parameter.

The `zzz_` lexicographic priority scheme is currently **implicit** — it lives in one docstring
sentence and in the two names that happen to exist (`zzz_uhd_NN`, `zzz_zz_pantheon_ads`).
Adding a third and fourth family without writing the ordering down is where this breaks, so
the schema below makes `packs.load_priority` an explicit stored column.

---

## 4. Findings index

Ordered by severity. **Nothing in this section was acted on** — this is an audit.

| # | Severity | Finding |
|---|---|---|
| F1 | High | Alpha lost on 90/90 alpha-bearing assets, and additionally at the pak00→PNG extraction step (257/400 sampled TGAs are RGBA, staged as RGB). `build_uhd_pk3.convert()`'s RGBA branch is unreachable. Contained today only by a default `--categories` argument. |
| F2 | High | 189 orphan `renders` rows, all `phase5_png/gfx|icons` — DB asserts PH5-7 violations that were correctly deleted from disk. Disk is clean; the index is not. |
| F3 | High | Live `assets.db` schema has drifted from `full_overnight.py::_init_db`. A freshly initialized DB lacks `status` and `source_type`, which `build_uhd_pk3.py` queries. Latent breakage. |
| F4 | Medium | 16 renders mixed `source_type='upscaled'` into otherwise-original runs (8× vs 2× scale inside one pipeline). Resume-by-file-existence cannot detect a parameter change. |
| F5 | Medium | `build_uhd_pk3.py` overwrites its manifest every run; no persisted record of which pack any render shipped in. |
| F6 | Medium | 437 staged files unindexed, including all 12 `env` skyboxes and 323 `levelshots` — both high-visibility for a cinematic overhaul. |
| F7 | Low | `CLAUDE.md` PH5-2 model table omits 7 models actually in production use; PH5-8's pipeline-name list is stale; the folder map says 8 workflows where 21 exist. |
| F8 | Low | `PH5-10` over-generalizes: the TTPlanet preprocessor is required for the SDXL `TTPLANET_*` tile ControlNet, deliberately omitted on the SD1.5 `control_v11f1e_sd15_tile` path. |
| F9 | Low | E2E gallery prose describes a different pipeline than the images show; `texture_wall` row duplicated; 10 of 14 generated variants per category never displayed for sign-off. |
| F10 | Low | `loras/manifest.json` omits `pixel-art-xl` (in production, 956 renders) and carries two unresolvable `search:` placeholder repo IDs. |
| F11 | Info | Non-power-of-two sources are floored to the latent grid in diffusion pipelines (54×32 → 104×64, ~3.7% aspect squeeze). The CNN `upscale_only` path is exact. |
| F12 | Info | `category_config` holds exactly one row; the per-category override mechanism works but is unused. |

---

## 5. What this audit did not cover

- **No visual sign-off.** Structural correlation (§2.2) measures layout survival, not whether
  the output looks good. `PH5-4`'s human-approval gate is unaffected by this audit.
- **No ComfyUI runtime check.** `verify_comfyui.py` was not run; model *presence on the E:
  drive* was not verified, only the model *names referenced by workflow JSONs*.
- **Seam/tileability was not measured** on wall textures, which matters for `WORLD_TILEABLE`.
- **Sample sizes** are stated per check and are small by design (§2.1 n=40, §2.2 n=12,
  §2.3 full 5,776-asset scan, §2.4/§2.5 full DB scan).
