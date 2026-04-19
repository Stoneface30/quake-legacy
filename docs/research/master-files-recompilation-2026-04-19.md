# Master Files Recompilation State — 2026-04-19

**Scope:** Our ability to recompile game master files (textures, skins, shaders, models)
into 100%-owned pk3 overrides — either AI-generated (ComfyUI img2img photoreal) or
hand-crafted. End goal: ship the project without redistributing any id Software
copyrighted assets. Pattern: `zzz_photorealistic.pk3` alpha-sorted after `pak00.pk3`
per ENG-2.

---

## Executive Summary

We are **about three steps** from building a real `zzz_photorealistic.pk3`, **but the
code that does it currently lives only on branch `feature/creative-suite-v2`** — the
active branch (`design/phase1-pantheon-system`) does NOT contain the Python sources.
Only stale `.pyc` bytecode remains in `creative_suite/{pk3_build,overrides,comfy,inventory,api}/__pycache__/`.
The Steam paks (ENG-1) are accessible and authoritative (962 MB QL + 496 MB Q3A,
13,358 files catalogued in `docs/research/steam-pak-inventory-2026-04-17.md`).
The ComfyUI runtime is downloaded (portable 7z ~2 GB) with the RealVisXL 5.0 checkpoint
(6.9 GB) and xinsir Union ProMax ControlNet (2.5 GB) **already on disk**. The creative-suite
SQLite DB is empty (0 assets, 0 variants, 0 pack_builds) on this branch. Remaining
work before a real pk3 ships: (1) merge/rebase v2 sources forward, (2) run ingest
against `pak00.pk3` to populate the assets table, (3) stand up ComfyUI and actually
approve 5 variants to clear Gate CS-1, (4) configure `WOLFCAM_BASEQ3_DIR` (the
default `tools/wolfcamql/baseq3` does NOT exist). No ID-Software-copyrighted asset
is distributed by this pipeline — we only read paks locally and ship AI-generated
replacements.

---

## Steam Paks (Source of Truth — ENG-1)

All paks present and readable from this machine (verified 2026-04-19):

| Pak | Path | Size | Files |
|---|---|---:|---:|
| QL pak00 | `C:/Program Files (x86)/Steam/steamapps/common/Quake Live/baseq3/pak00.pk3` | 962 MB | 9,285 |
| Q3A pak0 | `C:/Program Files (x86)/Steam/steamapps/common/Quake 3 Arena/baseq3/pak0.pk3` | 479 MB | 3,539 |
| Q3A pak1..pak8 | same dir | 9.6 MB ea max | 534 total |

Reference texture `textures/base_wall/basewall01b.tga` — **not present under that
exact name**. Pak00 contains `textures/base_wall/basewall01bit.png` and
`basewall01bitfx.jpg`. The `_classify` function in `inventory/catalog.py` categorises
these under `surface`, which matches Gate CS-1 requirements.

Read-only discipline (ENG-4) holds — nothing modifies Steam paths.

---

## Extraction Pipeline

**No persistent extracted tree exists on this branch.** `tools/game-assets/` contains
only `q3a-extracted/demos/four.dm_68` (a demo, not an asset). No
`tools/game-assets/extracted/baseq3/` directory.

The pipeline on `feature/creative-suite-v2` does **in-memory** extraction rather than
a disk dump: `creative_suite/inventory/catalog.py::walk_pk3()` zipfile-streams pak00
and builds `CatalogEntry` dataclasses without writing files. The variant runner
(`creative_suite/comfy/runner.py::extract_asset_to_png`) pulls a single asset's bytes
on demand, decodes via Pillow, and writes the input PNG under
`storage/variants/{asset_id}/_input/{variant_id}_in.png`. Output PNG lands at
`storage/variants/{asset_id}/{variant_id}.png`.

Design choice: no FULL_CATALOG.json prerequisite. `catalog.py` honors it if present
but builds from pak direct otherwise. The 2026-04-17 inventory JSON
(`docs/research/steam-pak-manifest-2026-04-17.json`, 1.6 MB, 13,358 rows) is
documentation-grade, not a runtime artifact.

---

## Asset Catalog

`tools/game-assets/FULL_CATALOG.json` — **does not exist**. Neither on disk nor in
any branch. The config property `Config.full_catalog_json` points at this path but
no code requires it.

