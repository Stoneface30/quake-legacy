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
- Game audio mix level: **55% by default** (under music), never 0% — Part4 v1 review: 30% was too quiet
- NOTE: Updated Plan (2026-04-16) proposes 30% or 45% variants — awaiting user decision in `HUMAN-QUESTIONS.md §5.1`. Until resolved, ship at 55%.
- Critical sounds to preserve: grenade direct hit, rocket impact, rail crack, weapon combos
- These sounds define fragmovie texture — muting them loses the sport entirely
- Phase 2 future: grenade/rocket direct hits OUT OF POV = automatic follow-cam candidates
- `assemble_part()` must always use `amix` when music present — never discard game audio

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

## Phase Status

| Phase | Status | Current Task |
|---|---|---|
| Phase 1 | In Progress | Experiment renders → user review → lock style → all 9 Parts |
| Phase 2 | Planned | Await P3-A highlight criteria session + P3-B command inventory |
| Phase 3 | Research | Phase3 AI research complete. Await highlight criteria session |
| Phase 4 | Vision | Public CLI tool for anyone with demos |

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

## Phase 4 Vision

Once the system works for this project, it becomes a public CLI:
`pip install quake-legacy` → give it demos → get a fragmovie.

Document EVERYTHING as we go. All RE findings, all binary format work, all camera math.
The community will build on this. The Q3 engine is open source — this is the gift back.
