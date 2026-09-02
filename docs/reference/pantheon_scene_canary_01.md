# PANTHEON_SCENE_CANARY_01 — the first complete directed scene

**Date:** 2026-09-01 · **Verdict: PASS, with three defects found and fixed
by frame inspection and two open issues recorded honestly.**

This is composition, not research. Every primitive used here
(`cam10_writer`, `camera_compiler_v2`, `camera_paths`, `pantheon_runtime`,
`scene_recipe`, the FX DSL, the pk3 grade override, the depth pass) was
already proven; the work was assembling them into one reproducible,
data-driven scene and looking at every frame that came out.

Harness (uncommitted, scratchpad): `build_hero_scene.py`,
`canary_capture.py`, `run_canary.py`, `determinism_proof.py`.
Frames: scratchpad `frames/` + `sheet_*.png`. **Not promoted to
`docs/visual-record/`** — same discipline as `free_wins_proof.md`.

---

## 0. Headline findings

Four bugs and two limitations, all found by **looking at frames**. Every
capture in this document exited `rc=0` with zero errors in `qconsole.log`,
including the ones whose output was unusable.

| # | Finding | Severity |
|---|---|---|
| 1 | `cg_drawCameraPath` / `cg_drawCameraPointInfo` default to **1** and are `CVAR_ARCHIVE`. Every `NATIVE_CAM10` capture renders wolfcam's own path-editing overlay into the movie. | **Critical** — silently ruins every native-camera master |
| 2 | `pantheon_runtime.baseline_lines()` emitted a non-ASCII em dash, so it could never be written into an `encoding="ascii"` capture cfg. The module had never run in a real capture. | **High** |
| 3 | Defining `weapon/rocket/trail` **replaces** the stock trail wholesale, including its `Light`. The first SUBTLE pass therefore made the shot *darker* than FX OFF. | **High** |
| 4 | A one-shot `runfx` cannot make a trail; the trail is a per-frame engine HOOK. Modelling it as a cue yields one puff at the muzzle that reads as a working trail. | **High** (design) |
| 5 | The first HERO FX bloom obscured the victim entirely — an effect that eats the frag. Retuned. | Medium |
| 6 | A `zzz_uhd_*.pk3` renders one surface as a pure black quad. The "UHD" look is not strictly an improvement. | Medium — **open** |

---

## 1. Hero scene selection — and why not frag 5979

Frag **5979** was suggested. It is the highest-scoring rocket in the corpus
(`highlight_score` 46.7, `DIRECT_ROCKET` + `AIR_ROCKET` 829u +
`EXTREME_FLICK`), but its cached projectile path is unusable for a
projectile camera:

```
frag 5979  launch t=553075 pos [-355.6, 175.3, 684.1]
           impact t=553075 pos [-374.0, 178.0, 718.0]
           points: 2      flight: 25 ms      distance: 38.7u
```

A 2-point, 25 ms, 38-unit path is a point-blank rocket. There is no flight
to follow.

The other suggestion — `CA-<player>-overkill-2012_12_06-19_31_30.dm_73`
@ 523875, "161 points, 4000 ms" — was also rejected, for a subtler reason:
316u over 4000 ms is **79 u/s**. A QL rocket travels ~900 u/s. Surveying
all 4,391 cached paths, the median implied speed is 1079 u/s (correct), so
that row's launch time is simply wrong. It would have produced a camera
crawling behind a rocket that is not there.

**Selection criteria actually used** (physics, not score): `weapon_name`
LIKE `ROCKET%`, `confidence = CONFIRMED`, `>= 8` points, implied speed in
**800-1200 u/s**, flight `>= 700 ms`. 260 candidates; sorted by
`highlight_score`.

### Chosen: frag 24326

