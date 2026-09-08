> **Superseded ranking — read this first (2026-09-01).**
>
> The tables below were produced before `transition_match.py` was fixed, so
> their rankings no longer reproduce. The analysis that motivated the fixes
> stands and is what prompted them; three of its findings are now enforced in
> code (`45f65d0d` and follow-up):
>
> - implausible projectile speeds are rejected (`speed_plausible`),
> - a moment re-saved under a second filename can no longer be its own
>   Scene B (`event_signature`),
> - map names are case-folded, so one arena no longer reads as two.
>
> Two corrections to the reasoning below:
>
> 1. **Straightness is not evidence of a fabricated path.** 100% of paths
>    inside the plausible-speed band are perfectly straight (arc == chord).
>    Rockets fly straight. Speed alone is the discriminator.
> 2. **The speed floor is 800 u/s, not 600.** The arc-speed histogram is
>    bimodal with a trough at 600-900 u/s; the floor sits at the top of that
>    trough. This matches the 800-1300 band chosen by hand here, now with the
>    distribution as its justification.
>
> Corrected top 10 Scene A, every entry at 895-1101 u/s:
>
> | # | frag | map | flight | arc speed | score | top Scene B |
> |---|---|---|---|---|---|---|
> | 1 | 13114 | campgrounds | 1300 ms | 1101 u/s | 30.5 | 24326 (1.06) |
> | 2 | 2553 | quarantine | 1300 ms | 1020 u/s | 29.0 | 37977 (1.01) |
> | 3 | 28580 | trinity | 1475 ms | 1006 u/s | 27.5 | 24326 (1.08) |
> | 4 | 10028 | campgrounds | 1250 ms | 1043 u/s | 25.2 | 24326 (1.08) |
> | 5 | 9141 | asylum | 1425 ms | 991 u/s | 24.0 | 24326 (1.02) |
> | 6 | 33099 | campgrounds | 1425 ms | 992 u/s | 23.8 | 24326 (1.07) |
> | 7 | 27622 | trinity | 1350 ms | 1039 u/s | 20.5 | 24326 (1.09) |
> | 8 | 2110 | overkill | 1225 ms | 895 u/s | 19.5 | 26042 (1.03) |
> | 9 | 10668 | campgrounds | 1225 ms | 996 u/s | 18.0 | 24326 (1.03) |
> | 10 | 12633 | campgrounds | 1325 ms | 1004 u/s | 17.1 | 24326 (1.05) |
>
> 815 of 1,377 candidates (59%) now pass the speed contract, and 163 moments
> are recorded under more than one filename (331 frags).
>
> Frag 24326 is top Scene B for 8 of the 10. That is a real weakness in the
> scoring rather than a property of the corpus: payoff saturates and breaks
> most ties, so one high-scoring frag wins nearly every shortlist. Diversity
> is not yet a scored component.

# PROJECTILE_BRIDGE — Ranked Candidate Set

Analysis only. No bridge was built, nothing was rendered, nothing was written to any
database. Every number below comes from a query actually run against
`creative_suite/database/frag_recognition.db` (opened `mode=ro`) and
`creative_suite/database/frags_rebuilt.db` (map names) on 2026-09-01,
using `creative_suite/engine/transition_match.py` and
`creative_suite/engine/director_preview.py::projectile_evidence` unmodified.

Frags are identified by numeric id, map and `server_time_ms` only. No demo filenames.

---

## 1. How many Scene A candidates exist

`recognition_projectile_paths` holds **4,391 rows**, all with a distinct
`(demo_name, server_time_ms)` key. Joined to `recognized_frags` this fans out to
4,400 rows, because **9 paths match two frag rows each** — worth knowing before
anyone sums a join result.

Grading every path against `projectile_evidence` (>= 8 points, >= 200 ms span,
>= 64 u displacement, positive flight, finite coords):

| Outcome | Paths |
|---|---|
| **usable AND ride-able** (`projectile_evidence` usable **and** `path_metrics` returns metrics) | **1,370** |
| rejected: `too_few_points` (< 8 points) | 1,687 |
| rejected by `path_metrics` only (< 400 ms or < 3 points, after passing evidence) | 1,064 |
| rejected: `flight_too_short` (< 200 ms) | 197 |
| rejected: `displacement_too_small` (< 64 u) | 82 |

**1,370 is the answer to "how many Scene A candidates passed the contract".**
All 1,370 join to a distinct frag id (no duplicates, no orphans), spread over
33 map-name strings. 1,326 are `CONFIRMED`, 44 are `LIKELY`.

