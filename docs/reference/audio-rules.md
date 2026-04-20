# Audio Rules Reference

## Music Volume (P1-G v5)
- music_volume = 0.20
- fadein_s = 1.5
- ebur128 gate: music <= -12 LU below game peak -> else FAILED_LEVEL_GATE

## Three-Track Contract (P1-R v2)
- Every Part: intro_music + main_music + outro_music
- Continuous coverage mandatory -- silence gaps = render failure
- All tracks play FULL; last may truncate at phrase boundary only

## Music Stitcher (P1-AA v2)
- Video body length is truth
- Queue N full tracks until sum(duration) >= body_duration
- Last track truncates at PHRASE boundary (never mid-bar)
- Seams = DJ beat+phrase match at 8/16-bar boundaries
- Sidechain-duck music ~6 dB on recognized game events

## Action Peak Recognition (P1-Z v2)
- Events: player_death, rocket_impact, rail_fire, grenade_explode, LG_hit
- Template match against creative_suite/engine/sound_templates/
- Minimum confidence 0.55 to trigger effect
- Fallback: loudest onset + tag RECOGNITION_FAILED
