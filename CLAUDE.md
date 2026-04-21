# QUAKE LEGACY — Project Instructions for Claude

This file is loaded automatically every Claude Code session for this project.

## What This Project Is

QUAKE LEGACY is a single unified interface: one web app that IS the GUI for the CLI engine underneath. AI-powered Quake Live fragmovie production system.

- 10+ years of `.dm_73` Quake Live demo recordings → automated fragmovie pipeline
- All features in one place: video assembly, demo extraction, texture generation, 3D intro lab, engine dissection

**GitHub:** https://github.com/Stoneface30/quake-legacy (PUBLIC repo)
**Local root:** G:\QUAKE_LEGACY
**User role:** Creative director, quality judge — approves everything before batch runs.
**Editing brand:** PANTHEON (temple logo, grey/silver style)

## CRITICAL: Public Repo Rules

- **NEVER commit** player names, nicknames, personal identifiers, Steam IDs
- **NEVER commit** .dm_73, .avi, .mp4, .db, .env files
- Demo player names are anonymized in all code and docs
- All gameplay analysis is statistical — no player profiles

## New Folder Structure

```
G:\QUAKE_LEGACY\
  creative_suite/          <- THE WHOLE APP
    engine/                <- render pipeline (was phase1/)
    tools/                 <- ffmpeg, ghidra, comfyui (was tools/)
    database/              <- MusicLibrary.json, frags.db (was database/)
    api/                   <- FastAPI routers
    frontend/              <- HTML/CSS/JS (includes /studio)
    tests/                 <- all test suites
    editor/                <- OTIO bridge + state
  engine/                  <- engine source trees (was game-dissection/)
    engines/               <- ioquake3, wolfcamql, q3mme, etc. (SHA-256 deduped)
    wolfcam/               <- WolfcamQL binary + staging (from WOLF WHISPERER)
    wolfcam-knowledge/     <- protocol-73 docs + cvar inventory
    parser/                <- dm73 C++17 parser scaffold (FT-1)
    ghidra/                <- RE outputs (FT-4)
    graphify-out/          <- combined engine knowledge graph
  demos/                   <- 13 GB .dm_73 corpus (stays at root)
  QUAKE VIDEO/             <- T1/T2/T3 source AVIs (stays at root)
  output/                  <- render output (stays at root)
```

## Key Tool Paths

```
FFmpeg:      creative_suite/tools/ffmpeg/ffmpeg.exe
WolfcamQL:   engine/wolfcam/WolfcamQL/wolfcam-ql/wolfcamql.exe (moved from WOLF WHISPERER)
UDT:         creative_suite/tools/uberdemotools/UDT_json.exe
Ghidra:      creative_suite/tools/ghidra/
MusicLib:    creative_suite/database/MusicLibrary.json
Demo corpus: demos/ (6,465 .dm_73 files, 13.19 GB)
T1/T2/T3:   QUAKE VIDEO/T1/Part1-12/, T2/, T3/
PANTHEON intro: FRAGMOVIE VIDEOS/IntroPart2.mp4
```

## HARD RULES — Render Pipeline

*Superseded versions archived at `docs/_archive/claude-md-superseded-2026-04-19.md` — grep by rule ID.*

---

### 1. AUDIO

#### P1-G (Music mix) [v5, 2026-04-18]
- **WHAT** Music volume 0.20. PANTHEON = own audio only; music fades in 0→0.20 over 1.5s at title-card start; body = game 1.0 + music 0.20 sidechain-ducked. Final render MUST pass ebur128 gate: music ≤ −12 LU below game peak, else render is `FAILED_LEVEL_GATE` and not shipped.
- **WHERE** `cfg.music_volume=0.20`, `cfg.music_fadein_s=1.5` · `render_part_v6.py::final_render` audio graph (3-segment concat: PANTHEON+own-audio | title+music-fadein | body+game+ducked-music) · `creative_suite/engine/audio_levels.py::measure_music_vs_game` · `output/partNN_levels.json`
- **WHY** Subjective complaints about music loudness repeat every review (v1/v2/v3/v4). Objective gate ends it.

---

### 2. TRIMMING

#### P1-L (Head/tail trim) [v4, 2026-04-18]
- **WHAT** FP clips: head=0, tail=0 (frags are clean start-to-end). FL clips: head=1.0s (console), tail=2.0s (angle falloff). Skip any clip whose post-trim body < 2.0s (min_playable). No speed-stretch to fit.
- **WHERE** `cfg.clip_head_trim_fp=0.0`, `_fl=1.0` · `clip_tail_trim_fp=0.0`, `_fl=2.0` · `min_playable_duration_s=2.0` · `render_part_v6.py::build_body_chunks` · per-clip overrides in `partNN_overrides.txt` win over defaults.
- **WHY** Trimming FP was always wrong; only FL needs edges cleaned. Short-clip protection prevents 1s blurs.

#### P1-D (Preview clip-name burn-in)
- **WHAT** Preview renders burn the original clip filename in bottom-left at 18pt. Final renders do NOT show clip names.
- **WHERE** `render_part_v6.py` preview branch only · full renders strip the drawtext overlay.
- **WHY** User references clips by name/timestamp when giving edit feedback — the label must be on-screen in the review loop.

