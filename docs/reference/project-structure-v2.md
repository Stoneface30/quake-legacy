# QUAKE LEGACY — Project Structure v2 (Reorganization Proposal + Execution Log)

**Date:** 2026-04-17
**Status:** Safe moves EXECUTED. Risky moves PENDING USER APPROVAL (see bottom checklist).
**Source of truth for intent:** `docs/specs/2026-04-16-quake-legacy-design.md`

---

## 1. Current State — Mapped Tree (top 3 levels)

```
G:\QUAKE_LEGACY\
  CLAUDE.md                          Project instructions for Claude (live)
  README.md                          GitHub-facing project overview
  PROJECT_STRUCTURE.md               Legacy structure doc (supersede with this v2 doc)
  .gitignore                         Git exclusions (UPDATED this session)
  .git/                              (untouchable)
  .claude/                           Per-project Claude state (settings, scheduled_tasks.lock)
  .playwright-mcp/                   Playwright MCP browser artifacts (logs/page snapshots)
  _staging_cleanup/                  NEW — quarantine for items pending deletion review
  FRAGMOVIE VIDEOS/                  Reference finished videos + PANTHEON intro (UNTOUCHABLE)
  QUAKE VIDEO/                       Source AVI tiers T1/T2/T3 (UNTOUCHABLE)
  WOLF WHISPERER/                    WolfcamQL renderer + WolfWhisperer.exe (UNTOUCHABLE)
  database/                          SQLite frag store (frags.db live, schema.sql)
  docs/                              All documentation
    INDEX.md                         Master doc index
    archive/                         Archived snapshots
      2026-04-17-user-updated-docs-incoming/  Earlier snapshot from user (plans, specs, etc)
    plans/                           Multi-phase & per-phase plan markdown (5 files now)
    reference/                       Technical reference (catalogs, command docs)
      screenshots/                   NEW subdir — all reference jpgs moved here
        tribute/                     40 tribute reference frames
        pantheon-intro/              5 PANTHEON intro frames
        wipeout/                     10 wipeout reference frames
    research/                        Phase 3 AI research writeups
    reviews/                         Human review artifacts (CONSOLIDATED)
      2026-04-17-phase1-2-3-5-state-for-user-review.md
      part04/                        NEW — Part 4 v1-v4 style reviews + INDEX
    specs/                           Canonical specs (design doc, highlight criteria)
    visual-record/                   VIS-1 rule deliverables (screenshots per date)
      2026-04-16/                    5 PNG records
  game-dissection/                   Reverse-engineering workspace (716M)
    .graphify_*.json                 Graphify analysis artifacts (regenerable)
    GRAPHIFY_PLAN.md, README.md
    graphify-out/                    GRAPH_REPORT.md, graph.html, graph.json
    assets/, ioquake3-client/, q3a-engine-core/, q3a-game/, q3mme-*/, wolfcam-game/, ...
    repos/                           (empty)
  output/                            All pipeline outputs (gitignored)
    logs/                            NEW — consolidated log dir
    previews/                        14 Part*_*_preview.mp4 renders (4.3G)
    normalized/                      Normalized AVI->MP4 cfr60 clips (22G)
  phase1/                            FFmpeg assembly pipeline
    clip_lists/                      22 text files: part03-12 + style variants
    music/                           *.mp3/*.ogg + *.beats.json + helper scripts
    presets/                         grade_tribute.json
    tools/                           music_frag_matcher.py, part04_feedback_processor.py (moved)
    *.py                             assembler, beat_sync, clip_list, config,
                                     experiment, intro, inventory, normalize, pipeline,
                                     preview, render_part4, verify_env
  phase2/                            Demo parser + batch renderer
    README.md
    parse_demos.py, score_frags.py, generate_cap_cfg.py, test_results_sample10.md
    cap_out/                         Per-demo cap.cfg + manifest.json pairs
  phase3/                            AI cinematography engine
    README.md
    camera_planner.py, director.py, montage_sequencer.py, score_model.py
    test_director.py, test_output.json
  phase5/                            ComfyUI texture pipeline (3.8G in tools/game-assets)
    00_extracted/  01_png/  02_processed/  03_tga/  04_pk3/
    batch_comfyui.py, convert_*.py, extract_*.py, repack_pk3.py
  tests/                             pytest suite
    phase1/                          test_clip_list, test_config, test_inventory,
                                     test_normalize, test_pipeline, conftest.py
  tools/                             Downloaded binaries + source trees
    README.md, TOOLS.md, download_tools.py
    ffmpeg/                          (UNTOUCHABLE — live binary)
    avisynth-src/, blur/, ffmpeg-python-src/, moviepy-src/,
    vapoursynth-src/, virtualdub2-src/   Source trees (reference only)
    quake-source/                    (UNTOUCHABLE — submodule-like trees)
    game-assets/ (3.8G)              Extracted Q3A/QL assets
  wolfcam-configs/                   cameras/ and cfgs/ — both empty
```

