# Dodge / near-miss: extraction reconciliation + quality tier

**Date:** 2026-09-01
**Scope:** `engine/parser/extract_dodge_events.py`, `engine/parser/reclassify_v2.py`,
`creative_suite/api/frags.py`
**Databases:** `frags_rebuilt.db` read-only throughout. Writes confined to
`frag_recognition.db` — the `dodge_extracted` / `recognition_dodge_events` tables
owned by the extractor, plus new attribute keys and class labels on
`recognized_frags`. No existing column semantics were changed.

> Demo filenames are replaced by `demo:<8 hex>` (SHA-256 prefix) throughout —
> the corpus filenames embed player nicknames and this repo is public.

---

## Task A — the 2 extraction failures

### What the run recorded

The full-corpus run logged its per-demo outcome in `dodge_extracted(status)`.
Both failures were the same exception class:

| demo | anchors | status | recorded |
|---|---|---|---|
| `demo:08edd2a9` | 11 | `fail: TypeError` | 2026-08-31 22:52 |
| `demo:f0140052` | 8 | `fail: TypeError` | 2026-08-31 23:39 |

### Classification: **extractor code defect** — not corrupt sources, not transient

Both reproduce deterministically on a direct re-parse via `demo_parse.DM73Parser`,
which itself succeeds — the demos parse fine, so the source files are healthy.
The traceback is identical for both:

```
File "engine/parser/extract_dodge_events.py", line 175, in straight_line_samples
    origin[1] + direction[1] * d,
TypeError: unsupported operand type(s) for +: 'NoneType' and 'float'
```

**Root cause.** The shooter entity-track filter in `analyze_dodges` validated only
one of the three origin components:

```python
if (cn is None or cn == recorder_client or en.get("origin_x") is None
        or en.get("angle_yaw") is None or en.get("angle_pitch") is None):
    continue
```

Delta-compressed entity rows can carry a **partially decoded** origin — `origin_x`
and `origin_y` present, `origin_z` still `None`. Measured on one failing demo: 5
such rows out of 49,703 (`(x,y,z)` None-patterns `(F,F,T)`×2, `(F,T,F)`×2,
`(T,F,F)`×1). When one of those five happened to be the nearest angle sample
within `ANGLE_TOL_MS` for a rocket or grenade fire event, its `None` coordinate
propagated into `straight_line_samples()` and raised, and because failures are
isolated per-demo the **entire demo** was abandoned — not just that candidate.

Why exactly 2 in 3,997: it requires the coincidence of a partial entity row being
the *nearest* sample to a *rocket/grenade* fire event inside a *kill-anchor
window*. The rail branch never crashed, because both `segment_perp` and
`extract_projectile_paths.ray_point_perp` are already `None`-safe (they return
`inf`, and the candidate is silently dropped).

### Fix

Two changes in `extract_dodge_events.py`:

1. **Root cause** — the entity filter now requires all three origin components.
2. **Belt-and-braces** — `shooter_origin_dir` nulls out any origin that still
   contains a `None`, so a future edit reintroducing one would skip the candidate
   rather than crash the demo.

The fix is **behaviour-preserving for already-processed demos**: a `None`-bearing
origin previously produced `inf` on the rail paths (candidate skipped) and a crash
on the projectile paths. It now produces a skip on all four paths. The only
residual difference is that partial entity rows no longer occupy the
"nearest angle sample" slot, which can promote a neighbouring fully-decoded
sample — strictly more correct, and confined to the handful of demos that carry
such rows.

### Targeted retry

No full rescan. The extractor's resume logic (`dodge_extracted.status='ok'`)
already made a plain rerun self-targeting — the `todo` list computed to exactly
the two failing demos, verified before running:

```
{"eligible_kill_anchors": 58, "demos_to_open": 2, "events_updated": 19,
 "near_misses_written": 21, "failed": 0, "wall_s": 31.4}
```

### Final state

| metric | value |
|---|---|
| Demos processed `status='ok'` | **3,997 / 3,997** |
| Failures | **0** |
| Permanently unavailable | **0** — nothing needed marking; both were recoverable |
| `recognition_dodge_events` rows | **36,586** (was 36,565 — **+21**, no regression) |
| `recognized_frags` carrying `dodge_scanned` | 36,568 / 36,607 |

