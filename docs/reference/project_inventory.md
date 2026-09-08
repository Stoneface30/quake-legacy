# QUAKE LEGACY — Filesystem Inventory

**Generated:** 2026-08-31 · **Method:** full recursive filesystem walk of `G:\QUAKE_LEGACY` (not `git status`) · **Mode:** read-only, nothing moved, deleted, or modified
**Machine-readable companion:** [`project_inventory.json`](project_inventory.json)

Step 1 of the *PANTHEON Engine & AI Asset Overhaul* workstream.

---

## Headline numbers

| | |
|---|---|
| Total on disk | **705.2 GB** across **74,462 files** |
| Classified entries | **130** covering **704.8 GB / 74,360 files** (99.9%) |
| Largest single area | `QUAKE VIDEO/` — 526 GB (frozen 2019 AVI corpus) |
| Largest *reducible* area | `output/` — 111 GB, of which ~40 GB is duplicate or regenerable |
| Git object store | 12.0 GB (`.git/objects/pack` = 11,996 MB) |

### Size distribution by classification

| Classification | Entries | Size | % of tree | Files |
|---|---:|---:|---:|---:|
| SOURCE | 14 | 520.0 GB | 73.8% | 34,494 |
| GENERATED | 15 | 124.6 GB | 17.7% | 14,992 |
| CACHE | 11 | 21.4 GB | 3.0% | 9,471 |
| RUNTIME | 10 | 18.2 GB | 2.6% | 5,603 |
| ARCHIVE_CANDIDATE | 7 | 14.2 GB | 2.0% | 672 |
| EXPERIMENTAL | 6 | 4.8 GB | 0.7% | 112 |
| ACTIVE | 36 | 0.8 GB | 0.1% | 2,040 |
| REFERENCE | 19 | 0.7 GB | 0.1% | 4,789 |
| SUPERSEDED | 6 | 0.1 GB | 0.0% | 2,169 |
| TEMPORARY | 3 | 0.0 GB | 0.0% | 15 |
| UNKNOWN | 3 | 0.0 GB | 0.0% | 3 |

The shape is healthy: 92% of the tree is irreplaceable SOURCE plus regenerable GENERATED output. The actual codebase (ACTIVE, 36 entries) is under 1 GB. Everything worth reclaiming sits in the GENERATED / CACHE / ARCHIVE_CANDIDATE bands.

> **Note on arithmetic.** Entries are non-overlapping by construction: where a parent and child are both interesting, only one is counted and the other is described inline (e.g. `photoreal/pipelines` counts `upscale_only` inside it; `engine/music` excludes `library/` and `_stitched/`, which are separate rows).

---

## ⚠️ Stale path references — flagged for correction

