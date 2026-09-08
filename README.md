<div align="center">

<img src="docs/brand/pantheon-mark.svg" width="120" alt="PANTHEON mark" />
<br/>

# QUAKE LEGACY

### AI-Powered Quake Live Fragmovie Production

**A single web app that IS the GUI for the render engine underneath — demo review, clip assembly, beat sync, and 1080p60 output, all without leaving the browser.**

[![License: GPL-2.0](https://img.shields.io/badge/license-GPL--2.0-e8b923?style=flat-square)](LICENSE)
[![Status](https://img.shields.io/badge/status-active%20development-2a9d2a?style=flat-square)]()
[![Stack](https://img.shields.io/badge/stack-FastAPI%20%7C%20WebCodecs%20%7C%20FFmpeg%20%7C%20OTIO-2a5acc?style=flat-square)]()
[Verification status](docs/reference/project-review-2026-09-05.md)

</div>

---

## What it is

Quake Legacy turns 10+ years of `.dm_73` Quake Live demos into finished fragmovies through a unified web cockpit. You review clips in a browser editor, assemble a timeline with beat-synced music, and the deterministic render pipeline handles everything else — three-tier clip combining, multi-track audio mixing, xfade transitions, title card, CRF 15 final encode.

**Vision:** Once this system works end-to-end it ships as `pip install quake-legacy` for the whole Quake community. All RE findings, format work, and camera math are public. The Q3 engine is open source — this is the gift back.

---

## Current Status

Current evidence and remaining limits are tracked in the [2026-09-05 project review](docs/reference/project-review-2026-09-05.md).

| Domain | Status |
|---|---|
| V1 archive | Frozen manifest present; records 68 episodes. Do not overwrite. |
| Reviewer | Mobile lifecycle repairs tested with synthetic media; live phone acceptance still required. |
| Demo parsing | Python parser and derived-event pipeline present; older C++ scaffold claims are historical. |
| Engine capture | Wolfcam integration present; legacy Cinema Tier A capture still needs source/config wiring. |
| Production contracts | ActionTruth / Scene provenance layer present; shared multi-backend ShotSpec / FrameTruth remains proposed. |
| Verification | See dated review for completed tests and repository-wide type-check debt. |

---

## Quick Start

> Python 3.11+. Capture tooling is configured for Windows; other platforms require tool-path adaptation.

```bash
git clone https://github.com/Stoneface30/quake-legacy.git
cd quake-legacy
pip install -e ".[dev]"

# Run the Creative Suite (FastAPI, port 8765)
python -m uvicorn creative_suite.app:create_app --factory --host 0.0.0.0 --port 8765 --reload
```

Browser URLs once running:

| URL | What |
|---|---|
| `http://localhost:8765/studio` | Full cockpit — STUDIO / LAB / CREATIVE |
| `http://localhost:8765/docs` | FastAPI auto-docs |
| `http://localhost:8765/health` | Health check |

For texture regeneration (ComfyUI required): see `CLAUDE.md` → "App Startup — Full Stack".

---

## The Cockpit — Three Modes

`/studio` is a single-page app with one observable store (`studio-store.js`) and three top-level modes:

### STUDIO (`?mode=studio`)

The editing workspace. Two views:

- **CLIPS** — Part browser; select a part to enter EDIT
- **EDIT** — Integrated NLE: preview panel, clip timeline (animation-timeline-js), audio waveforms (wavesurfer-multitrack), FX node graph (LiteGraph), inspector (Tweakpane + Theatre.js)

### LAB (`?mode=lab`)

Engine and demo tooling. Pages: `demos` · `extraction` · `patterns` · `annotate` · `flags` · `forge` · `engine`. Forge status is honest about stub vs ready.

### CREATIVE (`?mode=creative`)

ComfyUI texture pipeline control. Asset panels grouped by kind: `maps` · `skins` · `sprites` · `packs` · `prompts`. Queue panel pulls from `/api/variants/feed`.

---

## Screenshots

All visual records live in `docs/visual-record/YYYY-MM-DD/`.

| Screenshot | Path |
|---|---|
| Studio CLIPS page | `docs/visual-record/2026-04-22/studio_clips.png` |
| Studio CLIPS — clip selected | `docs/visual-record/2026-04-21/studio_clip_selected.png` |
| Studio EDIT page (NLE) | `docs/visual-record/2026-04-21/studio_edit_page.png` |
| Cockpit v2 — LAB mode stubs | `docs/visual-record/2026-04-21/cockpit-v2-lab-mode-stubs.png` |
| Cockpit v2 — CREATIVE mode | `docs/visual-record/2026-04-21/cockpit-v2-creative-mode.png` |
| Part 4 title card smoke | `docs/visual-record/2026-04-18/title_card_quake_smoke_part04_t003.png` |
| Part 4 render frames | `docs/visual-record/2026-04-19/part04_grid.png` |
| Engine knowledge graph | `docs/visual-record/2026-04-17/engine-graphify/graphify_canonical_top_hubs_overview.png` |

---

## Production Pipeline — 12 Parts

**Clips on disk** (T1 / T2 / T3 tiers):

- **Parts 4–12**: 77–85 AVI clips per part, ready to render
- **T1** = elite/rare frags (climax moments)
- **T2** = main meal (≥70% of screen time)
- **T3** = atmospheric/cinematic (intro/outro pool)

**Render pipeline** (`creative_suite/engine/render_part_v6.py`):

- PANTHEON intro (5s) + Quake-style title card (8s) + body clips
- Beat-synced 3-track music (intro / main / outro), full-length coverage contract
- 0.40s xfade seams, event-localized slow-mo (P1-Z confidence gate ≥0.55)
- CRF 15 · x264 High · 1920×1080 · 60 fps
- A/V drift gate: < 40 ms per minute (ffprobe audited post-render)

**Music status**: Parts 4–12 have 5–6 track slots each. Parts 1–3 need music assigned.

---

## Architecture

```
creative_suite/
  app.py                  FastAPI entry (port 8765)
  api/                    Routers: studio · forge · clips · comfy · assets
  engine/                 Render pipeline (render_part_v6.py, beat_sync, effects…)
  frontend/               /studio SPA
    studio-store.js       Observable store — single source of truth
    studio-pages.js       Mode/page router (STUDIO/LAB/CREATIVE)
    studio-edit.js        Integrated NLE workspace
    css/tokens.css        PANTHEON design tokens
    icons/pantheon.svg    39-glyph SVG sprite
  comfy/                  ComfyUI integration (workflows, pipelines, loras)
  database/               MusicLibrary.json, frags.db, studio_nle.db

engine/
  parser/                 dm_73 C++17 parser scaffold (FT-1)
  wolfcam/                WolfcamQL binary + staging
  engines/                ioquake3 · wolfcamql · q3mme (SHA-256 deduped)
  ghidra/                 RE outputs (wolfcamql fully decompiled, 5,091 fns)

demos/                    .dm_73 corpus — NOT committed (gitignored)
output/                   Render output — NOT committed
```

---

## Milestones

- [x] **Plan 1** — Repo restructure, reference docs, CLAUDE.md ruleset (16 rules)
- [x] **Plan 2** — Studio cockpit: 8 REST endpoints, observable store, 5 panels, multi-mode router
- [x] **Plan 3** — Engine assimilation: OTIO bridge, MLT scaffold, dm_73 C++17 parser, FORGE stubs, knowledge graph, WolfcamQL ingestion
- [x] **Cockpit v2 closeout** — Shell contract locked, test suite 561 passing, wiring pass complete
- [ ] **Plan 4** — Live demo extraction UI (Scout/LAB fully wired, not stubbed)
- [ ] **Plan 5** — Live-link engine WebSocket (25 Hz state, real-time camera control)
- [ ] **Plan 6** — Ship Part 4 end-to-end through 8 acceptance gates

---

## Technology Stack

**Frontend**: Vanilla JS + Web Components · WebCodecs · animation-timeline-js · wavesurfer-multitrack · LiteGraph · Tweakpane · Theatre.js · mp4box.js

**Backend**: FastAPI · SQLite + FTS5 · OpenTimelineIO · MLT framework

**Engine**: C / C++17 · CMake · ioquake3-derived · WolfcamQL

**Render**: FFmpeg (CRF 15, x264 High) · Beat This! beat detection · msaf music structure

**AI/Textures**: ComfyUI · dreamshaper_8 SD1.5 · control_v11f1e_sd15_tile ControlNet · 4x-UltraSharp upscaler

---

## What Is and Isn't Committed

**Committed**: all source, design tokens, logos, docs, fixtures, test harnesses, the 39-icon sprite.

**Never committed**: `.dm_73` · `.avi` · `.mp4` · player names · Steam IDs · `.db` files · anything under `demos/` `output/` `QUAKE VIDEO/`.

---

## License

**GPL-2.0** — inherited from ioquake3 + wolfcamql + q3mme lineage. The PANTHEON design system (logos, tokens, icon sprite under `docs/brand/`) is released under **CC BY 4.0**.

Not affiliated with id Software, ZeniMax, or the Quake Live team.

---

<div align="center">

**Quake Legacy** — built for the scene that refused to stop recording.

</div>