**The honest denominator.** 3,997 is the count of demos actually opened, not the
number of demos in the corpus. Two separate exclusions are legitimate and should
not be read as failures:

- **39 kill anchors across 38 demos will never receive `dodge_scanned`.** The
  bookkeeping key is `duplicate_of or content_hash`, so a demo whose canonical
  twin was already processed is correctly skipped — but the *anchor rows filed
  under its own demo_name* never get written back. These re-appear as
  "candidates" on every future run and are then excluded from `todo`, so they
  cost nothing, but they are also never scanned. This is a duplicate-suppression
  artifact, not a failure.
- **Demos with a NULL `recorder_client`** are skipped by design (documented in
  the extractor: the recorder's own shots cannot be told from enemy shots).

Also note: **a demo with zero near-misses is a success, not a failure.** 3,997
demos were opened and 3,573 produced at least one event; the other ~424 simply
had no qualifying incoming threat inside any kill-anchor window.

---

## Task B — DODGE_HERO / RAIL_DODGE_HERO / PROJECTILE_DODGE_HERO

### The problem being solved

The broad labels are **discovery evidence**: "a threat weapon passed inside its
near-miss threshold and I lived". At corpus scale `DODGE_TO_KILL` fires on 13,887
of 36,607 recognized frags (~38%). In Clan Arena a player is nearly always moving
and nearly always being shot at, so *proximity + motion* is the base rate, not a
highlight. The tier below separates rare hero-quality evidence from that base rate.

### Design

Scored per **event row** in `recognition_dodge_events`, not from the anchor's
flattened summary — the summary keeps only the closest near-miss and discards the
geometry method and timing, which are exactly what decide whether the proximity
meant anything. Style follows the module's existing labels (percentile-based
thresholds, documented reasoning inline, idempotent through the `_reclass_delta`
bookkeeping and `_REASON_RE` strip).

```
score = ( 0.40 · proximity_pctile          # within its OWN threat_type pool
        + 0.40 · evasion_pctile            # recorder_velocity_change, corpus-wide
        + 0.20 · immediacy )               # how tightly the dodge leads to the kill
        × geometric_confidence(method)
```

Percentile-normalised for the same reason the speed and flick labels are:
absolute unit thresholds do not transfer across weapons (a 120u rail near-miss and
a 120u rocket near-miss are not the same event), while "closer than 90% of this
weapon's near-misses" does.

**`evasion_pctile` is the component that answers the actual question.**
`recorder_velocity_change` is the vector-difference magnitude of the recorder's own
horizontal velocity sampled ±450 ms around the shot. A player travelling in an
unrelated straight line when a shot happens near them has a *low* delta; a player
who genuinely broke trajectory has a high one. That is precisely the
"already moving in an unrelated direction" false positive the brief asks to
suppress.

#### Geometric confidence — measured vs reconstructed

Not a tuning knob. It encodes how much of each path is real, per the extractor's
own docstring:

| method | conf | why |
|---|---|---|
| `segment` | **1.00** | Real rail beam: observed `fire_weapon` origin → observed `railtrail` endpoint. `closest_approach_units` is then the **true orthogonal displacement of the recorder from the actual beam**. Nothing simulated. |
| `sim_straight` | 0.80 | Rocket: launch point and time observed directly, and a rocket does fly straight at constant speed — but no BSP, so the sim can pass through a wall that would have stopped the real rocket. |
| `ray_angle` | 0.70 | Rail fallback: no `railtrail` matched, beam direction reconstructed from shooter view angles ±200 ms. Direction inferred, not observed. |
| `sim_ballistic` | 0.60 | Grenade: gravity-only, bounces **not** simulated, provisional fuse constant. Weakest of the four. |

This is what makes the rail score the higher-confidence one the brief asks for: for
`segment` rows the orthogonal displacement from the beam is a measurement, and the
rail hero tier additionally **refuses `ray_angle` rows outright** (only 23 corpus-wide).

#### Gates — a conjunction, on purpose

An event must clear all of these to be hero-eligible. The failure mode being
removed is one component carrying a row alone (very close but stone-still; wild
strafing but the shot was 150u away):