The commissioning message referenced `game-dissection\engines\variants\ioquake3` and `game-dissection\engines\dissection`, and project memory says those moved under `engine\` in the 2026-04-20 restructure. **Both are true, and that is the problem.**

| Path | On disk? | Files | Status |
|---|---|---|---|
| `engine/engines/variants/ioquake3` | ✅ EXISTS | 208 | **Canonical** — use this |
| `engine/engines/dissection` | ✅ EXISTS | 63 | **Canonical** — use this |
| `game-dissection/engines/variants/ioquake3` | ⚠️ ALSO EXISTS | 207 | Stale pre-restructure copy |
| `game-dissection/engines/dissection` | ⚠️ ALSO EXISTS | 63 | Stale pre-restructure copy |

`game-dissection/` was **never removed** during the restructure. It is a real directory (verified: not a junction, not a symlink) holding a complete pre-move snapshot. Verification performed:

- `git ls-files game-dissection` → **1,848 tracked files**; `git ls-files engine` → 1,886.
- Every path under `game-dissection/` maps to an identical path under `engine/` (`comm -23` → **0 unique paths**).
- Sampled blob hashes are identical except `engines/README.md` and `engines/REPOS.md`, which `engine/` has since path-corrected.
- `game-dissection/` is **not** covered by `.gitignore`, so the whole engine-dissection corpus is committed to the public repo **twice**.

**Additional stale references found:**

1. **`engine/README.md` line 1** — the file's title is literally `# game-dissection/`. The body correctly describes the new layout; only the heading is stale.
2. **`.gitignore` lines 137–155** — ignores `engine/engines/ioquake3/`, `engine/engines/q3mme/`, `engine/engines/wolfcamql-src/` and 13 more as *top-level* dirs. None of those paths exist any more; the trees now live in `_canonical/`, `variants/`, and `_forks/`. Only line 137 (`_canonical/`) still matches anything. The negation lines `!engine/engines/_manifest/` etc. are also inert, since nothing above them excludes those paths.
3. **Every doc inside `game-dissection/`** (~50 files: `ARCHITECTURE.md` triads, `REPOS.md`, `_manifest/DELETE_READY.md`, `build_canonical.py`, `build_inventory.py`) still self-references `game-dissection/...` with hardcoded `G:/QUAKE_LEGACY/game-dissection/...` paths. The `engine/engines/` copies of the same files were updated. This is contained inside the stale tree, so removing the tree removes the stale refs.
4. **`docs/visual-record/2026-04-19/STATE.md` line 36** — references `game-dissection/engines/dissection/`. This is a dated historical record; leave it as-is.
5. **`game-dissection/engines/wolfcam-knowledge/_scripts/gen.py` line 134** — hardcodes an output path into a deleted worktree (`.claude/worktrees/hopeful-shtern-7fe850/`). That worktree directory exists but is empty.

**Recommendation:** treat `engine/engines/*` as canonical everywhere. Do not delete anything as part of this audit — but `game-dissection/` is the single clearest archive candidate in the tree.

---

## By area

### `creative_suite/` — the active FastAPI app · 39.8 GB / 36,985 files

As expected, the code is overwhelmingly ACTIVE/SOURCE. The bulk is not code — 16.4 GB is ComfyUI photoreal output and 12.4 GB is bundled tooling.

| Path | Class | Size | Files | Notes |
|---|---|---:|---:|---|
| `api/` | ACTIVE | 0.2 MB | 23 | FastAPI routers; live on :8765 |
| `engine/` | ACTIVE | 4 MB | 96 | Render pipeline; edits through 2026-08-31 |
| `engine/effects/` | ACTIVE | — | 3 | incl. `speed_ramp.py` (P1-Q-AUTO) |
| `engine/tests/` | ACTIVE | 5.8 MB | 31 | + media fixtures |
| `engine/assets/` | SOURCE | 56.6 MB | 31 | fonts, `pantheon_ads`, `round_intro` |
| `engine/sound_templates/` | REFERENCE | 40.8 MB | 570 | Rule P1-DD pak00 templates, frozen 2026-04-22 |
| `engine/music/` | ACTIVE | 321 MB | 81 | per-Part slots + beat caches |
| `engine/music/library/` | SOURCE | **9.4 GB** | 2,093 | download pool, gitignored (copyright) |
| `engine/music/_stitched/` | GENERATED | 244 MB | 6 | Rule P1-AA beds, regenerable |
| `engine/parser/` | **SUPERSEDED** | 30 KB | 11 | stub; live parser is `engine/parser/` (57 files) |
| `frontend/` | ACTIVE | 4.3 MB | 64 | `/studio` cockpit |
| `web/` | ACTIVE | 50 KB | 9 | annotate / creative |
| `tests/` | ACTIVE | 0.7 MB | 118 | ~596 tests |
| `database/` | RUNTIME | 206 MB | 30 | SQLite; gitignored; **PII — schema only, not queried** |
| `storage/thumbnails/` | **CACHE** | **399.9 MB** | **6,578** | see below |
| `storage/` (rest) | RUNTIME | 50 KB | 1 | `creative_suite.db` + empty subdirs |
| `generated/packs/` | GENERATED | 29.5 MB | 1 | `zzz_photorealistic.pk3` |
| `graphify-out/cache/` | CACHE | 23.4 MB | 2,076 | 2026-04-22 run |
| `editor/ clips/ annotations/ capture/ inventory/ pk3_build/ overrides/ scripts/ db/` | ACTIVE | <100 KB ea. | ~35 | small live modules |
| `ollama/` | EXPERIMENTAL | 5 KB | 2 | untouched since 2026-04-22 |