```
demo          CA-<player>-qUARanTINe-2011_09_22-18_43_52.dm_73   (map: quarantine)
content_hash  0bbddb724288cb78d15884fe88fc9f40209a16c26c7a6ebf03ac3d42d285d55c
server_time   291650 ms   round 8   recognition_version 2
highlight     40.9
classes       DIRECT_ROCKET, AIR_ROCKET, FLICK_SHOT, CLEAN_FLICK,
              DIRECT_CONFIRMED_GEO, PREDICTION_TEMPORAL, PIXEL_SHOT_GEO,
              TINY_GAP_SHOT
launch        t=290525  pos [751.1, 1018.2, 632.1]  dir [0.649, -0.761, 0.009]
impact        t=291650  pos [1499.0, 141.0, 668.0]
path          46 points, 1125 ms flight, 1153u, 1025 u/s, CONFIRMED
```

Why this one is the better shot: **1.125 seconds of real rocket flight over
1153 units** gives the camera genuine time to do something, and the target
earns the shot — airborne at 266u, moving 677 u/s, travelling 487.9u
*during the flight*, visible only **11.1%** of the time
(`los_visible_fraction`, `los_angular_size_deg` 2.63 — hence
`PIXEL_SHOT_GEO` / `TINY_GAP_SHOT`), hit **directly**
(`projectile_direct_geometry = DIRECT_CONFIRMED`, expansion 0.0u) after a
122°/325 ms flick. It is a hard shot that photographs well.

### Note on path linearity

3,860 of 3,935 multi-point cached paths deviate <1u from a straight line.
That is **not** a defect: rockets fly straight. The 89 `grenade` paths do
show real ballistic curvature (up to 363u deviation), confirming the
extractor records genuine trajectories where they exist.

---

## 2. Architecture — three identities, three lifetimes

`SceneRecipeV2` was **not** extended (adding a field changes `recipe_id`
for every existing recipe and breaks the concurrent Music Intelligence V2
workstream). The new production layer is subordinate and refers to it by id.

```
SceneRecipeV2         demo identity + TimeMap + semantic anchors   WHAT / WHEN
   | recipe_id
PantheonScene         camera intent + fx stack + look + passes     HOW IT LOOKS
   | camera_compilation.artifact_hash
camera_compilations   the compiled .cam10                          EXECUTION
```

New modules:

| File | Role |
|---|---|
| `creative_suite/engine/pantheon_scene.py` | `PantheonScene`, `CameraIntent`, `FxCue`, `CameraCompilation`, `OutputPasses`; anchor resolver; FX cfg compiler; `pantheon_scenes` table in `cinematic.db` |
| `creative_suite/engine/pantheon_grade.py` | `GRADE_ORIGINAL` / `GRADE_PANTHEON_SUBTLE` / `GRADE_PANTHEON_HERO` as `scripts/colorcorrect.fs` in `zzz_zz_pantheon_grade.pk3` |
| `creative_suite/engine/pantheon_fx.py` | the `.fx` script at each intensity, HOOK and CUE effects |

`camera_compilations` is **reused** from `cam10_writer.py`, not duplicated.

### Semantic anchoring (§12/§16)

No camera stage and no FX cue stores a raw millisecond. Each names a recipe
anchor plus an integer-µs offset, and every anchor carries an `EvidenceRef`
back to the recognition row. Resolution is the only sanctioned way to get a
time:

```python
resolve_anchor(recipe, "impact-0", -200_000)   -> demo µs
resolve_anchor_ms(recipe, "impact-0")          -> demo ms, half away from zero
```

Three anchors are minted for this scene and kept **independently named even
where two resolve to the same instant**: `launch-0` (PROJECTILE_LAUNCH),
`impact-0` (ROCKET_IMPACT), `frag-0` (FRAG). A direct hit kills on contact,
so `impact-0` and `frag-0` coincide here — but a splash kill separates them,
and the camera language must not have to change when it does.

Regression-tested: moving the impact anchor 25 ms moves the camera window
and the FX fire time **together**
(`test_anchor_move_moves_camera_and_fx_together`). An unresolved or unknown
anchor raises rather than silently resolving to zero.

---

## 3. The camera

### Arc — 4 stages of the 6, deliberately

