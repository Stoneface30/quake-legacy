# Part 5 v6 — New-Rules Baseline Render (2026-04-18)

**Output:** `output/Part5_v6_newrules_2026-04-18.mp4`
**Size:** 8.12 GB
**Duration:** 1503.75 s (25 min 4 s)
**Encoder:** AV1 NVENC, preset p7, tune uhq, 10-bit (p010le), cq=18
**Render time:** 15.6 min

## Rules applied

Same rule matrix as Part 4 (P1-C, P1-N, P1-G, P1-H, P1-K, P1-L, P1-O, P1-P, P1-R, P1-S).
See `../part4-v6-newrules/README.md` for the full table.

## Music plan (Rule P1-R)

- Intro: `pantheon_intro_music.mp3`, 15 s window
- Main playlist: `part05_music_01..06.mp3` (Phonky Tribu Funk Tribu phonk, 1758 s total)
- Outro: `pantheon_outro_music.mp3`, 30 s tail
- Coverage verdict: **PASS** (1758 s available vs 1464 s needed) → no tail-loop required.
- Stitched track: `phase1/music/_stitched/part05_stitched_37a9b91524f2def9.mp3`

## Body chunks

Built fresh from `phase1/clip_lists/part05_styleb.txt` (130 segments after FP+FL expansion)
via `phase1/build_part5_chunks.py`. Stored at `output/_part05_v6_body_chunks/`
(libx264 CRF 20 preset fast intermediates, 1 s head / 2 s tail trim per Rule P1-L).

## VIS-1 frames

- `part5_t0s.jpg`      — PANTHEON logo first frame
- `part5_t7s.jpg`      — Title card reveal
- `part5_t15s.jpg`     — Body start (first frag)
- `part5_t60s.jpg`     — 1-minute checkpoint
- `part5_t75188s.jpg`  — midpoint (751.88 s)
- `part5_t147375s.jpg` — end − 30 s (1473.75 s)

## Known compromises / flags

None. Music PASS verdict, fresh chunk build, AV1 NVENC succeeded on first try.
