# Phase 3 AI Cinematography Engine — Research Document
## AI/ML Approaches for Automated Fragmovie Production
**Date:** 2026-04-16
**Project:** QUAKE LEGACY — .dm_73 demo → automated fragmovie pipeline

---

## Overview

This document covers the research findings for all 8 Phase 3 technical challenges. The architecture philosophy is: **rule-based pattern detection first, ML scoring layer second** (once Phase 2 review data exists). All pattern detection works directly on demo binary data — no engine replay required.

---

## 1. LG Accuracy Tracking Algorithm

### Problem
Detect "sustained 70%+ LG accuracy" frags from raw demo data.

### Key Finding: Two-Track Approach

The LG accuracy problem has two data sources in .dm_73 demos:

**Track A — End-of-round stats commands (preferred, authoritative)**

Quake Live servers transmit `xstats2` / `xstats2a` / `mstats` configstring commands at round end. These contain pre-computed per-weapon stats:
- `LightningGunHits` — total hits
- `LightningGunShots` — total shots fired
- `LightningGunAccuracy` — hits/shots * 100 (integer percent)
- `LightningGunDamage` — total damage dealt

UberDemoTools' `plug_in_stats.cpp` reads these commands directly. The accuracy value is **server-authoritative** — computed by the game engine which has perfect hit registration data.

**Track B — Snapshot delta analysis (window-based, for real-time detection)**

Since LG fires at 20 times/second (50ms intervals) and deals 7 damage per tick in Quake Live:
- Monitor `EV_FIRE_WEAPON` events (weapon == WP_LIGHTNING) on the killer entity
- Monitor victim `playerState_t.stats[STAT_HEALTH]` delta between snapshots
- Each snapshot is at 30Hz (33ms). LG beam fires at ~20Hz
- A "hit" = victim health decreases by 7 (or multiple of 7) in the window the killer is firing LG
- A "miss" = EV_FIRE_WEAPON event occurred but victim health unchanged

**Algorithm for sustained accuracy detection:**

```python
def detect_lg_accuracy_window(killer_events, victim_states, frag_time_ms,
                               window_ms=3000, accuracy_threshold=0.70):
    """
    Detect if killer maintained >= accuracy_threshold LG accuracy
    in the window_ms before a frag.
    """
    window_start = frag_time_ms - window_ms
    
    # Collect all LG fire events in window
    lg_fires = [e for e in killer_events
                if e.time_ms >= window_start
                and e.time_ms <= frag_time_ms
                and e.weapon == WP_LIGHTNING]
    
    if len(lg_fires) < 10:  # Minimum sample size
        return False, 0.0
    
    # Count hits: each hit = victim health drops exactly 7 (or 8 with armor)
    # Cross-reference fire event timing with victim health deltas
    hits = 0
    for fire_event in lg_fires:
        # Find victim snapshot closest to fire time
        snap = get_victim_snapshot_at(victim_states, fire_event.time_ms)
        prev_snap = get_victim_snapshot_at(victim_states, fire_event.time_ms - 50)
        
        if snap and prev_snap:
            health_delta = prev_snap.health - snap.health
            # LG hit = 7 damage (possibly 5-8 with armor absorption variance)
            if 5 <= health_delta <= 9:
                hits += 1
    
    accuracy = hits / len(lg_fires)
    return accuracy >= accuracy_threshold, accuracy
```

**Simpler approach: Use end-of-round xstats2 data**

If the round includes the frag, use the server-side accuracy stats directly. This is 100% accurate and requires no heuristics. UDT extracts this already via `plug_in_stats.cpp`.

### Data Required
- `EV_FIRE_WEAPON` events on killer entity (weapon field = WP_LIGHTNING = 8 in Q3/QL)
- Victim `playerState_t.stats[STAT_HEALTH]` across snapshots
- OR: end-of-round `xstats2` configstring command (server-authoritative)

### LG Damage Values (Quake Live)
- LG hit: 7 damage (pre-nerf), 6 damage (post-nerf era)
- LG armor absorption: typically 1/3 to health, 2/3 to armor
- Good LG accuracy in QL competitive: 30-45% average, 60%+ is elite

### Implementation Complexity: Medium

---

## 2. Air Shot Detection

### Problem
Detect frags where the victim was airborne at kill moment.

### Algorithm (Directly from UDT source study)

UberDemoTools `analysis_pattern_mid_air.cpp` uses this exact approach, which we should replicate:

