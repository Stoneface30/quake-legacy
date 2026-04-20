# Open Items (extracted 2026-04-20)

## Blocking for batch render
- Part 3 style lock: A/B/C/V5 hybrid -- user decision needed before Parts 4-12 full batch
- Game audio level: 0.55 vs 0.75 A/B test on next render pass (Config.game_audio_volume)

## Parts review status
- Parts 4/5/6 rendered, user review pending (6-axis: chain flow, beat, game audio, multi-angle, intro, grade)
- Parts 7-12 full renders unlock after Part 4 approved
- Parts 6/7 crash root cause: normalize cache corruption -- fix before next batch
- Parts 8-12: clip_lists/partNN_styleb.txt missing -- need creation
- Part 4 v12 already reviewed by user -- do NOT re-request review (rule L157)
- Part 5 preview shipped (output/Part05_v1_PREVIEW_freshstems.mp4) -- user review pending

## Demo corpus
- 6,465 .dm_73 files in demos/ (13.19 GB)
- 948 in WOLF WHISPERER/WolfcamQL/wolfcam-ql/demos/ (some <150KB action-extracts)

## Phase 2 / parser
- Gate P3-0: highlight criteria must be confirmed with user before 6,465-demo batch
- Custom C++ parser (FT-1): user approved Path B; scaffold at phase2/dm73parser/
- highlight-criteria-v2.md referenced in CLAUDE.md but only v1 exists on disk -- v2 needs authoring

## Infrastructure
- Disk tight: ~49 GB free of 932 GB (as of 2026-04-20 morning)
- output/normalized/ cache: 650 good files (~32 GB), scrub_normalize_cache.py available for validation
- Parts 8-12 skipped overnight: no clip_lists/part0N_styleb.txt authored yet
- L153 fix pending: use tasklist //FI "PID eq $PID" for Windows process liveness (not kill -0)
- L154 fix pending: atomic writes in phase1/normalize.py (write to .partial, mv on success, ffprobe gate)

## Ghidra RE (FT-4)
- Blocked: need Ghidra 11.3 + JDK 21 installed (user machine)
- Blocked: need WOLF WHISPERER/Wolf Whisperer.rar extracted
- No WolfcamQL Phase 2 automation ships until FT-4 completes

## Render quality ceiling (FT-6, Rule P1-J)
- Current renders use NVENC av1_nvenc p7 CQ18
- Decision pending: keep current / x264 CRF 15 slow / x265 CRF 17 slow

## Music tracks (Parts 7-12)
- Beat caches and mp3s exist for all parts
- User has not confirmed per-Part picks; default = use what is already downloaded
- Library grew to 1,206 tracks overnight (was 270)

## Next session entry point
- Tier 2 editor Step 5 (media-bin panel) -- see NEXT_SESSION.md
- Do NOT re-run scripts/batch_preview_4_to_12.sh without user re-approval