Runtime catalog is built by `creative_suite/inventory/`:
- `catalog.py` — `CatalogEntry` dataclass, `walk_pk3()`, `build_catalog()`, `_classify()`
  with categories: `weapon | skin | surface | effect | gfx | model | misc`
- `ingest.py` — `INSERT OR IGNORE` upsert into `assets` table, idempotent.
  `default_pk3_paths()` hard-codes the Steam paths above.
- `thumbnails.py` — unread (needed for UI).

Consumers: `creative_suite/api/assets.py` (read), `creative_suite/api/packs.py` (build).

Current DB state (`storage/creative_suite.db`, 60 KB): tables present (`assets`,
`variants`, `pack_builds`, `annotations`, `clip_durations`, `render_versions`),
**all rows zero**. Thumbnails dir has ~1,000 PNGs from a prior session but no
rows tying them to assets — likely stale.

---

## pk3 Build Pipeline (creative_suite/pk3_build + api/packs)

| File | Git status | Purpose | Status |
|---|---|---|---|
| `creative_suite/pk3_build/__init__.py` | on v2 branch, missing on active | package marker | OK |
| `creative_suite/pk3_build/png_to_tga.py` | on v2 | PNG→RGBA→32-bit TGA via Pillow | **Done + tested** (`test_png_to_tga.py`, roundtrip alpha-preservation) |
| `creative_suite/pk3_build/zip_pk3.py` | on v2 | Deterministic DEFLATE zip, sorted entries, frozen 1980 timestamps, sha256 return, zip-slip guards | **Done** |
| `creative_suite/api/packs.py` | on v2 | `/api/packs/status`, `/build` (Gate CS-1), `/install` (Gate CS-2 alpha-sort) | **Done + tested** (`test_api_packs.py`) |

`png_to_tga` forces RGBA (32-bit) because Quake shader alpha tests demand it — decals,
grates, glass break without alpha. `zip_pk3` compressesevery member with DEFLATE
(engine rejects LZMA), sorts entries, freezes timestamps → same approved-variant set
always produces byte-identical sha256 (pack_builds dedup works).

`_coerce_internal_path_to_tga` rewrites any PNG/JPG source extension to `.tga` so the
shader loader picks up our override via its vanilla TGA-first resolution order.

Known gap: `png_to_tga` tested on synthetic Pillow images; never exercised against a
real `basewall01bit.png` round-trip on `design/phase1-pantheon-system`.

---

## ComfyUI img2img Pipeline (variant generation)

| File | Git status | Purpose |
|---|---|---|
| `creative_suite/comfy/client.py` | on v2 | httpx wrapper for `/prompt`, `/upload`, `/view`, `/history`; placeholder substitution (`{{seed}}`, `{{denoise}}`, `{{prompt}}`, `{{input_image}}`, `{{negative_prompt}}`) with numeric type coercion |
| `creative_suite/comfy/runner.py` | on v2 | Synchronous background runner: zipfile-extract asset → PNG → submit → poll `/history` → fetch output → write to `storage/variants/` |
| `creative_suite/comfy/prompts.py` | on v2 | `PHOTOREAL_SEED_PROMPT` + negative; `build_final_prompt(user_suffix)` |
| `creative_suite/comfy/workflows/img2img_sdxl.json` | on v2 | SDXL img2img, 28 steps, dpmpp_2m_sde_gpu + karras, checkpoint = RealVisXL_V5.0_fp16.safetensors |
| `creative_suite/comfy/workflows/img2img_sdxl_canny.json` | on v2 | Same + xinsir Union ProMax ControlNet in canny mode, strength 0.55 |

Runtime on disk **and ready**:
- `tools/comfyui/ComfyUI_windows_portable_nvidia.7z` — 1.98 GB (not yet extracted)
- `tools/comfyui/models/checkpoints/RealVisXL_V5.0_fp16.safetensors` — 6.94 GB
- `tools/comfyui/models/controlnet/xinsir-union-promax/diffusion_pytorch_model_promax.safetensors` — 2.51 GB
- `tools/comfyui/models/vae/` — empty (SDXL VAE ships with the RealVis checkpoint)

Tests: `test_comfy_client.py`, `test_comfy_validation.py` — both use `httpx.MockTransport`,
no real ComfyUI instance required.

---

## Current Overrides (creative_suite/overrides)