---

### 3. TRANSITIONS

#### P1-H (Transitions) [v4, 2026-04-18]
- **WHAT** 0.40s seam xfade between every body chunk. Banned: any xfade ≥0.8s, fade-to-black, dip-to-white, cross-dissolve >0.3s, any intro/outro dramatic fade.
- **WHERE** `cfg.seam_xfade_duration=0.40` · `render_part_v6.py::assemble_body_with_xfades` · every chunk audio enters with `asetpts=PTS-STARTPTS,aresample=async=1:first_pts=0` (drift fix ships with P1-BB).
- **WHY** User asked for visible transitions four times; v1's "hard cuts only" was rejecting 1s drama fades, not short bleeds. 0.4s is the minimum perceptible seam.

---

### 4. MUSIC STRUCTURE

#### P1-R (Three-track music contract) [v2, 2026-04-18; merges P1-O + P1-W]
- **WHAT** Every Part ships THREE tracks: intro + main + outro. Intro plays under PANTHEON+title (default: *Cinema - Sped Up*). Main = per-Part hype pick. Outro = ~30s cooldown (default: *Eple - Badger*). Continuous coverage mandatory — silence gaps = render failure. All tracks play FULL; last may truncate at phrase boundary only (see P1-AA). Mid-song cuts banned.
- **WHERE** `Config.intro_music_path(part)` / `music_path(part)` / `outro_music_path(part)` · `creative_suite/engine/music_stitcher.py` · per-Part overrides `partNN_intro_music.*` / `partNN_outro_music.*` resolved first.
- **WHY** Single-track renders rejected by user; mid-song swaps rejected twice; silence gaps rejected once. Three-track + continuous = stable contract.

#### P1-AA (Music stitcher — video is truth) [v2, 2026-04-18]
- **WHAT** Video body length rules. Queue N full tracks until `sum(duration) ≥ body_duration`; last track may truncate at a PHRASE boundary (never mid-bar). Seams = DJ beat+phrase match at 8/16-bar boundaries; time-stretch B to BPM_A via rubberband when |ΔBPM|≤8, else `afade` fallback flagged `BPM_MISMATCH`. Sidechain-duck music ~6 dB on recognized game events.
- **WHERE** `creative_suite/engine/music_stitcher.py` · `creative_suite/engine/sidechain.py` · `output/partNN_music_plan.json` (ship gate: every `duration == full_duration ± 0.1s` EXCEPT last, which must land on phrase boundary).
- **WHY** Mid-song cuts + looped tails rejected twice by user; `acrossfade` chains compound drift. Beat-matched DJ mix is what listeners expect.

#### P1-F (Music track catalog)
- **WHAT** Per-Part music files live in `creative_suite/engine/music/` and are auto-detected by filename (`partNN_intro_music.*`, `partNN_music.*`, `partNN_outro_music.*`). Series defaults: `pantheon_intro_music.mp3`, `pantheon_outro_music.mp3`.
- **WHERE** `creative_suite/engine/music/available_tracks.txt` is the human-readable catalog. `Config.*_music_path()` is the resolver.
- **WHY** One source of truth for "what music does Part N use" — no hardcoded paths in render code.

---

### 5. TITLE CARD

#### P1-Y (Title card — Quake aesthetic) [v2 + P1-T merged, 2026-04-18]
- **WHAT** Hero word (`QUAKE TRIBUTE`) uses OFL display font (candidate: Black Ops One / Russo One / Bungee Inline — pending user pick). Subtitle (`Part N`, `By Tr4sH`) uses Bebas Neue. Metallic red→gold fill, triple-layer 3D slab (black shadow + red inner glow + white core+border), 8%-opacity scanlines, 200ms chromatic aberration on reveal, scale-punch per char (1.15×→1.0× over 80ms), final one-frame white flash on last char of hero, 400ms red underline under credit. Renders over desaturated FL gameplay backdrop (`hue=s=0.25, brightness=-0.22, gblur=σ=4, vignette`). Duration 8s. NEVER over black.
- **WHERE** `creative_suite/engine/title_card.py::render_title_card` · `pick_intro_backdrop_fls` walks `T3→T2→T1` FL files · smoke-test grabs at t=0.3, 1.0, 2.0, 4.0, 6.5 into `docs/visual-record/YYYY-MM-DD/title_card_quake_smoke_partNN.png`.
- **WHY** v6 black-void readability fail + v8 Impact-kerning "TRI BUTE" split + user ask for "more effort" all resolved in one design. Smoke test per VIS-1 enforces visual sign-off before ship.

---

### 6. BEAT SYNC & GAME AUDIO