```python
# Constants from Q3/QL source
ENTITYNUM_NONE = 1023     # groundEntityNum value when airborne
DEFAULT_GRAVITY = 800     # units/s^2 (from bg_public.h)
JUMP_VELOCITY = 270       # initial upward velocity on jump (Q3/QL value)
# At peak of jump: velocity[2] == 0
# Falling: velocity[2] is negative

# Typical velocity[2] values:
# Just jumped:        +270 units/s
# Peak of jump:       ~0
# Mid-fall:           -200 to -400 units/s
# Just before land:   -400 to -600 units/s
# Rocket-launched:    +500 to +900 units/s
# Fall damage starts: when delta_velocity > 700 units/s at landing

Z_MOVEMENT_THRESHOLD = 1.0  # UDT value: change > 1 unit = tracking vertical

def is_victim_airborne(victim_state_at_frag):
    """
    Primary check: groundEntityNum
    Secondary check: velocity[2] threshold
    Tertiary check: air time duration
    """
    # Method 1: Ground entity check (most reliable)
    if victim_state_at_frag.groundEntityNum == ENTITYNUM_NONE:
        return True, "ground_check"
    
    # Method 2: Z-velocity (catches edge cases where ground snapping is delayed)
    # At 30Hz snapshots, a player can be 1 frame off ground
    if victim_state_at_frag.velocity[2] > 100:  # clearly going up
        return True, "velocity_up"
    
    if victim_state_at_frag.velocity[2] < -150:  # clearly falling
        return True, "velocity_down"
    
    return False, None

def classify_airshot_type(victim_state_at_frag):
    """
    Classify HOW airborne for scoring purposes.
    """
    vz = victim_state_at_frag.velocity[2]
    
    if victim_state_at_frag.pm_flags & PMF_JUMP_HELD:
        return "jump"                    # player just jumped
    elif vz > 400:
        return "rocket_launched"         # knocked up by explosion
    elif vz > 100:
        return "ascending"               # still going up
    elif vz < -300:
        return "falling_fast"            # deep fall = more impressive
    elif vz < -100:
        return "falling"                 # normal fall
    else:
        return "apex"                    # at jump peak, hardest to hit
```

### Recommended Thresholds

Based on Q3 physics (gravity=800, jump=270):

| Scenario | velocity[2] | Air time from jump | Notes |
|---|---|---|---|
| Just jumped | +270 | 0ms | PMF_JUMP_HELD set |
| Ascending | +1 to +269 | 0-450ms | |
| Apex | ~0 | ~450ms | Hardest to hit |
| Falling | -1 to -270 | 450-900ms | |
| Full fall | -270 to -600 | 900ms+ | Terminal velocity limited by drag |
| Rocket boost | +400 to +900 | any | Launched by explosion |

**Recommended minimum for "air shot" flag:** `groundEntityNum == ENTITYNUM_NONE` is the primary gate. Set `MinAirTimeMs = 100` (UDT default-style) to filter out 1-2 frame ground touching.

### UDT's Additional Check
UDT also validates that the kill weapon is a **direct-hit projectile** (rocket, grenade, plasma, BFG) — not a splash kill. For LG it just checks groundEntityNum since LG is hitscan.

### Data Required
- `victim.groundEntityNum` at frag timestamp
- `victim.velocity[2]` at frag timestamp
- `victim.pm_flags` for PMF_JUMP_HELD (0x0002)
- Air time duration: `frag_time_ms - last_ground_contact_ms`

### Implementation Complexity: Easy

---

## 3. Multi-Kill Grouping

### Problem
Group 2+ kills from the same killer within a time window into a "multi-kill" event.

### Algorithm (From UDT frag_run analysis)

UDT's `analysis_pattern_frag_run.cpp` implements this exactly:

```python
from dataclasses import dataclass
from typing import List

@dataclass
class Frag:
    killer_slot: int
    victim_slot: int
    time_ms: int
    weapon: str
    demo_id: int

def group_multikills(frags: List[Frag],
                     window_ms: int = 3000,
                     min_kill_count: int = 2) -> List[dict]:
    """
    Group consecutive kills from the same killer within window_ms.
    
    UDT uses configurable maxIntervalMs. Recommended defaults:
    - window_ms=3000: tight multi-kill (impressive)
    - window_ms=5000: extended multi-kill
    
    Quake CA round duration: typically 30-90 seconds.
    A 3s window catches genuine reaction chains, not lucky coincidences.
    """
    # Sort by time
    frags.sort(key=lambda f: f.time_ms)
    
    multikills = []
    
    # Group by killer
    from itertools import groupby
    killer_frags = {}
    for frag in frags:
        killer_frags.setdefault(frag.killer_slot, []).append(frag)
    
    for killer_slot, kills in killer_frags.items():
        kills.sort(key=lambda f: f.time_ms)
        
        # Sliding window grouping
        current_group = [kills[0]]
        
        for i in range(1, len(kills)):
            time_gap = kills[i].time_ms - kills[i-1].time_ms
            
            if time_gap <= window_ms:
                current_group.append(kills[i])
            else:
                # Gap too large — emit current group if valid
                if len(current_group) >= min_kill_count:
                    multikills.append({
                        'killer_slot': killer_slot,
                        'kills': current_group,
                        'count': len(current_group),
                        'duration_ms': current_group[-1].time_ms - current_group[0].time_ms,
                        'weapons': [k.weapon for k in current_group],
                        'start_time_ms': current_group[0].time_ms,
                        'end_time_ms': current_group[-1].time_ms,
                    })
                current_group = [kills[i]]
        
        # Final group
        if len(current_group) >= min_kill_count:
            multikills.append({
                'killer_slot': killer_slot,
                'kills': current_group,
                'count': len(current_group),
                'duration_ms': current_group[-1].time_ms - current_group[0].time_ms,
                'weapons': [k.weapon for k in current_group],
                'start_time_ms': current_group[0].time_ms,
                'end_time_ms': current_group[-1].time_ms,
            })
    
    return multikills
```

