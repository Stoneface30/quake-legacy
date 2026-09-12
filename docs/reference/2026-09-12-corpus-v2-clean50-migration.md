# Corpus migration: parser v1 → parser v2

Scope: **50 demos** held by the v2 build; v1 rows are restricted to the same demos where the table carries `content_hash`. Aggregates only.

## Frags (matched by content hash, server time, victim)

| | count |
|---|---:|
| old | 2304 |
| new | 2304 |
| kept | 2303 |
| added | 1 |
| removed | 1 |

Changed among kept: `{'tags': 214}` · by_recorder flips: `{}` · score: `{'mean': -0.2484, 'changed': 211}`

Per-demo frag-count delta (v2 − v1): `{'n': 50, 'min': 0, 'p5': 0, 'median': 0, 'p95': 0, 'max': 0, 'nonzero': 0}`

## Why it changed

Parser v1 was wrong (`STALE_PRE_PARSER_V2`), so differences are expected; each bucket names what moved.

```
{
 "recovered_kills": 1,
 "lost_or_invalid_old_kills": 1,
 "shifted_timestamps": {
  "n": 0,
  "ms": {
   "n": 0
  }
 },
 "recognized_matched": 312,
 "changed_attributes": {
  "frags_by_side": {
   "entity": 310,
   "playerstate_or_event": 297
  },
  "by_key_top25": {
   "victim_speed_percentile": 308,
   "attacker_speed_percentile": 280,
   "distance": 181,
   "victim_air_height": 173,
   "dodge_proximity_pctile": 163,
   "dodge_quality_score": 162,
   "dodge_evasion_pctile": 157,
   "dodge_near_miss_count": 148,
   "dodge_min_closest_approach_units": 146,
   "dodge_to_kill_gap_ms": 141,
   "dodge_max_velocity_change": 135,
   "dodge_best_threat_type": 128,
   "lg_incoming_fire_ticks": 75,
   "victim_vertical_speed": 73,
   "projectile_victim_airborne": 53,
   "lg_incoming_hit_ratio": 46,
   "lg_dodge_rating": 43,
   "victim_travel_during_flight": 40,
   "projectile_victim_vertical_speed": 36,
   "projectile_direct_expansion_u": 36,
   "projectile_direct_geometry": 33,
   "lg_taken_lg_dmg": 27,
   "visibility_ms": 27,
   "popup_rise_vz": 22,
   "dodge_immediacy": 21
  }
 },
 "changed_classification": {
  "frags": 218,
  "labels_gained_top15": {
   "DODGE_TO_KILL": 90,
   "NEAR_MISS_ROCKET": 66,
   "NEAR_MISS_RAIL": 58,
   "LG_TRACKING": 31,
   "POPUP_COMBO": 21,
   "RAIL_AIR": 21,
   "DIRECT_CONFIRMED_GEO": 15,
   "DODGE_STRAFE": 14,
   "AIR_ROCKET_GEO": 13,
   "RAPID_MULTIKILL": 12,
   "NEAR_DIRECT": 7,
   "TARGET_TRANSFER": 6,
   "HIGH_SPEED_FRAG": 6,
   "AIR_ROCKET": 4,
   "NEAR_MISS_GRENADE": 3
  },
  "labels_lost_top15": {
   "RAIL_AIR": 9,
   "NEAR_MISS_ROCKET": 5,
   "DODGE_STRAFE": 3,
   "DODGE_TO_KILL": 2,
   "DODGE_HERO": 1,
   "SNAP_ON_ARRIVAL": 1,
   "EXTREME_SPEED": 1,
   "CORNER_PREFIRE_CONFIRMED": 1,
   "REACTION_SHOT": 1,
   "SPEED_TARGET_FRAG": 1,
   "POPUP_COMBO": 1,
   "NEAR_MISS_GRENADE": 1
  }
 },
 "clutch_membership": {
  "clutch_all_players.csv": {
   "old": 13,
   "new": 13,
   "kept": 13,
   "added": 0,
   "removed": 0
  },
  "clutch_recorder.csv": {
   "old": 8,
   "new": 8,
   "kept": 8,
   "added": 0,
   "removed": 0
  }
 }
}
```

## Highlights (top-N by highlight_score, matched by identity)

| | v1 | v2 | overlap | jaccard |
|---|---:|---:|---:|---:|
| top50 | 50 | 50 | 1 | 0.01 |
| top100 | 100 | 100 | 16 | 0.087 |
| top500 | 312 | 312 | 312 | 1.0 |

## Tables

