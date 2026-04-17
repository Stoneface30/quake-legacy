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

### Rule P1-G: In-Game Audio Is Non-Negotiable
**In-game sound must ALWAYS be preserved and audible under music.**
- Game audio mix level: **75% by default** (under music), never 0%
  - v1 was 30% (too quiet — Part4 v1 review)
  - v2 was 55% (HUMAN-Q §5.1 ticked value). Part3 A/B/C review said "way too low"
  - v3 is 75% — trust the review, not the ticked answer
- Critical sounds to preserve: grenade direct hit, rocket impact, rail crack, weapon combos
- These sounds define fragmovie texture — muting them loses the sport entirely
- Phase 2 future: grenade/rocket direct hits OUT OF POV = automatic follow-cam candidates
- `assemble_part()` must always use `amix` when music present — never discard game audio
- Configurable via `Config.game_audio_volume` (default 0.75)

### Rule P1-K: Multi-Angle Clips MUST Interleave Within the Frag
**Multi-angle captures (FP + FL1/FL2/FL3 of the SAME frag) must NEVER play
sequentially. Playing the same frag back-to-back from 4 angles = boring (Part3 review).**
- FP + FL* angles show the SAME frag from different cameras
- Required behavior: cut between angles WITHIN one screen-time window for that frag
- Default schedule (for a frag window T, N FL angles):
  - FP setup           (0% → 35% of T)
  - FL angles in order (35% → 75% of T; middle FL gets climax weight)
  - FP confirmation    (75% → 100% of T)
- Source-time offsets into each FL source clip are synced to the window
  position so all cameras show the same instant of the frag
- Implemented via `trim_starts` + `trim_durations` in `build_filter_complex`
- Cuts INSIDE a multi-angle group are ALWAYS hard cuts (no xfade,
  see `TransitionPlanner`) — we are mid-action
- Transitions between DIFFERENT frags use a variety palette
  (flash cut / xfade / section fade / white flash on T1→T1 peaks) —
  see `phase1/transitions.py`
- Effects variety (slow-mo / speed ramp / zoom punch / desat flash / beat pulse)
  via `phase1/effects.py` — no longer "slow-mo on every T1"

### Rule P1-L: Clip Padding Convention — NEVER Cut Action
**Every Phase 1 AVI clip has ~2s pre-action + ~3s post-action padding baked in by the WolfcamQL capture. The post-roll tail ends with a console-close / HUD-drop artifact.**
- Strip `Config.clip_tail_trim` (default **1.5s**) off the tail of EVERY clip. Non-negotiable: that artifact never reaches the cut.
- The 2s head + 1.5s remaining tail = "transition envelope" — xfade / section-fade / white-flash consume THIS region, never the action.
- `Config.transition_envelope` (default **1.0s**) is the maximum beat-sync is allowed to trim beyond the tail-strip. So for a clip of raw length L, beat-sync may set duration anywhere in `[L - 1.5 - 1.0, L - 1.5]`. **Beat-sync cutting into action is a hard failure** (Part 3 rev1 review).
- Implementation: `phase1/experiment.py` applies tail-trim universally after clip resolution, then floors beat-sync planned durations at `usable_dur - transition_envelope`.
- User phrased it: "the 2 sec after a clip is meant to be used for the transition — use 1 second in start and 1 sec in end to transition fade."

### Rule P1-H: Transition Minimalism
**Minimal transitions. Chain quality > visible transition effects.**
- Default xfade: 0.08s (near-invisible, just a flash cut)
- Use real xfade (0.25s+) ONLY at major section breaks
- Focus on: clip ordering, tier hierarchy placement, beat alignment
- "The chain" = the sequence of clips flowing correctly. That's where effort goes.

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
