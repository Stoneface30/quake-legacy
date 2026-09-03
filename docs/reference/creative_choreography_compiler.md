# Creative choreography compiler v1 (2026-09-03)

Modules: `creative_suite/engine/choreography.py`, `creative_corpus.py`,
`choreography_proofs.py`, `choreography_sheet.py`.

## The architectural correction

A score slot does not ask *"which frag goes here"*. It asks *"what should HAPPEN
here"*, and the answer is a set of synchronised lanes. A musical attack may be
answered by a kill, or equally by a skin flash, a wall dissolving, a damage number
ticking, an enemy appearing, a camera cut, or a single stuttered frame. The frag is
one lane out of fifteen.

Ranking songs on frag fit alone would be the old mistake in a better suit: pick the
song first, then wonder where the effects go. So the shortlist stays shut until the
composer can score whether the archive can perform a song's **whole visual
performance** (`choreography.assess_readiness`).

## ChoreographyPlan

Fifteen lanes: GAMEPLAY, NARRATIVE, CAMERA, TIME, TRANSITION, FX, MODEL_SKIN,
MATERIAL_TEXTURE, WORLD, ANIMATION, INFORMATION, PIP, TEXT_CHAT, SOUND_DESIGN,
MUSIC_GESTURE_RESPONSE.

Every element carries `start_us`, `peak_us`, `end_us` in edit time, the `trigger`
that fires it, its `musical_relation`, and a `purpose` from a closed list.
`EFFECT_FOR_EFFECTS_SAKE` is refused by the constructor. A plan is refused when an
element runs outside its slot, when a peak sits outside its element, or when a
truth-bearing lane (GAMEPLAY, INFORMATION, NARRATIVE) carries no evidence.

**Result truth is a gate, not a weight.** `round_result_required="WIN"` against
`round_result_evidence="LOSS"` or `UNKNOWN` raises. A victory treatment over a round
that was not won is a lie the viewer can check against the scoreboard.

`plan_hash` is deterministic over the serialised plan. Nothing in the module can
write: a plan holds references, never a connection.

## Capability and cost

`PROVEN_RUNTIME` (13) · `PROTOTYPE` (13) · `DESIGNABLE` (29) ·
`REQUIRES_NEW_TECH` (2) · `CREATIVE_SEED` (3). Cost: CHEAP 15, MODERATE 25,
EXPENSIVE 15, R&D 5.

A plan's `weakest_capability` governs what it can actually deliver, and
`fillability()` reports **gameplay fillability** and **choreography fillability**
separately, so a song is never ranked highly because the moments exist while the
effects it wants do not.

## Creative corpus — 60 entries, all 15 lanes

Every idea from both lists is registered with its lane, purpose, evidence
requirement, capability and cost. Nothing was dropped.

**From the original dump:** world strip / rebuild / morph, fly-into-object,
projectile morph bridge, map construction intro, low-HP reactive world, wall
x-ray + rebuild, 1vX reveal and decrementing count, texture countdown text,
grenade football gag, truth-gated victory payoff and loss continuation, team
round story, identity match cut, PIP on world surfaces, chat reactions, rhythmic
motif montage, movement transitions (doors, teleports, rocket jumps, speed),
telefrag and gauntlet grammar, multi-exposure / frame echo / temporal
decomposition, music-reactive materials, death as transition.

**From the later list:** team identity morph, post-win teammate model reveal,
rhythmic image stutter, mosaic tile interpolation, micro action accents, rail
cooldown telegraph, damage ledger over target, round damage counter, semantic
compression, danger cross sign, strafe-jump audio match, hero-then-death-rewind,
death motif bank, rocket flyby audio anchor, diegetic scoreboard, assisted round
finish, NOPE retreat and commit-1vX, speed-scaled slow motion, damage chase
assist, lag/teleport stylisation, shaft duel, enemy POV in three provenances.

**Episode 1 framing:** PROJECT_INTRO, CA_EXPLAINER, QUAKE_TRIBUTE_OUTRO.

## The ten proofs

`choreography_proofs.py` builds ten planning-only choreographies: team identity
morph, rhythmic image stutter, damage ledger, hero-then-death-rewind, rocket flyby
transition, wall x-ray rebuild, 1vX enemy reveal, diegetic scoreboard, movement
audio match, enemy POV preshot. Two are gated on a real round win.

The 1vX proof is the canonical shape: a three-attack figure answered by three
enemy reveals in FX, a count decrementing in INFORMATION on real deaths, the map
stripped during the build and rebuilt on the drop, slow motion into the release,
and the payoff refused unless the round was won.

Sheets: `docs/visual-record/2026-09-03/choreography_sheet_whole.png` (seven bands)
and `choreography_sheet_zoom_1vx.png` (every lane separate, peaks marked).

