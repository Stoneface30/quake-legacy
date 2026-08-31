# Frag Taxonomy — Review Sheet (V2 recognition cache, 2026-08-31)

All 62 classes the recognizer assigns over the MAIN_CA pool (35,170 frags;
side pools: 164 duel, 1,273 other). Counts are current DB state; example ids
are browsable in the /frags UI. **Review columns: keep the class? default
cinematic treatment OK?** Edit inline — this file is the Gate-R contract for
the 3D/effects config (`creative_suite/engine/frag_vision_config.json`).

Evidence tiers: **GEO** = geometry/BSP-verified · **MEAS** = measured from
extracted timeseries (honest, no fake stats) · **HEUR** = event-pattern
heuristic · **CAND** = candidate flag awaiting stronger evidence.

## Projectile skill (rockets / grenades)

| Class | Count | Evidence | Definition | Default vision |
|---|---|---|---|---|
| DIRECT_ROCKET | 3,169 | HEUR | missile_hit on victim within kill window | POV + impact hold |
| DIRECT_CONFIRMED_GEO | 3,211 | GEO | reconstructed path, bbox expansion ≤ 24u | POV + **projectile_follow** replay |
| NEAR_DIRECT | 347 | GEO | small expansion, not direct | POV only |
| AIR_ROCKET | 1,053 | HEUR | victim airborne at impact | slow-mo window |
| AIR_ROCKET_GEO | 918 | GEO | victim z-velocity/ground clearance proven | **projectile_follow** + slow-mo |
| AIR_GRENADE | 55 | HEUR | grenade kill, victim airborne | projectile_follow (arc cam) |
| PREDICTION_TEMPORAL | 192 | GEO | fired before victim visible (LOS gap) | third-person reveal + freeze |
| PREDICTION_CANDIDATE | 41 | CAND | weaker temporal evidence | POV only |

## Rail

| Class | Count | Evidence | Definition | Default vision |
|---|---|---|---|---|
| RAIL_FRAG | 10,496 | HEUR | rail kill | POV (no effect below score gate) |
| RAIL_AIR | 1,815 | MEAS | victim airborne at rail kill | slow-mo window |
| RAIL_CONSECUTIVE | 664 | HEUR | back-to-back rails ≤ 4s | speed-ramp chain |
| RAIL_FLICK | 62 | MEAS | rail + clean flick curve | **flick vision** (see aim) |
| PIXEL_SHOT_GEO | 56 | GEO | visible_fraction ≤ 0.25, ang ≤ 3.0° | freeze + zoom on gap |
| PIXEL_SHOT_CANDIDATE | 1 | CAND | stage-2 not confirmed | POV only |
| TINY_GAP_SHOT | 31 | GEO | visible_fraction ≤ 0.12 | freeze + zoom |
| REACTION_SHOT | 121 | GEO | LOS open ≤ 250ms before kill | speed-ramp in |
| REACTION_SHOT_CANDIDATE | 3 | CAND | weaker LOS evidence | POV only |
| CORNER_PREFIRE_CONFIRMED | 85 | GEO | fired pre-LOS at corner | third-person reveal |

## Aim (view-timeseries, onset-based)

| Class | Count | Evidence | Definition | Default vision |
|---|---|---|---|---|
| FLICK_SHOT | 2,211 | MEAS | onset flick before kill | POV |
| CLEAN_FLICK | 767 | MEAS | flick ≥ 90° ≤ 350ms ≥ 350dps, reversals ≤ 1 | **flick vision**: freeze at onset → whip |
| EXTREME_FLICK | 415 | MEAS | subset of CLEAN_FLICK, extreme values | flick vision + slow-mo |
| HIGH_SPEED_AIM_TRANSITION | 315 | MEAS | big aim transfer at speed | speed-ramp |
| AGGRESSIVE_TRACKING_SWEEP | 289 | MEAS | sustained high-dps tracking | POV, no cut |
| LARGE_AIM_TRANSITION | 26 | MEAS | wide transfer, slower | POV |
| TARGET_TRANSFER | 60 | MEAS | kill→kill aim transfer | one-cut two-kill framing |

## LG (damage-flow model — honest metrics)

| Class | Count | Evidence | Definition | Default vision |
|---|---|---|---|---|
| LG_TRACKING | 5,439 | MEAS | sustained contact-pain rate | POV |
| LG_HIGH_ACCURACY | 1,141 | MEAS | top contact-rate band | POV + damage counter overlay (planned) |
| LG_HIGH_PRESSURE | 473 | MEAS | contact rate ≥ 2.0/s | POV + shake |
| LG_DODGE_MASTER | 323 | MEAS | dealt/received ratio ≥ 20, incoming ≤ 0.10 | **third-person dodge cam** |
| LG_TRANSFER | 13 | MEAS | LG kill→kill transfer | one-cut framing |
| DAMAGE_BURST | 208 | MEAS | ≥ 100 dmg in short burst | speed-ramp |