### Heavy-dir sizes (for reference)

| Path | Size |
|---|---|
| `output/normalized/` | 22 GB |
| `output/previews/` | 4.3 GB |
| `tools/game-assets/` | 3.8 GB |
| `tools/quake-source/` | 1.2 GB |
| `game-dissection/` | 716 MB |
| `phase5/*` (combined) | ~100 MB |
| `docs/reference/` (pre-reorg) | 12 MB |

---

## 2. Problems Identified

### 2a. Cache / build bloat (SAFE, moved to `_staging_cleanup/`)
- `__pycache__/` in: `phase1/`, `phase1/tools/`, `phase3/`, `phase5/`, `tests/`, `tests/phase1/`
- `.pytest_cache/` at root
- All now in `_staging_cleanup/pycache/` and `_staging_cleanup/.pytest_cache/`

### 2b. Logs scattered
- `output/music_download.log`, `music_download_v2.log`, `music_v3.log`, `music_v4.log`
- `output/part3_full_render.log`, `part3_full_render_v2.log`, `part3_render.log`
- `phase5/batch_run.log`
- **Resolution:** All consolidated into `output/logs/`.

### 2c. Playwright MCP artifacts in repo
- `.playwright-mcp/` has 10 console/page dumps — transient debug data.
- **Resolution:** moved into `_staging_cleanup/playwright-mcp/`; added `.playwright-mcp/` to `.gitignore`.

### 2d. Two parallel review dirs: `docs/review/` and `docs/reviews/`
- Inconsistent naming. `docs/review/` held Part 4 v1-v4 style reviews + a Python feedback processor script mixed with md files.
- **Resolution:**
  - Reviews moved to `docs/reviews/part04/`
  - `docs/review/INDEX.md` moved to `docs/reviews/part04/INDEX.md`
  - `docs/review/part04_feedback_processor.py` (a tool, not a doc) moved to `phase1/tools/`
  - `docs/review/` removed (empty).

### 2e. Two parallel plan dirs: `docs/plans/` and `docs/superpowers/plans/`
- `docs/superpowers/` only held plans — unnecessary layer.
- **Resolution:** Merged all 5 plan files into `docs/plans/`; `docs/superpowers/` removed.

### 2f. `docs/reference/` mixing md and 55 loose jpgs
- Reference catalog markdown buried among reference screenshots.
- **Resolution:** All jpgs moved into `docs/reference/screenshots/{tribute,pantheon-intro,wipeout}/`.

### 2g. Root-level `PROJECT_STRUCTURE.md` drift
- Describes an older layout. This v2 doc should replace it.
- **Action pending (risky):** see Checklist item R1.

### 2h. Phase 2 probe scripts (exploratory one-offs)
- `phase2/_probe_cmdtypes.py`, `_probe_extract.py`, `_probe_servercmd.py` — underscore-prefixed exploratory scripts, not part of the live pipeline.
- **Resolution:** moved to `_staging_cleanup/`. Original names preserved.

### 2i. Gitignored but tracked/generated content
- `output/` already gitignored.
- Added to `.gitignore`: `.pytest_cache/`, `_staging_cleanup/`, `.playwright-mcp/`, `.claude/scheduled_tasks.lock`, `phase5/0[1-4]_*/`, `phase1/music/*.beats.json`, `game-dissection/.graphify_*.json`, `game-dissection/graphify-out/cache/`.

### 2j. Empty directories (not removed — harmless)
- `wolfcam-configs/cameras/`, `wolfcam-configs/cfgs/` — scaffold for future P2 work, keep.
- `game-dissection/repos/` — scaffold, keep.
- `game-dissection/graphify-out/cache/` — graphify runtime, keep.
- Empty dirs inside untouchable trees (`WOLF WHISPERER/WolfcamQL/*`, `tools/avisynth-src/filesystem`) — do not touch.

### 2k. Archive folder may be stale duplicate
- `docs/archive/2026-04-17-user-updated-docs-incoming/` contains a copy of live docs (specs, plans, research, review). Spec file is identical to live; plan file differs.
- **Action pending (risky):** see Checklist item R2.

### 2l. Inconsistent naming: `Part3_` vs `part04` vs `part05_stylea`
- Live clip lists mix `part03_stylea.txt` (lowercase) with preview outputs `Part3_styleA_preview.mp4` (PascalCase).
- Low urgency — no functional break. See Checklist item R3.