Two contract details that matter:

- **The two filters disagree.** `projectile_evidence` demands 8 points / 200 ms;
  `path_metrics` demands 3 points / 400 ms. Neither is a subset of the other.
  Calling `load_candidates()` on its own returns **1,377** rows, of which **51 fail
  `projectile_evidence`** — all for `displacement_too_small`. If the bridge is
  built on `load_candidates()` alone it will admit 51 paths that the authoritative
  contract says film nothing. The pool used below is the intersection.
- **256 paths have `launch.t == impact.t`.** Confirmed as 25 ms snapshot
  quantisation of the scalars, not corruption — every one of them still has a real
  point series. Everything below is measured from the point series.

Class memberships **overlap heavily** and must not be summed. All 1,370 usable
candidates carry at least one class; the largest memberships are
`DIRECT_ROCKET` 992, `DIRECT_CONFIRMED_GEO` 913, `DODGE_TO_KILL` 480,
`NEAR_MISS_ROCKET` 436, `NEAR_MISS_RAIL` 262, `AIR_ROCKET` 222.
The true union is 1,370.

---

## 2. The physics problem that reshapes the ranking

`pick_scene_a()` prefers long flights. Measuring chord speed on the point series
across the whole usable pool shows why that preference is dangerous:

| Flight duration | n | median chord speed |
|---|---|---|
| 400–700 ms | 727 | **1,048 u/s** |
| 700–1000 ms | 261 | 998 u/s |
| 1000–1500 ms | 190 | 870 u/s |
| 1500 ms+ | 192 | **211 u/s** |

The speed histogram is sharply bimodal: 728 of 1,370 paths sit in the
900–1,200 u/s band, which is the real Quake Live rocket (900 u/s nominal; the
canonical reference frag 4121 measures 1,062 u/s over 300 ms / 319 u).
The rest trail off toward zero. **400 of the 1,312 rocket-weapon paths measure
below 600 u/s**, which no rocket does.

Inspecting the slow ones: they are perfectly straight (1,311 of 1,370 have
`arc <= 1.005 x chord`; `deviation_u` median is 0.0), sampled at a clean 25 ms
step, and travel at an exactly constant per-segment speed. E.g. frag 2740 —
118 points, 2,925 ms, 680 u, every segment 233 u/s to three significant figures.
That is a straight line drawn between two endpoints, not an observed rocket.

**Consequence: of the 276 candidates with duration >= 1200 ms — the pool
`pick_scene_a()` draws from — 213 (77%) have implausible chord speed.** Ranking
by "longest flight" systematically selects the least trustworthy paths. The
ranked set below is therefore given twice: as the module returns it, and
filtered to the physically-plausible band.

Physically-plausible pool (800–1,300 u/s): **798** candidates,
**380** of them with >= 600 ms runway, **48** with >= 1,200 ms.

---

## 3. Top 10 Scene A — recommended set

Pool: passes `projectile_evidence`, passes `path_metrics`, chord speed in the
800–1,300 u/s rocket band, duration >= `MIN_RUNWAY_MS` (600 ms). Ordered by
`pick_scene_a()`'s own criterion (highlight score, then duration).
Scene B shortlists are `shortlist_scene_b(..., top_n=3)` with default
`prefer_different_map=0.15`. Score components: `spd` speed match, `pit` pitch
match, `run` runway, `pay` payoff. Max possible total is 1.15, not 1.0.

### A1 — frag 13278 · campgrounds · ROCKET_SPLASH
score 46.59 · flight 1,000 ms · 1,073 u · 41 points · 1,073 u/s · terminal pitch −0.013 · CONFIRMED
Classes: FLICK_SHOT, EXTREME_SPEED, CLEAN_FLICK, EXTREME_FLICK, HIGH_SPEED_AIM_TRANSITION, NEAR_DIRECT, NEAR_MISS_RAIL, DODGE_TO_KILL

| | Scene B | map | total | spd | pit | run | pay | why |
|---|---|---|---|---|---|---|---|---|
| A | 24326 | quarantine | 1.072 | .955 | .978 | .938 | .818 | near-identical speed and dead-level pitch on both sides; 1,125 ms of runway; strong payoff |
| B | 28580 | trinity | 1.015 | .938 | .994 | 1.00 | .550 | best pitch continuity in the pool and maximum runway, but a weak frag to land on |
| C | 31304 | hiddenfortress | 1.005 | .988 | .961 | .646 | .750 | tightest speed match of the three; loses on runway (775 ms) |

