# Quake Legacy Command Center — Design Spec

**Date:** 2026-04-17
**Status:** Draft v2 (supersedes `2026-04-17-creative-suite-design-v1-superseded.md`)
**Scope:** One unified project-local app that does asset variant factory,
style-pack pk3 compilation, demo hub, graphify bridge, per-clip style
switching at fragmovie render time, and remains CLI-introspectable so Claude
(me) can keep driving n8n + graphify hooks in parallel.
**Companion spec:** `2026-04-17-engine-pivot-design.md` decides the render
engine. Command Center depends on that choice for Sprint 8.
**Out of scope:** Sprint 10 (engine 4K master + YouTube mastering) — separate spec.

---

## 1. Prime Directives (user ruling)

1. **Everything Quake lives in `G:\QUAKE_LEGACY\`.** No DB, no cache, no
   generated asset lands in `C:\Users\...` or `AppData`. One folder, one
   truth, one portable drive.
2. **Docker where it helps, native where it doesn't.** FastAPI + SQLite run
   in a container with `G:\QUAKE_LEGACY\` bind-mounted. ComfyUI stays
   external on host (existing setup). Ollama stays external on host.
3. **Command Center, not a toy.** This UI replaces ad-hoc scripts for asset
   browsing, demo selection, clip review, style assignment, pk3 compile,
   and render kickoff. Claude CLI keeps working alongside — n8n webhooks,
   graphify, wrap-up hooks fire on the same data the UI reads.
4. **Graphify-aware storage.** Every generated/approved asset writes to a
   predictable folder tree so graphify + Obsidian can link actions →
   assets → clips → fragmovies in real time.
5. **2026 it.** Don't carry wolfcam's 2012 assumptions forward. Use its
   source as reference, ingest what it does, then build the modern pipeline.

---

## 2. System Layout (project-local, Docker + host mix)

```
G:\QUAKE_LEGACY\
├─ creative_suite\                  <-- NEW, replaces scattered tools
│  ├─ docker-compose.yml             one-command stack start
│  ├─ Dockerfile                     FastAPI + deps
│  ├─ app\                           Python source (api, db, comfy, md3, pk3)
│  ├─ web\                           Static UI (Three.js importmap, no npm)
│  ├─ data\
│  │  ├─ command_center.db           SQLite WAL — assets, variants, packs, clips, demos
│  │  ├─ thumbnails\                 generated previews
│  │  └─ logs\
│  ├─ generated\                     <-- graphify-watched root
│  │  ├─ variants\<pack_slug>\<asset_category>\<asset_name>\<variant_id>.png
│  │  ├─ packs\zzz_<pack_slug>.pk3
│  │  ├─ sprites\<sprite_pack>\<effect>\frame_####.png
│  │  └─ renders\<part>\<clip_id>\<pack_slug>.mp4
│  └─ workflows\                     ComfyUI workflow JSONs (img2img, animate, SVD)
│
├─ (existing) QUAKE VIDEO, WOLF WHISPERER, FRAGMOVIE VIDEOS,
│  phase1, phase2, phase3, phase35, tools, docs, database
```

**Docker compose services (one stack):**

```yaml
services:
  command_center:
    build: ./creative_suite
    ports: ["8000:8000"]
    volumes:
      - G:/QUAKE_LEGACY:/workspace                # everything the app touches
      - ./creative_suite/data:/workspace/creative_suite/data   # named for clarity
    environment:
      COMFY_URL: http://host.docker.internal:8188   # external ComfyUI
      OLLAMA_URL: http://host.docker.internal:11434 # external Ollama
      PROJECT_ROOT: /workspace
    extra_hosts: ["host.docker.internal:host-gateway"]
