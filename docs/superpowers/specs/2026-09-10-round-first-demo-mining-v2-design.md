# Round-First Demo Mining V2 Design

**Date:** 2026-09-10

**Status:** Proposed for user review

**Input:** `C:/Users/Stoneface/Downloads/calibration_answers.json`
**Scope:** Quake Live Clan Arena plus exceptional CTF Instagib material

## Goal

Mine complete, editable gameplay stories instead of isolated overlapping trait clips. Clan Arena review and capture use a recorder-life segment bounded by the five-second countdown and the earliest of recorder death or authoritative round end. CTF Instagib is admitted only when it passes a separate high-value gate. Duel, TDM and every other gametype are excluded.

This design prepares a validated extraction manifest and a Calibration V2 review set. It does not authorize an unattended Wolfcam batch; the existing sample and batch review gates remain in force.

## Calibration V1 Findings

The supplied calibration contains 333 answers over 106 traits and 277 unique clip IDs. Twenty-six clips were presented more than once, producing 56 redundant presentations; one clip appeared under ten traits. The comments repeatedly identify four structural problems:

1. The visible interval omits the buildup, other frags, last-man call, round win or useful death ending.
2. The same underlying action appears under several trait headings, making the requested trait difficult to judge.
3. Several low-value labels describe incidental facts rather than movie-worthy action.
4. Non-CA footage, non-recorder action and broken audio were allowed to compete with valid CA material.

The calibration also establishes that an ordinary frag can become useful when it completes a strong round, supports a weapon sequence, provides transition material or lands on a musical phrase. Scoring must therefore evaluate both events and the containing round segment.

## Source Eligibility

### Clan Arena

CA is the primary corpus. A candidate is eligible only when all of the following hold:

- gametype is authoritatively classified as Clan Arena;
- the recorder identity is known for the active segment;
- the segment belongs to an authoritative fight round;
- the segment contains at least one recorder frag, a recorder death after useful action, or a user-approved cinematic/filler event;
- source and canonical content hash are known;
- parser and round-data versions meet the manifest's required versions.

### CTF Instagib

CTF Instagib is a separate exceptional lane. It is never mixed into CA percentile distributions and is eligible only when:

- gametype is CTF and Instagib is positively identified from recorded configuration or weapon/mode evidence;
- the recorder owns the action;
- the candidate contains a calibrated exceptional feature such as a long rail sequence, multi-frag rail, extreme flick, flag-play climax or exceptional movement chain;
- its mode-local score reaches the `CTF_INSTAGIB_HERO` threshold;
- its audio and capture context are usable.

An isolated ordinary rail, recorder death without payoff or non-recorder sequence is rejected even if a generic trait fires.

### Excluded Modes

Duel, TDM and all non-CA/non-CTF-Instagib modes are excluded before scoring and never enter review or extraction manifests.

## Canonical Review and Capture Unit

### CA recorder-life segment

The canonical unit is identified by:

```text
(content_hash, gamestate_id, authoritative_round_id, recorder_client, life_index)
```

The media interval is:

```text
start = five-second countdown start
end   = min(recorder death, authoritative round end, gamestate/demo end)
```

Rules:

- The five-second countdown is included once at the beginning.
- If the recorder dies, the segment ends on that death after a small audiovisual completion tail capped inside the same round. It does not continue through teammate spectating.
- If the recorder survives, the segment ends after the authoritative round result and its short audiovisual completion tail.
- The next round, next countdown and next spawn are hard exclusions.
- Every recorder frag and relevant supporting event inside the interval is preserved.
- No trait-specific trim may remove earlier or later frags from the same segment.
- The raw server-time interval and resolved Wolfcam game-clock interval are stored separately with conversion provenance.

The completion tail defaults to 750 ms and is clamped to the current round/gamestate boundary. It exists to preserve the final hit, obituary, announcer and visual response without admitting the next round.

### CTF Instagib action segment

Because CTF does not use CA fight rounds, the canonical unit is a bounded recorder-owned action sequence. The sequence begins five seconds before the first qualifying event and ends five seconds after the last linked event, clamped at recorder death, map/gamestate end or a maximum 30-second duration. Linked events are at most five seconds apart.

## Authoritative Round Boundaries

Round bounds are evidence, not inferred solely from frag gaps. The resolver consumes the versioned round-state model and records which signals established each bound. It must distinguish countdown, fight start, round result, inter-round state and next countdown.

Before manifest publication, each CA unit must pass:

- one countdown start;
- one fight start following that countdown;
- no next-round fight start inside the unit;
- monotonically ordered server-time bounds;
- recorder identity continuity;
- end reason in `RECORDER_DEATH`, `ROUND_END` or `DEMO_END`;
- no cross-gamestate join.

