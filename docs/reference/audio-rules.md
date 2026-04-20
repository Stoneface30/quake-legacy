# Audio Rules Reference

## Music Volume (P1-G v5)
- music_volume = 0.20
- fadein_s = 1.5
- ebur128 gate: music <= -12 LU below game peak -> else FAILED_LEVEL_GATE
- Config: cfg.music_volume=0.20, cfg.music_fadein_s=1.5 | Code: render_part_v6.py::final_render audio graph | Audit: output/partNN_levels.json | Fail state: FAILED_LEVEL_GATE (not shipped)

## Three-Track Contract (P1-R v2)
- Every Part: intro_music + main_music + outro_music
- Continuous coverage mandatory -- silence gaps = render failure
- All tracks play FULL; last may truncate at phrase boundary only
- Config: Config.intro_music_path(part) / music_path(part) / outro_music_path(part) | Code: phase1/music_stitcher.py | Override: partNN_intro_music.* / partNN_outro_music.*

## Music Stitcher (P1-AA v2)
- Video body length is truth
- Queue N full tracks until sum(duration) >= body_duration
- Last track truncates at PHRASE boundary (never mid-bar)
- Seams = DJ beat+phrase match at 8/16-bar boundaries
- Sidechain-duck music ~6 dB on recognized game events
- Code: phase1/music_stitcher.py + phase1/sidechain.py | Ship gate: output/partNN_music_plan.json (every track duration == full_duration ± 0.1s EXCEPT last)

## Action Peak Recognition (P1-Z v2)
- Events: player_death, rocket_impact, rail_fire, grenade_explode, LG_hit
- Template match against phase1/sound_templates/ (-> creative_suite/engine/sound_templates/ post-restructure)
- Minimum confidence 0.55 to trigger effect
- Fallback: loudest onset + tag RECOGNITION_FAILED
- Code: phase1/audio_onsets.py::recognize_game_events | Output: output/partNN_beats.json

## P1-BB — Split Graphs, PCM WAV, CFR
- Body assembly: two parallel ffmpeg graphs (video: xfade chain; audio: concat+afade pairs)
- Intermediates: PCM WAV (never AAC) — avoids AAC priming delay (~1024 samples/chunk)
- Ingest: -vsync cfr -r 60 (CFR enforcement before any filter)
- amix: duration=first + explicit apad on game; never duration=longest
- Ship gate: drift audit via ffprobe -> output/partNN_sync_audit.json; max_drift_ms <= 40
- Code: render_part_v6.py::assemble_body_with_xfades (video) + separate audio assembly
