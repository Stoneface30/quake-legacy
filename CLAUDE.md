# QUAKE LEGACY — Project Instructions for Claude

This file is loaded automatically every Claude Code session for this project.

## What This Project Is

AI-powered Quake Live fragmovie production system. 3 active phases + Phase 4 (public tool).
10+ years of `.dm_73` Quake Live demo recordings → automated fragmovie pipeline.

**GitHub:** https://github.com/Stoneface30/quake-legacy (PUBLIC repo)
**Local root:** G:\QUAKE_LEGACY
**User role:** Creative director, quality judge — approves everything before batch runs.
**Editing brand:** PANTHEON (temple logo, grey/silver style)

## CRITICAL: Public Repo Rules

- **NEVER commit** player names, nicknames, personal identifiers, Steam IDs
- **NEVER commit** .dm_73, .avi, .mp4, .db, .env files
- Demo player names are anonymized in all code and docs
- All gameplay analysis is statistical — no player profiles

## Source Material Locations

```
G:\QUAKE_LEGACY\
  QUAKE VIDEO\T1\Part1-12\         ← Top tier AVI clips (backbone of each Part)
  QUAKE VIDEO\T2\Part1-12\         ← Second tier AVI clips (fill + intro/outro candidates)
  QUAKE VIDEO\T3\Part1-12\         ← Lower tier AVI clips (intro/outro priority)
  WOLF WHISPERER\                  ← WolfWhisperer.exe + WolfcamQL + Python scripts
  FRAGMOVIE VIDEOS\                ← 3 finished tribute videos + PANTHEON intro
    IntroPart2.mp4                 ← PANTHEON intro (25.77s total, USE FIRST 7s ONLY) — prepend to ALL parts
    Clan Arena Tribute 1/2/3.mp4   ← Reference quality finished videos
  tools\                           ← all downloaded dependencies
  phase1\                          ← FFmpeg assembly pipeline
  phase2\                          ← demo parser + batch renderer
  phase3\                          ← AI cinematography engine
  database\                        ← SQLite frag database schema
  docs\                            ← design specs, research, plans
```

## HARD RULES — Phase 1 (domain-grouped, live versions only)

*Superseded versions archived at `docs/_archive/claude-md-superseded-2026-04-19.md` — grep by rule ID.*

---

### 1. AUDIO

#### P1-G (Music mix) [v5, 2026-04-18]
- **WHAT** Music volume 0.20. PANTHEON = own audio only; music fades in 0→0.20 over 1.5s at title-card start; body = game 1.0 + music 0.20 sidechain-ducked. Final render MUST pass ebur128 gate: music ≤ −12 LU below game peak, else render is `FAILED_LEVEL_GATE` and not shipped.
- **WHERE** `cfg.music_volume=0.20`, `cfg.music_fadein_s=1.5` · `render_part_v6.py::final_render` audio graph (3-segment concat: PANTHEON+own-audio | title+music-fadein | body+game+ducked-music) · `phase1/audio_levels.py::measure_music_vs_game` · `output/partNN_levels.json`
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
- **WHERE** `Config.intro_music_path(part)` / `music_path(part)` / `outro_music_path(part)` · `phase1/music_stitcher.py` · per-Part overrides `partNN_intro_music.*` / `partNN_outro_music.*` resolved first.
- **WHY** Single-track renders rejected by user; mid-song swaps rejected twice; silence gaps rejected once. Three-track + continuous = stable contract.

#### P1-AA (Music stitcher — video is truth) [v2, 2026-04-18]
- **WHAT** Video body length rules. Queue N full tracks until `sum(duration) ≥ body_duration`; last track may truncate at a PHRASE boundary (never mid-bar). Seams = DJ beat+phrase match at 8/16-bar boundaries; time-stretch B to BPM_A via rubberband when |ΔBPM|≤8, else `afade` fallback flagged `BPM_MISMATCH`. Sidechain-duck music ~6 dB on recognized game events.
- **WHERE** `phase1/music_stitcher.py` · `phase1/sidechain.py` · `output/partNN_music_plan.json` (ship gate: every `duration == full_duration ± 0.1s` EXCEPT last, which must land on phrase boundary).
- **WHY** Mid-song cuts + looped tails rejected twice by user; `acrossfade` chains compound drift. Beat-matched DJ mix is what listeners expect.

