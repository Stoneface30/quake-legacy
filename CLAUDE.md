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

### Rule P1-G v3: Music at 30%, Layered Over ENTIRE Output (REVISED Part 5 v7 review 2026-04-18)
**Music drops from 0.50 → 0.30 AND layers across PANTHEON + title + body, not body only.**
User verdict: *"music is ONCE AGAIN too loud compared to game sound"* + *"intro sound NEED to be kept"*.
- `cfg.music_volume = 0.30` (was 0.50)
- `cfg.game_audio_volume = 1.00` unchanged
- `final_render()` filter_complex builds a 3-part foreground track (PANTHEON audio + silent title + body game) and amix'es music ACROSS the whole thing. Previously music only played under the body; intro was music-silent.
- PANTHEON audio preserved at full volume; intro music sits under it at 0.30.

### Rule P1-H v3: Short Seam Xfades ARE Allowed (REVISED Part 5 v7 review 2026-04-18)
**0.15s xfade between every body chunk. Distinct from the banned 1s dramatic fade.**
User verdict: *"the transition are still non existant"* + *"for the clip is to have space for transition"*.
- `cfg.seam_xfade_duration = 0.15` (was 0.0)
- `assemble_body_with_xfades()` in `render_part_v6.py` builds the body as one mp4 with xfade chain across all chunks (`xfade=transition=fade:duration=0.15` + `acrossfade d=0.15`).
- The 2s tail-trim from Rule P1-L is now officially "transition space".
- Still banned: 1s fade-to-black, dip-to-white, cross-dissolve > 0.3s, any intro/outro dramatic fade.
- Legacy `xfade_duration=0` stays; only `seam_xfade_duration` is active. Supersedes "HARD_CUT unconditionally" in TransitionPlanner.

### Rule P1-L v2: FP/FL-Differentiated Head Trim (REVISED Part 5 v7 review 2026-04-18)
**FP clips trim 1s off head; FL clips trim 2s to kill the console/loading view.**
User verdict: *"head is 1 or 2 there are difference in the FL clips as you need to cut the console 2sec in"*.
- `cfg.clip_head_trim_fp = 1.0` (FP — unchanged)
- `cfg.clip_head_trim_fl = 2.0` (FL — new)
- `cfg.clip_tail_trim   = 2.0` (unchanged; reclassified as "transition space" per P1-H v3)
- `build_body_chunks()` detects FL via filename token (`"FL" in src.stem.upper().split("_")`).

### Rule P1-U: Tier Interleave for Pacing (NEW Part 5 v7 review 2026-04-18)
**Clip list is reshuffled into round-robin tier buckets so T1/T2/T3 alternate.**
User verdict: *"mix of t3 t2 t1 organized each clip depending on the tier the map and the time of the action so we dont have 5 actions that last 30 sec in a row"*.
- `interleave_clips_by_tier()` in `render_part_v6.py` round-robins with drain order T2/T1/T3/T2/T3/T1/T2 — T2 (main meal) shows up most, T1 sprinkled, T3 woven in.
- Preserves local ordering within each tier bucket (FIFO).
- Map-aware and duration-aware interleaving are Phase 2 follow-ups.

### Rule P1-V: Beat-Snap + Silence-Detect (DEFERRED to Part 5 v9)
**Not in v8. Open work items:**
- `phase1/beat_sync.py` doesn't exist yet; `plan_beat_cuts()` is imported by `experiment.py` but dead. Needs librosa onset-detection + seam-timestamp snap (±200ms window).
- Silence-detect via `ffmpeg silencedetect` → 1.5-2× `atempo` on clip-internal silence >2s. No scaffold.
- Tracked in `docs/research/beat-and-silence-2026-04-18.md` (TODO to write).

### Rule P1-G v4: Music at 0.20 + Objective Level Gate (REVISED Part 6 v8 draft review 2026-04-18)
**Music drops 0.30 → 0.20. Final mix MUST pass an objective ebur128 two-channel check before render is shipped.**
User verdict (third complaint in a row): *"volume of the music is still too loud compared to the game, please use 2 channel and check level so you can see the issue."*
- `cfg.music_volume = 0.20` (was 0.30 in v3, 0.50 in v2, 0.30 in v1).
- `cfg.music_fadein_s = 2.0` — music hard-started in v8, now fades in over 2 s under PANTHEON.
- `cfg.music_fadeout_s = 2.5` — matches outro track closeout.
- **Objective gate** (blocks render ship): `phase1/audio_levels.py::measure_music_vs_game()` runs `ffmpeg ebur128` on (a) music-only stem and (b) game-only stem extracted from the final render. **Music integrated loudness MUST be ≥ 12 LU below game peak LU.** If not, render is flagged `FAILED_LEVEL_GATE` and not copied to deliverables.
- Subjective "lower music" verdicts now produce a committed ratio, not a guess. Gate log lives at `output/partNN_levels.json`.