## SHAFT_DUEL — design requirements, not an implementation

**Feasibility from cached data: NO.** `recognition_lg_engagements` has 13,696 rows
whose `my_fire` / `victim_pain` / `my_pain` series are **all empty**, and
`lg_extracted` stores a status string rather than events. The raw material exists
(12.9M LG `fire_weapon` events, 1.15M `pain` events carrying the victim and their
health after damage) but **`EV_PAIN` does not name the attacker**, so per-attacker
LG damage is a derived quantity, not a recorded one. Registered as `CREATIVE_SEED`.

Requirements when it is built:
- essentially 1v1 LG engagement; both players actively shafting each other
- exclude jump-pad and airborne farming; exclude obvious third-party damage
- meaningful mutual overlap duration and enough contacts to be statistically useful
- derive `MY_LG_DAMAGE`, `ENEMY_LG_DAMAGE`, contact rates, damage advantage, ratio
- classes: DOMINANT_OUTSHAFT / OUTSHAFT / EVEN_SHAFT / OUTSHAFTED / HEAVILY_OUTSHAFTED
- stylistic and occasional; PANTHEON is not an analytics overlay

## Enemy POV provenance

`ENEMY_POV_REAL` requires `MULTI_DEMO_RECOVERED` (another client's actual recording
of the same historical occurrence). `ENEMY_POV_RECONSTRUCTED` is built from recorded
enemy state and labelled DERIVED. `ENEMY_POV_SYNTHETIC` is authored. The three are
never interchangeable.

---

# Temporal choreography solver v1 (2026-09-03)

Modules: `creative_suite/engine/temporal_operators.py`, `temporal_solver.py`,
`temporal_proofs.py`; sheet in `choreography_sheet.render_temporal_sheet`.

## The correction

Choreography elements are not intervals placed on an existing timeline. They ARE
edit time. A freeze does not annotate 300 ms, it *spends* 300 ms of the song. A
replay inserts its own duration. A stutter's dwell and count decide how long the
shot lasts. A transition overlap **removes** net time. Those are the variables
that let an immutable song be fitted exactly.

```
final = Σ retimed source spans
      + freezes + replay insertions + repeats + synthetic inserts + holds
      − trims − transition overlaps
subject to  final == score slot duration   (exactly, on a 1 ms quantum)
```

**Sync is a property of the finished choreography.** Not the raw frag, not the
scene before effects. Anything inserted ahead of the hero moves the hero, so
`ComposedTimeMap` refuses to be built from a plan that does not occupy its slot
exactly — the regression is guarded by a test.

## TemporalOperator

Ten kinds: TRIM, RETIME, FREEZE, INSERT, REPLAY, REPEAT, STUTTER, OVERLAP,
REPLACE, SYNTHETIC_INSERT. Sign is a property of the kind: TRIM and OVERLAP
subtract, REPLACE is concurrent and costs nothing (that is the difference between
a picture-in-picture enemy POV and a sequential one), the rest add.

Each declares hard limits and a visually preferred band, plus rate bounds and a
preferred rate for retimes, repeat counts and dwell for stutters. `soft_cost`
combines distance from the preferred duration and distance from the preferred
rate, and **the search and the final ranking use the same cost** — ranking states
by one metric and choosing by another silently discards the better answer.

## Sync bias is per effect

