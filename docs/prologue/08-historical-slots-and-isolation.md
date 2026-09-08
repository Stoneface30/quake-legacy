# HISTORICAL SLOTS & RESOURCE ISOLATION

Human review is the priority workstream. This file is the contract that keeps
the prologue from interfering with it.

---

## 1. NOTHING HISTORICAL IS CONSUMED

Not one frag has been assigned to the prologue. Every place footage would go is
a **named slot** carrying a requirement and a live count of what qualifies.

Run `python -m creative_suite.prologue.slots` for current pools.

| Slot | Part | Requirement | Pool today |
|---|---|---|---|
| `SLOT_ACCEL` | P1 | unbroken strafe run, 1.0–2.5 s, peak ≥ 700 ups, readable trajectory | **469** |
| `SLOT_ACCEL_FRAG` | P1 | as above, ending in a frag | **166** |
| `SLOT_ROCKET_JUMP` | P1 | health visibly traded for height/speed, ≤ 1.0 s | *not yet derivable* |
| `SLOT_RAIL_FLICK` | P1 | railgun, clean single impact, ≤ 0.6 s | 61,106 |
| `SLOT_AIR_ROCKET` | P1 | direct rocket on an airborne victim | *airshot derivation pending* |
| `SLOT_TELEFRAG` | P1 | telefrag, ≤ 0.4 s | **1,443** |
| `SLOT_LG_TRACK` | P1 | sustained lightning contact ≥ 0.6 s | 77,688 |
| `SLOT_JUMPPAD` | P1 | clean vertical routing | **40,342** |
| `SLOT_TELEPORT` | P1 | confirmed transit, in and out | **53,503** |
| `SLOT_RHYTHM` | P1 | 6 × short readable actions for the density ramp | 155,647 |
| `SLOT_CLANWAR` | P3 | full round story, team context, round won | **7,013** |
| `SLOT_PROMISE` | P3 | 5 × 1.5 s technique demonstrations | *authored, not selected* |

**Every pool is deep.** Nothing about the prologue is blocked on review
finishing — it is blocked only on review *starting to express preferences*,
which is a much lower bar.

### Two slots are not yet countable

`SLOT_ROCKET_JUMP` and `SLOT_AIR_ROCKET` have no derivation behind them today.
An airshot needs victim-airborne state at impact; a rocket jump needs
self-damage correlated with a velocity change. Both are real derivations that
do not exist yet. They are marked `n/a` rather than given a guessed pool,
because a fabricated count is worse than an admitted gap.

**Neither blocks the treatments.** Both beats can be filled from the synthetic
explainer if review does not surface a candidate.

---

## 2. HOW A SLOT GETS FILLED

```
human review assigns a role  ->  optionally writes an annotation
                             ->  slots.intro_candidates() surfaces it
                             ->  the user chooses
                             ->  only then is it in the prologue
```

**The code never chooses.** `intro_candidates()` returns a list; it does not
rank, score, or auto-assign. Ranking would be a recommendation, and the point of
the slot system is that this workstream does not make that call.

### What the code listens for

An annotation matching `intro · opening · opener · first shot · good first ·
explain quake · ca explanation · prologue · title` on a moment whose role is
**T1_FEATURE_FX, T2_TRANSITION or T3_RHYTHM_MONTAGE**.

**T4_KEEP_NORMAL and T5_PASS_FILLER are never eligible.** PASS means "not
primary gameplay material", and the opening of the film is the most primary
place there is.

**Human annotation beats machine score, always.** A moment the user tagged
"good first shot" outranks anything a scorer liked. There is no tiebreak in
which the machine wins.

### Current state
**0 candidates.** No human-provenance annotation mentions the opening yet, which
is the expected state this early. The four rows currently in `human_reviews` all
carry `provenance = TEST` and are correctly excluded — an automated run must
never be able to cast the film.

### A near-miss worth recording
The first version of this lookup guessed the table name `review_verdicts`. The
real table is `human_reviews`. It returned `[]` — indistinguishable from "the
user has annotated nothing yet" — and would have made the prologue permanently
deaf to human review while looking healthy. It now raises `ReviewSchemaChanged`
instead, and a test asserts the table exists.

---

## 3. RESOURCE ISOLATION

### Capture priority — unchanged
```
1. interactive user review        <- absolute priority
2. review proxy generation
3. user-requested full round
4. intro proof                    <- THIS WORKSTREAM
5. background experiments
```

**Nothing in this deliverable used a capture resource.** No WolfcamQL launch, no
ffmpeg render, no proxy generation. The entire proof is SQL reads and generated
SVG. That is deliberate: the prologue can be designed in full while review has
uncontested use of the machine.

The first capture this workstream will need is the **synthetic CA round** for
Part 2 — one local recording, at priority 4, and it should be scheduled when the
user is not reviewing.

### Git isolation
Branch `feature/pantheon-prologue` in worktree
`.claude/worktrees/pantheon-prologue`, cut from `demo-v2-mining@f665207e`.

The review session's working tree is untouched. Verify with `git worktree list`.

### Cache isolation
The caches are 10 GB and live once, in the main checkout. This workstream reads
them **across the worktree boundary, read-only** (`?mode=ro`), via
`QL_DB_ROOT`. Nothing is copied — a copy would go stale the moment the user
recorded another verdict, and the prologue would start quoting yesterday's
archive.

```bash
QL_DB_ROOT=/g/QUAKE_LEGACY/creative_suite/database python -m creative_suite.prologue.facts
```

### Code isolation
Everything new lives in `creative_suite/prologue/`. **No file owned by the
review workstation has been modified.**

One defect *was* found in review-session code — `master_profile.py` sets
`cg_drawSpeedometer`, a q3mme cvar WolfcamQL does not have, so the speed-review
profile's readout was never drawn. It has been **raised as a separate task, not
fixed here.**

---

## 4. WHAT REVIEW WOULD MOST HELP WITH

Not a request to change anything — just what would unblock the most, in order:

1. **One annotated opening candidate.** A single moment tagged "good first shot"
   proves the whole slot → candidate → placement path end to end.
2. **`SLOT_ACCEL`.** The Part 1 opening run is the single most load-bearing shot
   in the prologue. 469 qualify; one needs to be right.
3. **`SLOT_CLANWAR`.** For the Part 3 promise montage only — 1.5 s of it.

Everything else can wait, or be served by synthetic material.