Ambiguous or contradictory bounds are quarantined as `ROUND_BOUNDARY_UNCERTAIN` and never captured automatically.

## One Video, Many Traits

A media unit is rendered and reviewed once. Traits are evidence attached to the unit rather than separate review videos.

Each unit stores:

- all detected traits;
- the exact event or interval supporting each trait;
- involved weapon or weapon sequence;
- confidence and provenance;
- calibration status;
- event-local score contribution;
- whether the trait is primary, supporting, transition-only or diagnostic.

The review UI may filter the same canonical unit into multiple virtual lanes, but once reviewed its verdict is shared everywhere. A `SEEN` state is derived from canonical identity; it is not a new human verdict and cannot create another presentation.

## Weapon-First Organization

CA units are available in these review lanes:

1. Rocket
2. Rail
3. Lightning Gun
4. Grenade
5. Gauntlet and close-range novelty
6. Multi-weapon sequences
7. Teleport and prediction
8. Clutch and multikill rounds
9. Filler, transition and blooper material

The primary lane is chosen from the highest-scoring calibrated moment. Secondary weapon/trait facets remain filterable. Per-weapon percentiles and thresholds prevent a common rail from outranking an exceptional grenade or gauntlet action merely because rail evidence is more abundant.

## Calibration V2 Trait Policy

### Hero families

These remain independent, high-value evidence families and receive dedicated per-weapon review examples:

- teleport exit denial and teleport prediction;
- tiny-gap and geometry-confirmed precision shots;
- split-tick or multi-frag rail;
- air rocket, air grenade and meaningful vertical punish;
- popup and multi-weapon combinations;
- target transfer and strong LG tracking/lift sequences;
- calibrated prediction and corner prefire;
- multikill, weapon triptych and exceptional clutch completion;
- high-speed action when speed materially contributes to the frag;
- genuine flick/reaction shots when the shot, not merely camera motion, is exceptional.

### Supporting modifiers

These cannot independently qualify a CA hero candidate. They may improve or explain a strong round:

- first blood and round-winning frag;
- low or critical HP with validated health provenance;
- last-man/outnumbered state;
- recorder death after useful action;
- trade/refrag;
- collateral or near-direct damage;
- fast weapon switch;
- movement, dodge or near miss without a resulting exceptional action;
- chat reaction when tied to the visible event;
- environmental death, gauntlet and telefrag when used as novelty, transition, compilation or blooper material.

### Retired standalone candidates

The following no longer create review items by themselves because Calibration V1 consistently found them incidental, misleading or useless without stronger context:

- `CHAT_REACTION_NEARBY`
- `ECONOMY_KILL`
- `REVENGE_FRAG`
- `RING_OUT`
- `SHOT_DENIED`
- `SHARED_FIREFIGHT`
- `DIED_WITH_SHOT_IN_FLIGHT` when the in-flight shot has no payoff
- `FROM_THE_GRAVE` when no post-death frag occurs
- `HERO_THEN_DEATH` and `KILL_THEN_DEATH_FAST` as standalone labels
- generic `NEAR_MISS_*` when the dodge does not enable an exceptional frag

The raw facts may still be stored for composition, search and later model development.

## Scoring Model

Scoring is hierarchical and explainable.

### Event score

Each event receives:

```text
event_score = weapon_base
            + calibrated_trait_value
            + execution_quality
            + context_value
            - evidence_penalties
```

All contributions name their source evidence. Missing telemetry contributes zero rather than an invented value.

### CA round score

```text
round_score = strongest_event
            + 0.60 * second_event
            + 0.35 * third_event
            + sequence_bonus
            + clutch_or_round_finish_bonus
            + editability_bonus
            - quality_penalties
```

Only the three strongest distinct moments contribute directly, preventing long mediocre rounds from winning by event count. Sequence bonuses cover coherent weapon chains, escalating multikills, repeated teleport punishment and other movie-worthy development.

Quality penalties cover wrong recorder, uncertain boundary, broken audio, unsupported trait, duplicate content and action hidden outside the recorder's usable view. Wrong recorder, excluded mode or uncertain boundary is a hard rejection rather than a numeric penalty.

### Calibration-derived weights

Verdicts map initially to ordinal targets:

| Verdict | Target |
|---|---:|
| GOLDEN | 5 |
| HIGH | 4 |
| MED | 3 |
| LOW | 2 |
| DISCOUNT | 1 |
| DROP | 0 |

Missing verdicts are excluded from weight fitting. Trait and weapon weights use regularized estimates so three reviewed examples cannot produce an extreme coefficient. Comment-derived structural decisions are encoded as explicit rules; free text is not silently converted into model labels.