#### P1-F (Music track catalog)
- **WHAT** Per-Part music files live in `phase1/music/` and are auto-detected by filename (`partNN_intro_music.*`, `partNN_music.*`, `partNN_outro_music.*`). Series defaults: `pantheon_intro_music.mp3`, `pantheon_outro_music.mp3`.
- **WHERE** `phase1/music/available_tracks.txt` is the human-readable catalog. `Config.*_music_path()` is the resolver.
- **WHY** One source of truth for "what music does Part N use" — no hardcoded paths in render code.

---

### 5. TITLE CARD

#### P1-Y (Title card — Quake aesthetic) [v2 + P1-T merged, 2026-04-18]
- **WHAT** Hero word (`QUAKE TRIBUTE`) uses OFL display font (candidate: Black Ops One / Russo One / Bungee Inline — pending user pick). Subtitle (`Part N`, `By Tr4sH`) uses Bebas Neue. Metallic red→gold fill, triple-layer 3D slab (black shadow + red inner glow + white core+border), 8%-opacity scanlines, 200ms chromatic aberration on reveal, scale-punch per char (1.15×→1.0× over 80ms), final one-frame white flash on last char of hero, 400ms red underline under credit. Renders over desaturated FL gameplay backdrop (`hue=s=0.25, brightness=-0.22, gblur=σ=4, vignette`). Duration 8s. NEVER over black.
- **WHERE** `phase1/title_card.py::render_title_card` · `pick_intro_backdrop_fls` walks `T3→T2→T1` FL files · smoke-test grabs at t=0.3, 1.0, 2.0, 4.0, 6.5 into `docs/visual-record/YYYY-MM-DD/title_card_quake_smoke_partNN.png`.
- **WHY** v6 black-void readability fail + v8 Impact-kerning "TRI BUTE" split + user ask for "more effort" all resolved in one design. Smoke test per VIS-1 enforces visual sign-off before ship.

---

### 6. BEAT SYNC & GAME AUDIO

#### P1-Z (Action peak = recognized game event) [v2, 2026-04-18]
- **WHAT** Detect `player_death` / `rocket_impact` / `rail_fire` / `grenade_explode` / `LG_hit` / etc. in clip audio via template match against `phase1/sound_templates/` (P1-DD). Peak = `argmax(weight × confidence)`. Grenade throw + 3s + explode = compound `grenade_direct`, peak at explosion. `player_death` wins over weapon events. Fallback: loudest onset + tag `RECOGNITION_FAILED` (all events < 0.4 confidence).
- **WHERE** `phase1/audio_onsets.py::recognize_game_events` · logs `output/partNN_beats.json` (`[{clip, action_peak_t, event_type, confidence, target_downbeat, shift, tag}]`).
- **WHY** Loudest-amplitude onset mislabeled 30%+ of clips; recognized events are correct by construction.

#### P1-DD (QL sound template library)
- **WHAT** Every game-audio event Phase 1 cares about has a reference template extracted from Quake Live `pak00.pk3`. Scope: `sound/weapons/**`, `sound/player/**{death,gasp,pain,jump,land}*`, `sound/misc/**{telein,teleout,quad,powerup}*`, `sound/items/**{pickup,health,armor}*`, `sound/feedback/**`, `sound/world/**` (capped). All normalized to PCM WAV 48 kHz mono 16-bit.
- **WHERE** `phase1/sound_templates/` + `manifest.json` (path → `event_type` with duration + RMS) · source: `C:\Program Files (x86)\Steam\steamapps\common\Quake Live\baseq3\pak00.pk3` (read-only per ENG-4).
- **WHY** Bridge between Phase 1 (action-peak recognition) and Phase 2 (demo-audio event labeling). Any Phase 2 demo extractor that does NOT consume this library is doing the work twice.

#### P1-CC (Flow-driven cut placement) [v2, 2026-04-18]
- **WHAT** Flow planner walks music `sections[]` and picks clips by SECTION SHAPE, not tier: `build`→T3 atmospherics + slow FLs; `drop`→clip with `player_death` / `rocket_impact` nearest the drop timestamp; `break`→longest downtime clip; `outro`→tail frags. Tier is sort-key tiebreaker only (T1>T2>T3), never a hard gate.
- **WHERE** `phase1/beat_sync.py::plan_flow_cuts_v2` · `phase1/music_structure.py` produces `sections[]` via Beat This! + msaf + sub-200Hz RMS novelty.
- **WHY** "Perfect drop on a T3 action becomes T1 to the watcher." Tier-as-gate was too rigid — flow wins.