`BIAS_US`: HERO −15 ms (the director's measured preference), everything else 0.
A held stutter frame reads on its attack; applying the hero bias globally would
drag every frame off its own beat.

## Temporal elasticity

`elasticity()` returns the range of final durations a candidate can honestly
produce. **That**, not raw source duration, is what a score-slot search should
ask about. The double air rocket carries 2.9 s of source and an envelope of
3.695–7.350 s.

## The five proofs

| proof | slot | raw source | added | removed | anchors |
|---|---|---|---|---|---|
| DOUBLE_AIR_ROCKET | 5850 ms | 3275 ms | retime 1992, freeze 275, replay 3691, morph 392 | overlap 500 | hero −29.6 ms hit |
| RHYTHMIC_IMAGE_STUTTER | 2600 ms | 1800 ms | retime 1880, stutter 720 | — | duration derived from the figure |
| FREEZE_GO_FRAG | 4000 ms | 3100 ms | retime 3517, freeze 483 | — | release +3.0 ms, hero +1.3 ms |
| HERO_THEN_DEATH_REWIND | 7200 ms | 3140 ms | retime 2400, freeze 367, flashes 587, rewind 1100, replay 2746 | — | hero +0.8 ms |
| TRANSITION_OVERLAP | 3850 ms | 4000 ms | retime 4000 | overlap 150 | both scenes at rate exactly 1 |

The stutter's 720 ms is **derived** from four attacks 180 ms apart — the music
sets the effect's length. The overlap proof saves 150 ms with neither scene
accelerated, which is the whole point of that degree of freedom.

## Honest infeasibility

Duration feasibility and anchor feasibility are separate. When every composition
occupies the slot but none lands a required anchor, the report says so
(`anchors_reachable=False`) and names the closest miss, rather than stretching an
effect past its limits to reach it. Both were observed while building these
proofs and the anchors were moved to where the composition can actually land.

## Sheet

`docs/visual-record/2026-09-03/temporal_double_air_rocket.png` and
`temporal_transition_overlap.png`: fixed music on top, the composition on that
ruler, and an explicit time-added / time-removed accounting underneath.

---

# Effect template library v1 (2026-09-03)

Module: `creative_suite/engine/effect_templates.py`. Atlas:
`docs/visual-record/2026-09-03/effect_temporal_atlas.png`. Raw canary numbers:
`docs/reference/effect_canary_measurements.json`.

## Why

The solver knew a freeze adds its duration. It did not know that a 120 ms freeze
reads as a dropped frame. Those are different kinds of knowledge, and until an
envelope has been looked at, the solver is working from an estimate and must say so.

**The ladder:** `DESIGN_ESTIMATE` → `SYNTHETIC_TEST` → `RUNTIME_MEASURED` →
`HUMAN_APPROVED`. `solver_trusted` starts at SYNTHETIC_TEST. Nothing in the library
is HUMAN_APPROVED yet, and a test asserts that.

**50 templates across all 15 families cover all 60 creative ideas** (55 directly,
5 by explicit exemption with a stated reason). 8 are swept, 42 are estimates —
`measured_share` 0.16, reported rather than hidden.

## What the canaries measured (60 fps, generated footage)

| primitive | finding |
|---|---|
| **Freeze** | Delivery is exact to the frame but **always one frame long** (+16.6 ms at every point from 50 to 900 ms). The request is now compensated via `request_for()`. |
| **Stutter** | **Unequal figures survive.** 110/230/170 ms delivered within 6.7 ms; 60/90/45/120 within 1.7 ms. Nothing is forced onto an even grid. A 33 ms hold (two frames) is the floor. |
| **Rate** | 3/10, 2/5 and 1/1 land **exactly**. 1/4, 1/2, 55/100 and 7/10 lose one frame and deliver a slightly faster effective rate (0.5 → 0.5042). |
| **Overlap** | Removes **exactly** the time requested: 0.0 ms error at all of 50–500 ms. |

Aesthetic bounds remain the director's. Review clips are in
`docs/visual-record/2026-09-03/review_{freeze,stutter,rate,overlap}_sweep.mp4`,
each labelled with its duration.

## Temporal power

MICRO ≤300 ms · SMALL ≤1 s · MEDIUM ≤3 s · LARGE ≤8 s · SEQUENCE ≤60 s. The
constructor refuses a template whose envelope exceeds its class, which caught two
misclassifications on first run. This is what stops a four-second death montage
being reached for to solve a 120 ms deficit.

## Three feasibility questions, kept apart

`MATHEMATICALLY_FEASIBLE` (the arithmetic closes) · `VISUALLY_FEASIBLE` (inside a
swept envelope) · `HUMAN_APPROVED` (somebody looked). An untested MODEL_MORPH at
400 ms reports only the first.

## Template-driven solve

`slot_verdict(5850 ms, spec)` → **PREFERRED_FEASIBLE**, hard 1280–15100 ms,
preferred 2950–8300 ms, and *"2 of 5 envelopes are reasoning, not measurement"*.
`solve_from_templates` then finds 263 exact compositions with the hero at +1.0 ms,
every duration drawn from the library rather than hand-picked.

## Combination rules

`good_with` / `bad_with` / `must_precede` / `must_follow` / `can_overlap`.
WORLD_STRIP with MOSAIC_TILE_STEP is flagged as competing for attention;
WORLD_REBUILD before WORLD_STRIP is flagged as out of order.

## Second canary batch (2026-09-03)

Raw numbers: `docs/reference/effect_canary_measurements_2.json`.

| primitive | finding |
|---|---|
| **PIP vs cut** | The same creative idea, two temporal behaviours, measured at 600–2400 ms. An overlay adds **exactly 0.0 ms** of sequence time at every point; cutting to the same material adds **exactly its own duration**. |
| **Rewind** | A rewind runs the slice backwards and then forwards again, so it costs **exactly twice the slice** — 150/300/450/600/900/1200 ms slices delivered 300/600/900/1200/1800/2400 ms, 0.0 ms error throughout. The template envelope is the *delivered cost*, not the slice length. |

Measured coverage is now **12 of 50 templates (24%)** across four temporal scales.
