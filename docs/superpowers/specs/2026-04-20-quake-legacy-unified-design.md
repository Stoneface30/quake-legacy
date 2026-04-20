# QUAKE LEGACY — Unified Interface Design Spec
**Date:** 2026-04-20  
**Status:** Approved — proceed to implementation plan  
**Replaces:** All prior phase-scoped specs (2026-04-16, 2026-04-17 engine-pivot, Cinema Suite v2)

---

## 1. Vision

QUAKE LEGACY is a single interface: one web app that IS the GUI for the CLI engine underneath. No more phases. Everything — fragmovie assembly, demo extraction, texture generation, 3D intro lab, engine dissection — is a feature of one product.

- **User never touches the CLI** — the UI calls it
- **PANTHEON** = the clan / brand / aesthetic (gold + deep blue), not the product name
- **Public endgame** = `pip install quake-legacy` → give it demos → get a fragmovie (Phase 4 vision, not current focus)

---

## 2. New Folder Structure

```
QUAKE_LEGACY/                        ← git root
│
├── creative_suite/                  ← THE WHOLE APP
│   ├── api/                         ← FastAPI routers
│   ├── frontend/                    ← HTML/CSS/JS (includes /studio)
│   ├── web/                         ← /annotate + /creative routes
│   ├── engine/                      ← ★ formerly phase1/ (render pipeline)
│   ├── tools/                       ← ★ formerly tools/ (ffmpeg, comfyui, ghidra)
│   ├── database/                    ← ★ formerly database/ (schema + MusicLibrary)
│   ├── scripts/                     ← ★ formerly scripts/ (QA batch utilities)
│   ├── storage/                     ← ★ formerly storage/ (SQLite + thumbnails)
│   ├── tests/                       ← ★ formerly tests/ (all test suites)
│   ├── editor/                      ← OTIO bridge + state (expand for /studio)
│   ├── comfy/                       ← ComfyUI client + phase5 ESRGAN merged
│   ├── clips/                       ← clip parser (single source of truth)
│   ├── capture/                     ← WolfcamQL cfg writer
│   ├── db/                          ← SQLite migrate
│   ├── annotations/                 ← annotation store
│   ├── inventory/                   ← asset discovery
│   ├── pk3_build/                   ← pk3 assembler
│   └── ollama/                      ← local LLM (vision prompts)
│
├── engine/                          ← ★ formerly game-dissection/ + WOLF WHISPERER
│   ├── wolfcam/                     ← WolfcamQL fully ingested (binary + source)
│   ├── engines/                     ← all source trees (ioquake3, q3mme, wolfcamql, etc.)
│   ├── parser/                      ← ★ dm73 parser (formerly phase2/dm73parser)
│   ├── ghidra/                      ← RE outputs (FT-4)
│   ├── wolfcam-knowledge/           ← protocol-73 docs + cvar inventory
│   └── graphify-out/                ← combined engine knowledge graph output
│
├── demos/                           ← 13 GB .dm_73 corpus (stays at root)
├── QUAKE VIDEO/                     ← T1/T2/T3 source AVIs (stays at root)
├── output/                          ← render output (stays at root)
├── Vault/                           ← Obsidian memory (stays, full rewrite)
│
├── CLAUDE.md                        ← REWRITTEN (current rules only, new paths)
└── README.md                        ← REWRITTEN (unified interface vision)
```

### Cleanup Actions (destructive — confirm per item before executing)

| Action | Target |
|---|---|
| DELETE | `phase35/` (empty blueprint, no code) |
| DELETE | `WOLF WHISPERER/Backup/` (2017-2019 version archives) |
| DELETE | `WOLF WHISPERER/*.rar` (archived builds) |
| DELETE | `phase5/02_processed/`, `03_tga/`, `04_pk3/` (empty pipeline dirs) |
| DELETE | `docs/` entire tree AFTER extracting useful knowledge |
| DELETE | `HUMAN-QUESTIONS.md`, `NEXT_SESSION.md`, `OVERNIGHT_REPORT.md`, `SPLIT1_USER_CHECKLIST.md` AFTER extracting open items |
| MOVE | `phase1/` → `creative_suite/engine/` |
| MOVE | `tools/` → `creative_suite/tools/` |
| MOVE | `database/` → `creative_suite/database/` |
| MOVE | `scripts/` → `creative_suite/scripts/` |
| MOVE | `storage/` → `creative_suite/storage/` |
| MOVE | `tests/` → `creative_suite/tests/` |
| MOVE | `game-dissection/` → `engine/` (rename) |
| MOVE | `WOLF WHISPERER/WolfcamQL/` → `engine/wolfcam/` |
| CREATE | `engine/parser/` — dm73 parser C++17 project scaffold (phase2/dm73parser never existed on disk; start fresh here) |
| MOVE | `phase5/01_png/` → `creative_suite/comfy/assets/phase5_png/` |
| REWRITE | `CLAUDE.md` — extract live rules, kill dead ones, update all paths |
| REWRITE | `Vault/learnings.md` — extract reusable L-rules, wash stale ones |
| REWRITE | `.claude/projects/G--QUAKE-LEGACY/memory/` — full rewrite to new structure |
| REWRITE | `README.md` — unified interface vision |

