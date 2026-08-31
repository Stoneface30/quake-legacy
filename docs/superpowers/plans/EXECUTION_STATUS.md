# QUAKE LEGACY — Execution Status

*Last updated: 2026-08-27 (review-state refresh - see the 2026-08-27 Audit at the end of this file)*

Three plans are being executed via Subagent-Driven Development.
Original plan docs were lost during the P1 restructure. This file is the live tracker.

---

## Plan 1 — Foundation Restructure ✅ COMPLETE

All 10 tasks done. Commits: 935a1444 → fad72d49.

| Task | Status | What |
|---|---|---|
| P1-T1 | ✅ | `docs/reference/` — 16 reference docs (audio, dm73, highlight-criteria, wolfcam, etc.) |
| P1-T2 | ✅ | `creative_suite/config.py` — REPO_ROOT, CS_ROOT, TOOLS_ROOT, DATABASE_ROOT constants |
| P1-T3 | ✅ | DRY clip parser — public `parse_clip_entry` in `creative_suite/clips/parser.py` |
| P1-T4 | ✅ | `_rebuild_job.py` path fix + stale comment cleanup |
| P1-T5 | ✅ | `tools/uberdemotools/` README reference updated |
| P1-T6 | ✅ | `phase5/` PNG assets verified (107 files in subdirs — no data loss) |
| P1-T7 | ✅ | Docs restructure (plan files were here — now lost; this doc replaces them) |
| P1-T8 | ✅ | `CLAUDE.md` rewritten — all 23 P1-* rules with updated paths, CS-1..6, UI-1..3, ENG-1..5 |
| P1-T9 | ✅ | `README.md` rewritten — clean 53-line version with Quick Start |
| P1-T10 | ✅ | Memory updated — `project_context.md`, L160 in learnings.md |

---

## Plan 2 — Studio UI Wiring ✅ COMPLETE

Building a Premiere-class `/studio` editor. Libraries: animation-timeline-js, wavesurfer-multitrack, mp4box.js, litegraph.js, Theatre.js, Tweakpane.

| Task | Status | Commits | What |
|---|---|---|---|
| P2-T1 | ✅ | d6f41da5, d8bcf988, 78af9334 | npm security audit, 7 vendor libs (incl. litegraph), AGPL exception documented |
| P2-T2 | ✅ | 29192251 | `creative_suite/api/studio.py` — `/api/studio/parts`, `/clips`, `/flow`, `/status` |
| P2-T3 | ✅ | (after T2) | `studio.html` shell + `studio.css` PANTHEON dark theme, `GET /studio` route |
| P2-T4 | ✅ | 21b0058c | `studio-store.js` (observable store) + `studio-app.js` (bootstrap) |
| P2-T5 | ✅ | fa5ef553 | `studio-preview.js` — WebCodecs preview panel, LRU frame cache, graceful fallback |
| P2-T6 | ✅ | 420eee97 | `studio-timeline.js` — animation-timeline-js clip timeline, Canvas 2D fallback |
| P2-T7 | ✅ | (after T6) | `studio-audio.js` — wavesurfer-multitrack audio waveform panel |
| P2-T8 | ✅ | ff6d353d | `studio-beatmarkers.js` — beat markers overlay + `/api/studio/part/{n}/beats` |
| P2-T9 | ✅ | aae6cbfe | Music library panel + `music_match.py`, `/api/studio/part/{n}/music` |
| P2-T10 | ✅ | 471dd97d | LiteGraph effect node graph, 5 custom Quake node types |
| P2-T11 | ✅ | a1ea1e48 | Inspector panel (Tweakpane + Theatre.js core), Theatre disposal fix |
| P2-T12 | ✅ | (after T11) | Multi-mode cockpit router `studio-pages.js` — current live contract is `STUDIO = { CLIPS, EDIT }` plus LAB and CREATIVE |

Current source of truth:

- [docs/reference/cockpit-v2-contract.md](/mnt/g/QUAKE_LEGACY/docs/reference/cockpit-v2-contract.md)
- [docs/superpowers/plans/2026-04-21-cockpit-ui-closeout-stabilization.md](/mnt/g/QUAKE_LEGACY/docs/superpowers/plans/2026-04-21-cockpit-ui-closeout-stabilization.md)

Archived earlier five-page-shell design materials:

- [docs/_archive/2026-04-21-cockpit-shell/README.md](/mnt/g/QUAKE_LEGACY/docs/_archive/2026-04-21-cockpit-shell/README.md)

---

## Plan 3 — Engine Assimilation (0 of 7 done)

Independent tasks (P3-T4/T5/T6/T7) can run after P1. P3-T1 needs P2-T9 first.

| Task | Status | What | Dependency |
|---|---|---|---|
| P3-T4 | ✅ | d23dcb5d | OTIO bridge — emits `.otio` on rebuild, lazy import guard |
| P3-T5 | ✅ | 59dcc622 | MLT: ADOPT via conda-forge (user approved 600MB overhead) |
| P3-T6 | ✅ | (after T5) | dm73 C++17 scaffold — CMake, reader.h, frag_extractor, dm73dump CLI |
| P3-T7 | ✅ | 7bb3df52 | FORGE stubs — `/api/forge/status`, `/intro`, `/demo/extract` |
| P3-T1 | ✅ | 05994caf | Music contract — `validate_music_coverage`, `/api/studio/part/{n}/music_contract` |
| P3-T2 | ✅ | (after T1) | Engine knowledge graph — 21 nodes, 25 edges, interactive HTML |
| P3-T3 | ✅ | (after T2) | WOLF WHISPERER ingestion — wolfcam inventory + capture scaffolding |

---

## Cockpit UI Closeout Stabilization ✅ COMPLETE

Plan: `docs/superpowers/plans/2026-04-21-cockpit-ui-closeout-stabilization.md`

Closes the gap between the live `/studio` shell, test suite, and documentation after the
multi-mode cockpit rewrite. Current shell contract is `STUDIO = { CLIPS, EDIT }` — the old
five-page router (preview/timeline/audio/effects/inspector) is retired.

| Task | Status | Commits | What |
|---|---|---|---|
| T1 — Shell contract tests | ✅ | 65948831 | Replace stale 5-page assertions; add mode-switch + URL-sync coverage |
| T2 — CREATIVE asset panels | ✅ | 6cdd6eeb | `?kind=` filter on `/api/assets`; creative-maps/skins/sprites use `?kind=` |
| T3 — Variant queue/pack gating | ✅ | f6179bd9 | Add `/api/variants/feed`; creative-queue.js → feed; packs already correct |
| T4 — LAB payloads + lifecycle | ✅ | b5effa46 | lab-forge STUB→BLOCKED; extract DONE→QUEUED; static contract tests |
| T5 — Docs/visual records | ✅ | (this commit) | cockpit-v2-contract.md updated; EXECUTION_STATUS updated; visual-record README |

Backend API changes:
- `GET /api/assets?kind={maps|skins|sprites}` → shell-level asset grouping (was `?category=`)
- `GET /api/variants/feed` → flat recent variant list for CREATIVE/QUEUE panel

---

## Test Count

| When | Tests |
|---|---|
| Pre-session baseline | 185 passing |
| After P1 (phase1 tests moved in) | 217 collected, 5 pre-existing failures |
| After P2-T8 | 33 new studio tests + earlier = ~250+ collected |

---

## Key Library API Notes (for future implementers)

| Library | Vendor file | Actual global | Notes |
|---|---|---|---|
| animation-timeline-js | `vendor/animation-timeline.js` | `window.timelineModule` | `new timelineModule.Timeline(options, model)` — `options.id` must be element ID string |
| wavesurfer-multitrack | `vendor/wavesurfer-multitrack.js` | `globalThis.Multitrack` | `Multitrack.create(tracks[], options)` — embeds own WaveSurfer copy |
| wavesurfer.js | `vendor/wavesurfer.js` | ES module — no IIFE global | Not needed directly; multitrack bundles it |
| litegraph.js | `vendor/litegraph.js` | `LiteGraph` | Standard canvas graph editor |
| tweakpane | `vendor/tweakpane.js` | `Tweakpane` | `new Tweakpane.Pane({ container })` |
| theatre-core-studio | `vendor/theatre-core-studio.js` | `TheatreStudio`, `TheatreCore` | AGPL-3.0 Studio — local use only (see CLAUDE.md exception) |
| mp4box | `vendor/mp4box.js` | `MP4Box` | `MP4Box.createFile()` |

---

## 2026-04-23 Audit — Pipeline State Snapshot

*Audit run against live server state as of 2026-04-22. Commits through PR #15 (d39e62b1).*