## Multikill / clutch / fights

| Class | Count | Evidence | Definition | Default vision |
|---|---|---|---|---|
| MULTIKILL_DOUBLE | 2,118 | HEUR | 2 kills in CA-round window | kill-counter popup |
| MULTIKILL_TRIPLE | 129 | HEUR | 3 kills | kill-counter + ramp per kill |
| MULTIKILL_QUAD | 4 | HEUR | 4+ kills | full scene treatment |
| RAPID_MULTIKILL | 24 | HEUR | kills ≤ 2s apart | speed-ramp chain |
| HIGH_SPEED_MULTIKILL | 1 | MEAS | multikill at extreme speed | scene treatment |
| CLUTCH_1V2 | 1,294 | HEUR | round won from 1v2 | 1vX counter overlay |
| CLUTCH_1V3 | 456 | HEUR | round won from 1v3 | 1vX counter + scene treatment |
| CLUTCH_1V4_PLUS | 86 | HEUR | round won from 1v4+ | full scene treatment |

## Movement / speed

| Class | Count | Evidence | Definition | Default vision |
|---|---|---|---|---|
| HIGH_SPEED_FRAG | 2,476 | MEAS | percentile speed band at kill | POV |
| VERY_FAST_FRAG | 701 | MEAS | higher band | speed lines / ramp |
| EXTREME_SPEED | 367 | MEAS | p99+ band | **third-person chase cam** |
| SPEED_TARGET_FRAG | 1,215 | MEAS | victim at high speed | slow-mo on victim |
| HIGH_SPEED_AIR_FRAG | 43 | MEAS | recorder airborne + fast | chase cam + slow-mo |
| VERTICAL_ACTION | 361 | MEAS | large z-travel in window | low-angle third person |
| STRAFE_CHAIN_FRAG | 28 | MEAS | strafe-jump chain into kill | chase cam |
| ROCKET_JUMP_ENTRY | 29 | HEUR | RJ ≤ 3s before kill | chase cam |
| ROCKET_JUMP_FRAG | 24 | HEUR | RJ directly into kill | chase cam + slow-mo |
| DODGE_AND_KILL | 699 | MEAS | incoming fire dodged in window | third-person dodge cam |
| ESCAPE_TURNAROUND | 153 | MEAS | retreat→turn→kill pattern | third-person reveal |

## Health drama (secondary by mandate)

| Class | Count | Evidence | Definition | Default vision |
|---|---|---|---|---|
| LOW_HP_FRAG | 287 | MEAS | HP ≤ 35 at kill | subtle red vignette |
| CRITICAL_HP_FRAG | 132 | MEAS | HP ≤ 15 | vignette + heartbeat (optional) |
| LAST_HP_FRAG | 56 | MEAS | bucket floor = last band | vignette |
| LAST_HP_CANDIDATE | 82 | CAND | quantized-bucket uncertainty | none |
| LOW_HEALTH_WIN | 96 | MEAS | round won at low HP | vignette on round end |
| HEAVY_DAMAGE_SURVIVED | 452 | MEAS | large damage absorbed, survived | none (context only) |

## Weapon craft

| Class | Count | Evidence | Definition | Default vision |
|---|---|---|---|---|
| WEAPON_COMBO | 506 | HEUR | 2 weapons ≤ 2s into kill | quick-cut combo framing |
| MULTI_WEAPON_CHAIN | 63 | HEUR | 3+ weapons chained | combo framing + ramp |
| FAST_WEAPON_SWITCH | 468 | MEAS | switch ≤ 400ms before kill | POV |
| WEAPON_SWITCH_FINISH | 24 | HEUR | switch-weapon finisher | quick-cut |
| COMBO_KILL | 21 | HEUR | legacy combo tag | fold into WEAPON_COMBO? |
| POPUP_COMBO | 153 | HEUR | knock-up → finish | slow-mo apex |

## Open review questions

1. Merge `COMBO_KILL` into `WEAPON_COMBO`? (21 rows, same pattern)
2. `RAIL_FRAG` at 10k rows is a weapon tag, not a highlight — keep as
   sort-key only, never a capture reason. Agree?
3. `*_CANDIDATE` classes: hide from the browser default view?
4. Health-drama family: vignette effects on by default, or only when
   stacked with a skill class?