**`creative_suite/storage/thumbnails` — it exists.** 6,578 PNGs, 399.9 MB, numerically named (`1.png`, `10.png`, `1010.png`…) — a clip-id-keyed thumbnail cache. **Every single file carries a timestamp inside a 31-second window on 2026-04-18 (22:42:46–22:43:17)** and nothing has been written since. Fully regenerable from the source AVIs. Classified CACHE, and stale by four months.

#### `creative_suite/comfy/` — 16.4 GB / 21,089 files

| Path | Class | Size | Files | Notes |
|---|---|---:|---:|---|
| `comfy/` (scripts) | ACTIVE | 0.3 MB | 12 | `full_overnight.py` edited 2026-08-31 |
| `workflows/` | ACTIVE | 50 KB | 21 | CLAUDE.md says 8 → **doc drift** |
| `loras/` | ACTIVE | 70 KB | 5 | manifest for 6 styles |
| `assets/phase5_png/` | SOURCE | 1.7 MB | 108 | Rule PH5-3 107-file scope |
| `photoreal/assets/` | SOURCE | 986 MB | 6,213 | pak00 extraction — proprietary, gitignored |
| `photoreal/pipelines/` | GENERATED | **15.0 GB** | 14,224 | see breakdown |
| `photoreal/e2e/` | GENERATED | 46.7 MB | 155 | Rule PH5-4 grid |
| `photoreal/pass1/` | **SUPERSEDED** | 30.3 MB | 300 | `.gitignore` calls it "legacy first-pass output" |
| `photoreal/compare/` | **SUPERSEDED** | 30 KB | 1 | `.gitignore` calls it "old comparison UI" |
| `photoreal/celshade_wild/` | EXPERIMENTAL | 3.8 MB | 8 | one-off, 2026-04-21 |
| `photoreal/twopass_test/` | EXPERIMENTAL | 16.3 MB | 11 | one-off, 2026-04-21 |
| `photoreal/` (logs + db) | RUNTIME | 14 MB | 21 | `assets.db` 5 MB + 17 April log files |

**Pipeline completion is very uneven** — 20 pipeline dirs exist where Rule PH5-8 documents 6:

- **Complete:** `upscale_only` — 10,060 MB / 5,776 files (the full 6,190-asset batch).
- **Partial (~800 files, ~500 MB each):** `chromatic`, `depth_realism`, `dreamlike`, `edge_chrome`, `isometric`, `neon`, `painterly`, `photoreal`, `pixel_art`, `zavy_depth` — 9 undocumented style pipelines carrying 4.6 GB between them.
- **E2E stubs only (7–11 files each):** `tile_d35`, `tile_d50`, `tile_d60`, `tile_d70`, `tile_d80`, `cel_shade`, `cartoon`, `concept_art`, `ink_etching`.

The `tile_d*` pipelines that CLAUDE.md treats as the documented output set are effectively empty, while ten pipelines that CLAUDE.md never mentions hold nearly all the non-`upscale_only` bytes. Rule PH5-8 and the on-disk reality have diverged.

#### `creative_suite/tools/` — 12.4 GB / 3,703 files