### Recommended Time Windows

| Window | Name | Use Case |
|---|---|---|
| 1500ms | Double Kill | Ultra-tight double (both kills in reaction time) |
| 3000ms | Multi-Kill | Standard multi-kill window (matches most FPS game conventions) |
| 5000ms | Extended Run | Frag run / killing spree |
| 10000ms | Frag Run | UDT's "frag sequence" default, broader context |

**Recommendation for QUAKE LEGACY:** Use 3000ms as primary multi-kill window. Also store 5000ms groupings as "frag runs" — these make better cinematic sequences.

**CA-Specific context:** In CA, a team has 4-8 players. A 3-kill run in 3 seconds eliminates 3/4 of a team. This is genuinely extraordinary and should score very high.

### UDT Filters Applied
- Self-kills excluded by default
- Team-kills excluded by default (set `AllowTeamKills=False`)
- Respawn breaks the chain (player dies = chain resets)

### Data Required
- All `EV_OBITUARY` events with killer_slot + timestamp
- Player death events (to reset chains)

### Implementation Complexity: Easy

---

## 4. Weapon Combo Detection

### Problem
Detect RL→RG→LG (or similar) weapon switches within 2-3 seconds of a kill.

### Algorithm

```python
# Quake Live weapon IDs (WP_* constants)
WEAPON_IDS = {
    1:  'WP_GAUNTLET',
    2:  'WP_MACHINEGUN',
    3:  'WP_SHOTGUN',
    4:  'WP_GRENADE_LAUNCHER',
    5:  'WP_ROCKET_LAUNCHER',
    6:  'WP_LIGHTNING',
    7:  'WP_RAILGUN',
    8:  'WP_PLASMAGUN',
    9:  'WP_BFG',
    10: 'WP_GRAPPLING_HOOK',
    # QL additions:
    11: 'WP_NAILGUN',
    12: 'WP_PROX_LAUNCHER',
    13: 'WP_CHAINGUN',
}

def detect_weapon_combo(killer_states, frag_time_ms,
                        combo_window_ms=3000,
                        min_weapons=2):
    """
    Detect weapon switches in the window before a frag.
    
    Track playerState_t.weapon field across snapshots.
    A switch = weapon field changes between consecutive snapshots.
    """
    window_start = frag_time_ms - combo_window_ms
    
    # Collect all snapshots of killer in window
    states_in_window = [s for s in killer_states
                        if window_start <= s.time_ms <= frag_time_ms]
    
    if not states_in_window:
        return None
    
    # Extract weapon sequence (deduplicate consecutive same weapon)
    weapon_sequence = []
    prev_weapon = None
    for state in sorted(states_in_window, key=lambda s: s.time_ms):
        w = state.weapon
        if w != prev_weapon:
            weapon_sequence.append({
                'weapon': WEAPON_IDS.get(w, f'WP_{w}'),
                'time_ms': state.time_ms,
            })
            prev_weapon = w
    
    if len(weapon_sequence) < min_weapons:
        return None
    
    # Check for specific high-value combos
    weapons = [w['weapon'] for w in weapon_sequence]
    combo_name = classify_combo(weapons)
    
    return {
        'combo_name': combo_name,
        'sequence': weapon_sequence,
        'unique_weapons': len(set(weapons)),
        'frag_weapon': weapons[-1],  # weapon used for the kill
    }

def classify_combo(weapons: list) -> str:
    """Name recognizable weapon combos."""
    seq = tuple(weapons)
    
    # Holy Trinity combos
    if 'WP_ROCKET_LAUNCHER' in weapons and 'WP_RAILGUN' in weapons and 'WP_LIGHTNING' in weapons:
        return 'holy_trinity'
    
    # RL finisher combos
    if weapons[-1] == 'WP_ROCKET_LAUNCHER':
        if 'WP_RAILGUN' in weapons[:-1]:
            return 'rail_to_rocket'
        if 'WP_LIGHTNING' in weapons[:-1]:
            return 'lg_to_rocket'
    
    # Rail finisher combos  
    if weapons[-1] == 'WP_RAILGUN':
        if 'WP_ROCKET_LAUNCHER' in weapons[:-1]:
            return 'rocket_to_rail'
        if 'WP_LIGHTNING' in weapons[:-1]:
            return 'lg_to_rail'
    
    # LG sustain to finisher
    if weapons[0] == 'WP_LIGHTNING' and len(weapons) >= 2:
        return f'lg_into_{weapons[-1].lower()}'
    
    return 'weapon_combo'
```

