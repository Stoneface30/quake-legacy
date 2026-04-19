# Creative Suite — Design Spec

**Date:** 2026-04-17
**Status:** Draft (autonomous-loop defaults applied; awaits user review)
**Scope:** Phase 1.5 — ComfyUI-driven asset variant factory, MD3 preview, pk3 compilation, per-clip style switching at fragmovie render time.
**Out of scope (tracked separately):** Sprint 10 — engine 4K re-render + YouTube master encode (will live in its own spec).

---

## 1. One-Line Summary

A local web UI that turns any Quake Live texture / skin / model into an approved
variant via ComfyUI, stores accepted variants in an asset library, compiles them
into style-specific `zzz_*.pk3` overrides, and lets the fragmovie pipeline switch
style per-clip so T1 peaks, T2 backbone, and T3 filler can each carry a different
aesthetic (photoreal / pixel / cel / retro / cyberpunk).

---

## 2. Feature Sections

### 2.1 Asset Browser

Left pane of the UI. Tree view across categories:

- `weapons/` (world MD3, view MD3, projectiles, explosion sprites, muzzle flash)
- `skins/` (playermodels: sarge, xaero, visor, doom, ranger, keel, …)
- `textures/surfaces/` (map wall/floor/ceiling textures from baseq3 + `q3a-extracted/`)
- `textures/effects/` (smoke, lightning, rail trail, rocket trail, blood)
- `gfx/` (HUD, crosshair, scoreboard, menu backgrounds)
- `sounds/` (out of scope for v1 — pack schema supports it, UI tab disabled)

Click an asset → center pane loads preview (MD3 viewer for models, `<img>` for textures).

**Data source:** `docs/research/existing-assets-inventory-2026-04-17.md` already
inventoried 131 baseq3 pk3s, 4000 q3a-extracted files, 8700 ql-extracted files,
plus `FULL_CATALOG.json`. v1 ingests from `FULL_CATALOG.json`; no re-scan needed.

### 2.2 Preview Canvas

Center pane.

- **Textures:** side-by-side `<canvas>` — left is the current baseq3 original, right
  is the selected variant. Zoom + pan synced between both. Pixel-ruler overlay
  optional.
- **MD3 models:** embedded `md3viewer` Three.js canvas (already built). Uses the
  new `/api/md3/frame` endpoint. Turntable button spins the model. Lighting
  sliders exposed (ambient/key/fill/rim/rim_power) already added in L85.
- **Animated models (weapon view, player):** playback scrubber over the
  animation.cfg frame ranges (`IDLE`, `DEATH_1`, `LEGS_RUN`, …). Research in
  `docs/research/md3-animation-system-2026-04-17.md` documents the MD3
  morph-target flow; the viewer caches per-frame interpolated geometry.

### 2.3 ComfyUI Variant Generator

Right pane.

- Selected asset appears as "Input image."
- Dropdown: **Style Pack** (see § 2.5). Picking a pack auto-populates workflow id,
  prompt prefix, negative prompt, denoise ceiling, and optional ControlNet.
- Text area: additional user prompt ("more rust," "add scratches," "ice theme").
  Final prompt sent to ComfyUI = `pack.prompt_prefix + " " + user_prompt`.
- Optional: **Ollama prompt assist** button → POSTs to local `gemma3:4b-vision`
  with the input image asking "suggest 3 prompt variations that would enhance
  this texture for a <style pack name> fragmovie." Returns 3 clickable chips.
  Gemma is optional; UI works without it.
- "Generate" button → POSTs to `/api/comfy/queue` which relays to ComfyUI
  `/prompt`, polls `/history/{job}`, streams progress over websocket.
- Result grid below: every generation for this asset ever, newest first.
  Each tile: thumbnail, pack badge, timestamp, ✓ Approve / ✗ Reject / ⟳ Re-roll.

### 2.4 Approval Loop

- ✓ Approve → variant row gets `approved_at` timestamp, PNG promoted into the
  asset library, thumbnail cached.
- ✗ Reject → variant kept in history (so you know what failed) but flagged out
  of future pk3 builds.
- ⟳ Re-roll → reuses same prompt + pack with new seed.

### 2.5 Style Packs (core concept)

A **Style Pack** is a named aesthetic bundle. Every variant belongs to exactly
one pack. Every pack compiles to its own `zzz_<slug>.pk3`. The fragmovie pipeline
picks one pack per clip at render time.

Seeded v1 packs:

| slug                | display name         | workflow         | denoise | prompt prefix                                                       |
|---------------------|----------------------|------------------|---------|---------------------------------------------------------------------|
| `photoreal`         | Photorealistic       | `img2img_sdxl`   | 0.35    | "photorealistic PBR material, 8k, physically based rendering,"      |
| `pixel_art_16bit`   | Pixel Art (16-bit)   | `img2img_pixel`  | 0.70    | "16-bit pixel art, retro SNES era, limited palette, crisp pixels,"  |
| `cel_shaded`        | Cel Shaded           | `img2img_cel`    | 0.55    | "cel shaded, thick black outlines, flat color regions, comic book," |
| `retro_quake1`      | Retro Quake 1        | `img2img_dark`   | 0.45    | "dark gothic Quake 1 style, brown rust, low saturation, grimy,"     |
| `cyberpunk_neon`    | Cyberpunk Neon       | `img2img_neon`   | 0.40    | "cyberpunk neon, magenta and cyan highlights, wet surfaces,"        |