#### P1-Z (Action peak = recognized game event) [v2, 2026-04-18]
- **WHAT** Detect `player_death` / `rocket_impact` / `rail_fire` / `grenade_explode` / `LG_hit` / etc. in clip audio via template match against `creative_suite/engine/sound_templates/` (P1-DD). Peak = `argmax(weight × confidence)`. Grenade throw + 3s + explode = compound `grenade_direct`, peak at explosion. `player_death` wins over weapon events. Fallback: loudest onset + tag `RECOGNITION_FAILED` (all events < 0.4 confidence).
- **WHERE** `creative_suite/engine/audio_onsets.py::recognize_game_events` · logs `output/partNN_beats.json` (`[{clip, action_peak_t, event_type, confidence, target_downbeat, shift, tag}]`).
- **WHY** Loudest-amplitude onset mislabeled 30%+ of clips; recognized events are correct by construction.

#### P1-DD (QL sound template library)
- **WHAT** Every game-audio event the render pipeline cares about has a reference template extracted from Quake Live `pak00.pk3`. Scope: `sound/weapons/**`, `sound/player/**{death,gasp,pain,jump,land}*`, `sound/misc/**{telein,teleout,quad,powerup}*`, `sound/items/**{pickup,health,armor}*`, `sound/feedback/**`, `sound/world/**` (capped). All normalized to PCM WAV 48 kHz mono 16-bit.
- **WHERE** `creative_suite/engine/sound_templates/` + `manifest.json` (path → `event_type` with duration + RMS) · source: `C:\Program Files (x86)\Steam\steamapps\common\Quake Live\baseq3\pak00.pk3` (read-only per ENG-4).
- **WHY** Bridge between the render pipeline (action-peak recognition) and the demo parser (demo-audio event labeling). Any demo extractor that does NOT consume this library is doing the work twice.

#### P1-CC (Flow-driven cut placement) [v2, 2026-04-18]
- **WHAT** Flow planner walks music `sections[]` and picks clips by SECTION SHAPE, not tier: `build`→T3 atmospherics + slow FLs; `drop`→clip with `player_death` / `rocket_impact` nearest the drop timestamp; `break`→longest downtime clip; `outro`→tail frags. Tier is sort-key tiebreaker only (T1>T2>T3), never a hard gate.
- **WHERE** `creative_suite/engine/beat_sync.py::plan_flow_cuts_v2` · `creative_suite/engine/music_structure.py` produces `sections[]` via Beat This! + msaf + sub-200Hz RMS novelty.
- **WHY** "Perfect drop on a T3 action becomes T1 to the watcher." Tier-as-gate was too rigid — flow wins.

#### P1-S (Beat-sync governs seams, never clip duration)
- **WHAT** Beat-match lives on the JOIN between clips. It shifts WHEN a cut happens (±400 ms cap, absorbed by trim budget), never HOW LONG a clip plays. Clips play their full post-P1-L duration.
- **WHERE** `plan_beat_cuts()` / `plan_flow_cuts_v2()` return cut timestamps, not clip durations. Any code that shortens a clip below `full_length − head_trim − tail_trim` is broken.
- **WHY** Render pipeline clips are already-rendered AVIs — each clip IS the frag. Truncating to hit a beat defeats the whole pipeline.

#### P1-I (Golden rule — frag + effect + music align)
- **WHAT** Every chosen effect (slow-mo window, zoom, speed-up, hard cut) must match both frag type AND the music section. A T1 peak without matching musical weight is a miss. A slow-mo without a corresponding bass hit is a miss.
- **WHERE** Effect selection in `creative_suite/engine/effects.py` consumes `partNN_music_structure.json` + `partNN_beats.json` jointly.
- **WHY** User-stated north star: "the frag + effect + music is the golden rule of a good video."

---

### 7. MULTI-ANGLE

#### P1-A (Three-tier clip combining)
- **WHAT** Every Part combines ALL THREE tiers: `T1/PartN` + `T2/PartN` + `T3/PartN`. Tier semantics: **T1 = rarest / elite peak frags** (precious, save for climax moments, never filler); **T2 = main meal** (≥70% of screen time, backbone of the Part); **T3 = filler / cinematic** (atmospheric, intro/outro priority, FL slow-mo establishing shots).
- **WHERE** `scan_part_frags(part, cfg)` MUST scan all three tier directories. Interleave via `interleave_clips_by_tier()` (round-robin drain: T2/T1/T3/T2/T3/T1/T2…).
- **WHY** A Part assembled from T1 only is wrong. A Part using T1 as filler is also wrong. Tier semantics were inverted in the original spec — this is the corrected reading.

#### P1-B (Intro/outro clip pool)
- **WHAT** Lower-tier multi-angle subdirs (contain FL clips) are the intro/outro pool. Priority: T3 multi-angle → T2 multi-angle → T1 multi-angle (only if T2/T3 exhausted).
- **WHERE** `creative_suite/engine/title_card.py::pick_intro_backdrop_fls` · same resolver feeds the cinematic outro slot.
- **WHY** Lower-tier frags look good as cinematic intros because they're less intense, and the FL angles give more visual variety for establishing shots.