### Rule P1-H v4: Visible Transitions (0.4 s) (REVISED Part 6 v8 draft review 2026-04-18)
**Seam xfades bump 0.15 s → 0.40 s. 0.15 s was invisible — user has asked for transitions four times.**
User verdict: *"ive been asking for transition since the first prompt but it was never made"*.
- `cfg.seam_xfade_duration = 0.40` (was 0.15).
- Still banned: anything ≥ 0.8 s, fade-to-black, dip-to-white.
- Tail-trim budget must cover this — see P1-L v3 (tail 2.5 s leaves 2.1 s clean content + 0.4 s fade).
- Audio drift fix (mandatory, ships with this rule): every chunk enters the xfade chain with `asetpts=PTS-STARTPTS,aresample=async=1:first_pts=0`. The v8 chain compounded ~40 ms drift per N seams; v9 pins every chunk PTS to zero before `acrossfade`.

### Rule P1-L v4: Trimming is FL-ONLY, FP Clips Untouched (REVISED Part 4 v10 review 2026-04-18)
**FP clips have NO head or tail trim. Only FL clips get head=1.0 / tail=2.0.**
User verdict: *"the 1 second before 2 second in the end rule was only for the FL views"*.
v1–v3 had been progressively trimming ALL clips — that was wrong. FP is the frag itself (console/HUD stays clean from start through kill through follow-through). Only FL (free-look) has console reappearance at start + angle falloff at end.
- `cfg.clip_head_trim_fp = 0.0` (was 1.0)
- `cfg.clip_head_trim_fl = 1.0` (was 2.0)
- `cfg.clip_tail_trim_fp = 0.0` (was 2.5 blanket)
- `cfg.clip_tail_trim_fl = 2.0` (was 2.5 blanket)
- `cfg.min_playable_duration_s = 2.0` unchanged.
- Tail-trim no longer carries the xfade budget. 0.4 s xfade blends across untrimmed FP content — accept the blend.
- Cached chunks MUST be invalidated (`rm -rf output/_partNN_v6_body_chunks/`) when upgrading to v4.
- partNN_overrides.txt still wins: per-clip `head_trim=X` / `tail_trim=X` override the FP/FL defaults.

### Rule P1-L v3 (SUPERSEDED by v4 — kept for history): Tail Trim 2.5 s + Short-Clip Protection Floor (REVISED Part 6 v8 draft review 2026-04-18)
**Tail trim bumps 2.0 → 2.5 s. Clips whose post-trim body would fall below 2.0 s are SKIPPED, not squeezed.**
User verdict: *"09Sec : we can see the console need to cut clip 0.5 shorter in the end"* + *"149-77 is cut we can't see anything review and ensure we don't cut clip that are already too short"*.
- `cfg.clip_tail_trim = 2.5` (was 2.0 — kills console reappearance at clip end).
- `cfg.clip_head_trim_fp` and `clip_head_trim_fl` unchanged (1.0 / 2.0).
- `cfg.min_playable_duration_s = 2.0` — NEW. `build_body_chunks()` computes `clip_dur - head_trim - tail_trim`; if < 2.0 s, log `SKIP_TOO_SHORT` and drop the clip from the Part. No compression, no magic stretching.
- Short-T1 auto-slowmo (from previous session) still applies BEFORE the trim check, giving short T1 frags a legitimate way to stay in the render.

