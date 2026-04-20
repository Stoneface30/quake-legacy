# Part 4 Review — 2026-04-17 (user verdict + rule changes)

Hard feedback from the user after watching Part 4 Style B (NVENC final render,
4.2 GB, rendered 2026-04-17 17:58). This document is the authoritative
translation of that feedback into pipeline rules. Every item below is a HARD
RULE — no more negotiation on these points.

---

## 1. Audio mix — music -50%, game sound kept

**User quote:** *"lower music by 50% keep game sound"*

- Music track volume: **halve it** before the amix node (0.5× pre-gain).
- Game audio volume: keep full (`game_audio_volume = 1.0`).
- Net effect: music sits behind game audio, which is the opposite of the
  previous mix where game audio sat under music.
- Rationale: grenade hits, rocket impacts, rail cracks define Quake's sport
  texture. Music is atmosphere, not foreground.

**Rule P1-G is superseded.** New mix:
```
music_volume      = 0.5
game_audio_volume = 1.0
```

## 2. Transitions — NONE. Zero. Hard cuts only.

**User quote:** *"no fucking transition not even a fading to the next image or
anything"*

- `xfade_duration = 0.0`
- Every cut is a plain concat join.
- `TransitionPlanner` becomes a no-op for Phase 1 — keep the class file for
  later but all `plan()` calls return `HARD_CUT` unconditionally.
- No section fades, no white flash, no dip-to-black, no cross-dissolve.
- We will design a transition palette LATER when we work on our pattern
  database. Phase 1 ships with pure hard cuts.

**Rule P1-H is superseded.** New rule: *all inter-clip joins are hard cuts in
Phase 1. Pattern-database-driven transitions are Phase 2.*

## 3. Clip trimming — 1s head, 2s tail, keep everything else

**User quote:** *"we can just cut the first second and the 2 last second for
the transition effects"*

- Head trim: **1.0s** (was 2.0s)
- Tail trim: **2.0s** (was 1.5s)
- Transition envelope: **0s** (was 1.0s — irrelevant now that transitions are gone)
- Beat-sync may NOT shorten a clip beyond these trims. If beat doesn't land,
  we use the clip-end slow-mo effect (see §5) to stretch, we do not truncate.

**Rule P1-L superseded** with new trim values. Beat-sync constraint becomes:
`duration ∈ [raw_length - 1.0 - 2.0, raw_length - 1.0 - 2.0]` (fixed length
post-trim). Variance comes from speed-ramping, not truncation.

## 4. Multi-angle handling — FP backbone + 1 FL as effect (NOT 4-angle ping-pong)

**User quote:** *"the FPV its absolutly terrible they swap back and forth in a
terrible order, you should focus on keeping the main pov and use 1 of the FL
video files you can slomo the main and the other for the effect"*

- Multi-angle groups are no longer FP → FL1 → FL2 → FL3 → FP.
- New pattern: **main FP is the spine. At most ONE FL cuts in, used as an
  effect contrast (slow-mo the main ↔ FL, or normal FP ↔ slow FL).**
- The other FL sources in a multi-angle dir are NOT played this Part. They
  may be used in later Parts or in effect-variety patterns.
- Inter-FL ping-pong within one frag is banned.
- Choice of which FL to pair with the FP: pick the one with the biggest
  angle delta from FP (typically a `side/` or `top/` label in the subdir).

**Rule P1-K is superseded.** New pattern (FP-dominant slow-mo contrast):
```
  0% → 40%  FP normal speed    (setup)
  40% → 65% FL slowmo 0.5×     (replay of the same moment, contrast angle)
  65% → 100% FP normal speed   (confirmation / follow-through)
```
Cuts inside the group remain hard cuts. No ping-pong.

## 5. Effect — replay-speed contrast for short T1 clips

**User quote:** *"good effect on really short T1 clip is to play it slow once
replay it normal speed, or the other way around"*