### DRY Fix (code duplication)
`phase1/clip_list.py` and `creative_suite/clips/parser.py` both parse the FP > FL grammar.  
After move: `creative_suite/engine/clip_list.py` imports from `creative_suite/clips/parser.py`.

---

## 3. Engine Assimilation

The `engine/` folder is the home for building the **single unified `quake_legacy_engine`** — takes the best from all source engines, zero duplication.

**Source engines to assimilate:**
- ioquake3 (canonical GPL-2.0 base)
- WolfcamQL (protocol-73 demo playback, camera scripting)
- q3mme (free-cam recording, capture pipeline)
- uberdemotools (demo parsing reference)
- darkplaces / yamagi-quake2 (rendering techniques, reference only)
- gtkradiant (map tooling, reference only)

**Graphify run:** One combined knowledge graph of all engines in `engine/engines/` → `engine/graphify-out/combined.html`. Goal: visualize overlaps so we take the best of each and eliminate duplication in the merged engine.

**Demo parser** (`engine/parser/`) is dissected alongside the engine work — it uses the same protocol-73 knowledge from `engine/wolfcam-knowledge/`.

---

## 4. /studio — The Main Editor Route

Replaces `/editor`. Absorbs `/cinema`. `/annotate` and `/creative` stay as specialist routes.

### Page System (DaVinci-inspired, 5 pages)

| Page | Focus | Key Panels |
|---|---|---|
| **CUT** | Quick assembly — drag clips to timeline | Media bin, preview, simple timeline |
| **EDIT** | Full timeline editing, beat sync, effects | All panels active |
| **MIX** | Audio focus — beat matching, music library | wavesurfer-multitrack, BPM grid, music match % |
| **COLOR** | Grade controls per clip | Color inspector, before/after compare |
| **FORGE** | Skeleton: 3D intro lab + demo extractor UI | Placeholder panels, not functional yet |

### Layout (always-visible anchors)

```
┌─────────────────────────────────────────────────────────────────┐
│  QUAKE LEGACY  [CUT][EDIT][MIX][COLOR][FORGE]    ▶ ■ ◀ ▶▶  ⚙  │
├──────────────┬───────────────────────────────┬──────────────────┤
│              │                               │                  │
│  MEDIA BIN   │   PREVIEW CANVAS              │   INSPECTOR      │
│  20% width   │   WebCodecs + mp4box.js       │   20% width      │
│              │   always visible              │   Tweakpane v4   │
│  Tabs:       │                               │   + Theatre.js   │
│  • Clips     │                               │   curves         │
│  • Music     │                               │                  │
│  • Assets    │                               │   Context-aware: │
│              │                               │   clip selected  │
│  Music lib:  │                               │   → properties   │
│  match %     │                               │   → effects      │
│  auto BPM    │                               │   → keyframes    │
│  suggest     │                               │   → automation   │
├──────────────┴───────────────────────────────┴──────────────────┤
│  TIMELINE — always visible, 40% height                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ [GOLD] VIDEO  ▓▓▓▓ clip1 ▓▓▓▓  ▓▓▓ clip2 ▓▓  ▓ clip3   │   │
│  │ [GOLD] FX     ──── slowmo ────  ─── zoom ──             │   │
│  │ [CYAN] MUSIC  ████████ track1 ████████  ██ track2 ██    │   │
│  │ [CYAN] GAME   ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒  │   │
│  │ [CYAN] STEMS  wavesurfer-multitrack rows                 │   │
│  │        ──── beat markers ──●───────●───────●────── ──   │   │
│  └──────────────────────────────────────────────────────────┘   │
│  [Dockable, slides up] LiteGraph.js effect node graph           │
└─────────────────────────────────────────────────────────────────┘
```