### Rule P1-W: Music is Full Tracks, Never Mid-Song Cuts (NEW Part 6 v8 draft review 2026-04-18)
**Every music slot plays a complete track. Mid-song swaps, looped tails, or hard-cut song seams are a hard failure.**
User verdict: *"15sec the music swap to another music what the fuck? we need full songs not a song cut in the middle"*.
- `phase1/music_stitcher.py` MUST queue N full tracks whose combined duration ≥ body duration + fade budget. Each track plays to its natural end.
- If main track is shorter than body, queue a second *full* main-style track and beat-match crossfade at the seam (`cfg.music_crossfade_on_stitch = 1.5`). Looping a truncated tail is banned.
- Pool: `phase1/music/partNN_main_*.mp3` (multiple main candidates per Part — new naming). If only one main exists and is too short, the pipeline FAILS LOUDLY rather than loop-cutting.
- Logs a `music_plan.json` next to render: `[{track, start, end, role}]`. Ship gate: every entry must have `duration == track.full_duration ± 0.1s` (no truncations).

### Rule P1-X: PANTHEON Intro is 5 s, Not 7 s (REVISED Part 6 v8 draft review 2026-04-18)
**Intro clip duration drops 7 s → 5 s. The logo beat lands at 5 s; the extra 2 s in v8 was dead air.**
User verdict: *"5second only intro sound"*.
- `cfg.intro_clip_duration = 5.0` (was 7.0 — still hard-coded in `render_part_v6.py::build_intro()`).
- Title card (Rule P1-N / P1-Y) still 8 s.
- Total pre-content offset: 5 + 8 = 13 s (was 15 s). Annotation tool (creative_suite Track 2) MUST read this from config, not hard-code 15.

### Rule P1-Y: Title Card Font + Kerning Quality Gate (NEW Part 6 v8 draft review 2026-04-18)
**Title card uses Bebas Neue (vendored OFL TTF), growing-substring typewriter with fixed left-anchor x, glow-blend integration with FL backdrop, and a 2 px sine drift to kill the "pasted sticker" look.**
User verdict: *"text Quake Tribute got a space like TRI BUTE and the fonts is horrible... it is also not correcting melting with the clip please lookup how agent do in 2026 and fix"*.
- Font: `phase1/assets/fonts/BebasNeue-Regular.ttf` (Google Fonts OFL build, 61 KB, verified magic `\x00\x01\x00\x00`). Impact is retired — its letter widths vary 0.35–0.75 × fontsize, which broke the v6 per-char x estimator.
- **Typewriter rule:** render with a single `drawtext` per reveal step using `text=QUAKE%{if(gte(t,1.2),\ TRIBUTE,)}` style growing-substring — NEVER per-character concatenation with computed x. The v6 "TRI BUTE" bug was per-prefix centering; the v8 bug was Impact's variable advance widths. Bebas Neue is a monospaced-cap display face that fixes both.
- Fixed left-anchor x: compute `x = (W - final_text_w) / 2` ONCE using the FINAL full string width (ffprobe it from the font), then hold that x constant across all reveal steps. No `x=(w-text_w)/2` per-frame (that was the v6 jitter).
- **Integration with backdrop** (no more black rectangle feel): filter chain is `[backdrop][text]overlay` where `[text]` is `split=2[a][b]; [a]gblur=sigma=18[glow]; [glow][b]blend=all_mode=screen`. Gives the halo ("melting into clip"). Plus `y=H*0.55 + sin(t*2)*3` for a 2 px sine drift so text doesn't look pasted.
- Border stays (`borderw=4:bordercolor=black@0.9`) for legibility on bright FL frames.
- Implementation: `phase1/title_card.py` rewritten in v9; smoke test renders a 2-frame grab (t=0.3 and t=2.5) into `docs/visual-record/YYYY-MM-DD/title_card_smoke_partNN.png` per Rule VIS-1.