```

No other services. SQLite is a file inside the volume — no postgres, no
redis, no complication. Existing Claude CLI sees `G:\QUAKE_LEGACY\` natively.

---

## 3. Modules

### 3.1 Asset Browser
Tree view across `weapons / skins / surfaces / effects / gfx / sounds(disabled v1)`.
Source: `tools/game-assets/FULL_CATALOG.json` from existing-assets inventory.
Click → preview.

### 3.2 Preview Canvas
- Textures: side-by-side original vs variant, synced zoom/pan.
- **Animated MD3 playback.** Per `docs/research/md3-animation-system-2026-04-17.md`:
  weapon view-models have animation.cfg with IDLE/FIRE/RELOAD ranges;
  player models have LEGS_RUN/TORSO_ATTACK etc. UI scrubber walks the frames.
  Caches interpolated geometry via `/api/md3/bulk_frames`.
- Turntable button, lighting sliders (ambient/key/fill/rim/rim_power from L85).

### 3.3 ComfyUI Variant Generator
- Input: selected asset. Style Pack dropdown (§ 3.5). User prompt text area.
  Optional: Ollama gemma3:4b-vision prompt-suggest button (3 chips).
- `POST /api/comfy/queue` relays to ComfyUI `/prompt`, progress via WS.
- Result grid: thumbnail + pack badge + timestamp + approve/reject/reroll.

### 3.4 Approval Loop
Approve → `generated/variants/<pack>/<category>/<asset>/<id>.png` + thumbnail.
Reject → kept in DB as history. Reroll → same prompt, new seed.

### 3.5 Style Packs (first-class)

A pack bundles: workflow, prompt prefix, negative prompt, denoise ceiling,
optional ControlNet, compiled `zzz_<slug>.pk3`, thumbnail, optional **sprite
animator workflow** (see § 3.7).

**Seed packs v1 — my picks for question 7:**

| slug               | display name       | workflow        | denoise | notes                          |
|--------------------|--------------------|-----------------|---------|--------------------------------|
| `photoreal`        | Photorealistic     | img2img_sdxl    | 0.35    | PBR materials, hero realism    |
| `pixel_art_16bit`  | Pixel Art (16-bit) | img2img_pixel   | 0.70    | SNES palette, crisp pixels     |
| `cel_shaded`       | Cel Shaded         | img2img_cel     | 0.55    | Borderlands-ish outlines       |
| `retro_quake1`     | Retro Quake 1      | img2img_dark    | 0.45    | Gothic rust, Trent Reznor mood |
| `q2_sonic_mayhem`  | Quake 2 Tribute    | img2img_strogg  | 0.45    | Industrial, Strogg palette     |

Swapped `cyberpunk_neon` out for `q2_sonic_mayhem` — better Quake-lineage
story than generic neon. Cyberpunk can be pack #6 added later.

Rule P1-M (new): style packs rotate on section / beat boundaries, never
mid-clip.

### 3.6 Templates & Presets
User ruling on question 4: multiple presets per pack.

Each pack exposes **sub-presets** — variations on the base pack prompt
(e.g. `photoreal/wet`, `photoreal/dry`, `photoreal/rust`). Presets are
just rows: `(pack_id, preset_name, extra_prompt, extra_negative,
denoise_override)`. UI shows preset chips under the pack dropdown.

### 3.7 Sprite & Projectile Animator (the wow-factor feature)

Per user: "we could also use our existing model if we can animate or
generate the sprites."

Targets:
- Rocket trail (sprite sheet or looping sequence)
- Rail beam (segmented sprite chain)
- Plasma ball (animated projectile)
- Muzzle flash (short burst sequence)
- Explosion (frame sequence)
- Smoke puffs, blood sprays, lightning core

**Two generators, chosen per-pack:**

1. **AnimateDiff / SVD img2vid** — ComfyUI workflow takes a base frame
   and produces N coherent frames. Output: frame sequence PNG → repackaged
   as animated sprite sheet in pk3 build.
2. **Procedural** — for things like the rail beam where we know the
   physics (straight line + ripple), render N frames with a shader.
   Already doable in the MD3 viewer's Three.js canvas.

Each pack can opt into animated sprites via `pack.sprite_workflow_id`.
If set, pk3 build auto-generates animated sprites for that pack using
its aesthetic prompts.

### 3.8 pk3 Compiler
`python -m command_center.pk3_build --pack photoreal` → walks approved
variants + generated sprites → PNG→TGA/JPG → zip with `.pk3` extension →
writes to `generated/packs/zzz_photoreal.pk3`. Engine picks it up via
load order (see companion spec for which engine).

### 3.9 Per-Clip Style Switching (fragmovie integration)

Table `clip_style_assignments(clip_id, style_pack_id, preset_name?)`.

Flow:
1. Open a Part in UI. Clip list shows current tier (T1/T2/T3).
2. Bulk-assign rules: "T1→photoreal, T2→cel_shaded, T3→pixel_art_16bit".
3. Per-clip override possible. Style Exploration mode renders one clip
   through all packs for grid comparison.
4. Render time: pipeline re-captures each clip with the matching pk3
   loaded, then Phase 1 stitches. Rule P1-M enforced.

### 3.10 Demo Hub (new, replaces ad-hoc scripts)

Tab in the UI. Lists every demo on disk (primary: `WOLF WHISPERER/.../demos/`,
secondary: `demos/` once staged). Columns: filename, size, detected player
aliases, map, duration, dedup status, extraction status.

Actions:
- "Dedup" — runs hash + fingerprint match across 8GB dump + existing 948.
- "Extract" — invokes our `dm73parser` → JSON Lines → `database/frags.db`.
- "Preview first frag" — decodes first snapshot, shows top entities.
- "Tag notable player" — flags demos with aliases matching FT-5 regex.

### 3.11 Graphify Bridge

Every DB write fires an event. Graphify watcher (outside the container,
reading SQLite via `file:` URL) knows when a variant is approved, a pack
is built, a clip is assigned. Obsidian `Vault/projects/quake_legacy/`
gets auto-updated notes via n8n webhook → "Pack `photoreal` rebuilt at
T, 47 variants, linked to Part 4 T1 clips."

Generated folder tree is graphify-scannable: paths encode pack → asset
category → clip → variant, so the graph clusters correctly without extra
metadata files.

### 3.12 CLI Parity

The UI is a view over SQLite + filesystem. Every UI action has a CLI
equivalent (`ccc variant approve <id>`, `ccc pack build <slug>`, …) so
Claude can script against the same state the UI reads. No stateful
in-memory daemons that break CLI parity.

---

## 4. Data Model

```sql
-- inventoried overridable assets (one row per file we can replace)
CREATE TABLE assets (
  id INTEGER PRIMARY KEY,
  category TEXT NOT NULL,        -- weapon|skin|surface|effect|gfx|sprite
  subcategory TEXT,
  source_pk3 TEXT NOT NULL,
  internal_path TEXT NOT NULL,
  checksum TEXT NOT NULL,
  extracted_path TEXT,
  width INTEGER, height INTEGER,
  is_animated INTEGER DEFAULT 0, -- 1 for sprite sheets / MD3 frames
  UNIQUE (source_pk3, internal_path)
);

