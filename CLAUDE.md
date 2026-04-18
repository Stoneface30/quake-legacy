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

## HARD RULES — Phase 1 Automation (from user review, never violate)

### Rule P1-A: Three-Tier Clip Combining
**Every Part must combine ALL THREE tiers: T1/PartX + T2/PartX + T3/PartX.**

CORRECTED tier semantics (Gate 1 review update):
- **T1 = RAREST, elite/peak frags** — fewest clips, most precious. Save for climax moments. Each T1 clip carries weight. NEVER use as filler.
- **T2 = MAIN MEAL** — most clips per Part. The backbone. 70%+ of screen time comes from T2. This is what the fragmovie IS.
- **T3 = FILLER / CINEMATIC** — atmospheric, more numerous. Intro/outro priority. Can be sorted/filtered. Slow-mo FL angles for establishing shots.

`scan_part_frags(part, cfg)` MUST scan all three tiers.
A Part assembled from T1 only is WRONG. A Part that uses T1 as filler is also wrong.

### Rule P1-B: Intro/Outro Clip Selection
**Lower tier multi-angle subdirs are the intro/outro clip pool.**
- T3 multi-angle folders (contain FL clips) → first choice for Part intros/outros
- T2 multi-angle folders → second choice
- T1 multi-angle folders → use only if T2/T3 exhausted
- Context: lower-tier frags look good as cinematic intros because they're less intense
  and the FL angles give more visual variety for establishing shots

### Rule P1-C: PANTHEON Intro — ALWAYS Prepend
**Every Part gets IntroPart2.mp4 prepended. Never skip.**
- Path: `G:\QUAKE_LEGACY\FRAGMOVIE VIDEOS\IntroPart2.mp4`
- Duration: 25.77s, 1920x1080, 30fps H264
- Style: PANTHEON temple logo (grey bg) → in-game CA Tribute billboard scene
- Future: generate alternate PANTHEON intro versions in same style (Phase 4)

### Rule P1-D: Preserve Clip Names in Previews
**Preview filenames must show the original clip name** (via burn-in text or filename log).
- User reviews previews and references clips by name/timestamp to give edit feedback
- Format: burn clip filename in bottom-left corner at 18pt for preview renders only
- Full renders do NOT show clip names

### Rule P1-E: Phase 1 Effects Scope
**What can be done in Phase 1 with existing AVIs (do it now):**
- Slow-motion (setpts + atempo)
- Speed-up / fast-forward
- Zoom (crop + scale)
- Basic tracking (scale + translate for center-of-action)
- Camera angle cuts (FP → FL, using existing FL AVIs)
- Transitions (xfade, fade to black, hard cut)

**What requires Phase 2/3/4 (do NOT try in Phase 1):**
- Rocket follow / bullet cam (needs WolfcamQL re-render)
- New camera angles not in existing AVIs
- Demo re-recording from different positions
- Any WolfcamQL command-driven capture

### Rule P1-G: Audio Mix — Game Foreground, Music Halved (REVISED Part 4 review 2026-04-17)
**Game sound is FOREGROUND. Music is atmosphere underneath.**
- `game_audio_volume = 1.0` (full — grenade hits, rail cracks, rocket impacts)
- `music_volume      = 0.5` (halved — sits behind game audio)
- User verdict: *"lower music by 50% keep game sound"*
- History: v1 30% / v2 55% / v3 75% / v4 85% (all game-under-music) → v5 music halved, game full
- `assemble_part()` must always use `amix` when music present — never discard game audio
- See `docs/reviews/part4-review-2026-04-17.md` §1

### Rule P1-K: Multi-Angle — FP Backbone + ONE FL Slow-Contrast (REVISED Part 4 review 2026-04-17)
**FP is the spine. At most ONE FL cuts in, used as slow-motion contrast. No 4-angle ping-pong.**
User verdict: *"the FPV its absolutly terrible they swap back and forth in a terrible order,
you should focus on keeping the main pov and use 1 of the FL video files you can slomo the main
and the other for the effect."*
- New window schedule (FP-dominant):
  - FP normal speed   (0% → 40% of T)   — setup
  - FL slow-mo 0.5×   (40% → 65% of T)  — contrast replay of the same moment
  - FP normal speed   (65% → 100% of T) — confirmation / follow-through
- Only ONE FL is used per frag. The rest of a multi-angle dir stays unused this Part.
- Pick the FL with biggest angle delta from FP (side/top preferred).
- All cuts remain hard cuts (no xfade — see P1-H).
- Ping-pong between multiple FL angles is BANNED.