### Rule P1-Y v2: Quake-Style Title Card (REVISED Part 4 v9 review 2026-04-18)
**Upgrade the v9 Bebas card to a genuine Quake 3 Arena aesthetic — metallic red/gold fill, triple-layer 3D depth, scanlines, chromatic aberration on reveal, scale-punch per character, final-flash beat.**
User verdict: *"please use quake style and a little more effort in the text"*.
- **Two-font hierarchy**: hero word (`QUAKE TRIBUTE`) uses a chunkier OFL display face (candidate: **Black Ops One**, **Russo One**, or **Bungee Inline** — pending user pick). Subtitle (`Part N`, `By Tr4sH`) stays Bebas Neue.
- **Metallic Q3A fill**: warm off-white base `#f5e8c8` + masked vertical gradient red `#8a0a0a` → gold `#d4a04a` via `geq` on luma-keyed text channel.
- **Triple-layer 3D slab**: (L1) black shadow offset +6/+6 σ=3 = weight, (L2) red inner glow `split→colorize=red→gblur σ=18→screen` = Quake rim heat, (L3) white core with `borderw=8:bordercolor=black@0.95`.
- **Scanlines**: 8% opacity horizontal scanline overlay via `geq='if(mod(Y,3),lum(X,Y),lum(X,Y)*0.85)'`. CRT/arcade feel.
- **Chromatic aberration on reveal**: during the 1.5 s typewriter, split RGB, offset red +2 px / blue −2 px. Settles to 0 px by t=2.0 s.
- **Scale-punch per character**: each letter lands with a 1.15× → 1.0× overshoot over 80 ms. Combines with typewriter reveal — letters *hit*, don't crawl.
- **Final flash**: on last char of `QUAKE TRIBUTE`, one-frame full-screen white at 30%, then cut to black-red vignette. Weapon-pickup energy.
- **"Part N" glitch**: 200 ms `rgbashift` stutter on entry (damage-indicator feel).
- **"By Tr4sH" underline bar**: thin red bar draws L→R over 400 ms under the credit.
- **Backdrop override**: `render_title_card(..., backdrop_paths=[single_clip])` now accepts one explicit clip (for Q2 case where `Demo (389INTRO)` replaces the auto-discovered FL pool). Backdrop filter bumps to `hue=s=0.25, eq=brightness=-0.22:contrast=0.95, gblur=sigma=4, vignette=PI/4`.
- **Smoke test** (VIS-1): 5 frame grabs at t=0.3, 1.0, 2.0, 4.0, 6.5 into `docs/visual-record/YYYY-MM-DD/title_card_quake_smoke_partNN.png` before render ships.

### Rule P1-G v5: Music Starts After PANTHEON, Proper Fade-In (REVISED Part 4 v9 review 2026-04-18)
**PANTHEON intro is music-silent — only its own soundtrack plays. Music enters on title-card start with a 1.5 s fade-in. Body = game audio 1.0 + music 0.20 (P1-G v4 retained).**
User verdict: *"why you use 15sec of a full song and swap to another with no fade ... for the beginning we wait the pantheon opening without the music it should start after"*.
- PANTHEON 0–5 s: audio = IntroPart2.mp4's own soundtrack, zero music mix. Supersedes the P1-G v3 "music layers across PANTHEON" rule.
- Title card 5–13 s: music fades in from 0 → 0.20 over 1.5 s (`afade=t=in:st=0:d=1.5`). No game audio yet (title card has no gameplay sound).
- Body 13 s+: game audio 1.0 + music 0.20, sidechain-ducked (see P1-AA).
- `render_part_v6.py::final_render()` audio graph must build three segments (pantheon-with-own-audio | title-with-music-fadein | body-with-game+ducked-music) and concat, NOT amix-over-all.

### Rule P1-Z v2: Action Peak = Recognized Game Event, Not Loudest Onset (REVISED beat-maker brainstorm 2026-04-18 eve)
**Alignment target = each clip's strongest RECOGNIZED game event (rail fire, rocket fire/impact, grenade throw+3s+explode, player death, LG hit). NOT the loudest amplitude. Matched against a QL sound template library.**
User verdict: *"the peak should be recognicable pattern, one rail shot one rocket shot one grenade shot ... loudest dosnt mean accurate"*.
- `phase1/audio_onsets.py` rewrites `find_action_peak` → `recognize_game_events(clip_wav)` returning `list[{t, event_type, confidence, weight}]`.
- Matcher = template cross-correlation (MFCC + spectrogram fingerprint) against `phase1/sound_templates/` library.
- Event weight table (initial, tunable):
  - `player_death`       = 1.0  (the kill IS the frag)
  - `rocket_impact`      = 0.95
  - `rail_fire`          = 0.90 (rail crack is THE Quake signature)
  - `grenade_explode`    = 0.90
  - `rocket_fire`        = 0.70
  - `lg_hit`             = 0.60 (one hit marker; stream of hits → use last)
  - `grenade_throw`      = 0.40 (use for 3s-fuse pattern not solo)
  - `plasma_hit`         = 0.55
  - `shotgun_fire`       = 0.50
  - others               = 0.30