| gate | value | reasoning |
|---|---|---|
| `survived` | `= 1` | always true in extractor v1; kept explicit |
| proximity pctile | ≥ 50 | closer than the median for its own weapon |
| evasion pctile | ≥ 60 | demonstrably broke trajectory |
| projectile flight | ≥ 100 ms | a projectile whose closest approach is at the muzzle was point-blank — there was no flight time for a dodge to exist in. **Rail is exempt**: it is hitscan (flight always 0) and is dodged *pre-emptively*, which the evasion component already measures. |

Gate pass rate: **6,443 of 36,586 events (17.6%)**.

#### Cuts — ranked per weapon pool, not globally

| label | rule | cut |
|---|---|---|
| `RAIL_DODGE_HERO` | gated, `RAIL`, `segment`, top decile of the gated rail pool | q ≥ **83.8** (pool 1,906) |
| `PROJECTILE_DODGE_HERO` | gated, `ROCKET`/`GRENADE`, top decile of the gated projectile pool | q ≥ **65.8** (pool 4,535) |
| `DODGE_HERO` | top 2% of its own weapon pool | rail q ≥ **91.2** / projectile q ≥ **71.4** |

**Why per-pool and not one global cut.** A single global cut was tried first and
rejected on the measurement: at p99-of-everything (q ≥ 80.1) `DODGE_HERO` selected
191 rows — *exactly and only* the `RAIL_DODGE_HERO` rows, because the confidence
factor deliberately depresses projectile scores. That would have been a renaming,
not a tier. Ranking each weapon against itself makes `DODGE_HERO` genuinely
cross-weapon.

**Label contract** (mirrors the existing `EXTREME_FLICK ⊂ CLEAN_FLICK` contract):
`DODGE_HERO` is a strict subset of `RAIL_DODGE_HERO ∪ PROJECTILE_DODGE_HERO` and
is never applied without the weapon label that qualified it. Verified corpus-wide:
**0 violations.**

Score weights: `RAIL_DODGE_HERO` +9 movement, `PROJECTILE_DODGE_HERO` +6
(confidence `HIGH`, not `CONFIRMED` — the path was simulated, so the proximity is
a physics estimate, not a measurement), `DODGE_HERO` +5 movement / +3 drama on top.

### Resulting counts

| label | rows | % of 36,607 frags |
|---|---|---|
| `NEAR_MISS_ROCKET` (broad) | 10,996 | 30.0% |
| `NEAR_MISS_RAIL` (broad) | 8,344 | 22.8% |
| `NEAR_MISS_GRENADE` (broad) | 537 | 1.5% |
| `DODGE_STRAFE` (broad) | 1,993 | 5.4% |
| `DODGE_TO_KILL` (broad) | 13,887 | 37.9% |
| **`PROJECTILE_DODGE_HERO`** | **444** | **1.21%** |
| **`RAIL_DODGE_HERO`** | **192** | **0.52%** |
| **`DODGE_HERO`** | **134** | **0.37%** |

Hero tier union: **634 rows, 4.6% of the 13,887 broad `DODGE_TO_KILL` population**
— a genuine rare subset, not a relabelling. `DODGE_HERO`'s 134 rows split 95
rocket / 40 rail (one row carries both), so the elite tier is cross-weapon as
intended.

The broad labels did **not** regress — they moved only by the +21 recovered events
(`NEAR_MISS_RAIL` 8,339→8,344, `NEAR_MISS_ROCKET` 10,991→10,996,
`DODGE_STRAFE` 1,992→1,993, `DODGE_TO_KILL` 13,878→13,887).

### Performance

Full pass: **6.4 s** — single-digit seconds, DB-only contract intact. The new work
is one `SELECT` over 36,586 rows plus two sorts; no demo IO was added.

### `/frags` wiring

The three labels were appended to `_FILTER_GROUPS["movement"]` in
`creative_suite/api/frags.py`, alongside the existing `NEAR_MISS_*` /
`DODGE_STRAFE` / `DODGE_TO_KILL` entries. Purely additive — counts are computed
live from the class cache. Verified through `list_filter_groups()`.

### Evidence persisted per anchor

