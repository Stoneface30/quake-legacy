# Review dossier — observability matrix

*Measured 2026-09-04 against the live caches. Every number here was counted,
not estimated. This document exists so the dossier is built from what is
actually observable and says UNKNOWN everywhere else.*

> **ABSENCE FROM A CLIENT DEMO IS NOT NEGATIVE GAME TRUTH.**
> Unknown means UNKNOWN. Not `0`. Not `0%`.

---

## Summary

| field group | status | note |
|---|---|---|
| HP / armor | **PARTIAL — 47.3%** | 7.4% by design -> 30.4% -> 47.3%; the rest is a real limit |
| damage dealt/taken | **PARTIAL** | LG-context only |
| **outgoing** action accuracy | **DERIVABLE, NOT BUILT** | the path is proven below |
| cached LG accuracy | **UNAVAILABLE** | the table is an empty scaffold |
| movement | **AVAILABLE** | 98%+ |
| aim / geometry | **AVAILABLE** | 98%+ |
| round state | **AVAILABLE** / DERIVED | alive curve is arithmetic |
| enemy HP / armor | **UNAVAILABLE** | never in a client demo |

---

## HP and armor

| field | source | status | coverage | scope |
|---|---|---|---|---|
| `health_at_frag` | playerstate | OBSERVED | **15,743 / 33,316 user frags (47.3%)** | own camera only |
| `armor_at_frag` | playerstate | OBSERVED | same | own camera only |
| `engagement_start_health` / `_armor` | playerstate, −10 s | OBSERVED | same | own camera only |
| `min_health_10s` / `min_armor_10s` | playerstate | OBSERVED | same | own camera only |
| `biggest_drop_10s`, `health_recovered` | derived from series | DERIVED | same | own camera only |
| enemy HP / armor | — | **UNAVAILABLE** | — | not in a client demo |

**The 7.4% was by design, not a data limit.** `extract_health_armor.py`
selected only CA clutches and MAIN_CA rows scoring ≥ 10 — 2,705 events across
1,251 demos — because health was then wanted only for likely-used frags. The
extractor now takes `--all`. The widened pass ran: **2,272 demos, 8,121
events filled, 0 failures, 898s** — taking coverage from 2,701 (7.4%) to
**11,501 (31.4%)**, a 4.3x improvement.

**It did not reach 100%, and that is not yet explained.** The candidate map
listed 14,581 events across 3,424 demos; the run covered 2,272 demos and
filled 8,121. The remainder may be demos whose file is missing, or frags
where the playerstate series does not cover that moment. Worth one bounded
look before the dossier promises HP on every clip — until then the honest
figure is 31.4% and the panel must say UNKNOWN for the rest.

**Scope limit that must reach the UI:** health is the RECORDER's. On a
foreign-camera observation it is the cameraman's health, not the actor's, and
must not be shown as the actor's.

---

## Damage

| field | source | status | coverage |
|---|---|---|---|
| `lg_damage_burst_3s` (dealt, LG window) | recognizer | PARTIAL | 13,615 (37.2%) |
| `lg_taken_total_dmg` (taken) | recognizer | PARTIAL | 13,569 (37.1%) |
| `lg_taken_lg_dmg` | recognizer | PARTIAL | 13,569 (37.1%) |
| damage to a NAMED target | — | **UNAVAILABLE** | attribution not persisted |

Damage exists only in an LG context. There is no general per-engagement
damage ledger, and inventing one from health deltas would attribute the
victim's fall damage or a teammate's splash to the user.

---

## Action accuracy — the important finding

### Cached LG accuracy is **not usable**

`recognition_lg_engagements` holds 13,696 rows whose `series` is
`{"my_fire": [], "victim_pain": [], "my_pain": []}`. Sampled 4,000 rows:
**0 (0.0%) contain any `my_fire` data.** The table is a scaffold that was
never filled. Nothing about outgoing aim can be read from it.

`lg_incoming_hit_ratio` exists (37.1%) but is **INCOMING** — the share of
shots that hit *the user*. It describes the opponent's aim. Showing it as the
user's accuracy would be exactly backwards.