Over-editing is a failure mode, so `FPV` and an explicit `RELEASE` move
were dropped. FPV was also dropped for a mechanical reason worth recording:
a first-person stage needs `cg.freecam` **off**, while the whole cam10
sampling block is gated on it being **on** (`cg_view.c:3092-3094`). Mixing
the two inside one capture is not a proven mechanism, and inventing it here
would have been research, not composition.

| Stage | Window (anchored) | Shape |
|---|---|---|
| `PROJECTILE_FOLLOW` | `launch-0 +0` → `launch-0 +750 ms` | ride behind the rocket, stand-off ramping 34u → 150u |
| `SIDE_LEAD` | `launch-0 +750 ms` → `impact-0 +0` | smoothstep hand-off out to the orbit entry |
| `IMPACT_ORBIT` | `impact-0 +0` → `impact-0 +700 ms` | 105° arc, r=260u, h=110u |
| `IMPACT_HOLD` | `impact-0 +700 ms` → `impact-0 +1000 ms` | hold, then cut |

Total 2.125 s. Look-at is decoupled from position via `retarget_lookat`
against a subject track that is **the rocket during flight and the impact
point after it**, with `damping=0.25` and a 220°/s angular-speed cap.

### Compilation result

```
authored keyframes      29
dense samples (60 Hz)   128        hz_clamped: False
final .cam10 points     128
collision status        VALID      (0 solid keyframes, 0 blocked segments)
min wall clearance      5.5 u
adjustments             none — adjust_path never had to run
rejected sections       none
backend                 NATIVE_CAM10   (loadcamera / playcamera)
.cam10                  137,403 bytes, LF-only, no CRLF
artifact hash           55ab1bb1ac141a3262279a0816f53a6f4fdf8225f5f94060893de698ef337e43
```

128 points is well inside `MAX_CAMERAPOINTS` (512) and consumes **zero**
`MAX_AT_COMMANDS` slots — the whole capture used 4 of 128 (`video`, one
`runfx`, `stopvideo`, `quit`).

### Two collision failures, and the geometry probe that fixed them

The first compile came back **SHORTENED** — only 58 of 128 samples usable,
min clearance 0.375u, blocked at samples 3-6 and 57-73:

* **Samples 3-6 (launch).** A camera parked 150u behind the muzzle starts
  *inside the wall behind the shooter*. Fixed by ramping the stand-off
  34u → 150u over 320 ms, which also reads better: the shot opens tight on
  the rocket and falls back as it flies.
* **Samples 57-73 (orbit entry).** The orbit at r=300 crossed geometry.
  Fixed by probing the map rather than guessing — for every azimuth at a
  range of radii and heights, test "camera point in open space AND clear
  line of sight to the impact":

  ```
  h=110 R=260  clear+LOS azimuths: 0-40, 130-290
  h=110 R=300  clear+LOS azimuths: 0-40, 130-160, 190-240, 300-350  (fragmented)
  ```

  The rocket arrives on bearing 130.5°, so the orbit enters at +10° and
  sweeps +105° (140° → 245°), entirely inside the clear 130-290 band, at
  r=260 rather than 300.

Recompile: **VALID**, 128/128 samples, 5.5u clearance.

---

## 4. THE CRITICAL FINDING — wolfcam draws its camera path into your movie

The first successful capture was correctly framed, correctly timed, and
completely unusable. Giant glowing cyan numerals filled the frame; a ribbon
of digits traced the camera's own path through the shot; a point the camera
passed close to filled the entire screen.

These are not HUD elements. `cg_draw2D` was already `0`. They are drawn in
**world space** by wolfcam's camera-authoring overlay:

| cvar | Default | Flags | Draw site |
|---|---|---|---|
| `cg_drawCameraPath` | **`1`** | `CVAR_ARCHIVE` | `cg_view.c:4827` |
| `cg_drawCameraPointInfo` | **`1`** | `CVAR_ARCHIVE` | `cg_draw.c:139`, `:667` |
| `cg_drawCameraPathAngles` | `0` | `CVAR_ARCHIVE` | — |

Registered at `cg_main.c:2316-2319`. They exist so a human can hand-author a
path in a live session, and they are **on out of the box**. With a 128-point
path the result is a wall of numbered markers.

