# PANTHEON — Pandora Effect Atlas

**Status:** research and design only  
**Date:** 2026-09-01  
**Implementation gate:** no production effect work until the four editorial
canaries pass and the user approves a prototype slice.

This document defines a Quake-native cinematic vocabulary. It does not claim
that every entry is implemented. Capability labels are deliberately strict:

- **PROVEN CURRENT RUNTIME** — exercised by current code plus a test or runtime
  artifact.
- **SMALL IMPLEMENTATION** — existing evidence and runtime primitives are
  sufficient, but the adapter/compiler/consumer is missing.
- **POST/COMPOSITOR** — needs a V2 image compositor, mattes, optical flow, or
  multi-pass assembly that PANTHEON does not currently have.
- **MODEL/ANIMATION** — needs authored model, rig, skin, or animation assets.
- **ENGINE/FORK RESEARCH** — needs renderer or replay-engine work beyond the
  proven stock WolfcamQL runtime.

## 1. Creative constitution

1. **Gameplay truth is immutable.** Effects may reveal, frame, retime, or
   transform presentation; they must not move a kill, dodge, hit, round result,
   or chat event.
2. **Evidence before spectacle.** An effect fires from a typed semantic anchor
   with provenance and confidence, never because a timestamp “looks close.”
3. **Music chooses presentation, not history.** Music may select a legal
   slow-motion rate or sync anchor; it may not relocate the gameplay event.
4. **POV proves; cinema explains.** FP is the truth-bearing spine. A recam,
   FL, or transformed world must clarify geometry, emotion, or consequence.
5. **Result-aware storytelling.** A lost 1vX may be tense or tragic, never
   falsely triumphant. A kill followed by death may be excluded, acknowledged,
   or used as a transition according to the actual outcome.
6. **OFF is real.** Every effect has OFF / SUBTLE / HERO forms. OFF must be a
   byte-stable no-op at the recipe level, following `pandora.py`.
7. **Clarity wins.** If prerequisites are weak, confidence is low, or the
   treatment obscures the frag, fall back to clean FP and the normal seam.
8. **Surrealism is authored punctuation.** The ULBE lineage gives permission
   for wit and rupture, not random filters or imitation of a signature work.

### The selection question

Every chosen treatment must answer:

> Why this effect, on this event, at this musical moment, from this camera?

If the system cannot answer all four clauses, the effect is OFF.

## 2. External technique map

| Film/VFX concept | Why it works | Quake-semantic use | Honest domain |
|---|---|---|---|
| Action match | Carries motion across a discontinuity | rocket arc, strafe, recoil, jump line | SMALL IMPLEMENTATION |
| Graphic match | Carries shape, color, or composition | doorway, rail line, weapon silhouette, armor orb | SMALL IMPLEMENTATION |
| Audio match / J- or L-cut | Sound predicts or survives the image cut | launch in A, impact in B; announcer or chat bridge | SMALL IMPLEMENTATION |
| Occlusion/object wipe | Hidden frame gives a natural substitution point | door, pillar, weapon, player, smoke | SMALL IMPLEMENTATION with clean occluder; otherwise POST |
| Depth wipe | Separates foreground and background spatially | architecture peels away to reveal enemies | POST/COMPOSITOR using proven depth export |
| Whip transition | Directional blur suppresses detail while preserving velocity | snap aim, high-speed turn, recam pan | SMALL IMPLEMENTATION; POST for optical-flow refinement |
| Match dissolve / pose match | Shared silhouette makes one image appear to evolve | killer pose, airborne model, weapon framing | POST/COMPOSITOR plus motif descriptors |
| Portal / camera-through-object | Gives an in-world reason for changing scenes | teleporter, eye, barrel, impact crater, ad board | POST; true continuous path may need ENGINE work |
| Speed ramp / bullet time | Allocates attention around the decisive instant | direct rocket, rail hit, dodge clearance | TimeMap proven; capture/render consumer missing |
| Freeze decomposition | Holds meaning while components separate | enemy/map/weapon breaks into layers | POST or MODEL/ANIMATION |
| Match move / tracked composite | Makes inserted media inherit perspective and motion | world-surface video, PANTHEON glyph, threat lines | POST/COMPOSITOR |
| Projection mapping / video texture | Turns footage into part of the world | ad boards, temple walls, teleporter surface | POST now; engine-native video material needs research |
| Material transition | Stable geometry with changing surface reads as world mutation | low HP, buildup, countdown, frag premonition | SMALL IMPLEMENTATION for shader remap; POST for local masks |
| Disintegration/reassembly | Makes a scene change feel caused by impact | gib/stone/metal shards form next scene | POST or MODEL/ANIMATION |
| Silhouette reveal | Preserves recognition while withholding detail | sequential enemy reveal, clutch tableau | POST; engine skin/lighting variant is possible later |
| Motion-vector transition | Carries per-pixel motion into the next image | LG smear, strafe flow, projectile direction | POST/COMPOSITOR |
| Clone/time echo/multi-exposure | Makes movement path and rhythm visible | rocket jump, dodge, rail flick | POST; simple frame echoes are a small implementation |
| World-building reveal | Local detail expands into spatial understanding | wireframe → texture → light; FP → arena reveal | camera proven; compositing/material phases missing |
| Controlled datamosh | Predictive-frame failure reads as digital rupture | demo-memory tear or teleporter overload | POST only; rare, deterministic, never over proof frame |

Commercial template libraries are useful as taxonomy and timing references,
not as PANTHEON's design language. Preset-derived glitch, HUD, and transition
packs are rejected unless rebuilt around Quake evidence and PANTHEON materials.

## 3. Effect Atlas

Each entry supplies the required production contract in compact form.

### IMPACT — `IMPACT_EVENT_LOCK`

- **Purpose:** make the recognized hit or kill feel inevitable and readable.
- **Trigger:** `PROJECTILE_IMPACT`, `FRAG`, or weapon-specific hit with
  confidence at or above the effect threshold.
- **Required evidence:** event type, actor, demo/edit clock, confidence,
  impact position when spatial FX is requested.
- **Visual:** 6–12 frame pressure ramp into the event, optional one-frame light
  accent, rapid release; never hide hit confirmation.
- **Audio/music:** event transient lands on a selected beat/subdivision; game
  transient remains audible and may sidechain music.
- **Camera:** FP default; FL only if it reveals an otherwise unclear trajectory.
- **Time:** event-local piecewise TimeMap with the event fixed as a hard anchor.
- **Domain:** TimeMap + safe `at <t> runfx`; final consumer is SMALL IMPLEMENTATION.
- **OFF / SUBTLE / HERO:** clean event / micro-ramp+audio focus / ramp+spatial FX+
  one-frame grade punch.
- **Cheap failure:** generic shake, long flash, effect firing on muzzle rather
  than impact, or optical flow smearing the decisive frame.

### DODGE — `THREAT_MISS_REVEAL`

- **Purpose:** visualize skill expressed by what almost happened.
- **Trigger:** `DODGE_HERO` with classified projectile/beam threat.
- **Required evidence:** threat path, player path, closest approach, clearance,
  classifier version, confidence.
- **Visual:** brief threat line or negative-space halo at closest approach;
  optional echo of the player's evasive path.
- **Audio/music:** near-miss accent on a pickup or syncopation; payoff on safe
  clearance, not on projectile launch.
