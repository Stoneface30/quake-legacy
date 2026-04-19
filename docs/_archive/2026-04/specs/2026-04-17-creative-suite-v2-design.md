# Creative Suite v2 — Design Spec

**Date:** 2026-04-17
**Status:** Draft — awaits user review
**Supersedes:** `2026-04-17-creative-suite-design-v1-superseded.md`
**Related:** `docs/reviews/part4-review-2026-04-17.md`, `docs/research/existing-assets-inventory-2026-04-17.md`
**Scope:** One local FastAPI app serving two tracks — (1) single-pack photoreal pk3 factory,
(2) Part-review annotation capture feeding the future demo-pattern corpus.
**Out of scope:** Multi-pack rotation, per-clip style switching, style exploration mode,
sound variants, demo re-extraction (FT-1), pattern compiler / DSL / predicates library
(Stage 2 — belongs to Phase 3 demo-extraction work).

---

## 1. One-Line Summary

A local web UI that (a) turns every baseq3 texture / skin / model into an approved
photorealistic variant through ComfyUI, compiles them into a single
`zzz_photorealistic.pk3` that wolfcamql loads over `pak00.pk3`, re-rendering every
demo at maximum ingame resolution — AND (b) lets the user annotate rendered Parts
in English while reviewing, building a corpus of *("description, AVI-achievable
effect, dream-phase effect, back-resolved clip coords")* tuples that becomes the
training set for Phase 3 pattern-recognition over the 10 GB demo library.

---

## 2. Why Two Tracks in One App

Track 1 (pk3 factory) and Track 2 (annotation) share:

- One FastAPI process, one SQLite WAL file, one launcher (`python -m creative_suite`).
- One asset inventory ingest (`FULL_CATALOG.json`).
- One `md3viewer.js` Three.js canvas (already built, has lighting sliders from L85).
- One place to look when the user thinks "I need to open the tool."

They do NOT share data — annotations live in `annotations`, variants in `variants`,
joined only through the eventual `clip_id` once demo-extraction phase runs.

Keeping them co-located pays off when (eventually) we want:
*"show me every clip flagged `lms_clutch` rendered with `zzz_photorealistic.pk3`."*

---

## 3. Track 2 — Annotation Tool (ships first, usable end of day 1)

### 3.1 User flow

1. User launches `python -m creative_suite` → opens `http://localhost:8765/annotate`.
2. Dropdown picks a Part (populated from `output/PartN.mp4` files that actually exist).
3. `<video>` element plays the mp4. Keyboard controls:
   - `Space` — play / pause
   - `←` / `→` — step 1 second
   - `Shift+←` / `Shift+→` — step 0.1 second
   - `M` — mark moment (opens side-panel form, auto-fills `mp4_time`)
4. Form fields:
   - `mp4_time` — float seconds, editable
   - `description` — multi-line. The English. What happened, why it mattered.
   - `avi_effect` — what could be done with the existing AVI (slowmo, replay
     contrast, speed ramp, hard cut placement, grade push, `none`).
   - `dream_effect` — what you'd want if this were re-rendered from demo
     (kill-cam, rocket-cam, free-cam, zoom-follow, chase-cam, `none`).
   - `tags` — chips, freely addable (`peak`, `airshot`, `multikill`, `clutch`,
     `lms`, `flick`, `chase`, `notable_victim` as starter set).
5. [Save] — POSTs to `/api/annotations`. Server auto-resolves `mp4_time → clip_index`
   (see §3.3), stamps `id` and `created_at`, appends to JSONL and SQLite.
6. Below the video: live-updating table of all saved annotations for this Part.
   Edit / delete inline. Click a row to seek video to that `mp4_time`.

### 3.2 Data shape (JSONL record)

```json
{
  "id": "2026-04-17-part04-000012",
  "part": 4,
  "mp4_time": 133.4,
  "description": "LMS clutch — last alive, 4 reds, LG chase into rail finisher.",
  "avi_effect": "slowmo final rail hit; replay-contrast the LG chase section",
  "dream_effect": "kill-cam each of the 4 kills; free-cam pullback at round win",
  "tags": ["clutch", "lms", "peak"],
  "clip_index": 17,
  "clip_filename": "Demo (490)  - 596.avi",
  "demo_hint": "490",
  "demo_file": null,
  "servertime_ms": null,
  "created_at": "2026-04-17T21:14:02Z"
}
```

### 3.3 Clip resolution at save time

Reality check: current `phase1/clip_lists/partNN.txt` files are AVI filenames, not
demo+servertime tuples. The AVI's prefix (e.g. `Demo (490)`) is a *hint* to which
`.dm_73` was the source, but precise servertime requires either (a) an existing
mapping table we don't have, or (b) FT-1 parser output we won't have until demo-
extraction phase.

**So MVP auto-resolution does the honest thing:**

1. Read `phase1/clip_lists/partNN.txt`, strip comments, enumerate clips in order.
2. For each clip, read the AVI's duration (`ffprobe`, cached in SQLite on ingest).
3. Prepend PANTHEON (7s) + Title Card (8s, per Rule P1-N) to the timeline.
4. Find the clip covering `mp4_time`. Fill `clip_index`, `clip_filename`, `demo_hint`.
5. Leave `demo_file` and `servertime_ms` NULL.

When FT-1 ships and we have true `(avi → demo, servertime_start, servertime_end)`
mapping, a backfill job fills those NULL fields across all annotations written so
far. The annotation corpus carries forward with zero rework.

### 3.4 Storage

- `storage/annotations/part{NN}.jsonl` — append-only, human-readable, git-friendly.
- `annotations` table in SQLite — mirror for query joins.
- JSONL is source of truth; SQLite is rebuilt from JSONL on startup if out of sync.

### 3.5 API

```
GET    /api/annotations?part=4
POST   /api/annotations                 body = form fields; server adds id + clip coords
PATCH  /api/annotations/{id}
DELETE /api/annotations/{id}
GET    /api/clips/resolve?part=4&time=133.4
        → {clip_index, clip_filename, demo_hint, mp4_offset, clip_offset}
GET    /api/parts                       list Parts that have a rendered mp4
```

### 3.6 Explicit non-goals for MVP

- No DSL, predicate library, or pattern compiler — Stage 2 work.
- No scan-across-demos search — Stage 2 work.
- No back-resolution to servertime — waits on FT-1.
- No video segmentation / clip extraction from annotations — export only.

---

## 4. Track 1 — Creative Suite MVP (single-pack photoreal)

### 4.1 Scope lock

- ONE pack, hardcoded slug `photorealistic`.
- Output: `storage/packs/zzz_photorealistic.pk3` (ENG-2 naming).
- Install hook copies pk3 into wolfcam's `baseq3/`, `sv_pure 0` required (ENG-3).
- Steam paks remain read-only source of truth (ENG-1, ENG-4).

### 4.2 User flow

1. Browse assets in left-pane tree (categories: weapons / skins / surfaces /
   effects / gfx — sounds disabled in v1).
2. Click a texture → `<img>` preview in center pane. Click an MD3 → embedded
   md3viewer canvas with turntable and lighting sliders.
3. Right pane:
   - Seed prompt pre-filled (hardcoded):
     `"photorealistic PBR material, 8k, physically based rendering,
       tactile surface detail, no stylization,"`
   - User prompt suffix (textarea) — "more rust," "darker concrete," etc.
   - Final prompt = seed + user suffix.
   - [Suggest prompts] — optional button. POSTs thumbnail to local Ollama
     `gemma3:4b-vision`, asks for 3 photoreal-flavored variations. Returns 3
     clickable chips that pre-fill the suffix. Degrades gracefully if Ollama
     is not running.
   - [Generate] — POSTs to `/api/comfy/queue`. ComfyUI workflow:
     `img2img_sdxl` with denoise 0.35, ControlNet canny (optional, toggled).
4. Progress streams over WebSocket (`/api/comfy/progress/{job_id}`).
5. Result grid below the prompt — tile per generation with timestamp.
6. Click a tile → side-by-side compare:
   - Textures: two `<canvas>` elements, synced pan/zoom, pixel-ruler overlay.
   - Models: two md3viewer canvases, synced camera.
7. [✓ Approve] / [✗ Reject] / [⟳ Reroll] per tile.
8. Approved variants accumulate. Any time: [Build pk3] →
   - Walks all `status = 'approved'` variants.
   - Converts PNG → TGA via Pillow (preserving alpha, sRGB).
   - Zips into `storage/packs/zzz_photorealistic.pk3` with original
     internal paths preserved.
   - Records `pack_builds` row with `sha256`, variant count, timestamp.
9. [Install to wolfcam] — copies pk3 into the wolfcam `baseq3/` dir from config.
10. User runs existing phase2 batch re-render with max-ingame-quality config
    (see §4.4). Every demo frag renders with the photoreal pack loaded.

### 4.3 Asset ingest

- Source: `tools/game-assets/FULL_CATALOG.json` (confirmed exists).
- Re-uses research doc `docs/research/existing-assets-inventory-2026-04-17.md`
  categorizations (131 baseq3 pk3s, 4000 q3a-extracted files, 8700 ql-extracted).
- Ingest on first run, idempotent. Re-ingest on `--refresh-assets` flag.
- Thumbnails pre-generated for textures (`PIL.thumbnail`, 256px, cached).

### 4.4 Max-quality wolfcam capture config (Rule P1-J)

Capture cvars written into `gamestart.cfg` by the re-render launcher:

```
r_mode -1
r_customwidth 3840
r_customheight 2160
r_fullscreen 0
cg_fov 100
r_picmip 0
r_textureMode GL_LINEAR_MIPMAP_LINEAR
r_ext_texture_filter_anisotropic 1
r_ext_max_anisotropy 16
r_lodbias -2
r_subdivisions 1
cg_drawFPS 0
cg_draw2D 0
cg_drawCrosshair 0
cg_drawGun 0                // for FL angles only; FP keeps gun
com_maxfps 125
com_hunkmegs 512
set sv_pure 0
```

AVI capture at 4K/125fps, downsample to 1080p/60fps later via ffmpeg
(`scale=1920:1080:flags=lanczos`, then FT-6 encoder).

### 4.5 Ollama prompt assist (optional)

- Only invoked on explicit button press.
- Timeout 5s; on failure, silently disable the button for this session.
- Prompt template:
  > *"This is a Quake 3 texture (category: {category}, subcategory: {subcategory}).
  > Suggest 3 short prompt suffixes that would turn this into a photorealistic
  > PBR surface for a fragmovie. Each suffix under 20 words. Return as JSON
  > array of strings."*
- Response parsed as JSON; chips displayed.

---

## 5. Architecture

```
┌────────────────────────────────────────────────────────────────┐
│  Browser — two pages, served statically from /web              │
│  /annotate     Track 2 UI (video + form + table)               │
│  /creative     Track 1 UI (asset browser + comfy + compare)    │
└────────────────────────────┬───────────────────────────────────┘
                             │ REST + WebSocket
┌────────────────────────────▼───────────────────────────────────┐
│  creative_suite/ (FastAPI, uvicorn :8765)                       │
│  ├─ app.py           entrypoint, mounts routers + static        │
│  ├─ api/                                                        │
│  │  ├─ assets.py     list / preview / thumbnail                 │
│  │  ├─ md3.py        existing md3viewer endpoints               │
│  │  ├─ comfy.py      queue / poll / fetch ComfyUI jobs          │
│  │  ├─ variants.py   approve / reject / reroll                  │
│  │  ├─ packs.py      build + install zzz_photorealistic.pk3     │
│  │  ├─ ollama.py     gemma3:4b-vision prompt assist             │
│  │  ├─ annotations.py  Track 2 CRUD                             │
│  │  └─ clips.py      clip-list parse + time resolution          │
│  ├─ db/                                                         │
│  │  ├─ schema.sql    see §6                                     │
│  │  └─ migrate.py                                               │
│  ├─ inventory/       FULL_CATALOG.json → assets ingest          │
│  ├─ pk3_build/       PNG→TGA + zip writer                       │
│  └─ web/             static html + js (importmap, Three.js CDN) │
└───────────┬────────────────┬────────────────┬──────────────────┘
            │                │                │
      ┌─────▼────┐      ┌────▼────┐      ┌────▼─────┐
      │ ComfyUI  │      │ Ollama  │      │  SQLite  │
      │ :8188    │      │ :11434  │      │  WAL     │
      └──────────┘      └─────────┘      └──────────┘
```

**Why FastAPI:** async routers, native WebSocket, auto OpenAPI at `/docs`,
minimal ceremony.
**Why SQLite WAL:** joins across assets × variants × annotations, one file,
concurrent reads while writes happen.
**Why no npm:** every browser dep is Three.js + importmap — see existing
`md3viewer.js`.

---

## 6. Data model

```sql
-- Track 1: asset factory
CREATE TABLE assets (
  id              INTEGER PRIMARY KEY,
  category        TEXT NOT NULL,     -- weapon|skin|surface|effect|gfx
  subcategory     TEXT,
  source_pk3      TEXT NOT NULL,
  internal_path   TEXT NOT NULL,     -- textures/base_wall/basewall01b.tga
  checksum        TEXT NOT NULL,
  extracted_path  TEXT,
  width           INTEGER,
  height          INTEGER,
  thumbnail_path  TEXT,
  UNIQUE (source_pk3, internal_path)
);

CREATE TABLE variants (
  id              INTEGER PRIMARY KEY,
  asset_id        INTEGER NOT NULL REFERENCES assets(id),
  user_prompt     TEXT,
  final_prompt    TEXT NOT NULL,
  seed            INTEGER,
  comfy_job_id    TEXT,
  png_path        TEXT NOT NULL,
  thumbnail_path  TEXT,
  width           INTEGER,
  height          INTEGER,
  status          TEXT NOT NULL,     -- pending | approved | rejected
  approved_at     DATETIME,
  created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_variants_asset_status ON variants(asset_id, status);

CREATE TABLE pack_builds (
  id              INTEGER PRIMARY KEY,
  pack_slug       TEXT NOT NULL,     -- 'photorealistic' in MVP
  pk3_path        TEXT NOT NULL,
  variant_count   INTEGER NOT NULL,
  sha256          TEXT NOT NULL,
  built_at        DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Track 2: annotation corpus
CREATE TABLE annotations (
  id              TEXT PRIMARY KEY,  -- '2026-04-17-part04-000012'
  part            INTEGER NOT NULL,
  mp4_time        REAL NOT NULL,
  description     TEXT NOT NULL,
  avi_effect      TEXT,
  dream_effect    TEXT,
  tags            TEXT,              -- JSON array
  clip_index      INTEGER,           -- resolved at save time
  clip_filename   TEXT,
  demo_hint       TEXT,              -- AVI name prefix (e.g. '490')
  demo_file       TEXT,              -- filled by FT-1 backfill
  servertime_ms   INTEGER,           -- filled by FT-1 backfill
  created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_annotations_part ON annotations(part);
CREATE INDEX idx_annotations_tags ON annotations(tags);
```

---

## 7. Build sequence (9 steps, ~9.5 build-days)

Day-counts are realistic for single-operator pace with TDD + superpowers discipline.

| # | Step                                     | Deliverable                                      | Day |
|---|------------------------------------------|--------------------------------------------------|-----|
| 1 | FastAPI skeleton + SQLite migrate        | `python -m creative_suite` boots, `/health` OK   | 0.5 |
| 2 | **Annotation UI end-to-end**             | **`/annotate` usable — ships first**             | 1.0 |
| 3 | Asset ingest from FULL_CATALOG.json      | `assets` table populated, /api/assets returns    | 0.5 |
| 4 | Asset browser + texture preview + md3    | `/creative` left-pane navigation                 | 1.5 |
| 5 | ComfyUI client + photoreal workflow      | Generate one variant end-to-end                  | 1.5 |
| 6 | Variant panel + approval loop            | Approve / reject / reroll, persists              | 1.0 |
| 7 | Side-by-side compare canvas              | Synced pan/zoom textures; dual md3 for models    | 1.0 |
| 8 | pk3 builder + wolfcam install hook       | `zzz_photorealistic.pk3` loads in wolfcam        | 1.5 |
| 9 | Ollama prompt assist + max-quality config | Optional prompt chips + 4K capture cvars file   | 1.0 |

Steps 1–2 on day 1 → annotation tool live before anything else.
Steps 3–8 produce first full photoreal pk3. Step 9 polish.

**First full product delivery:** after step 8, user picks one demo, runs wolfcam
re-render with `zzz_photorealistic.pk3` + §4.4 config, and we ship the resulting
clip as the reference "this is what v2 looks like." That's the proof artifact.

---

## 8. Gates & rules

- **Rule P1-J (existing):** quality ceiling — file size doesn't matter, CRF 15–17
  x265/x264/AV1 per FT-6 benchmark. Max wolfcam capture res is 4K downsampled to 1080.
- **Rule ENG-1..4 (existing):** Steam paks read-only, `zzz_*.pk3` naming, `sv_pure 0`.
- **Gate CS-1:** before step 8 ships, user approves 5 photoreal variants on
  one reference asset (proposed: `textures/base_wall/basewall01b.tga`) and
  one player skin. Prevents shipping a bad pack.
- **Gate CS-2:** before first full-demo re-render, user watches one 5-second
  pk3-loaded clip vs the baseq3 version. Confirms the pack wins alphabetically
  over `pak00.pk3` and there are no texture load failures in wolfcam console.
- **Gate ANN-1:** after step 2, user annotates 10 moments in Part 4 to stress-test
  the form ergonomics. Any friction → fix before moving to step 3.

---

## 9. Testing

- Every step has a smoke test against one reference asset
  (`textures/base_wall/basewall01b.tga`) or a small reference MD3 (rocket model).
- pytest for API routes (`tests/test_annotations.py`, `tests/test_clips.py`,
  `tests/test_pk3_build.py`).
- Manual browser gates (CS-1, CS-2, ANN-1) are explicit — not skipped.
- pyright clean before each commit (global rule).

---

## 10. YAGNI — what we are NOT building

| Cut | Reason |
|-----|--------|
| Multi-pack / `style_packs` CRUD | One pack MVP; adding later is a schema row + prompt row |
| Per-clip style switching | `clip_style_assignments` table not needed for global re-render |
| Style exploration "render in all packs" grid | Requires multi-pack first |
| Rule P1-M (pack rotation on beat) | Moot with single pack |
| Sound variants | Out of MVP scope |
| Pattern DSL / predicates library / demo-corpus scan | Stage 2 work, Phase 3 territory |
| mp4_time → servertime exact resolution | Waits on FT-1 parser output |
| Multi-user / auth | Local tool |
| npm / bundler | importmap + CDN |
| Undo history on rejected variants | Rejected status IS the history |
| Cloud ComfyUI / Ollama | Local only — `127.0.0.1:8188`, `127.0.0.1:11434` |

---

## 11. Known risks & open items

1. **Clip-list formats aren't uniform.** `phase1/clip_lists/` holds many
   `partNN_styleX.txt` variants. The annotation tool needs to know which clip
   list was actually rendered into `output/PartN.mp4`. **Mitigation:** pipeline
   writes a `render_manifest.json` next to each output mp4 naming the clip list
   it used. One-line addition to `pipeline.py`; part of step 1.
2. **PANTHEON + Title Card offset.** Rule P1-N adds a fixed 15s pre-content
   offset. Annotation resolver must subtract that before matching `mp4_time` to
   clip durations. **Mitigation:** hardcode 15s offset from config; unit-test it.
3. **ComfyUI workflow drift.** `img2img_sdxl` workflow JSON is stored under
   `creative_suite/comfy/workflows/`. If a ComfyUI update breaks node ids, the
   workflow file needs refreshing. **Mitigation:** check the workflow at app
   boot, log a warning if nodes missing — don't crash.
4. **TGA alpha.** Some baseq3 textures use 32-bit TGA with explicit alpha
   channels used as masks. PNG→TGA must preserve alpha exactly. **Mitigation:**
   test with `textures/effects/` masks first; they're the pickiest.
5. **Annotation "dream_effect" vocabulary drift.** In free-text today, needs
   future clustering. **Mitigation:** accept drift now; Phase 3 clustering job
   is a one-liner over the JSONL corpus.

---

## 12. Exit criteria (Creative Suite v2 is "done")

- `python -m creative_suite` starts cleanly on a fresh machine after `pip install -r`.
- Annotation tool survived Gate ANN-1 (10 annotations in Part 4 without friction).
- `zzz_photorealistic.pk3` built, installed, loaded by wolfcam, Gate CS-2 passed.
- One full demo re-rendered with photoreal pack, user approves the clip as "yes,
  this is the quality bar."
- Spec doc committed, implementation plan at `docs/superpowers/plans/` committed,
  pytest green, pyright green.

Everything past this point (multi-pack, per-clip switching, pattern DSL, Phase 3
scan) gets its own spec. This one closes.