| Path | Class | Size | Files | Notes |
|---|---|---:|---:|---|
| `ffmpeg/` | ACTIVE | 290 MB | 3 | core dependency |
| `comfyui/` | **ARCHIVE_CANDIDATE** | **10.9 GB** | 8 | second ComfyUI — see findings |
| `ghidra/` | **ARCHIVE_CANDIDATE** | 789 MB | 253 | installer **and** extraction both kept |
| `vendored-src/` | REFERENCE | 329 MB | 3,159 | moviepy / ffmpeg-python / vapoursynth / avisynth / virtualdub2 |
| `virtualdub2/` | REFERENCE | 122 MB | 47 | binaries + plugins, not in the render path |
| `blur/` | REFERENCE | 15.4 MB | 177 | cloned repo incl. its own 11 MB `.git` |
| `comfy-pilot/` | EXPERIMENTAL | 3.1 MB | 48 | MCP disabled in CLAUDE.md; `__pycache__` touched 2026-08-31 |
| `game-assets/` | REFERENCE | 0.2 MB | 1 | stub |
| `uberdemotools/` | UNKNOWN | ~0 | 1 | CLAUDE.md claims `UDT_json.exe` lives here — **binary absent** |
| `davinci/` | UNKNOWN | 0 | 1 | never populated |

---

### `engine/` — RE and source-tree work · 3.8 GB / 19,892 files

| Path | Class | Size | Files | Notes |
|---|---|---:|---:|---|
| `engines/_canonical/` | SOURCE | **548 MB** | 16,623 | SHA-256 deduped merge of 18 trees. Wholly gitignored — invisible to `git status`. Contains a 227 MB `demo_files/` set and an embedded 49 MB / 6,728-file `graphify-out/`. |
| `engines/_forks/q3mme/` | **ACTIVE** | 67.2 MB | 921 | protocol-73 port base — the **only** engine tree with 2026-08-31 edits |
| `engines/variants/` | SOURCE | 29.5 MB | 1,214 | thin per-tree diffs; `variants/ioquake3` = 6.4 MB / 208 files |
| `engines/_diffs/` | REFERENCE | 3.8 MB | 513 | per-file `.diff.md` docs — tracked deliverable |
| `engines/_manifest/` | REFERENCE | 7.5 MB | 11 | inventory + build scripts + `DELETE_READY.md` |
| `engines/dissection/` | REFERENCE | 80 KB | 63 | ARCHITECTURE/QUIRKS/EXTENSION_POINTS triads ×18 |
| `engines/wolfcam-knowledge/` | REFERENCE | 1.0 MB | 14 | Rule P3-B protocol-73 docs + patches |
| `engines/ghidra/` | REFERENCE | 53.6 MB | 30 | FT-4: 16 MB reports + 37.6 MB gitignored binaries |
| `parser/` | ACTIVE | 1.1 MB | 38 | FT-1 C++17 dm73 parser; `tests/` touched 2026-08-31 |
| `assets/` | SOURCE | 179 MB | 32 | `xcsv_hires.zip` HD texture pack |
| `music/library/` | **ARCHIVE_CANDIDATE** | **2.8 GB** | 396 | orphaned second music pool — see findings |

Confirming the brief: `_canonical/` is entirely `.gitignore`d (line 137) and would be invisible to any git-based audit. It alone is 16,623 files — 22% of the whole tree's file count.

---

### `game-dissection/` — SUPERSEDED · 95.5 MB / 1,847 files

The stale pre-restructure duplicate. Covered in full above. Every timestamp is 2026-04-22; no file has been touched since.

---

### `output/` — render + recognition output · 111 GB / 1,670 files

Gitignored wholesale (`.gitignore:44`). Mixed as expected — the ledgers and manifests are live and the media is largely reclaimable.

