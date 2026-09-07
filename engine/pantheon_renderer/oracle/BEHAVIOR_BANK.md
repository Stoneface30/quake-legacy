# Source-behaviour bank

What of the original engine's behaviour PANTHEON has actually *proved* it
reproduces, and what each proof required. The point is to stop rediscovering
Quake from scratch every time a new filmmaking idea needs it.

**Target authority:** WolfcamQL 11.3, local archive
`3051397d08f15ee9345f71c4eac35eaedc568ac2bf8b3ad3de3d9aa4349ee8dc`
(`WOLF WHISPERER/WolfcamQL/wolfcamql-src.tar.gz`).
12.7test49, Q3MME and QL protocol 90/91 are **separate** target versions and
must never be substituted silently — behaviour proved against 11.3 is a claim
about 11.3.

Source is quoted here only as provenance. Function bodies live in
`oracle_generated.c`, regenerated from the archive, never hand-edited, under
the original GPL-2.0 terms.

---

## PLAYER_ANGLES — head/torso/legs separation

| | |
|---|---|
| source | `cg_players.c :: CG_PlayerAngles` — `sha256:27381516f1439a48` |
| depends on | `CG_SwingAngles`, `CG_AddPainTwitch`, `AngleMod`, `AnglesToAxis`, `AngleSubtract` |
| state | per-actor swing (`legs.yawAngle/yawing`, `torso.yawAngle/yawing`, `torso.pitchAngle/pitching`) |
| inputs | view yaw/pitch, `legsAnim`, `torsoAnim`, `angles2[YAW]` (0–7), `eFlags` (EF_DEAD), velocity, `fixedlegs`/`fixedtorso` |
| cvars tested | `cg_swingSpeed 0.3`, `cg_playerLeanScale 1.0` |
| output | legs angles (world), torso and head angles **relative to parent** |
| timing | stateful; deterministic under a declared step (25 ms canonical) |
| status | **PROVEN** — 37 differential cases, axes compared to 1e-4 |
| limits | render schedule of the original recording is unknown, so this is faithful *behaviour*, never bit-identical to a specific historical client run |
| consumers | custom camera views, actor posing, retargeted performance, presenters |

## SWING_ANGLES — the lag that makes a body read as a body

| | |
|---|---|
| source | `cg_players.c :: CG_SwingAngles` — `sha256:8886c348ef1e5450` |
| status | **PROVEN** — yaw turn, pitch, 359→5 wrap, all 8 movement dirs, idle, variable frametime |
| gotcha | `AngleMod` is **quantised** to 1/182° (`(360/65536)*((int)(a*(65536/360))&65535)`), not a modulo. The scale branch uses a strict `<`, so exact-modulo values sit ON the boundary and take the wrong branch. |
| gotcha | first sight of an actor centres him **and still swings that step** |
| consumers | anything that turns a body: replays, retargets, presenter gestures |

## PLAYER_LEAN — velocity bank on the legs

| | |
|---|---|
| source | tail of `CG_PlayerAngles` |
| inputs | `pos.trDelta`, `cg_playerLeanScale` |
| behaviour | `speed = VectorNormalize(vel) * leanScale * 0.05`; roll −= speed·dot(vel, axis[1]); pitch += speed·dot(vel, axis[0]) |
| status | **PROVEN** — 6 velocity cases (still, forward, sideways, diagonal, high speed, airborne) |
| measured | up to ~31° of combined lean on the real fixture |
| consumers | high-speed shots, movement retargeting, strafe/rocket-jump emphasis |

## PAIN_TWITCH — damage reaction

| | |
|---|---|
| source | `cg_players.c :: CG_AddPainTwitch` — `sha256:93e26c21d6271c29` |
| behaviour | ±20° torso roll decaying linearly over `PAIN_TWITCH_TIME` 200 ms |
| inputs | time, `pe.painTime`, `pe.painDirection` |
| provenance | `painTime` is the recorded `EV_PAIN`; direction **alternates** per pain (`cg_event.c: painDirection ^= 1`). Both recovered from the event stream — never invented from an obituary or a guessed damage figure. |
| status | **PROVEN** — onset / mid-decay / last ms / expired, both directions |
| consumers | damage reactions, low-HP emphasis, freeze-and-explain |

## FIXED_LEGS / FIXED_TORSO — per-model posing rules

| | |
|---|---|
| source | `cg_players.c :: CG_ParseAnimationFile` (flags), consumed in `CG_PlayerAngles` |
| **where from** | the MODEL'S `animation.cfg`. Configstrings choose the model, and therefore which animation.cfg applies — the flags are not configstring fields. |
| status | **PROVEN in the evaluator** (4 flag combinations) · **NOT WIRED**: PANTHEON does not yet read animation.cfg for these, so both are currently false in real renders |
| consumers | correct posing for models that declare them |

## ANIMATION_PHASE — frame, oldFrame, backlerp

| | |
|---|---|
| source | `CG_RunLerpFrame` / `CG_SetAnimFrame`, reproduced in closed form |
| status | **NOT ORACLE-PROVEN** — implemented and unit-tested, not yet differentially compared. Next candidate for the `WANT` list. |
| known-correct | `LEGS_WALKCR = 13` and the leg-frame skip; the toggle bit restarts an animation whose number did not change |
| consumers | replay, stutter, retime, freeze, presenter gestures |

## VIEW_OFFSET — first-person camera

| | |
|---|---|
| source | `cg_view.c :: CG_OffsetFirstPersonView` and its call graph |
| status | **NOT IMPLEMENTED, NOT PROVEN.** Only recorded `viewheight` (26 / 12 / −16) and snapshot interpolation are done. Bob, landing, step smoothing, damage kick, duck transition and the death branch (roll 40°, pitch −15°, `STAT_DEAD_YAW`) are all absent. |
| consumers | faithful POV, damage chase, landing/step camera effects |

## IMPACT_EFFECT — projectile transitions

| | |
|---|---|
| status | **NOT STARTED.** Recorded rocket trajectories render (`trType`/`trTime` recovered); trail, muzzle flash and explosion are cgame effect services the host does not have. |
| consumers | explosion choreography, projectile transitions, freeze/replay recipes |

---

## Adding the next behaviour

1. Name the creative requirement.
2. Find the real implementation in the 11.3 tree.
3. Add `(file, signature)` to `WANT` in `extract_oracle.py`; extraction fails
   if the function is not found uniquely, and `--check` fails on drift.
4. Give it a genuine test context. **A stubbed dependency means that
   behaviour is not tested** — say so rather than letting a no-op agree with
   a no-op.
5. Feed identical state and declared times to oracle and PANTHEON.
6. Diff the outputs that get *drawn*, not just convenient scalars. Comparing
   swing yaw alone hid the entire velocity lean, which lands on pitch and roll.
7. Implement the semantic behaviour in PANTHEON.
8. Add an entry here with hashes, inputs, status and limits.

Add behaviour when a creative requirement needs it. Do not bulk-lift cgame.
