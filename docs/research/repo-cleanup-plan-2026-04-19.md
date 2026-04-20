# Repo Cleanup Plan — 2026-04-19

**Author:** repo-cleanup planning agent (READ-ONLY; this doc proposes, it does not execute).
**Scope:** `G:\QUAKE_LEGACY` (excluding the 5 in-flight-agent paths listed below).
**Bar:** Zero net information loss. Everything archived stays on disk, grep-able.

## Hard-constraint paths (NOT touched by this plan)

Left alone entirely because other agents are in flight or they are user-owned:

- `tools/quake-source/**` (engine-unification agent)
- `engine/**` (engine-unification agent)
- `docs/reference/**` (Q3A-ingestion agent)
- `phase2/dm73parser/**` (engine-unification agent)
- `.claude/worktrees/engine-fork/**` (active ENG-1 engine fork work)
- `QUAKE VIDEO/`, `FRAGMOVIE VIDEOS/`, `WOLF WHISPERER/`, `demos/` (user source material)
- `tools/ffmpeg/`, `tools/wolfcamql/`, `tools/uberdemotools/` (third-party binaries)
- `creative_suite/`, `phase1/` source, `phase3/`, `phase35/`, `phase5/`, `scripts/`, `tests/` (live code trees)
- `pyproject.toml`, `CLAUDE.md`, `README.md`, `SPLIT1_USER_CHECKLIST.md`, `HUMAN-QUESTIONS.md` (canonical root docs — never propose deletion)
- `database/`, `storage/` (live state)
- `.git/`, `.github/` (git internals)

---

## 1 · Baseline inventory

| Area | Size | Notes |
|---|---:|---|
| `output/` | **56 GB** | Biggest cleanup target (render caches + stems + normalized) |
| `output/normalized/` | 37 GB | **LIVE CACHE** — 604 CFR-normalized demo mp4s, referenced by `phase1/config.py:297`. Keep. |
| `output/_part04_v6_body_chunks/` | 4.2 GB | Superseded by v10 |
| `output/_part04_v9_body_chunks/` | 4.0 GB | Superseded by v10 |
| `output/_part05_v6_body_chunks/` | 4.5 GB | Superseded by v10 |
| `output/_part06_v6_body_chunks/` | 4.1 GB | Superseded by v10 |
| `output/_part07_v6_body_chunks/` | 84 MB | Partial / early (v10 ships with different chunking) |
| `output/_part04_stems/` | 672 MB | v1 stems — superseded by `_part04_stems_v2` and v10 sync_audit path |
| `output/_part04_stems_v2/` | 640 MB | v2 stems — older run, not referenced by current `audio_levels.py` path |
| `output/_part05_stems/` | 705 MB | Older stems, superseded by v10 |
| `output/Part4_v10_4_manual_review.mp4` | 682 MB | **Keep (deliverable reference)** — referenced by `creative_suite/tests/test_api_phase1.py:122` |
| `output/_pantheon_trim_5s.mp4` | 692 KB | One-off trim. Not referenced anywhere. |
| `docs/` | 41 MB | Mostly `visual-record/` = 37 MB |
| `docs/research/` | 3.4 MB | 16 research docs, mixed age |
| `docs/reviews/` | 12 KB | Only 1 review file (`part4-review-2026-04-17.md`) |
| `graphify-out/` | 3.1 MB | Current (2026-04-19). Keep. |
| `.swarm/` | 1.7 MB | Live RuFlo memory. Keep (gitignored). |
| `.playwright-mcp/` | 761 KB | Browser-automation cache. Keep (gitignored). |
| `.pytest_cache/` | 25 KB | Ephemeral. Keep (gitignored). |
| `_cs_gate_out/` | 63 KB | Cinema Suite gate test output (has own `.git`!) |
| `quake_legacy.egg-info/` | 5 KB | Setuptools artifact, gitignored — benign |
| `.nickname_map.json` | 813 B | Local-only alias dictionary (FT-5). Keep (gitignored). |