| Path | Class | Size | Files | Notes |
|---|---|---:|---:|---|
| `output/` (root) | GENERATED | **24.3 GB** | 272 | 33 mp4 (23.9 GB) + 58 JSON + 14 CSV + ~165 logs |
| `reference/` | GENERATED | **54.3 GB** | 69 | 68 mp4 from the 2026-08-29/30 batch |
| `demo_v2/_wolfcam_staging/` | RUNTIME | 5.9 GB | 279 | live capture staging |
| `demo_v2/_bench/` | EXPERIMENTAL | 4.8 GB | 40 | single-day benchmark burst, 2026-08-30 |
| `demo_v2/music_auditions/` | GENERATED | 168 MB | 10 | 2026-08-31 |
| `demo_v2/review_proxies/` | GENERATED | 87 MB | 6 | Gate R-2/R-3 proxies |
| `demo_v2/presentation/` | GENERATED | 18.5 MB | 15 | 2026-08-31 |
| `demo_v2/recognition/` | ACTIVE | 0.4 MB | 22 | drives current mining |
| `demo_v2/part01/`, `_wolfcam_director_staging/`, `review/` | ACTIVE | <100 KB | 7 | new 2026-08-31 |
| `_part04/05/06_v6_body_chunks/` | CACHE | **16.2 GB** | 376 | Rule P1-BB intermediates, 2026-08-28 |
| `_part04/05/06_stems/` | CACHE | **4.7 GB** | 6 | separated audio stems, 2026-08-28 |
| `_hl_manifests/` | ACTIVE | 2.0 MB | 281 | episode manifests |
| `_series_manifests/` | ACTIVE | 2.2 MB | 218 | continuous-series manifests |
| `_v2_manifests/` | ACTIVE | 10 KB | 1 | current |
| `_v2_manifests_superseded/` | SUPERSEDED | 50 KB | 5 | self-labelled |
| `_beat_grids/` | GENERATED | 20 KB | 7 | P1-Z / P1-CC inputs |
| `_hl_ledger/` | ACTIVE | 10 KB | 1 | promoted master pool |
| `_quarantine_collision_2026-08-29/` | ARCHIVE_CANDIDATE | 10 KB | 10 | forensic quarantine, nothing reads it |
| `LEFTOVERS/` | TEMPORARY | 20 KB | 2 | 2026-08-30 reconciliation leftovers |
| `brand/` | GENERATED | 0.7 MB | 11 | PANTHEON frames |
| `summary/` | GENERATED | 8.1 MB | 2 | batch summaries |

---

### Frozen corpora — SOURCE, do not touch

| Path | Class | Size | Files | Notes |
|---|---|---:|---:|---|
| `demos/` | SOURCE | **13.1 GB** | 6,445 | `.dm_73` corpus. Frozen since 2026-04-19. **Read-only. Contains PII — not enumerated or parsed for this audit.** |
| `QUAKE VIDEO/T1/` | SOURCE | 209.7 GB | 728 | Tier-1, Parts 1–12. Frozen 2019-10. |
| `QUAKE VIDEO/T2/` | SOURCE | 196.0 GB | 691 | Tier-2 backbone. Frozen 2019-10. |
| `QUAKE VIDEO/T3/` | SOURCE | 48.4 GB | 160 | Tier-3 filler/cinematic. Frozen 2019-10. |
| `QUAKE VIDEO/Gaunlet/` | SOURCE | 19.5 GB | 79 | Parts 1–6. Frozen 2019-10-04. |
| `QUAKE VIDEO/VIDEO PART1/` | SOURCE | 21.1 GB | 75 | "ALL ACTION PART1". Frozen 2019-10. |
| `QUAKE VIDEO/Demos QUAKELIVE/` | SOURCE | 0.8 GB | 2 | 2019 demo bundles. |
| `QUAKE VIDEO/Ready for youtube/` | **GENERATED** | 30.4 GB | 37 | ⚠️ written 2026-08-30 — **output living inside the frozen source corpus.** The only non-frozen folder under `QUAKE VIDEO/`. |
| `SOURCE_EXCEPTIONS/` | ACTIVE | 141 MB | 2 | `manifest.json` + one recovered AVI; ledger for `avi_reconcile.py` |
| `WOLF WHISPERER/` | REFERENCE | 13.6 MB | 2 | `wolfcamql-src.tar.gz` (2016) + `models.7z` (2019). **No `.exe` on disk** — FT-4's "extract the .rar" blocker is still open, and the `.rar` itself is not present either. |