- New effect: `REPLAY_SPEED_CONTRAST`
- Behavior: for a short T1 clip (raw length < ~3.0s after trim), play it
  once at 0.5× speed then once at 1.0× speed (or 1.0× → 0.5× — planner
  chooses based on beat position).
- Add to `phase1/effects.py` as a first-class effect type alongside slow-mo,
  speed ramp, zoom punch, desat flash, beat pulse.

**Task:** research agent (offline) should survey YouTube fragmovies and
propose additional replay-style effects. Document findings in
`docs/research/effect-catalog-expansion.md`.

## 6. Filler misunderstanding — every clip plays its full post-trim length

**User quote:** *"a lot of the clip you do in quick succession are just
showing half a second of a totally unrelated clip, i think you did not
understand what a filler was, in this step with all the clips we need to keep
ALL the original clip length"*

- There are no 0.5s clip fragments. Every clip that enters a Part plays its
  full post-trim duration (raw − 1.0s head − 2.0s tail).
- T3 "filler" means **atmospheric full-length establishing shot**, not
  "tiny cutaway". T3 clips are slower, more cinematic — they set scene.
- The quick-swap pattern previously used on T3 is deleted.

**New Rule P1-P: Full-Length Clip Contract.** A clip in a Part occupies the
screen for its full post-trim duration. No sub-clip fragmenting.

## 7. Quick-swap → migrate to FL beat-effect only

**User quote:** *"the quick clip swap you use with t3 should be used with FL
views that could be a nice beat effect if you really want to use it"*

- The "rapid cuts" idea survives — but only inside a multi-angle group as
  a beat-locked micro-cut between FP and ONE FL (16th-note rate max).
- Never between unrelated clips (that was the Part 4 failure mode).

This is a Phase 2 effect, not a Phase 1 default. Flag it in
`phase1/effects.py` as `FL_BEAT_STUTTER` but gate it off by default.

## 8. Music coverage — end-to-end, no silence

**User quote:** *"the music stop when tis over and there is not another one
who take over, beatmaker and pipeline should be with music from after the
intro until the outro"*

- If a Part's total runtime exceeds the music track's length, the pipeline
  MUST queue a second track (or loop with beat-matched stitch) so music
  plays from **end of title intro** through **start of outro**.
- Outro credits (generated) are a future add. Spec'd in §9.
- Implementation: `pipeline.py` amix node should accept a list of music
  tracks; when one ends, the next fades in seamlessly (0.5s crossfade on
  music stream only — video stream stays hard-cut).

**New Rule P1-O: Music Coverage Contract.** Music audio is continuous from
title intro end to outro start. Silence gaps are a failure mode.

## 9. Title intro — CRITICAL gap

**User quote:** *"you did not create the intro of the video, we have our
trademark but not the title, no Quake Tribute, no By Trash no number no slowmo
with the letters this is critical for final product!"*

Current intro = PANTHEON logo only (first 7s of IntroPart2.mp4). Missing:
- "QUAKE TRIBUTE" title text
- "Part N" label
- "By Tr4sH" credit
- Slow-mo animated letter reveal

Target sequence (to build):
```
  0s  → 7s   PANTHEON logo (existing IntroPart2.mp4 first 7s)
  7s  → 10s  "QUAKE TRIBUTE" letter-by-letter slowmo reveal (white on black,
             bold Impact-style font, motion-blurred entry)
  10s → 12s  "Part N" number reveal (big number, kerning-wide)
  12s → 14s  "By Tr4sH" credit (smaller, bottom-right)
  14s → 15s  Fade title block to black → content begins
```

**Implementation plan (separate task — spawn):** title-card generator
module `phase1/title_card.py` using ffmpeg `drawtext` + `zoompan` +
`geq` filters. Render to `phase1/assets/title_card_partNN.mp4` once per
Part, concat after PANTHEON logo, before first clip.

**New Rule P1-N: Title Card Contract.** Every Part intro sequence is
[PANTHEON 7s] + [Title Card 8s] + [Content]. No exceptions.