`rc=0`. Zero warnings. Nothing in `qconsole.log`. Caught only by opening the
PNG.

**This is the single most important entry now in
`pantheon_runtime.RUNTIME_BASELINE`** — it is exactly the `CVAR_ARCHIVE`
leak class that module was written to prevent, and it had been missed
because nobody had captured a native-camera shot and *looked* at it.

```python
"cg_drawCameraPath": "0",
"cg_drawCameraPathAngles": "0",
"cg_drawCameraPointInfo": "0",
```

After the fix, the same capture: clean frames, `camera loaded` ×1,
`couldn't get nextsnap` ×0, `too many at commands` ×0, `couldn't find fx` ×0.

### Second runtime-baseline bug

`baseline_lines()` opened with `f"// {BASELINE_VERSION} — explicit reset…"`.
That em dash is not ASCII, and capture cfgs are written
`encoding="ascii"` because the engine tokenizer is byte-oriented. Every
attempt to use the baseline raised `UnicodeEncodeError` at write time — so
`pantheon_runtime`, committed to prevent cvar leakage, had **never once run
in a real capture**. Fixed; regressed by
`test_baseline_lines_are_pure_ascii`.

---

## 5. FX — the `runfxat` trap, and a bigger one behind it

### Primitive selection is not exposed to the caller (§17)

`CG_RunFx_f` (`cg_consolecmds.c:7662`) and `CG_RunFxAt_f` (`:7746`) take the
**same** optional trailing arguments — `[origin0..2] [dir0..2]
[velocity0..2]` — and both fall back to a view snapshot for whatever is
missing. The difference is *when* that snapshot happens:

* `at <t> runfx <name>` — the whole command is deferred, snapshot at **fire
  time**. Measured PASS.
* `runfxat <t> <name>` — executes immediately and re-emits
  `at <t> runfx <name> <baked floats>`; snapshot at **parse time**. From
  `cgamepostinit.cfg` that is before the demo is seeked, i.e. the map
  origin. Measured as pure noise.

Since `runfx` already accepts explicit coordinates, `runfxat` has no
remaining advantage. **`compile_fx_cfg_lines` never emits it at all** —
the broken form is unreachable, not merely discouraged. A cue with
`world_pos` compiles to `at <t> runfx <name> <x> <y> <z>` (deferred *and*
explicit); without it, to `at <t> runfx <name>`.

### The bigger trap: a one-shot cannot make a trail

An earlier draft modelled the projectile trail as a `runfx` cue at the
launch anchor. That would have emitted **one puff at the muzzle** — and
looked enough like a trail to be reported as one.

`cg_fx_scripts.c:6940-7440` binds a fixed set of script *names* to per-frame
engine hooks. `weapon/rocket/trail` (bound at `:7147`) runs **every frame
for every rocket in flight**, receiving that rocket's own
`origin/angles/velocity/dir/axis`. Defining the name is what arms it; there
is no console command and no fire time.

`FxCue` therefore carries `parameters["binding"]`:

* `CUE` (default) — fired once by `at <t> runfx …`
* `HOOK` — armed by definition; compiles to **no cfg line**, and a
  `world_pos` on a HOOK is refused (the engine supplies the entity's origin
  every frame, so a caller-supplied one would be silently ignored).

### The defect that only a frame could show

Defining `weapon/rocket/trail` **replaces** the stock trail wholesale — it
does not layer onto it. The shipped `q3mme.fx` version opens with
`color 1 0.75 0 / size 200 / Light`. The first SUBTLE pass omitted a
`Light`, so it **deleted the rocket's warm dynamic glow**: at t=0.45 the
SUBTLE frame was measurably *darker* than FX OFF (`dmean −1.87`), which is
the exact opposite of what an effect level should do.

Fixed: every level now carries a light, and SUBTLE's reproduces the stock
one (`_STOCK_TRAIL_LIGHT = ("1 0.75 0", 200)`).

### FX ladder — measured, at identical camera / time / look

Only the `.fx` file content differs across these three.