### Rule P1-L: Clip Trim — 1s Head / 2s Tail, Full-Length Between (REVISED Part 4 review 2026-04-17)
**User verdict:** *"we can just cut the first second and the 2 last second for the transition effects."*
- `clip_head_trim = 1.0s` (was 2.0s envelope)
- `clip_tail_trim = 2.0s` (was 1.5s + 1.0s envelope)
- `transition_envelope = 0.0s` (no transitions means no envelope)
- Beat-sync may NO LONGER truncate clips. If beat doesn't land, use Rule P1-Q
  (REPLAY_SPEED_CONTRAST) to stretch via slow/normal replay instead of cutting.

### Rule P1-H: NO TRANSITIONS (REVISED Part 4 review 2026-04-17)
**All inter-clip joins are hard cuts in Phase 1.** User verdict: *"no fucking transition
not even a fading to the next image or anything."*
- `xfade_duration = 0.0`
- `TransitionPlanner.plan()` returns HARD_CUT unconditionally (all other kinds dead code)
- No section fades, white flash, dip-to-black, cross-dissolve
- Transition palette design is DEFERRED to Phase 2 pattern-database work

### Rule P1-N: Title Card Contract (NEW Part 4 review 2026-04-17)
**Every Part intro sequence is [PANTHEON 7s] + [Title Card 8s] + [Content]. No exceptions.**
User verdict: *"no Quake Tribute, no By Trash no number no slowmo with the letters this is critical."*
```
  0s  → 7s   PANTHEON logo (IntroPart2.mp4 first 7s) — existing
  7s  → 10s  "QUAKE TRIBUTE" letter-by-letter slow-mo reveal
  10s → 12s  "Part N" number
  12s → 14s  "By Tr4sH" credit
  14s → 15s  Fade title block → content begins
```
- Implementation: `phase1/title_card.py` — ffmpeg `drawtext + zoompan + geq` filters
- Rendered per-Part to `phase1/assets/title_card_partNN.mp4`, concat after PANTHEON, before first clip
- Font style: bold Impact-like, white on black, motion-blurred entry

### Rule P1-O: Music Coverage (NEW Part 4 review 2026-04-17)
**Music audio is continuous from title-card end to outro start. Silence gaps are a failure.**
User verdict: *"the music stop when tis over and there is not another one who take over."*
- If Part runtime > music length: pipeline queues a second track (beat-matched stitch)
  or loops (crossfade) on music stream only
- Video stream stays hard-cut; music crossfade is `cfg.music_crossfade_on_loop = 0.5s`
- `cfg.music_loop_if_short = True` enables auto-loop

### Rule P1-P: Full-Length Clip Contract (NEW Part 4 review 2026-04-17)
**No sub-clip fragments. A clip that enters a Part plays its full post-trim duration.**
User verdict: *"a lot of the clip you do in quick succession are just showing half a second
of a totally unrelated clip, i think you did not understand what a filler was, we need to
keep ALL the original clip length."*
- "Filler" = full-length atmospheric establishing shot (typically T3), NOT 0.5s cutaway
- Quick-swap pattern previously used on T3 is DELETED
- The micro-cut idea survives ONLY as a beat-locked FP↔FL stutter inside one multi-angle group
  (flagged as `FL_BEAT_STUTTER` in `phase1/effects.py`, gated off by default)

### Rule P1-Q: Replay-Speed Contrast Effect (NEW Part 4 review 2026-04-17)
**Short T1 clips (< 3.0s post-trim) may be played twice: once slow, once normal
(or normal → slow).** User verdict: *"good effect on really short T1 clip is to play
it slow once replay it normal speed, or the other way around."*
- New effect `REPLAY_SPEED_CONTRAST` in `phase1/effects.py`
- Planner picks direction (slow→normal or normal→slow) based on beat position
- Replaces beat-sync truncation (which is now banned by Rule P1-L)
- Research agent to survey additional replay-style effects → `docs/research/effect-catalog-expansion.md`