- **Camera:** FP truth followed by one short side/top explanatory view if needed.
- **Time:** subtle hold or slow around minimum separation; anchors remain fixed.
- **Domain:** semantic data proven; overlay needs POST/COMPOSITOR.
- **OFF / SUBTLE / HERO:** clean / faint line+duck / path echo+geometry reveal.
- **Cheap failure:** esports-analysis clutter, invented trajectory, or celebrating
  a dodge that still results in immediate death without narrative intent.

### LG/TRACKING — `LG_BEAM_CHOREOGRAPHY`

- **Purpose:** turn continuous aim into a readable musical phrase.
- **Trigger:** high-confidence `LG_BURST` with sustained contact/tracking span.
- **Required evidence:** beam start/end samples, hit cadence, screen/world
  direction, duration, target identity scoped only to the scene.
- **Visual:** beam brightness breathes with hit cadence; optional restrained
  multi-exposure of target movement.
- **Audio/music:** hits align to subdivisions; beam sustain may bridge a cut.
- **Camera:** FP preferred; axis cam only when it explains tracking geometry.
- **Time:** usually 1:1; short ramp at acquisition/release, not blanket slow-mo.
- **Domain:** FX cue SMALL IMPLEMENTATION; beam bridge/echo POST.
- **OFF / SUBTLE / HERO:** native / cadence glow / axis recam+beam bridge.
- **Cheap failure:** nightclub strobe, obscured target, or forcing each damage
  tick to a beat.

### MULTIKILL — `KILL_COUNT_CASCADE`

- **Purpose:** make escalation legible without turning the film into a HUD demo.
- **Trigger:** verified multikill window with distinct victims/events.
- **Required evidence:** ordered kills, canonical moment ID, round context,
  survival/outcome, confidence.
- **Visual:** one restrained count token per confirmed kill; geometry or material
  state can simplify progressively.
- **Audio/music:** each decrement/addition uses real game transient; final kill
  receives the phrase-level weight only when musically supported.
- **Camera:** FP spine; at most one FL contrast under P1-K.
- **Time:** individual event locks; no clip shortening to manufacture cadence.
- **Domain:** count overlay POST; event sequence proven.
- **OFF / SUBTLE / HERO:** clean / minimal count / staged world simplification.
- **Cheap failure:** giant gamer text, incorrect count, repeated canonical moment,
  or treating unrelated cleanup kills as one chain.

### 1VX — `LAST_ONE_STANDING`

- **Purpose:** tell a truthful surrounded-player story with resolution.
- **Trigger:** round state identifies one subject against X live opponents.
- **Required evidence:** round boundaries, rosters/team relation, alive states,
  positions/visibility, ordered deaths, final round result.
- **Visual:** enemy reveal, count, threat directions, progressive strip-away, and
  result-specific payoff.
- **Audio/music:** tension pulse follows threats; victory release is forbidden
  unless `ROUND_WIN`; loss resolves with cut, collapse, or death bridge.
- **Camera:** tactical overview may introduce; FP carries decisions and kills.
- **Time:** setup may breathe; kill anchors stay fixed.
- **Domain:** evidence extraction + POST; full design in §5.
- **OFF / SUBTLE / HERO:** clean / count only / full geometry-and-threat tableau.
- **Cheap failure:** false victory, wallhack-like information the player/audience
  cannot parse, or enemy labels exposing personal identifiers.

### CLUTCH — `CLUTCH_PRESSURE_FIELD`

- **Purpose:** express narrowing options and a decisive solution.
- **Trigger:** low-resource/high-threat state followed by round-deciding action.
- **Required evidence:** health/armor/ammo, alive count, timer, positions,
  decision event, outcome.
- **Visual:** vignette/space compresses during pressure then releases on success;
  on loss it closes or cuts into death.
- **Audio/music:** thin the mix before decision; restore bandwidth on resolution.
- **Camera:** FP; overview only before engagement.
- **Time:** restrained pre-event compression and outcome-dependent release.
- **Domain:** SMALL IMPLEMENTATION for grade/audio; POST for spatial field.
- **OFF / SUBTLE / HERO:** clean / mix+grade pressure / spatial compression.
- **Cheap failure:** melodrama on an ordinary duel or triumph before result.

### LOW_HP — `LAST_HEART_WORLD`

- **Purpose:** make vulnerability perceptible without faking game state.
- **Trigger:** health below approved threshold during a meaningful survival span.
- **Required evidence:** sampled HP/armor, damage timestamps, recovery/death,
  scene boundaries.
- **Visual:** materials lose warmth/detail or skin/world state shifts; restoration
  follows actual recovery, not the edit beat.
- **Audio/music:** narrowed ambience and real heartbeat-like low pulse only if it
  does not mask weapon/audio evidence.
- **Camera:** FP.
- **Time:** no compulsory retime; damage and recovery are fixed anchors.
- **Domain:** global shader remap is SMALL IMPLEMENTATION; selective world/player
  treatment needs POST or engine hook research.
- **OFF / SUBTLE / HERO:** clean / grade+sound / reactive material state.
- **Cheap failure:** generic red vignette, wrong threshold, or state persisting
  after health recovery.

### ROUND_WIN — `ARENA_RELEASE`

- **Purpose:** give a verified win spatial and musical consequence.
- **Trigger:** `ROUND_WIN` after the final deciding event.
- **Required evidence:** authoritative result, final event, team membership.
- **Visual:** world detail/light returns or expands; count locks at zero.
- **Audio/music:** release/downbeat after result; announcer remains intelligible.
- **Camera:** FP proof then optional short arena reveal.
- **Time:** no pre-result victory cue.
- **Domain:** FX/light remap SMALL IMPLEMENTATION; world reveal uses camera+POST.
- **OFF / SUBTLE / HERO:** clean / light release / arena-scale reveal.
- **Cheap failure:** confetti, premature payoff, or identical win treatment on
  every round.

### ROUND_LOSS — `DEFEAT_CONTINUATION`

- **Purpose:** preserve the value of brave play without lying about the outcome.
- **Trigger:** meaningful sequence ending in `ROUND_LOSS`.
- **Required evidence:** result, subject death/survival, preceding kills/dodges.
- **Visual:** effect language contracts, collapses, or transfers momentum into
  the next scene through death/impact/occlusion.
- **Audio/music:** tension may continue; no victory sting.
- **Camera:** stay with consequence; do not cut away before proof.
- **Time:** usually real-time at result.
- **Domain:** editorial SMALL IMPLEMENTATION; collapse variants POST.
- **OFF / SUBTLE / HERO:** clean / restrained grade falloff / designed death bridge.
- **Cheap failure:** humiliation gag on a serious clutch or ambiguous outcome.

### TEAM_ROUND — `TACTICAL_COLLAPSE_MAP`

- **Purpose:** turn a coordinated round into a team story, not isolated frags.
- **Trigger:** 2–4 in-scope teammates versus a coordinated opposing side.
- **Required evidence:** anonymized team relation, round bounds, positions,
  regroup/crossfire/chase/isolation/collapse events, result.
- **Visual:** sparse tactical lines and spatial chapters; individual hero effects
  remain subordinate to the team arc.
- **Audio/music:** sections map to setup, contact, collapse, resolution.
- **Camera:** overview establishes relationships; POV rotations prove actions.
- **Time:** round structure governs pacing; events are not moved.
- **Domain:** new evidence model + POST; design in §6.
- **OFF / SUBTLE / HERO:** clean round / chapter labels / full tactical tableau.
- **Cheap failure:** minimap clutter, invented coordination, or public player IDs.

