# Asset Manifest Schema + Named Workflow Registry — Design

> Design date: 2026-08-31 | **Design document only.** Nothing here has been implemented;
> no database was modified. Companion to `docs/reference/comfyui_pipeline_audit.md`, which
> establishes the on-disk facts this design responds to. Rule references are to `CLAUDE.md`
> §Phase 5 (`PH5-1..PH5-10`) and §Engine Assimilation (`ENG-1..ENG-5`).

---

## 0. Headline decision

**Extend `creative_suite/comfy/photoreal/assets.db`. Do not create a new database.**

The audit found the existing schema already covers roughly 70% of the requested manifest —
`asset_id`, `source_file`, `source_hash`, `generated_master`, and `status` all exist today
under different names, and 5,776 assets / 14,413 renders are already indexed against them.
A parallel database would fork the source of truth on day one and orphan the working
`build_uhd_pk3.py` query.

The extension is **purely additive**: new columns (all nullable or defaulted), four new
tables, zero destructive changes, zero renames of existing columns. Every current query
— including `build_uhd_pk3.py`'s `SELECT ... WHERE r.pipeline='upscale_only' AND
r.status='ok'` — keeps working untouched.

---

## 1. Requested fields → what already exists

| Requested field | Status | Lands as |
|---|---|---|
| `asset_id` | **exists** | `assets.id` (INTEGER PK AUTOINCREMENT) |
| `logical_game_path` | **new** | `assets.logical_game_path` — currently reconstructed at pack time by `build_uhd_pk3.pak00_index()` string surgery; materialize it |
| `asset_family` | **new** | `assets.asset_family` — `assets.category` exists but is a *source-tree* label, a different axis (§2.2) |
| `source_file` | **exists** | `assets.rel_path` + `assets.source` |
| `source_hash` | **exists** | `assets.sha256` |
| `generated_master` | **exists** | `renders.output_path` |
| `generated_hash` | **new** | `renders.output_sha256` |
| `comfyui_workflow` | **new** | `renders.workflow_name` → FK into the registry (§3) |
| `workflow_hash` | **new** | `renders.workflow_sha256` — pinned at generation time, not looked up later |
| `ai_model` | **new** | resolved through the registry; denormalized digest in `renders.model_fingerprint` |
| `generation_parameters` | **partial** | `renders.denoise` exists; widen to `renders.params_json` + `renders.params_sha256` |
| `runtime_derivatives` | **new** | own table — genuinely 1:N (§2.4) |
| `pack` | **new** | own table + membership table (§2.5) |
| `version` | **new** | `renders.version` + `packs.version` |
| `status` | **exists** | `renders.status` (currently `'ok'` on all 14,413 rows) |

---

## 2. The extension

### 2.0 Precondition — reconcile `_init_db` with the live DB (audit F3)

Before any migration runs, `full_overnight.py::_init_db` must be brought in line with the
database actually on disk. The audit found they have diverged: the initializer declares
`denoise REAL NOT NULL`, `style TEXT NOT NULL DEFAULT 'photoreal'`, and
`UNIQUE(asset_id, pipeline, style)`, while the live DB has none of those and instead carries
`status` and `source_type` columns the initializer never creates. **A fresh `assets.db` built
today would break `build_uhd_pk3.py`**, which queries `r.status='ok'`.

This is pre-existing breakage, not something the new schema introduces, but the migration
must not be layered on top of it. Fix `_init_db` first, then migrate.

### 2.1 `assets` — three added columns

```sql
ALTER TABLE assets ADD COLUMN logical_game_path TEXT;   -- 'models/players/xaero/xaero.tga'
ALTER TABLE assets ADD COLUMN asset_family      TEXT;   -- 'player_skin' | 'world_surface' | ...
ALTER TABLE assets ADD COLUMN has_alpha         INTEGER;-- 1|0|NULL(unknown)
CREATE INDEX IF NOT EXISTS assets_family        ON assets(asset_family);
CREATE INDEX IF NOT EXISTS assets_logical_path  ON assets(logical_game_path);
```

**`logical_game_path` carries the ORIGINAL in-pak extension**, not the staged `.png`
extension. This is the single most load-bearing column in the design, and it exists because
of the trap `build_uhd_pk3.py`'s docstring already names: shipping a `.png` where the
original was `.jpg`/`.tga` means the asset "exists" in the pack but the engine's
extension-priority lookup never loads it. Today that mapping is rebuilt from scratch on every
pack run by zipping through pak00 and doing `Path.with_suffix("")` string surgery. Storing it
makes it auditable — you can query for assets whose logical path was never resolved, instead
of finding out at pack time via a `skipped: "not in pak00"` line.

**`has_alpha` is a direct response to audit finding F1** (90/90 alpha-bearing assets lost
their alpha, and alpha was already discarded at the pak00→PNG extraction step). Without a
recorded per-asset alpha expectation there is no way to *gate* on it — see
`derivatives.alpha_preserved` in §2.4 and the ship gate in §5.

### 2.2 Why `asset_family` is not `category`

They are different axes and collapsing them is how the pack tooling gets stuck.

`assets.category` is a **source-tree label**, mechanically derived from where the file sits in
pak00 (`models/players/…` → `players`). It drives `PH5-7` FX-vs-SURFACE routing and must not
change — `route`, `category_config`, and the whole `full_overnight.py` scanner depend on it.

`asset_family` is a **semantic grouping for delivery**. The two cross-cut:

| Family | Draws from categories | Note |
|---|---|---|
| `player_skin` | `players` | subset — Xaero-only packs are a slice *within* `players` |
| `world_surface` | `textures` | |
| `world_sky` | (`env` — **currently unindexed**, audit F6) | |
| `weapon_surface` | `weapons2`, `phase5` | spans two categories |
| `hud_fx` | `gfx`, `icons`, `ui`, `wolfcam_hud`, `sprites`, `weaphits` | all FX-routed |
| `mapobject` | `mapobjects` | |
| `banner` | (generated, no pak00 source) | `pantheon_ads.py` output — no `assets` row today |
| `levelshot` | (`levelshots` — **currently unindexed**) | |

The audit's F6 gap bites here: `env` (12 skyboxes) and `levelshots` (323) have no `assets`
rows at all, because neither label appears in `full_overnight.py`'s `_FX_LABELS` or
`_SURFACE_LABELS`. Any `world_sky` family is empty until the scanner is widened. Skyboxes
additionally need seam-aware generation, which is what `WORLD_TILEABLE` in the registry is for.

The `banner` family raises a design question worth settling explicitly: `pantheon_ads.py`
output has no `assets` row because it has no pak00 source — it is generated from
`PantheonProduction.JPG` and PIL primitives. The schema handles this by allowing
`assets.rel_path` to name a synthetic source and `assets.source = 'procedural'`, so banners
can be packed and versioned through the same tables as everything else. See §3.3.

### 2.3 `renders` — provenance columns

```sql
ALTER TABLE renders ADD COLUMN workflow_name     TEXT;    -- FK -> registry (§3)
ALTER TABLE renders ADD COLUMN workflow_version  TEXT;
ALTER TABLE renders ADD COLUMN workflow_sha256   TEXT;    -- of the workflow JSON, at gen time
ALTER TABLE renders ADD COLUMN model_fingerprint TEXT;    -- 'ckpt=juggernautXL_ragnarokBy;cnet=TTPLANET_..._v2_fp16;lora=-'
ALTER TABLE renders ADD COLUMN params_json       TEXT;    -- full resolved params
ALTER TABLE renders ADD COLUMN params_sha256     TEXT;    -- digest, for cheap equality
ALTER TABLE renders ADD COLUMN output_sha256     TEXT;
ALTER TABLE renders ADD COLUMN output_width      INTEGER;
ALTER TABLE renders ADD COLUMN output_height     INTEGER;
ALTER TABLE renders ADD COLUMN version           INTEGER NOT NULL DEFAULT 1;
CREATE INDEX IF NOT EXISTS renders_workflow ON renders(workflow_name, workflow_version);
CREATE INDEX IF NOT EXISTS renders_params   ON renders(params_sha256);
```

**`params_sha256` is the fix for audit finding F4** — the 16 rows that mixed
`source_type='upscaled'` into otherwise-original `tile_d35`/`tile_d50` runs, producing 8×
output for 3 files and 2× for the other 8 *inside the same pipeline, category, and directory*.

The root cause is that `full_overnight.py` resumes by checking whether the output file
exists. That check cannot detect that the *parameters* changed between runs, so a later
`--twopass` invocation skipped 8 already-present files and generated only the 3 missing ones
under a different regime. The DB recorded the divergence in `source_type` and nothing flagged
it.

With `params_sha256` stored, the resume predicate becomes a comparison rather than an
existence test:

```python
# today  — cannot detect a parameter change
if dst.exists():
    continue