- **Grenade 3-second-fuse pattern**: when `grenade_throw` at t_a and `grenade_explode` at t_a + (2.5..3.5)s co-occur in a clip, treat as ONE compound event "grenade_direct". Action peak = t_explode. The silence between throw and boom is itself a beat-match hook (drop a downbeat on the explosion).
- **Player death is THE high-value event**: if a clip has a player_death, it wins over any weapon event. The frag IS the kill.
- Action peak = `argmax(weight × confidence)` across recognized events, NOT argmax(amplitude).
- If NO event recognized (confidence < 0.4 everywhere), fall back to v1 loudest-onset detection + tag `RECOGNITION_FAILED`.
- Shift absorbed by trims (±400 ms cap, bounded by `min_playable_duration_s = 2.0`). Supersedes P1-Z v1 "loudest onset".
- Logs `partNN_beats.json`: `[{clip, action_peak_t, event_type, confidence, target_downbeat, shift, tag}]`.

### Rule P1-DD: QL Sound Template Library (NEW beat-maker brainstorm 2026-04-18 eve)
**Every game-audio event Phase 1 cares about has a reference template extracted from Quake Live `pak00.pk3`. Library lives at `phase1/sound_templates/` and is the single source of truth for both Phase 1 action-peak recognition AND Phase 2 demo-audio event labeling.**
User verdict: *"use the quake file to extract the rocket sound and the rail sound and all other sound so you can map everything to the .wav ( this is another big idea for our real demo extraction phase add it too )"*.
- **Source**: `C:\Program Files (x86)\Steam\steamapps\common\Quake Live\baseq3\pak00.pk3` (READ ONLY per ENG-1).
- **Extraction scope**: `sound/weapons/**`, `sound/player/**death|gasp|pain|jump|land*`, `sound/misc/**telein|teleout|quad|powerup*`, `sound/items/**pickup|health|armor*`, `sound/feedback/**`, `sound/world/**` (capped).
- **Normalization**: every .ogg transcoded to PCM WAV 48 kHz mono 16-bit via ffmpeg. Originals preserved.
- **Manifest**: `phase1/sound_templates/manifest.json` categorizes by path → `event_type` with duration + RMS per file.
- **QL ONLY**: all our demos are QL — Q3A variants deferred. Revisit if we ever ingest Q3A demos.
- **Consumers**:
  - Phase 1: `audio_onsets.py` template-matching for clip action peaks.
  - Phase 2: demo-extractor correlates demo audio against library to label frames with game events independently of `.dm_73` entity parsing.
- **Dual-use gate**: this library is the bridge between Phase 1 (already here) and Phase 2 (to come). Any Phase 2 demo extraction that does NOT use this library is doing the same work twice.

### Rule P1-Z v1 (SUPERSEDED — kept for history): Beat-Sync Runs on GAME Audio Onsets, Not Seam Timing
**Alignment target = each clip's LOUDEST action transient (rocket hit, rail crack, LG kill pop) lands on the nearest music downbeat. The seam between clips is *derived* from this, not the other way around.**
User verdict: *"please review how beat making work with the AUDIO of the game clip and match with this, DO NOT base on the clip length or video ... when you watch the video there is no beat at all attached to the action rhythm"*.
- `phase1/audio_onsets.py` (new): `find_action_peaks_per_clip()` — librosa onset detection on game audio with `backtrack=True`, pre-emphasis HPF (kills LG hum), `pre/post_max=20`, `delta=0.3`, `wait=30`, peak = loudest onset not first. Accuracy ~5 ms at hop=256.
- `phase1/beat_sync.py` rewrite: input = (clips with peaks, music downbeat grid), output = per-seam trim adjustments so each clip's action_peak lands on nearest music downbeat.
- **Shift absorbed by trims**, never by speed changes: `head_trim[i] += min(shift, 0.4)` or `tail_trim[i-1] += min(-shift, 0.4)`, bounded by `min_playable_duration_s = 2.0` (P1-L v3).
- Max shift: ±400 ms. Beyond that → tag `WEAK_ALIGN` in `output/partNN_beats.json` and use nearest half-beat instead.
- Logs `partNN_beats.json`: `[{clip, action_peak, target_downbeat, shift, tag: TIGHT|WEAK_ALIGN|SKIP_ALIGN}]`.
- Research source: `docs/research/audio-montage-2026-04-18.md` §B, §C.