### DEATH — `DEATH_AS_CUT`

- **Purpose:** decide honestly whether post-kill death is excluded, retained, or
  transformed into transition material.
- **Trigger:** subject death within the approved aftermath window.
- **Required evidence:** preceding kill, trade relation, round result, death type,
  timing, next-scene match candidate.
- **Visual:** hard consequence, blood/gib/occlusion wipe, or clean exclusion when
  death adds nothing.
- **Audio/music:** retain death transient when narratively material; bridge it
  only to compatible next-scene sound.
- **Camera:** proof first; no evasive cut that falsely implies survival.
- **Time:** no slow glorification by default.
- **Domain:** decision logic SMALL IMPLEMENTATION; wipes POST.
- **OFF / SUBTLE / HERO:** leave edit unchanged / consequence tail / matched wipe.
- **Cheap failure:** hiding a strategically meaningful death or using gore as a
  generic transition stamp.

### MOVEMENT — `VELOCITY_SIGNATURE`

- **Purpose:** make elite traversal a recurring visual and musical language.
- **Trigger:** high-speed line, dodge chain, strafe solution, or route motif.
- **Required evidence:** player path, speed curve, camera direction, map region,
  canonical occurrence ID.
- **Visual:** restrained path echo, speed contrast, or vector-matched cut.
- **Audio/music:** footsteps/jumps/landings hit subdivisions; movement payoff may
  land on phrase transition.
- **Camera:** FP or geometry-explaining recam.
- **Time:** rate changes must preserve takeoff/landing/action anchors.
- **Domain:** metadata search SMALL IMPLEMENTATION; echoes POST.
- **OFF / SUBTLE / HERO:** clean / one echo / motif chain across scenes.
- **Cheap failure:** generic speed blur that destroys map readability.

### ROCKET_JUMP — `RJ_PHRASE`

- **Purpose:** use repeated but distinct rocket jumps as transition vocabulary.
- **Trigger:** classified rocket-jump occurrence with valid movement/projectile
  evidence.
- **Required evidence:** occurrence ID, takeoff/launch/landing, path/vector,
  weapon, map region, camera direction.
- **Visual:** 4/8/16-cut action/graphic match family; never repeat the same
  canonical moment without override.
- **Audio/music:** launch and landing form call/response across subdivisions.
- **Camera:** consistent framing or deliberately alternating FP/FL grammar.
- **Time:** candidate rates chosen within visual bounds to land hard anchors.
- **Domain:** motif search design + existing TimeMap; assembly missing.
- **OFF / SUBTLE / HERO:** single clip / 4-cut motif / 8–16-cut phrase montage.
- **Cheap failure:** same clip recycled, mismatched direction, or cuts too short
  to understand the route.

### TELEPORT — `TELEPORTER_WORLD_PASS`

- **Purpose:** make scene change diegetic to Quake.
- **Trigger:** real teleporter entry/exit or explicitly authored FX portal.
- **Required evidence:** entry/exit anchors, positions, camera approach vector,
  compatible destination frame.
- **Visual:** camera enters energy/occlusion and exits another scene; optional
  material/grade interpolation inside the portal.
- **Audio/music:** teleport transient spans seam; destination ambience pre-laps.
- **Camera:** continuous-looking approach/exit, not necessarily one true take.
- **Time:** cut occurs under full occlusion or peak emission.
- **Domain:** native teleporter FX proven; screen-space pass POST.
- **OFF / SUBTLE / HERO:** hard match / light wipe / full world portal.
- **Cheap failure:** circular stock portal pasted over unrelated framing.

### DOOR — `DOOR_GEOMETRY_MATCH`

- **Purpose:** use arena architecture as an invisible transition mechanism.
- **Trigger:** camera/player crosses or is occluded by a door/arch/pillar.
- **Required evidence:** geometry/region descriptor, screen-space occlusion,
  motion/camera direction, destination geometry match.
- **Visual:** object wipe or graphic match into a different map/round.
- **Audio/music:** door/footstep may bridge; cut aligns with rhythmic hinge.
- **Camera:** approach and exit vectors match.
- **Time:** cut under occlusion; gameplay event clocks unchanged.
- **Domain:** motif descriptors + compositor mask; some clean wipes small.
- **OFF / SUBTLE / HERO:** hard cut / tracked object wipe / material morph doorway.
- **Cheap failure:** edge mismatch, reversed screen direction, or visible mask slip.

### CHAT — `CHAT_IN_WORLD_ECHO`

- **Purpose:** use genuine reaction, rage, humor, praise, or team call as scene
  material without turning private identities into spectacle.
- **Trigger:** categorized timed chat linked to a relevant event/round.
- **Required evidence:** demo time, anonymized speaker role, raw text in private
  data only, safe/redacted display text, category/confidence, context link.
- **Visual:** restrained subtitle, world-surface projection, or bubble that becomes
  a transition mask.
- **Audio/music:** appears in a musical pocket; no synthetic voice by default.
- **Camera:** screen/world placement must not obscure action.
- **Time:** exact chat timestamp through TimeMap.
- **Domain:** parser/index research + POST; §8.
- **OFF / SUBTLE / HERO:** hidden / subtitle / in-world portal or kinetic type.
- **Cheap failure:** meme-font spam, decontextualized insult, leaked identifier,
  or displaying team calls before their tactical meaning is clear.

### INTRO — `WORLD_FORGING_REVEAL`

- **Purpose:** present PANTHEON as a system that creates the Quake world.
- **Trigger:** title/intro sequence, not an arbitrary frag.
- **Required evidence:** approved map/asset set and ordered build phases.
- **Visual:** wireframe → material → details → lighting → living gameplay.
- **Audio/music:** construction layers enter with musical layers; final light-up
  lands on title or first gameplay handoff.
- **Camera:** controlled NATIVE_CAM10 flythrough or 3D scene camera.
- **Time:** phase boundaries follow music structure.
- **Domain:** camera proven; true staged world build needs ENGINE/FORK or 3D POST.
- **OFF / SUBTLE / HERO:** normal title / shader-light reveal / full map forge.
- **Cheap failure:** generic tech wireframe unrelated to actual map geometry.

### TRANSITION — `KILLER_MATCH_FREEZE`

- **Purpose:** turn a decisive pose/weapon/frame into the next scene's entry.
- **Trigger:** verified kill/death frame with a high-similarity candidate.
- **Required evidence:** actor pose or silhouette, weapon, screen position,
  camera direction, canonical IDs for both moments.
- **Visual:** brief freeze or deceleration; player/weapon/pose becomes matched
  frame in next scene.
- **Audio/music:** impact can ring across; next scene audio pre-laps.
- **Camera:** matched framing and direction are mandatory.
- **Time:** both source events remain fixed; only entry/exit handles adjust.
- **Domain:** motif search + POST/COMPOSITOR.
- **OFF / SUBTLE / HERO:** hard match / short dissolve / morph/decomposition.
- **Cheap failure:** loose match advertised as magic, long freeze, face/model warp.

### MOTIF_MONTAGE — `RHYTHMIC_MOTIF_GRID`

- **Purpose:** convert less-important, unused moments into a coherent 4/8/16-cut
  musical statement.
- **Trigger:** music requests a phrase-length rapid sequence and enough distinct
  compatible occurrences exist.
- **Required evidence:** motif descriptors, canonical occurrence identity,
  usage ledger, action readability floor, musical subdivision grid.