**Caveat:** 24326's stored map string is the case variant `qUARanTINe`. See §5.

### A2 — frag 26042 · quarantine · ROCKET_SPLASH
score 46.00 · flight 775 ms · 713 u · 32 points · 921 u/s · terminal pitch −0.407 · CONFIRMED
Classes: CLUTCH_1V4_PLUS, DIRECT_CONFIRMED_GEO, AIR_ROCKET_GEO, NEAR_MISS_ROCKET, DODGE_TO_KILL, REACTION_SHOT

| | Scene B | map | total | spd | pit | run | pay | why |
|---|---|---|---|---|---|---|---|---|
| A | 37632 | campgrounds | 0.976 | .992 | .918 | .708 | .615 | the only strong partner that matches A2's downward pitch (−0.49 vs −0.41); speed is all but identical |
| B | 13278 | campgrounds | 0.975 | .858 | .628 | .833 | .932 | wins purely on payoff — pitch continuity is poor (level launch after a diving arrival) |
| C | 24326 | quarantine | 0.973 | .898 | .584 | .938 | .818 | same trade as B: payoff and runway carrying a bad pitch match |

### A3 — frag 38457 · campgrounds · ROCKET
score 45.20 · flight 650 ms · 691 u · 27 points · 1,064 u/s · terminal pitch −0.035 · CONFIRMED
Classes: DIRECT_ROCKET, ROCKET_JUMP_FRAG, VERTICAL_ACTION, CLUTCH_1V3, DIRECT_CONFIRMED_GEO, NEAR_MISS_RAIL, DODGE_TO_KILL, LOW_HP_FRAG, HEAVY_DAMAGE_SURVIVED

| | Scene B | map | total | spd | pit | run | pay | why |
|---|---|---|---|---|---|---|---|---|
| A | 24326 | quarantine | 1.071 | .964 | .956 | .938 | .818 | level-to-level, matched speed, long runway, high payoff — every component strong |
| B | 28580 | trinity | 1.016 | .946 | .984 | 1.00 | .550 | maximum runway and near-perfect pitch; payoff is the only weak leg |
| C | 31304 | hiddenfortress | 1.012 | .997 | .983 | .646 | .750 | essentially perfect motion match, short runway |

### A4 — frag 19639 · overkill · ROCKET
score 43.50 · flight 650 ms · 726 u · 27 points · 1,117 u/s · terminal pitch −0.427 · CONFIRMED
Classes: DIRECT_ROCKET, AIR_ROCKET, SPEED_TARGET_FRAG, DIRECT_CONFIRMED_GEO, AIR_ROCKET_GEO, PREDICTION_TEMPORAL, NEAR_MISS_RAIL, DODGE_TO_KILL

| | Scene B | map | total | spd | pit | run | pay | why |
|---|---|---|---|---|---|---|---|---|
| A | 13278 | campgrounds | 1.008 | .961 | .608 | .833 | .932 | ranked first almost entirely on payoff; the pitch break (diving arrival into a level launch) is the worst in this shortlist |
| B | 2553 | quarantine | 1.006 | .914 | .954 | 1.00 | .580 | the honest motion match: both diving at ~−0.45, full runway |
| C | 37977 | asylum | 0.995 | .946 | .937 | .604 | .823 | good pitch and payoff, penalised on 725 ms runway |

**Caveat:** A4 and A5 are the same physical event (see §5).

### A5 — frag 34346 · overkill · ROCKET
score 43.50 · flight 650 ms · 726 u · 27 points · 1,117 u/s · terminal pitch −0.427 · CONFIRMED
Identical classes and identical shortlist to A4 — **this is the same frag recorded in a
second demo file** (same map, same `server_time_ms` 465350, same victim slot, different
content hash: a ~3 MB full demo and a ~166 KB re-saved excerpt). Treat A4 and A5 as one
candidate; the shortlister does not.

### A6 — frag 37977 · asylum · ROCKET
score 41.15 · flight 725 ms · 766 u · 30 points · 1,056 u/s · terminal pitch −0.470 · CONFIRMED
Classes: DIRECT_ROCKET, SPEED_TARGET_FRAG, DODGE_AND_KILL, CLUTCH_1V2, DIRECT_CONFIRMED_GEO, AIR_ROCKET_GEO, NEAR_MISS_ROCKET, DODGE_STRAFE, LOW_HP_FRAG, HEAVY_DAMAGE_SURVIVED