Additional packs (e.g. `q2_sonic_mayhem_tribute`, `ice_world`, `hellscape`) can
be added without schema change — just a new row.

**Rule P1-M (new):** Style packs rotate on section / beat boundaries, never
mid-clip. Texture pop inside a frag = disqualifying glitch.

### 2.6 pk3 Compiler

Per-pack build button or CLI:

```
python -m creative_suite.pk3_build --pack photoreal --out mods/zzz_photoreal.pk3
```

- Walks approved variants for that pack
- Converts PNG → TGA (Quake 3 texture format) via Pillow
- Preserves original asset path inside pk3 (`textures/base_wall/basewall01b.tga`)
- Writes zip with `.pk3` extension
- Records `pk3_path` and `pk3_built_at` on the style_packs row

WolfcamQL picks up the pk3 via `fs_game` / baseq3 load order — zzz_ prefix wins
over baseq3.pk3 by alphabetical precedence.

### 2.7 Per-Clip Style Switching (fragmovie integration)

New table `clip_style_assignments(clip_id, style_pack_id)` plus pipeline changes.

Flow:
1. User opens a Part's clip list in the UI.
2. Bulk-assign rules: "T1 → photoreal, T2 → cel_shaded, T3 → pixel_art_16bit."
3. Individual clip override possible.
4. At render time, Phase 2 re-captures each clip with the matching pk3 loaded
   (`+set fs_game baseq3 +set sv_pure 0` then pk3 resolved by name), then
   Phase 1 stitches as usual.
5. Rule P1-M enforced: adjacent clips of different packs are only allowed at
   transition-envelope boundaries (see Rule P1-L).

### 2.8 Style Exploration Mode

Side flow for "what would this frag look like in every style?"

- Pick one frag.
- Click "Render in all packs."
- Pipeline re-captures that clip once per pack.
- UI shows grid of N video tiles side-by-side.
- Click a tile to set that pack as the clip's assignment.

---

## 3. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Web UI (Three.js + importmap CDN, no npm)                  │
│  - AssetBrowser  PreviewCanvas  VariantPanel  PacksAdmin    │
└────────────────┬────────────────────────────────────────────┘
                 │ REST + WS (FastAPI)
┌────────────────▼────────────────────────────────────────────┐
│  creative_suite/ (Python, FastAPI, uvicorn)                 │
│  ├─ api/          routes: assets, variants, packs, comfy    │
│  ├─ db/           SQLite + WAL, schema below                │
│  ├─ comfy/        ComfyUI client (queue, poll, fetch)       │
│  ├─ ollama/       optional gemma3:4b-vision prompt assist   │
│  ├─ md3/          bulk_frames endpoint + tag composition    │
│  ├─ pk3_build/    approved variants → zzz_<slug>.pk3        │
│  └─ inventory/    ingest from FULL_CATALOG.json             │
└────────────────┬────────────────────────────────────────────┘
                 │
   ┌─────────────┼──────────────┬───────────────┐
   │             │              │               │
┌──▼──┐     ┌────▼────┐    ┌────▼───┐     ┌─────▼─────┐
│Comfy│     │ Ollama  │    │ SQLite │     │ pk3 files │
│ UI  │     │gemma3:4b│    │  WAL   │     │ mods/     │
└─────┘     └─────────┘    └────────┘     └───────────┘
```

**Why FastAPI:** async, websockets for ComfyUI progress, auto OpenAPI, easy to
wire ollama + comfy clients alongside REST.

**Why SQLite + WAL:** joins across variants × packs × clips, grows to 10K+
variants without refactor, single file.

**Why PNG in library → TGA at build:** lossless working format, fast `<img>`
preview, only pay the TGA conversion cost once when building the pk3.

---

## 4. Data Model (SQLite)

```sql
-- inventoried baseq3/HD-pack assets (one row per overridable file)
CREATE TABLE assets (
  id              INTEGER PRIMARY KEY,
  category        TEXT NOT NULL,   -- weapon|skin|surface|effect|gfx|sound
  subcategory     TEXT,            -- rocket|rail|sarge|base_wall|smoke
  source_pk3      TEXT NOT NULL,
  internal_path   TEXT NOT NULL,   -- textures/base_wall/basewall01b.tga
  checksum        TEXT NOT NULL,
  extracted_path  TEXT,            -- absolute path on disk if extracted
  width           INTEGER,
  height          INTEGER,
  UNIQUE (source_pk3, internal_path)
);

