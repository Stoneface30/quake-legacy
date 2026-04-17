# Part 4 v5 — Title Card Render (2026-04-17)

Post-review render of Part 4 with the full 15-second intro sequence (PANTHEON + Title Card)
and all rules from the 2026-04-17 Part 4 Style B review applied.

## Output

- Path: `G:/QUAKE_LEGACY/output/Part4_v5_titlecard_2026-04-17.mp4`
- Size: **9,610,132,412 bytes (9.61 GB)**
- Duration: **00:29:01.32**
- Resolution: 1920x1080 60fps
- Video codec: **av1_nvenc** (AV1, Main profile, yuv420p10le, BT.709, ~43.8 Mbps)
- Audio codec: aac LC, 48 kHz stereo, 314 kbps

## Render Command

Driver script: `phase1/render_part4_v5_direct.py`

Single-shot ffmpeg with filter_complex:

```
ffmpeg -y \
  -i output/_pantheon_trim_7s.mp4 \
  -i phase1/assets/title_card_part04.mp4 \
  -f concat -safe 0 -i output/_part4_v5_body_chunks/_concat.txt \
  -stream_loop -1 -i phase1/music/part04_music.mp3 \
  -filter_complex "[3:a]volume=0.5[mus];[2:a]volume=1.0[game];\
                   [game][mus]amix=inputs=2:duration=first:dropout_transition=0[body_a];\
                   [0:v][0:a][1:v][1:a][2:v][body_a]concat=n=3:v=1:a=1[vout][aout]" \
  -map [vout] -map [aout] \
  -c:v av1_nvenc -preset p7 -tune uhq -multipass fullres \
  -spatial-aq 1 -temporal-aq 1 -rc-lookahead 32 -b_ref_mode middle -bf 4 \
  -rc vbr -b:v 0 -cq 18 -highbitdepth 1 -pix_fmt p010le \
  -r 60 -g 120 -c:a aac -ar 48000 -b:a 192k -movflags +faststart \
  output/Part4_v5_titlecard_2026-04-17.mp4
```

## Intro Sequence (Rule P1-N)

| Range        | Content                                                 |
|--------------|---------------------------------------------------------|
| 0.0s  → 7.0s | PANTHEON logo (IntroPart2.mp4 first 7s)                 |
| 7.0s → 10.0s | "QUAKE TRIBUTE" letter-by-letter reveal                 |
| 10.0s → 12.0s| "Part 4"                                                |
| 12.0s → 14.0s| "By Tr4sH"                                              |
| 14.0s → 15.0s| Fade title block to black                               |
| 15.0s → end  | Body (103 clip entries / 132 normalized segments)       |

## Rules Applied

- **P1-G revised**: game_audio=1.0, music=0.5 (music sits behind full game audio)
- **P1-H**: HARD CUTS ONLY — xfade_duration=0.0
- **P1-J**: NVENC av1_nvenc cq=18 p7 tune=uhq, 10-bit p010le
- **P1-K**: FP backbone + ONE FL slow-contrast multi-angle (no ping-pong)
- **P1-L**: clip trim 1s head / 2s tail
- **P1-N**: Title card sequence above
- **P1-O**: Music looped (5:46 source × 5 loops covers 29 min body)

## Frame Grabs

| File              | Timestamp | Expected content               |
|-------------------|-----------|--------------------------------|
| frame_0s.png      | 0s        | PANTHEON logo opening          |
| frame_3s.png      | 3s        | PANTHEON mid-reveal            |
| frame_7s.png      | 7s        | Title card — "QUAKE" forming   |
| frame_10s.png     | 10s       | "Part 4"                       |
| frame_14s.png     | 14s       | Fade to black                  |
| frame_30s.png     | 30s       | Body — first clip(s)           |
| frame_60s.png     | 60s       | Body — 1 min in                |
| frame_120s.png    | 2:00      | Body — 2 min in                |
| frame_180s.png    | 3:00      | Body — 3 min in                |
| frame_1735s.png   | 28:55     | Body — near end                |

## Comparison vs Part 4 Style B (prior render)

| Aspect           | Style B (prior)        | v5 titlecard (this)              |
|------------------|------------------------|----------------------------------|
| Intro            | PANTHEON 7s only       | PANTHEON 7s + title card 8s      |
| Transitions      | xfade                  | HARD CUTS only                   |
| Music volume     | 0.85                   | 0.5                              |
| Game audio       | reduced                | 1.0 foreground                   |
| Head/tail trim   | 2s / 1.5s+envelope     | 1s / 2s                          |
| Multi-angle      | FP↔FL ping-pong        | FP spine + ONE FL slow-contrast  |
| Final codec      | libx264                | av1_nvenc 10-bit cq=18           |

## Notes

- Direct render path used because `ffprobe.exe` was deleted by a concurrent cleanup
  pass, which broke `phase1/pipeline.assemble_part`. The body was already pre-encoded
  into 133 chunks at `output/_part4_v5_body_chunks/` from an earlier run, so
  `render_part4_v5_direct.py` concatenates those chunks with the PANTHEON trim +
  title card + looped music in a single ffmpeg invocation.
- No transitions, no xfades — every clip boundary is a hard cut.
- Music loops with no crossfade (music_crossfade_on_loop applied at playback stream
  level via -stream_loop -1 + amix duration=first).