### Notes on Snapshot Rate
At 30Hz snapshots, weapon field changes are visible per-frame. Switch detection works well. The animation switch time in QL is ~500ms — if weapon changes and then changes back quickly it may be a missed shot, not an intentional combo.

### Data Required
- `playerState_t.weapon` across all snapshots for the killer in the window

### Implementation Complexity: Easy

---

## 5. AI Scoring Model

### Recommended Architecture: Hybrid Rule-Based + Future ML

#### Phase 3A: Rule-Based Scoring (implement now)

Score each frag 0.0–1.0 based on weighted features:

```python
# Frag quality score computation
def score_frag(frag_features: dict) -> float:
    score = BASE_SCORE
    
    # --- Weapon bonuses ---
    weapon_scores = {
        'MOD_RAILGUN':      0.20,  # Rail is the prestige weapon
        'MOD_ROCKET_SPLASH':0.10,  # RL is classic
        'MOD_ROCKET':       0.12,  # Direct rocket = harder
        'MOD_LIGHTNING':    0.08,  # LG = skill weapon
        'MOD_BFG10K':       0.05,
        'MOD_PLASMA':       0.05,
        'MOD_GRENADE':      0.08,  # Grenade = skill
        'MOD_GAUNTLET':     0.30,  # Gauntlet = incredible
        'MOD_TELEFRAG':     0.25,  # Telefrag = funny
        'MOD_CRUSH':        0.10,
    }
    score += weapon_scores.get(frag_features['weapon'], 0.05)
    
    # --- Position bonuses ---
    if frag_features['victim_airborne']:
        # Base air shot bonus
        score += 0.25
        # Extra for deep fall
        if frag_features.get('victim_vz', 0) < -300:
            score += 0.10
        # Extra for apex shot
        if abs(frag_features.get('victim_vz', 0)) < 50:
            score += 0.05
    
    # --- Multi-kill bonus ---
    kill_streak = frag_features.get('kill_streak', 1)
    streak_bonuses = {1: 0.0, 2: 0.15, 3: 0.25, 4: 0.35, 5: 0.45}
    score += streak_bonuses.get(min(kill_streak, 5), 0.45)
    
    # --- Accuracy bonus (for LG frags) ---
    if frag_features['weapon'] == 'MOD_LIGHTNING':
        lg_acc = frag_features.get('lg_accuracy', 0.0)
        if lg_acc >= 0.70:
            score += 0.30
        elif lg_acc >= 0.50:
            score += 0.15
        elif lg_acc >= 0.35:
            score += 0.05
    
    # --- Distance bonus (for rail/LG) ---
    if frag_features['weapon'] in ('MOD_RAILGUN', 'MOD_LIGHTNING'):
        dist = frag_features.get('killer_victim_distance', 0)
        if dist > 2000:
            score += 0.20
        elif dist > 1000:
            score += 0.10
        elif dist > 500:
            score += 0.05
    
    # --- Weapon combo bonus ---
    combo = frag_features.get('weapon_combo')
    if combo == 'holy_trinity':
        score += 0.20
    elif combo in ('rail_to_rocket', 'rocket_to_rail', 'lg_to_rail'):
        score += 0.10
    elif combo:
        score += 0.05
    
    # --- Game context bonuses ---
    # Last frag of the round (CA = clutch)
    if frag_features.get('is_clutch'):
        score += 0.20
    
    # Round-critical (opponent was last alive)
    if frag_features.get('is_round_winner'):
        score += 0.15
    
    # Low health kill (killer had < 25 hp)
    killer_hp = frag_features.get('killer_health', 100)
    if killer_hp <= 25:
        score += 0.15
    elif killer_hp <= 50:
        score += 0.05
    
    # Flick rail (fast angle change pre-shot)
    if frag_features.get('is_flick_rail'):
        score += 0.15
    
    # Combo air shot
    if frag_features['victim_airborne'] and frag_features['weapon'] == 'MOD_RAILGUN':
        score += 0.10  # Extra for rail air shot
    
    return min(score, 1.0)  # Cap at 1.0

BASE_SCORE = 0.10
```

#### Phase 3B: ML Scoring (once review data exists)

Once ~500 human-reviewed frags exist in Phase 2 database:

**Feature vector per frag (see frag-scoring-features.md):**
- Numeric: distance, lg_accuracy, victim_vz, killer_hp, kill_streak, round_time_remaining
- Categorical (one-hot): weapon, game_type, map_name
- Boolean: is_airshot, is_multikill, is_flick_rail, is_combo, is_clutch