**`overrides/file_io.py` is NOT about asset overrides.** It reads/writes
`part{NN}_overrides.txt` — Phase 1 **clip render** overrides (`slow`, `slow_window`,
`head_trim`, `tail_trim`, `section_role` per chunk). No connection to pk3 building.

The asset-override path is end-to-end:
`assets` row → `variants` row (ComfyUI output PNG) → approved flag → `pack_builds`
row. No intermediate "overrides" file.

---

## Gates

### Gate CS-1 — Build pre-flight
**Enforced** in `creative_suite/api/packs.py::_gate_cs1_check()`. Requires:
- `≥5 approved variants total` (status = 'approved')
- `≥1 approved in category='surface'`
- `≥1 approved in category='skin'`

`POST /api/packs/build` returns HTTP 409 with structured detail if any check fails.
Covered by `test_api_packs.py` (4 dedicated test cases: <5, no surface, no skin, pass).

### Gate CS-2 — Install verification
**Enforced** in `install_pack()`. After copying pk3 into `WOLFCAM_BASEQ3_DIR`:
1. Lists all `*.pk3` in the dir
2. Confirms our pk3 sorts **after** `pak00.pk3` alphabetically (ENG-2)
3. Returns `alpha_sort_ok: true/false` + `reminder_sv_pure: "launch wolfcam with +set sv_pure 0 (ENG-3)"`

The wolfcam smoke-test (actually launching the engine and loading the pk3) is NOT
automated — it's a manual user step triggered by the reminder string. No CI or
integration test drives wolfcam headlessly.

---

## End-to-End Dry Run

**"Can we build a zzz_photorealistic.pk3 from basewall01bit.png today?"**

| Step | Status | Action |
|---|---|---|
| 1. Steam pak accessible | READY | Verified pak00.pk3 open, 9,285 members |
| 2. Python sources on active branch | BLOCKED | Sources live on `feature/creative-suite-v2` only; need merge/rebase |
| 3. SQLite migrated | READY | `storage/creative_suite.db` exists, schema current |
| 4. assets table populated | BLOCKED | 0 rows — run `ingest(cfg, build_catalog(default_pk3_paths()))` |
| 5. ComfyUI running | BLOCKED | 7z not extracted; must unpack + launch `run_nvidia_gpu.bat` |
| 6. Checkpoints present | READY | RealVisXL + ControlNet promax on disk |
| 7. variants generated | BLOCKED | Need at least 5 API calls to `/api/comfy/queue` |
| 8. variants approved | BLOCKED | User action — `/api/variants/{id}/approve` × 5 covering surface + skin |
| 9. Gate CS-1 passes | BLOCKED | Dependent on step 8 |
| 10. pk3 written | READY when 9 passes | `/api/packs/build` produces `storage/packs/zzz_photorealistic.pk3` |
| 11. Install target exists | BLOCKED | `Config.wolfcam_baseq3 = tools/wolfcamql/baseq3` does NOT exist; real install is `WOLF WHISPERER/WolfcamQL/wolfcam-ql/` (no baseq3 subdir) — must set `WOLFCAM_BASEQ3_DIR` env var |
| 12. Gate CS-2 alpha-sort | READY when 11 resolves | Automatic check in `/api/packs/install` |
| 13. Wolfcam smoke-test (`+set sv_pure 0`) | MANUAL | No automation |

**Readiness: 3 of 13 steps ready as-is, 2 more ready once prior steps clear, 8 blocked.**

---

## Open Blockers for User

