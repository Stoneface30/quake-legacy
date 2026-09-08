# Movement, jump and animation: action-to-code reference

This document maps an observed action to protocol state, parser support and client presentation.
All sample identities are aliases; P02 is the primary recorded POV.
Times below are absolute demo server milliseconds, not video timestamps.

## What the evidence can establish

Three layers must stay separate:

- **Source:** the local canonical WolfcamQL tree identifies itself as 12.7test49.
- **Runtime:** the configured capture installation is 11.3; source line references do not prove binary equivalence.
- **Sample:** `evidence.json` is the sanitized demo509 observation set. It contains positions, scalar speed, health, armor and selected events.

The local `game/g_*` and shared `bg_*` mechanics below are explanatory reference implementations.
They are **not** a claim to possess the proprietary historical Quake Live server implementation.
Exact historical movement constants, damage rules and mod settings require matching server evidence.
No new capture or production-code change was made for this reference.

The sanitized snapshot schema omits velocity components, grounded state, movement flags, input commands and animation IDs.
Consequently it can show an ascent or speed change, but cannot alone prove a jump button, crouch, landing, knockback or strafe input.
The parser has some richer fields than this export; the distinctions below matter.

## Protocol and parser field map

Protocol 73 uses the `playerStateFieldsQ3` table in this client, not the extended protocol 90/91 tables.
The selection is explicit in [MSG_ReadDeltaPlayerstate](/mnt/g/quake_legacy/engine/engines/_canonical/code/qcommon/msg.c:2986).
Indices below are zero-based netfield positions, not byte offsets into the demo.

| Meaning | Protocol-73 playerstate fields | Parser/export status |
|---|---|---|
| Position | origin X/Y/Z at 1/2/9 | Parser exports origin; sanitized evidence exports x/y/z |
| Velocity | velocity X/Y/Z at 4/5/10 | Parser exports components; evidence retains only 3D magnitude `speed` |
| Ground contact | groundEntityNum at 20, 10 bits; 1023 means ENTITYNUM_NONE | Parser exports nullable `airborne`; evidence omits it |
| Crouch / control timers | pm_flags at 19, 16 bits; pm_time at 12 | Read in internal delta state, not returned as public snapshot fields |
| Directional pose | movementDir at 15, 4 bits | Not returned by parser snapshot export |
| Animation | torsoAnim at 14; legsAnim at 17; both 8 bits | Not returned by parser snapshot export |
| View height | viewheight at 28, signed 8 bits | Not returned by parser snapshot export |
| Predictable events | eventSequence 13; events at 16/18; parms at 38/39 | Sequence-edge detection; captured events include jump and jump_pad |
| Pad association | jumppad_ent at 46, 10 bits | Not returned by parser snapshot export |

Source: [protocol table](/mnt/g/quake_legacy/engine/engines/_canonical/code/qcommon/msg.c:2244),
[parser field constants](/mnt/g/quake_legacy/engine/parser/demo_parse.py:165),
[delta-state/event handling](/mnt/g/quake_legacy/engine/parser/demo_parse.py:1038),
[public snapshot output](/mnt/g/quake_legacy/engine/parser/demo_parse.py:1074).

For other visible players, entity position uses `pos.trBase`, velocity uses `pos.trDelta`,
and contact uses `groundEntityNum`. The parser records changed player entities with these fields.
It does not publish legsAnim or angles2 movement direction in that track.
See [entity extraction](/mnt/g/quake_legacy/engine/parser/demo_parse.py:882).
These tracks are not a promise of one independent update for every player on every frame.

Raw attached events carry toggle bits `0x100` and `0x200`; their normalized code is `event & ~0x300`.
Temporary entities carry an event in eType; the parser has a separate normalization path.
Do not discard toggle bits before repeated-event deduplication.
See [event bits](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/bg_public.h:784)
and [parser event normalization](/mnt/g/quake_legacy/engine/parser/demo_parse.py:903).

## Normal jump: an event, not simply upward motion

**Mechanic:** local `PM_CheckJump` checks upmove, respawn and jump-held flags,
clears ground contact, sets vertical velocity to JUMP_VELOCITY, emits EV_JUMP,
and selects forward/backward jump legs animation.
The local constant is 270 units/s; it is not a measured demo509 launch constant.
Sources: [PM_CheckJump](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/bg_pmove.c:365),
[JUMP_VELOCITY](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/bg_local.h:32).