- **Visual:** one chosen invariant—weapon, doorway, vector, pose, geometry—remains
  stable while context changes.
- **Audio/music:** game transients form a designed percussion layer.
- **Camera:** consistent axis or an intentional alternating pattern.
- **Time:** no candidate is shortened below its readable action kernel; event
  anchors remain fixed.
- **Domain:** new search/index + assembly; §7.
- **OFF / SUBTLE / HERO:** no montage / four cuts / eight or sixteen cuts.
- **Cheap failure:** clip soup, repeated canonical moment, no invariant, or every
  cut landing mechanically on quarter notes.

### MODEL/ANIMATION — `GRENADE_FOOTBALL_CONTROL`

- **Purpose:** deliver one authored comic rupture from a direct-grenade event.
- **Trigger:** direct grenade trajectory/body contact with an approved gag slot.
- **Required evidence:** grenade path, contact position, target pose/window,
  outcome, comedy budget.
- **Visual:** chest control or headbutt-style anticipation/contact/reaction,
  grounded in the actual grenade path.
- **Audio/music:** contact on a comic accent; preserve explosive consequence.
- **Camera:** one explanatory recam; return to truth quickly.
- **Time:** short anticipation stretch only; contact anchor fixed.
- **Domain:** MODEL/ANIMATION plus post or engine replay choreography.
- **OFF / SUBTLE / HERO:** clean direct / tiny contact emphasis / full bespoke gag.
- **Cheap failure:** canned animation, wrong collision, overlong joke, repeated use.

## 4. Transition grammar

Every transition recipe needs source/destination recipe IDs, semantic anchors,
resolved edit-clock values, canonical-moment inequality, evidence references,
music strategy, visual prerequisites, fallback, and intensity.

| Type | Match/trigger contract | Domain | Fallback / reject condition |
|---|---|---|---|
| `PROJECTILE_BRIDGE` | plausible point-series flight; A impact → B launch/direction | metadata exists; final visual SMALL/POST | hard impact cut; reject slow/bad path |
| `TELEPORTER_PASS` | entry emission/occlusion → compatible exit | POST | light wipe; reject weak approach framing |
| `DOOR_MATCH` | same doorway/arch shape and screen direction | SMALL/POST | graphic hard cut |
| `OCCLUSION_CUT` | opaque foreground coverage above threshold | SMALL/POST | hard cut at maximum coverage |
| `WHIP_MATCH` | outgoing/incoming camera velocity direction and magnitude match | SMALL/POST | short motion-blur cut |
| `GRAPHIC_MATCH` | shape/color/composition similarity above threshold | SMALL | hard cut |
| `POSE_MATCH` | distinct occurrences; pose/silhouette and framing match | POST | short dissolve or OFF |
| `KILLER_MATCH` | killer/weapon/pose in A matches role/framing in B | POST | hard match |
| `WEAPON_MATCH` | same weapon silhouette and screen position | SMALL/POST | hard cut |
| `GEOMETRY_MATCH` | map edge/arch/corridor descriptor match | SMALL/POST | hard cut |
| `BLOOD_WIPE` | real blood/death event supplies expanding matte | POST | death transient hard cut |
| `GIB_WIPE` | real gib field crosses sufficient screen area | POST | particle/light wipe |
| `RAIL_LINE_WIPE` | rail vector traverses frame and matches B direction | POST | flash/hard cut |
| `LG_BEAM_BRIDGE` | sustained beam axis/cadence compatible across scenes | POST | audio bridge |
| `DEPTH_WIPE` | valid synchronized depth streams on both scenes | POST | luma/occlusion wipe |
| `MATERIAL_DISSOLVE` | stable geometry or tracked surface correspondence | POST; global remap SMALL | grade lerp |
| `WORLD_MORPH` | map/geometry correspondence or reconstructed scene | POST/ENGINE | geometry match |
| `MAP_BUILD` | ordered wireframe/material/detail/light states | ENGINE/3D POST | light reveal |
| `EYE_PORTAL` | tracked eye/visor-like surface with sufficient screen coverage | POST/MODEL | circular occlusion cut |
| `WEAPON_BARREL_PORTAL` | barrel center, orientation, and push-in coverage | POST/3D | muzzle-flash wipe |
| `AD_BOARD_PORTAL` | identified planar world surface and tracked corners | POST | screen replacement then cut |
| `VIDEO_TEXTURE_PORTAL` | stable surface plus approved video source/matte | POST/ENGINE research | ad-board hard cut |
| `CHAT_BUBBLE_TRANSITION` | safe timed chat plus bubble covering cut region | POST | subtitle J-cut |
| `PLAYER_MORPH` | compatible silhouette/pose and authorized model treatment | MODEL/POST | pose match |
| `MODEL_MATCH` | model/weapon silhouette and camera match | SMALL search + POST | graphic match |

### Transition rules

- A transition cannot bridge a scene to itself. Near-duplicate demo recordings
  require canonical occurrence identity, not filename/hash alone.
- Projectile validity is measured from the point series: at least 8 points,
  at least 200 ms, at least 64 units, finite coordinates, and plausible arc
  speed. Scalar launch/impact equality is not corruption evidence.
- An effect-heavy seam needs a reason and a cooldown. Most seams remain clean
  action/graphic/audio matches.
- Seam handles may move inside approved trim budget; gameplay events do not.

## 5. 1vX story treatments

### Required state model

`RoundStory` should eventually contain round ID, mode, start/end/result,
anonymized team roles, alive-state intervals, sampled positions, visibility or
knowledge policy, event anchors, and a `truth_tone` of `VICTORY`, `LOSS`, or
`UNRESOLVED`. The tone is derived from result; the editor cannot override it to
victory.

### Treatment A — Tactical minimal

1. Establish `1vX` count for 12–24 frames.
2. Show only threats supported by approved position/visibility evidence.
3. Decrement on authoritative deaths.
4. Remove the overlay during the actual proof frame.
5. Resolve with `ROUND_WIN` release or `ROUND_LOSS` consequence.

### Treatment B — Geometry strip-away

The arena progressively simplifies around confirmed threats: nonessential
materials desaturate, then selected architecture becomes outline/depth planes.
Enemies appear sequentially as evidence permits. Each kill removes one threat
layer. This needs depth/segmentation compositing; it is not a current shader
remap claim.

### Treatment C — Mythic tableau

A short tactical overview freezes or slows before contact. Threat lines and
enemy silhouettes form a readable composition; the camera dives back to FP.
Use once per major sequence. If the round is lost, the tableau fractures or
flows into `DEATH_AS_CUT`; it never blooms into triumph.

## 6. Team-round cinematic system

### Candidate detection

- Round-bounded, mode-aware sequence.
- Between 2 and 4 in-scope teammates share a team.
- Opponents form a coordinated or similar-tag group, stored as anonymized team
  relation rather than public nicknames.
- Sufficient event/position coverage to classify at least two of: regroup,
  chase, crossfire, isolated player, collapse, clutch, resolution.

### Narrative phases

| Phase | Evidence | Editorial language |
|---|---|---|
| SETUP | spawn/formation/position samples | wide or movement breath |
| REGROUP | teammate distance converges | lines/geometry converge |
| CONTACT | damage/fire/visibility cluster | FP rotation begins |
| ISOLATION | one player separates under threat | mix narrows, space contracts |
| CROSSFIRE | complementary attacks/angles | alternating POV with shared target |
| COLLAPSE | opponent alive count and positions compress | pacing accelerates |
| CLUTCH | last actor/high leverage | 1vX grammar, result-aware |
| RESOLUTION | authoritative round result | release or consequence |

