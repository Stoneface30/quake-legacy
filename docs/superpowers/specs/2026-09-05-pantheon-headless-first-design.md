# PANTHEON headless-first — design

**Date:** 2026-09-05 · **Branch:** `feature/pantheon-prologue` · **Rules:** CLAUDE.md HL-1..HL-4
**Status:** boundary + interface + guard test shipped (d7b40d77); headless loop, event emission, ActionGraph, MapSpatialIndex, PerformanceLibrary, bench and golden set shipped on `feature/pantheon-headless` (2026-09-05 evening). See §7.

## 1. The problem

Two jobs had been mixed together. PANTHEON should already be the headless engine;
Wolfcam should be one visual backend and an external compatibility oracle. Sessions kept
returning to Wolfcam because a few things were still only proven by the running client:
MD3 animation and interpolation, model/skin/shader behaviour, PVS, native effects
(`cg_wh`), camera playback, and "does this `.dm_73` really play and look like Quake?".
Those are renderer and runtime questions. They are not a reason for Wolfcam to be in
control of the pipeline.

The cost was the iteration loop for movement and action logic:

```
change → launch Wolfcam → capture → wait → look at frame → discover mistake → relaunch
```

That loop was right for the colour path and latched cvars. It is wrong for
`jump pad → air movement → mouse flick → rocket fire → projectile → hit`, which is
arithmetic on the demo's own serverTime.

## 2. What was already true in the tree (review, 2026-09-05)

| Layer | Module | Headless today? |
|---|---|---|
| PerformanceTrace extraction | `engine/pantheon/performance.py` | yes — parser only |
| FrameTruth | `engine/pantheon/frame_truth.py` | yes — emitted from scenario, never reconstructed |
| RoundScenario / compiler → `.dm_73` | `scenario.py`, `compiler.py`, `engine/parser/dm73_write.py` | yes |
| Navigation / motion statistics | `navigation.py`, `motion_reference.py` | yes — frags DB + parser |
| Recorded action → scenario keyframes | `scenario.py::Actor.perform(trace)` (commit 8e3b177f, same day) | yes — 77/77 samples, 0.000 u error at 40 Hz |
| ShotSpec → film | `shot.py::render` | Wolfcam (correct: it is the backend) |
| cvar existence | `cvar_probe.py` | Wolfcam (correct: RUNTIME_CAPABILITY_PROOF) |

No headless module imported `wolfcam_capture` or spawned a process. The boundary held in
practice but was undocumented and unenforced, and there was no `retarget` / `compare` /
`validate_semantics`, so every reproduction check was a Wolfcam capture.

## 3. Architecture

```
RAW .dm_73
   → DM73 parser
   → canonical game state (players, movement, aim, animation, weapons,
                           projectiles, damage/events, round state, POV)
   → PerformanceTrace
   → FrameTruth
   → Scene · TimeMap · RoundScenario
   → ChoreographyPlan
   → ShotSpec
   → RenderJob
       ├── WOLFCAM_REFERENCE   (shipped)
       ├── BLENDER             (planned — IDs, Cryptomatte, depth, normals, cameras)
       └── OFFSCREEN_QUAKE     (planned — renderer engineering, blocks nothing)
```

Everything above the backend row runs without launching a game.

### 3.1 Shipped this session

- `engine/pantheon/backends.py` — `BackendUse` (closed list of four), `RenderBackend`
  protocol, `WolfcamReference`, `render(backend, *, shot, out_dir, use)`. `use` is
  keyword-only with no default: a launch must name its purpose.
- `creative_suite/tests/test_pantheon_headless_boundary.py` — AST scan. Headless modules
  may not import `subprocess`, `wolfcam_capture`, `shot`, `backends`, `cvar_probe`,
  `ab_scene`. Every module under `engine/pantheon/` must be classified HEADLESS or
  BACKEND_ALLOWED or the suite fails.
- CLAUDE.md `HARD RULES — PANTHEON HEADLESS` (HL-1..HL-4), in the prologue worktree and
  the main checkout.

### 3.2 Next unit: the headless reproduction loop

Target API (all headless):

```python
trace  = pantheon.extract_performance(demo=demo_id, actor=actor, interval=(t0, t1))
repro  = pantheon.retarget(trace, actor="SLASH", transform=target_frame)
result = pantheon.compile(repro)              # RoundScenario → FrameTruth → .dm_73 bytes
report = pantheon.compare(trace, result.trace) # result.trace = extract_performance(result.demo)
assert report.semantic_fidelity == PASS
```