### Outgoing accuracy IS derivable — path proven, not built

`semantic_events_v1` holds the two halves:

| stream | count | meaning |
|---|---|---|
| `fire_weapon`, `source='playerstate'` | **3,074,889** (weapon on 3,074,888) | the RECORDER's own shots |
| `pain`, with `client_num` | **1,000,344** of 1,150,558 | who was hit, and when |

Recorder shots by weapon: LG (6) 2,359,880 · rocket (5) 399,209 · plasma (8)
143,547 · **rail (7) 99,929** · grenade (4) 39,022 · machinegun (2) 22,817.

So for an engagement window: **denominator** = recorder `fire_weapon` events
of that weapon inside the window; **numerator** = `pain` events on the victim
inside the window. Both are per-tick server facts, both are already cached,
and no reparse is needed.

**Caveats that must be respected when this is built:**
- LG fires ~20×/second, so "shots" for LG means attack ticks, not clicks —
  the denominator is a tick count and must be labelled as one.
- A `pain` event proves damage, not *whose* damage. With one attacker in the
  window it is safe; in a crossfire it is not, and the confidence must drop.
- Weapon ids here are the **WP_** launcher space, not MOD_.

---

## Movement, aim and geometry — available

| field | coverage |
|---|---|
| `killer_speed`, `attacker_speed_percentile` | 35,987 (98.3%) |
| `victim_speed`, `victim_air_height` | 36,432 / 36,462 (99.5%) |
| `flick_degrees`, `flick_duration_ms`, `deg_per_sec` | 35,964 (98.2%) |
| `distance` | 35,886 (98.0%) |
| `visibility_ms` | 36,500 (99.7%) |
| movement moments (HIGH_SPEED / JUMPPAD) | 1,333 / 40,342, 12,767 linked to a frag |

---

## Round state

| field | status |
|---|---|
| round number, duration, kills, per-actor frag counts | OBSERVED — from `kill_occurrences_v1` |
| team sizes | OBSERVED — `player_teams_v1` (RED 14,927 / BLUE 14,905 / UNKNOWN 2,775) |
| alive progression | **DERIVED** — team size minus observed deaths, one life per round in CA |
| round win / loss | **PARTIAL** — not reliably attributed yet |

---

## What the dossier must therefore show

Available now: weapon, opponent, map, round, time, camera provenance,
occurrence id, machine score and rank, usage state, round frag counts, alive
curve (labelled DERIVED), movement, flick, distance, visibility, trait chips.

Available on 31.4% of frags: HP and armor at start / min / frag, and the
low-HP tags that follow. The other 68.6% must read UNKNOWN, not 0.

Derivable but NOT BUILT: outgoing action accuracy per weapon, per-engagement
damage beyond the LG window.

Never available: enemy HP and armor, and any actor-state field on a
foreign-camera observation.


---

## HP denominator — the full breakdown (2026-09-05)

Of **33,316** confirmed user frag occurrences:

| category | count | share |
|---|---|---|
| **A** observed and extracted | **15,743** | **47.3%** |
| **C** foreign camera — health is the cameraman's | 719 | 2.2% |
| **D** demo processed, no playerstate at that moment | 16,854 | 50.6% |
| **E** demo file missing | 0 | 0.0% |

**How D was split, and why it mattered.** At first D was 64.6% and looked
like one thing. It was two. The extractor's resume is keyed by DEMO, not by
frag — correct while the candidate set is fixed, wrong the moment it widens.
The 1,251 demos from the original narrow run were skipped wholesale by the
`--all` pass, so only their high-scoring frags ever got a value: those demos
measured **17.1%** coverage against **45.3%** for demos the widened pass
actually processed.

Bumping `EXTRACTOR_VERSION` to 2 reopened 1,153 demos and filled 5,779 more
events with zero failures, taking coverage from 30.4% to **47.3%**.

What remains in D is the genuine limit: the recorder's playerstate series
does not cover that moment. **Do not run another pass against it** — the
answer is UNKNOWN and UNKNOWN is correct.
