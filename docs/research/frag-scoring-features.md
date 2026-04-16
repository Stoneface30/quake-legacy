# Frag Scoring Feature Table
## Per-Frag Extractable Features for Quality Score (0.0–1.0)
**Date:** 2026-04-16
**Project:** QUAKE LEGACY — Phase 3 AI Scoring Model

---

## Feature Extraction Sources

| Source | What it provides |
|---|---|
| EV_OBITUARY entity | weapon, killer_slot, victim_slot, frag_time_ms |
| playerState_t (killer) | position, velocity, health, armor, weapon, pm_flags |
| playerState_t (victim) | position, velocity, groundEntityNum, pm_flags, health |
| Snapshot sequence | kill_streak, weapon_switches, trajectory data |
| xstats2 / mstats | server-authoritative weapon accuracy per round |
| CS_SERVERINFO | map_name, game_type, round number |
| CS_SCORES | team scores, round scores (for clutch context) |
| EV_OBITUARY sequence | round kill order (is killer last alive?) |

---

## Feature Table

| Feature | Type | Range / Values | Extraction Source | Expected Score Impact | Difficulty |
|---|---|---|---|---|---|
| **WEAPON FEATURES** | | | | | |
| `weapon` | categorical | MOD_* constant | EV_OBITUARY.eventParm | HIGH — weapon is primary quality driver | Easy |
| `is_railgun` | boolean | True/False | derived from weapon | HIGH — rail frags are prestige | Easy |
| `is_direct_rocket` | boolean | True/False | MOD_ROCKET (not SPLASH) | HIGH — harder than splash | Easy |
| `is_gauntlet` | boolean | True/False | MOD_GAUNTLET | VERY HIGH — rare and humiliating | Easy |
| `is_telefrag` | boolean | True/False | MOD_TELEFRAG | HIGH — funny/intentional | Easy |
| `is_grenade` | boolean | True/False | MOD_GRENADE | MEDIUM — skill required | Easy |
| **AIRSHOT FEATURES** | | | | | |
| `victim_airborne` | boolean | True/False | victim.groundEntityNum == ENTITYNUM_NONE | VERY HIGH — core highlight type | Easy |
| `victim_vz` | float | -800 to +900 units/s | victim.velocity[2] | HIGH — faster fall = more impressive | Easy |
| `victim_air_time_ms` | integer | 0 to 2000ms | frag_time - last_ground_contact | MEDIUM — longer air time = harder shot | Medium |
| `victim_at_apex` | boolean | True/False | abs(victim.velocity[2]) < 50 | HIGH — apex is hardest to hit | Easy |
| `victim_rocket_launched` | boolean | True/False | victim.velocity[2] > 400 | MEDIUM — context for the air state | Easy |
| `victim_jumped` | boolean | True/False | victim.pm_flags & PMF_JUMP_HELD | LOW — distinguishes from knockback | Easy |
| **DISTANCE FEATURES** | | | | | |
| `killer_victim_distance` | float | 0 to 8000 units | vector_distance(killer.origin, victim.origin) | HIGH for rail/LG — long range = impressive | Easy |
| `killer_victim_distance_2d` | float | 0 to 8000 units | horizontal distance only | MEDIUM — 2D distance for map context | Easy |
| `height_diff` | float | -2000 to +2000 | killer.z - victim.z | MEDIUM — kills below you more impressive (downward) | Easy |
| `is_long_range` | boolean | True/False | distance > 1000 units | HIGH for rail | Easy |
| `is_extreme_range` | boolean | True/False | distance > 2000 units | VERY HIGH for rail | Easy |
| **ACCURACY FEATURES (LG)** | | | | | |
| `lg_accuracy` | float | 0.0 to 1.0 | xstats2 or health-delta method | VERY HIGH for LG frags | Medium |
| `lg_accuracy_window` | float | 0.0 to 1.0 | accuracy in 3s before kill | HIGH — sustained accuracy window | Medium |
| `lg_damage_dealt` | integer | 0 to 5000 | server stats or health deltas | MEDIUM — total damage context | Medium |
| `is_high_lg_accuracy` | boolean | True/False | lg_accuracy >= 0.60 | HIGH | Easy (derived) |
| **MULTI-KILL FEATURES** | | | | | |
| `kill_streak` | integer | 1 to 16 | kills within 5s window | VERY HIGH — 3+ kills = top highlight | Easy |
| `is_double_kill` | boolean | True/False | kill_streak == 2 | MEDIUM | Easy |
| `is_triple_kill` | boolean | True/False | kill_streak == 3 | HIGH | Easy |
| `is_quad_kill` | boolean | True/False | kill_streak >= 4 | VERY HIGH | Easy |
| `multikill_duration_ms` | integer | 0 to 5000 | time from first to last kill in streak | HIGH — faster = more impressive | Easy |
| `multikill_weapons` | list | [MOD_*] | weapons used across streak | MEDIUM — combo context | Medium |
| **WEAPON COMBO FEATURES** | | | | | |
| `weapon_combo` | categorical | None/combo_name | playerState.weapon sequence | HIGH — shows weapon mastery | Easy |
| `is_holy_trinity` | boolean | True/False | RL+RG+LG in 3s | HIGH | Easy |
| `unique_weapons_used` | integer | 1 to 5 | distinct weapons in window | MEDIUM | Easy |
| `weapon_switches_count` | integer | 0 to 10 | weapon field changes | LOW — too many switches = spam | Easy |
| `frag_weapon_switch_delay_ms` | integer | 0 to 3000 | time since last weapon switch | MEDIUM — instant switch to kill = skill | Easy |
| **FLICK RAIL FEATURES** | | | | | |
| `is_flick_rail` | boolean | True/False | angular velocity > threshold before RG kill | HIGH — requires UDT-style angle tracking | Medium |
| `flick_angular_velocity` | float | 0 to 1800 deg/s | max angle change rate in 200ms window | HIGH | Medium |
| `flick_angle_delta` | float | 0 to 360 degrees | total angle change before shot | MEDIUM | Medium |
| **GAME CONTEXT FEATURES** | | | | | |
| `game_type` | categorical | FFA/CA/CTF/Duel | CS_SERVERINFO | MEDIUM — CA context = more stakes | Easy |
| `map_name` | categorical | e.g., "campgrounds" | CS_SERVERINFO | LOW — map affects style not quality | Easy |
| `round_time_remaining_ms` | integer | 0 to 180000 | round_duration - (frag_time - round_start) | HIGH in CA — clutch timing matters | Medium |
| `is_round_winner` | boolean | True/False | killer's kill ends the round | VERY HIGH in CA — round-winning kill | Hard |
| `is_clutch` | boolean | True/False | killer was last alive on team | VERY HIGH in CA | Hard |
| `score_differential` | integer | -15 to +15 | team score diff at moment of kill | MEDIUM — comeback frags more valuable | Medium |
| `victims_remaining_before` | integer | 0 to 8 | enemy players alive before kill | HIGH in CA — killing 1-of-1 = clutch | Hard |
| `round_number` | integer | 1 to 30 | count of round-end events | LOW — late rounds slightly more intense | Medium |
| **KILLER STATE FEATURES** | | | | | |
| `killer_health` | integer | 1 to 200 | killer.stats[STAT_HEALTH] at frag | HIGH — low HP kill = clutch | Easy |
| `killer_armor` | integer | 0 to 200 | killer.stats[STAT_ARMOR] at frag | MEDIUM — context for survivability | Easy |
| `killer_is_low_health` | boolean | True/False | killer_health <= 25 | HIGH — high-pressure kill | Easy |
| `killer_had_powerup` | boolean | True/False | killer.powerups (quad, etc.) | LOW — powerup frags less impressive | Medium |
| `killer_velocity` | float | 0 to 1200 units/s | magnitude of killer.velocity | LOW — context | Easy |
| `killer_is_airborne` | boolean | True/False | killer.groundEntityNum == ENTITYNUM_NONE | MEDIUM — air-to-air is elite | Easy |
| **VICTIM STATE FEATURES** | | | | | |
| `victim_health_at_kill` | integer | 1 to 200 | victim health at frag | LOW — full HP kill slightly more impressive | Easy |
| `victim_had_powerup` | boolean | True/False | victim.powerups | LOW — killing quad carrier is notable | Medium |
| `victim_count_in_demo` | integer | 1 to 100 | how many times victim was killed | LOW — killing dominant player notable | Medium |
| **TRAJECTORY FEATURES** | | | | | |
| `frag_entity_num` | integer | 0 to 1023 | ET_MISSILE entity closest to kill point | Required for bullet cam, not scoring | Hard |
| `projectile_flight_time_ms` | integer | 0 to 3000 | spawn time to kill time for rocket | MEDIUM — longer flight = more impressive | Hard |
| `projectile_arc_height` | float | 0 to 2000 | max Z above spawn point | LOW — visual interest only | Hard |
| **TEMPORAL FEATURES** | | | | | |
| `time_since_last_death_ms` | integer | 0 to 180000 | killer's last respawn time | LOW — freshly spawned kill noted | Medium |
| `time_to_next_kill_ms` | integer | 0 to 60000 | next kill in streak gap | MEDIUM — tight followup | Easy |
| `is_opening_frag` | boolean | True/False | first kill of the round | MEDIUM — sets tone | Medium |
| `is_last_kill_of_round` | boolean | True/False | no more kills in round after | MEDIUM — round ender | Medium |