Only then:

```python
backends.render("WOLFCAM_REFERENCE", shot=shot, out_dir=out,
                use=BackendUse.REFERENCE_RENDER)
```

`compare` re-extracts a PerformanceTrace from the synthetic demo with the SAME extractor
used on the real one, so the two sides are measured by one instrument. Wolfcam receives
the finished demo only as an independent validator (`EXTERNAL_DM73_VALIDATION`).

Module placement: `Actor.perform(trace)` already covers the verbatim case of `retarget`
(same actor, same place). `retarget` proper (new actor model, world transform, time
offset) and `compare` are new headless modules (`engine/pantheon/retarget.py`,
`engine/pantheon/compare.py`); add both to `HEADLESS` in the guard test when created.
Neither imports anything from the BACKEND_ALLOWED set. The 77/77 round-trip number
quoted in commit 8e3b177f must become a `compare` report on disk, not a commit message.

### 3.3 Check sheet — jump-pad rocket (template for every action reproduction)

All times on the demo's serverTime ms. Tolerances are proposals; tighten against the
first real trace.

```
start:
  position error        ≤ 1 u
  velocity error        ≤ 5 u/s
jump_pad:
  event present         EV_JUMP_PAD, same client
  timestamp error       0 ms  (snapshot-exact)
apex:
  timestamp error       ≤ 1 snapshot
  position error        ≤ 4 u
aim:
  yaw trace RMS error   ≤ 0.5°
  pitch trace RMS error ≤ 0.5°
  flick peak slew error ≤ 10 %
fire:
  EV_FIRE_WEAPON delta  0 ms
  weapon                ROCKET
rocket:
  spawn position error  ≤ 2 u
  trajectory error      ≤ 2 u per sample (missile entity pos series, not scalars)
  speed                 ~900 u/s (the only usable-path discriminator)
impact:
  EV_MISSILE_HIT / obituary present
  time error            ≤ 1 snapshot
  location error        ≤ 4 u
animation:
  legs/torso run-length sequence identical
```

A failed line renders nothing. Report format: one JSON per comparison under
`creative_suite/generated/pantheon/compare/<demo_hash>_<client>_<t0>.json` with every line
above as `{expected, observed, error, tolerance, pass}`.

## 4. Headless engine vs headless renderer

Ready now: the engine (game truth is already owned). Not ready: a Quake-faithful headless
renderer. Wolfcam gives BSP, MD3, QL shaders, lightmaps, animation, effects, weapon models,
particles, marks, client interpolation, PVS and native cgame rendering for free.
Reimplementing that only to remove Wolfcam is wasted effort (HL-4).

Two later routes, neither blocking the film:

- **Route 1 — offscreen Quake renderer.** FrameTruth → cgame adapter → offscreen GL →
  RGB / depth / masks / normals. The ideal faithful backend; renderer engineering.
- **Route 2 — Blender.** FrameTruth → Blender scene state. Gives what Wolfcam cannot:
  object IDs, Cryptomatte, depth, normals, custom materials, wall visibility control,
  custom poses and pointing, geometry transforms, destruction, arbitrary cameras.
  Wolfcam remains the reference: does the Blender reconstruction line up with Quake?

Route 2 first — it adds capability; Route 1 only removes a dependency.

## 5. What this fixes beyond speed

Runtime Wolfcam behaviour discovered so far — latched cvars applying a launch late,
nonexistent cvars from 12.7 source, camera jitter between launches, archived settings
contaminating experiments, capture lock problems, renderer profiles moving cached IDs —
is all backend contamination. With the import graph closed it cannot influence game
truth, performance truth, scene truth, timing truth, camera intent or synthetic action.

## 6. Instruction for the prologue session

Before continuing the jump-pad rocket reproduction:

1. Run `pytest creative_suite/tests/test_pantheon_headless_boundary.py` — must be green.
2. Build `retarget` and `compare` headless (§3.2), classify them HEADLESS in the guard.
3. Produce the §3.3 check sheet against the chosen candidate from
   `performance.find_jumppad_rocket` and get it to PASS.
4. Only then film via `backends.render(..., use=BackendUse.REFERENCE_RENDER)` and
   compare frames with the real capture.

No Wolfcam launch before step 4.

