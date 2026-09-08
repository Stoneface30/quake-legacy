# Local state report — 2026-09-07

What is on this disk, what was removed today, and which branch knows what.
Every number below was measured, not estimated.

---

## 1. Cleanup performed

All of this was removed. Nothing removed was tracked by git, referenced by
code, or the only copy of anything.

| Removed | Size | Why it was dead |
|---|---|---|
| `creative_suite/comfy/photoreal/*.log` (13 files) | 8.9 MB | ComfyUI batch logs from 2026-04-21/22. The batch's real record is `assets.db` (5,776 assets / 14,413 renders). `comfyui_err.log` alone was 8.6 MB. |
| `.tmp/` — 30 entries older than today | 145 MB | Scratch from 2026-09-01..06: comparison mp4/png pairs, suite logs, pytest dirs, review collections. Today's scratch was kept — a session is still using it. |
| `.playwright-cli/`, `.playwright-mcp/` | 154 KB | Console and page dumps from browser automation runs on 08-31 and 09-04. |
| `creative_suite/creative_suite/` | empty | A `ROOT` vs `REPO_ROOT` artefact — the same class of bug recorded in `feedback_root_vs_repo_root.md`. |
| `creative_suite/output/part0{4,5,6}_music_plan.json` | 12 KB | Same bug: written to `config.ROOT` instead of `REPO_ROOT`. The real, larger, same-day plans live at `output/`. |
| `_tc_test.py`, `creative_suite/database/_writetest.tmp` | 235 B | A throwaway title-card smoke script and a zero-byte disk probe. |
| 4 empty stub directories | — | `docs/design/readme-mockup`, `docs/visual-record/2026-04-21/_tmp_shot`, `.../pipelines/pixel_art/phase5_png`, `creative_suite/engine/parser/tests`. |

Moved, not deleted: `ann.html` (330 KB scrape of the ESR *AnnihilatioN*
review) went to `docs/reference/_research/annihilation-esr-review.html`. It is
the reference for the FT-3 morph-remaster idea, so it belongs in docs rather
than at the repository root.

`.playwright-cli/` was added to `.gitignore`; `.playwright-mcp/` already was.

**Reclaimed: about 154 MB.**

### Not removed — these are yours to call

| Candidate | Size | Why I stopped |
|---|---|---|
| `creative_suite/database/performance_index.db` | **94.1 GB** | Marked `OBSOLETE_REPLACED` on 2026-09-06, read by no code, superseded by `F:\QUAKE_LEGACY_STORE\performance_index_v2.db`. Its own marker file says deletion is an operator decision, and there is a standing instruction not to destroy it automatically. This is the largest reclaimable object on G:. |
| `output/_part0{4,5,6}_v6_body_chunks` | 17.5 GB | Per-chunk intermediates from the Parts 4/5/6 renders that already shipped. Regenerable, but regenerating costs a full render pass. |
| `output/_part0{4,5,6}_stems` | 5.0 GB | Audio stems from the same renders. Same trade. |
| `docs/visual-record` duplicates | 2.8 MB | 13 byte-identical groups. VIS-1 calls visual records deliverables, so I left them. |

---

## 2. Local file status

**Disk:** G: 1,000 GB total, **194 GB free (81% used)**. F: 1,000 GB total, 506 GB free.

| Area | Size | State |
|---|---|---|
| `QUAKE VIDEO/` | 510 GB | 1,658 source AVIs, T1/T2/T3. Untouched source. |
| `output/` | 112 GB on disk | 59 GB `reference`, 30 GB `demo_v2`, 26 GB loose renders, 22.5 GB Part 4/5/6 intermediates. Summing file sizes gives 147 GB; the 35 GB gap is the asset packs, which `assets.py` installs with `os.link`, so the staging copies are hard links and occupy no extra disk. |
| `creative_suite/database/` | 106.5 GB | **94.1 GB of it is the obsolete v1 index.** Live databases total about 12 GB, dominated by `frag_recognition.db` at 10.8 GB. |
| `creative_suite/comfy/` | 17.2 GB | pak00 source PNGs plus 14,413 generated renders. |
| `demos/` | 14.1 GB | 6,445 `.dm_73`. |
| `engine/` | 6.4 GB | Deduped engine source trees plus Ghidra output. |
| `docs/` | 0.32 GB | 291 MB of it is `visual-record` — VIS-1 deliverables. |

