# Highlight Criteria v1 — Phase 2 Fragmovie Selection Rules

**Status:** Draft v1 (Claude-authored defensible defaults)
**Date:** 2026-04-17
**Scope:** CA (Clan Arena) demos, QL `.dm_73` format
**Consumer:** `phase2/score_frags.py`, `phase2/generate_cap_cfg.py`
**Pre-requisite:** Gate P3-0 user review session to lock criteria before 2,277-demo batch

---

## 1. Philosophy

A fragmovie highlight is not just "a kill." It is a kill that carries **narrative weight**:
surprise, skill, context, or consequence. We score per-frag on a 0-200 scale.

- **> 120** = T1 elite / peak (airshot rail, triple, LMS clutch rail, quad-damage rampage)
- **80-120** = T2 main-meal (clean rail, rocket direct hit, double, good context)
- **40-80**  = T3 filler / cinematic (standard kill with decent context, intro candidates)
- **< 40**   = skip (shotgun pokes, gauntlet spam, no context)

Tier mapping aligns with Rule P1-A (T1 rare/peak, T2 main meal, T3 filler).

---

## 2. Weapon Tier Weights (base score)

| Weapon | MOD | Base Score | Rationale |
|---|---|---|---|
| Railgun | MOD_RAILGUN (10) | **40** | Hitscan precision, the signature QL weapon |
| Rocket direct hit | MOD_ROCKET (6) | **35** | Prediction + timing, high skill |
| Lightning gun | MOD_LIGHTNING (11) | **28** | Sustained tracking, tier-S in QL meta |
| Plasma direct | MOD_PLASMA (8) | **22** | Uncommon, satisfying thunk |
| Grenade direct | MOD_GRENADE (4) | **30** | Rare direct hit — very cinematic |
| BFG direct | MOD_BFG (12) | **35** | Novelty weapon, rare in serious play |
| Rocket splash | MOD_ROCKET_SPLASH (7) | **15** | Decent, needs combo/context |
| Plasma splash | MOD_PLASMA_SPLASH (9) | **10** | OK as filler only |
| Grenade splash | MOD_GRENADE_SPLASH (5) | **12** | OK for multikills |
| Gauntlet | MOD_GAUNTLET (2) | **20** | Humiliation — cinematic when clean |
| Machine gun | MOD_MACHINEGUN (3) | **8** | Filler, need combo |
| Shotgun | MOD_SHOTGUN (1) | **5** | Filler unless point-blank headshot |
| BFG splash | MOD_BFG_SPLASH (13) | **5** | Rare, low skill signal |
| Telefrag | MOD_TELEFRAG (18) | **25** | Classic Q3 moment |
| Nail (HMG) | 24 / 31 | **10** | QL-specific filler |
| **Excluded** | | | |
| Suicide | MOD_SUICIDE (20) | skip | Never useful |
| Falling | MOD_FALLING (19) | skip | Environmental |
| Crush | MOD_CRUSH (17) | skip | Environmental |
| Trigger hurt | MOD_TRIGGER_HURT (22) | skip | Environmental |
| Water/Slime/Lava | 14/15/16 | skip | Environmental |

**Rationale:** Rail weighted highest because it's the skill-expression weapon in QL.
Rocket direct slightly below rail because while impressive it's often the POV's own
shot; rail direct is unambiguous skill. Splash damage discounted heavily because it's
the majority of frags and would drown the signal.

---

## 3. Context Modifiers (additive)

Modifiers stack on top of the base weapon score. Each modifier is rationale-driven.

### 3.1 Airshot — **+50**
- **Definition:** victim is airborne (not touching ground) at moment of kill for >= 300ms prior
- **Minimum conditions:** victim Z-velocity > |100 units/s| OR victim `groundEntityNum == ENTITYNUM_NONE` in the 3 snapshots before kill
- **Must combine with:** direct-hit weapons only (rail, rocket, plasma, grenade direct).
  Splash airshots do NOT count — too common.
- **Rationale:** Airshot-rails are the peak fragmovie shot. +50 puts a rail airshot at 90 baseline, guaranteed T2/T1.

### 3.2 Multi-kill (same killer, <= 3000ms window) — **+30 per extra kill**
- **Double:** 2 kills within 3s = +30 to the FIRST kill (anchor), tag second as "combo"
- **Triple:** 3 kills within 3s = +60 total
- **Quad:** 4+ kills = +90+ and tier-1 guarantee
- **Window:** 3000ms measured between first and last kill (not consecutive pairs)
- **Rationale:** The anchor frag carries the full clip. Secondary frags are "chained" into the
  same clip (extend post_roll). 3s matches human attention span for a "moment."

### 3.3 Long-distance kill (rail/rocket) — **+15**
- **Threshold:** killer-victim distance > 1500 Quake units (approx. one long hallway)
- **Applies to:** rail, rocket direct, grenade direct (trajectory weapons)
- **Rationale:** Cross-map rails are visually impressive and read well on screen.

### 3.4 Last-man-standing situation — **+40**
- **Definition:** killer is alone on their team vs 2+ opponents at moment of kill
- **CA-specific:** check "You are the only one left" `cp` server command in recent history (< 15s before kill)
- **Rationale:** LMS clutch frags are narrative peaks — the round pivots on this shot.