| comparison | t | Δmean | % px >8 |
|---|---|---|---|
| OFF → SUBTLE | 0.45 | +0.15 | 2.0 |
| OFF → SUBTLE | 1.20 | −0.04 | 1.1 |
| SUBTLE → HERO | 0.45 | +4.22 | 14.4 |
| SUBTLE → HERO | 1.20 | **+5.64** | **6.6** |

*Before* the retune, SUBTLE→HERO at impact was `+18.75 / 18.1%` and the
bloom hid the victim completely. HERO was reduced (burst 42→30, bloom
0.8s/`150+430*lerp` → 0.5s/`80+200*lerp`) until the frag stayed readable.
The cap on this level is "unmistakable on a single frame", **not** "obscures
the frag" — a fragmovie effect that eats the frag is a failed effect.

**Honest limitation:** SUBTLE is now *very* close to OFF (1-2% of pixels).
It is genuinely restrained, as required, but at impact the natural rocket
explosion dominates and SUBTLE's burst barely reads. SUBTLE currently earns
its keep on the trail, not on the impact.

---

## 6. The PANTHEON grade

Mechanism per `free_wins_proof.md` proof 3: one `scripts/colorcorrect.fs`
inside `zzz_zz_pantheon_grade.pk3` in the wolfcam gamedir.

`RB_ColorCorrect` (`tr_backend.c:1092`) resolves **four** uniforms —
`backBufferTex`, `p_gammaRecip`, `p_overbright`, `p_contrast` — and calls
`ri.Error(ERR_FATAL)` if any lookup fails. GLSL strips uniforms a shader
never *reads*, so declaring them is not enough.
`assert_consumes_all_uniforms` runs on every build and is itself tested with
a deliberately-stripped shader.

`GRADE_ORIGINAL` is a **real variant** that writes the stock maths verbatim,
not "ship no pk3". All three looks therefore go through the identical
override path, and the only difference between frames is the colour
arithmetic — not "pk3 present vs absent", which would confound the
comparison with search-path and shader-recompile differences.

The look, in order: shadow **lift** (before anything else, so nothing is
crushed that we then try to grade) → gentle smoothstep S-curve → controlled
desaturation against true luma → cool shadows / warm highlights split-tone →
light vignette floored by `smoothstep(0.55, 1.0, r)`. Explicitly not
orange-and-teal. Tests enforce the restraint envelope: saturation ≥ 0.80,
shadow lift > 0, vignette ≤ 0.35, tint ≤ 0.05 per channel.

### Grade ladder — measured

The first HERO tuning was a label, not a level: **0.0%** of pixels differed
from SUBTLE by >8 at t=0.45. Strengthened (sat 0.86→0.80, contrast
0.18→0.34, vignette 0.22→0.32, tints ~1.4×):

| SUBTLE → HERO | mean RGB | Δmean | % px >8 |
|---|---|---|---|
| t=0.45 | `65.7 58.5 48.7` → `59.7 56.1 51.5` | −1.88 | 7.0 |
| t=1.20 | `59.6 52.9 44.9` → `53.8 50.7 48.1` | −1.62 | 2.8 |
| t=2.05 | `82.5 69.8 59.2` → `76.2 67.0 61.1` | −2.42 | 8.9 |

Red falls, blue rises, mean drops — desaturation + cool split-tone +
vignette, exactly as designed, and still legibly Quake.

---

## 7. A/B/C look comparison — identical camera, FOV, time, FX OFF

`sheet_look_ABC_t2.05.png`, `sheet_look_ABC_t0.45.png`,
`sheet_grade_t2.05.png`. Same `.cam10` (hash
`55ab1bb1…`), same window, same `cg_fov`, FX OFF in all three. The only
variables are the asset packs and the grade.