**Model options (in order of recommendation):**

1. **Gradient Boosted Trees (XGBoost/LightGBM)** — Best for tabular frag features
   - Handles mixed numeric/categorical features naturally
   - Interpretable feature importances
   - Requires ~200 labeled examples minimum, 500+ for good results
   - Train/test split by demo file (not by frag) to avoid data leakage

2. **Linear Regression with feature engineering** — Baseline, fully explainable
   - Good for understanding feature weights
   - Use `sklearn.linear_model.Ridge` with feature scaling
   - Forces explicit feature design (good discipline)

3. **Random Forest** — More robust than linear, less complex than XGBoost
   - Use as a comparison model vs XGBoost

4. **Small MLP (2-3 layers)** — Only if dataset grows > 1000 labeled frags
   - More complex, less interpretable
   - Not recommended until data volume justifies it

**Training protocol:**
```python
# Features: see frag-scoring-features.md
# Target: human_rating (1-5 scale, normalized to 0.0-1.0)
# Loss: MSE for regression, or binary cross-entropy if threshold-based

from sklearn.model_selection import GroupKFold
from xgboost import XGBRegressor

# Group by demo_id to prevent leakage
gkf = GroupKFold(n_splits=5)
model = XGBRegressor(n_estimators=200, max_depth=4, learning_rate=0.05)

for train_idx, val_idx in gkf.split(X, y, groups=demo_ids):
    model.fit(X[train_idx], y[train_idx])
    # Evaluate on val_idx
```

### Implementation Complexity: Medium (rule-based Easy, ML Medium)

---

## 6. Camera Auto-Selection

### Research Findings

Academic research on automatic sports broadcast (Automatic Camera Selection in Multi-Camera Theater Recordings, 2023) and the CS2 replay systems (lhm.gg) converge on the same decision framework:

**Core principle:** Camera selection is a function of (action_type, spatial_context, dramatic_intensity).

### Decision Framework for QUAKE LEGACY

```python
def auto_select_camera(frag: dict, available_cameras: list) -> dict:
    """
    Returns a camera configuration dict:
    {
        'type': 'firstperson'|'thirdperson'|'freecam_spline'|'bullet_cam'|'overview',
        'target': entity_num or player_slot,
        'fov': degrees,
        'start_ms': timestamp,
        'end_ms': timestamp,
        'timescale': [{'at_ms': t, 'scale': s}, ...],
    }
    """
    
    # Rule 1: Air shot + projectile weapon → bullet cam
    if frag['is_airshot'] and frag['weapon'] in PROJECTILE_WEAPONS:
        return {
            'type': 'bullet_cam',
            'target': frag['frag_projectile_entity'],
            'start_ms': frag['projectile_spawn_ms'],
            'end_ms': frag['frag_time_ms'] + 500,
            'timescale': [
                {'at_ms': frag['projectile_spawn_ms'], 'scale': 0.25},
                {'at_ms': frag['frag_time_ms'] + 500,  'scale': 1.0},
            ],
        }
    
    # Rule 2: Multi-kill (3+) → overview/pull-back showing all victims
    if frag['kill_streak'] >= 3:
        map_cameras = get_map_cameras(frag['map_name'], 'overview')
        nearest = find_nearest_camera(map_cameras, frag['killer_position'])
        return {
            'type': 'freecam_spline',
            'camera_file': nearest['path'],
            'start_ms': frag['start_time_ms'] - 2000,
            'end_ms': frag['end_time_ms'] + 1000,
            'timescale': [{'at_ms': frag['start_time_ms'], 'scale': 1.0}],
        }
    
    # Rule 3: Rail gun + long distance → wide angle showing beam length
    if frag['weapon'] == 'MOD_RAILGUN' and frag.get('distance', 0) > 800:
        return {
            'type': 'freecam_spline',  
            'camera_file': find_rail_reveal_camera(frag),
            'start_ms': frag['frag_time_ms'] - 1000,
            'end_ms': frag['frag_time_ms'] + 1500,
            'timescale': [
                {'at_ms': frag['frag_time_ms'] - 200, 'scale': 0.20},
                {'at_ms': frag['frag_time_ms'] + 800,  'scale': 1.0},
            ],
        }
    
    # Rule 4: LG high-accuracy frag → first person, slow-mo on kill
    if frag['weapon'] == 'MOD_LIGHTNING' and frag.get('lg_accuracy', 0) > 0.60:
        return {
            'type': 'firstperson',
            'target': frag['killer_slot'],
            'start_ms': frag['frag_time_ms'] - 3000,
            'end_ms': frag['frag_time_ms'] + 800,
            'timescale': [
                {'at_ms': frag['frag_time_ms'] - 100, 'scale': 0.30},
                {'at_ms': frag['frag_time_ms'] + 600,  'scale': 1.0},
            ],
        }
    
    # Rule 5: Gauntlet / Telefrag → thirdperson for humiliation effect
    if frag['weapon'] in ('MOD_GAUNTLET', 'MOD_TELEFRAG'):
        return {
            'type': 'thirdperson',
            'target': frag['killer_slot'],
            'start_ms': frag['frag_time_ms'] - 1000,
            'end_ms': frag['frag_time_ms'] + 2000,
            'timescale': [
                {'at_ms': frag['frag_time_ms'], 'scale': 0.15},
                {'at_ms': frag['frag_time_ms'] + 1500, 'scale': 1.0},
            ],
        }
    
    # Default: first person, killer POV
    return {
        'type': 'firstperson',
        'target': frag['killer_slot'],
        'start_ms': frag['frag_time_ms'] - 4000,
        'end_ms': frag['frag_time_ms'] + 1000,
        'timescale': [
            {'at_ms': frag['frag_time_ms'] - 100, 'scale': 0.30},
            {'at_ms': frag['frag_time_ms'] + 600,  'scale': 1.0},
        ],
    }
```