| table | v1 | v2 | Δ |
|---|---:|---:|---:|
| frags_rebuilt.db:demos | 50 | 50 | +0 |
| frag_recognition.db:scanned_demos | 50 | 50 | +0 |
| frag_recognition.db:recognized_frags | 312 | 312 | +0 |
| frag_recognition.db:kill_events_v1 by death_cause = PLAYER_KILL | 2242 | 2242 | +0 |
| frag_recognition.db:kill_events_v1 by death_cause = SUICIDE | 8 | 8 | +0 |
| frag_recognition.db:kill_events_v1 by death_cause = TELEFRAG | 62 | 62 | +0 |
| frag_recognition.db:kill_events_v1 by mod_name = GAUNTLET | 2 | 2 | +0 |
| frag_recognition.db:kill_events_v1 by mod_name = GRENADE | 20 | 20 | +0 |
| frag_recognition.db:kill_events_v1 by mod_name = GRENADE_SPLASH | 16 | 16 | +0 |
| frag_recognition.db:kill_events_v1 by mod_name = LIGHTNING | 712 | 712 | +0 |
| frag_recognition.db:kill_events_v1 by mod_name = MACHINEGUN | 4 | 4 | +0 |
| frag_recognition.db:kill_events_v1 by mod_name = MOD_29 | 8 | 8 | +0 |
| frag_recognition.db:kill_events_v1 by mod_name = PLASMA | 13 | 13 | +0 |
| frag_recognition.db:kill_events_v1 by mod_name = PLASMA_SPLASH | 2 | 2 | +0 |
| frag_recognition.db:kill_events_v1 by mod_name = RAILGUN | 808 | 808 | +0 |
| frag_recognition.db:kill_events_v1 by mod_name = ROCKET | 187 | 187 | +0 |
| frag_recognition.db:kill_events_v1 by mod_name = ROCKET_SPLASH | 406 | 406 | +0 |
| frag_recognition.db:kill_events_v1 by mod_name = SHOTGUN | 72 | 72 | +0 |
| frag_recognition.db:kill_events_v1 by mod_name = TELEFRAG | 62 | 62 | +0 |
| frag_recognition.db:semantic_events_v1 by type = change_weapon | 25602 | 25602 | +0 |
| frag_recognition.db:semantic_events_v1 by type = death | 1351 | 1351 | +0 |
| frag_recognition.db:semantic_events_v1 by type = fire_weapon | 176190 | 176190 | +0 |
| frag_recognition.db:semantic_events_v1 by type = gib_player | 679 | 679 | +0 |
| frag_recognition.db:semantic_events_v1 by type = item_pickup | 4 | 4 | +0 |
| frag_recognition.db:semantic_events_v1 by type = jump | 23758 | 23758 | +0 |
| frag_recognition.db:semantic_events_v1 by type = jump_pad | 2212 | 2212 | +0 |
| frag_recognition.db:semantic_events_v1 by type = missile_hit | 47049 | 47049 | +0 |
| frag_recognition.db:semantic_events_v1 by type = missile_miss | 90650 | 90650 | +0 |
| frag_recognition.db:semantic_events_v1 by type = pain | 13526 | 13526 | +0 |
| frag_recognition.db:semantic_events_v1 by type = railtrail | 7868 | 7868 | +0 |
| frag_recognition.db:semantic_events_v1 by type = teleport_in | 5839 | 5839 | +0 |
| frag_recognition.db:semantic_events_v1 by type = teleport_out | 3222 | 3222 | +0 |
| frag_recognition.db:semantic_events_v1 by type = use_item | 1078 | 1078 | +0 |
| frag_recognition.db:missile_samples_v1 | 43534 | 74115 | +30581 |
| frag_recognition.db:teleport_transits_v1 by outcome = TELEPORT_PLAYER_CONFIRMED | 1846 | 2721 | +875 |
| frag_recognition.db:teleport_transits_v1 by outcome = UNKNOWN | 960 | 85 | -875 |
| frag_recognition.db:server_text_v1 by kind = chat | 2131 | 1265 | -866 |
| frag_recognition.db:server_text_v1 by kind = cp | 256 | 174 | -82 |
| frag_recognition.db:server_text_v1 by kind = print | 433 | 306 | -127 |
| frag_recognition.db:server_text_v1 by kind = tchat | 225 | 150 | -75 |
| frag_recognition.db:round_state_v1 | 4144 | 2526 | -1618 |
| frag_recognition.db:team_changes_v1 | 706 | 692 | -14 |
| frag_recognition.db:kill_occurrences_v1 *(unscoped: whole-DB counts)* | 206268 | 2312 | -203956 |
| frag_recognition.db:action_moments_v1 by activity_label = RECORDER_DOMINANT | 81 | 98 | +17 |
| frag_recognition.db:action_moments_v1 by activity_label = SHARED_FIREFIGHT | 714 | 789 | +75 |
| mining_epoch.db:action_moments_v1 by activity_label = RECORDER_DOMINANT | 81 | 98 | +17 |
| mining_epoch.db:action_moments_v1 by activity_label = SHARED_FIREFIGHT | 714 | 789 | +75 |
| mining_epoch.db:aim_events_v1 | 12379 | 12380 | +1 |
| frag_shapes.db:frag_shapes_v1 | 570 | 580 | +10 |

## Human linkage (v1 live → v2 build)

```
{
 "human_targets": 14,
 "by_status": {
  "OUT_OF_SCOPE": 13,
  "ONE_TO_ONE": 1
 },
 "one_to_one": 1,
 "manual_review": [],
 "migratable_without_review": true
}
```