### Color System
```
Background base:    #1a1a1a
Panel surface:      #242424
Panel hover:        #333333
Border:             #404040
Text primary:       #E0E0E0

Video / FX accent:  #D4AF37  (PANTHEON gold)
Audio accent:       #00B0F0  (cyan)
Action / CTA:       #FF9500  (high-tech orange)
Danger:             #FF4444
```

### Keyboard Shortcuts (industry standard)
```
J / K / L     — backward / stop / forward (playback)
Space         — play / pause
I / O         — in / out points
M             — add marker
Delete        — remove selected clip
Shift+Delete  — ripple delete
Cmd+K         — cut at playhead
Shift+F       — fit timeline to window
Alt+Scroll    — pan timeline horizontally
```

---

## 5. Tech Stack — Full Wiring

### Frontend Libraries (all security-audited before install)

| Library | Version | License | Source | Role |
|---|---|---|---|---|
| WebCodecs API | browser native | W3C | built-in | Frame-accurate decode in preview canvas |
| mp4box.js | latest | BSD-3 | CDN | MP4 demux for WebCodecs |
| animation-timeline-control | latest | MIT | npm (audited) | Video + FX timeline rows |
| wavesurfer.js | 7.x | BSD-3 | npm (audited) | Audio waveform + multitrack rows |
| wavesurfer-multitrack | bundled | BSD-3 | npm (audited) | Stem rows + sync |
| LiteGraph.js | upstream jagenjo | MIT | CDN | Per-clip effect node graph, beat-linked |
| Theatre.js `@theatre/browser-bundles` | latest | core Apache-2.0 | npm (audited) | Keyframe curves (studio AGPL OK — local personal tool) |
| Tweakpane | 4.x | MIT | existing | Inspector parameter binding |

**npm allowance rule applies to every install:**  
License ∈ {MIT, BSD-2, BSD-3, Apache-2.0, ISC} · `npm audit` clean · Snyk clean · pinned version · no network calls at build time.

### Backend Changes

| Change | Detail |
|---|---|
| MLT + Python SWIG | Verify MLT beats raw ffmpeg-CLI on: (a) serializable XML graph round-trips correctly, (b) drift audit still passes P1-BB ≤40ms, (c) all 26 P1-rules enforceable. If all three pass: `creative_suite/engine/render_part_v6.py` becomes thin wrapper over `MLTRenderer`. `.otio` → `.mlt` XML path added. If any fail: keep ffmpeg-CLI, document why. |
| OTIOBuilder | `creative_suite/editor/otio_bridge.py` extended — every rebuild emits a `.otio` sibling artifact. |
| New `/studio` route + API | `creative_suite/api/studio.py` router, `creative_suite/frontend/studio.html` page. |
| Music match API | New endpoint: `GET /api/music/match?part=N` — scores all tracks in MusicLibrary.json against the part's beat profile, returns ranked list with match %. |
| Beat auto-suggest API | New endpoint: `POST /api/music/autosync` — given selected track, returns suggested slowmo/speedup windows for best beat alignment. |

---

## 6. Music Library — Beat Match System

The MIX page makes the music library a first-class feature:

1. **Match %** — every track in MusicLibrary.json gets scored against the current part's `partNN_beats.json` (action peaks + section shapes). Score = BPM compatibility + section shape alignment + event density match.
2. **Auto slowmo/speedup** — when a track is selected, the beat_sync engine proposes speed effect windows (±0.8s around action peaks) to align with the track's drop/build/break sections. User sees the suggestion as overlays on the timeline before accepting.
3. **Snap to beat** — dragging a clip cut snaps to the nearest beat marker (individual).
4. **Auto-sync** — "Sync All" button runs the full `beat_sync.py` engine against the selected track and recalculates all cut placements for the whole part.

---

## 7. LiteGraph Effect Node Graph

**Now (AVI pipeline):** Per-clip graph. Nodes: source → trim → slowmo → zoom → grade → output. Beat events from `partNN_beats.json` are inputs to speed/zoom nodes (beat-linked).