### What Makes a "Dramatic" Camera Angle

From academic research on sports broadcast + fragmovie conventions:

1. **Action proximity:** Camera closer to impact = more dramatic. Wide shots for multi-kills (show the chaos), tight shots for 1v1 (intimacy).
2. **Anticipation framing:** Camera should be positioned so the viewer sees the frag coming 0.5-1.0 seconds before it happens.
3. **Vector alignment:** For rail shots, the best camera angle is roughly perpendicular to the rail beam direction — shows full beam length.
4. **Low angle = power:** Camera below killer looking up exaggerates dominance.
5. **Follow vs. static:** Following projectile (bullet cam) creates sustained tension. Static cameras are used for landmark frags (air shots where height matters).

### WolfcamQL Camera Commands
```
# Follow killer first person
/follow <killer_slot>

# Follow specific entity (missile)
/chase <entity_num>                        # chase with offset
cg_autoChaseMissile 1                      # auto-chase missiles from followed player
cg_autoChaseMissileFilter "rocket grenade" # which weapon missiles to chase

# Spline camera
/loadcamera cameras/<map>_overview.cfg
/playcamera

# Slow motion
/timescale 0.2                             # 20% speed
com_timescalesafe 1                        # preserve snapshots at low timescale

# Third person
cg_thirdPerson 1
cg_thirdPersonRange 80                     # distance from player
cg_thirdPersonAngle 0                      # angle offset
```

### Implementation Complexity: Medium (rule selection Easy, camera library building Hard)

---

## 7. Slow-Mo Timing

### Research Findings

Fragmovie convention analysis from the top Quake and CS fragmovies + moviemaking guides:

### The 3-Phase Slow-Mo Structure

The most effective slow-mo pattern observed across top fragmovies:

```
PHASE 1: Normal speed buildup (show context)
  Duration: 2-4 seconds before frag
  Purpose: Let viewer understand the situation
  Timescale: 1.0

PHASE 2: Pre-frag ramp-down (tension build)
  Start: 200-500ms before kill moment
  End: Kill moment
  Timescale: 0.3 → 0.1 (exponential ease-in)
  Purpose: "Something amazing is about to happen"
  Music: Often synced to beat drop here

PHASE 3: Post-frag hold (let it land)
  Duration: 500ms - 1500ms after kill
  Timescale: 0.1 → 1.0 (ease-out)
  Purpose: Viewer processes what happened, ragdoll drama
  
PHASE 4: Resume (or cut)
  Timescale: 1.0
  Option A: Hard cut to next clip
  Option B: Speed ramp back to 1.0 over 500ms
```

### WolfcamQL Implementation

```cfg
# In gamestart.cfg (generated per-frag):

seekclock 9:05          # seek to pre-roll start
video avi name fragXXX  # start recording

# The slow-mo sequence:
at 9:09.8 timescale 0.3    # 200ms before frag: start slow
at 9:10.0 timescale 0.1    # at kill: max slow
at 9:10.5 timescale 0.3    # 500ms after: ease back
at 9:11.5 timescale 1.0    # 1500ms after: back to normal
at 9:12.0 quit             # end clip
```

### Timing by Frag Type

| Frag Type | Slow-Mo Start (before kill) | Duration | Max Slow |
|---|---|---|---|
| Air shot rocket | 500ms | 2000ms | 0.10x |
| Rail snap shot | 100ms | 800ms | 0.15x |
| Rail air shot | 300ms | 1500ms | 0.10x |
| LG sustained | At kill moment | 600ms | 0.25x |
| Multi-kill | First kill -200ms | Through all kills +500ms | 0.20x |
| Gauntlet | 300ms | 2000ms | 0.10x |
| Bullet cam | Projectile spawn | Until impact +1000ms | 0.15x |