The unit of selection is the round, not a bag of kills. Individual clips remain
full-length under existing rules unless a later raw-demo scene recipe defines a
new review-approved scene boundary.

## 7. Motif-montage search design

### Identity first

Use `canonical_moment_id`, distinct from demo filename and file hash. A moment
is the semantic occurrence: normalized demo lineage, round/event identity,
actor role, and tight source-time neighborhood. Near-duplicate demo files map to
one canonical moment. `moment_usage` rejects reuse unless an explicit override
records the reason.

### Descriptor layers

| Layer | Candidate features |
|---|---|
| Semantic | weapon, event, map, region, round role, movement type |
| Geometry | doorway/arch/corridor ID, depth edges, vanishing point, line map |
| Motion | player/projectile vector, speed curve, camera yaw/pitch velocity |
| Composition | opponent centroid/size, weapon silhouette, horizon, color blocks |
| Pose | coarse skeletal/model pose or silhouette embedding |
| Music fit | readable kernel duration, legal rates, transient pattern |
| Usage | canonical ID, prior sequence/part use, override/cooldown |

### Query contract

Input: motif type, 4/8/16 count, music region, hard sync anchors, visual rate
range, minimum readability, exclusions, and usage policy.

Pipeline:

1. Filter for evidence completeness and unused canonical moments.
2. Filter semantic invariants (for example same weapon + rocket jump).
3. Score geometry, motion, composition, and pose similarity.
4. Solve candidate playback rates inside the approved visual range.
5. Optimize the sequence jointly for continuity and diversity; nearest-neighbor
   independently per cut is forbidden because it creates duplicates/clusters.
6. Emit reasons and fallbacks for human review.

Different occurrences of the same route or movement are allowed. The same
canonical occurrence is not.

## 8. Chat creative index

### Feasibility question

Timed demo chat is useful only if the parser can prove message time, speaker
slot/role, and scene/round context. Until a real corpus sample validates packet
coverage and encoding, this remains a research slice—not a broad extraction
claim.

### Private index schema

```text
ChatEvent(
  chat_id, demo_sha256, demo_us, round_id,
  speaker_slot, speaker_role, raw_text_private,
  safe_text, category, category_confidence,
  surrounding_event_ids, scene_candidate_ids,
  pii_review_status, parser_version
)
```

Categories: `GG`, `RAGE`, `INSULT`, `REACTION`, `LAUGH`, `COMPLIMENT`,
`TEAM_CALL`, `OTHER`.

### Safety and creative rules

- Raw names/text never enter public docs, screenshots, or manifests.
- Search may use private text; display uses reviewed `safe_text` and anonymized
  roles.
- Insults require context and explicit creative approval; no automated public
  humiliation.
- `TEAM_CALL` is tactical evidence only when its timing and subsequent play
  support that reading.
- Chat can become subtitle, tracked world text, audio-less anticipation, or a
  transition matte. It never obscures the frag.

## 9. Music-reactive effect model

### Music may choose slow-motion rate

Let an event at source time `E` be fixed. For a reviewed source window of
duration `D_demo` and candidate musical span `D_music`, the constant candidate
rate is:

```text
rate = D_demo / D_music
```

The solver may consider integer beat spans and musically meaningful
subdivisions only when the music evidence is reliable. It filters candidates
through an effect-specific visual range before ranking musical exactness.
Starting review bounds—not production law—are:

| Treatment | Candidate visual rate |
|---|---:|
| subtle emphasis | 0.75–0.95× |
| hero impact/dodge | 0.45–0.75× |
| deliberate bullet-time accent | 0.25–0.45×, high-quality evidence only |
| speed release | 1.05–1.50×, never over proof frame |

These ranges require canary review before becoming defaults.

### Piecewise curve contract

A future `TimeMap` extension can approximate eased ramps with contiguous exact
rational segments. Hard anchors include event, cut, and selected music points.
The solver changes the mapping between anchors while preserving:

- source event identity and order;
- exact event-to-music alignment;
- approved source window;
- continuity at every segment boundary;
- readable minimum dwell around proof frames.

Reverse remains out of `SceneRecipeV2` today and must not be smuggled in as a
negative rate.

### Evidence hierarchy

Phrase/section boundary > high-confidence beat/downbeat > reliable subdivision
> transient-only fallback. Weak beat evidence disables exact-rate selection and
falls back to an editorially approved rate.

## 10. Model and animation idea list

| Idea | Semantic trigger | Required work |
|---|---|---|
| grenade chest control/headbutt | direct grenade/body contact | bespoke pose/animation + recam composite |
| player statue fracture | decisive kill/round result | player mesh/pose capture + fracture simulation |
| weapon-to-temple morph | weapon match / intro | compatible meshes + morph/post |
| low-HP skin degradation | health state | skin variants; runtime switching hook or post matte |
| slow-mo armor reassembly | pickup/recovery | model fragments + animation |
| enemy silhouette procession | 1vX reveal | pose/silhouette assets + depth composite |
| killer pose echo | kill transition | pose descriptors; optional rigged recreation |
| rail-body line sculpture | rail frag | beam/pose geometry + post |
| rocket-riding camera object | valid projectile flight | camera proven; hero projectile model/FX polish |
| gib-to-map reassembly | death transition | particle/geometry simulation |
| PANTHEON temple guardians | intro/team round | original models, rigging, legal asset provenance |
| animated weapon-surface video | portal/motif | UV/video material pipeline; engine research or post |

The current binary's practical runtime path remains MD3. Advanced IQM animation
would require engine rebase/fork work and weeks of asset validation; see
`model_animation_path.md`. glTF is an authoring interchange, not a runtime claim.

## 11. Current-capability matrix

| System | Honest status | What it enables now | Missing for the atlas |
|---|---|---|---|
| SceneRecipeV2 | PROVEN CURRENT RUNTIME | immutable scene identity, anchors, clocks, persistence | V2 final assembly consumer |
| semantic gameplay events | PROVEN for current datasets; partial wiring | typed evidence, impact/frag/dodge data | broad round/chat/team/motif evidence adapters |
| TimeMap | PROVEN contract/editor | exact rational normal/slow/freeze mapping | timed capture/final render consumer; reviewed piecewise solver |
| Music Intelligence V2 | PROVEN CURRENT RUNTIME | cached sections/events/profiles/regions | final-Part V2 integration and rate solver |
| NATIVE_CAM10 | PROVEN CURRENT RUNTIME | native 512-point camera paths | collision-quality improvements and final integration |
| `runfx` | PROVEN safe deferred form | semantic world-space cue/impact FX | wider effect compiler and authoring library |
| `runfxat` | TRAP unless explicit coordinates | explicit-coordinate scheduling only | never emit bare init-time form |
| shader remap | PROVEN engine primitive | live global material swap/revert | Scene/Pandora compiler; local/selective state logic |
| ComfyUI assets | PROVEN but partly degraded | asset generation/upscale/style workflows | repair failed workflows; deterministic manifest application |
| depth export | PROVEN auxiliary stream | ControlNet hint, depth-aware design input | synchronized compositor/mattes; not precision geometry |
| visual cache | PROVEN CURRENT RUNTIME | separates expensive capture from cheap music assembly | V2 final cache/assembly integration |
| Scene Editor | PROVEN CURRENT RUNTIME | edits/saves recipes and three clocks | effect-atlas UI and final compositor preview |
| TransitionRecipe | schema/test proven; one type only | persistent projectile-bridge metadata | render consumer and remaining transition types |
| Pandora schemas | strong in-memory/test foundation | domain tiers, provenance, OFF/SUBTLE/HERO | persistence, pack application, runtime compiler |
| post compositor | NOT PRESENT | — | mattes, depth, flow, tracking, multi-pass assembly |
| model/animation pipeline | researched, asset work not present | MD3 replacement path understood | authored assets, QA, optional engine rebase |