The V2 report must show, for every retained trait and weapon family: sample count, verdict distribution, learned adjustment, confidence, before/after rank examples and overlap with other traits.

### Output tiers

CA units receive one editorial role:

- `HERO_ROUND`
- `STRONG_ROUND`
- `FILLER_ROUND`
- `TRANSITION_OR_BLOOPER`
- `REJECT`

CTF Instagib has only `CTF_INSTAGIB_HERO` or `REJECT`.

Absolute thresholds are selected from Calibration V2 after reviewing top, boundary and false-positive examples. Until that review is complete, the manifest is `CALIBRATION_PENDING` and no batch capture is permitted.

## Calibration V2 Review Set

Calibration V2 is generated from the updated deterministic features and contains:

- globally deduplicated canonical media units;
- top, boundary and known-false-positive examples per hero family;
- dedicated examples per weapon within traits where weapon changes meaning;
- complete CA recorder-life segments;
- a separate small CTF Instagib hero section;
- all contributing traits and score explanations on one card;
- persistent verdicts shared by canonical unit;
- deliberate filler and transition examples, not only top-scoring heroes.

The set prioritizes information gain. It avoids showing the same unit merely to calibrate another correlated label.

## Extraction Manifest

The preparation job writes a versioned, immutable manifest. Each row includes:

- canonical unit ID and content hash;
- source path reference kept outside public exports;
- gametype and mode evidence;
- recorder client and ownership evidence;
- gamestate, round and life identity;
- server-time start/end;
- game-clock start/end plus conversion version;
- countdown/fight/death/round-end anchors;
- ordered frags and event offsets;
- weapons, traits and score breakdown;
- editorial tier;
- capture status and validation failures;
- parser, protocol, taxonomy, calibration, round-model and scoring versions.

The job performs no Wolfcam capture by default. A separate explicit command consumes an approved manifest.

## Hard Gates

Manifest publication fails if any selected row has:

- Duel, TDM or an unsupported gametype;
- CTF without positive Instagib evidence or hero threshold;
- unknown recorder ownership;
- an uncertain or cross-round CA boundary;
- the next countdown or next round inside the interval;
- a duplicate canonical media unit;
- a server-time/game-clock conversion without provenance;
- stale derived data relative to parser or taxonomy versions;
- a score without a complete breakdown;
- a public artifact containing player names or other personal identifiers.

Capture submission additionally requires:

- Calibration V2 user approval;
- manifest user approval;
- visual inspection of a small boundary sample;
- one successful midpoint/anchor validation for the active Wolfcam runtime;
- the existing single-worker queue and cancellation safeguards.

## Data Flow

```text
decoded demo evidence
        |
        +--> mode eligibility ----> reject Duel/TDM/other
        |
        +--> authoritative rounds + recorder lives
        |              |
        |              +--> canonical CA media units
        |
        +--> deterministic weapon/trait evidence
                       |
calibration V1 --------+--> V2 weights and trait policy
                                      |
                                      +--> round/event scoring
                                                   |
                                                   +--> deduplicated V2 review
                                                   +--> gated extraction manifest
```

## Verification Strategy

1. Unit-test countdown, death, round-end, demo-end and cross-gamestate boundaries.
2. Prove a next-round timestamp can never enter a CA interval.
3. Prove death ends recorder media before teammate spectating begins.
4. Test gametype exclusions and positive CTF Instagib evidence.
5. Test canonical deduplication across traits and duplicate demo files.
6. Test shared verdict propagation across virtual trait and weapon lanes.
7. Test ordinal calibration mapping, regularization and score explanations.
8. Differentially inspect selected round boundaries against the authoritative round-state evidence and Wolfcam playback.
9. Generate a visual record of Calibration V2 and the manifest summary.
10. Run relevant Python tests and pyright before any commit or PR.

## Delivery Sequence

1. Freeze Calibration V1 as a private input and create an anonymized aggregate report.
2. Implement the mode and canonical-unit contracts.
3. Implement hard round/life bounds and validation.
4. Implement calibration-derived trait policy and hierarchical scoring.
5. Generate the deduplicated Calibration V2 review set.
6. Incorporate the user's V2 decisions and lock thresholds.
7. Generate and validate the extraction manifest.
8. Review a small capture sample.
9. Only after approval, submit the full extraction job through the single-worker queue.

## Non-Goals

- Mining Duel or TDM.
- Treating every detected fact as an independent highlight.
- Guaranteeing unavailable non-POV telemetry.
- Reconstructing missing gameplay as measured evidence.
- Starting a batch capture from an unreviewed score threshold.
- Changing the protected-branch policy or human review gates.
