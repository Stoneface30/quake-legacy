# Part 4 v6 — New-Rules Baseline Render (2026-04-18)

**Output:** `output/Part4_v6_newrules_2026-04-18.mp4`
**Size:** ~9.17 GB
**Duration:** 1741.3 s (29 min 1 s)
**Encoder:** AV1 NVENC, preset p7, tune uhq, 10-bit (p010le), cq=18
**Render time:** 20.4 min (Blackwell RTX 5060 Ti, NVENC gen-9)

## Rules applied

| Rule | Applied |
|---|---|
| P1-C  PANTHEON 7 s prepend | Yes — `_pantheon_trim_7s.mp4` |
| P1-N  Title card 8 s (QUAKE TRIBUTE / Part 4 / By Tr4sH) | Yes — `phase1/assets/title_card_part04.mp4` |
| P1-G  Music 0.5, game 1.0 (amix normalize=0) | Yes — applied to body only (PANTHEON + title keep own audio) |
| P1-H  Hard cuts only | Yes — single concat demuxer join, no xfade/fade-to-black |
| P1-K  FP backbone + ONE FL 0.5× slow contrast | Honored by `part04_styleb.txt` expansion |
| P1-L  Clip trim 1 s head / 2 s tail | Baked into chunk encodes |
| P1-O  Continuous music coverage | Yes — stitched to 1743 s (2 s tail pad) |
| P1-P  Full-length clip contract | Yes — chunks play full post-trim duration |
| P1-R  Three-track music (intro + playlist + outro) | Yes — `pantheon_intro_music.mp3` + `part04_music_01..05.mp3` + `pantheon_outro_music.mp3` |
| P1-S  Beat-sync never shortens clips | Yes — stitcher only snaps crossfade joins |

## Music plan (Rule P1-R)

- Intro: `pantheon_intro_music.mp3` (Cinema — Sped Up — JKRS), 15 s window
- Main playlist: `part04_music_01..05.mp3` (MAKEBA techno-crossover, 960 s total)
- Outro: `pantheon_outro_music.mp3` (Eple — Badger), 30 s tail
- Coverage verdict: **INSUFFICIENT** for raw coverage (960 s < 1702 s main needed) →
  stitcher loops the tail track (`part04_music_05.mp3`) with 0.5 s crossfade.
- Final stitched track: `phase1/music/_stitched/part04_stitched_9318fbf213b7baa8.mp3`, 1750.5 s.

## Body chunks

Reused 132 existing chunks from `_part4_v5_body_chunks/` (built in v5 render 2026-04-17 using
the same trim+scale parameters — semantically identical to a fresh v6 build).

## VIS-1 frames

- `part4_t0s.jpg`      — PANTHEON logo first frame
- `part4_t7s.jpg`      — Title card reveal
- `part4_t15s.jpg`     — Body start (first frag)
- `part4_t60s.jpg`     — 1-minute checkpoint
- `part4_t87066s.jpg`  — midpoint (870.66 s)
- `part4_t171132s.jpg` — end − 30 s (1711.32 s)

## Known compromises / flags

- **Body duration 28.77 min vs 14.5 min estimate** — existing v5 chunks are longer than
  the user-expected Part length. The chunks were built with per-segment trim (1 s head /
  2 s tail) but the clip list has 107 entries expanding to 132 segments, and individual
  clips are longer than the original estimate assumed. Not a rule violation — just a note.
- Music coverage gap: 742 s deficit forced tail-track looping 5× with 0.5 s crossfade.
  This satisfies Rule P1-O but a future Part 4 remix may want a longer main playlist.