**Wire:** EV_JUMP = **10**, through playerstate events for the recorded POV or attached entity events for another player.
The parser captures it as `jump`; it does not record the original held key duration.
Sources: [event ID](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/bg_public.h:803),
[capture whitelist](/mnt/g/quake_legacy/engine/parser/demo_parse.py:94).

**Presentation:** `CG_EntityEvent` plays `*jump1.wav`, records jumpTime and jump-speed history.
The legs animation is a separate replicated state field, not a sound-to-animation inference.
Source: [jump event presentation](/mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_event.c:2026).

**Observed P02 example:** E01045, round 1, playerstate code 10 at **61300 ms**, parm 0.

| Snapshot ms | Position x, y, z | 3D speed | Health / armor |
|---|---|---:|---:|
| 61275 | 667.13, 1751.06, 925.26 | 501.40 | 161 / 17 |
| 61300 | 666.06, 1750.94, 937.76 | 274.61 | 161 / 17 |
| 61325 | 664.93, 1750.74, 943.51 | 258.33 | 161 / 17 |

This proves an emitted jump event and neighboring upward position changes.
It does not prove a 270-unit sampled vertical velocity: `speed` includes all three axes,
and server-event timing need not equal the exact physical launch instant.
Sample source: [sanitized evidence](/mnt/g/quake_legacy/docs/reference/demo509/evidence.json), event_id E01045.

## Jump pad: distinct cause and distinct event

**Mechanic:** local `BG_TouchJumpPad` copies pad `origin2` into player velocity.
It remembers the pad entity to suppress repeated trigger sound and emits EV_JUMP_PAD = **9**.
Its local parm 0/1 classification derives from pad launch angle; do not treat parm as pad identity.
Source: [BG_TouchJumpPad](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/bg_misc.c:6397).

**Parser:** captures `jump_pad` independently of `jump`.
A pad can propel a player without a jump-button action.
**Presentation:** custom jumpPad effect script, or smoke puff plus pad sound;
then the player's jump voice sound. Hearing a jump voice alone cannot distinguish the two actions.
Source: [pad presentation](/mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_event.c:1991).

**Observed P02 example:** E01015, round 1, playerstate code 9 at **60500 ms**, parm 0.

| Snapshot ms | Position x, y, z | 3D speed | Health / armor |
|---|---|---:|---:|
| 60475 | 687.21, 1857.75, 280.12 | 329.66 | 161 / 17 |
| 60500 | 686.26, 1854.60, 295.89 | 1121.89 | 161 / 17 |
| 60525 | 686.26, 1853.41, 320.36 | 1104.65 | 161 / 17 |

The explicit pad event is the cause evidence; the speed increase and ascent are corroboration.
Sample source: [sanitized evidence](/mnt/g/quake_legacy/docs/reference/demo509/evidence.json), event_id E01015.

## Falling, landing and stepping are different transitions

**Falling:** local `PM_GroundTraceMissed` sets groundEntityNum to NONE;
it can force LEGS_JUMP/JUMPB when a sufficiently deep drop lies below.
It does **not** emit EV_JUMP in that path.
Source: [walk-off/freefall path](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/bg_pmove.c:1084).
Thus a jump animation is not proof of a jump button or even an EV_JUMP event.
A negative vertical velocity while airborne would establish descent, not its cause.
Evidence.json lacks both fields, so this document does not assign a verified fall interval.

**Landing:** local `PM_CrashLand` chooses LEGS_LAND/LANDB and sets legsTimer,
then computes impact severity from the prior velocity, displacement and gravity.
Water, crouching and SURF_NODAMAGE alter event selection.
The event IDs are EV_FALL_SHORT **6**, MEDIUM **7**, FAR **8**;
these describe the landing impact, not the whole airborne interval.
Source: [landing mechanic](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/bg_pmove.c:939).

The local server reference applies medium/far falling damage 5/10 unless disabled,
with MOD_FALLING **19**; these numbers are not established historical QL match settings.
Source: [ClientEvents falling damage](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/g_active.c:576).
Client presentation is landSound / pain100 voice / fall1 voice plus view landChange -8/-16/-24.
Source: [landing sounds and view offsets](/mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_event.c:1889).

**Coverage gap:** parser `_CAPTURE_EVENTS` omits 6/7/8 and footstep events.
Absence in evidence.json therefore says nothing about whether landings happened.
A parser-based landing audit needs ground-contact transitions or retention of these raw events.
Source: [capture whitelist](/mnt/g/quake_legacy/engine/parser/demo_parse.py:94).