---

## Feature Priority Matrix

| Priority | Features | Why |
|---|---|---|
| P0 (implement first) | weapon, victim_airborne, kill_streak, killer_health | Core quality signals, all easy to extract |
| P1 (implement with patterns) | victim_vz, killer_victim_distance, weapon_combo, is_flick_rail | Medium complexity, high value |
| P2 (after Phase 2 review data) | lg_accuracy, is_clutch, is_round_winner, round_time_remaining | Need parser extensions or game state tracking |
| P3 (nice to have) | frag_entity_num, projectile_flight_time, victim_rocket_launched | Hard, needed only for bullet cam and deep analysis |

---

## Scoring Weight Suggestions (Rule-Based)

For initial rule-based scoring before ML training data exists:

```python
FEATURE_WEIGHTS = {
    # Weapon base (one-hot, these are additive to base 0.10)
    'MOD_GAUNTLET':       +0.30,
    'MOD_TELEFRAG':       +0.25,
    'MOD_RAILGUN':        +0.20,
    'MOD_ROCKET':         +0.12,  # direct
    'MOD_GRENADE':        +0.08,
    'MOD_ROCKET_SPLASH':  +0.08,
    'MOD_LIGHTNING':      +0.08,
    
    # Airshot (multiplicative feel, applied as additive bonus)
    'victim_airborne_base':      +0.25,
    'victim_at_apex':            +0.05,  # extra
    'victim_vz_deep':            +0.10,  # vz < -300
    'air_plus_rail':             +0.10,  # extra for RG air shot
    
    # Multi-kill
    'kill_streak_2':             +0.15,
    'kill_streak_3':             +0.25,
    'kill_streak_4':             +0.35,
    'kill_streak_5plus':         +0.45,
    
    # LG accuracy
    'lg_acc_60pct':              +0.10,
    'lg_acc_70pct':              +0.20,
    'lg_acc_80pct':              +0.30,
    
    # Distance
    'distance_500_1000':         +0.05,
    'distance_1000_2000':        +0.10,
    'distance_2000plus':         +0.20,
    
    # Killer state
    'killer_hp_under_25':        +0.15,
    'killer_hp_under_50':        +0.05,
    
    # Game context
    'is_clutch':                 +0.20,
    'is_round_winner':           +0.15,
    'is_flick_rail':             +0.15,
    
    # Combo
    'holy_trinity':              +0.20,
    'two_weapon_combo':          +0.10,
    
    # Killer airborne
    'killer_airborne':           +0.10,  # air-to-air
}
```