**Endgame (demo extraction pipeline):** Graph embedded in creation pipeline. Nodes can swap sprites live, change animations, control camera parameters — full compositor replacing static effects.

Architecture: graph schema is forward-compatible. Beat-linked node type exists from day one.

---

## 8. FORGE Page — Skeletons

### Intro Lab (formerly phase35)
- Panel placeholder in FORGE page
- UI shell: select Q3 map, select player model (MD3), select style preset
- Backend stub: `POST /api/forge/intro` → returns `{"status": "not_implemented"}`
- Data: phase35 models/ directory merged into `creative_suite/comfy/assets/intro_lab/`

### Demo Extractor (formerly Phase 2)
- Panel placeholder in FORGE page  
- UI shell: drop `.dm_73` file, see parsed events table
- Backend stub: calls `engine/parser/` dm73 parser if compiled, else returns mock data
- Real extraction work happens in `engine/parser/` (C++17, separate build track)

---

## 9. Documentation Strategy

**Delete everything in `docs/`** — extract useful knowledge first into these replacement files:

| New file | Extracted from |
|---|---|
| `docs/reference/dm73-format.md` | `docs/reference/dm73-format-deep-dive.md` (keep technical spec, strip session notes) |
| `docs/reference/wolfcam-commands.md` | Keep as-is (24KB cvar inventory — still needed) |
| `docs/reference/engine-assimilation.md` | New — engine merge plan + graphify findings |
| `docs/reference/highlight-criteria.md` | `docs/specs/highlight-criteria-v2.md` (keep the locked v2 criteria) |
| `docs/reference/audio-rules.md` | Extract P1-G, P1-R, P1-AA, P1-Z rules into one audio reference |
| `README.md` | Rewrite — unified interface vision, folder map, quick start |
| `CLAUDE.md` | Rewrite — current rules only, new paths, no phase references |

Everything else (`_archive/`, `handoff/`, `superpowers/old-specs/`, `research/`, `reviews/`) → deleted after extraction.

---

## 10. Rules + Memory Wash

**CLAUDE.md rewrite principles:**
- No phase numbers anywhere (Phase 1, Phase 2 etc → gone)
- All paths updated to new structure (`creative_suite/engine/` not `phase1/`)
- Keep all P1-* rules that still apply — they govern the render pipeline regardless of where it lives
- Kill all session-state rules (NEXT_SESSION references, overnight report rules, etc.)
- New sections: /studio UI rules, engine assimilation rules, npm security rules

**Vault/learnings.md wash:**
- Keep L-rules that are genuinely reusable patterns (MOCK_ISOLATION, API_CONTRACT, PLATFORM_QUIRK, etc.)
- Kill L-rules that are session-specific observations or fixed bugs
- Consolidate duplicates (same pattern caught multiple times → one canonical rule)

**Memory files (.claude/projects/G--QUAKE-LEGACY/memory/):**
- Full rewrite — new folder structure, no phase references, new domain files matching new architecture

---

## 11. Security Rules (npm + dependencies)

Every npm package install requires ALL of:
1. License ∈ {MIT, BSD-2, BSD-3, Apache-2.0, ISC} — no AGPL on public-facing code (Theatre.js studio AGPL exception: local personal tool only)
2. `npm audit` — zero high/critical
3. Snyk advisory DB — clean
4. Pinned exact version (no `^` or `~`)
5. GitHub source with >1k stars OR >3 years maintained
6. No network calls at build time

**History:** Nearly had a vercel + litellm supply chain incident. This checklist is non-negotiable.

---

## 12. Open Items (extracted from root .md files before deletion)

From `HUMAN-QUESTIONS.md` — still blocking:
- **Part 3 style lock** — A/B/C/V5 hybrid decision needed before Parts 4-12 full batch render
- **Game audio level** — 0.55 vs 0.75 A/B test on next render pass (Config.game_audio_volume)

From `SPLIT1_USER_CHECKLIST.md` — still open:
- User reviews Parts 4/5/6 on 6-axis template (chain flow, beat, game audio, multi-angle, intro, grade)
- Parts 7-12 full renders unlock after Part 4 approved

From `OVERNIGHT_REPORT.md` — still outstanding:
- Parts 6/7 crashes need root cause fix before next batch run
- Parts 8-12 need clip_lists created (`partNN_styleb.txt` missing)