#### P1-K (Multi-angle — FP backbone + ONE FL slow-contrast) [2026-04-17]
- **WHAT** FP is the spine. At most ONE FL cuts in per frag, used as slow-motion contrast (`0.5×`). No 4-angle ping-pong. Window schedule: FP normal 0%→40%T · FL slow-mo 40%→65%T · FP normal 65%→100%T. Pick the FL with biggest angle delta from FP (side/top preferred).
- **WHERE** Clip-list grammar: `FP_path > FL_path` activates multi-angle on that frag (`>` = paired). Consecutive lines = sequential, not multi-angle.
- **WHY** User rejected swap-back-and-forth editing: "focus on keeping the main pov, use 1 FL for effect." FL is an *effect* on FP, not a standalone frag.

---

### 8. FULL-LENGTH CLIP CONTRACT

#### P1-P (No sub-clip fragments)
- **WHAT** A clip that enters a Part plays its full post-trim duration. "Filler" = full-length atmospheric establishing shot (typically T3), NOT a 0.5s cutaway. Quick-swap 0.5s fragments are banned.
- **WHERE** `build_body_chunks` emits one chunk per clip; no sub-trim for pacing. The micro-cut idea survives ONLY as a beat-locked FP↔FL stutter inside one multi-angle group (`FL_BEAT_STUTTER` flag, gated off by default).
- **WHY** User: "you did not understand what a filler was — we need to keep ALL the original clip length."

#### P1-Q (Speed effects) [v2, 2026-04-18; merges P1-EE]
- **WHAT** Effects apply to a WINDOW around recognized event peak (default ±0.8s), NEVER whole clip. Ramps in/out over 100 ms. Audio handling: **Option B default** (`atempo=2.0` counters `0.5×` video → natural-speed audio) for weapon events; **Option A** mute + crossfade edges for heavy-reverb events (`player_death`); **Option C** natural-speed audio at 60% volume for multi-kills. Requires P1-Z confidence ≥0.55 — no peak, no effect. `REPLAY_SPEED_CONTRAST` for short T1 clips (<3s post-trim) stays.
- **WHERE** `creative_suite/engine/effects.py` · `render_part_v6.py::build_body_chunks` · `partNN_overrides.txt` grammar: `slow=<rate>` means "event-localized", `slow_window=<seconds>` overrides the ±0.8s default.
- **WHY** Whole-clip slowmo stutters audio (user flagged); event-localized = velocity feel on the money shot only.

---

### 9. RENDER PIPELINE INTERNALS