| | Scene B | map | total | spd | pit | run | pay | why |
|---|---|---|---|---|---|---|---|---|
| A | 2553 | quarantine | 1.033 | .966 | .997 | 1.00 | .580 | the best pure motion match in the whole recommended set — pitch delta 0.003, full runway |
| B | 13278 | campgrounds | 1.007 | .984 | .565 | .833 | .932 | payoff-driven; pitch discontinuity is severe |
| C | 26042 | quarantine | 1.002 | .872 | .936 | .646 | .920 | good pitch and payoff, weakest speed match and short runway |

### A7 — frag 1937 · campgrounds · ROCKET
score 41.00 · flight 750 ms · 746 u · 31 points · 995 u/s · terminal pitch −0.768 · CONFIRMED
Classes: DIRECT_ROCKET, CLUTCH_1V3, DIRECT_CONFIRMED_GEO, PREDICTION_TEMPORAL, NEAR_MISS_ROCKET, DODGE_TO_KILL, HEAVY_DAMAGE_SURVIVED

| | Scene B | map | total | spd | pit | run | pay | why |
|---|---|---|---|---|---|---|---|---|
| A | 19598 | overkill | 0.979 | .981 | .842 | .604 | .785 | one of very few steep-dive launches (−0.93) able to follow A7's −0.77 arrival; short runway |
| B | 21846 | overkill | 0.979 | .981 | .954 | .917 | .445 | better pitch and runway than A, but a much weaker frag |
| C | 2553 | quarantine | 0.977 | .975 | .705 | 1.00 | .580 | full runway, mediocre pitch continuity |

A7 is the hardest Scene A in this set: a −0.77 dive needs a steeply diving Scene B
and the pool has few of them, so all three totals fall below 0.98.

### A8 — frag 24326 · quarantine · ROCKET
score 40.91 · flight 1,125 ms · 1,153 u · 46 points · 1,025 u/s · terminal pitch +0.031 · CONFIRMED
Classes: DIRECT_ROCKET, AIR_ROCKET, FLICK_SHOT, CLEAN_FLICK, DIRECT_CONFIRMED_GEO, PREDICTION_TEMPORAL, PIXEL_SHOT_GEO, TINY_GAP_SHOT

| | Scene B | map | total | spd | pit | run | pay | why |
|---|---|---|---|---|---|---|---|---|
| A | 13278 | campgrounds | 1.071 | .955 | .934 | .833 | .932 | the reciprocal of A1 — this pair is the strongest two-way bridge in the set |
| B | 28580 | trinity | 1.021 | .982 | .950 | 1.00 | .550 | best speed + runway; low payoff |
| C | 13114 | campgrounds | 1.020 | .931 | .956 | 1.00 | .610 | balanced, no standout leg |

A8 is the longest trustworthy flight in the recommended set (1,125 ms / 1,153 u at a
credible 1,025 u/s) and is level-to-slightly-rising, which makes it the most flexible
Scene A — a level arrival matches the largest share of the pool.

### A9 — frag 19598 · overkill · ROCKET
score 39.25 · flight 725 ms · 735 u · 30 points · 1,014 u/s · terminal pitch −0.922 · CONFIRMED
Classes: DIRECT_ROCKET, EXTREME_SPEED, DIRECT_CONFIRMED_GEO, NEAR_MISS_RAIL, DODGE_TO_KILL

| | Scene B | map | total | spd | pit | run | pay | why |
|---|---|---|---|---|---|---|---|---|
| A | 1937 | campgrounds | 0.992 | .981 | .845 | .625 | .820 | reciprocal of A7; the best available steep-dive-to-steep-dive pair |
| B | 26067 | quarantine | 0.962 | .999 | .996 | .562 | .604 | near-perfect motion continuity (−0.92 into −0.93) but only 675 ms of runway |
| C | 2553 | quarantine | 0.953 | .994 | .552 | 1.00 | .580 | full runway, but a −0.92 arrival into a −0.47 launch reads as a jolt |

A9 is a near-vertical dive. It is the most cinematically specific Scene A here and the
one where the pitch weight (0.20) is arguably too low relative to what a viewer sees.

### A10 — frag 34856 · asylum · ROCKET
score 38.90 · flight 725 ms · 766 u · 30 points · 1,056 u/s · terminal pitch −0.470 · CONFIRMED
Same event as A6 (frag 37977): asylum, `server_time_ms` 450650, same victim slot,
identical path geometry, two demo files (~2.7 MB and ~159 KB, different content hashes).
Shortlist is identical to A6. Note the highlight scores differ (41.15 vs 38.90) even
though the event is the same — the shorter demo gives the recogniser less context.