CREATE TABLE style_packs (
  id INTEGER PRIMARY KEY,
  slug TEXT UNIQUE NOT NULL,
  display_name TEXT NOT NULL,
  workflow_id TEXT NOT NULL,
  sprite_workflow_id TEXT,       -- optional animate/SVD workflow
  prompt_prefix TEXT NOT NULL,
  prompt_negative TEXT,
  denoise_max REAL NOT NULL,
  controlnet TEXT,
  pk3_path TEXT,
  pk3_built_at DATETIME,
  thumbnail_path TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE pack_presets (
  id INTEGER PRIMARY KEY,
  pack_id INTEGER NOT NULL REFERENCES style_packs(id),
  name TEXT NOT NULL,            -- "wet", "dry", "rust"
  extra_prompt TEXT,
  extra_negative TEXT,
  denoise_override REAL,
  UNIQUE (pack_id, name)
);

CREATE TABLE variants (
  id INTEGER PRIMARY KEY,
  asset_id INTEGER NOT NULL REFERENCES assets(id),
  style_pack_id INTEGER NOT NULL REFERENCES style_packs(id),
  preset_id INTEGER REFERENCES pack_presets(id),
  user_prompt TEXT,
  final_prompt TEXT NOT NULL,
  seed INTEGER,
  comfy_job_id TEXT,
  png_path TEXT NOT NULL,
  is_animated INTEGER DEFAULT 0,
  frame_count INTEGER,            -- for animated sprites
  fps INTEGER,
  thumbnail_path TEXT,
  width INTEGER, height INTEGER,
  status TEXT NOT NULL,           -- pending|approved|rejected
  approved_at DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_variants_asset ON variants(asset_id, status);
CREATE INDEX idx_variants_pack  ON variants(style_pack_id, status);

CREATE TABLE clip_style_assignments (
  clip_id TEXT PRIMARY KEY,
  style_pack_id INTEGER NOT NULL REFERENCES style_packs(id),
  preset_id INTEGER REFERENCES pack_presets(id),
  assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  rule_source TEXT                -- manual|tier_rule|exploration
);

CREATE TABLE demos (
  id INTEGER PRIMARY KEY,
  abs_path TEXT UNIQUE NOT NULL,
  filename TEXT NOT NULL,
  size_bytes INTEGER NOT NULL,
  sha256 TEXT NOT NULL,
  fingerprint TEXT,               -- snapshot-sample hash for dedup
  map TEXT,
  duration_s REAL,
  aliases TEXT,                   -- JSON array of detected player aliases
  is_duplicate_of INTEGER REFERENCES demos(id),
  extracted_at DATETIME,
  notable INTEGER DEFAULT 0,
  discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 5. API Surface (abridged — full list generates from routes)

```
# assets
GET  /api/assets               list/filter
GET  /api/assets/{id}
GET  /api/assets/{id}/preview
GET  /api/md3/frame            (yaw, frame, lighting)
GET  /api/md3/bulk_frames

# packs & presets
GET  /api/packs
POST /api/packs
POST /api/packs/{id}/build
POST /api/packs/{id}/build_sprites
GET  /api/packs/{id}/presets
POST /api/packs/{id}/presets

# comfy
POST /api/comfy/queue
WS   /api/comfy/progress/{job_id}
GET  /api/comfy/result/{job_id}

# variants
POST /api/variants/{id}/approve
POST /api/variants/{id}/reject
POST /api/variants/{id}/reroll

# ollama
POST /api/ollama/suggest_prompts

# clips
GET  /api/clips
POST /api/clips/assign_styles
POST /api/clips/{id}/style
POST /api/explore/frag/{clip_id}    # render in all packs

# demos
GET  /api/demos
POST /api/demos/scan                # walk disk, hash, dedup
POST /api/demos/{id}/extract        # run dm73parser → frags.db

# system
GET  /api/health
GET  /api/events                    # SSE stream for graphify / n8n
```

---

## 6. Sprint Plan (~30 build-days, 10 sprints)

| # | Sprint                           | Deliverable                                       |
|---|----------------------------------|---------------------------------------------------|
| 1 | Docker skeleton + SQLite schema  | `docker compose up`, `/api/health` 200            |
| 2 | Inventory ingest + asset browser | Tree UI over `FULL_CATALOG.json`                  |
| 3 | MD3 preview + animation playback | Embedded viewer, scrubber, lighting sliders       |
| 4 | ComfyUI client + 5 pack workflows| Queue/poll/fetch, img2img workflows for v1 packs  |
| 5 | Variant panel + approval loop    | Generate, grid, approve/reject/reroll             |
| 6 | Packs admin + presets + seeds    | CRUD packs, preset chips, seed 5 default packs    |
| 7 | pk3 compiler                     | PNG→TGA, per-pack zzz_<slug>.pk3 output           |
| 8 | Per-clip style switching         | clip_style_assignments + pipeline pk3 swap hook   |
| 9 | Sprite/projectile animator       | AnimateDiff / SVD workflow, animated pk3 build    |
|10 | Demo hub + graphify bridge       | Dedup, extract, SSE event stream, n8n wiring      |

**Gate CS-1 (before sprint 7):** User approves 5 seeded pack aesthetics
on the rocket launcher texture (my pick for question 8 — sprint 6 seeds
`photoreal` first so hero asset is visible early).

**Gate CS-2 (before sprint 8):** User approves per-clip switching doesn't
violate Rule P1-L transition envelopes.

**Gate CS-3 (before sprint 9):** User approves sprite animator output on
rocket-trail reference.

---

## 7. Autonomous Decisions (questions 1/2/3/4/7/8 resolved)

| Q | Decision |
|---|----------|
| 1 (Docker) | **Yes, one service in compose, project-local bind-mount.** |
| 2 (FastAPI) | **FastAPI.** SSE for events, WS for comfy progress. |
| 3 (SQLite) | **SQLite WAL** inside `creative_suite/data/`. |
| 4 (Presets) | **`pack_presets` table** — chips under pack dropdown. |
| 4b (Sprite anim) | **Dedicated sprint 9** with AnimateDiff/SVD + procedural fallback. |
| 7 (Seed packs) | **photoreal / pixel_art_16bit / cel_shaded / retro_quake1 / q2_sonic_mayhem** (swapped out generic cyberpunk for Q2 tribute — deeper Quake lineage). |
| 8 (Hero asset) | **Rocket launcher texture** as Gate CS-1 reference. Sprint 6 seeds `photoreal` first so you see hero-quality output before week 3. |

---

## 8. Dependencies on Engine Pivot spec

Sprint 8 (per-clip style switching) and Sprint 9 (sprite animator) need
the engine decision locked. Specifically:
- Which executable re-captures a clip with pack pk3 loaded?
- How does the engine load `zzz_*.pk3` under `fs_game baseq3`?
- Does the engine support animated sprite shaders the way wolfcam does?

See `2026-04-17-engine-pivot-design.md` for the engine call + the one
blocker I need user input on (protocol 73 playback).

---

## 9. YAGNI cuts

- Sound variant generation — schema ready, UI tab disabled v1.
- Multi-user auth — local only.
- Cloud ComfyUI — local only, `http://host.docker.internal:8188`.
- npm / webpack — Three.js importmap + CDN.
- Live collaborative editing — single-user tool.

---

## 10. Open questions for user (short list)

- Dockerfile base: **python:3.12-slim** OK?
- Ollama vision model name on your machine: `gemma3:4b` or exact tag?
- Project-local means we drop the global `C:\Users\Stoneface\.claude\projects\...`
  memory writes for this module too, or keep them as session-summary
  overflow? (My rec: keep global memory for LESSONS, keep all DATA in
  project folder. Zero duplication, zero confusion.)

Non-blocking — write the implementation plan after user ACKs Docker base
+ engine-pivot spec.