**Docs-file count:** 148 total files, 43 `.md`.
**Git log summary:** Last 200 commits confirm creative-suite-v2 merged (PR #2, `68037f03`), Cinema Suite Phase D shipped, pantheon design branch merged into main (`78709e98`), Part 4 reached `v10_4`, Parts 5/6/7 reached `v10_3`.

---

## 2 · Category-by-category findings

### 2.1 · `docs/superpowers/plans/` — DOES NOT EXIST

**Finding:** `docs/INDEX.md` references `docs/superpowers/plans/*` on 6+ lines (e.g. lines 23, 25, 29, 30, 32, 33). Directory does **not exist** on disk. Every link in INDEX pointing there is dead.

- **Action class:** update INDEX.md (rewrite) — no files to move; the target dir simply isn't there.
- **Blast radius:** cosmetic (broken links in the index only).

### 2.2 · `docs/superpowers/specs/` — mostly shipped

| Path | Status | Action | Evidence |
|---|---|---|---|
| `2026-04-17-command-center-design.md` | Superseded by `creative-suite-v2-design.md` per CLAUDE.md (Phase 1.5 section). Live code under `creative_suite/`. | **archive** | CLAUDE.md merges this into the v2 manifesto |
| `2026-04-17-creative-suite-design-v1-superseded.md` | Filename admits it's superseded. | **archive** | Filename |
| `2026-04-17-creative-suite-v2-design.md` | **Shipped** via PR #2 (`68037f03`). 25-task plan delivered per CLAUDE.md Phase Status. | **archive** (keep for history) | Git log + CLAUDE.md |
| `2026-04-17-engine-pivot-design.md` | Referenced by `docs/research/engine-ingestion-state-2026-04-19.md` (live). Engine agent still consuming. | **keep** | Live references |
| `2026-04-17-tr4sh-quake-manifesto.md` | Split 2 roadmap — still forward-looking per CLAUDE.md. | **keep** | CLAUDE.md Phase Status |
| `2026-04-18-comfyui-video-pipeline-design.md` | Phase-5 design; phase5 scaffolded. Referenced only by graphify manifest. | **flag-for-review** | No live downstream |

- **Blast radius:** Archive candidates are NOT referenced by any non-archive doc or by code outside `.claude/worktrees/`. Safe to move.

### 2.3 · `docs/reviews/` — only one file, keep

| Path | Status | Action |
|---|---|---|
| `part4-review-2026-04-17.md` | Canonical Part 4 review — rules it produced are baked into CLAUDE.md (Rules P1-G/H/K/L/N/O/P/Q). | **keep** |

No superseded review files to archive.

### 2.4 · `docs/research/` — mostly live

| Path | Status | Action | Evidence |
|---|---|---|---|
| `claude-tooling-phase1-upgrade-2026-04-18.md` | 2026-04-18, unknown consumer | **flag-for-review** | No refs |
| `demo-dedup-report-2026-04-17.md` | Referenced by `HUMAN-QUESTIONS.md` | **keep** | Live |
| `demo-inventory-2026-04-17.json` | Data file, historical inventory pre-7z-extract | **flag-for-review** | No code refs; CLAUDE.md now cites 6,465 demos (newer reality) |
| `encoder-recommendation-2026-04-17.md` | Feeds FT-6; Rule P1-J still open | **keep** | CLAUDE.md FT-6 |
| `engine-ingestion-state-2026-04-19.md` | Today's state report | **keep** | Newest |
| `frag-scoring-features.md` | Cited by HUMAN-QUESTIONS §2 | **keep** | Live |
| `ghidra-rip-state-2026-04-19.md` | Today | **keep** | Newest |
| `live-simulation-capacity-2026-04-19.md` | Today | **keep** | Newest |
| `master-files-recompilation-2026-04-19.md` | Today | **keep** | Newest |
| `perf-tuning-2026-04-18.md` | Referenced by `CLAUDE.md` | **keep** | Live |
| `phase3-ai-approaches.md` | Referenced by `docs/INDEX.md` | **keep** | Live |
| `proto73-port-review-2026-04-17.md` | Referenced by CLAUDE.md + INDEX | **keep** | Live (Track A) |
| `steam-pak-inventory-2026-04-17.md` | Referenced by CLAUDE.md (ENG-1) | **keep** | Live |
| `steam-pak-manifest-2026-04-17.json` | Data for inventory | **keep** | Paired w/ above |
| `steam-pak-summary-2026-04-17.json` | Data for inventory | **keep** | Paired w/ above |

- Plan output doc itself (`repo-cleanup-plan-2026-04-19.md`) lives here — keep.

### 2.5 · `docs/specs/` (OLD, pre-`superpowers/` location)

| Path | Status | Action |
|---|---|---|
| `2026-04-16-quake-legacy-design.md` | Referenced by `CLAUDE.md` "When Starting a Session" step 1. **Canonical.** | **keep** |
| `highlight-criteria-v1.md` | **Superseded** by FT-2 (v2 lives inline in CLAUDE.md). Still referenced by `HUMAN-QUESTIONS.md:33` as the reading material for Gate P3-0. | **flag-for-review** — archiving breaks the HUMAN-QUESTIONS link; needs simultaneous doc edit |

### 2.6 · `docs/design/`

| Path | Status | Action |
|---|---|---|
| `pantheon-system.md` | Design doc for the pantheon brand — **shipped** into README (commit `070b5f0b`, 2026-04-19). | **archive** (historical) |
| `render-review-flow.md` | Not referenced anywhere (grep: only graphify manifest). Likely superseded by Cinema Suite Review Console. | **flag-for-review** |
| `readme-mockup/` | **Empty directory** (0 files) | **delete** |

### 2.7 · `docs/handoff/`, `docs/runbooks/`, `docs/sessions/`

| Path | Status | Action |
|---|---|---|
| `docs/handoff/claude-designer-liaison-2026-04-19.md` | No external refs. May be live for ongoing design thread. | **flag-for-review** |
| `docs/runbooks/gate-cs2-wolfcam-pk3-smoke.md` | CS-2 gate runbook. No external refs. Cinema Suite shipped per CLAUDE.md — gate likely closed. | **flag-for-review** |
| `docs/runbooks/task9-reference-asset-capture-smoke.md` | Task 9 shipped (`33d02b93`). | **archive** |
| `docs/sessions/2026-04-17-wrapup-TOMORROW.md` | Wrap-up doc. Every TL;DR item in it is DONE per git log (PR #1 merged, creative-suite-v2 merged, Part 4 v6 reached v10). | **archive** |

### 2.8 · `docs/INDEX.md` — STALE

**Last updated line says 2026-04-18 session 3.** Contents:
- References `docs/superpowers/plans/` — directory doesn't exist.
- References `docs/reference/phase5-bugs-fixed.md` — file is in `docs/reference/` (OK) but Phase 5 status context is pre-v2-merge.
- Status preamble talks about "dual Part 4 v6 + Part 5 v6 render running" — Part 4 has since reached v10_4.
- Lists `Creative Suite v2 Step 2 still shipped · Engine PR #1 still open` — PR #1 merged (`5ca8943f`).

- **Action class:** **rewrite** (not archive). INDEX is load-bearing navigation. Must reflect current state.

### 2.9 · `docs/visual-record/YYYY-MM-DD/`

Per Rule VIS-1 these are evidential and must not be lost. Current layout:

- `2026-04-17/` (3 items + one orphan mp4 `rocket_turntable.mp4`)
- `2026-04-18/` (~27 items — most referenced by the summary HTMLs)
- `2026-04-19/` (7 items)
- `github-readme/` (7 textures under `textures/`, 0 files at root) — the empty root dir should be left alone since `textures/` lives under it

- **Action class:** **keep** all; **add index.md** at `docs/visual-record/README.md` listing each date's contents (currently none).

### 2.10 · `output/` — the biggest win

#### 2.10.1 · Superseded body-chunk caches (~16.8 GB)

| Path | Size | Evidence superseded |
|---|---:|---|
| `_part04_v6_body_chunks/` | 4.2 GB | Part 4 reached v10_4 (`part04_v10_4_manual_review_log.txt` exists). v6 chunks are two major version gens old. No code references the v6 path. |
| `_part04_v9_body_chunks/` | 4.0 GB | Same — v10 is current. Review log `part04_v10_1_review_log.txt` through `part04_v10_4_manual_review_log.txt` confirms the v10 family. |
| `_part05_v6_body_chunks/` | 4.5 GB | `part05_v10_3_review_log.txt` confirms v10.3. |
| `_part06_v6_body_chunks/` | 4.1 GB | `part06_v10_3_review_log.txt` confirms v10.3. |
| `_part07_v6_body_chunks/` | 84 MB | `part07_v10_3_review_log.txt` confirms v10.3. Tiny — same disposition. |

- **Action class:** **delete** (regenerable from clip lists + source AVIs; Rule CS-1 governs re-render).
- **Blast radius:** **zero code references** (grep over non-`.claude` tree returned no hits).

#### 2.10.2 · Stems — superseded

| Path | Size | Evidence |
|---|---:|---|
| `_part04_stems/` | 672 MB | v1 stems. `audio_levels.py` uses the in-render path, no hard-coded stem dir reference. |
| `_part04_stems_v2/` | 640 MB | v2 stems. Superseded by v10 per-chunk PCM-WAV intermediates (P1-BB). |
| `_part05_stems/` | 705 MB | Same as Part 04 — v10 path no longer needs these. |

- **Action class:** **delete**. Regenerable.
- **Blast radius:** no code references.

#### 2.10.3 · One-off / ad-hoc

| Path | Size | Evidence | Action |
|---|---:|---|---|
| `_pantheon_trim_5s.mp4` | 692 KB | No refs. One-off derived from `FRAGMOVIE VIDEOS/IntroPart2.mp4` (canonical per CLAUDE.md Rule P1-X). | **delete** |
| `Part4_v10_4_manual_review.mp4` | 682 MB | **LIVING** — referenced by `creative_suite/tests/test_api_phase1.py:122`. | **keep** |

#### 2.10.4 · Logs (root of output/)

| Path | Status |
|---|---|
| `part3_rev2_render.log`, `rev1_part3_abc.log`, `part6_v8_draft.log`, `part6_v8_render.log`, `parts_4567_driver.log`, `parts_4567_status.txt`, `part04_smoke_log.txt`, `part04_review_log.txt`, `part04_v10_1_review_log.txt`, `part04_v10_2_review_log.txt`, `part04_v10_3_review_log.txt`, `part04_v10_4_manual_review_log.txt`, `part05_v10_3_review_log.txt`, `part06_v10_3_review_log.txt`, `part07_v10_3_review_log.txt` | All render/review logs. Not referenced by code. Historical only. |

- **Action class:** **archive to `output/_archive/logs/`** (preserve filenames). Cheap to keep, useful for incident forensics.

#### 2.10.5 · JSON artifacts (flow_plan / music_plan / music_structure / beats / levels / sync_audit / event_diversity / recognition_report)

These are **current** — referenced by `creative_suite/api/phase1.py` + tests (`test_api_phase1.py`, `test_git_flow.py`, `test_rebuild_job.py`). **Keep all.**

#### 2.10.6 · `clip_audit_*` artifacts from session 5 (2026-04-18)

| Path | Status |
|---|---|
| `clip_audit_part04.json`, `_proposed.txt`, same for 05/06/07, `clip_audit_summary.txt` | Output of `scripts/rescan_clips.py` + `scripts/validate_clip_lists.py`. Proposals already merged into `phase1/clip_lists/*` per commit `07019fec`. |

- **Action class:** **archive** (move to `output/_archive/clip_audit_session5/`). Not referenced by running code.

#### 2.10.7 · `output/logs/` (subdir)

Contains 20+ old render logs from v3..v8. Same disposition as §2.10.4 — **archive**.

#### 2.10.8 · `output/beat_maps/` (28 KB)

Contains `part03_{stylea,styleb,stylec}_beatplan.json` + `part04/05/06_styleb_beatplan.json`. No code references found. Superseded by new `part04_beats.json` / `part04_music_structure.json` schema.

- **Action class:** **archive**.

#### 2.10.9 · `output/previews/`

Empty directory. **Action class:** **delete** (or leave as-is — it's harmless; flag-for-review).

#### 2.10.10 · `output/normalized/` — LIVE CACHE

604 files, 37 GB. **LIVE** — referenced by `phase1/config.py:297` (`norm_dir = self.output_dir / "normalized"`). Every render consumes this.

- **Action class:** **keep** entirely. Never propose shrinking.

#### 2.10.11 · Final Part renders (the ship-quality mp4s)

`find` returned only `Part4_v10_4_manual_review.mp4` at `output/` root (the other Part mp4s live elsewhere / aren't on disk yet in this repo). **Keep.** Deliverable policy per the task brief.

### 2.11 · `phase1/clip_lists/` and `phase1/output/`

- `phase1/clip_lists/` — all 20 txt files are current; no `.bak`, no suffixed `_rescan.bak`. Clean.
- `phase1/output/` — **does not exist** (clean).

No action.

### 2.12 · Repo-root stragglers

| Path | Action | Evidence |
|---|---|---|
| `_cs_gate_out/` (has its own `.git`) | **flag-for-review** | 63 KB, gate test output. Own git subrepo. Unknown if still active — Cinema Suite shipped but test harness may reuse. Ask user. |
| `quake_legacy.egg-info/` | **delete** | Regenerable from `pyproject.toml`. Gitignored per `.gitignore:35`. |
| `__pycache__/` anywhere | **delete** (implicitly, per .gitignore) | Standard |
| `.nickname_map.json` | **keep** | Local alias dictionary (FT-5), gitignored |
| `.playwright-mcp/` | **keep** | MCP cache |
| `.pytest_cache/` | **keep** | pytest cache |
| `.swarm/` | **keep** | RuFlo live memory |

### 2.13 · `graphify-out/`

Current (2026-04-19, post-merge per `feedback_design_to_main_merge.md`). **Keep.**

### 2.14 · Stray `.graphify_*.json` outside `graphify-out/`

The task brief noted "engine/ had several" — but `engine/` is hard-constrained (do not touch). Also `.gitignore:65` already covers `engine/.graphify_*.json`. **Skip.**

---

## 3 · Archive strategy

**Chosen layout:** per-doc-root `_archive/YYYY-MM/` + `output/_archive/` for output-side.

Reasoning:
- Keeps each docs subtree self-contained. Grep from `docs/` still finds old content.
- Dated subfolders give future cleanups an obvious next cohort.
- Mirrors git branch conventions where historical work lives alongside current.

Proposed targets:

```
docs/_archive/2026-04/
  specs/
    2026-04-17-command-center-design.md
    2026-04-17-creative-suite-design-v1-superseded.md
    2026-04-17-creative-suite-v2-design.md
  design/
    pantheon-system.md
  runbooks/
    task9-reference-asset-capture-smoke.md
  sessions/
    2026-04-17-wrapup-TOMORROW.md

output/_archive/
  logs/                   # root-level .log / .txt review-logs from §2.10.4
  subdir_logs/            # former output/logs/*
  beat_maps/              # former output/beat_maps/*
  clip_audit_session5/    # former output/clip_audit_*
```

Rationale for **not** proposing a single top-level `_archive/`: it would create a second source of truth the file browser must learn. Keeping it sibling to its origin folder is zero-cognitive-overhead.

---

## 4 · Ordered execution plan

Each step has a verification gate. Nothing advances without green pytest.

### Step 0 — Preflight (mandatory before any file ops)

- `pytest creative_suite/tests phase1/tests -q` — must be green (expected 133+).
- `git status` — working tree should be clean of unrelated edits (there are many unrelated `M` entries from the engine-fork agent; confirm with user this cleanup runs on a fresh worktree or a dedicated branch).
- Confirm disk free space — archiving is a move (cheap), deletion reclaims. Deletions total ~17 GB; stems add another ~2 GB.

### Step 1 — Delete empty directories (safe, zero-risk)

Paths:
- `docs/design/readme-mockup/`
- `output/previews/` (flag-for-review alternative: leave empty)

Verification: `ls` confirms gone. No rollback needed.

### Step 2 — Delete regenerable caches (~19 GB reclaimed)

Paths (delete, not archive):
- `output/_part04_v6_body_chunks/`
- `output/_part04_v9_body_chunks/`
- `output/_part05_v6_body_chunks/`
- `output/_part06_v6_body_chunks/`
- `output/_part07_v6_body_chunks/`
- `output/_part04_stems/`
- `output/_part04_stems_v2/`
- `output/_part05_stems/`
- `output/_pantheon_trim_5s.mp4`
- `quake_legacy.egg-info/`
- All `__pycache__/` under `phase1/`, `creative_suite/`, `scripts/`, `tests/` (gitignored, free to nuke)

Verification:
- `pytest creative_suite/tests phase1/tests -q` re-run — must still be green.
- `python -c "from phase1 import config; print(config.Config().output_dir)"` — still imports.
- `git status` — no tracked files removed (everything above is gitignored or untracked).

Rollback: caches regenerate from `python -m phase1.build_part5_chunks` / render pipeline. No git history loss.

### Step 3 — Archive output-side logs + audit files

Create `output/_archive/` structure per §3 and move:
- All root `.log` / `_review_log.txt` / `_smoke_log.txt` files into `output/_archive/logs/`
- `output/logs/*` into `output/_archive/subdir_logs/`
- `output/beat_maps/*` into `output/_archive/beat_maps/`
- `output/clip_audit_*` into `output/_archive/clip_audit_session5/`

Verification: `pytest` green; `grep -r "clip_audit_" phase1/ creative_suite/ scripts/` returns nothing (already confirmed).

Rollback: `mv` back from `_archive/`.

### Step 4 — Archive shipped specs / design / sessions / runbooks

Move to `docs/_archive/2026-04/`:
- `docs/superpowers/specs/2026-04-17-command-center-design.md`
- `docs/superpowers/specs/2026-04-17-creative-suite-design-v1-superseded.md`
- `docs/superpowers/specs/2026-04-17-creative-suite-v2-design.md`
- `docs/design/pantheon-system.md`
- `docs/runbooks/task9-reference-asset-capture-smoke.md`
- `docs/sessions/2026-04-17-wrapup-TOMORROW.md`

Verification:
- `grep -rn "command-center-design\|creative-suite-design-v1\|creative-suite-v2-design\|pantheon-system.md\|task9-reference\|2026-04-17-wrapup-TOMORROW" docs/ phase1/ creative_suite/ scripts/ tests/ CLAUDE.md README.md HUMAN-QUESTIONS.md SPLIT1_USER_CHECKLIST.md` — every surviving reference (mostly from INDEX.md, CLAUDE.md, HUMAN-QUESTIONS.md) must be either (a) updated to point at `_archive/` or (b) removed. See §6 matrix.
- `pytest` green.
- `graphify-out/manifest.json` is regenerated on next graphify run — no fix needed there.

Rollback: move back.

### Step 5 — Rewrite `docs/INDEX.md`

- Remove every link to `docs/superpowers/plans/*` (dir doesn't exist).
- Update Phase Status preamble to match `CLAUDE.md` Phase Status table.
- Re-point links to archived files at their new `_archive/` locations.
- Mark Cinema Suite as shipped.
- Link `docs/research/repo-cleanup-plan-2026-04-19.md` (this doc).

Verification: every Markdown link in INDEX resolves (a simple script: for each `](path)` in INDEX, `test -f path`). Zero broken links.

### Step 6 — Write `docs/visual-record/README.md`

Per §2.9. Small one-off. Lists each dated subfolder and its contents.

### Step 7 — Handle flag-for-review set

These MUST get user input before action:

| Path | Question for user |
|---|---|
| `docs/superpowers/specs/2026-04-18-comfyui-video-pipeline-design.md` | Phase 5 still live? Keep or archive? |
| `docs/design/render-review-flow.md` | Superseded by Cinema Suite Review Console — archive? |
| `docs/handoff/claude-designer-liaison-2026-04-19.md` | Active handoff thread? |
| `docs/runbooks/gate-cs2-wolfcam-pk3-smoke.md` | Gate CS-2 closed? |
| `docs/specs/highlight-criteria-v1.md` | Replace HUMAN-QUESTIONS.md:33 reference with "(superseded by FT-2 in CLAUDE.md)" so we can archive? |
| `docs/research/claude-tooling-phase1-upgrade-2026-04-18.md` | Actionable or reference? |
| `docs/research/demo-inventory-2026-04-17.json` | Archive (CLAUDE.md now cites 6,465 demos)? |
| `_cs_gate_out/` | Is this a one-time gate artifact or live test fixture? |
| `output/previews/` | Delete empty dir or leave for future preview output? |

---

## 5 · Disk-space reclamation

| Action | Reclaimed | Cumulative |
|---|---:|---:|
| Delete `_part04_v6_body_chunks/` | 4.2 GB | 4.2 GB |
| Delete `_part04_v9_body_chunks/` | 4.0 GB | 8.2 GB |
| Delete `_part05_v6_body_chunks/` | 4.5 GB | 12.7 GB |
| Delete `_part06_v6_body_chunks/` | 4.1 GB | 16.8 GB |
| Delete `_part07_v6_body_chunks/` | 84 MB | 16.9 GB |
| Delete `_part04_stems/` | 672 MB | 17.6 GB |
| Delete `_part04_stems_v2/` | 640 MB | 18.2 GB |
| Delete `_part05_stems/` | 705 MB | 18.9 GB |
| Delete `_pantheon_trim_5s.mp4` | 692 KB | 18.9 GB |
| `__pycache__` + `egg-info` | ~few MB | 18.9 GB |
| **Total Step 2 reclamation** | | **~19 GB** |

**Everything else is archive-only** (no size win; just organization).

Before: `output/` = 56 GB. After Step 2: ~37 GB (essentially just `normalized/` left, which is the live cache).

---

## 6 · Reference-breakage matrix

For every path proposed to move/delete, the post-action reference state:

| Source of reference | Line | Target being moved | Fix required |
|---|---|---|---|
| `docs/INDEX.md` | multiple | `docs/superpowers/plans/*` (never existed) | INDEX.md rewrite (Step 5) — remove links |
| `docs/INDEX.md` | multiple | various to-be-archived specs/sessions | INDEX.md rewrite (Step 5) — repoint to `_archive/` |
| `CLAUDE.md` | §Phase Status + rule refs | keeps `creative-suite-v2-design` and others as historical pointers | Add "(archived)" annotation next to refs OR leave alone — `_archive/` paths are still grep-findable |
| `HUMAN-QUESTIONS.md` | line 33 | `docs/specs/highlight-criteria-v1.md` | **BLOCKER** — need user decision (§4 Step 7) before archiving |
| `docs/research/engine-ingestion-state-2026-04-19.md` | cites `2026-04-17-engine-pivot-design.md` | Not being moved | No fix |
| `docs/research/live-simulation-capacity-2026-04-19.md` | cites `dm73-format-deep-dive.md` in reference/ | Not being moved | No fix |
| `creative_suite/tests/test_api_phase1.py:122` | `output/Part4_v10.4_manual.mp4` | Keep (not moved) | No fix |
| `phase1/config.py:297` | `output/normalized/` | Keep | No fix |
| `graphify-out/manifest.json` | Every archived doc | Not a reference source of truth — rebuilt on `graphify --rebuild` | No fix; next graphify rerun updates |
| `scripts/render_parts_4567.sh` | Not inspected deeply — may reference `parts_4567_driver.log` | Archive log only | Script is historical; archive log doesn't break its future execution (log gets rewritten) |

**Zero broken references after Step 5** is the acceptance bar. Simple verification script (recommended):

```bash
python - <<'PY'
import re, pathlib
idx = pathlib.Path("docs/INDEX.md").read_text(encoding="utf-8")
broken = []
for m in re.finditer(r"\]\(([^)]+\.md)\)", idx):
    p = pathlib.Path("docs") / m.group(1).replace("..", "").lstrip("/")
    if not p.exists() and not (pathlib.Path(m.group(1)).exists()):
        broken.append(m.group(1))
print("BROKEN:", broken)
PY
```

---

## 7 · What we examined and deliberately left alone — SAFETY RECEIPT

| Path | Why left alone |
|---|---|
| `tools/quake-source/**` | Hard-constraint (engine-unification agent) |
| `engine/**` | Hard-constraint (engine-unification agent) |
| `docs/reference/**` | Hard-constraint (Q3A-ingestion agent) |
| `phase2/dm73parser/**` | Hard-constraint (engine-unification agent) |
| `.claude/worktrees/engine-fork/**` | Hard-constraint (active ENG-1 fork) |
| `.claude/worktrees/*` (other worktrees) | Not in hard-constraint list but also not in scope — worktree hygiene is a separate concern |
| `QUAKE VIDEO/`, `FRAGMOVIE VIDEOS/`, `WOLF WHISPERER/`, `demos/` | User source material |
| `tools/ffmpeg/`, `tools/wolfcamql/`, `tools/uberdemotools/` | Third-party binaries |
| `creative_suite/` (entire tree) | Live code |
| `phase1/*.py`, `phase1/assets/`, `phase1/clip_lists/`, `phase1/music/`, `phase1/sound_templates/`, `phase1/presets/`, `phase1/tools/`, `phase1/effects/`, `phase1/tests/` | Live code (only caches & output-side flagged) |
| `phase1/clip_lists/*` | All files on disk match current git HEAD — no stale `.bak` or backup suffixes found |
| `phase3/`, `phase35/`, `phase5/` | Live code |
| `scripts/*.py`, `scripts/*.sh` | Live tooling |
| `tests/` | Live |
| `database/` | Live state |
| `storage/` | Live state |
| `.git/`, `.github/` | Git internals |
| `.gitignore` | Canonical |
| `pyproject.toml`, `CLAUDE.md`, `README.md`, `SPLIT1_USER_CHECKLIST.md`, `HUMAN-QUESTIONS.md` | Canonical root docs |
| `docs/reviews/part4-review-2026-04-17.md` | Canonical — rules baked into CLAUDE.md |
| `docs/research/*` (13 of 16 files) | Live or today's work |
| `docs/specs/2026-04-16-quake-legacy-design.md` | Canonical session starter |
| `docs/superpowers/specs/2026-04-17-engine-pivot-design.md` | Live consumer (engine agent) |
| `docs/superpowers/specs/2026-04-17-tr4sh-quake-manifesto.md` | Live Split 2 roadmap |
| `docs/visual-record/**` | All visual evidence — Rule VIS-1 |
| `graphify-out/` | Current (2026-04-19) |
| `output/normalized/` | Live cache (~37 GB) — `phase1/config.py:297` |
| `output/Part4_v10_4_manual_review.mp4` | Cited by `creative_suite/tests/test_api_phase1.py:122` |
| `output/*.json` (flow_plan, music_plan, music_structure, beats, levels, sync_audit, event_diversity) | Live Cinema Suite artifacts |
| `output/part04_recognition_report.md` | Current recognition diagnostic |
| `.nickname_map.json`, `.playwright-mcp/`, `.pytest_cache/`, `.swarm/` | Live / gitignored caches |

---

## 8 · TL;DR (10 bullets)

1. **~19 GB reclaimable** from superseded render caches (`output/_partNN_v[6|9]_body_chunks/` + stems) — zero code references, safe delete.
2. **`output/normalized/` is a LIVE cache** (604 files, 37 GB). Never touch — `phase1/config.py:297` reads it.
3. **`output/Part4_v10_4_manual_review.mp4` must be kept** — referenced by `creative_suite/tests/test_api_phase1.py:122`.
4. **`docs/INDEX.md` is stale** — links to a `docs/superpowers/plans/` directory that doesn't exist. Rewrite required.
5. **Shipped specs move to `docs/_archive/2026-04/`**: command-center-design, creative-suite-design-v1-superseded, creative-suite-v2-design, pantheon-system, task9 runbook, 2026-04-17 wrapup session. All have matching ship commits in git log.
6. **Three specs stay live**: `engine-pivot-design.md`, `tr4sh-quake-manifesto.md`, `2026-04-16-quake-legacy-design.md`. All have downstream consumers.
7. **Output logs and `clip_audit_*` artifacts get archived to `output/_archive/`**, not deleted — cheap insurance for forensics.
8. **`HUMAN-QUESTIONS.md:33` blocks archiving `docs/specs/highlight-criteria-v1.md`** — needs simultaneous doc edit ("superseded by FT-2") for green-light.
9. **9 items flagged-for-review** (user call required): ComfyUI spec, render-review-flow, claude-designer-liaison, gate-cs2 runbook, highlight-criteria-v1, claude-tooling-upgrade research, demo-inventory JSON, `_cs_gate_out/`, empty `output/previews/`.
10. **Hard-constraint paths (5) + user-material paths (4) untouched.** Safety receipt in §7 — every examined path that was NOT proposed for change is listed with reason.

---

## Summary paragraph

This plan identifies **~19 GB of safely-reclaimable disk** in superseded body-chunk and stem caches under `output/`, a **stale `docs/INDEX.md`** pointing at a nonexistent `superpowers/plans/` directory, and roughly **six shipped specs/design/session docs** ready to archive (not delete) into `docs/_archive/2026-04/` per the reference-breakage matrix in §6. The archive-first, delete-second strategy means zero information loss — everything shipped stays grep-able, everything regenerable (caches, stems, intermediate logs) is recreated on next render. Nine items are **flagged-for-review** (user call) rather than decided unilaterally. The five hard-constraint paths owned by other in-flight agents are fully respected, verified against the safety receipt in §7, and no path under `creative_suite/`, `phase1/` source, `phase3/`, `phase35/`, `phase5/`, or `scripts/` is touched.