`dodge_quality_score`, `dodge_quality_threat`, `dodge_quality_method`,
`dodge_proximity_pctile`, `dodge_evasion_pctile`, `dodge_immediacy`,
`dodge_geom_confidence` — so a hero label can always be audited back to the
numbers that produced it.

---

## Task C — manual validation sample (data-level)

### Rubric

Fixed before inspecting any row, and stated in **raw units** so it is not a
restatement of the percentile score:

- **REAL** — approach ≤ 60u (rail) / ≤ 90u (splash) **and** velocity change ≥ 400 ups
  **and** near-miss precedes the kill **and** (rail, or projectile flight ≥ 150 ms)
- **WEAK** — approach ≤ 95u / ≤ 135u **and** velocity change ≥ 200, precedes the kill
- **COINCIDENT** — everything else; chiefly velocity change < 200 (the player was
  not meaningfully changing trajectory), or the near-miss landed *after* the kill

### Results

| sample | REAL | WEAK | COINCIDENT |
|---|---|---|---|
| **Tier A** — top 20 by `DODGE_HERO` quality score | **20/20** | 0 | **0** |
| **Tier B** — median 20 of broad `DODGE_TO_KILL` (hero excluded) | 3/20 | 10 | 7 |
| **Tier C** — random 20 of broad `DODGE_TO_KILL` (hero excluded) | 6/20 | 11 | 3 |

Whole-population agreement (all 19,877 scored anchors, not a sample):

| tier | n | REAL | WEAK | COINCIDENT |
|---|---|---|---|---|
| hero (`RAIL_`/`PROJECTILE_DODGE_HERO`) | 634 | **88.8%** | 11.2% | **0.0%** |
| broad `DODGE_TO_KILL`, hero excluded | 13,277 | 25.3% | 50.2% | 24.5% |
| other dodge anchors | 5,966 | 17.8% | 33.1% | 49.1% |

### Reading

**The threshold is separating signal from noise.** 20/20 REAL in the top tier
against 6/20 in a random draw from the broad population, and — the stronger
result, because it covers everything rather than a sample — **zero** of the 634
hero rows fall into COINCIDENT, against 24.5% of the broad population. Tier A's
rows are tight: 4–17u off a *measured* rail beam with 640–870 ups of trajectory
change, landing 25–300 ms before the kill.

Representative Tier A rows (all `RAIL`/`segment`):

| demo | anchor ms | dist u | vel Δ | gap ms | q |
|---|---|---|---|---|---|
| `demo:242fd8d8` | 317925 | 7.3 | 711 | 75 | 96.2 |
| `demo:62cc35bc` | 407050 | 10.6 | 768 | 50 | 96.2 |
| `demo:f943a000` | 1079550 | 9.1 | 874 | 300 | 95.0 |
| `demo:103363e0` | 583400 | 6.1 | 654 | 75 | 94.6 |

Contrast with COINCIDENT rows the tier correctly rejects — e.g. `demo:0cd4b2d6`
at 4.5u (closer than any Tier A row) but only 110 ups of velocity change: a rail
that passed very close while the recorder did essentially nothing. Proximity
alone buys nothing, which is the design intent.

**No threshold adjustment is recommended.** Both cuts are doing real work and
neither is obviously mistuned.

### Caveats — what this pass does *not* establish

1. **No video ground truth.** No wolfcam capture was made, so the rubric
   necessarily reads the same columns the score reads. It differs from the score
   *in kind* — absolute unit thresholds instead of corpus percentiles, hard
   conjunctions instead of a weighted blend, no confidence or immediacy term —
   so it is a meaningful cross-check, but it cannot catch a row that looks right
   in the numbers and wrong on screen. A 10–20 clip wolfcam pass over Tier A
   remains the real acceptance gate.
2. **Correlation is not causation.** `recorder_velocity_change` proves the
   recorder changed trajectory around the shot, **not that the change was caused
   by it**. A player who happened to turn a corner at that instant scores the
   same as one who reacted. Resolving intent needs a view-angle / threat-bearing
   correlation this DB does not carry. The gates suppress the bulk of these; they
   do not eliminate them. This is the single largest known weakness of the tier.