---

## ML Feature Vector Format

When training XGBoost/LightGBM on Phase 2 human review data:

```python
# Numeric features (scaled 0-1 or standardized)
numeric_features = [
    'killer_victim_distance',   # normalize by map size ~8000 units max
    'victim_vz',                # normalize by terminal velocity ~800
    'victim_air_time_ms',       # normalize by 2000ms
    'lg_accuracy',              # already 0-1
    'killer_health',            # normalize by 200
    'killer_armor',             # normalize by 200
    'kill_streak',              # clip at 5, normalize
    'multikill_duration_ms',    # normalize by 5000
    'round_time_remaining_ms',  # normalize by 180000
    'flick_angular_velocity',   # normalize by 1800
    'score_differential',       # normalize, clip at ±10
    'projectile_flight_time_ms',# normalize by 3000
]

# Boolean features (0/1, no scaling needed)
boolean_features = [
    'victim_airborne',
    'victim_at_apex',
    'victim_rocket_launched',
    'killer_is_airborne',       # air-to-air
    'is_flick_rail',
    'is_holy_trinity',
    'is_clutch',
    'is_round_winner',
    'killer_is_low_health',
    'victim_had_powerup',
    'killer_had_powerup',
    'is_opening_frag',
    'is_last_kill_of_round',
]

# Categorical features (one-hot encode)
categorical_features = [
    'weapon',       # ~15 values
    'game_type',    # FFA/CA/CTF/Duel/TDM
    'map_name',     # ~20 common maps
    'weapon_combo', # None, holy_trinity, rail_to_rocket, etc.
]

# Target
target = 'human_rating_normalized'  # Phase 2 review dashboard 1-5 → 0.0-1.0
```

---

## Fragmovie Tier Thresholds (Suggested)

Based on rule-based score ranges:

| Score | Tier | Description | Action |
|---|---|---|---|
| 0.80 - 1.00 | T1 | Extraordinary — must be in movie | Auto-approve for T1 clip list |
| 0.60 - 0.79 | T2 | Excellent — strong candidate | Queue for human review |
| 0.40 - 0.59 | T3 | Good — filler or B-roll material | Review only if T1/T2 sparse |
| 0.20 - 0.39 | T4 | Average — skip unless map/context notable | Skip |
| 0.00 - 0.19 | T5 | Unremarkable | Discard |