**Server:** FastAPI @ port 8765, running (reloader PID 26852)

**Test suite:** 562 collected, all passing (up from 561 after inspector Tweakpane wiring)

**Clip inventory (all 12 Parts stocked):**

| Tier | Per-Part count |
|---|---|
| T1 | 29–31 |
| T2 | 36–42 |
| T3 | 11–12 |

**Clip lists:** Parts 1-3 and 5-12 have populated sequences. **Part 4 clip list is empty** — ordering pass needed before render.

**frags.db:** 222 frags · 11 demos · 26,441 player_snapshots · 0 rendered_clips

**Music status:**
- Parts 4-12: multi-track slots present (5-6 files each, 41/41 source verified)
- Parts 1-3: **no music assigned** — needs track selection before render
- Part 4 slots _01 and _04: **truncated (~2 min)** — full tracks needed (see P1-R)

**Renders:** 0 assembled Parts — render pipeline has not run end-to-end on the new unified stack yet.

**Next hard blockers before first render:**
1. Part 4 clip list — ordering pass (Gate R-1)
2. Parts 1-3 music assignment
3. Part 4 music tracks _01/_04 replaced with full-length versions

---

## 2026-08-27 Audit — Review State Refresh

*Run against a clean boot of the unified stack. Supersedes the 2026-04-23 audit above where they disagree.*

### Stack

| Item | State |
|---|---|
| Test suite | **579 passed, 3 skipped** (was 562) |
| App factory | imports clean — **110 routes** |
| Server | started on **port 8770** (see port conflict below) |
| `/studio`, `/annotate`, `/cinema`, `/docs`, `/api/studio/*` | all **200** |

### ⚠ Port 8765 conflict (new finding)

`creative_suite/config.py:20` sets `port: int = 8765`, and `start_server.bat` /
`kill_and_start.bat` hardcode 8765. **8765 is also `POLYBOT_API` in the global
`~/.claude/.mcp.json`**, and Obscura (pythonw) holds the socket. Running
`kill_and_start.bat` will kill the Obscura/Polymarket service.

**Decision needed:** move Quake Legacy off 8765 (config + both .bat + CLAUDE.md + docs),
or move Obscura/Polybot. Until resolved, launch with an explicit `--port`.

Also: `uvicorn.exe` from the venv exits immediately with no output when launched detached.
`python -m uvicorn` works. Use the module form in launch scripts.

### Plan completion

| Plan | Status |
|---|---|
| Plan 1 — Foundation Restructure | ✅ COMPLETE |
| Plan 2 — Studio UI Wiring | ✅ COMPLETE |
| Plan 3 — Engine Assimilation | ✅ COMPLETE (7/7) |
| Cockpit UI Closeout Stabilization | ✅ COMPLETE |
| **2026-04-23 NLE Cockpit Full** | ✅ **COMPLETE (8/8)** — plan file checkboxes were stale, banner added |
| Music Manager sprints 1/2/3 | ✅ landed `5a1f08dd` — **no plan doc exists**, undocumented scope |

### Corrected: Parts 1-3 are NOT a blocker

The 2026-04-23 audit listed "Parts 1-3 music assignment" as a hard blocker. **This is wrong.**
`creative_suite/api/studio.py:251` sets `_VALID_PARTS = range(4, 13)` and
`creative_suite/engine/config.py:306` sets `self.parts = list(range(4, 13))` —
Parts 4-12 are the deliberate production scope (Parts 1-3 are already-published legacy videos).

The *real* defect is a UI/API contract mismatch: the CLIPS page lists **Parts 1-12**, and
`studio_nle.db` holds 85 arrangement rows for Part 1, but `/api/studio/part/{1,2,3}/music`
(and `/beats`, `/flow`) return **404 "not in range 4-12"**. Either gate the Part selector to
4-12 or extend the backend.

### Live UI defects (observed on clean boot, `/studio`)