**Code:** 546 tracked Python files · 190 test modules · 84 tracked docs ·
67 modules under `engine/pantheon/` on the headless branch.

### The finding that matters most

`assets.db` does **not** hold an HD texture pack. It holds **eleven distinct
render families**, and the shipped UHD pk3s use exactly one of them:

| Family | Renders | In the UHD packs? |
|---|---|---|
| `upscale_only` | 5,776 | **yes — this is all that ships** |
| `depth_realism` | 1,000 | no |
| `photoreal` | 1,000 | no |
| `pixel_art` | 956 | no |
| `chromatic`, `dreamlike`, `edge_chrome`, `isometric`, `neon`, `painterly`, `zavy_depth` | 800 each | no |
| `tile_d35..d80`, `cel_shade`, `cartoon`, `concept_art`, `ink_etching` | 7–11 each (E2E samples) | no |

**8,637 stylised renders of the game's own art are finished, on disk, and
have never been in a picture.** That is the material for texture-swapped
multi-render morphs, and it is why "an HD pack is what everyone has" does not
describe what we hold. The pipeline simply never packed anything but the
upscale.

The 861 HUD-family assets (`ui` 454, `gfx` 157, `powerups` 87, `icons` 63,
`weaphits` 43, `sprites` 34, `wolfcam_hud` 23) are all routed `fx` and all
deliberately excluded from the UHD packs, on the stated grounds that
alpha-edge fidelity outranks resolution on explosions and beams. That
exclusion is right for *replacing* HUD art and wrong for *animating* it.
`zzz_zz_moviehud.pk3` holds exactly one file, `scripts/gfx.shader`, and that
is the override point any HUD transition work goes through.

---

## 3. Branch and session currency

`feature/pantheon-headless` is the engine's source of truth. Everything below
is measured against it.

| Branch / worktree | Tip | Behind | Ahead | Tree | Has the shared engine? |
|---|---|---|---|---|---|
| `feature/pantheon-headless` | `e3d47016` | — | — | clean | **source of truth** — all 67 modules |
| `feature/pantheon-world` | `25d571d4` | 6 | 26 | clean | yes, except `assets.py` and `capture_lock.py` |
| `review-headless-integration` | `36473b93` | 15 | 8 | 3 uncommitted | yes, except `assets.py` and `capture_lock.py` |
| `feature/pantheon-prologue` | `453bcfc8` | 33 | 12 | 2 uncommitted | **no pantheon modules at all** |
| `demo-v2-mining` *(the root checkout)* | `c563fda9` | 77 | 6 | 122 uncommitted | **no pantheon modules at all** |
| `fix/public-export-name-burnin` | `b212445c` | 93 | 0 | clean | no — fully contained, mergeable or closeable |
| `feature/engine-fork-and-ghidra` | `476ea039` | 443 | 1 | 4 uncommitted | no — dormant since 2026-04-19 |
| `feature/creative-suite-v2` | `6e0795fa` | 441 | 0 | 4 uncommitted | no — dormant since 2026-04-19, zero unique work |
| `main` | `5a1f08dd` | 296 | 0 | — | **no — main is at 2026-04-24** |

### What is actually out of date

1. **`main` is five months stale.** Every branch above forked from it and none
   has gone back. Nothing on main knows the PANTHEON engine exists.
2. **`demo-v2-mining` is the checkout you run from** (`G:\QUAKE_LEGACY`) and it
   carries none of the headless engine — 77 commits behind, 122 uncommitted
   files. Anything run from the repository root runs the April architecture
   plus local mining work.