### 3.5 Round-winning frag — **+25**
- **Definition:** kill that ends a CA round (causes one team to reach 0 alive players)
- **Detection:** next round starts within 2s of the kill, OR scores command shows round-end
- **Rationale:** Final-blow frags structure the fragmovie timeline and make good section-end clips.

### 3.6 Quad Damage active — **+15**
- **Definition:** killer has quad damage powerup at time of kill
- **Detection:** playerstate `powerups[PW_QUAD]` > server_time at frag
- **Rationale:** Quad kills are signature moments in many Q3/QL fragmovies.

### 3.7 Low-health frag (clutch) — **+10**
- **Definition:** killer health <= 30 at time of kill
- **Rationale:** Surviving on low HP and still getting the kill = clutch narrative.

### 3.8 Opening kill of round — **+8**
- **Definition:** first frag within 5s of round start
- **Rationale:** Opening picks set tempo — good for section openers.

### 3.9 Revenge kill — **+5**
- **Definition:** killer was killed by this victim in a previous round
- **Rationale:** Minor narrative bump, good for Part-level editing.

---

## 4. Negative Modifiers (subtractive)

### 4.1 During timeout — **-999 (skip)**
- Any kill within a `timeOut_t` window is dropped. Game was paused.

### 4.2 Warmup kill — **-999 (skip)**
- Kills before `trap_GetGameStartTime()` dropped.

### 4.3 Self-kill / teamkill — **-999 (skip)**
- `killer == victim` or killer and victim on same team = drop.

### 4.4 Spam-streak penalty — **-5 per additional kill in a 30s window with no variety**
- If killer gets 5+ consecutive kills with the same low-tier weapon (MG/SG) in 30s, penalize each.
- Prevents machinegun spam from filling the movie.

---

## 5. Tier Assignment (final)

After `base + modifiers`:

| Final Score | Tier | Role |
|---|---|---|
| >= 150 | **T1** | Elite / Part climax. Rare. 1-3 per demo max. |
| 90-149 | **T2** | Main-meal backbone. 5-15 per demo typical. |
| 40-89  | **T3** | Filler / cinematic. Intros, outros, transitions. |
| < 40   | drop | Not a highlight. |

**Cap per demo (prevents one demo dominating):**
- Max 3 T1 frags per demo (keep rarest)
- Max 12 T2 frags per demo
- Max 20 T3 frags per demo

---

## 6. Clip Window Defaults (from feedback_phase2_recording_windows)

- **pre_roll_ms:** 8000 (8s before kill — shows setup, positioning)
- **post_roll_ms:** 5000 (5s after — reaction, next action, death animation)
- **Multi-kill extension:** extend post_roll to `(last_kill - anchor) + 5000`

---

## 7. Weapon Tier Summary (S/A/B/C from CLAUDE.md)

| Tier | Weapons | Base score range |
|---|---|---|
| **S** | Rail, Rocket direct, Lightning | 28-40 |
| **A** | Grenade direct, Plasma direct, BFG direct, Telefrag | 22-35 |
| **B** | Rocket splash, Grenade splash, Gauntlet | 12-20 |
| **C** | MG, SG, plasma splash, nails | 5-10 |
| **X** | Environmental, suicide, teamkill | skip |

---

## 8. Open Questions (Gate P3-0 discussion items for user)

1. **Airshot threshold:** is 300ms airborne too lenient? Should we require >500ms for T1?
2. **Multi-kill window:** 3000ms — should this be 4000ms to catch slower rocket combos?
3. **Long-distance:** 1500 units — verify against real map distances (campgrounds is ~3000 long).
4. **Should LMS-clutch outrank airshot?** Current: airshot +50 > LMS +40. Flip?
5. **Cap per demo** — is 3 T1 / demo too restrictive? Some elite demos have 10+.
6. **Railjump+rocket combos** — should we add detection via Z-velocity + rocket fire?
7. **Keep or drop shotgun/MG entirely?** Current: kept with low score. User may want hard exclude.

Once user approves, v1 becomes v1-locked and 2,277 demos are scored against it.

---

## 9. Data Dependencies

For full implementation, the demo parser must surface:

| Signal | Source | Status |
|---|---|---|
| Kill event + timestamp + killer/victim/weapon | snapshot EV_OBITUARY entity events | qldemo-python stubs this; needs UDT_json or full snapshot parsing |
| Player positions (for airshot distance/height) | entity origin / playerstate origin | same as above |
| Victim Z-velocity (airshot detection) | entity velocity/trajectory | same as above |
| Round boundaries | WolfcamQL `trap_GetRoundStartTimes` OR QL `scores` server commands | available via scores command parsing |
| Timeout windows | WolfcamQL `trap_Get_Demo_Timeouts` | available via configstring CS_TIMEOUT |
| Per-round scoreboard | QL `scores` server command | **available now** (parsed) |
| LMS "only one left" marker | `cp` server command text match | **available now** (parsed) |
| Quad/powerup state | snapshot playerstate.powerups | needs full snapshot parse |
| Health at kill | snapshot playerstate.stats[STAT_HEALTH] | needs full snapshot parse |
| Map name / gametype | configstring CS_SERVERINFO | **available now** |

**Blocking item:** full snapshot entity parse (adds ~400 LOC to qldemo-python) OR compile UDT_json.exe from `tools/quake-source/uberdemotools/UDT_DLL/`. Either unlocks full criteria.