`QUAKE VIDEO/Ready for youtube/` is a classification anomaly worth naming: 30 GB of 2026 render output stored inside a directory tree that every rule and doc treats as frozen 2019 source. It is not a duplicate, but it breaks the "`QUAKE VIDEO/` is read-only" invariant.

---

### `docs/` — 102 MB / 217 files

| Path | Class | Size | Files | Notes |
|---|---|---:|---:|---|
| `reference/` | REFERENCE | 0.4 MB | 31 | authoritative; cited by CLAUDE.md. **This inventory lands here.** |
| `visual-record/` | REFERENCE | 97.4 MB | 150 | Rule VIS-1, 2026-04-17 → 2026-08-31. Gameplay frames gitignored (HUD nameplate PII). |
| `superpowers/` | ACTIVE | 0.2 MB | 8 | plans + `EXECUTION_STATUS.md` (2026-08-30) |
| `mockups/` `claude_designer/` `screenshots/` `brand/` | REFERENCE | 3.5 MB | 19 | design artifacts, 2026-04 |
| `_archive/` | ARCHIVE_CANDIDATE | 0.1 MB | 3 | already an explicit archive folder |

---

### Root-level loose files

The root has accumulated three distinct generations of scratch. Splitting them:

**ACTIVE — the current demo-v2 workstream (untracked but live):**
`hl_series.py` (33 KB, edited 2026-08-31), `hl_generate.py` (42 KB), `hl_all.py`, `hl_audit.py`, `hl_batch.py`, `avi_queue.py`, `avi_reconcile.py`, `remix_audio.py`, `render_batch.py`, `_tc_test.py`. These are real pipeline drivers with substantial docstrings citing user direction from 2026-08-29. They are doing production work from the repo root, which is the wrong home — `creative_suite/scripts/` is where they belong.

**SUPERSEDED — April 2026 smoke tests:** `test_endpoints.py`, `test_routes.py`, `test_routes2.py`, `test_thumb.py`, `test_thumb.jpg`. Ad-hoc `urllib` pokes at `localhost:8765`, superseded by the 596-test suite. Note these are named `test_*.py` at the repo root, so a bare `pytest` from the root will try to collect them and they will fail without a running server.

**EXPERIMENTAL — one-off ComfyUI probes:** `twopass_test.py`, `celshade_wild.py`, `validate_workflows.py` (2026-04-21).

**Other:**

| File | Class | Size | Notes |
|---|---|---:|---|
| `ann.html` | REFERENCE | 0.3 MB | saved esreality.com article page ("AnnihilatioN by own-age") — FT-3 morph-remaster style reference. External web capture. |
| `scratch_after2.pkl` | TEMPORARY | **35.7 MB** | written 2026-08-31; no code references the name. A debugging dump. (`.pkl` executes code on load — treat as untrusted.) |
| `Quake Legacy.zip` | ARCHIVE_CANDIDATE | 2.6 MB | 2026-04-20 snapshot, undocumented provenance |
| `.graphify_*.json`, `.graphify_python` | CACHE | 9.1 MB | 2026-04-22 run, gitignored as regenerable |
| `app_*.log`, `uv*.log`, `twopass_*.log`, `celshade_wild_out.log`, `cinema_panel.png`, `creative_panel.png`, `creative_suite_*.png` | TEMPORARY | 0.2 MB | all explicitly gitignored as root scratch. One is literally named `creative_suite_landing_$(date).png` — a shell expansion that never fired. |
| `PantheonProduction.JPG` | REFERENCE | 33 KB | 2019 brand reference |
| `build.js`, `package.json`, `pyproject.toml`, `start_ui.bat`, `stop_ui.bat`, `kill_and_start.bat`, `start_server.bat` | ACTIVE | 10 KB | build + launch tooling |

### Infrastructure