### Key Principle: Sync to Music
If the fragmovie has a music track with a known BPM, the slow-mo ramp-up should align with a beat. The kill moment should land on a downbeat or bass hit. This is done in post-production (Phase 1 edit) not at render time — render at constant timescale and adjust in FFmpeg with setpts filter.

### Implementation Complexity: Easy (pattern is fixed, parameterize per frag type)

---

## 8. Bullet Cam / Projectile Follow

### Research Findings

WolfcamQL supports `cg_autoChaseMissile` and manual `/chase <entity_num>`. The key problem is: **which rocket entity will be the frag rocket?**

### Entity Identification Strategy

```python
def find_frag_rocket(entities_at_frag_time, frag_pos, killer_slot, 
                     frag_time_ms, demo_snapshots):
    """
    Find the entity number of the rocket/projectile that caused a frag.
    
    Strategy:
    1. At frag_time_ms - delta, find all ET_MISSILE entities owned by killer
    2. The frag rocket is the one whose trajectory leads to victim position
    3. Pick earliest-spawned still-alive rocket heading toward victim
    """
    
    # Quake entity types
    ET_MISSILE = 3  # Rockets, grenades, plasma bolts
    
    # Find frag rocket candidates
    candidates = []
    
    # Look back up to 2 seconds (max rocket flight time on most maps)
    for snap_time in range(frag_time_ms - 2000, frag_time_ms, 33):
        snap = get_snapshot(demo_snapshots, snap_time)
        if not snap:
            continue
            
        for ent in snap.entities:
            if ent.eType != ET_MISSILE:
                continue
            if ent.otherEntityNum != killer_slot:  # owner check
                continue
            
            # Extrapolate trajectory to frag_time
            projected_pos = extrapolate_position(ent, frag_time_ms)
            
            # How close to victim position at frag moment?
            dist = vector_distance(projected_pos, frag_pos)
            
            if dist < 200:  # Within 200 units of kill position
                candidates.append({
                    'entity_num': ent.number,
                    'spawn_time_ms': ent.pos.trTime,
                    'projected_dist': dist,
                    'weapon': WP_ROCKET_LAUNCHER,  # inferred from context
                })
    
    if not candidates:
        return None
    
    # Best candidate: closest projected position to kill point
    best = min(candidates, key=lambda c: c['projected_dist'])
    return best['entity_num']

def extrapolate_position(entity, target_time_ms):
    """Extrapolate ET_MISSILE position using trajectory type."""
    t = (target_time_ms - entity.pos.trTime) / 1000.0
    
    if entity.pos.trType == TR_LINEAR:
        # Plasma, BFG: straight line
        return (
            entity.pos.trBase[0] + entity.pos.trDelta[0] * t,
            entity.pos.trBase[1] + entity.pos.trDelta[1] * t,
            entity.pos.trBase[2] + entity.pos.trDelta[2] * t,
        )
    elif entity.pos.trType == TR_GRAVITY:
        # Rocket, grenade: parabolic
        g = 800  # DEFAULT_GRAVITY
        return (
            entity.pos.trBase[0] + entity.pos.trDelta[0] * t,
            entity.pos.trBase[1] + entity.pos.trDelta[1] * t,
            entity.pos.trBase[2] + entity.pos.trDelta[2] * t - 0.5 * g * t * t,
        )
    else:
        return entity.pos.trBase  # Fallback
```

### WolfcamQL Bullet Cam Implementation

Once `entity_num` is identified (stored in frags.db), the gamestart.cfg for that clip:

```cfg
# Bullet cam template
seekclock {pre_roll_clock}
video avi name {clip_name}

# Follow killer to see shot being fired
follow {killer_slot}
at {shoot_time_clock} chase {frag_entity_num} 0 0 60   # z-offset 60 = slight above rocket
at {frag_time_clock} timescale 0.1                      # hit: max slow
at {frag_time_plus_1s} timescale 1.0
at {post_roll_clock} quit
```

### Alternative: cg_autoChaseMissile

Simpler but less controllable:
```cfg
cg_autoChaseMissile 1
cg_autoChaseMissileFilter "rocket"
follow {killer_slot}
# WolfcamQL will auto-switch to the next missile fired by followed player
```

**Limitation:** `cg_autoChaseMissile` chases ANY missile fired by followed player, not specifically the frag rocket. If the killer fires multiple rockets in the sequence, it may follow the wrong one.

**Recommendation:** Pre-identify frag entity_num in Phase 2 parser and store in frags.db. Use explicit `/chase <entity_num>` in gamestart.cfg.

### Trajectory Types in .dm_73

| Constant | Value | Used For |
|---|---|---|
| TR_STATIONARY | 0 | Static objects |
| TR_INTERPOLATE | 1 | Players (interpolated between snaps) |
| TR_LINEAR | 2 | Plasma, BFG |
| TR_LINEAR_STOP | 3 | Grenades (stop at ground) |
| TR_GRAVITY | 5 | Rockets (parabolic arc) |
| TR_BUGGED_GRAVITY | 6 | Some mod rockets |

