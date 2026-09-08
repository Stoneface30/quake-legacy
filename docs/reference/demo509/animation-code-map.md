# Animation and visible-action code map

Scope: locally available canonical engine source, inspected 2026-09-07.
This tree is newer than the recording. It explains this playback implementation, not the exact historical Quake Live server build.
Animation constants and frame counts below must not be substituted for a protocol-specific capture-era schema.
No render was run for this reference; code paths describe possible behavior, not observed frames.

## The complete chain

`delta snapshot → reconstructed state → snapshot selection → position/angle interpolation → animation state → model frames/tags → scene → pixels`

A parallel branch is `event/state → sound, particles, lights, marks, HUD`.
The animation branch is not the complete visual-event branch.

| Stage | Source anchor | What it establishes |
|---|---|---|
| Wire reconstruction | [msg.c:1944][delta-es], [msg.c:2949][delta-ps] | Delta readers reconstruct entity/player state against prior state. Field tables vary by protocol. |
| Animation fields | [msg.c:963][wire-anim] | Example entity table carries torso/legs animation values as eight-bit fields; verify selected table before decoding a recording. |
| Snapshot advancement | [cg_snapshot.c:185][transition], [cg_snapshot.c:1661][process] | Current and next snapshots provide state and server-time context. |
| Discontinuity handling | [cg_snapshot.c:546][tele-interp] | Invalid prior entity or changed teleport flag disables interpolation. |
| Interpolation fraction | [cg_ents.c:3427][packets] | Uses next/current server-time delta and fractional `cg.ftime`; zero delta has a guard. |
| Entity transform | [cg_ents.c:2648][interpolate], [cg_ents.c:2725][calc] | Evaluate trajectories, blend positions and wrapped angles, or use alternate Wolfcam interpolation. |
| Motion basis | [bg_misc.c:6026][trajectory] | Trajectory evaluation is distinct from model animation. |
| Body animation | [cg_players.c:2265][player-anim] | Separate legs and torso lerp states supply old frame, frame and backlerp. |
| Body assembly | [cg_players.c:6927][body], [cg_players.c:7129][torso-tag], [cg_players.c:7435][head-tag] | Build model parts, attach torso/head using interpolated model tags. |
| Scene submission | [cg_syscalls.c:269][submit], [cg_draw.c:11211][scene] | Ref entities enter scene; rendering consumes the final view definition. |

## State is not a frame number

`legsAnim` and `torsoAnim` identify animation sequences plus a restart toggle.
The local definition is `ANIM_TOGGLEBIT = 128`: [bg_public.h:1263][toggle].
[PM_StartTorsoAnim / PM_StartLegsAnim][start-anim] flip that bit when starting a sequence.
The continuation helpers compare the sequence with the toggle removed before deciding whether to restart.
Thus the same base sequence with a changed toggle can mean a new animation start; stripping the bit permanently loses evidence.

[CG_SetLerpFrameAnimation][set-anim] retains the raw number, masks the toggle for the animation-table lookup, then schedules the initial lerp.
[CG_RunLerpFrame][run-anim] detects raw animation changes and advances old/current model frames against its supplied time.
The preceding `CG_SetAnimFrame` handles `firstFrame`, duration, looping, reversal and flip-flop behavior.
`backlerp = 1 - (time - oldFrameTime)/(frameTime - oldFrameTime)` when those frame times differ.
This weights the old model frame; it is a separate interpolation from the entity's world position.

[CG_ParseAnimationFile][anim-file] reads the model's `animation.cfg`.
Its parsing at [cg_players.c:235][anim-fields] interprets first frame, number of frames, loop count and FPS, including legs-frame adjustment.
FPS determines `frameLerp` and `initialLerp`; identical sequence IDs need not imply identical mesh frames across models.
[Model registration][models] loads lower, upper and head MD3s and resolves animation.cfg paths.
Model tags interpolate through [CG_PositionEntityOnTag][tags] and the renderer's tag syscall.
Skins, shaders and powerup rendering add appearance beyond geometry: [CG_AddRefEntityWithPowerups][powerups].

## Which actions select sequences?

| Action family | Local implementation | Recognition limit |
|---|---|---|
| Idle, crouch, swim, walk, run, backwards locomotion | [PM_Footsteps][footsteps] chooses legs sequences from movement state. | Run animation does not establish a precise world speed or a footstep sound at every visible step. |
| Weapon drop / raise / attack | [bg_pmove.c:1500][weapon-state] onward selects torso states; weapon processing begins at 1553. | An attack pose alone does not prove a projectile hit or damage. |
| Turn in place | [CG_PlayerAnimation][player-anim] can substitute `LEGS_TURN` for idle while yawing. | Visible turning can be client-generated rather than a new transmitted legs sequence. |
| Aim and body orientation | [CG_PlayerAngles][angles] derives legs/torso/head axes. | Torso twist and head orientation depend on movement/yaw state, not only animation ID. |
| Teleport or reappearance | [Snapshot interpolation guard][tele-interp] plus [teleport event handling][tele-events]. | A discontinuous transform and a spawned effect are separate pieces of evidence. |