3. **`review-headless-integration` and `feature/pantheon-world` are missing the
   same two modules**: `engine/pantheon/assets.py`, so captures render against
   whatever pk3s happen to be in the gamedir rather than the declared asset
   set; and `engine/pantheon/capture_lock.py`, so two renderers can clobber one
   `capture.cfg` — which is what happened on 2026-09-07. `git merge-tree`
   reports zero conflicts for both.
4. **`feature/creative-suite-v2` has zero commits of its own** and is 441
   behind. It is a worktree holding nothing but a stale copy.

### Concurrent activity tonight

A commit landed on `feature/pantheon-headless` at **23:18 tonight**
(`e3d47016`, adding `creative_suite/engine/frag_shapes.py`, 592 lines), and
`frag_shapes.db` and `match_roster.db` were written at 23:35. That is a
different working session from this one and it is still moving. Its scratch
files under `.tmp/` were deliberately spared by the cleanup.

---

## 4. Still owed — updated 2026-09-08

Four of these were closed the next day. What follows replaces the original
list, which was wrong in one place and is corrected here.

### Closed

- **HUD animation.** `engine/pantheon/hud.py`. 281 shader blocks inventoried
  and classified; nine treatments, split into those that can be cued and those
  that cannot. See `hud_wardrobe_and_voice.md`.
- **`assets.db` into the pipeline.** `engine/pantheon/asset_library.py`
  publishes ten looks as installable asset sets;
  `engine/pantheon/morph.py` plans the multi-take swaps. Four plans are
  shootable today.
- **DLSS.** Assessed and answered: it cannot run, and it is the wrong tool for
  an offline pipeline. See `dlss_and_supersampling_assessment.md`. The useful
  outcome was finding that `RenderProfile.internal_scale` had described
  supersampling for months with **no consumer**, so every master silently
  shipped at 1x. It has one now.
- **`review_db_write_safe` has no caller.** It does now — `put_review` asks
  the smallest of the three disk thresholds before writing a human verdict.

### Corrected

- **Voice generation was NOT "not started".** The original report said it was.
  `engine/pantheon/voice.py` already carried seven character voice profiles, a
  game-voice bank over the shipped VO, whisper word-alignment and an ffmpeg
  treatment chain, and a finished proof video existed. What was missing was
  one function, `synthesize()`, which is why the `tts_voice` field had no
  consumer. It now works end to end.
- **FT-3's `intro_lab` directory does not exist.** It is a row in the
  funded-track table and nothing on disk.

### Still open

- **Character animation beyond seven stances.** Authored motion works, but the
  vocabulary is 7 stances and exactly one gesture — `TORSO_FOLLOWME` and its
  siblings memcpy from `TORSO_GESTURE` for stock models, so they render
  identically. `CUSTOM_POINT_GESTURE = UNSUPPORTED_NATIVE` is already on the
  books and routes to Blender, which is registered as four UNKNOWN
  capabilities with no implementation. **Do not plan a pointing presenter
  against the native path.**
- **Zero HD sound assets.** Unchanged. The UHD packs contain no sound entries;
  the only audio is the 1,137 stock entries in `pak00.pk3`. That install does
  hold ~380 VO files including 40 transcribed instructional sentences, which
  is more than "stock" suggests.
- **Human verdicts nobody but a human can give.** `XRAY_ACTOR` awaits one;
  seven capabilities in the proof registry await one; no HUD pack or look has
  been confirmed to change a frame.
- **Captures nobody has run.** Four registered engine switches are unproven as
  output. `MASTER_RASTER` has never been captured at 5760x3240. A dissolve
  between two takes has never been frame-aligned.

### Branch table, updated

`feature/pantheon-headless` was local-only when this report was written. It is
now pushed and open as PR #16 against `main`. The three commits missing from
`review-headless-integration` remain missing, and `git merge-tree` still
reports zero conflicts for them.
