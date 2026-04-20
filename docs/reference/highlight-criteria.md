# Highlight Criteria Reference

**Gate:** P3-0 user session to confirm before 6,465-demo batch run.
**Scope:** CA (Clan Arena), QL `.dm_73` demos.

> **Source:** `docs/specs/highlight-criteria-v1.md` (base). FT-2 locked overrides from `CLAUDE.md` applied inline (marked [FT-2]). v2 spec not yet authored — see open-items.md.

---

## Scoring Scale

| Final Score | Tier | Role                              |
|-------------|------|-----------------------------------|
| >= 150      | T1   | Elite / Part climax. 1-3 per demo max. |
| 90-149      | T2   | Main-meal backbone. 5-15 per demo. |
| 40-89       | T3   | Filler / cinematic. Intros, outros. |
| < 40        | drop | Not a highlight.                  |

Cap per demo: T1 max 3, T2 max 12, T3 max 20.

---

## Weapon Base Scores

| Weapon | MOD value | Base Score |
|--------|-----------|-----------|
| Railgun direct | 10 | 40 |
| Rocket direct | 6 | 35 |
| BFG direct | 12 | 35 |
| Grenade direct | 4 | 30 |
| Lightning gun | 11 | 28 |
| Telefrag | 18 | 25 |
| Gauntlet | 2 | 20 |
| Plasma direct | 8 | 22 |
| Rocket splash | 7 | 15 |
| Grenade splash | 5 | 12 |
| MG / HMG | 3 / 32 | 8-10 |
| Shotgun | 1 | 5 |
| Plasma splash | 9 | 10 |
| MOD_SUICIDE, ENV kills | 20,19,17,14-16,22 | skip |
| Teamkill / self-kill | — | skip |
| During timeout | — | skip |
| During warmup | — | skip |

**Weapon tier summary (S/A/B/C):**
- S: Rail, Rocket direct, LG (28-40)
- A: Grenade direct, Plasma direct, BFG direct, Telefrag (22-35)
- B: Rocket splash, Grenade splash, Gauntlet (12-20)
- C: MG, SG, plasma splash, nails (5-10)

---

## Context Modifiers (additive)

| Condition | Modifier |
|-----------|---------|
| Airshot (victim airborne >= 300 ms, direct-hit weapon only) | +50 |
| Multi-kill: double (2 kills within 3 s window) | +30 to anchor |
| Multi-kill: triple (3 kills) | +60 |
| Multi-kill: quad+ (4+) | +90, T1 guarantee |
| Long-distance kill (> 1500 units, trajectory weapons) | +15 |
| Last-man-standing clutch | +40 |
| Round-winning frag | +25 |
| Quad Damage active at kill | +15 |
| Low-health killer (<= 30 HP) | +10 |
| Opening kill of round (within 5 s of start) | +8 |
| Revenge kill (killed by this victim in previous round) | +5 |
| Spam streak: 5+ same low-tier weapon in 30 s | -5 per extra kill |

---

## Multi-Kill Window

Full CA round — the entire round is the multi-kill window. Window = 3 s between
first and last kill for the cluster bonus. Multi-kill window definition per CLAUDE.md FT-2.

---

## Airshot Definition

- Victim airborne for minimum **200 ms** (FT-2 locked value from CLAUDE.md)
- Detect via: victim Z-velocity > |100 units/s| OR `groundEntityNum == ENTITYNUM_NONE`
  in the 3 snapshots before kill
- Any weapon qualifies (FT-2: "any weapon, 200ms min air time")
- Splash airshots do NOT count

---

## LG Accuracy Bands

Per CLAUDE.md FT-2 [FT-2]: LG frags are accuracy-banded at thresholds 40% / 50% / 56%.
LG base weight = 1.5 (from weapon weights table). Bands applied as multipliers on the base score of 28.

| Accuracy threshold | Multiplier | Final LG score |
|--------------------|-----------|----------------|
| >= 40% (low band)  | 0.7×      | 1.05           |
| >= 50% (mid band)  | 1.0×      | 1.50           |
| >= 56% (high band) | 1.3×      | 1.95           |

Note: multipliers apply to the FT-2 weight (1.5), not to the raw base score of 28.
The base score of 28 is used for sorting/tier; the weighted score drives flow-cut priority.

---

## Clip Window Defaults

| Parameter | Value |
|-----------|-------|
| pre_roll_ms | 8000 (8 s before kill) |
| post_roll_ms | 5000 (5 s after kill) |
| Multi-kill extension | `(last_kill - anchor) + 5000` |

---

## Detection Sources

| Signal | Source in demo |
|--------|----------------|
| Kill event + time + killer/victim/weapon | Snapshot `EV_OBITUARY` entity events |
| Player positions (airshot) | Entity origin / playerstate origin |
| Victim Z-velocity | Entity trajectory fields |
| Round boundaries | `cs 662 <ms>` server command |
| Timeout windows | `CS_TIMEOUT_BEGIN/END_TIME` configstrings |
| LMS marker | `cp` server command text match |
| Quad powerup | playerstate.powerups[PW_QUAD] > serverTime |
| Health at kill | playerstate.stats[STAT_HEALTH] |