These are mappings in this local tree, not assertions that a particular action occurred in the sample.

## First person, third person, and weapons

[CG_Player][body] fills separate legs/torso frame tuples.
The preceding visibility logic at [cg_players.c:6915][visibility] applies `RF_THIRD_PERSON` to the relevant viewed-player body: the comment specifies mirror-only drawing.
Third-person/free-camera/follow settings change which body and weapon path is visible; record the actual camera mode.
The world weapon attaches via [CG_AddPlayerWeapon call][world-gun] after body assembly.

[CG_AddViewWeapon][view-gun] builds the first-person weapon path, with view-mode and weapon-display guards.
At [cg_weapons.c:2852][gun-frames], a debug gun-frame override can replace normal animation.
Otherwise old/current hand frames come from [CG_MapTorsoToWeaponFrame][gun-map] and reuse torso backlerp.
That mapping translates selected torso drop/attack frame ranges into weapon frames; it is not a second wire-level weapon-animation stream.
[CG_FireWeapon][fire] separately handles firing presentation; the event dispatch begins at [cg_event.c:2302][fire-event].
Muzzle flash, looping weapon effects, projectile trails, impacts, marks and sound need their own event/state evidence.
A visible muzzle flash and an attack pose can be related without having identical lifetimes or a one-to-one count.

## Prediction, demo timing, and seeking

[CG_PredictPlayerState demo branch][prediction] calls `CG_InterpolatePlayerState(qfalse)` for demo playback or follow mode.
Do not describe this branch as rerunning the original player's local input prediction.
The live prediction path and recorded playerstate interpolation are different sources of the displayed pose.
[BG_PlayerStateToEntityState assignments][ps-es] copy legs/torso animation fields into the entity representation.
[CG_AddPacketEntities][packets] constructs the predicted-player entity from playerstate and also visits snapshot entities.

The standard interpolation path evaluates current/next positions at their respective snapshot server times and uses `LerpAngle` for orientation.
Other trajectories can be evaluated at playback time and adjusted for movers: [CG_CalcEntityLerpPositions][calc].
Wolfcam can substitute [Wolfcam_InterpolateEntityPosition][wolf-interp] when original interpolation is disabled.
It assigns entity-specific `cgtime` using snapshot offsets at [wolfcam_ents.c:710][entity-time].
[CG_PlayerAnimation][player-anim] passes that entity time to its lerp-frame machinery.
Seeking also has explicit animation reconstruction using stored start times: [cg_snapshot.c:1146][seek].
Consequently server event time, snapshot time, playback time, entity animation time and output-video time must remain separate columns.
Do not infer animation phase from `server_time_ms` alone, or interpolate across teleport, missing-state, seek or entity-reuse boundaries.

## Effects outside legsAnim / torsoAnim

| Family | Source anchor | Additional evidence needed |
|---|---|---|
| Teleport in/out | [cg_event.c:2449][tele-events] | Event position, sound, spawn effect or configured effect script; transform discontinuity independently. |
| Item pickup | [cg_event.c:2125][pickup] | Item/event parameter, pickup sound and local HUD behavior; not a body sequence. |
| Item pop / respawn | [cg_event.c:2478][respawn] | Item model identity and `miscTime` scale-up; do not confuse item respawn with player respawn. |
| Jump pad / footsteps | [cg_event.c:1991][jump-pad], [PM_Footsteps][footsteps] | Event/surface/movement context; sounds and particles may be independent of mesh phase. |
| General world sound | [cg_event.c:2913][sound] | Sound index/configuration and emitting entity rather than an animation sequence. |
| Persistent marks / local effects | [cg_view.c:6257][marks], [cg_view.c:6462][local-fx] | Local-entity lifetime, shader and renderer time; an effect can outlive its source event. |
| Player powerups | [cg_players.c:2996][player-powerups] | Powerup bits and rendering configuration; geometry animation alone is insufficient. |

[CG_CheckEvents][check-events] is the separate event dispatch boundary; its event deduplication is not an animation restart detector.
A player reappearing should be classified from lifecycle/teleport/state evidence, not from an item-respawn label.

## What the Python parser exports and omits