#### P1-BB (Split video/audio graphs, PCM WAV, CFR)
- **WHAT** Body assembly uses TWO parallel ffmpeg graphs — video via `xfade` chain, audio via `concat + afade` pairs. Intermediate chunks encode audio as PCM WAV (never AAC). Force CFR on ingest: `-vsync cfr -r 60` before any filter. `amix=duration=first` with explicit `apad` on game; never `duration=longest`. After render: ffprobe audits per-minute v:0 vs a:0 drift into `output/partNN_sync_audit.json`. Ship gate: `max_drift_ms ≤ 40`.
- **WHERE** `render_part_v6.py::assemble_body_with_xfades` (video) + separate audio assembly · ffprobe audit step.
- **WHY** AAC priming delay (~1024 samples/chunk) + `xfade` implicit audio timeline together produced the 3:25 drift that survived per-chunk PTS reset. Split graphs + PCM WAV + CFR is the root-cause fix (ffmpeg issues #9248, #10229).

#### P1-J (Final render quality ceiling)
- **WHAT** File size does not matter; quality does. Target: CRF 15–17, preset `slow` / `veryslow`, x264 High Profile 1920×1080 60fps. Preview renders may use CRF 23 `veryfast` for speed; only final per-Part renders commit to the ceiling.
- **WHERE** `creative_suite/engine/config.py` final-render block · FT-6 benchmark feeds the exact knobs from Part 4 onward.
- **WHY** Originals stay full quality; YouTube re-encodes downstream. The WOW-factor renderer is the target, not the bytes saved.

#### P1-E (Render pipeline effect scope)
- **WHAT** What CAN be done in the render pipeline with existing AVIs: slow-motion (setpts + atempo), speed-up, zoom (crop+scale), basic tracking (scale+translate), camera-angle cuts between existing FP/FL AVIs, transitions (xfade, fade, hard cut). What requires the demo parser or engine assimilation track: rocket follow / bullet cam, new camera angles not in existing AVIs, demo re-recording, any WolfcamQL command-driven capture.
- **WHERE** `creative_suite/engine/effects.py` is the whitelist. Anything not listed there escalates.
- **WHY** Scope discipline: the render pipeline ships Parts 4–12 on existing AVIs. Don't rabbit-hole into re-capture.

---

### 10. INTRO

#### P1-C (PANTHEON intro prepend)
- **WHAT** Every Part gets `IntroPart2.mp4` prepended. Never skip.
- **WHERE** Path: `G:\QUAKE_LEGACY\FRAGMOVIE VIDEOS\IntroPart2.mp4` (1920×1080 30fps H264). Only the first 5s used (see P1-N).
- **WHY** Series identity — the PANTHEON logo opens every entry.

#### P1-N (Intro sequence) [v3, 2026-04-18; merges P1-T + P1-X]
- **WHAT** Every Part opens with `[PANTHEON 5s] + [Title card 8s] + [Content]`. PANTHEON = `IntroPart2.mp4` first 5s with its own audio (music-silent per P1-G). Title card = P1-Y v2 (Quake-style over FL backdrop). Pre-content offset = 13s. Hard cut into first clip (no dramatic fade per P1-H).
- **WHERE** `cfg.intro_clip_duration=5.0` · `render_part_v6.py::build_intro` · `creative_suite/engine/title_card.py` · annotation tool (creative_suite Track 2) reads offset from config, never hardcodes 15.
- **WHY** Series identity is structural, not polish. 5s drops 2s of dead PANTHEON hold; title card sits over live gameplay, never over black.

---

*Archive footer:* full text of all superseded P1-* versions (P1-G v3, P1-H v3, P1-L v2/v3, P1-Y v1, P1-Z v1, P1-AA v1, P1-CC v1, P1-G legacy, P1-L Part-4-2026-04-17, P1-H "NO TRANSITIONS") lives in `docs/_archive/claude-md-superseded-2026-04-19.md`. Grep by rule ID to retrieve.

## HARD RULES — Demo Parser & Highlight Criteria

### Rule P3-A: Own Highlight Criteria Before Demo Extraction
**Before running the AI scoring model, the user defines the highlight ruleset.**
- Do NOT auto-extract frags and call them "highlights"
- First session: user + Claude review sample frag types together
- Together define: which airshots qualify (minimum air time? weapon?), which multi-kills count
- Only after user-approved criteria does the parser scan all demos
- This is Gate R-0 (before any demo extraction)

### Rule P3-B: WolfcamQL + WolfWhisperer Command Inventory
**ALL console commands and cvars must be inventoried before automation.**
- Source: `engine/engines/wolfcamql-local-src/code/cgame/wolfcam_consolecmds.c`
- Also: `engine/engines/wolfcamql-src/code/cgame/wolfcam_consolecmds.c`
- WolfWhisperer.exe: reverse engineer with Ghidra to find IPC commands
- Document in: `docs/reference/wolfcam-commands.md`
- This is required before writing any WolfcamQL automation

## HARD RULES — Cinema Suite

### Rule CS-1: Single-Worker Job Queue, Never Parallel Renders
**The render/preview job queue is depth=1. Second submit → HTTP 409 busy.**
- `creative_suite/api/_render_worker.py` `JobQueue` enforces `RuntimeError` when a job is active.
- The router returns 409 on `RuntimeError`, never queues.
- If the user clicks REBUILD while a job runs, they get the busy response — they do not stack.
- Applies to both `/rebuild` and `/preview` endpoints (shared queue).

### Rule CS-2: Mock Env Vars for CI / Offline Dev
**Three env vars let the suite run without wolfcamql.exe / ffmpeg.exe / engine binary:**
- `CS_REBUILD_MOCK=1` — `rebuild_part()` emits fake SSE events instead of spawning `render_part_v6.py`
- `CS_PREVIEW_MOCK=1` — `run_preview_tier_a()` writes an 8-byte mp4 stub instead of running wolfcam+ffmpeg
- `CS_ENGINE_MOCK=1` — `EngineSupervisor._grab_once()` returns `b"\xff\xd8\xff\xe0mockjpeg"` sentinel instead of BitBlt grabbing
- All three are tested in `creative_suite/tests/`. Real-engine paths remain the default (no env var set).

### Rule CS-3: Git Sub-Repo is Auto-Managed, User Never Commits There
**`output/.git` is a separate git repo. `_git_flow.py` owns it.**
- Tags: `part{NN}/{tag}` (e.g. `part04/v10.5-opener`)
- Refname regex validation: `r"^(?![.\-])[\w.\-]+$"`, no `..` — prevents DB row / missing-tag divergence
- Never push this repo anywhere. It's a local-only version history for `flow_plan.json`.
- User must NOT `git init` inside `output/` manually — the suite bootstraps it.

### Rule CS-4: Subprocess Cancellation Must Terminate, Not Orphan
**Every `await proc.wait()` on a GUI subprocess (wolfcam, ffmpeg) must be wrapped in try/except with terminate→kill cascade.**
- Pattern: `proc.terminate() → asyncio.wait_for(proc.wait(), timeout=3) → proc.kill() → await proc.wait()`
- Catches `asyncio.CancelledError` AND `BaseException` (server shutdown from KeyboardInterrupt).
- Applies to `_preview_job.py` (wolfcam + ffmpeg) and `engine/supervisor.py`.
- Wolfcam is a GUI process — orphaning it hangs the desktop and holds demo-file locks.

### Rule CS-5: Cfg Injection Validator on Every User-Influenced String
**`write_gamestart_cfg` and `write_preview_cfg` reject `;` and `\n` in `demo_name`, `seek_clock`, `quit_at`.**
- Because the cfg oneliner is `seekclock {seek}; video avi name :{demo}; at {quit} quit` — one stray `;` in `demo_name` opens a cvar-exec injection.
- Any NEW user-string → cfg flow must use the same guard.

### Rule CS-6: Render Hook (§11.1) is Bounds-Checked and Guarded
**`render_part_v6.py` §11.1 hook reads `beat_snapped_offsets[]` from flow_plan.json and overrides `body_seam_offsets[i]`.**
- Negative `seam_idx` filtered out in the comprehension.
- Applied count logged vs requested count.
- Empty override list = byte-identical render to pre-hook behavior.
- DO NOT extend this hook to mutate clip durations — Rule P1-S bans that. Seam offsets only.

## HARD RULES — /studio UI

### Rule UI-1: No innerHTML with Untrusted Data
All dynamic content inserted into the DOM uses `textContent` or an `esc()` helper — never raw innerHTML with untrusted track titles, clip names, or file paths. DOM nodes are built with createElement/replaceChildren.

### Rule UI-2: Shared Store is the Single Source of Truth
All panels (timeline, preview, audio, inspector, music library) subscribe to studio-store.js. No panel holds local state that could drift from the store. Mutations go through `set(key, value)`.

### Rule UI-3: WebCodecs Frame Cache is Bounded
The frame cache in studio-preview.js maps timestamp_us → ImageBitmap. Max 500 frames cached. Older frames evicted on overflow. Do not grow unbounded.

## HARD RULES — Engine Assimilation

### Rule ENG-1: Steam Paks are Source of Truth
`C:\Program Files (x86)\Steam\steamapps\common\Quake Live\baseq3\pak00.pk3` is the authoritative asset source. Wolfcam extracts are reference only. Never modify Steam pak files.

### Rule ENG-2: Style Pack Naming
Style pack pk3s MUST be named `zzz_*.pk3` for alphabetical override of `pak00.pk3`.

### Rule ENG-3: Pack Testing
Pack testing requires `+set sv_pure 0`.

### Rule ENG-4: Steam Paks Read-Only
Steam pak files are read-only. Never modify.

### Rule ENG-5: No Duplication in quake_legacy_engine
The unified quake_legacy_engine takes the best from all source trees, zero duplication. Protocol-73 from wolfcamql, camera scripting from q3mme, capture from ioquake3 cl_avi.c.

## npm Security Policy

Every npm package install requires ALL of:
1. License in {MIT, BSD-2, BSD-3, Apache-2.0, ISC} — reject AGPL, custom, unknown
2. `npm audit` — zero high/critical
3. Snyk advisory DB — clean
4. Pinned exact version (no `^` or `~`)
5. GitHub source with >1k stars OR >3 years maintained
6. No network calls at build time

**History:** Nearly had a vercel + litellm supply chain incident. Non-negotiable.

### Pre-Approved AGPL Exception

**`@theatre/browser-bundles@0.7.2`** — AGPL-3.0 (Studio UI portion)  
Pre-approved for local personal use in the Cinema Suite editor.  
Before any public release of this codebase, replace Theatre Studio with an Apache-2.0 alternative or remove the Studio bundle entirely. `@theatre/core` alone is Apache-2.0.

## Demo Corpus

| Corpus | Path | Count | Size |
|---|---|---|---|
| Primary | `demos/` | 6,465 `.dm_73` | 13.19 GB |
| WolfcamQL staging | `engine/wolfcam/WolfcamQL/wolfcam-ql/demos/` | 948 | ~2 GB |

**11 anonymized players** across the corpus.

## Frag Detection in .dm_73

```python
entity.event & ~0x300 == EV_OBITUARY   # (0x300 masks toggle bits)
killer = entity.otherEntityNum2          # client slot 0-63
victim = entity.otherEntityNum           # client slot 0-63
weapon = entity.eventParm                # MOD_* constant
time   = snapshot.server_time            # milliseconds
```

## WolfcamQL Automation Pattern

```
Write gamestart.cfg:
  seekclock 8:52; video avi name :demoname; at 9:05 quit
Launch: wolfcamql.exe +set fs_homepath <out_dir> +exec cap.cfg +demo demo.dm_73
```

## Human Review Gates (NEVER skip)

1. **Gate R-0:** Define highlight criteria WITH user before ANY demo extraction
2. **Gate R-1:** Review clip lists before rendering (`creative_suite/engine/clip_lists/partXX.txt`)
3. **Gate R-2:** Watch 30s preview before full render
4. **Gate R-3:** Watch full Part render before moving to next
5. **Gate P-1:** Review parser output on 10 sample demos before full parse
6. **Gate P-2:** Rate frags in dashboard before batch WolfcamQL render
7. **Gate P-3:** Review 10 rendered clips before full batch

## Visual Documentation (ALL outputs)

### Rule VIS-1: Always Capture Visual Records
**Every significant output must be screenshotted and documented.**

- After any render: screenshot or frame-grab the output
- After any grade change: before/after color comparison image
- After any graphify run: screenshot the interactive HTML graph in browser
- After Obsidian updates: screenshot vault dashboard and graph view
- After ComfyUI processing: screenshot input vs output side-by-side
- After any pipeline run: capture terminal output visually if impressive

**Save to:** `G:/QUAKE_LEGACY/docs/visual-record/YYYY-MM-DD/`
**Naming:** `before_[description].png`, `after_[description].png`, `[feature]_screenshot.png`
**Tools:** Use Playwright MCP or Claude in Chrome MCP to capture browser content

This is non-negotiable. Screenshots and before/after comparisons are deliverables, not optional.

## When Starting a Session

1. Read `docs/specs/2026-04-16-quake-legacy-design.md` for full architecture
2. Check `creative_suite/database/` for cross-domain learnings
3. Check current plans in `docs/superpowers/plans/`
4. Review `creative_suite/engine/music/available_tracks.txt` for music status
5. Never run batch operations without human confirming at review gate
6. Never commit personal data

## Funded Research Tracks

| Track | Description | Status | Location |
|---|---|---|---|
| FT-1 | C++17 dm73 parser | Scaffold done | `engine/parser/` |
| FT-2 | Highlight criteria v2 | Locked | `docs/reference/highlight-criteria.md` |
| FT-3 | 3D intro lab | Research | `creative_suite/comfy/assets/intro_lab/` |
| FT-4 | Ghidra RE all executables | Partially done | `engine/ghidra/` |
| FT-5 | Nickname dictionary + notable-player regex | Planned | `creative_suite/database/frags.db` |
| FT-6 | FFmpeg encoder benchmark → quality ceiling | Pending | feeds `creative_suite/engine/config.py` |
| FT-7 | Game audio mix level A/B test (0.55 vs 0.75) | Pending | `Config.game_audio_volume` |

### FT-1 Detail: Custom C++ `.dm_73` parser
- Lives in `engine/parser/` — C++17 + CMake, static lib + `dm73dump` CLI → JSON Lines
- Vendors `msg.c`, `huffman.c`, `common.c`, `q_shared.h`, `bg_public.h` from wolfcamql-src under GPL-2.0 with preserved headers
- Authoritative format reference: `docs/reference/dm73-format-deep-dive.md` (1,337 lines)
- Validated against `UDT_json.exe` golden output on 3 hand-picked demos before trust
- Spirit: *"WE ARE QUAKE WE BREATH QUAKE WE KNOW IF WE CHANGE THIS BIT IT WILL MAKE THE RAIL PINK"* — full control, no black boxes
- Parser fixture env var: `DM73_FIXTURE_DIR` (overrides path in `engine/parser/tests/fixtures.h`)

### FT-2 Detail: Highlight Criteria v2 (locked)
- Authoritative: `docs/reference/highlight-criteria.md` (supersedes v1)
- Every frag enters the corpus (no minimum threshold); tiering is for *ordering*, not filtering
- Weapon weights: Rocket 2.0, Rail 1.5, Grenade direct 2.5, LG accuracy-banded (40/50/56)
- Multi-kill window = full CA round; airshot = any weapon, 200ms min air time
- LMS is a separate tag with audio-cue integration opportunity
- All weapon-combo sequences ≤ 2s extracted for pattern-recognition ML

### FT-3 Detail: 3D Intro Lab
- Parallel research track, not on critical path for Parts 4-12
- Goal: AI-assisted 3D intros using Q3 BSP maps + MD3 models (Xaero/Visor priority) + ComfyUI/AnimateDiff
- Also carries the Parts 1-3 morph-remaster experiment (Annihilation-style game-to-game morphs)

### FT-4 Detail: Ghidra blockers (user actions needed)
- Install Ghidra 11.3 + JDK 21 (user machine)
- Extract `G:\QUAKE_LEGACY\WOLF WHISPERER\Wolf Whisperer.rar` (contains main binary)
- Decision: build or drop UDT_json / q3mme as RE targets (scope call)
- Already done without Ghidra: `qagamex86.dll` has DWARF + STABS debug info (not stripped), 34-entry MOD_* enum seed, 103-entry EV_* enum seed, WolfcamQL capture-cvar seed

### FT-5 Detail: Nickname dictionary + notable-player regex
- User's historical nicknames (Tr4sH + variants) and famous opponents become regex tags
- Notable-victim frags get auto-flagged as Part-opening / climax candidates
- All alias strings stay LOCAL — public exports use opaque canonical_id hashes only

## Public CLI Vision

Once the system works for this project, it becomes a public CLI:
`pip install quake-legacy` → give it demos → get a fragmovie.

Document EVERYTHING as we go. All RE findings, all binary format work, all camera math.
The community will build on this. The Q3 engine is open source — this is the gift back.

## ComfyUI Photoreal Pipeline (Phase 5)

### HARD RULES — never violate these

#### Rule PH5-1: Correct pipeline is Upscale + ControlNet-Tile (NOT plain img2img)
- **WRONG**: plain SDXL img2img (destroys UV texture layout at any denoise > 0.10)
- **CORRECT**: `4x-UltraSharp` upscale → `dreamshaper_8` SD1.5 + `control_v11f1e_sd15_tile` ControlNet-Tile
- Workflow files: `creative_suite/comfy/workflows/upscale_only.json` + `tile_controlnet_sd15.json`
- `RealVisXL_V5.0_fp16.safetensors` is SDXL — **incompatible with SD1.5 Tile ControlNet**. Do NOT pair them.

#### Rule PH5-2: Models on disk (verified 2026-04-21)
| Model | Path | Purpose |
|---|---|---|
| `RealVisXL_V5.0_fp16.safetensors` | `quake_legacy checkpoints/` | SDXL plain img2img only |
| `dreamshaper_8.safetensors` | `ComfyUI/models/checkpoints/` | SD1.5 — pairs with Tile ControlNet |
| `control_v11f1e_sd15_tile.pth` | `ComfyUI/models/controlnet/` | SD1.5 Tile ControlNet |
| `4x-UltraSharp.pth` | `ComfyUI/models/upscale_models/` | CNN upscaler (no diffusion) |

#### Rule PH5-3: Scope is 107 weapon/HUD textures, NOT all pak00
- Phase 5 target: `creative_suite/comfy/photoreal/assets/phase5_png/` (107 files)
- Full pak00 (6,190 files) is for archival extraction only — NOT for bulk img2img
- UV body sheets, icons, sprites, gfx tiles: do NOT run diffusion on these (content destroyed)
- Face textures (`*_h.png`), mapobjects, wall textures, weapon surfaces: diffusion-viable

#### Rule PH5-4: E2E test before ANY batch run
- Script: `creative_suite/comfy/photoreal_e2e_test.py`
- Output: `creative_suite/comfy/photoreal/e2e/index.html`
- Must show before/after for all 11 categories. User approves per-category pipeline before batch starts.

#### Rule PH5-5: ComfyUI launch requires WorkingDirectory
- `Start-Process "E:\PersonalAI\run_comfyui_api.bat" -WorkingDirectory "E:\PersonalAI"`
- Without `-WorkingDirectory`, `cd ComfyUI` in the bat fails silently and ComfyUI never starts.

#### Rule PH5-6: Batch script is resumable — log must work
- Use `python -u script.py > run.log 2>&1` (CMD direct redirect, NOT PowerShell Tee-Object)
- `Tee-Object` piped from a bat child process produces empty log files
- Launcher: `creative_suite/comfy/photoreal/launch.bat`

#### Rule PH5-7: E2E-validated category routing (2026-04-21)
- **SURFACE** (upscale_only + all tile_d* pipelines): `players`, `weapons2`, `textures`, `phase5`
- **FX / shape-critical** (upscale_only ONLY — diffusion destroys these): `weaphits`, `gfx`, `icons`, `ui`, `wolfcam_hud`, `powerups`, `mapobjects`, `sprites`
- Auto-detect unknown: black-pixel ratio >70% → FX, else SURFACE
- UV sheets: tile_d35 max — d50+ destroys UV layout
- Face textures (`*_h.png`): tile_d35 sweet spot, d50 acceptable
- Wall textures: upscale_only wins (CNN alone is photorealistic on Quake geometry)

#### Rule PH5-8: Multi-pipeline output structure
- All outputs live in `photoreal/pipelines/{pipeline_name}/{rel_path}.png`
- All renders logged in `photoreal/assets.db` (SQLite, tables: assets + renders)
- Pipeline names: `upscale_only`, `tile_d35`, `tile_d50`, `tile_d60`, `tile_d70`, `tile_d80`
- d60/d70/d80 are experimental — FX artifacts expected, kept for UI experimentation
- CLI: `python -u creative_suite/comfy/full_overnight.py --categories players --pipelines tile_d35 tile_d50`

#### Rule PH5-9: Style LoRA suite
- Base model: `juggernautXL_ragnarokBy.safetensors` (SDXL)
- Workflow: `creative_suite/comfy/workflows/tile_sdxl_lora.json` (LoraLoader between checkpoint and KSampler)
- Manifest: `creative_suite/comfy/loras/manifest.json` — 6 styles documented
- Downloaded: `NeonifyV2-4Extreme.safetensors` (cel shade, 1.8GB), `sdxl_photorealistic_slider_v1-0.safetensors` (24MB)
- Needs API token: `Photov3-000008.safetensors` (PhotorealTouch v3, 223MB) — `python download_loras.py --token YOUR_KEY`
- LoRA strength sweet spot: 0.5–0.8 with tile ControlNet at denoise=0.35–0.45
- Retro Quake LoRA: needs custom training on pak00 corpus (TRAIN_NEEDED in manifest)

#### Rule PH5-10: ComfyUI node prerequisites
- `TTPlanet_TileGF_Preprocessor` is MANDATORY for tile workflows — without it ControlNet hallucinates at any denoise > 0.30
- Source: ComfyUI-TTPLanet_Tile_Preprocessor (git clone into ComfyUI/custom_nodes/)
- Verification script: `creative_suite/comfy/verify_comfyui.py` — run before any batch; checks nodes + models + workflows + scripts
- After adding new LoRA files: ComfyUI must be restarted to scan models directory

## Cross-Domain Learning Store

All work writes learnings to: `G:\QUAKE_LEGACY\creative_suite\database\knowledge.db`