### Implementation Complexity: Hard (entity tracking + trajectory math + timing sync)

---

## Existing Tools Survey

### UberDemoTools (mightycow) — PRIMARY REFERENCE
**GitHub:** https://github.com/mightycow/uberdemotools  
**Relevance:** High — already detects mid-air shots, frag runs, flick rails, multi-rail, weapon accuracy stats.  
**What to reuse:** The pattern detection logic as reference implementations. Use `UDT_json.exe` to extract base frag data, then build Phase 3 patterns on top.  
**Key patterns implemented:**
- `analysis_pattern_mid_air.cpp` — air shot detection
- `analysis_pattern_frag_run.cpp` — multi-kill grouping
- `analysis_pattern_flick_rail.cpp` — flick rail via angular velocity
- `analysis_pattern_multi_rail.cpp` — multi-kill with single rail
- `plug_in_stats.cpp` — weapon accuracy from server stats commands

### Quake Live Demo Tools (QLDT) — redrumrobot
**GitHub:** https://github.com/redrumrobot/qldt  
**Relevance:** Low — basic demo management, no pattern detection

### quakestats — brabiega
**GitHub:** https://github.com/brabiega/quakestats  
**Relevance:** Medium — processes QL match logs, extracts weapon stats, K/D, medals. Python-based. Good reference for stats extraction pipeline.

### CS2 Highlight Automator — Keanoski
**GitHub:** https://github.com/Keanoski/CS2-Highlight-Automator-for-OBS  
**Relevance:** Medium — similar pipeline concept (demo → highlight extraction → OBS recording). Uses kill streak detection.

### LHM.gg Auto Replay Generator (CS2/Dota2)
**URL:** https://lhm.gg/features/auto-replay-generator  
**Relevance:** High concept reference — commercial system that prioritizes multikills, headshots, teamkills. Confirms 3000ms multi-kill window is industry standard.

### Autohighlight: League of Legends (academic paper)
**DOI:** 10.1016/j.mlwa.2022.100348 (ScienceDirect)  
**Relevance:** High for ML approach — uses crowd-sourced view data + inflated 3D CNN for highlight scoring. The key insight: **crowd engagement (concurrent viewers at a timestamp) is the best proxy for highlight quality**. For QUAKE LEGACY, human review ratings in Phase 2 serve this same function.

### ScoringNet (action quality, academic)
**Venue:** ECCV 2019  
**Relevance:** Medium — introduces ranking loss for quality scoring. Key insight: ranking loss (frag A is better than frag B) works better than regression loss for quality prediction, because human raters are better at relative judgments than absolute scores.

---

## Recommended Implementation Order

### Sprint 1: Foundation Patterns (implement with Phase 2)
1. **Air shot detection** (Easy) — `groundEntityNum + velocity[2]` check. Zero dependencies.
2. **Multi-kill grouping** (Easy) — Time-window grouping on EV_OBITUARY stream. Zero dependencies.
3. **Weapon combo detection** (Easy) — playerState.weapon field tracking. Zero dependencies.

### Sprint 2: Advanced Patterns
4. **LG accuracy via server stats** (Medium) — Parse xstats2/mstats commands from configstrings. Requires extended parser.
5. **Rule-based frag scoring** (Easy once patterns exist) — Weight the boolean/numeric pattern fields.
6. **Slow-mo timing** (Easy) — Parameterized templates per frag type. Just write the gamestart.cfg generator.

### Sprint 3: Cinematics
7. **Camera auto-selection** (Medium) — Rule engine using detected patterns. Requires per-map camera library.
8. **Bullet cam** (Hard) — Entity tracking + trajectory extrapolation + entity_num storage + WolfcamQL integration.

### Sprint 4: ML Layer (after Phase 2 review data)
9. **ML frag scoring model** (Medium) — XGBoost on human review ratings. Requires 200+ labeled frags.
10. **Camera path library** (Hard ongoing) — Manual WolfcamQL work to build per-map camera paths.

---

## Data Pipeline Summary

```
.dm_73 demo
  → UDT_json.exe  (frags, weapons, basic stats)
  → qldemo-python (snapshots, playerState, velocity, weapon)
  → Phase 3 patterns:
      air_shot_detector.py     → frags.is_airshot, frags.victim_vz
      multikill_grouper.py     → frags.kill_streak, multikills table
      weapon_combo_detector.py → frags.weapon_combo
      lg_accuracy_tracker.py   → frags.lg_accuracy
      frag_scorer.py           → frags.ai_score (0.0-1.0)
      camera_selector.py       → frags.camera_type, frags.camera_config_json
      entity_tracker.py        → frags.frag_entity_num (for bullet cam)
  → frags.db (all features stored)
  → Phase 2 renderer uses camera_config_json to write gamestart.cfg
```