## 10. Sort / rename / organize / de-duplicate the clip library

**User quote:** *"sort the video clip as you like (you can rename them sort
them in video parts and organize the output folder (delete outdated video)
Also delete all duplicates."*

- Full authority to reorganize `QUAKE VIDEO/T{1,2,3}/PartN/` contents.
- Rename conventions: Claude-chosen, but must be stable and grep-friendly.
- De-duplicate: SHA-256 on file bytes, keep earliest-modified, delete the rest.
- Outdated output videos in `output/` and `output/previews/`: flag and delete.

**Spawned as separate task** — see `docs/superpowers/plans/` at commit time.

## 11. Demo drive organization

**User quote:** *"I copied all the demo here: G:\QUAKE_LEGACY\WOLF
WHISPERER\WolfcamQL\wolfcam-ql\demos ... Regarding the demos you have full
permission to skin the drive and archive 7z files, [I'd] like to have my demo
in one place and all the duplicate removed."*

- Full authority to walk the entire G: drive, locate all `.dm_73` files,
  de-duplicate by SHA-256, consolidate into `G:\QUAKE_LEGACY\demos\`.
- Archive source directories (after dedup) into per-source `.7z` files
  under `G:\QUAKE_LEGACY\demos\_archive\`.
- Spawned as separate task.

## 12. Wolfcam exit — knowledge extraction mandate

**User quote:** *"if we leave wolfcam we will need to cleanup our repo from it
meaning we need to extract all the knowledge from it and ingest it in our
dissector."*

Before wolfcamql source is removed from the repo, extract:
- Every cvar and console command from `wolfcam_consolecmds.c`,
  `wolfcam_cvars.c`, and related files
- Every protocol-73 patch delta vs stock Q3 (for Tr4sH Quake engine port)
- Every fragmovie-relevant quirk documented in source comments
- IPC command set exposed to WolfWhisperer.exe

Destination: `engine/wolfcam-knowledge-ingest/` with a structured
markdown report per subsystem. Then wolfcam can be retired.

**Spawned as separate task.**

---

## Supersedes / invalidates

| Previous rule | Status |
|---|---|
| Rule P1-G (game audio 0.85 under music) | SUPERSEDED — music 0.5, game 1.0 |
| Rule P1-H (xfade 0.08s hard-cut flash + xfade at sections) | SUPERSEDED — no transitions at all |
| Rule P1-K (FP→FL1→FL2→FL3→FP multi-angle) | SUPERSEDED — FP + 1 FL slow-contrast |
| Rule P1-L (1s head / 1s tail envelope) | SUPERSEDED — 1s head / 2s tail, no envelope |
| `TransitionPlanner` palette | DEAD CODE — planner becomes HARD_CUT-only |
| T3 quick-swap filler pattern | DELETED — fillers are full-length shots |

## New rules added

| Rule | Topic |
|---|---|
| P1-N | Title card contract (PANTHEON + Quake Tribute / Part N / By Tr4sH) |
| P1-O | Music coverage contract (end-to-end, no silence gaps) |
| P1-P | Full-length clip contract (no sub-clip fragments) |
| P1-Q | Replay-speed contrast effect for short T1 clips |

## Gate before re-rendering Parts 4/5/6

1. Config.py updated (audio + trims + transitions)
2. pipeline.py: amix rewired for music 0.5 + game 1.0, multi-music queue
3. TransitionPlanner forced to HARD_CUT
4. Multi-angle group builder rewritten for FP + 1 FL pattern
5. Title card generator module exists and is concatenated into output
6. Music coverage logic implemented (loop or queue second track)
7. Rule P1-P enforced — no sub-clip fragments in the render path
8. Effect `REPLAY_SPEED_CONTRAST` added to `phase1/effects.py`

Only after all 8 green do Parts 4/5/6 re-render. Parts 7-12 first render
direct uses the new rules.