| comparison | t | mean RGB | Δmean | % px >8 |
|---|---|---|---|---|
| A ORIGINAL → B UHD | 0.45 | `79.6 69.3 53.6` → `67.4 58.3 44.1` | −10.86 | 23.0 |
| A ORIGINAL → B UHD | 2.05 | `87.7 72.8 58.4` → `85.0 69.9 55.5` | −2.86 | 10.3 |
| B UHD → C PANTHEON | 0.45 | `67.4 58.3 44.1` → `65.7 58.5 48.7` | +1.03 | 0.9 |
| B UHD → C PANTHEON | 1.20 | `61.2 52.3 39.7` → `59.6 52.9 44.9` | +1.42 | 0.7 |

B→C is small in mean but **systematic in direction**: blue rises +4.6 /
+5.2 / +3.7 while red falls, across all three sample times. That is the
cool-shadow split-tone doing exactly what it was written to do. The SUBTLE
grade is, by design, a whisper.

### OPEN ISSUE — a UHD pack renders a surface pure black

Visible in every UHD frame and absent from ORIGINAL: a wall/beam seen
through the upper-left doorway is replaced by a **solid black quad**
(`sheet_uhd_panel.png`).

```
region y 303-467, x 214-429 @ t=2.05
  ORIGINAL  mean RGB 64.9 50.5 33.3   max 255
  UHD       mean RGB 39.4 28.6 15.9   max 195
```

`log_default_shader` was recorded per capture but the culprit pack was not
isolated — that needs a per-pack bisect of `zzz_uhd_01..05.pk3`. Until then,
**"UHD" is not strictly an improvement over "ORIGINAL"**, and the PANTHEON
look inherits the defect because it builds on the UHD packs.

---

## 8. Beauty + depth pass

One capture, `mme_saveDepth 1` + `mme_depthRange 2000` + `mme_depthFocus 0`,
same recipe / time / camera pose. Two AVIs:

| stream | bytes |
|---|---|
| `canary01_depth-0000.avi` (beauty) | 54,478,848 |
| `canary01_depth-depth-0000.avi` (depth) | 9,455,616 |

Depth semantics verified, not assumed:

| | t=0.45 | t=1.20 |
|---|---|---|
| resolution | 1920×1080 | 1920×1080 (matches beauty exactly) |
| min / max | 126 / 239 | 128 / 255 |
| mean / std | 139.51 / 9.23 | 147.39 / 17.46 |
| unique values | 111 | 104 |
| percentiles 1/25/50/75/99 | 132/134/137/141/168 | 132/135/143/153/206 |

**Non-constant**, and near/far polarity correct (near = dark):

| region (t=1.20) | depth mean |
|---|---|
| near left pillar | **133.6** |
| mid centre (impact) | 183.8 |
| far ceiling gap | **196.8** |

`sheet_depth_t1.20.png` confirms by eye: near geometry black, far corridor
white, the victim's gib a correctly-placed silhouette at its own depth.
MJPEG-lossy as documented in proof 6 (~104-111 distinct levels) — fine as a
ControlNet depth hint, not a precision buffer.

---

## 9. Determinism proof (§48)

`determinism_proof.py`. Two independent builds, then persist → reload →
independent recompile.

```
recipe_id    5c40d954862e6836cd7f19e8241f894b90d004e788e320d395875f88bf743325  MATCH
scene_id     283c0a7bf74832ea61eab2c71bd71fbd9b47738856321367afffd15a2315460d  MATCH
cam10_hash   55ab1bb1ac141a3262279a0816f53a6f4fdf8225f5f94060893de698ef337e43  MATCH

.cam10 file  137,403 bytes    CRLF present: False

recipe reload id match : True
scene  reload id match : True
scene  json byte-equal : True
scene  == original     : True

recompiled camera hash : 55ab1bb1ac141a3262279a0816f53a6f4fdf8225f5f94060893de698ef337e43
matches scene pointer  : True
camera_compilations    : cam10-v1 / NATIVE_CAM10 / 55ab1bb1…

cfg sha256 run1        : 47a408dab032b0d8a750f241f587db586fff1ed198d006807195115862e76cd3
cfg sha256 run2        : 47a408dab032b0d8a750f241f587db586fff1ed198d006807195115862e76cd3  MATCH

RESULT: PASS
```