# proposed — skip only if the SAME recipe produced it
row = db.execute(
    "SELECT params_sha256, workflow_sha256 FROM renders "
    "WHERE asset_id=? AND pipeline=? AND version=?",
    (asset_id, pipe_name, version)).fetchone()
if dst.exists() and row == (want_params_sha, want_workflow_sha):
    continue
# else: regenerate, or bump version and record both
```

`workflow_sha256` is stored **at generation time**, not resolved by reading the registry
later. A workflow JSON edited after a batch would otherwise silently rewrite the history of
what produced those images. The audit computed these hashes for all 21 current workflows;
they are tabulated in `comfyui_pipeline_audit.md` §1.1 and can seed the registry directly.

`output_width`/`output_height` exist because the audit's dimension spot-check had to open
every file with PIL to compare against `assets.width`/`height`. That check should be a SQL
query, not a filesystem walk — it is the cheapest possible regression gate against both the
mixed-source-type bug and the latent-grid aspect squeeze (audit F11: 54×32 → 104×64).

### 2.4 `derivatives` — runtime forms, a real 1:N relation

`runtime_derivatives` earns its own table rather than a column because one generated master
legitimately produces several runtime forms: a 2048-clamped `.tga` for the pack, a `.jpg` at
the original extension for a different pack, a downscaled variant for a low-VRAM profile.

```sql
CREATE TABLE IF NOT EXISTS derivatives (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    render_id       INTEGER NOT NULL REFERENCES renders(id),
    kind            TEXT    NOT NULL,   -- 'pack_ready' | 'preview' | 'normal_map' | 'emissive'
    file_path       TEXT    NOT NULL UNIQUE,
    game_ext        TEXT    NOT NULL,   -- '.tga' | '.jpg' | '.png' — the ORIGINAL in-pak ext
    width           INTEGER,
    height          INTEGER,
    sha256          TEXT,
    alpha_preserved INTEGER,            -- 1|0|NULL — gate against audit F1
    max_dim_clamped INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS derivatives_render ON derivatives(render_id);
CREATE INDEX IF NOT EXISTS derivatives_kind   ON derivatives(kind);
```

`game_ext` and `max_dim_clamped` capture what `build_uhd_pk3.convert()` already does in
memory but never records: writing back at the original extension, and LANCZOS-downscaling
anything over `MAX_DIM = 2048` to respect the engine texture cap.

`alpha_preserved` is the enforcement point for audit F1. The current code has an RGBA branch
in `convert()` that **can never fire**, because no render is ever RGBA — so an alpha-bearing
`.tga` would ship opaque and render as a solid block in-game. That is contained today only by
`build_uhd_pk3.py`'s default `--categories textures players weapons2`; passing
`--categories gfx sprites` would ship broken transparency with no error. With
`assets.has_alpha` recorded and `derivatives.alpha_preserved` checked, the mismatch
`has_alpha=1 AND alpha_preserved=0` is a queryable ship-gate failure rather than something
you discover in-engine.

Fixing the underlying loss is out of scope for a schema — it requires re-extracting pak00
with alpha intact (`PH5` extraction step) and carrying RGBA through ComfyUI. The schema's job
is to make the defect *visible and gateable*, which it currently is not.

### 2.5 `packs` + `pack_members` — persisted pack identity

```sql
CREATE TABLE IF NOT EXISTS packs (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    pack_name      TEXT    NOT NULL,          -- 'zzz_uhd_01' | 'zzz_zz_pantheon_ads'
    pack_file      TEXT    NOT NULL UNIQUE,   -- absolute path to the .pk3
    load_priority  INTEGER NOT NULL,          -- explicit; see §2.6
    search_path    TEXT    NOT NULL,          -- 'gamedir' | 'baseq3'
    asset_family   TEXT,
    version        TEXT    NOT NULL,
    built_at       TEXT DEFAULT (datetime('now')),
    builder        TEXT,                      -- 'build_uhd_pk3' | 'pantheon_ads' | ...
    size_bytes     INTEGER,
    sha256         TEXT,
    status         TEXT NOT NULL DEFAULT 'built', -- built|staged|shipped|superseded
    notes          TEXT,
    UNIQUE(pack_name, version)
);

CREATE TABLE IF NOT EXISTS pack_members (
    pack_id       INTEGER NOT NULL REFERENCES packs(id),
    derivative_id INTEGER NOT NULL REFERENCES derivatives(id),
    pak_path      TEXT    NOT NULL,   -- path INSIDE the zip
    PRIMARY KEY (pack_id, derivative_id)
);
CREATE INDEX IF NOT EXISTS pack_members_deriv ON pack_members(derivative_id);
```

This is the direct answer to audit finding F5. `build_uhd_pk3.py` writes its manifest to a
single fixed path whose own comment reads *"overwritten per run; offset keeps pk3 names
distinct."* Build two families and the first family's manifest is destroyed while its `.pk3`
files remain in the gamedir — there is no record anywhere of which pack a given render
shipped in. `pack_members` makes shipped-provenance a query:

```sql
-- Which pack is currently shipping this game path, and what produced it?
SELECT p.pack_name, p.version, r.workflow_name, r.workflow_version, r.params_sha256
FROM   pack_members pm
JOIN   packs p       ON p.id = pm.pack_id
JOIN   derivatives d ON d.id = pm.derivative_id
JOIN   renders r     ON r.id = d.render_id
WHERE  pm.pak_path = 'models/players/xaero/xaero.tga'
  AND  p.status = 'shipped';
```

The JSON manifest `build_uhd_pk3.py` already emits stays as a build artifact — it is useful
for eyeballing a single run. The DB becomes the durable record.

### 2.6 `load_priority` — write the ordering down

The `zzz_` precedence scheme works today but exists only as one sentence in
`pantheon_ads.py`'s docstring plus the two filenames that happen to sort correctly:

> gamedir beats baseq3, and `zzz_zz` sorts after the `zzz_uhd_*` packs whose upscaled house
> ads otherwise win.

Two axes are in play — search path (gamedir over baseq3) and lexicographic filename order
within a path — and both are currently encoded implicitly in strings. Adding a third and
fourth asset family without writing the ordering down is exactly where this breaks. Making
`load_priority` an explicit stored integer means the intended order is asserted rather than
inferred, and a build step can verify that actual filenames still sort to match it:

| `load_priority` | Pack | Wins over |
|---:|---|---|
| 10 | `zzz_uhd_NN.pk3` (world/player/weapon UHD) | stock `pak00` |
| 20 | `zzz_skin_<style>.pk3` (player-skin variants) | UHD bodies |
| 30 | `zzz_zz_pantheon_ads.pk3` (ad boards) | everything |

Priority is intentionally sparse (10/20/30) so families can be inserted without renumbering.
`ENG-2`'s `zzz_*` naming rule is unchanged — this only records what the names already imply.

`pantheon_ads.py`'s other discipline is worth preserving as a schema-level convention rather
than a comment: *"The pack contains ONLY the four ad_content jpgs — it cannot override
unrelated map textures."* Minimal blast radius is a property you can now check, by counting
`pack_members` rows against the family's expected extent.

---

## 3. Named workflow registry

### 3.1 Format: JSON file, not a table

`creative_suite/comfy/workflows/registry.json`. It belongs in git next to the workflow JSONs
it indexes, gets reviewed in diffs, and versions with the code that consumes it — none of
which is true of a DB table. The DB references entries by `(workflow_name, workflow_version)`
and pins `workflow_sha256` at generation time, so the registry can evolve without rewriting
render history.

### 3.2 Entry shape

```jsonc
{
  "name": "PLAYER_SKIN_UHD",
  "version": "1.0.0",
  "generator": "comfyui",              // "comfyui" | "procedural"  — see §3.3
  "workflow_file": "workflows/style_photoreal.json",
  "workflow_sha256": "495a0287f062…",
  "required_models": {
    "checkpoint": {"name": "juggernautXL_ragnarokBy.safetensors", "architecture": "sdxl"},
    "controlnet": {"name": "TTPLANET_Controlnet_Tile_realistic_v2_fp16.safetensors",
                   "architecture": "sdxl"},
    "upscaler":   {"name": "4x-UltraSharp.pth"},
    "preprocessor": "TTPlanet_TileGF_Preprocessor"
  },
  "default_parameters": {
    "denoise": 0.35, "steps": 20, "cfg": 7.0,
    "sampler_name": "dpmpp_2m", "scheduler": "karras",
    "controlnet_strength": 0.9, "source_type": "upscaled"
  },
  "applies_to_families": ["player_skin"],
  "route_constraint": "surface",       // enforces PH5-7
  "notes": "denoise capped at 0.40 — a player skin IS a UV body sheet (PH5-7)."
}
```

**`architecture` is an explicit field, never inferred from the filename.** The audit found the
exact reason: `style_isometric.json` loads `stylized-isometric-sdxl.safetensors`, which is
**SD1.5 despite the "sdxl" in its name** — a discrepancy that was found and fixed at template
v4 and is recorded only in that file's `_description`. Filename-based architecture inference
would reintroduce precisely the `PH5-1` mispairing the rule exists to prevent.

**`route_constraint` makes `PH5-7` machine-checkable.** Today FX-vs-SURFACE routing lives in
`full_overnight.py`'s `_route()` and is enforced only by that script. The audit found disk
routing clean but the DB carrying 189 stale rows asserting violations that were correctly
deleted — an integrity gap a declared constraint plus a validation query would have caught.

### 3.3 `generator` — the registry must cover non-ComfyUI producers

`BANNER_GENERATION` is not a ComfyUI workflow. `pantheon_ads.py` draws banners procedurally
with PIL from `PantheonProduction.JPG` and a 20-entry `CATALOG`, with deterministic selection
seeded on `(map, frag_class, event_hash)`. Modelling it as a workflow JSON would be a lie.

The `generator` field admits both kinds. For `"generator": "procedural"`, `workflow_file`
points at the Python module and `workflow_sha256` is the hash of that module — so the same
provenance guarantee (this exact code produced this exact output) holds for both paths, and
banners version and pack through the same tables as diffusion output.

### 3.4 The nine named workflows, mapped against what exists

| Name | Backing | Status |
|---|---|---|
| `WORLD_UHD_FAITHFUL` | `upscale_only.json` (`4x-UltraSharp`, no diffusion) | **Ships today** — 5,776 renders. The `PH5-7` FX-safe path. |
| `PLAYER_SKIN_UHD` | `style_photoreal.json` @ denoise 0.30–0.40 | **Exists**, needs a family-scoped preset. Denoise cap per `model-texture-pipeline-research.md` §4 and `PH5-7`'s UV-sheet rule. |
| `WEAPON_UHD` | `style_photoreal.json` scoped to `weapon_surface` | **Exists**, needs family scoping. |
| `CINEMATIC_VARIANT` | `style_neon` / `style_chromatic` / `style_edge_chrome` | **Ships today** — 800 renders each. Model as one registry entry with a `variant` parameter, not three entries. |
| `XAERO_PANTHEON` | derived from `PLAYER_SKIN_UHD` | **New.** Prompt/palette variant plus a new `.skin` file. Per the research doc §2.4 this is a pure data change — no MD3 or geometry work. |
| `BANNER_GENERATION` | `creative_suite/engine/pantheon_ads.py` | **Ships today**, but `"generator": "procedural"` (§3.3). |
| `WORLD_TILEABLE` | — | **New.** No existing workflow does seam-aware generation. Needed for `world_surface` and especially `world_sky` (the 12 `env` skyboxes, currently unindexed per audit F6). Requires a tiling-aware sampler or a seam-blend post-pass; the audit did not measure seam quality on existing wall textures, so this needs its own E2E before batch. |
| `NORMAL_DETAIL` | — | **New.** No workflow in the repo emits a normal map. Also needs an engine-side answer: stock Q3/QL shaders do not consume normal maps, so this is blocked on a shader story, not just a workflow. Flag before committing effort. |
| `EMISSIVE_REBUILD` | — | **New.** No workflow emits emissive/glow maps. Unlike normals, this has a clean engine path — Q3 shaders already support additive glow stages — but needs per-asset shader authoring alongside the texture. |

Six of nine map onto workflows that exist; three are genuinely new, and two of those
(`NORMAL_DETAIL`, `EMISSIVE_REBUILD`) have engine-side prerequisites that should be settled
before any generation work is scheduled.

### 3.5 Registry validation

A `verify_registry.py` (sibling to the existing `verify_workflows.py`) should assert, before
any batch:

1. Every `workflow_file` exists and its SHA-256 matches `workflow_sha256`.
2. Every `required_models` entry is present in the ComfyUI models directory.
3. **No entry pairs mismatched architectures** — an `sdxl` checkpoint with an `sd15`
   controlnet, or vice versa (`PH5-1`).
4. Any entry whose controlnet is a `TTPLANET_*` SDXL tile model declares
   `preprocessor: TTPlanet_TileGF_Preprocessor`. Narrower than `PH5-10` as written, and
   matching what the code actually does — the audit found the preprocessor present in every
   SDXL-tile workflow and deliberately absent on the SD1.5 `control_v11f1e_sd15_tile` path.
5. `route_constraint` is consistent with `applies_to_families` under `PH5-7`.

Point 4 implies a small `CLAUDE.md` amendment to `PH5-10`, and points about the model table
imply one to `PH5-2` (audit F7/F8). Both are documentation corrections, listed here so they
are not lost — no rule change is proposed on the strength of this design alone.

---

## 4. Migration

Additive, reversible, and staged. No existing column is renamed or dropped; every new column
is nullable or defaulted, so **every current query keeps working** — verified specifically
against `build_uhd_pk3.py`'s `SELECT a.rel_path, r.output_path … WHERE r.pipeline='upscale_only'
AND r.status='ok' AND a.category IN (…)`, which touches no changed column.

| Step | Action | Reversible |
|---|---|---|
| 0 | **Back up `assets.db`.** 5.4 MB — copy it. | n/a |
| 1 | Reconcile `full_overnight.py::_init_db` with the live schema (§2.0, audit F3). | yes |
| 2 | `ALTER TABLE` the new `assets` and `renders` columns; create indexes. | drop columns |
| 3 | Create `derivatives`, `packs`, `pack_members`. | drop tables |
| 4 | Backfill `assets.logical_game_path` from `pak00_index()`; `assets.has_alpha` by reading source modes. Record misses rather than guessing. | re-run |
| 5 | Backfill `renders.workflow_name` / `workflow_sha256` / `model_fingerprint` from the pipeline→workflow mapping in `full_overnight.py::PIPELINE_DEFS` and the hashes in `comfyui_pipeline_audit.md` §1.1. | re-run |
| 6 | Backfill `renders.output_sha256` / `output_width` / `output_height` by walking `pipelines/`. ~14k files, one pass. | re-run |
| 7 | Write `registry.json`; run `verify_registry.py`. | delete |
| 8 | Reconcile the 189 orphan rows (audit F2) — see below. | n/a |

**Step 5 has a known limitation, and it should be recorded as data rather than papered over.**
Historic renders were produced before workflow hashing existed, so a backfilled
`workflow_sha256` asserts *"this is the current hash of the workflow file that pipeline maps
to today"* — not a verified record of what actually ran. The audit's finding F4 proves the
distinction matters: 16 rows demonstrably ran under different parameters than their pipeline
name implies. Backfilled rows should therefore carry `renders.version = 0` to mark
provenance as reconstructed, with `version >= 1` reserved for rows written by
hash-at-generation-time code. Any ship gate that requires verified provenance filters on
`version >= 1`.

**Step 8 — the 189 orphan rows.** All are `phase5_png/gfx|icons` paths whose files were
correctly deleted when the `_PHASE5_FX_SUBDIRS` rule landed. The recommendation is to
`UPDATE ... SET status='superseded_by_ph5_7'` rather than delete: it preserves the audit trail
of what was generated and why it was withdrawn, and `build_uhd_pk3.py`'s `status='ok'` filter
already excludes them. **This is a recommendation, not an action — no row was modified.**

---

## 5. Ship gates the schema makes queryable

The point of the extension is that these become SQL instead of filesystem archaeology:

```sql
-- G1: alpha regression (audit F1) — must return 0 rows
SELECT a.logical_game_path, d.file_path
FROM   derivatives d JOIN renders r ON r.id=d.render_id JOIN assets a ON a.id=r.asset_id
WHERE  a.has_alpha = 1 AND d.alpha_preserved = 0;

-- G2: mixed parameter regimes within one pipeline (audit F4) — must return 0 rows
SELECT pipeline, version, COUNT(DISTINCT params_sha256) AS regimes
FROM   renders WHERE status='ok'
GROUP BY pipeline, version HAVING regimes > 1;

-- G3: PH5-7 routing violation — must return 0 rows
SELECT a.category, r.pipeline, COUNT(*)
FROM   renders r JOIN assets a ON a.id=r.asset_id
WHERE  a.route='fx' AND r.pipeline<>'upscale_only' AND r.status='ok'
GROUP BY 1,2;

-- G4: DB/disk integrity (audit F2) — every 'ok' render has output_sha256 set
SELECT COUNT(*) FROM renders WHERE status='ok' AND output_sha256 IS NULL;

-- G5: unresolved logical path — would silently fail the extension-priority lookup
SELECT COUNT(*) FROM assets WHERE logical_game_path IS NULL;

-- G6: dimension regression (audit F11) — non-4x output on the CNN path
SELECT a.rel_path, a.width, a.height, r.output_width, r.output_height
FROM   renders r JOIN assets a ON a.id=r.asset_id
WHERE  r.pipeline='upscale_only'
  AND (r.output_width <> a.width*4 OR r.output_height <> a.height*4);
```

Run against the database as it stands today, G1 returns 90 rows, G2 flags 5 pipelines, G3
returns 0, G4 returns 14,413, and G5 returns 5,776 — which is the concise statement of what
this design is for.

---

## 6. Open questions for the user

1. **Alpha re-extraction.** Fixing F1 properly means re-extracting pak00 with alpha intact and
   carrying RGBA through ComfyUI — a re-run of the 5,776-asset base pass, not a schema change.
   Worth it only if FX/HUD families are actually in scope for the overhaul. If packs stay
   scoped to `textures`/`players`/`weapons2`, the current containment holds and the schema's
   gate is enough.
2. **`NORMAL_DETAIL` engine story.** Stock Q3/QL shaders do not consume normal maps. Is there
   an engine-side plan, or should this entry be dropped from the registry?
3. **`env` / `levelshots` indexing.** 335 unindexed files, including every skybox. In scope?
4. **Orphan-row disposition.** `status='superseded_by_ph5_7'` (recommended, preserves the
   trail) or hard delete?