#### P1-S (Beat-sync governs seams, never clip duration)
- **WHAT** Beat-match lives on the JOIN between clips. It shifts WHEN a cut happens (±400 ms cap, absorbed by trim budget), never HOW LONG a clip plays. Clips play their full post-P1-L duration.
- **WHERE** `plan_beat_cuts()` / `plan_flow_cuts_v2()` return cut timestamps, not clip durations. Any code that shortens a clip below `full_length − head_trim − tail_trim` is broken.
- **WHY** Phase 1 clips are already-rendered AVIs — each clip IS the frag. Truncating to hit a beat defeats the whole pipeline.

#### P1-I (Golden rule — frag + effect + music align)
- **WHAT** Every chosen effect (slow-mo window, zoom, speed-up, hard cut) must match both frag type AND the music section. A T1 peak without matching musical weight is a miss. A slow-mo without a corresponding bass hit is a miss.
- **WHERE** Effect selection in `phase1/effects.py` consumes `partNN_music_structure.json` + `partNN_beats.json` jointly.
- **WHY** User-stated north star: "the frag + effect + music is the golden rule of a good video."

---

### 7. MULTI-ANGLE

#### P1-A (Three-tier clip combining)
- **WHAT** Every Part combines ALL THREE tiers: `T1/PartN` + `T2/PartN` + `T3/PartN`. Tier semantics: **T1 = rarest / elite peak frags** (precious, save for climax moments, never filler); **T2 = main meal** (≥70% of screen time, backbone of the Part); **T3 = filler / cinematic** (atmospheric, intro/outro priority, FL slow-mo establishing shots).
- **WHERE** `scan_part_frags(part, cfg)` MUST scan all three tier directories. Interleave via `interleave_clips_by_tier()` (round-robin drain: T2/T1/T3/T2/T3/T1/T2…).
- **WHY** A Part assembled from T1 only is wrong. A Part using T1 as filler is also wrong. Tier semantics were inverted in the original spec — this is the corrected reading.

#### P1-B (Intro/outro clip pool)
- **WHAT** Lower-tier multi-angle subdirs (contain FL clips) are the intro/outro pool. Priority: T3 multi-angle → T2 multi-angle → T1 multi-angle (only if T2/T3 exhausted).
- **WHERE** `phase1/title_card.py::pick_intro_backdrop_fls` · same resolver feeds the cinematic outro slot.
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
- **WHERE** `phase1/effects.py` · `render_part_v6.py::build_body_chunks` · `partNN_overrides.txt` grammar: `slow=<rate>` means "event-localized", `slow_window=<seconds>` overrides the ±0.8s default.
- **WHY** Whole-clip slowmo stutters audio (user flagged); event-localized = velocity feel on the money shot only.

---

### 9. RENDER PIPELINE