CREATE TABLE style_packs (
  id               INTEGER PRIMARY KEY,
  slug             TEXT UNIQUE NOT NULL,
  display_name     TEXT NOT NULL,
  workflow_id      TEXT NOT NULL,    -- ComfyUI workflow json name
  prompt_prefix    TEXT NOT NULL,
  prompt_negative  TEXT,
  denoise_max      REAL NOT NULL,
  controlnet       TEXT,             -- optional: canny|depth|none
  pk3_path         TEXT,             -- mods/zzz_photoreal.pk3
  pk3_built_at     DATETIME,
  thumbnail_path   TEXT,
  created_at       DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE variants (
  id               INTEGER PRIMARY KEY,
  asset_id         INTEGER NOT NULL REFERENCES assets(id),
  style_pack_id    INTEGER NOT NULL REFERENCES style_packs(id),
  user_prompt      TEXT,
  final_prompt     TEXT NOT NULL,
  seed             INTEGER,
  comfy_job_id     TEXT,
  png_path         TEXT NOT NULL,
  thumbnail_path   TEXT,
  width            INTEGER,
  height           INTEGER,
  status           TEXT NOT NULL,    -- pending|approved|rejected
  approved_at      DATETIME,
  created_at       DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_variants_asset ON variants(asset_id, status);
CREATE INDEX idx_variants_pack  ON variants(style_pack_id, status);

-- per-clip style assignment at fragmovie render time
CREATE TABLE clip_style_assignments (
  clip_id          TEXT PRIMARY KEY,  -- matches phase1 clip id
  style_pack_id    INTEGER NOT NULL REFERENCES style_packs(id),
  assigned_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
  rule_source      TEXT               -- manual|tier_rule|exploration
);
```

---

## 5. API Surface

```
GET    /api/assets                     list/filter/paginate
GET    /api/assets/{id}                metadata + preview url
GET    /api/assets/{id}/preview        raw pixels (PNG)

GET    /api/md3/frame                  render MD3 frame (params: model, frame, yaw, lighting)
GET    /api/md3/bulk_frames            turntable or animation sequence

GET    /api/packs                      list style packs
POST   /api/packs                      create pack
POST   /api/packs/{id}/build           compile zzz_<slug>.pk3
GET    /api/packs/{id}/variants        approved variants in this pack

POST   /api/comfy/queue                {asset_id, pack_id, user_prompt}  → job_id
WS     /api/comfy/progress/{job_id}    progress stream
GET    /api/comfy/result/{job_id}      final PNG

POST   /api/variants/{id}/approve
POST   /api/variants/{id}/reject
POST   /api/variants/{id}/reroll

POST   /api/ollama/suggest_prompts     {asset_id, pack_id} → [3 prompts]

GET    /api/clips                      phase1 clip list
POST   /api/clips/assign_styles        {rule: "tier", mapping: {T1: 1, T2: 3, T3: 2}}
POST   /api/clips/{id}/style           {pack_id}

POST   /api/explore/frag/{clip_id}     render in all packs → grid
```

---

## 6. Sprint Plan

Total ~27 build-days, 9 sprints of ~3 days.

| # | Sprint                       | Deliverable                                             |
|---|------------------------------|---------------------------------------------------------|
| 1 | Skeleton                     | FastAPI app, SQLite schema, inventory ingest            |
| 2 | Asset browser UI             | Tree view, texture preview, search/filter               |
| 3 | MD3 preview integration      | Embed md3viewer, lighting sliders, turntable            |
| 4 | ComfyUI client               | Queue + poll + fetch, workflow templates for 5 packs    |
| 5 | Variant panel + approval     | Generate UI, result grid, approve/reject/reroll         |
| 6 | Style Packs admin            | CRUD packs, seed 5 default packs, thumbnails            |
| 7 | pk3 compiler                 | Per-pack build, PNG→TGA, zzz_<slug>.pk3 output          |
| 8 | Per-clip style switching     | clip_style_assignments + pipeline pk3 swap + Rule P1-M  |
| 9 | Style Exploration + Ollama   | Explore-all-packs grid, gemma3:4b-vision prompt assist  |

After sprint 7 you can already produce a fully-restyled Part; sprint 8 unlocks
per-clip mixing; sprint 9 is polish.

---

## 7. Rules & Gates

- **Rule P1-M (new):** Style packs rotate on section / beat boundaries, never mid-clip.
- **Gate CS-1:** Before sprint 7 build, user approves 5 seeded pack aesthetics on one shared reference asset (rocket texture).
- **Gate CS-2:** Before sprint 8 wiring, user approves that per-clip switching doesn't break Rule P1-L transition envelopes.

---

## 8. YAGNI cuts

- Sound variants — schema supports it, UI tab disabled in v1.
- Multi-user / auth — local-only tool.
- Cloud ComfyUI — local ComfyUI only, `http://127.0.0.1:8188`.
- npm / build pipeline — importmap + CDN Three.js only.
- Undo history — rejected variants are the history.

---

## 9. Open questions for user review

1. Seed packs OK, or swap `cyberpunk_neon` for `q2_sonic_mayhem_tribute`?
2. Gate CS-1 reference asset — rocket texture OK, or prefer a player skin?
3. Any pack you want FIRST (sprint 6 seeds one as hero so you can see progress early)?

Overrides from user review get folded into the plan; otherwise writing-plans
skill produces the implementation plan directly from this spec.
