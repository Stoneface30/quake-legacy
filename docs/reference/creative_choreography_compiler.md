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