**Stepping:** EV_STEP_4 through EV_STEP_24 are local enum **196–201**.
They drive step smoothing; the client explicitly skips that smoothing branch during demo playback.
Do not confuse these with raw QL landing events or ordinary jump actions.
Sources: [step enum](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/bg_public.h:914),
[step handler/demo bypass](/mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_event.c:1938).

## Knockback: velocity change does not identify the force

The local `G_Damage` reference adds direction-scaled momentum to velocity,
sets a bounded pm_time and PMF_TIME_KNOCKBACK (**64**) when appropriate.
Knockback can occur even when later protection prevents health damage.
Sources: [momentum application](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/g_combat.c:896),
[flag definitions](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/bg_public.h:468).

There is no universal EV_KNOCKBACK in this mapping.
Useful evidence would combine velocity components, pm_flags/time, impact events and damage state.
The current parser does not export that timer/flag combination, and the sanitized evidence lacks velocity vectors.
A simultaneous hit and acceleration is a candidate association, not a verified impulse attribution.

Local ground handling can force jump animation when positive velocity throws the player off a surface.
Source: [kickoff branch](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/bg_pmove.c:1147).
Consequently LEGS_JUMP can mean normal jump, walk-off pose or knockback pose.
No demo509 sample is labeled verified rocket-jump or knockback from scalar speed alone.

## Crouch, walk, run and strafe

**Crouch:** PMF_DUCKED = **1**; local `PM_CheckDuck` sets it for negative upmove,
but standing is blocked if a full-height collision trace remains solid.
Thus crouch state itself does not prove the crouch key is still held.
Viewheight and bounds change; crouched idle/walk use distinct legs animations.
Sources: [crouch flag](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/bg_public.h:463),
[crouch mechanic](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/bg_pmove.c:1264).

**Walk/run:** `PM_Footsteps` chooses LEGS_WALK versus LEGS_RUN using BUTTON_WALKING,
with backward and crouched variants. Crouched movement suppresses ordinary footsteps;
running emits surface footsteps on bob-cycle boundaries.
A small measured speed is not sufficient to establish walking input.
Source: [gait and sound selection](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/bg_pmove.c:1375).

**Strafe:** local movementDir encodes 0 forward, 1 forward-left, 2 left, 3 back-left,
4 back, 5 back-right, 6 right, 7 forward-right.
With no movement input, pure side codes can relax to diagonals for presentation.
The shared state converter places movementDir into entity angles2[YAW].
Sources: [direction assignment](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/bg_pmove.c:328),
[state conversion](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/bg_misc.c:6468).
Air/ground acceleration use forward/right command components and view axes:
[PM_AirMove](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/bg_pmove.c:609),
[PM_WalkMove](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/bg_pmove.c:700).
Neither a curved trajectory nor high speed establishes a specific held key sequence or optimal strafe technique.
No verified crouch/walk/strafe interval is available in the sanitized export.

## Animation-to-render chain

Base animation IDs from the local enum: WALKCR **13**, WALK **14**, RUN **15**, BACK **16**,
SWIM **17**, JUMP **18**, LAND **19**, JUMPB **20**, LANDB **21**, IDLE **22**, IDLECR **23**.
Strip ANIM_TOGGLEBIT (**128**) when identifying the base animation;
the toggle enables restarting the same animation.
Sources: [animation enum](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/bg_public.h:1194),
[toggle bit](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/bg_public.h:1263).

`CG_PlayerAnimation` consumes replicated legsAnim/torsoAnim; `CG_RunLerpFrame`
chooses model frames and interpolation. `CG_PlayerAngles` rotates legs/torso from movementDir
and leans the model using velocity. These are visual pose effects, not new server physics.
Sources: [frame interpolation](/mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_players.c:2183),
[animation selection](/mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_players.c:2265),
[pose calculation](/mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_players.c:2433).

`CG_Player` calls the angle/animation functions, builds body-part render entities,
and submits legs/torso/head with model skins and powerup effects.
Sources: [animation into render frames](/mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_players.c:6924),
[legs submission](/mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_players.c:7085).
Model animation.cfg, renderer settings, effects scripts and runtime version can change what is seen.
This source trace explains the intended presentation path; it is not a frame-by-frame runtime capture verification.