---

## 4. Top 10 as `pick_scene_a()` returns it, unfiltered

For completeness, the ranking the module produces with no physics filter. Every
entry marked (!) has a chord speed no rocket can have and should not be built on
without inspecting the path first.

| # | frag | map | weapon | flight ms | disp u | pts | chord u/s | best B (score) |
|---|---|---|---|---|---|---|---|---|
| 1 | 2740 | trinity | ROCKET_SPLASH | 2,925 | 680 | 118 | 233 (!) | 37168 (1.047) |
| 2 | 37168 | campgrounds | ROCKET_SPLASH | 2,575 | 468 | 104 | 182 (!) | 31455 (1.009) |
| 3 | 27911 | trinity | GRENADE | 2,200 | 481 | 90 | 219 | 12936 (1.057) |
| 4 | 10987 | campgrounds | ROCKET_SPLASH | 1,300 | 698 | 53 | 537 (!) | 28319 (1.059) |
| 5 | 12936 | campgrounds | ROCKET | 1,775 | 346 | 72 | 195 (!) | 24362 (1.082) |
| 6 | 17811 | hiddenfortress | ROCKET | 1,850 | 763 | 75 | 413 (!) | 7171 (1.039) |
| 7 | 1995 | hiddenfortress | ROCKET_SPLASH | 1,225 | 436 | 50 | 356 (!) | 11354 (1.021) |
| 8 | 7501 | asylum | GRENADE_SPLASH | 3,650 | 520 | 148 | 142 | 29419 (1.049) |
| 9 | 37720 | campgrounds | ROCKET_SPLASH | 3,150 | 513 | 127 | 163 (!) | 22936 (0.974) |
| 10 | 28319 | trinity | GRENADE | 1,225 | 636 | 51 | 519 | 10987 (1.062) |

Entry 3 (frag 27911) is the one genuinely interesting path in this table: it is a
grenade with real curvature — arc 832 u against a 481 u chord, 6 segments below
50 u/s, a bouncing arc rather than a straight line. Grenades are where the
non-straight paths live (45 of the 1,370 usable paths record bounces; 1,325 record
none). Entry 9's A and B shortlist slots are frags 22936 and 35346 — a near-duplicate
pair with byte-identical metrics, i.e. the same event offered twice.

---

## 5. What `transition_match.py` does not score

### 5.1 World heading — the deliberate omission, and what it actually costs

The module argues (docstring, lines 9–15) that world heading is invisible across a
cut because the projectile direction *is* the camera forward vector. That reasoning
is correct as far as it goes. What it misses is that the omitted quantity is not
just heading, it is everything derived from heading — and one derivative **is**
visible:

- **Turn rate / curvature is not scored.** A camera riding a rocket that is
  curving left has a non-zero apparent angular velocity. Cut to a rocket curving
  right at the same speed and pitch and the two score identically, but the viewer
  sees the world whip-pan reverse on the frame of the cut. Nothing in `score_pair`
  can distinguish them. The pool makes this mostly moot today (1,311 of 1,370
  paths are straight, `deviation_u` median 0.0) — but it becomes the dominant
  defect the moment grenades and bounced rockets enter the set, which is exactly
  the material with the most visual interest.
- **Roll is not scored at all.** Neither the path nor the metrics carry an up
  vector, so the bridge has no defined roll continuity. The renderer will have to
  invent one, and whatever it invents is unconstrained by this ranking.
- **The pitch term is the vertical component only, and it is compared raw.**
  `pitch_match = 1 - |dz|` where `dz` is a difference of sines. A 0→30° change
  costs 0.50 of pitch; a 60→90° change costs 0.13. Near-vertical dives — A9 is
  one — are scored as far more interchangeable than they look.

### 5.2 The near-duplicate demo hole

`shortlist_scene_b` excludes only `cand["demo_name"] == scene_a["demo_name"]`.
Because the corpus contains re-saved excerpts of full demos under different names
and different content hashes, **the same physical frag can be offered as a partner
for itself**. Measured: `score_pair(19639, 34346)` = **0.875** with
`speed_match = 1.000` — a perfect speed match precisely because it is the same
flight — and 34346 sits at **rank 59 of 812** in 19639's shortlist. The same holds
for 37977/34856 (rank 74). Only the `different_map` penalty keeps these out of the
top three; set `prefer_different_map=0` and they climb. In the physics-plausible
pool, **111 signature groups covering 227 of 798 rows (28%)** look like duplicate
events by (map, server_time, speed, duration).

