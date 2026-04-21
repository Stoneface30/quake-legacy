# QUAKE LEGACY — Execution Status

*Last updated: 2026-04-21 (manual closeout refresh for cockpit stabilization)*

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