### Architectural recommendation

Do not expand `SceneRecipeV2` for every experimental parameter. Preserve it as
WHAT/WHEN identity. Add separately versioned effect-atlas intent and resolved
execution records that reference `recipe_id`, evidence IDs, Pandora pack IDs,
and TransitionRecipe IDs. This prevents every atlas edit from invalidating
unrelated identities and preserves the existing visual-capture/music-assembly
cache split.

## 12. Top 20 WOW effects

Scores are 1–5 for **impact / feasibility / originality / Quake readability**.
The order favors total score but penalizes prerequisites that cannot be proven.

| Rank | Effect | I/F/O/Q | Why it belongs |
|---:|---|---|---|
| 1 | Projectile Bridge | 5/4/5/5 | pure Quake causality; foundation already exists |
| 2 | Teleporter World Pass | 5/3/5/5 | diegetic world change with unmistakable Quake grammar |
| 3 | 1vX Geometry Strip-Away | 5/2/5/5 | transforms tactics into cinema without losing truth |
| 4 | Killer Match Freeze | 5/3/4/5 | strong film grammar anchored to real kill evidence |
| 5 | Rocket-Jump Phrase Montage | 4/4/5/5 | turns movement heritage into musical vocabulary |
| 6 | World Forging Reveal | 5/2/5/5 | defines PANTHEON's creative ceiling |
| 7 | Last-Heart World | 4/3/5/5 | game state drives materials and sound |
| 8 | Threat-Miss Reveal | 4/3/5/5 | celebrates invisible defensive skill |
| 9 | LG Beam Bridge | 4/3/4/5 | continuous weapon behavior becomes transition logic |
| 10 | Door Geometry Match | 4/4/4/5 | cheap, elegant, map-native |
| 11 | Tactical Team Collapse | 5/2/5/5 | elevates coordinated rounds above isolated frags |
| 12 | Material Countdown Arena | 4/3/5/4 | embeds tension into actual world surfaces |
| 13 | Ad-Board Video Portal | 4/2/5/4 | map surface becomes editorial memory |
| 14 | Impact Event Lock | 4/4/3/5 | essential reusable punctuation |
| 15 | Velocity Signature Echo | 4/3/4/5 | makes movement readable without analysis UI |
| 16 | Death-as-Cut Family | 4/4/4/5 | turns an editorial problem into honest grammar |
| 17 | Player/Model Match Morph | 5/1/5/4 | spectacular but asset-heavy |
| 18 | Chat-in-World Echo | 4/2/5/4 | human texture tied to the real scene |
| 19 | Gib/Stone Reassembly | 5/1/4/4 | strong causal transition, heavy post/3D work |
| 20 | Grenade Football Control | 4/1/5/5 | unforgettable one-off Quake humor |

## 13. Top 5 prototype candidates after four canaries pass

These are prototype recommendations, not authorization to implement.

1. **Door Geometry Match** — validates motif descriptors and transition review
   with little engine risk.
2. **Impact Event Lock** — validates music-chosen legal rate, fixed event anchor,
   and safe `runfx` cue in one narrow effect.
3. **Projectile Bridge visual consumer** — completes the already-modeled
   TransitionRecipe path using speed-plausible evidence and a clean fallback.
4. **Rocket-Jump four-cut motif montage** — validates canonical-moment identity,
   distinct-occurrence search, musical subdivisions, and usage ledger.
5. **1vX Tactical Minimal** — count and result-aware tone only; proves the truth
   contract before geometry strip-away or silhouettes.

Prototype order is intentionally not identical to WOW rank. It maximizes what
the project learns per unit of risk and builds prerequisites for the later hero
effects.

## 14. Research lineage and source ledger

### Quake/arena editing