### Rule P1-AA v2: Video is Source of Truth, Song Transitions are Beat-Matched DJ Mixes (REVISED beat-maker brainstorm 2026-04-18 eve)
**Video body duration rules. Middle tracks play in full; LAST track may truncate at a phrase boundary to match video end. No padding video to meet music, no looping a truncated tail. Song seams are DJ-style beat+phrase matches, not fades.**
User verdict: *"video is the source of truth we dont extend video because audio is too long, we can shorten song for better beatmatch and fitting in the video ... couldnt we beatmatch the songs so the transition can also be seamless ?"*.
- **Queue sizing**: music_stitcher computes `body_duration` first (from clip list + seam xfades), then picks N tracks where `sum(track_i.full_duration for i < N)` < body_duration and `sum(track_i.full_duration for i < N+1)` ≥ body_duration. Last track is truncated at the nearest **phrase boundary** (from `sections[]`) ≤ body_duration. Never truncate mid-bar.
- **Seam strategy — beat + phrase match, not crossfade**:
  1. For each pair (A, B), find an 8- or 16-bar phrase boundary in A within 4–12 s of A.full_duration (from msaf sections).
  2. Find the matching incoming phrase boundary in B (typically start of a `build` or `drop` section).
  3. If `|BPM_A - BPM_B| ≤ 3`, overlap 8 bars with both tracks on-beat. No time-stretch.
  4. If `|BPM_A - BPM_B| ≤ 8`, time-stretch B's first 8 bars to BPM_A via `rubberband` (pitch-preserving) for the overlap window only.
  5. If `|BPM_A - BPM_B| > 8`, either (a) reject the pair and try a different B, or (b) fall back to a long `afade` crossfade (4–6 s) — flagged `BPM_MISMATCH` in `music_plan.json`.
  6. Optional 500 ms high-pass sweep on the last bar of A as a transform FX.
- `acrossfade` chains still BANNED (drift). Each seam gets its own explicit afade pair (or overlap for beat-matched seams).
- **Sidechain ducking** on body (not seams): music ducks ~6 dB under every recognized high-weight game event via `sidechaincompress`. See `phase1/sidechain.py`.
- **`music_plan.json` ship gate (REVISED)**: every entry's `duration == full_duration ± 0.1 s` EXCEPT the last, which may have `duration < full_duration` iff `truncation_boundary == phrase_boundary`. Mid-bar truncation = hard fail.
- Pool naming: `phase1/music/partNN_main_{1,2,…}.mp3`.

### Rule P1-EE: Event-Localized Speed Effects (NEW beat-maker brainstorm 2026-04-18 eve)
**Slow-mo, speed-up, and pitch effects apply to a WINDOW around the recognized event peak — typically ±0.8 s — never to the whole clip. Time-stretched audio in the slow window is replaced with pitched-up original speed audio OR natural-speed audio at lower volume, because pitch-preserving time-stretch stutters.**
User verdict: *"use the slowmo as velocity and dont slow the shole video to the whole clip but just for the peak of the action same for speed up or thing like this, also slowmo audio is kinda stutering too much!"*.
- Prerequisite: Rule P1-Z v2 (recognized event peak with confidence ≥ 0.55). No peak = no effect.
- **Slow-mo window**: default `event_peak ± 0.8 s` = 1.6 s of slowed video at `slow_rate=0.5`. Ramps in/out over 100 ms (velocity feel).
- **Speed-up window**: default `event_peak - 1.5s` to `event_peak - 0.3s` (speed up the boring setup, land natural-speed on the event).
- **Audio handling in slow window** (fixes stuttering):
  - **Option A (default)**: mute slow window entirely, crossfade 100 ms at window edges. The music carries the rhythm; event sound is replayed at natural speed in a replay beat if rule P1-Q triggers.
  - **Option B**: `atempo=2.0` on the slow segment = audio plays at 2× (compensates for 0.5× video) = audio stays at natural speed while video slows. Audio becomes "natural sounding during slow-mo".
  - **Option C**: natural-speed audio at 60% volume under slow video = "dream state" effect.
- Default is Option B for weapon events (preserves rail crack / rocket boom), Option A for player_death (reverb-heavy sound stretches badly), Option C for multi-kill compounds.
- Ramp filter (video): `setpts='if(between(T,WIN_START,WIN_END), PTS + (WIN_START-T)*(1-RATE) + (T-WIN_START)*(1-RATE)/DUR, PTS)'` — linear time-stretch inside window, identity outside.
- **Replaces blanket `slow=<rate>` override in `partNN_overrides.txt`**: `slow` override now means "apply event-localized slow around the recognized peak", NOT "slow the whole clip". Grammar addition: `slow_window=<seconds>` to override the ±0.8 s default.
- Supersedes previous whole-clip `setpts=(1/slow)*PTS + atempo=slow` behavior in `render_part_v6.py::build_body_chunks`.