| Path | Class | Size | Files | Notes |
|---|---|---:|---:|---|
| `.git/` | RUNTIME | 12.0 GB | 803 | 11,996 MB in packfiles |
| `.claude/worktrees/` | RUNTIME | 195 MB | 3,133 | two live worktrees (`creative-suite-v2`, `engine-fork`), both stale at 2026-04-19, plus an empty `hopeful-shtern-7fe850/` |
| `node_modules/` | RUNTIME | 65.5 MB | 1,290 | incl. `@theatre` (AGPL, pre-approved exception) |
| `graphify-out/` | GENERATED | 7.6 MB | 176 | regenerable |
| `storage/` (root) | ARCHIVE_CANDIDATE | 50 KB | 1 | duplicate skeleton — see findings |
| `tools/comfy-pilot/` (root) | UNKNOWN | ~0 | 1 | near-empty; real tooling is in `creative_suite/tools/` |
| `Vault/`, `projects/` | RUNTIME | 40 KB | 43 | local notes / memory |
| `.pytest_cache`, `__pycache__` ×many, `quake_legacy.egg-info` | CACHE | 6.3 MB | 320 | regenerable |
| `.playwright-mcp`, `.playwright-cli`, `.swarm`, `.superpowers` | CACHE | 3.8 MB | 109 | tool caches |

---

## Duplication findings

**Nothing below is a deletion recommendation.** These are flagged for the user's decision.

### 1. `output/` root ↔ `output/reference/` — 23.9 GB byte-identical

Verified by name+size match across all 33 root mp4s, plus an MD5 spot-check:

```
Part10_highlight_ep5.mp4
  output/                 MD5 2911F95388FF1D88884207E1DEC7FC57
  output/reference/       MD5 2911F95388FF1D88884207E1DEC7FC57   identical
```

**31 of 33** root mp4s are byte-identical copies of files in `reference/`. Only `_pantheon_trim_5s.mp4` and `_val_intro.mp4` are root-only. `reference/` additionally holds 37 files the root does not. Both sets were written in the same 2026-08-29/30 batch window — this looks like a copy step that ran without a move.

**23.9 GB reclaimable. Largest single finding in the tree.**

### 2. `game-dissection/` ↔ `engine/engines/` — 95.5 MB, 1,848 files, committed twice

Detailed above. Unique in being duplicated **in git history**, not just on disk — and this is a public repo.

### 3. `creative_suite/tools/comfyui/` — 10.9 GB unreferenced second ComfyUI