3. **Sorting `DODGE_HERO` by raw `q` returns rail first.** The top 20 are all
   rail, because `geom_confidence` is 1.00 there by design. The label set overall
   is 95 rocket / 40 rail. A highlight picker wanting weapon variety should rank
   within weapon pool, not by raw score.
4. **Near-duplicate demos survive into the tier.** Within the hero tier's event
   rows, 87 `(anchor_ms, threat, distance, velocity)` signatures appear more than
   once — the same real moment saved under two demo filenames that content-hash
   dedup treats as distinct (canonical-hash dedup reports 0 duplicates among the
   634). Consistent with the known near-duplicate-demo rule: dedupe moments by
   map + server_time + kill signature, never by hash alone.

---

## Pre-existing issue found (not fixed — flagging for a decision)

`reclassify_v2.run()` needed **two** passes to reach a fixed point after the new
labels were introduced. Run *n* and run *n+1* differed; runs *n+1*, *n+2*, *n+3*
are byte-identical (verified by hashing `classes / attributes / reasons /
highlight_score / movement_score / drama_score` over all 36,607 rows).

**Cause — a pre-existing feedback loop in the rarity term, not in the new code.**
`label_freq` is counted from the `classes` column *as stored*, i.e. **before** the
idempotency strip, so it includes labels the previous run added. Introducing any
new label therefore changes `label_freq` on the following run, changing `rarity`,
changing scores — once. With the corpus at 36,607 rows the ultra-rare cutoff is
73.2 and the semi-rare cutoff is 366.1, so `RAIL_DODGE_HERO` (192) and
`DODGE_HERO` (134) newly count as semi-rare on the second pass, while
`PROJECTILE_DODGE_HERO` (444) does not.

The existing `test_reclassify_v2_dodge.py` cannot catch this: its synthetic DB has
10 rows, so the rarity cutoffs are 0.02 and 0.1 and no label ever qualifies.

The new labels' own contribution **is** idempotent — the `_reclass_delta` strip and
the extended `_REASON_RE` cover them. The transient is entirely the rarity term
absorbing a changed label set. The clean fix is to count `label_freq` from the
*stripped* (base v1) class sets, but that would shift rarity scores corpus-wide
for every existing label, so it is left for a deliberate decision rather than
changed silently here.

---

## Tests

New file `engine/parser/tests/test_dodge_quality_score.py` — 15 tests over the
pure scorer and a throwaway-DB integration (real project databases never opened):

- evasion separates a real dodge from coincidental proximity at identical distance
- a wide miss is gated out even with violent movement (conjunction, not either/or)
- point-blank projectiles gated out; rail correctly exempt from the flight gate
- a dead recorder is never a dodge
- measured rail beam > simulated rocket > gravity-only grenade, for identical inputs
- reconstructed `ray_angle` ranks below a measured beam
- an unknown future `method` scores conservatively
- score components are reported, not hidden
- immediacy rewards a dodge leading into the kill; a post-kill near-miss scores 0
- a missing velocity sample cannot earn a hero label (absent evidence ≠ evidence)
- hero tier is rare and obeys the `DODGE_HERO ⊆ weapon-hero` subset contract
- deliberately coincidental proximity never reaches the hero tier
- hero labels idempotent across two runs
- quality evidence persisted on the anchor row
- a missing `recognition_dodge_events` table degrades to no hero labels

### Results

```
engine/parser/tests/                     26 passed in 0.96s
  test_extract_dodge_events.py + test_reclassify_v2_dodge.py    11 passed
  test_dodge_quality_score.py (new)                             15 passed

creative_suite/tests/ -k "frag or filter"    152 passed, 3 skipped in 22.3s
```

All green. Nothing committed — changes left in the working tree for review.

### Files changed

| file | change |
|---|---|
| `engine/parser/extract_dodge_events.py` | partial-origin entity filter fix + defensive guard |
| `engine/parser/reclassify_v2.py` | DODGE QUALITY SCORE block, `score_dodge_event`, `load_dodge_quality`, 3 labels, `_REASON_RE` + stats |
| `creative_suite/api/frags.py` | 3 labels appended to `_FILTER_GROUPS["movement"]` |
| `engine/parser/tests/test_dodge_quality_score.py` | new, 15 tests |
