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

## ANIMATION_PHASE - frame, oldFrame, backlerp

| | |
|---|---|
| source | `cg_players.c` -- `CG_RunLerpFrame` `sha256:13003b6ad8f6c82a`, `CG_SetAnimFrame` `sha256:61e8c20269a1d47b`, `CG_SetLerpFrameAnimation` `sha256:c7aa7b70cad83a30`, `CG_ClearLerpFrame` `sha256:c08b2f55a52a49c5` |
| harness | `oracle_anim.exe` (`oracle_anim_main.c`) -- reads an animation table and a schedule, prints `animationNumber animationTime frameTime oldFrameTime oldFrame frame backlerp` per step |
| state | per body part: `animation`, `animationNumber`, `animationTime`, `frameTime`, `oldFrameTime`, `frame`, `oldFrame`, `backlerp` |
| inputs | animation number (with `ANIM_TOGGLEBIT`), `speedScale`, the render time, and the model's animation table |
| cvars tested | `cg_animSpeed 1`, `cg_debugAnim 0` |
| PANTHEON | `render_frame.py::run_lerp_frame` / `clear_lerp_frame` |
| status | **PROVEN** -- 51 differential cases: six animation shapes x five fixed schedules (16/25/33/100/250 ms), variable frametime, initialLerp, non-loop clamp, reversed, flipflop, partial loop, mid-sequence switch, toggle restart, switch every step, clear, large forward jump, backward jump, repeated time, five speed scales |
| limits | faithful under a DECLARED render schedule. The schedule of whatever client originally recorded the demo is unknown and unknowable, so this is never a claim of bit-identity with a specific historical playback |
| consumers | replay, stutter, retime, freeze, presenter gestures |

**The closed form is retired.** PANTHEON reproduced this as
`frame = time / frameLerp`, and the host carried its own copy. The oracle
proved both wrong. The engine advances `frameTime` by exactly ONE `frameLerp`
per RENDER CALL, **from the previous frameTime**, and only then clamps up to
the current time. Two consequences no function of time alone can express:

* an animation advances at most one frame per render call, so a render
  schedule coarser than the animation's own frame rate plays it **slower**
  rather than skipping frames;
* `backlerp` measures the real interval between two frame times, not the
  fractional part of an index.

`animationTime` is `frameTime + initialLerp` **at the moment of the switch**,
so where an animation starts depends on when the switch happened.

Visual record: `docs/visual-record/2026-09-07/animation_phase_engine_vs_closedform.png`
-- one sarge run cycle at a 30 fps schedule, engine-faithful on top and the
retired closed form below. The closed form runs one whole frame ahead at every
step.

### Gotchas the oracle caught

| | |
|---|---|
| `ANIM_TOGGLEBIT` is **128** and `MAX_TOTALANIMATIONS` is **37** | written from memory as 256 and 44; the oracle threw `Bad animation number: 257` rather than agreeing. `test_anim_constants_match_the_header` now reads both out of `bg_public.h`. |
| `f *= speedScale` is **not** double arithmetic | `speedScale` is a float32 but the product is evaluated wider and truncated straight to int (32-bit gcc, `FLT_EVAL_METHOD 2`). At scale 1.3 that is 12.99999952 -> frame 2, where a float32-rounded 13.0 gives frame 3. |
| `(frameTime - animationTime) / frameLerp` truncates **toward zero** | right after a switch the numerator really is negative, and Python floor division puts the body a frame behind. |
| first sight must call `CG_ClearLerpFrame` | it seeds `oldFrame` AND `frame` to the animation's first frame. A zeroed lerp frame leaves `oldFrame` at 0 -- an unrelated pose -- and the first render blends the actor out of it. |

## FIXED_LEGS / FIXED_TORSO -- per-model posing rules (WIRED)

| | |
|---|---|
| source | `cg_players.c :: CG_ParseAnimationFile` (flags), consumed in `CG_PlayerAngles` |
| **where from** | the MODEL'S `animation.cfg`. Configstrings choose the model, and therefore which animation.cfg applies -- the flags are not configstring fields. |
| how PANTHEON reads it | `pantheon_frame.exe --dump-model <model>` prints the parsed table and both flags; `engine/pantheon/model_assets.py` turns that into an `AnimationSet`, which `from_frame_truth(model_anims=...)` consumes. The host reads the pak because only it can; it decides nothing about the answer. |
| status | **PROVEN in the evaluator** (4 flag combinations) and **WIRED**: real renders now read the real `animation.cfg`. |
| measured | all **26** player models shipping an `animation.cfg` in `baseq3` parse cleanly, and **none of them declares either flag**. Wiring this therefore changes no pixel on the stock asset set. It is not dead code -- a custom or imported model that declares one is now posed correctly instead of silently ignored -- but nothing in the current corpus looks different because of it. |
| consumers | correct posing for models that declare them |

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