1. **Merge/rebase decision (BLOCKER #1)** — `feature/creative-suite-v2` has the
   pk3-build pipeline sources; `design/phase1-pantheon-system` does not. Per
   `SPLIT1_USER_CHECKLIST.md`, Split 1 closes first (Parts 4-12) before Split 2
   (Tr4sH Quake). Creative Suite v2 is Split 2 territory. **User must decide:**
   do we pull pk3_build onto the active branch now, or wait for Split 1 to close?
2. **Wolfcam install path (BLOCKER #2)** — `Config.wolfcam_baseq3` defaults to
   `tools/wolfcamql/baseq3/` which doesn't exist. The real wolfcam install is in
   `WOLF WHISPERER/WolfcamQL/wolfcam-ql/` but that dir has no `baseq3/` either
   (models are inside `models.7z`). User must confirm the install target: (a) extract
   models.7z to expose baseq3, (b) point config at a fresh wolfcam install, or
   (c) rely on `WOLFCAM_BASEQ3_DIR` env override for tests only.
3. **ComfyUI extraction (easy)** — `tools/comfyui/ComfyUI_windows_portable_nvidia.7z`
   is 1.98 GB and not yet extracted. Needs a 7z extraction + first-run of
   `run_nvidia_gpu.bat` to confirm the pipeline reaches `http://127.0.0.1:8188`.
4. **Gate CS-1 variant approval loop** — There is no UI on the active branch for
   reviewing/approving variants. `frontend/app.js` on v2 has it. Same blocker as #1.
5. **FULL_CATALOG.json convention** — `Config.full_catalog_json` is referenced but
   never written. If user wants an on-disk human-readable catalog (grep-able), add
   a write-out step to `build_catalog()`. Currently the in-memory catalog is
   sufficient for runtime.

---

## Files of Note

**Absolute paths (on `feature/creative-suite-v2` unless noted):**

- `G:/QUAKE_LEGACY/creative_suite/pk3_build/zip_pk3.py` — deterministic pk3 writer
- `G:/QUAKE_LEGACY/creative_suite/pk3_build/png_to_tga.py` — 32-bit RGBA TGA converter
- `G:/QUAKE_LEGACY/creative_suite/api/packs.py` — `/api/packs/{status,build,install}` + Gates CS-1/CS-2
- `G:/QUAKE_LEGACY/creative_suite/comfy/client.py` — ComfyUI httpx wrapper
- `G:/QUAKE_LEGACY/creative_suite/comfy/runner.py` — variant generation runner
- `G:/QUAKE_LEGACY/creative_suite/comfy/prompts.py` — photoreal seed + negative
- `G:/QUAKE_LEGACY/creative_suite/comfy/workflows/img2img_sdxl.json` — base SDXL workflow
- `G:/QUAKE_LEGACY/creative_suite/comfy/workflows/img2img_sdxl_canny.json` — SDXL + ControlNet
- `G:/QUAKE_LEGACY/creative_suite/inventory/catalog.py` — pak walker + classifier
- `G:/QUAKE_LEGACY/creative_suite/inventory/ingest.py` — SQLite upsert, Steam pak paths
- `G:/QUAKE_LEGACY/creative_suite/config.py` — paths incl. `packs_dir`, `wolfcam_baseq3`, `full_catalog_json`
- `G:/QUAKE_LEGACY/creative_suite/tests/test_api_packs.py` — Gates CS-1/CS-2 coverage
- `G:/QUAKE_LEGACY/creative_suite/tests/test_png_to_tga.py` — alpha roundtrip
- `G:/QUAKE_LEGACY/creative_suite/tests/test_inventory_catalog.py` — fixture pk3 ingest

**On every branch / active branch:**
- `G:/QUAKE_LEGACY/docs/research/steam-pak-inventory-2026-04-17.md` — 13,358-file catalog writeup
- `G:/QUAKE_LEGACY/docs/research/steam-pak-manifest-2026-04-17.json` — full manifest (1.6 MB)
- `G:/QUAKE_LEGACY/docs/research/steam-pak-summary-2026-04-17.json` — category counts
- `G:/QUAKE_LEGACY/tools/comfyui/ComfyUI_windows_portable_nvidia.7z` — 1.98 GB, not extracted
- `G:/QUAKE_LEGACY/tools/comfyui/models/checkpoints/RealVisXL_V5.0_fp16.safetensors` — 6.94 GB
- `G:/QUAKE_LEGACY/tools/comfyui/models/controlnet/xinsir-union-promax/diffusion_pytorch_model_promax.safetensors` — 2.51 GB
- `G:/QUAKE_LEGACY/storage/creative_suite.db` — 60 KB, schema current, zero rows
- `C:/Program Files (x86)/Steam/steamapps/common/Quake Live/baseq3/pak00.pk3` — 962 MB source of truth
- `C:/Program Files (x86)/Steam/steamapps/common/Quake 3 Arena/baseq3/pak0.pk3` — 479 MB

**Stale / phantom:**
- `G:/QUAKE_LEGACY/creative_suite/{pk3_build,overrides,comfy,inventory,api}/__pycache__/` —
  `.pyc` bytecode without matching `.py` sources on active branch (from prior v2 run)
- `G:/QUAKE_LEGACY/storage/thumbnails/*.png` — ~1,000 files with no DB rows referencing them