### Rule P1-AA v1 (SUPERSEDED — kept for history): Full-Track Music Queue + Explicit-afade Crossfades
**Every music seam is a beat-matched long crossfade (4–6 s), computed per track pair with explicit `afade` filters. `acrossfade` chains are BANNED — they compound drift.**
User verdict: *"why you use 15sec of a full song and swap to another with no fade no transition no mix in and no mix out this is bad ... Also regarding the music it looks like the song are cutting shortly we could save some usage same issue as intro"*.
- `phase1/music_stitcher.py` rewrite: queue N full tracks whose combined duration ≥ body + fade budget. Each track plays to its natural end minus 6 s; next track enters on its first downbeat at the 6 s mark. 4–6 s crossfade exposes both tracks' downbeats simultaneously.
- Filter graph per pair (from §E of research brief):
  ```
  [A]afade=t=out:st={fadeout_start}:d={xfade}[Afaded];
  [B]atrim=start={B_first_downbeat},asetpts=PTS-STARTPTS,
     afade=t=in:st=0:d={xfade},adelay={fadeout_ms}|{fadeout_ms}[Bfaded];
  [Afaded][Bfaded]amix=inputs=2:duration=longest
  ```
- `music_plan.json` (ship gate): every entry must have `duration == track.full_duration ± 0.1 s`. Truncated tails = hard fail.
- **Sidechain ducking** on top: music stream ducks ~6 dB under every game transient via `sidechaincompress=threshold=0.05:ratio=8:attack=5:release=250`. See `phase1/sidechain.py` (new).
- Pool naming: `phase1/music/partNN_main_{1,2,…}.mp3` for multi-main, intro/outro unchanged.
- Research source: `docs/research/audio-montage-2026-04-18.md` §D, §E.

### Rule P1-CC v2: Flow-Driven Cut Placement, Tier is Ordering Hint (REVISED beat-maker brainstorm 2026-04-18 eve)
**Beat-sync consumes structural music analysis. Tier is a SORT KEY, not a HARD GATE — any tier can land on any cut candidate if the flow requires it. A T3 action on a drop becomes T1 to the viewer.**
User verdict: *"music is not bound to tier, its bound to flow, having the perfect drop on a t3 action can make it t1 for the watcher so the tiering is not a HARD rule for the beatmatch"*.
- Flow planner walks `sections[]` of the music and picks clips per section based on **section shape**, not clip tag:
  - `build` sections → T3 atmospherics + slow FLs (earn the drop)
  - `drop` sections → whatever clip has a `player_death` or `rocket_impact` event closest to the drop timestamp
  - `break` sections → longest full-length clip with downtime (lets viewer breathe)
  - `outro` → tail frags, T1 reserved last
- Tier preference only applies when two clips tie on flow fit: T1 wins, then T2, then T3.
- One T1 per drop is still preferred but not enforced.
- Supersedes P1-CC v1 hard mapping.

### Rule P1-CC v1 (SUPERSEDED — kept for history): Downbeat + Phrase + Drop-Aware Cut Placement
**Beat-sync consumes structural music analysis, not raw beat grid. T1 frags pin to drops, T2 to strong downbeats, T3 fillers to medium. Cuts are anticipation-offset −33 ms (2 frames @ 60 fps) so the visual peak lands ON the beat, not the cut.**
User verdict: *"also review beatmaker and update knowledge for best results"*.
- `phase1/music_structure.py` (new): runs Beat This! (ISMIR 2024 SOTA, `pip install beat_this`) on the stitched music WAV to get beats + downbeats; madmom DBN as CPU fallback. Plus `msaf` for phrase segmentation (intro/build/drop/break/outro), custom sub-200 Hz RMS novelty for drop detection, per-downbeat salience ranking `max(onset_env[±50ms]) × (0.5 + 0.5 × kick_energy)`.
- Output artifact: `output/partNN_music_structure.json` with `bpm_global`, `beat_grid`, `downbeats[].salience`, `sections[]`, `drops[].strength`, `cut_candidates.{strong,medium,soft}`.
- `phase1/beat_sync.py` consumer rewrite: tier → candidate pool mapping:
  - **T1 frags** pin to `drops[]` (salience ≥ 0.80 or explicit drop), one per drop max.
  - **T2 frags** to `cut_candidates.strong` (salience ≥ 0.55).
  - **T3 fillers** to `cut_candidates.medium` (salience ≥ 0.30).