### 2m. No .dm_73 demos located in repo tree
- Scanned root — none present. Confirms gitignore is effective.

---

## 3. Target Structure (v2)

```
G:\QUAKE_LEGACY\
  CLAUDE.md, README.md, .gitignore
  FRAGMOVIE VIDEOS/   QUAKE VIDEO/   WOLF WHISPERER/      (untouchable)
  database/                                                (live)
  docs/
    INDEX.md
    specs/          -- canonical specs
    plans/          -- ALL plan docs (merged from superpowers/)
    reference/
      *.md          -- catalogs, API docs, command references
      screenshots/  -- all reference image assets
    research/       -- AI / scoring / tooling research
    reviews/        -- all human review artifacts
      part04/       -- per-Part review dirs going forward
    visual-record/  -- VIS-1 dated screenshot deliverables
    archive/        -- dated snapshots only; not for live work
  output/           (gitignored)
    logs/           -- all pipeline logs here
    previews/       -- preview renders
    normalized/     -- normalized intermediates
  phase1/  phase2/  phase3/  phase5/
  tests/
  tools/
  game-dissection/
  wolfcam-configs/
```

### Justifications
- **One review dir, one plan dir** — removes ambiguity about where a new review/plan goes.
- **screenshots/ subdir under reference** — keeps catalog markdown readable, images browsable.
- **output/logs/** — a single place to tail for pipeline debugging.
- **_staging_cleanup/** — user-visible quarantine so nothing is lost; promotes to delete once verified.
- **Keep phase1/tools/** — pipeline-adjacent helper scripts live with their phase, not in docs.

---

## 4. Execution Log — SAFE MOVES (DONE THIS SESSION)

| # | Action | From | To | Status |
|---|---|---|---|---|
| 1 | Moved `__pycache__` (6 dirs) | `phase1/`, `phase1/tools/`, `phase3/`, `phase5/`, `tests/`, `tests/phase1/` | `_staging_cleanup/pycache/` | DONE |
| 2 | Moved `.pytest_cache` | root | `_staging_cleanup/.pytest_cache/` | DONE |
| 3 | Moved Playwright MCP artifacts | `.playwright-mcp/*.log`, `*.yml` | `_staging_cleanup/playwright-mcp/` | DONE |
| 4 | Consolidated logs | 7 files in `output/`, 1 in `phase5/` | `output/logs/` | DONE |
| 5 | Consolidated reviews | `docs/review/*.md` (4 files + INDEX) | `docs/reviews/part04/` | DONE |
| 6 | Relocated feedback script | `docs/review/part04_feedback_processor.py` | `phase1/tools/part04_feedback_processor.py` | DONE |
| 7 | Removed empty `docs/review/` | — | — | DONE |
| 8 | Merged plans | `docs/superpowers/plans/*` (5 files) | `docs/plans/` | DONE |
| 9 | Removed empty `docs/superpowers/` | — | — | DONE |
| 10 | Grouped reference screenshots | `docs/reference/*.jpg` (55 files) | `docs/reference/screenshots/{tribute,pantheon-intro,wipeout}/` | DONE |
| 11 | Staged phase2 probe scripts | `phase2/_probe_*.py` (3 files) | `_staging_cleanup/` | DONE |
| 12 | Updated `.gitignore` | — | added 7 new patterns | DONE |

All moves are reversible — nothing deleted, nothing `git rm`'d. Restore by moving back out of `_staging_cleanup/`.

---

## 5. Checklist — RISKY MOVES (user sign-off required)

Mark `[x]` to approve, then ask Claude to execute.

- [ ] **R1. Replace `PROJECT_STRUCTURE.md` with this v2 doc (or delete).**
  - Reason: The root PROJECT_STRUCTURE.md describes the pre-reorg layout. Having two structure docs will drift.
  - Impact: GitHub viewers lose the top-level structure doc. Mitigation: point README.md at `docs/reference/project-structure-v2.md`.
  - Approved? [ ]

- [ ] **R2. Delete `docs/archive/2026-04-17-user-updated-docs-incoming/` after confirming no unique content.**
  - Reason: Appears to be a duplicate snapshot of live docs. Spec file is identical; plan file differs — need a manual diff pass before deletion.
  - Impact: If the plan diff contains something intentional (user-edited upload), we lose it.
  - Suggested action: first run `diff -r docs/archive/2026-04-17-user-updated-docs-incoming/ docs/` and surface deltas; only then move to `_staging_cleanup/`.
  - Approved? [ ]

- [ ] **R3. Rename preview output files to lowercase `part03_...` for consistency.**
  - Reason: `part03_stylea.txt` (clip list) vs `Part3_styleA_preview.mp4` (rendered). Same data, different casing.
  - Impact: Any script or doc referencing `Part3_styleA_preview.mp4` will break until updated. The 14 files in `output/previews/` are user-reviewed already.
  - Approved? [ ]

- [ ] **R4. Move `output/previews/_intro_trim_7s.mp4` to `phase1/tools/` or `FRAGMOVIE VIDEOS/`.**
  - Reason: This is a reusable asset (the 7s PANTHEON intro trim), not a preview output. It's regenerated from `IntroPart2.mp4` but is used as input to every Part render.
  - Impact: Scripts referencing the old path break.
  - Approved? [ ]

- [ ] **R5. Flatten `docs/superpowers/` successor: move `docs/plans/2026-04-16-full-phase-plan.md` duplicate.**
  - Reason: After R8's merge from superpowers, we now have the file twice only if the user had already merged earlier — verify no dupe, no action needed if fine.
  - Status: Verified — only one copy of `2026-04-16-full-phase-plan.md` in `docs/plans/` after merge. No action required. (Marked here for audit clarity.)
  - Approved? N/A resolved.

- [ ] **R6. Delete `_staging_cleanup/` entirely after a 1-2 week observation window.**
  - Reason: Quarantined content (pycache, probes, playwright logs) serves no purpose once confirmed stable.
  - Impact: Irreversible. Any currently-unknown dependency on one of those probe scripts would break.
  - Approved? [ ]

- [ ] **R7. Delete `output/normalized/` old-run cfr60 mp4s (22 GB) once Phase 1 renders are locked.**
  - Reason: Huge disk cost; they are intermediates, regeneratable from source AVIs via `phase1/normalize.py`.
  - Impact: Next render will take hours to regenerate.
  - Approved? [ ]

- [ ] **R8. Move `game-dissection/.graphify_*.json` (large analysis JSONs, ~3 MB total) to `_staging_cleanup/` or delete.**
  - Reason: These are graphify intermediate artifacts, regeneratable.
  - Status: Now covered by `.gitignore` so they won't re-track. No physical move required unless the user wants disk space back.
  - Approved? [ ]

- [ ] **R9. Consolidate `tools/*-src/` source trees into `tools/vendored-src/` subgroup.**
  - Reason: 6 `*-src/` dirs (avisynth, blur, ffmpeg-python, moviepy, vapoursynth, virtualdub2) clutter `tools/`.
  - Impact: `download_tools.py` path references will break.
  - Approved? [ ]

- [ ] **R10. Empty `wolfcam-configs/{cameras,cfgs}/` — delete or keep as scaffold?**
  - Reason: Empty since 2026-04-16. Phase 2 plan references them.
  - Suggestion: keep as scaffold (already tracked), add a `.gitkeep`.
  - Approved? [ ]

---

## 6. Diff Summary — What Changed This Session

### Directories created
- `_staging_cleanup/` (root)
- `_staging_cleanup/pycache/`
- `_staging_cleanup/playwright-mcp/`
- `output/logs/`
- `docs/reference/screenshots/`
- `docs/reference/screenshots/tribute/`
- `docs/reference/screenshots/pantheon-intro/`
- `docs/reference/screenshots/wipeout/`
- `docs/reviews/part04/`

### Directories removed (empty after moves)
- `docs/review/`
- `docs/superpowers/plans/`
- `docs/superpowers/`

### Files moved
- 6 `__pycache__/` trees → `_staging_cleanup/pycache/`
- `.pytest_cache/` → `_staging_cleanup/.pytest_cache/`
- ~10 Playwright MCP dumps → `_staging_cleanup/playwright-mcp/`
- 8 log files → `output/logs/`
- 5 plan markdown files → `docs/plans/`
- 5 review markdown files + INDEX → `docs/reviews/part04/`
- 1 Python script → `phase1/tools/`
- 55 JPGs → `docs/reference/screenshots/{tribute,pantheon-intro,wipeout}/`
- 3 `_probe_*.py` → `_staging_cleanup/`

### Files edited
- `.gitignore` — added 7 new patterns (see section 2i)

### No destructive operations
- No `git rm`, no `rm -rf`, no overwrites.
- Everything is reversible by moving files back from `_staging_cleanup/` or the new locations.

---

## 7. Next Steps for User

1. Review this document.
2. Tick approvals in Section 5 (Risky Moves Checklist).
3. Ask Claude to execute approved items.
4. Verify `pytest` still runs (it will regenerate `__pycache__` and `.pytest_cache` — that's fine, they're gitignored).
5. After 1-2 weeks of stable running, approve R6 to permanently discard `_staging_cleanup/`.