## 7. Shipped on `feature/pantheon-headless` (2026-09-05)

| Unit | Module | Proof |
|---|---|---|
| Headless API | `engine/pantheon/headless.py` — `extract_performance`, `compile_performance`, `reextract`, `run` | `test_pantheon_headless_api.py` |
| Retarget | `engine/pantheon/retarget.py` — `EXACT_WORLD`, `LOCAL_FRAME`, `validate_retarget` | same |
| Compare | `engine/pantheon/compare.py` — `PerformanceDiff`, six statuses, gaps as spans | same |
| Event emission | `compiler.py` — entity events with sequence bits, temp-entity impacts/trails | REAL_ACTION_TRACE_PROOF_01 `event:* = MATCHED` |
| Sound intent + recorded pose | `frame_truth.py::SOUND_INTENT`, `ActorTruth.pitch/velocity/legs_anim` | `test_frame_truth_carries_the_recorded_pose_and_the_sound_intent` |
| ActionGraph | `engine/pantheon/action_graph.py` — evidence-bearing nodes, transform validation, projectile tracks, rail/LG on their own terms, closed category list | `test_action_graph.py`; real trace reads `JUMP_PAD -> AIRBORNE -> FIRE -> PROJECTILE` |
| MapSpatialIndex | `engine/pantheon/map_spatial_index.py` — 64u cells, layers, adjacency, encounters, floors; feeds `validate_retarget` | `test_map_spatial_index.py` |
| PerformanceLibrary | `engine/pantheon/performance_library.py` — `PERF:` refs, SQL coarse categories, ActionGraph fine categories | CLI `--counts` |
| Bench | `engine/pantheon/headless_bench.py` | `creative_suite/generated/pantheon/bench/bench.json` |
| Golden set | `creative_suite/tests/test_pantheon_golden_headless.py` — real demos, skips without the corpus | run log |
| Boundary audit | `test_pantheon_headless_boundary.py` — imports AND vocabulary (`wolfcam`, `cvar`, `.avi`, `cam10`, `Popen`, `cg_` ...) | suite |

Rules HL-5 (character != performance), HL-6 (gaps stay gaps), HL-7 (events and sound are game state) added to CLAUDE.md.

## 8. Sprint 2 (2026-09-06): one authority, render permission, templates

- **Merge reconciliation.** `feature/pantheon-prologue` merged into `feature/pantheon-headless` (de07fb6e). The prologue's event chain (`ActionEvent.code/carrier/other_entity`, temp-entity events read off entity state, `_RecordedEvent` replayed by the compiler) is the surviving extraction/compilation; the headless branch's parallel emission was dropped. On top: attribution by event semantics (missile impact = his missile in that slot on the previous tick; rail trail = entity names him; obituary = him as killer; teleport = out/in pair AND his own discontinuity), parser rows from entities >= MAX_CLIENTS never double-counted, absent wire fields read as zero, removed temp entities forgotten by the edge detector, otherEntityNum mapped real -> synthetic, recorded obituaries credited not re-authored, context actors performed from their own traces.
- **Temp entities are fresh entities.** eType is 8 bits on the wire; the toggle bits were truncated (316 -> 60) and two identical impacts on consecutive ticks in one slot read as one. Temp emissions rotate through a 96-slot pool; same-tick extra player events go out as external temp entities.
- **RenderPermit** (`creative_suite/engine/render_permit.py`, HL-8): default DENY; `PANTHEON_RENDER_ALLOWED=1`; defer while `quakelive*.exe` runs; `PANTHEON_RENDER_FORCE=1`; queues keep `QUEUED` + `RENDER DEFERRED`; eight launch sites gated; conftest forbids any game process in tests.
- **Performance templates** (`performance_templates.py`): `TPL:<group>:<hash>:<client>:<start_ms>`, 12,969 real segments from 2,400 traces, 11 of 14 groups populated (RETREAT/CHASE need `others`, ROCKET_PREDICTION needs an observed splash impact before the kill); `find()` by distance / heading / duration / stance / weapon / airborne.
- **SpatialValidity**: NavigationTruth + MapSpatialIndex asked together for LOCAL_FRAME.
- **Golden headless suite**: 9 real cases green (jump pad, rocket kill, rail, run/turn, jump, death, observation gap, teleport, weapon change); zero game processes.
- **Ownership**: `docs/reference/pantheon_ownership.md`.