### Rule P1-S: Beat-Sync Governs Transitions, Never Clip Duration (NEW 2026-04-18)
**Beat-match lives on the JOIN between clips — it sets WHEN a cut happens, not HOW LONG a clip is.**
User verdict: *"we dont beat match cutting the clips as the clips ARE the frags
if you show 2sec of a 5sec clip it will be pointless for phase1, we need to
beatmatch on transition for phase1."*
- Phase 1 clips are already-rendered AVIs — each clip = one frag. The clip IS the moment.
- Beat-sync may ONLY nudge **transition points** (the hard cut between clip N and N+1):
  - `Clip N` plays its full post-P1-L-trim duration.
  - The next beat ≥ `clip_N.end` becomes the cut-in time for `Clip N+1`.
  - If the gap between `clip_N.end` and the next beat is large, fill with
    a full-length T3 cinematic (Rule P1-P) — **never** extend clip N artificially.
- Beat-sync may NOT:
  - Truncate clip content to land on a beat (banned — see Rule P1-L, P1-P)
  - Time-stretch clips (banned — speed changes only via REPLAY_SPEED_CONTRAST per P1-Q)
  - Shift audio by clip-body milliseconds — audio crossfades happen at the cut seam only
- `plan_beat_cuts()` returns *cut timestamps*, not *clip durations*. Any code path that
  shortens a clip below `full_length - head_trim - tail_trim` is broken.
- This formalizes the golden rule P1-I ("frag + effect + music align") — alignment
  is at the seam, not inside the frag.

### Rule P1-R: Three-Track Music Structure (NEW 2026-04-18 music-picks approval)
**Every Part ships with THREE music tracks: intro + main + outro. One-track renders are invalid.**
User verdict: *"we need to have multiple audio track for the whole video we need intro and outro!"*
- Music layout per Part:
  - **Intro track** — plays under PANTHEON logo (7s) + title card (8s) = ~15 s atmospheric build
  - **Main track** — the curated per-Part hype/energy track (body of the Part)
  - **Outro track** — ~30 s cooldown/closer at the tail, matches intro in tone
- Series-wide defaults (PANTHEON identity):
  - `phase1/music/pantheon_intro_music.mp3` — *Cinema - Sped Up* (JKRS)
  - `phase1/music/pantheon_outro_music.mp3` — *Eple* (Badger)
- Per-Part overrides: `partNN_intro_music.*` / `partNN_outro_music.*` (resolved first)
- Crossfades between tracks are **beat-locked** (librosa onset snap), not time-locked:
  - `intro_music_crossfade = 1.5s`, `outro_music_crossfade = 2.0s`
- Rule P1-O (music coverage continuity) still applies — no silence gaps anywhere.
- Config accessors: `Config.intro_music_path(part)` / `music_path(part)` / `outro_music_path(part)`.
  `None` from main = hard fail; `None` from intro/outro = warning + degrade to main-only.
- 2026-04-18 music drop (committed): Part 4 MAKEBA · Part 5 Phonky Tribu · Part 6 Past Lives
  Hardtekk · Part 7 SPRINTER Techno · Part 8 bulletproof tekkno · Part 9 Zoo Rave Edit ·
  Part 10 ANXIETY HYPERTECHNO · Part 11 Timewarp (Dimension Rmx) · Part 12 Vois sur ton chemin.

### Rule P1-I: Golden Rule — Frag + Effect + Music Must Align
**The chosen effect (slow-mo, zoom, fast-forward, hard cut) must match both the frag type AND the music beat/section.**
- A T1 peak without matching musical weight is a miss
- A slow-mo without a corresponding bass drop is a miss
- Beat-sync is mandatory from Part 4 onward — every cut snaps to a beat, T1 peaks snap to section drops
- `phase1/beat_sync.py` is the authority; integrate via `plan_beat_cuts()` in every render path
- User phrased it: "the style need to match the music / beat — the frag + effect + music is the golden rule of a good video"

### Rule P1-J: Final Render Quality Ceiling
**File size does not matter. Quality does.**
- User confirmed: originals will be kept full quality, YouTube/streaming re-encodes downstream
- Final render target (pending user approval in HUMAN-QUESTIONS.md §5.4): CRF 15-17, preset slow/veryslow, x264 High Profile 1920×1080 60fps
- Preview renders may use CRF 23 veryfast for speed; only the final per-Part render commits to the quality ceiling

### Rule P1-F: Music Catalog
All available music tracks listed in: `phase1/music/available_tracks.txt`
- Place downloaded tracks as `part04_music.mp3` etc. in `phase1/music/`
- Pipeline auto-detects by filename
- Quake 1 (NIN), Quake 2 (Sonic Mayhem), Quake 3 OST are valid choices

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
- Outputs land in `game-dissection/ghidra/` with per-binary markdown reports
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