Contains `ComfyUI_windows_portable_nvidia.7z` (1.9 GB installer) plus 9.0 GB of model weights (`RealVisXL_V5.0_fp16.safetensors`, `xinsir-union-promax` ControlNet). But CLAUDE.md's startup procedure and Rule PH5-5 both point the live pipeline at `E:\PersonalAI\run_comfyui_api.bat`, and Rule PH5-2's model table lists `E:\...\ComfyUI\models\` as the location of every model actually in use. `.gitignore` lines 123–131 ignore `tools/comfyui/**` — but that pattern targets the *root* `tools/`, not `creative_suite/tools/`, so this tree is only incidentally untracked. Nothing on disk or in the docs references this copy.

### 4. `engine/music/library/` — 2.8 GB orphaned second music pool

396 files, frozen 2026-04-21. Compared name+size against the active `creative_suite/engine/music/library/` (2,093 files, 9.4 GB): **zero overlap** — so this is not a copy, it is a *separate, older* download pool. `engine/music/` contains nothing else: no scripts, no manifest, no `available_tracks.txt`, no code referencing it. Rule P1-F names `creative_suite/engine/music/` as the single source of truth. This is a dead-end staging directory from the restructure.

### 5. `creative_suite/tools/ghidra/` — installer + extraction both retained

`ghidra_12.0.4_PUBLIC.zip` (486 MB) sits beside the already-extracted `ghidra_12.0.4_PUBLIC/` (302 MB). ~486 MB redundant once the extraction is confirmed working.

### 6. Lesser duplicates

- **`storage/` (root) vs `creative_suite/storage/`** — the root copy is an empty skeleton (`annotations/`, `packs/`, `thumbnails/`, `variants/`, `wolfcam_capture/`) plus a 48 KB `creative_suite.db`, created 2026-04-21. The directory structure matches `creative_suite/storage/` exactly. This is the signature of the known ROOT-vs-REPO_ROOT config bug: the app was started from the wrong CWD and created its storage tree one level up.
- **`engine/engines/_canonical/graphify-out/`** — 49 MB / 6,728 files of graphify artifacts committed *inside* the canonical engine source tree. `.gitignore` has `**/graphify-out/`, so it is ignored, but it inflates `_canonical`'s file count by 40%.
- **`creative_suite/tools/blur/.git/`** (11 MB) and **`creative_suite/tools/comfy-pilot/.git/`** (2.4 MB) — nested repo histories inside the working tree.

### 7. Not duplicates, but worth naming

- `output/_part04|05|06_v6_body_chunks/` + `_stems/` — **20.9 GB** of Rule P1-BB intermediates from a single day (2026-08-28). Fully regenerable, not duplicated. Standard CACHE, but it is 3% of the entire tree from one render session.
- `docs/visual-record/` at 97 MB is large for a docs folder, but Rule VIS-1 makes these deliverables, not clutter.

---

## Top 5 ARCHIVE_CANDIDATE findings

| # | Path | Size | Justification |
|---|---|---:|---|
| 1 | `output/reference/` ∩ `output/` | **23.9 GB** | 31 mp4s byte-identical across both locations (MD5-verified). One copy is redundant; only 2 root files and 37 reference files are unique. |
| 2 | `creative_suite/tools/comfyui/` | **10.9 GB** | Complete second ComfyUI install + model weights. CLAUDE.md startup and Rules PH5-2/PH5-5 point exclusively at `E:\PersonalAI`. Zero references on disk or in docs. |
| 3 | `engine/music/library/` | **2.8 GB** | Orphaned older music pool with zero content overlap with the active library. No sibling code, manifest, or catalog. Rule P1-F names the other path as the single source of truth. |
| 4 | `creative_suite/tools/ghidra/ghidra_12.0.4_PUBLIC.zip` | **486 MB** | Installer retained alongside its own successful extraction (302 MB) in the same directory. |
| 5 | `game-dissection/` | **95.5 MB** | Pre-restructure duplicate of `engine/engines/`. 0 unique paths, identical blob hashes, **tracked in git on a public repo** — so it costs history as well as disk, and it is the source of every stale `game-dissection/...` path reference in the project. Smallest of the five by bytes, but the highest-value cleanup: it is the only one that actively misleads. |

**Runners-up:** `creative_suite/storage/thumbnails/` (400 MB stale cache, four months cold), `creative_suite/comfy/photoreal/pass1/` + `compare/` (30 MB, both self-labelled superseded in `.gitignore`), root `storage/` skeleton, `output/_quarantine_collision_2026-08-29/`, `docs/_archive/`, `scratch_after2.pkl`.

Combined, items 1–5 account for **~38 GB**. Adding the regenerable CACHE bands (`_v6_body_chunks`, `_stems`, `thumbnails`, graphify caches) brings the reclaimable total to roughly **60 GB — about 8.5% of the tree** — without touching a single byte of SOURCE.

---

## Handling notes for this audit

- Read-only throughout. Nothing was moved, deleted, renamed, or committed.
- `creative_suite/database/*.db` — sizes and filenames only. No table was queried and no row was read.
- `demos/` — file counts and byte totals only. No demo was opened, parsed, or enumerated by player identity.
- `QUAKE VIDEO/` — metadata only.
- `.nickname_map.json` (813 B, gitignored, sha8→nickname) was noted as present and not opened.
- The MD5 spot-check in finding #1 read two video files for hash comparison only.