| # | Defect | Evidence |
|---|---|---|
| 1 | `/api/studio/clip-thumb` returns **400 "Path must be absolute"** — preview shows "Thumbnail unavailable" | frontend sends basename `Demo (123)  - 40.avi`; endpoint requires abs path. DB *has* abs paths. |
| 2 | **All 85 Part 1 `duration_s` are NULL** — timeline renders uniform-width blocks; beatmatch has no real durations | T5 ffprobe runs only on *new* import; no backfill |
| 3 | `Unexpected token 'export'` at page load | `studio.html:53` loads `/vendor/wavesurfer.js` as a classic script; it is an ES module. Project's own notes say multitrack bundles it — **the tag should be deleted** |
| 4 | Theatre.js logs an error on **every** page load | `theatre-core-studio.js` imported without `studio.initialize()` |
| 5 | Part 03 shows a `MUSIC` badge with **0 audio slots** | only a stale `part03_music.ogg.beats.json` on disk |
| 6 | `/favicon.ico` 404 | cosmetic |

### Data inventory

| Store | State |
|---|---|
| Clip lists | Parts 1-3, 5-12 populated; **`part04.txt` still empty** (`part04_stylea/b/c.txt` hold 103/103/43) |
| `studio_nle.db` | 136 arrangements — Part 1: 85, Part 4: 51. 0 trashed. All `duration_s` NULL |
| `frags.db` | 222 frags · 11 demos · 26,441 snapshots · **0 rendered_clips** |
| Music | Parts 4-12 all have 5-6 slots. Part 4 slots are **full length** (3:17–5:59) — the "truncated ~2 min" note in the 2026-04-23 audit is **stale/resolved** |
| Renders | **0 assembled Parts** — pipeline still never run end-to-end |

### Real blockers before first render

1. `part04.txt` ordering pass (Gate R-1) — pick from stylea/styleb/stylec
2. Backfill `duration_s` for all arrangements (blocks beatmatch + timeline accuracy)
3. Fix `clip-thumb` path contract (blocks visual review in the NLE)
4. Resolve the 8765 port conflict before any scripted launch

### Visual record

`docs/visual-record/2026-08-27/` — `studio_boot_clips_page.png`, `studio_boot_edit_page.png`

---

## 2026-08-28 — FIRST END-TO-END RENDERS (Parts 4, 5, 6)

The pipeline had never completed a Part. It turned out this was not a tuning
problem but a hard bug.

### Root cause: slow-mo normalization never terminated

`normalize.py::_audio_filter()` appends `apad` for slow clips, which pads audio
*indefinitely*. `-shortest` was only appended on the `speedup` branch, so ffmpeg
never reached EOF and encoded silence until the disk filled. Observed: one 6.3 s
source clip consumed 700+ CPU-seconds and a 69 MB `.partial`, still growing.

Fix: `-shortest` on both speed branches. **714 s -> 3.3 s** on the same clip,
output duration correct (12.77 s for a 2x stretch of 6.3 s).
Guarded by `creative_suite/tests/test_normalize_slow_terminates.py`.

### Results — both hard ship gates PASS on all three

| Part | Duration | Size | Level gate (P1-G, >=12 LU) | Sync drift (P1-BB, <=40 ms) | Wall |
|---|---|---|---|---|---|
| 4 | 26:14 | 1939.8 MB | 13.6 LU PASS | 12.0 ms PASS | 13.9 min |
| 5 | 28:59 | 2117.1 MB | 14.4 LU PASS |  8.0 ms PASS | 32.9 min |
| 6 | 25:35 | 1784.0 MB | 16.7 LU PASS |  6.7 ms PASS | 30.9 min |

1920x1080 @ 60 fps, h264 + aac. Music plan verdict PASS on all three.
Profile: `preview` (CRF 23 veryfast). **Not yet re-run at `--profile final`.**

### Other production bugs fixed this session

| Bug | Fix | Test |
|---|---|---|
| Title cards rendered **over black** (P1-Y violation) — `pick_intro_backdrop_fls` built its path from `config.ROOT` (=`creative_suite/`) but the corpus is at `REPO_ROOT` | use `cfg.clips_root` / `REPO_ROOT` | `test_title_backdrop_root.py` |
| Title-card fonts absent **and** the BebasNeue fallback absent -> `drawtext` had no usable face | fetched the 4 OFL faces named in P1-Y into `creative_suite/engine/assets/fonts/` | — |
| A corrupt cached chunk aborted a whole Part (`CalledProcessError` from `_probe_duration`) | added normalize's L154 validate-before-trust guard to the chunk cache | — |
| VIS-1 auto-capture **never ran** — `creative_suite/engine/visual_record.py` was imported but never written | implemented; samples only the intro/title window so gameplay HUD nicknames stay out of the public repo | `test_visual_record.py` |
| `/api/studio/clip-thumb` 400 "Path must be absolute" | tolerant resolver + cached basename index, traversal still refused | `test_clip_path_resolve.py` |
| All 136 `duration_s` NULL | `creative_suite/database/backfill_durations.py` — 136/136, 0 failures | — |
| `Unexpected token 'export'` on every page load | removed the ES-module `wavesurfer.js` classic-script tag | — |
| Theatre.js error on every page load | headless init shim | — |
| `/favicon.ico` 404 | wired `pantheon.svg` | — |