- **Anticipation cut** at seam-render time: `seam_cut_time = target_downbeat - 0.033` (60 fps). Logged per seam as `offset_ms: -33` in `partNN_beats.json`.
- **Ghost downbeats** (sidechain duck moments on game explosions) use hit-on-beat (0 offset) — already visually sync'd by the duck itself.
- Visual record: `docs/visual-record/YYYY-MM-DD/partNN_music_structure.png` = waveform + beat grid + downbeats + drops overlay.
- Research source: `docs/research/beatmaker-2026-04-18.md` §B–§F.

### Rule P1-BB: Split Video/Audio Graphs, PCM WAV Intermediates (NEW Part 4 v9 review 2026-04-18)
**Body assembly uses TWO parallel ffmpeg graphs — video via `xfade`, audio via `concat + afade`. Intermediate chunks encode audio as PCM WAV, never AAC. This is the root-cause fix for the 3:25 drift that survived per-chunk PTS reset.**
User verdict: *"3.25 the game audio is drifting again you have a delay ... Also please do your research on how the audio work for the montage as we stop having these issues"*.
- **Why `asetpts=PTS-STARTPTS, aresample=async=1:first_pts=0` didn't fix it**: (a) AAC priming delay (~1024 samples per intermediate) survives PTS reset; (b) `xfade` filter has an implicit audio timeline that ffmpeg auto-re-times with different math than video. Known ffmpeg tickets #9248, #10229.
- **Fixes (all ship together)**:
  1. Intermediate chunks → PCM WAV audio (`-c:a pcm_s16le`), final render transcodes to AAC once.
  2. Force CFR on ingest: `-vsync cfr -r 60` BEFORE any filter (Wolfcam AVIs can be VFR).
  3. `amix=duration=first` (music drives duration), explicit `apad` on game to match. Never `duration=longest`.
  4. Split graphs: video `xfade` chain + separate audio `concat=v=0:a=1` + `afade` pairs at seams. Mux at the end.
- **Audit after each render**: ffprobe the final mp4, compare `v:0` and `a:0` durations at intervals (1min, 3min, 5min). Report into `output/partNN_sync_audit.json` with per-minute drift in ms. Ship gate: `max_drift_ms <= 40`.
- Research source: `docs/research/audio-montage-2026-04-18.md` §F.

### Rule P1-G (legacy — superseded by P1-G v4): Audio Mix — Game Foreground, Music Halved (REVISED Part 4 review 2026-04-17)
**Kept for history. See P1-G v3 above.**
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

### Rule P1-T: Title Card is FL-Backdropped, Never A Black Void (NEW Part 4 v6 review 2026-04-18)
**User verdict:** *"intro is a disaster please use unused fl view and look up how the text appear its overlaying black fint cant read anything."*
- The 8-second title card (Rule P1-N) renders its text **over desaturated FL gameplay**, not over a black screen.
- Backdrop pool: `pick_intro_backdrop_fls(part, cfg)` in `phase1/title_card.py` walks `QUAKE VIDEO/T{3,2,1}/Part{N}/**/*FL*.avi` (T3 first per Rule P1-B), deterministically shuffles, and returns the first 4 candidates.
- Backdrop filter: `hue=s=0.5, eq=brightness=-0.12:contrast=0.85, gblur=sigma=2` — soft, muted, legible beneath white Impact text.
- Title text gets `borderw=4:bordercolor=black@0.9` so letters stay sharp against any backdrop brightness.
- Trailing fade-to-black at card end is **banned** (was the "black video" artifact in v6). Credit holds until card end, pipeline hard-cuts into the first clip (consistent with Rule P1-H).
- Typewriter reveal for `QUAKE TRIBUTE` uses **fixed left-anchored x per character** — NOT `x=(w-text_w)/2` per prefix. The v6 bug stacked all 13 growing prefixes at the same midpoint, producing unreadable hash.
- Fallback: if no FL files exist for the Part, fall back to black lavfi (warning logged).

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

Ghidra FT-4 sandbox committed (`game-dissection/ghidra/`) with preliminary inventory. **Full dissection blocked on:**
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