Asset hashes (all deterministic — the pk3 uses `ZIP_STORED` with a fixed
`date_time` so the hash means "this grade", not "this build ran at this
second"):

| asset | sha256 (first 32) |
|---|---|
| `GRADE_ORIGINAL` | `b79895587e18a8c6cb4abc8c28cb1cc8` |
| `GRADE_PANTHEON_SUBTLE` | `b6406fae646d771a335a464256f27074` |
| `GRADE_PANTHEON_HERO` | `c8e393961768cc0d67a65c1cdae02c92` |
| fx `OFF` | `bb601a7ce9e957babcbb8aff3724e73b` |
| fx `SUBTLE` | `999d66214f6eb30166a1b6c0adbe0676` |
| fx `HERO` | `951e6e93700a12529b342346f60cf548` |
| runtime baseline | `36493f7140a2315c24d1a7d6faec6ade` |

Worth noting as *correct* behaviour: `scene_id` changed when
`cg_drawCameraPath` was added to `RUNTIME_BASELINE`, because
`runtime_baseline_hash` is a scene field. A scene captured under a different
runtime baseline **is** a different scene.

---

## 10. Cost (§50) — what is cheap enough for interactive use

Everything on the authoring side is effectively free; the engine is the
entire budget.

| operation | cost |
|---|---|
| camera authoring (29 keyframes) | < 1 ms |
| BSP load (quarantine, from pak00) | 0.075 s |
| resample + look-at retarget (128 samples) | < 1 ms |
| collision check + compile + write `.cam10` | **0.215 s** |
| grade pk3 build (×3) | 0.002 s |
| fx script write (×3) | < 1 ms |
| gamedir setup per variant (packs, pk3, fx) | ≤ 0.01 s |
| **wolfcam capture, 2.125 s @ 60 fps, 1920×1080** | **12.7 - 22.3 s** |
| depth pass (same window, second stream) | +~3 s, +9.5 MB |
| ffmpeg still extraction (8 PNGs) | 1.4 - 8.2 s |

Observations:

* **A full camera re-plan is interactive.** 0.29 s from evidence to a
  collision-checked, compiled, hashed `.cam10`. A director can iterate on
  camera geometry in a UI without a progress bar.
* **Capture is ~6-10× realtime** and dominates everything. One variant
  ≈ 20 s wall; the 10 captures in this document ≈ 3.5 minutes of engine time.
* **The depth pass is nearly free** (~15% overhead) — cheap enough to enable
  by default on any shot that might later feed AI conditioning.
* **Grade and FX swaps cost nothing to prepare** but each still needs a full
  re-capture, so an A/B/C look sheet costs 3 captures, not 1.
* Slow motion remains the expensive knob (`timewarp_measurement.md`:
  ~0.3 s wall per output frame) and was deliberately **not** used here — the
  scene is one `normal` 1/1 TimeMap segment, because it had to be captured
  ten times over.

---

## 11. What was NOT done

* **No bulk master capture.** Ten captures of one 2.125 s window.
* **No music modules touched**; `music_anchor_slots` carries names only
  (`build`, `drop`, `release`).
* **`render_part_v6.py` untouched** (V1, frozen).
* **No FPV stage** — see §3.
* **No slow motion** — see §10.
* **The UHD black-quad culprit was not isolated** — see §7.
* Nothing committed; left for review.

---

## 12. Staging hygiene

One wolfcam at a time; `taskkill` before and after every capture.
`zzz_uhd_*.pk3` were moved aside (never deleted) for the ORIGINAL variant
and restored. On completion: `capture.cfg` deleted,
`cgamepostinit.cfg` reset to `// idle`, grade pk3 removed,
`scripts/pantheon_canary.fx` removed, all `canary01_*` AVIs deleted, all
five UHD packs restored.

> **Provenance correction (2026-09-02):** the projectile trajectory used by this canary was INFERRED by `extract_projectile_paths` from the impact event and the recorder's view rays; the missile entity was never observed. Its evidence class is `EVENT_CONSTRAINED_RECONSTRUCTION`, not `ENTITY_OBSERVED`. The impact event itself is recorded. Geometry unchanged; label corrected.