[demo_parse.py:882][parser-entities] exports selected player-entity samples: timestamp, entity/client slots, position, velocity, yaw/pitch, weapon and ground/airborne fields.
These positions are `pos.trBase` selections, not the renderer's evaluated and interpolated `lerpOrigin`.
[demo_parse.py:1074][parser-ps] exports followed-player position/velocity, aim, weapon, speed, health and armor.
[Optional missile samples][parser-missiles] retain additional missile state but still do not describe rendered geometry.
The delta reader [demo_parse.py:1093][parser-delta] reads numeric field-index values; exported records are a narrower projection.
Neither player projection exports raw legs/torso animation IDs, their toggle histories, model frame tuples or backlerp.
They also omit the full trajectory timing/type, full angular trajectory, model/skin resolution, render flags and animation-start reconstruction needed for pose replay.
“No exported animation field” means unavailable to the current analysis output, not absent from the demo protocol.
Missing fields, sparse/delta-only entity sampling and baseline reconstruction must be audited before claiming continuous visibility or exact animation coverage.

## Reusable recognition and evidence contract

For each candidate action, preserve an anonymized entity slot plus lifecycle segment, protocol/table identity and source snapshot/message identifiers.
Retain raw animation values and their base/toggle decomposition for both torso and legs, including unchanged-state reconstruction and explicit unknowns.
Keep surrounding snapshots, full position/angular trajectories, eFlags, weapon, event sequence/payload and playerstate-versus-entity provenance.
Store independent times: server event, snapshot bracket, playback/cgtime, animation start and video frame mapping with uncertainty.
For a visual claim, record camera mode, engine revision/binary hash, asset pack/model/animation.cfg hashes and relevant interpolation/render/effect cvars.
Record derived old/current frames and backlerp only when actually evaluated; do not manufacture these from an exported weapon or movement label.
Separate conclusions into **wire observation**, **code-supported interpretation**, and **render-confirmed appearance**.
A recognition rule should name required fields, restart handling, discontinuity exclusions, missing-data behavior and corroborating events.
Use pose plus movement/event context for semantic labels; reserve hits, damage and kills for their own supporting evidence.
No single visual proves a unique event, and no single event guarantees an invariant image across code, assets, settings and camera modes.

[delta-es]: /mnt/g/quake_legacy/engine/engines/_canonical/code/qcommon/msg.c:1944
[delta-ps]: /mnt/g/quake_legacy/engine/engines/_canonical/code/qcommon/msg.c:2949
[wire-anim]: /mnt/g/quake_legacy/engine/engines/_canonical/code/qcommon/msg.c:963
[transition]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_snapshot.c:185
[process]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_snapshot.c:1661
[tele-interp]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_snapshot.c:546
[packets]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_ents.c:3427
[interpolate]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_ents.c:2648
[calc]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_ents.c:2725
[trajectory]: /mnt/g/quake_legacy/engine/engines/_canonical/code/game/bg_misc.c:6026
[player-anim]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_players.c:2265
[body]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_players.c:6927
[torso-tag]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_players.c:7129
[head-tag]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_players.c:7435
[submit]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_syscalls.c:269
[scene]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_draw.c:11211
[toggle]: /mnt/g/quake_legacy/engine/engines/_canonical/code/game/bg_public.h:1263
[start-anim]: /mnt/g/quake_legacy/engine/engines/_canonical/code/game/bg_pmove.c:93
[set-anim]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_players.c:2107
[run-anim]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_players.c:2183
[anim-file]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_players.c:117
[anim-fields]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_players.c:235
[models]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_players.c:735
[tags]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_ents.c:111
[powerups]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_players.c:4245
[footsteps]: /mnt/g/quake_legacy/engine/engines/_canonical/code/game/bg_pmove.c:1337
[weapon-state]: /mnt/g/quake_legacy/engine/engines/_canonical/code/game/bg_pmove.c:1500
[angles]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_players.c:2433
[visibility]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_players.c:6915
[world-gun]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_players.c:7593
[view-gun]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_weapons.c:2772
[gun-frames]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_weapons.c:2852
[gun-map]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_weapons.c:1630
[fire]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_weapons.c:3159
[fire-event]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_event.c:2302
[prediction]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_predict.c:495
[ps-es]: /mnt/g/quake_legacy/engine/engines/_canonical/code/game/bg_misc.c:6469
[wolf-interp]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/wolfcam_ents.c:204
[entity-time]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/wolfcam_ents.c:710
[seek]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_snapshot.c:1146
[tele-events]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_event.c:2449
[pickup]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_event.c:2125
[respawn]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_event.c:2478
[jump-pad]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_event.c:1991
[sound]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_event.c:2913
[marks]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_view.c:6257
[local-fx]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_view.c:6462
[player-powerups]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_players.c:2996
[check-events]: /mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_event.c:4124
[parser-entities]: /mnt/g/quake_legacy/engine/parser/demo_parse.py:882
[parser-ps]: /mnt/g/quake_legacy/engine/parser/demo_parse.py:1074
[parser-missiles]: /mnt/g/quake_legacy/engine/parser/demo_parse.py:862
[parser-delta]: /mnt/g/quake_legacy/engine/parser/demo_parse.py:1093