### 5.3 Map identity is a raw string compare

`different_map = scene_a["map"] != scene_b["map"]`. `frags_rebuilt.demos.map_name`
holds **61 distinct strings for 54 distinct maps** — `asylum`/`Asylum`/`AsyLUm`,
`overkill`/`Overkill`/`OVERKILL`, `quarantine`/`Quarantine`/`qUARanTINe`,
`campgrounds`/`Campgrounds`. So two clips on the same arena can collect the +0.15
different-map bonus. Corpus-wide the effect is small (8 of 1,370 candidates carry a
case variant, 1,600 of 937,765 pairs falsely bonused, 0.17%) but it is
**concentrated**: frag 24326 is one of those 8, and it is the top-ranked Scene B for
three of the ten recommended Scene A candidates. Any of those three cutting to 24326
is a same-arena cut being sold as a cross-arena one. Fix is one `.lower()`.

### 5.4 Physical plausibility is never tested

Neither `projectile_evidence` nor `path_metrics` compares the measured speed against
the weapon's known muzzle velocity, and neither compares arc length against chord.
The consequence is §2: 400 of 1,312 rocket paths measure below 600 u/s, 77% of the
long-flight pool `pick_scene_a` prefers is implausible, and `speed_match` — the
heaviest term at 0.35 — is in those cases matching measurement artefacts rather than
apparent speed. There is a second, subtler version of the same point even on the good
paths: every real rocket travels at the same world speed, so among trustworthy
candidates `speed_match` is near 1.0 by construction and carries almost no
discriminating information. It is doing the work of an outlier detector while being
weighted as the primary criterion.

### 5.5 Other gaps found by reading the module

- **Total is not normalised.** Weights sum to 1.00 plus an additive `map_bonus` of
  0.15, so the range is [0, 1.15] and most reported totals exceed 1.0. Anything
  downstream that treats the score as a probability or a percentage is wrong.
- **`payoff` saturates at a score of 50 and only 3 of 1,370 candidates reach it.**
  In practice payoff is a linear `score/50` term weighted 0.25, and it is what
  breaks most ties — including several above where it overrides a visibly bad
  pitch match (A2/B, A4/A, A6/B).
- **Runway is measured on B's whole flight, not on the flight remaining after the
  cut.** `runway = duration_ms / 1200`. If the cut lands mid-flight — which is the
  entire point of a bridge — the usable runway is less than that, and the module has
  no cut-point parameter to subtract.
- **Scene B is never re-checked against `projectile_evidence`.** `shortlist_scene_b`
  filters on `duration_ms >= 600` only. Fed a raw `load_candidates()` pool, it can
  return the 51 paths that fail the authoritative contract.
- **No temporal or rhythmic constraint.** Nothing prevents A and B from being
  seconds apart in the same match, or from placing two bridges back to back.
- **No visual-continuity terms at all**: no lighting, palette, map-brightness, FOV,
  or HUD-state matching, and no check that A's impact and B's launch are both
  actually on screen.
- **`pick_scene_a` breaks ties by highlight score then duration only**, with no
  path-quality term — which is how the §4 table came to be led by a straight line.
- **58 usable paths contain at least one zero-length time step** (duplicate
  timestamps in the point series). Harmless to the current metrics, but any
  velocity-per-segment computation added later must guard against division by zero.

---

## 6. Recommendations before building the bridge

1. Add a physical-plausibility gate: reject rocket paths outside roughly
   800–1,300 u/s chord speed, or better, flag `arc/chord` and per-segment speed
   variance and require them to look like sampled physics.
2. Canonicalise map names with `.lower()` in `load_map_names` — one line, and it
   removes a false bonus from the current top-ranked partner.
3. Dedupe by (map, `server_time_ms`, victim slot) rather than by `demo_name`, per
   the near-duplicate-demo rule.
4. Re-run Scene B through `projectile_evidence`, not just the duration check.
5. If curved paths become the target material, add a curvature/turn-rate continuity
   term. The heading argument in the docstring is sound; its derivative is not
   covered by it.
6. Start from **A8 (frag 24326) → A1 (frag 13278)** or the reverse: the strongest
   two-way pair in the trustworthy pool, both level-flight, both >= 1,000 ms,
   both credible rocket speed, both high payoff, genuinely different arenas.