- ESR's moviemaking interview series: [wntt](https://www.esreality.com/?a=longpost&id=2919989&page=11),
  [entik](https://www.esreality.com/?a=longpost&id=2919989&page=13),
  [KOS](https://www.esreality.com/?a=longpost&id=2919989&page=26), and
  [santile](https://www.esreality.com/?a=longpost&id=2919989&page=5).
- ULBE lineage: [Das Ulbe community page](https://www.esreality.com/post/2112658/das-ulbe-frag-movie/)
  and [bogOtac interview](https://www.esreality.com/?a=longpost&id=2919989&page=4).
- Runtime/tool context: [WolfcamQL source README](https://github.com/brugal/wolfcamql/blob/master/README-wolfcam.txt)
  and [Q3MME project](https://sourceforge.net/projects/quake3mme/).

The extracted lineage is structural: music-first mapping, action primacy,
selective recams, event-local slow motion, coherent grade, and rare authored
surreal punctuation. No cut sequence, joke, grade, soundtrack, or signature
treatment from a specific work is to be copied.

### Film/VFX and compositing

- [Oklahoma State film editing chapter](https://open.library.okstate.edu/introfilmtv/part/editing/)
  and [Columbia film glossary: montage](https://filmglossary.ccnmtl.columbia.edu/term/montage/).
- [Adobe time remapping](https://helpx.adobe.com/after-effects/desktop/animate-in-after-effects/time-stretching-and-time-remapping/time-stretching-time-remapping.html),
  [motion tracking](https://helpx.adobe.com/uk/after-effects/desktop/animate-in-after-effects/track-motion/tracking-stabilizing-motion-cs5.html),
  and [Roto Brush/mattes](https://helpx.adobe.com/after-effects/desktop/roto-brush-and-refine-matte/roto-brush/roto-brush-refine-matte.html).
- [Blackmagic Fusion reference](https://documents.blackmagicdesign.com/UserManuals/FusionManual.pdf)
  for tracking, particles, 3D compositing, and optical flow.
- [Blender motion tracking manual](https://docs.blender.org/manual/en/5.2/movie_clip/tracking/introduction.html).
- [Foundry Project3D](https://learn.foundry.com/nuke/content/reference_guide/3d_nodes/project3d.html)
  and [CameraTracker](https://learn.foundry.com/nuke/9.0/content/reference_guide/3d_nodes/cameratracker.html).
- Beier and Neely, [Feature-Based Image Metamorphosis](https://doi.org/10.1145/142920.134003).
- Schödl et al., [Video Textures](https://dblp.org/rec/conf/siggraph/SchodlSSE00.html).
- [NVIDIA depth-derived motion blur](https://developer.nvidia.com/gpugems/gpugems3/part-iv-image-effects/chapter-27-motion-blur-post-processing-effect).

### User-supplied practice/resource leads

- [Creative COW](https://creativecow.net/) is useful for long-tail professional
  troubleshooting and expressions/plugin practice.
- [Video Copilot tutorials](https://www.videocopilot.net/tutorials/) provide
  accessible studies in 3D space, projection-like setups, energy, particles,
  destruction, and title design.
- [Motion Array learning library](https://motionarray.com/learn/after-effects/)
  and Envato Elements are taxonomy/reference libraries, not a design source.
- Cineversity/Maxon official motion-tracking material is useful for camera solve,
  calibration, object tracking, and C4D/AE handoff; see
  [Maxon Motion Tracker footage documentation](https://help.maxon.net/c4d/2026/en-us/Content/html/OMOTIONTRACKER-PH_GROUP_FOOTAGE.html).
- **EliteFX / Elite Directive** and the named **Moxie2D editing hub** remain
  user-supplied community leads. The public web index did not resolve stable,
  unambiguous primary pages for the exact resources on 2026-09-01, so this
  atlas does not invent links or attribute technical claims to them.

## 15. Repo evidence ledger

Primary local evidence for capability claims:

- `creative_suite/engine/scene_recipe.py`
- `creative_suite/engine/music_intelligence_v2.py`
- `creative_suite/engine/music_features_v2.py`
- `creative_suite/engine/cam10_writer.py`
- `creative_suite/engine/camera_compiler_v2.py`
- `creative_suite/engine/pantheon_scene.py`
- `creative_suite/engine/pantheon_runtime.py`
- `creative_suite/engine/director_preview.py`
- `creative_suite/engine/transition_recipe.py`
- `creative_suite/engine/pandora.py`
- `creative_suite/api/scene_editor.py`
- `creative_suite/frontend/scene-editor.js`
- `docs/reference/free_wins_proof.md`
- `docs/reference/pantheon_scene_canary_01.md`
- `docs/reference/pantheon_engine_synthesis.md`
- `docs/reference/projectile_evidence_reconciliation.md`
- `docs/reference/model_animation_path.md`
- `docs/reference/cinematic_fx_transitions_research.md`

This pass deliberately did not modify canary code, output staging, assets,
databases, or production render behavior.

---

## 6. User creative seeds — 2026-09-02

**Provenance:** `USER CREATIVE SEED`, stated by the director on 2026-09-02.
These are DESIGN entries. None is implemented, and appearing here never
promotes an idea to a capability. Each keeps the strict capability labels from
section 1. Where an entry needs numbers on screen, those numbers come from
engine truth or the entry is not built at all.

### TEAM — `TEAM_IDENTITY_MORPH`

- **Purpose:** make a coordinated team fight legible as a team fight.
- **Trigger:** verified team-round context with two or more confirmed
  teammates engaged.
- **Required evidence:** entity identities, team assignment, round context.
  Enemy team grouping must be confirmed by data or by
  `MANUAL_VERIFIED_TEAM_IDENTITY`; it is never inferred from colour or guess.
- **Visual:** the director's own model presentation (Xaero, CPM white
  fullbright in source) and teammates shift toward pTn/Nauru identity colours;
  the opposing coordinated team shifts toward its own treatment.
- **Camera:** any; the transformation is presentation-only.
- **Time:** transformation occupies real score time, typically 400–1200 ms.
- **Domain:** MODEL/ANIMATION plus shader remap. Not implemented.
- **OFF / SUBTLE / HERO:** source presentation / colour accent only / full
  identity treatment on both teams.
- **Cheap failure:** inventing an enemy team that the demo never established,
  or altering semantic player identity rather than presentation.

### TEAM — `POST_WIN_MODEL_REVEAL`

- **Purpose:** pay off a team round on the teammate, not only on the frag.
- **Trigger:** `ROUND_WIN` confirmed, with a teammate visible shortly after.
- **Required evidence:** round result truth, teammate entity visible in frame.
- **Visual:** the player turns to a teammate whose model or skin resolves into
  its transformed state.
- **Time:** fires only after the win is real; a pending round may not use it.
- **Domain:** MODEL/ANIMATION.
- **OFF / SUBTLE / HERO:** nothing / colour resolve / full model reveal.
- **Cheap failure:** firing on a round that was not actually won.

### GESTURE — `RHYTHMIC_IMAGE_STUTTER`

- **Purpose:** let a repeated musical figure drive the picture one-for-one.
- **Trigger:** a detected `MusicalGesture` (see `music_gesture.py`), optionally
  carrying a human tag such as `USER_TAGGED_TRUMPET`.
- **Required evidence:** the gesture's perceptual anchors and its exact
  inter-onset intervals.
- **Visual:** frame stutter, strobe, stepped repeats or held slices, one visual
  event per musical attack.
- **Audio/music:** pattern-level alignment. The figure's intervals are quoted
  exactly; only the pattern's start and a per-class bias move.
- **Time:** occupies the gesture's own span.
- **Domain:** POST/COMPOSITOR.
- **OFF / SUBTLE / HERO:** clean / two-frame holds / full stepped treatment.
- **Cheap failure:** aligning each hit independently, which destroys the
  rhythm that made the figure worth quoting.

### GESTURE — `MOSAIC_TILE_INTERPOLATION`

- **Purpose:** retime parts of the frame instead of all of it.
- **Trigger:** a gesture or sustained musical figure over a legible shot.
- **Required evidence:** for world-space segmentation, depth or geometry; for
  screen-space, none beyond the frame.
- **Visual:** the picture is divided into tiles or regions that freeze, lag,
  interpolate, reveal or advance at different times.
- **Design note:** two research paths, screen-space mosaic and depth-aware
  segmentation. `mme_saveDepth` is the existing lead for the second.
- **Domain:** POST/COMPOSITOR. Not implemented.
- **OFF / SUBTLE / HERO:** clean / few large regions / dense tiling.
- **Cheap failure:** tiling that hides the decisive action.

### SUPPORT — `MICRO_ACTION_ACCENT`

- **Purpose:** give small real actions small real punctuation.
- **Trigger:** gauntlet switch, single gauntlet hit, item or armour pickup,
  weapon swap.
- **Required evidence:** the corresponding semantic event.
- **Visual:** a brief texture flash, accent or step. Never hero treatment.
- **Domain:** SMALL IMPLEMENTATION.
- **OFF / SUBTLE / HERO:** nothing / accent / short flourish. HERO is
  deliberately mild here.
- **Cheap failure:** letting a pickup read as loudly as a frag.

### INFORMATION — `RAIL_COOLDOWN_TELEGRAPH`

- **Purpose:** explain why the player waits, dodges or repositions.
- **Trigger:** rail cooldown that materially shapes the next decision.
- **Required evidence:** weapon state and timing from engine truth.
- **Visual:** a restrained charge or recovery indication near the player.
- **Domain:** SMALL IMPLEMENTATION.
- **OFF / SUBTLE / HERO:** nothing / faint indication / explicit countdown.
- **Cheap failure:** turning the film into a HUD tutorial.

### INFORMATION — `DAMAGE_LEDGER_OVER_TARGET`

- **Purpose:** show that the finishing shot was not the whole story.
- **Trigger:** a scene where the director inflicted most of a target's damage.
- **Required evidence:** cumulative confirmed damage per target, target
  identity and lifetime, all from engine truth.
- **Visual:** a world-space ledger tracking the target.
- **Domain:** SMALL IMPLEMENTATION plus world-space text.
- **OFF / SUBTLE / HERO:** nothing / total at the end / running total.
- **Cheap failure:** any number that is not measured. Never estimate damage.

### INFORMATION — `ROUND_DAMAGE_COUNTER`

- **Purpose:** carry a round's story as a number.
- **Design variants, deliberately both kept:** RUNNING, counting up from zero
  through the round; or PREVIEW, revealing the eventual total as a teaser.
- **Required evidence:** per-round damage truth.
- **Domain:** SMALL IMPLEMENTATION.
- **Cheap failure:** choosing between the two variants silently.

### STRUCTURE — `LONG_ROUND_COMPRESSION`

- **Purpose:** keep a long won round's story without its dead time.
- **Trigger:** a long round with a confirmed win.
- **Grammar:** context, then meaningful movement, then damage, then positional
  outplay, then the kill, then the win treatment.
- **Required evidence:** round timeline, damage events, result.
- **Domain:** SMALL IMPLEMENTATION at the planner level.
- **Cheap failure:** arbitrary jump-cutting. This is semantic compression, and
  each cut must correspond to a real beat of the round.

### GAG — `DANGER_CROSS_SIGN`

- **Purpose:** rare comedic punctuation before an obviously bad dive.
- **Trigger:** a dive into clearly unfavourable odds that the player wins.
- **Visual:** brief freeze, the player makes a cross or refusal gesture, return
  to first person, the enemy misses, the kill lands.
- **Domain:** MODEL/ANIMATION. Needs authored animation; not implemented.
- **OFF / SUBTLE / HERO:** nothing / pause only / full gesture.
- **Cheap failure:** using it often enough to stop being funny.

### TRANSITION — `STRAFE_JUMP_AUDIO_MATCH`

- **Purpose:** bridge two scenes on a matched movement sound.
- **Trigger:** repeated strafe jumps or landings either side of a cut.
- **Required evidence:** movement event truth, delivered game audio, music
  rhythm.
- **Purpose tag:** `MOTION_CONTINUITY`.
- **Domain:** SMALL IMPLEMENTATION.
- **Cheap failure:** matching on audio alone when the movements do not read as
  continuous.

### TRANSITION — `POST_HERO_DEATH_REWIND_BRIDGE`

- **Purpose:** stop a death shortly after a great frag from wasting the frag.
- **Trigger:** an excellent frag followed within roughly one second by the
  director's own death.
- **Visual:** freeze on the death and use the explosion or death state as the
  transition into another scene with a similar death, pose or camera vector.
- **Required evidence:** both deaths, with their real outcomes.
- **Domain:** POST/COMPOSITOR plus transition planning.
- **Cheap failure:** presenting the source scene as a survival when it was not.

### DODGE — `ROCKET_FLYBY_AUDIO_ANCHOR`

- **Purpose:** make a near miss felt.
- **Trigger:** a projectile passing close to the player or camera.
- **Required evidence:** projectile geometry first -- closest approach,
  distance, velocity -- with game audio as presentation evidence, never as the
  detector.
- **Uses:** dodge emphasis, slow motion, picture-in-picture, projectile follow,
  transition.
- **Domain:** SMALL IMPLEMENTATION.
- **Cheap failure:** finding the flyby in the mix rather than in the demo.

### REVEAL — `WALL_REMOVAL_XRAY`

- **Purpose:** show skill that geometry hid.
- **Trigger:** a shot or kill obscured by a wall.
- **Visual:** the wall is removed, ghosted, wireframed or x-rayed; the action
  replays; the wall rebuilds.
- **Domain:** ENGINE/FORK RESEARCH.
- **OFF / SUBTLE / HERO:** nothing / ghosted wall / full removal and replay.
- **Cheap failure:** revealing geometry the player could not have known about
  and implying they did.

### INFORMATION — `DIEGETIC_SCOREBOARD_SURFACE`

- **Purpose:** show state without turning the HUD back on.
- **Trigger:** a moment where score or round state carries meaning.
- **Visual:** real values rendered into an in-world surface -- an advertisement
  board, a screen, a monitor.
- **Required evidence:** engine truth for every value shown.
- **Domain:** ENGINE/FORK RESEARCH plus material work.
- **Cheap failure:** permanently exposing the ordinary HUD scoreboard.

### TEAM — `ASSISTED_ROUND_FINISH`

- **Purpose:** keep rounds where the director did the work and a teammate
  finished.
- **Grammar:** the director's meaningful action, a brief cut or
  picture-in-picture to the teammate's frag, then the win payoff.
- **Required evidence:** who actually got the final frag.
- **Domain:** SMALL IMPLEMENTATION.
- **Cheap failure:** implying the director got the kill.

### MOVEMENT — `MOVEMENT_TECH_PUNCTUATION`

- **Purpose:** treat exceptional movement as content.
- **Trigger:** double jump off a pad, jump-pad rocket jump, plasma climb,
  grenade jump, exceptional rocket jump, high-speed traversal.
- **Uses:** build sections, transitions, rhythm, spectacle.
- **Domain:** SMALL IMPLEMENTATION.
- **Cheap failure:** treating routine movement as exceptional.

### READ — `NOPE_RETREAT`

- **Purpose:** show the decision not to fight as a skill.
- **Trigger:** the player reads bad odds -- cooldown, grouped enemies -- and
  retreats.
- **Visual:** a brief pause, a refusal cue, then the retreat.
- **Inversion:** the same read followed by diving anyway and winning becomes
  HERO or SPECTACLE rather than comedy.
- **Domain:** SMALL IMPLEMENTATION plus optional animation.
- **Cheap failure:** presenting a retreat that was not a read.

### TIME — `SPEED_SCALED_RETIME_ENVELOPE`

- **Purpose:** let genuinely fast action earn deeper slow motion.
- **Rule:** relative movement speed widens the visually acceptable retime
  ENVELOPE. It never chooses the rate. Music still selects an exact musically
  valid rate inside that envelope.
- **Required evidence:** attacker and victim speeds from the demo.
- **Domain:** implemented as an envelope in `opportunity_graph.py`; the
  planner consumes it.
- **Cheap failure:** computing the slow rate from speed directly, which
  decouples the picture from the score.

### TEAM — `DAMAGE_CHASE_TO_TEAMMATE_KILL`

- **Purpose:** follow the director's damage to its real conclusion.
- **Trigger:** heavy damage dealt, the enemy flees, a teammate finishes.
- **Visual:** pause, switch or picture-in-picture to the victim's perspective,
  the death, then the round result. The damage ledger makes the contribution
  clear.
- **Domain:** SMALL IMPLEMENTATION.
- **Cheap failure:** crediting the frag to the wrong player.

### OPTIONAL — `LAG_GLITCH_STYLIZATION`

- **Purpose:** occasional humour from visible enemy lag or teleporting.
- **Priority:** LOW and optional.
- **Domain:** POST/COMPOSITOR.
- **Cheap failure:** distorting clean gameplay to manufacture a meme.

---

## 7. External inspiration — `MUSIC_GESTURE_EFFECT_INSPIRATION`

The Prince Karma, "Later Bitches"
(`https://www.youtube.com/watch?v=wP8FUeu3eUE`), cited by the director on
2026-09-02 for its repeated trumpet-like figure and the idea of each attack
driving one visual step.

This is an EXTERNAL CREATIVE REFERENCE only. The track has **not** been
analysed locally, is not in the library, and must not be downloaded. Nothing
in PANTHEON may claim measurements of it. What transfers is the concept, and
the concept is already implemented as a general mechanism in
`music_gesture.py`: any repeated figure with regular spacing can be detected,
optionally tagged by a human, and answered one-for-one by a visual response
pattern whose intervals quote the music exactly.

If the director later supplies a lawful local copy, it becomes an ordinary
library track and the same detector applies to it with no special casing.
