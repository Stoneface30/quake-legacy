# Teleports, POV visibility and reconstruction of missing action

The objective is to reconstruct a watchable complete action when a POV recording loses
projectiles or players. Recognition is the foundation; the reconstruction must distinguish
recovered recorded state, predicted motion, and synthesized cinematic material.

## Why a projectile can disappear while its kill remains

[SV_AddEntitiesVisibleFromPoint](/mnt/g/quake_legacy/engine/engines/_canonical/code/server/sv_snapshot.c:292)
builds a recipient-specific entity set. It considers client flags, connected map areas and
potentially visible clusters (PVS); broadcast entities take a separate route. This is not
simply a distance cutoff or the camera's screen rectangle. An object behind the camera can
still be transmitted, and one in another map region can be omitted.

The reference [death code](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/g_combat.c:513)
creates EV_OBITUARY and sets SVF_BROADCAST. This explains how a client can receive a lethal
outcome without receiving the projectile's full flight. This Q3-derived server source is an
implementation reference, not certification of every historical Quake Live server setting.

Distinguish four different losses:

| Situation | Can the original action be recovered? |
|---|---|
| Entity was recorded but our export discarded its fields | Re-decode and retain the original state. This is recovery, not invention. |
| Entity is in the reconstructed snapshot but playback hides it | Inspect camera, renderer, effect lifetime and visibility settings. Re-rendering may reveal it. |
| Entity leaves the recipient snapshot set but a previous trajectory exists | Predict only the supported continuation; unobserved interactions introduce uncertainty. |
| Neither launch nor projectile state is recorded; only obituary exists | The outcome is known, but the complete flight is underdetermined. A sequence can be synthesized, not claimed as recovered history. |

A field omitted by delta compression is inherited from its correct base; it is not a missing
entity. An entity removed from a recipient's snapshot is not necessarily destroyed on the
server. Entity numbers can be reused: track separate lifetimes rather than joining every
appearance with the same number.

Changing freecam, PVS or broadcast settings during playback cannot cause an old demo to gain
server updates that were never sent. A compatible second POV or server recording can add
real evidence, but requires clock alignment and matching entity lifetimes.

## Projectile reconstruction contract

Retain entity number and lifetime, weapon, trajectory type, trTime, trBase, trDelta,
trDuration, every observed state transition, relevant events, and any supported ownership
fields. An equipped weapon or a nearby fire event alone does not uniquely identify a missile.

[BG_EvaluateTrajectory](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/bg_misc.c:6026)
evaluates recorded trajectories. For a linear segment, p(t)=base+velocity·dt. A gravity
segment adds the corresponding vertical acceleration term. Use the actual protocol/runtime
parameters, not guessed constants. These equations describe a segment, not future collisions.

[G_RunMissile](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/g_missile.c:451)
traces motion; [G_MissileImpact](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/g_missile.c:273)
can change its outcome; [G_BounceMissile](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/g_missile.c:33)
changes trajectory; [G_ExplodeMissile](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/g_missile.c:70)
handles explosion. A grenade's missing bounces cannot be recovered by extending one parabola.

A matching BSP and physics implementation can constrain static-world collisions. Missing
players, movers, server rules, timing and interactions can still prevent exact simulation.
A kill time and MOD constrain a candidate; they do not uniquely determine launch position,
flight path, projectile identity or impact location. Splash allows the victim to be offset
from the explosion. Never draw a straight line to the victim and call it the recorded flight.

Reconstruction should preserve the original demo and use a separate overlay/sidecar:

1. Recover every available raw entity state before inventing any state.
2. Establish observed launch/flight segments and explicit observation-gap intervals.
3. Continue supported trajectories; stop or branch at uncertain collisions or lifetime bounds.
4. Match later observations and outcomes as constraints, retaining competing candidates.
5. Label each segment `recorded`, `predicted` or `synthesized`, with assumptions and evidence.
6. Render synthetic entities/effects separately so the creative director can accept or revise them.

Confidence is not a fabricated percentage. Store the conditions supporting a segment and what
would falsify it. A cinematic reconstruction can complete the visible story without pretending
that all its coordinates came from the historical recording.

## Teleport behavior

The reference [TeleportPlayer](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/g_misc.c:79)
emits separate temporary departure/arrival events, moves the player, optionally changes exit
velocity/view angles, toggles EF_TELEPORT_BIT, and handles destination occupancy. Its numerical
exit-speed/timer constants are reference values, not established historical match facts.

The [client snapshot transition](/mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_snapshot.c:546)
uses a changed teleport flag to prevent interpolation across the discontinuity. The correct
visual is a jump between locations, with applicable effects—not a fast movement line across
the map. Camera following, view orientation and motion after arrival must use the new state.

Protocol-73 events: teleport-in 39, teleport-out 40. Keep the entity's client association,
eFlags before/after, positions and timestamps. Do not pair the nearest in/out events solely
by time: simultaneous players and missing endpoints make that ambiguous. A discontinuity
alone can also involve respawn or POV changes and does not establish a map teleporter traversal.

In this sample the supported export contains **64 teleport-in and 5 teleport-out events**.
These counts do not establish 64 completed teleporter traversals. The first in-event is
E00004 at 30075 ms, position (1232,432,289); an out-event is E03947 at 162225 ms,
position (-1288,-899,186). They are examples, **not a paired traversal**. Both have null
encoded_client in the sanitized export, so that export cannot attribute them to a player.
Re-decode event entity fields before claiming identity or pairing.

A player teleport does not imply that their already-fired rocket or grenade teleports too.
Each projectile has its own lifetime and motion. Only matching game/mod behavior and evidence
can justify a projectile teleport. A later kill can belong to a projectile launched before
the player moved or teleported.

## Evidence needed before calling reconstruction validated

Use a fully observed flight as a held-out test: deliberately hide an interior interval, predict
without reading that interval, then compare against the concealed positions and events.
Include grenade bounces, visibility exits/re-entry, entity-number reuse, splash outcomes and
player teleports. Comparing a trajectory against its own fitting samples is not validation.

Report position/time residuals, event association errors and incorrectly bridged lifetimes.
Then test a genuine POV gap. Agreement with an obituary alone validates an outcome constraint,
not the unseen path. This chapter defines the reconstruction contract; it does not claim that
a missing flight in DEMO509 has already been reconstructed or rendered.