### PANTHEON intro/outro rebuilt

`IntroPart2.mp4` **and** its configured successor `intro_trim_7s.mp4` are both
absent from disk (searched all of `G:\` and `E:\PersonalAI`). New module
`creative_suite/engine/pantheon_intro.py` redraws the brand mark with PIL (no SVG
rasteriser is installed) so each element animates, composited over graded FL
demo footage. Wired into `cfg.intro_source` per P1-C and confirmed present at the
head of all three renders.

**Scope limit:** this is animated 2.5D, NOT engine-rendered 3D. FT-3 has no
pipeline — `/api/forge/intro` is a stub returning "not yet implemented" and no
MD3/BSP renderer exists.

### Test suite

**596 passed, 3 skipped, 0 failures** (was 562 at session start).

### Still open

1. Re-run at `--profile final` (P1-J) once the preview cuts are approved
2. Gates R-2 / R-3 — human review of the actual video, not just the gate numbers
3. `msaf has no attribute 'process'` — music structure analysis runs degraded
4. `PySoundFile failed -> audioread` fallback on onset detection (slow, deprecated)
5. Nothing is committed yet

---

## 2026-08-29 — Netcode review (dm_73 parser)

### CRITICAL, FIXED: snapshot areamask off-by-one desynced 73.6% of every demo

`engine/parser/demo_parse.py::_parse_snapshot` read `areamaskLen + 1` bytes
("QL stores count-1"). It does not — `docs/reference/dm73-format-deep-dive.md:348`
says `areamask byte[areamaskLen]`, matching Q3 `CL_ParseSnapshot`.

One extra byte desynced the bitstream at the head of every snapshot; playerstate
and all entity deltas after it decoded as garbage and overran the payload.

| | packets OK | failed | dropped |
|---|---|---|---|
| before | 5,652 | 15,737 | **73.6%** |
| after | 21,389 | 0 | **0.0%** |

Hidden because `parse()` swallows every packet exception with a bare
`except Exception: pass`. One demo now yields 9,162 events / 19,908 snapshots /
16 rounds / 63 obituaries. `frags.db` (222 frags across 11 demos) was built on
the broken parser and **must be rebuilt**.

Guarded by `creative_suite/tests/test_dm73_netcode.py`.

### Remaining netcode findings (NOT yet fixed)

| # | Severity | Finding |
|---|---|---|
| N1 | HIGH | `parse()` swallows all packet errors silently and keeps no counter — a systematic desync is indistinguishable from trailing garbage. Add a drop counter + threshold. |
| N2 | MED | `_Bits.readbits()` has no sign extension. Q3 `MSG_ReadBits` sign-extends for negative bit counts; `_PS_BITS` is documented as "abs values of signed fields", so signed playerState fields decode as large positives. |
| N3 | MED | `_Bits.readstring()` has no length cap. Q3 caps at MAX_STRING_CHARS (1024). Unbounded read on malformed input. |
| N4 | MED | No `MAX_MSGLEN` sanity check on the packet `length` header before `fh.read(length)`. A corrupt length triggers a huge allocation. |
| N5 | LOW | `_Bits`/`_AdaptiveHuff.receive()` index `data[offset >> 3]` with no bounds check — overruns surface as IndexError rather than a clear framing error. |
| N6 | LOW | The demo `seq` header and the per-packet ack sequence are read and discarded; no ordering/duplicate validation. |
| N7 | DOC | FT-1 is documented as a "C++17 dm73 parser scaffold — CMake, reader.h, frag_extractor, dm73dump CLI, validated against UDT_json.exe". **None of it exists.** `engine/parser/` contains `demo_parse.py` + `db_ingest.py` only. Same documentation-vs-reality gap as `effects.py` and `visual_record.py`. |

Test suite: **619 passed, 3 skipped**.