#### P1-BB (Split video/audio graphs, PCM WAV, CFR)
- **WHAT** Body assembly uses TWO parallel ffmpeg graphs — video via `xfade` chain, audio via `concat + afade` pairs. Intermediate chunks encode audio as PCM WAV (never AAC). Force CFR on ingest: `-vsync cfr -r 60` before any filter. `amix=duration=first` with explicit `apad` on game; never `duration=longest`. After render: ffprobe audits per-minute v:0 vs a:0 drift into `output/partNN_sync_audit.json`. Ship gate: `max_drift_ms ≤ 40`.
- **WHERE** `render_part_v6.py::assemble_body_with_xfades` (video) + separate audio assembly · ffprobe audit step.
- **WHY** AAC priming delay (~1024 samples/chunk) + `xfade` implicit audio timeline together produced the 3:25 drift that survived per-chunk PTS reset. Split graphs + PCM WAV + CFR is the root-cause fix (ffmpeg issues #9248, #10229).

#### P1-J (Final render quality ceiling)
- **WHAT** File size does not matter; quality does. Target: CRF 15–17, preset `slow` / `veryslow`, x264 High Profile 1920×1080 60fps. Preview renders may use CRF 23 `veryfast` for speed; only final per-Part renders commit to the ceiling.
- **WHERE** `phase1/config.py` final-render block · FT-6 benchmark feeds the exact knobs from Part 4 onward.
- **WHY** Originals stay full quality; YouTube re-encodes downstream. The WOW-factor renderer is the target, not the bytes saved.

#### P1-E (Phase 1 effect scope)
- **WHAT** What CAN be done in Phase 1 with existing AVIs: slow-motion (setpts + atempo), speed-up, zoom (crop+scale), basic tracking (scale+translate), camera-angle cuts between existing FP/FL AVIs, transitions (xfade, fade, hard cut). What requires Phase 2/3/4: rocket follow / bullet cam, new camera angles not in existing AVIs, demo re-recording, any WolfcamQL command-driven capture.
- **WHERE** `phase1/effects.py` is the whitelist. Anything not listed there escalates.
- **WHY** Scope discipline: Phase 1 ships Parts 4–12 on existing AVIs. Don't rabbit-hole into re-capture.

---

### 10. INTRO

#### P1-C (PANTHEON intro prepend)
- **WHAT** Every Part gets `IntroPart2.mp4` prepended. Never skip.
- **WHERE** Path: `G:\QUAKE_LEGACY\FRAGMOVIE VIDEOS\IntroPart2.mp4` (1920×1080 30fps H264). Only the first 5s used (see P1-N).
- **WHY** Series identity — the PANTHEON logo opens every entry. Future: generate alternate PANTHEON intros in Phase 4.

#### P1-N (Intro sequence) [v3, 2026-04-18; merges P1-T + P1-X]
- **WHAT** Every Part opens with `[PANTHEON 5s] + [Title card 8s] + [Content]`. PANTHEON = `IntroPart2.mp4` first 5s with its own audio (music-silent per P1-G). Title card = P1-Y v2 (Quake-style over FL backdrop). Pre-content offset = 13s. Hard cut into first clip (no dramatic fade per P1-H).
- **WHERE** `cfg.intro_clip_duration=5.0` · `render_part_v6.py::build_intro` · `title_card.py` · annotation tool (creative_suite Track 2) reads offset from config, never hardcodes 15.
- **WHY** Series identity is structural, not polish. 5s drops 2s of dead PANTHEON hold; title card sits over live gameplay, never over black.

---

*Archive footer:* full text of all superseded P1-* versions (P1-G v3, P1-H v3, P1-L v2/v3, P1-Y v1, P1-Z v1, P1-AA v1, P1-CC v1, P1-G legacy, P1-L Part-4-2026-04-17, P1-H "NO TRANSITIONS") lives in `docs/_archive/claude-md-superseded-2026-04-19.md`. Grep by rule ID to retrieve.

## HARD RULES — Phase 3 (from user review)

### Rule P3-A: Own Highlight Criteria Before Demo Extraction
**Before running the AI scoring model, the user defines the highlight ruleset.**
- Do NOT auto-extract frags and call them "highlights"
- First session: user + Claude review sample frag types together
- Together define: which airshots qualify (minimum air time? weapon?), which multi-kills count
- Only after user-approved criteria does Phase 2 parse all 2,277 demos
- This is Gate P3-0 (before any demo extraction)

### Rule P3-B: WolfcamQL + WolfWhisperer Command Inventory
**ALL console commands and cvars must be inventoried before Phase 2/3 automation.**
- Source: `tools/quake-source/wolfcamql-local-src/code/cgame/wolfcam_consolecmds.c`
- Also: `tools/quake-source/wolfcamql-src/code/cgame/wolfcam_consolecmds.c`
- WolfWhisperer.exe: reverse engineer with Ghidra to find IPC commands
- Document in: `docs/reference/wolfcam-commands.md`
- This is required before writing any WolfcamQL automation in Phase 2

## Project Structure — TWO SPLITS (user ruling 2026-04-17)

**SPLIT 1 — Video Pipeline** (current focus, close first)
- Finish Parts 4-12 as ship-quality fragmovies via the existing Phase 1 pipeline
- User-action checklist: `SPLIT1_USER_CHECKLIST.md` (root of repo, keep it visible)
- Nothing else gets built until Split 1 closes (Parts 4-12 approved + archived)

**SPLIT 2 — TR4SH QUAKE** (after Split 1)
- Single engine + command center + agent fusion
- Supersedes the separate Command Center + Engine Pivot specs (both merge in)
- Manifesto: `docs/superpowers/specs/2026-04-17-tr4sh-quake-manifesto.md`

## Phase Status

| Phase | Split | Status | Current Task |
|---|---|---|---|
| Phase 1 | S1 | Review gate | Parts 4/5/6 full renders delivered 2026-04-17. User reviewing per `SPLIT1_USER_CHECKLIST.md`. Parts 7-12 queued pending Part 4 approval. |
| Cinema Suite | S1 | **Shipped 2026-04-19** | 25-task plan delivered. 132 tests pass. 4 code-review findings fixed. Branch `creative-suite-v2-step2`. Panels 1–8 live. Tier A+B preview working. Real-engine latency check pending user hands-on. |
| Phase 1.5 | S2 | Spec'd | Tr4sH Quake manifesto committed. Command Center + Engine Pivot specs merge in. |
| Phase 2 | S2 | Planned | Agent (free cam / kill cam / image reader) + scene extrapolator |
| Phase 3 | S2 | Research | Highlight criteria locked via FT-2. Agent training feeds this. |
| Phase 3.5 | S2 | Research | Protocol-73 port becomes Track A of Tr4sH Quake engine fork |
| Phase 4 | S2 | Vision | Public release of Tr4sH Quake — community give-back |

## Authoritative Asset Sources (2026-04-17, confirmed on disk)

**NEW RULE — ENG-1:** Steam paks are the source of truth for baseq3 assets. Wolfcam extracts are reference only.

| Source | Path | Size |
|---|---|---|
| Quake Live baseq3 | `C:\Program Files (x86)\Steam\steamapps\common\Quake Live\baseq3\pak00.pk3` | 962 MB |
| Quake 3 Arena baseq3 | `C:\Program Files (x86)\Steam\steamapps\common\Quake 3 Arena\baseq3\pak0.pk3` + `pak1-8.pk3` | 496 MB |
| Q3 engine source | `tools/quake-source/quake3-source/` | — |
| q3mme (movie maker) | `tools/quake-source/q3mme/` | — |
| quake3e (modern fork) | `tools/quake-source/quake3e/` | — |
| UDT parser | `tools/quake-source/uberdemotools/` | — |

**Read-only for Steam paths. Never modify.** Our overrides are `zzz_*.pk3` in `creative_suite/generated/packs/`.

## HARD RULES — Cinema Suite (NEW 2026-04-19, Phase 1 ship)

### Rule CS-1: Single-Worker Job Queue, Never Parallel Renders
**The render/preview job queue is depth=1. Second submit → HTTP 409 busy.**
- `creative_suite/api/_render_worker.py` `JobQueue` enforces `RuntimeError` when a job is active.
- Phase1 router returns 409 on `RuntimeError`, never queues.
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

## npm Allowance Policy (NEW 2026-04-19)

User unlocked npm packages. **Vetting checklist (ALL must pass before `npm install`):**
1. ✅ License in {MIT, BSD-2, BSD-3, Apache-2.0, ISC} — reject AGPL, custom, unknown
2. ✅ `npm audit` clean (no high/critical) at install time
3. ✅ Snyk advisory-DB lookup clean
4. ✅ Pinned version — no `^` or `~` ranges
5. ✅ GitHub source + >1k stars OR >3 years maintained
6. ✅ No network calls at build time (pure lib only)

Currently on importmap+CDN — `wavesurfer.js` v7 (BSD-3, ~60KB, zero deps) queued as first candidate for Panel 4 upgrade. Introduce in dedicated commit, not mixed with feature work.

## Demo Corpus Inventory (2026-04-19, fully on disk)

| Corpus | Path | Count | Size |
|---|---|---|---|
| Primary (full 7z extract) | `G:\QUAKE_LEGACY\demos\` | **6,465** `.dm_73` files | **13.19 GB** |
| Secondary (wolfcam staging) | `G:\QUAKE_LEGACY\WOLF WHISPERER\WolfcamQL\wolfcam-ql\demos\` | 948 (some <150 KB action-extracts) | ~2 GB |

**11 anonymized players** across the corpus. FT-1 (custom C++ parser) and FT-5 (nickname regex dictionary) are no longer blocked.

## FT-4 Ghidra Blockers (user actions needed)

Ghidra FT-4 sandbox committed (`engine/ghidra/`) with preliminary inventory. **Full dissection blocked on:**
1. Install Ghidra 11.3 + JDK 21 (user machine)
2. Extract `G:\QUAKE_LEGACY\WOLF WHISPERER\Wolf Whisperer.rar` (contains main binary)
3. Decision: build or drop UDT_json / q3mme as RE targets (scope call)

**Already done without Ghidra** (from PE-probe sweep 2026-04-19):
- `qagamex86.dll` has DWARF + STABS debug info — **not stripped**, symbol-rich
- 34-entry MOD_* enum seed (protocol-73 confirmed via `MOD_HMG` + `MOD_RAILGUN_HEADSHOT`)
- 103-entry EV_* enum seed
- WolfcamQL capture-cvar seed (r_mode, com_maxfps, `video avi`, `seekclock`, ...)

## Engine Rules (NEW — from engine-pivot spec)

- **ENG-1**: Asset source of truth = Steam paks, not wolfcam extracts.
- **ENG-2**: Style pack pk3s MUST be named `zzz_*.pk3` for alphabetical override of `pak00.pk3`.
- **ENG-3**: Pack testing requires `+set sv_pure 0`.
- **ENG-4**: Steam pak files are read-only. Never modify.
- **Engine role split (v1)**: wolfcamql for `.dm_73` playback only; q3mme for everything else (map browse, sprite preview, pack testing, 4K capture).
- **Endgame**: port wolfcamql's protocol 73 patches into q3mme (Phase 3.5 research track), then retire wolfcam entirely.

## Key Technical Facts (memorize these)

### WolfcamQL Automation Pattern
```
Write gamestart.cfg:
  seekclock 8:52; video avi name :demoname; at 9:05 quit
Launch: wolfcamql.exe +set fs_homepath <out_dir> +exec cap.cfg +demo demo.dm_73
```

### Frag Detection in .dm_73
```python
# In each snapshot, scan entities for:
entity.event & ~0x300 == EV_OBITUARY   # (0x300 masks the toggle bits)
# Then:
killer = entity.otherEntityNum2   # client slot 0-63
victim = entity.otherEntityNum    # client slot 0-63
weapon = entity.eventParm         # MOD_* constant
time   = snapshot.server_time     # milliseconds
```

### Key Tools
- FFmpeg binary: `G:\QUAKE_LEGACY\tools\ffmpeg\ffmpeg.exe`
- WolfcamQL: `G:\QUAKE_LEGACY\tools\wolfcamql\wolfcamql.exe` (also in WOLF WHISPERER\)
- UberDemoTools: `G:\QUAKE_LEGACY\tools\uberdemotools\UDT_json.exe`
- WolfWhisperer binary (for RE): `G:\QUAKE_LEGACY\WOLF WHISPERER\WolfWhisperer.exe`
- **Demo corpus (primary):** `G:\QUAKE_LEGACY\WOLF WHISPERER\WolfcamQL\wolfcam-ql\demos\` (948 `.dm_73` files — verified 2026-04-17). Some are action-extracts (<150 KB), full demos are 2-4 MB.
- **Demo corpus (secondary, 2026-04-17):** User located original ~3000-demo dump — will be staged into `G:\QUAKE_LEGACY\demos\` for full re-extraction
- Parser fixture env var: `DM73_FIXTURE_DIR` (overrides path in `phase2/dm73parser/tests/fixtures.h`)

### Cross-Phase Learning Store
All phases write learnings to: `G:\QUAKE_LEGACY\database\knowledge.db`

## Human Review Gates (NEVER skip these)

1. **Gate P3-0:** Define highlight criteria WITH user before ANY demo extraction
2. **Gate P1-1:** Review clip lists before rendering (edit phase1/clip_lists/partXX.txt)
3. **Gate P1-2:** Watch 30s preview before full render
4. **Gate P1-3:** Watch full Part render before moving to next
5. **Gate P2-1:** Review parser output on 10 sample demos before full parse
6. **Gate P2-2:** Rate frags in dashboard before batch WolfcamQL render
7. **Gate P2-3:** Review 10 rendered clips before full batch
8. **Gate P3-1:** Review AI-selected frags vs human-selected — measure agreement rate

## HARD RULE — Visual Documentation (ALL Phases)

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
2. Check `database/knowledge.db` for cross-phase learnings (if exists)
3. Check current phase plan in `docs/superpowers/plans/`
4. Review `phase1/music/available_tracks.txt` for music status
5. Never run batch operations without human confirming at review gate
6. Never commit personal data

## Funded Tracks — User-Approved 2026-04-17 (HUMAN-QUESTIONS.md §10)

These were informal before — now they are hard commitments. Any plan that ignores these is wrong.

### FT-1: Custom C++ `.dm_73` parser (Path B)
- Lives in `phase2/dm73parser/` — C++17 + CMake, static lib + `dm73dump` CLI → JSON Lines
- Vendors `msg.c`, `huffman.c`, `common.c`, `q_shared.h`, `bg_public.h` from wolfcamql-src under GPL-2.0 with preserved headers
- Authoritative format reference: `docs/reference/dm73-format-deep-dive.md` (1,337 lines)
- Validated against `UDT_json.exe` golden output on 3 hand-picked demos before trust
- Spirit: *"WE ARE QUAKE WE BREATH QUAKE WE KNOW IF WE CHANGE THIS BIT IT WILL MAKE THE RAIL PINK"* — full control, no black boxes

### FT-2: Highlight Criteria v2 (locked)
- Authoritative: `docs/specs/highlight-criteria-v2.md` (supersedes v1)
- Every frag enters the corpus (no minimum threshold); tiering is for *ordering*, not filtering
- Weapon weights: Rocket 2.0, Rail 1.5, Grenade direct 2.5, LG accuracy-banded (40/50/56)
- Multi-kill window = full CA round; airshot = any weapon, 200ms min air time
- LMS is a separate tag with audio-cue integration opportunity
- All weapon-combo sequences ≤ 2s extracted for pattern-recognition ML

### FT-3: Phase 3.5 — 3D Intro Lab
- Parallel research track, not on critical path for Parts 4-12
- Goal: AI-assisted 3D intros using Q3 BSP maps + MD3 models (Xaero/Visor priority) + ComfyUI/AnimateDiff
- Also carries the Parts 1-3 morph-remaster experiment (Annihilation-style game-to-game morphs)
- Location: `phase35/` (already scaffolded)

### FT-4: Ghidra every executable
- `WolfWhisperer.exe` is the anchor but ALL executables in the project get reverse-engineered for full command/IPC mapping
- Targets: `tools/wolfcamql/wolfcamql.exe`, `tools/uberdemotools/UDT_json.exe`, any other shipped binaries
- Outputs land in `engine/ghidra/` with per-binary markdown reports
- No WolfcamQL automation ships in Phase 2 until this completes

### FT-5: Nickname dictionary + notable-player regex
- Per `database/frags.db` schema in HUMAN-QUESTIONS.md §6
- User's historical nicknames (Tr4sH + variants) and famous opponents (e.g. strenx) become regex tags
- Notable-victim frags get auto-flagged as Part-opening / climax candidates
- All alias strings stay LOCAL — public exports use opaque canonical_id hashes only

### FT-6: FFmpeg encoder benchmark → quality ceiling
- Per Rule P1-J, file size doesn't matter — find the WOW-factor renderer
- Agent benchmarking x264/x265/AV1/NVENC with VMAF on a reference clip
- Outcome feeds `phase1/config.py` for all final renders from Part 4 onward

### FT-7: Game-audio mix level = 55% (pending re-evaluation)
- User ticked 55% in HUMAN-QUESTIONS.md §5.1 with rider "we could still change this later"
- Part 3 review said "way too low" at that level → flagged for A/B test on next render pass
- `Config.game_audio_volume` is the single source of truth (currently 0.75 after Part 4 review)
- Resolve conflict: next preview compares 0.55 vs 0.75 on the same frag and user picks

## Phase 4 Vision

Once the system works for this project, it becomes a public CLI:
`pip install quake-legacy` → give it demos → get a fragmovie.

Document EVERYTHING as we go. All RE findings, all binary format work, all camera math.
The community will build on this. The Q3 engine is open source — this is the gift back.
