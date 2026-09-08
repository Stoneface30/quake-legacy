# q3mme Cinematic Capability Audit — source-level

**Date:** 2026-08-31
**Scope:** Research Agent B, PANTHEON Engine & AI Asset Overhaul workstream.
**Method:** read-only source audit of the two trees we actually care about:

| Tree | Path | Role |
|---|---|---|
| **q3mme** | `engine/engines/_forks/q3mme/trunk/code/` | the origin of MME; the eventual control-socket target (per `replay-runtime-feasibility.md`) |
| **wolfcamql** | `engine/engines/_canonical/code/` | **the engine we build and capture with today** |

Everything below cites file:line. Where the two trees differ, the difference is
called out explicitly, because **we run wolfcamql, not q3mme** — a q3mme
capability that wolfcamql never imported is a porting project, not a feature.

Companion docs (already written, not repeated here):
`docs/reference/replay-runtime-feasibility.md`,
`docs/reference/moviemaking-feature-matrix.md`.

---

## 0. Executive summary

### 0.1 The finding that matters most

**`creative_suite/engine/timeline.py::to_wolfcam_script` emits camera lines that
no engine in this repo can parse.** It writes

```
camera add <servertime> <x> <y> <z> <pitch> <yaw> <roll> <fov>
```

(`creative_suite/engine/timeline.py:238-244`). Both engines disagree on **both
halves** of that line:

1. **The command is not called `camera` in wolfcamql.** wolfcamql registers
   `q3mmecamera` (`cg_consolecmds.c:8590`), plus its own native `addcamerapoint`
   / `playcamera` / `savecamera` / `loadcamera` (`cg_consolecmds.c:8510-8516`).
   There is no `camera` command. In q3mme proper it *is* `camera`
   (`cg_demos_camera.c:858 demoCameraCommand_f`) — so the line would at best
   only ever have worked against stock q3mme, which we do not run.
2. **`camera add` takes no positional arguments in either engine.** It is a
   *snapshot* verb: it adds a point at the **current** demo play time using the
   **current** view origin/angles/fov.
   - q3mme: `cg_demos_camera.c:862-872` — `cameraPointAdd(demo.play.time, demo.camera.flags)`
     then `VectorCopy(demo.viewOrigin, point->origin)`.
   - wolfcamql: `cg_q3mme_demos_camera.c:901-916` — identical shape.
   The 8 numbers we emit are silently discarded.
3. `playq3mmecamera` **takes no argument** (`cg_consolecmds.c:8003-8035`), so
   `timeline.py:271`'s `playq3mmecamera <name>` passes an ignored token. It also
   hard-requires ≥2 points (`cg_consolecmds.c:8014-8017`) and issues its own
   `seekservertime` back to `points[0].time - cg_cameraRewindTime`
   (`cg_consolecmds.c:8019-8025`) — which will fight any seek we issued.

So the "already wired and working" assumption in the workstream brief is
**not supported by the source**. `at <t> timescale <v>` / `at <t> cg_fov <v>` /
`at <t> cl_freezeDemo 1` *are* real and do work (see §4); the **camera path half
is a no-op**. This has to be the first thing the new workstream fixes, and the
fix is easy — see §1.6.

### 0.2 REUSE / EXTEND / REPLACE

| Capability | Verdict | Where |
|---|---|---|
| Baked camera keyframes → engine | **REPLACE** — write `.cam10` / `.q3mmeCam` files, not `camera add` lines | §1.6 |
| Python-side spline/rig math (`camera_paths.py`) | **REUSE** — keep baking in Python; engine splines are worse-behaved than ours | §1.2, §1.3 |
| FOV keyframing | **REUSE** (native, per-point, both engines) | §1.4 |
| Motion blur (`mme_blurFrames`) | **REUSE as-is** — accumulation is real and correctly output-gated | §2.1 |
| Depth of field (`mme_dof*`) | **REUSE**, and **EXTEND** to a live preview via `mme_dofVisualize` | §2.2 |
| DoF live auto-focus on an entity | **REUSE** — already implemented in wolfcamql | §2.3, §5.2 |
| FX scripts (`CG_RunQ3mmeScript` / `runfx` / `runfxat`) | **REUSE — this is the big one.** A complete particle/beam/light/sound/decal DSL, console-triggerable at an exact servertime | §3 |
| Slow-motion during capture (`timescale`) | **REUSE with a documented A/V caveat** — see the desync finding | §4.2 |
| Native speed *ramps* (q3mme `line` system) | **REPLACE / port** — wolfcamql never imported it | §4.4 |
| Live entity look-at camera | **REUSE** — but the *native* wolfcam `/ecam angles ent`, **not** the q3mme `camera target` (which is `#if 0`'d out in wolfcamql) | §5 |
| Matte / stencil / world-shader passes | **REPLACE / port** — q3mme-only, and even q3mme's stencil path is `#if 0` in wolfcamql | §6.2 |
| Geometry morph / mesh warp | **NEW C CODE** — does not exist anywhere | §6.5 |

---

## 1. Camera system internals

### 1.1 There are TWO camera systems in wolfcamql, and they are not equivalent

wolfcamql ships both:

**(a) The imported q3mme camera** — `cg_q3mme_demos_camera.c`, commands
`q3mmecamera` / `playq3mmecamera` / `stopq3mmecamera` / `saveq3mmecamera` /
`loadq3mmecamera` (`cg_consolecmds.c:8590-8595`). Linked list of
`demoCameraPoint_t {time, origin, angles, fov, flags}`.

**(b) wolfcamql's own native camera** — `cg_camera.h:114-242 cameraPoint_t`,
commands `addcamerapoint` / `playcamera` / `savecamera` / `loadcamera` /
`ecam` (`cg_consolecmds.c:8510-8516`). A fixed array (`MAX_CAMERAPOINTS 512`,
`cg_camera.h:8`) of much richer points.

**(b) is strictly more capable** and is the one the wolfcam docs treat as
primary (`README-wolfcam.txt:1085-1240`). It has everything the q3mme camera
has plus: per-point origin type (`spline` / `interp` / `jump` / `curve` /
`splineBezier` / `splineCatmullRom`, `cg_camera.h:61-69`), per-point angle type
including **`CAMERA_ANGLES_ENT`** (`cg_camera.h:76`), separate roll type
(`cg_camera.h:84-90`), fov type (`cg_camera.h:92-99`), a position **offset**
channel (`cg_camera.h:101-106`), per-channel initial/final velocity control
(ease-in/ease-out), and a **per-point console command** (`cp->command`).

The q3mme camera in wolfcamql is a compatibility import that has been partially
gutted — see §5.1.

### 1.2 Interpolation — verified against source

`master_profile.py`'s docstring claims "catmullrom/bezier smoothing, quaternion
angles, CAM_FOV channel". All three claims are **true but need a large asterisk
on "bezier"**.

**Position** — `posInterpolate_t` is exactly three modes
(`cg_demos_math.h:26-31`): `posLinear`, `posCatmullRom`, `posBezier`.
The basis matrices are at `cg_demos_math.h:139-161`:

```c
case posCatmullRom:
    matrix[0] = 0.5f * ( -t + 2*t*t - t*t*t );
    matrix[1] = 0.5f * ( 2 - 5*t*t + 3*t*t*t );
    matrix[2] = 0.5f * ( t + 4*t*t - 3*t*t*t );
    matrix[3] = 0.5f * (-t*t + t*t*t);
    break;
default:
case posBezier:
    matrix[0] = (((-t+3)*t-3)*t+1)/6;
    matrix[1] = (((3*t-6)*t)*t+4)/6;
    matrix[2] = (((-3*t+3)*t+3)*t+1)/6;
    matrix[3] = (t*t*t)/6;
```

> **GOTCHA — "posBezier" is not a Bézier.** That `/6` basis is the **uniform
> cubic B-spline** basis. It is *approximating*, not *interpolating*: at `t=0`
> the weights are `(1/6, 4/6, 1/6, 0)`, so the curve passes through the
> **average of three neighbours**, never through the keyframe itself. A camera
> path baked in Python and played back with `smoothPos = posBezier` **will not
> visit the positions we computed** — it will visit a smoothed-inward version of
> them, and tight rigs (orbit radius, wall clearance from `camera_paths.py`'s
> BSP collision) are silently violated.
>
> `posCatmullRom` (`matrix[1] = 1` at `t=0`) **is** interpolating and *does*
> pass through every control point.
>
> **And the defaults are wrong for us in both engines:**
> - q3mme initialises `demo.camera.smoothPos = posBezier` (`cg_demos.c:963`).
> - wolfcamql's native camera defaults `cg_cameraDefaultOriginType "splineBezier"`
>   (`cg_main.c:2432`).
> - wolfcamql's q3mme-camera default is `cg_q3mmeCameraSmoothPos "0"`
>   (`cg_main.c:2435`) = `posLinear`, i.e. no smoothing at all.
>
> **Action:** any baked path we ship must explicitly set catmullrom
> (`q3mmecamera smoothPos 1`, or per-point `type = CAMERA_SPLINE_CATMULLROM = 5`
> in a `.cam10` file). The wolfcam docs say the same thing in prose at
> `README-wolfcam.txt:1188-1189`: *spline* "you are not likely to pass through
> the exact origin that you selected", *curve* "has the advantage … of being able
> to pass through exactly through the chosen origins".

**Arc-length reparameterisation.** q3mme does not walk the spline in uniform
`t`. `cameraPointLength()` (`cg_demos_camera.c:114-156`) numerically integrates
segment arc length by 100-step subdivision, and `cameraOriginAt()`
(`cg_demos_camera.c:158-229`) then feeds those lengths through
`dsplineCalc()` (`cg_demos_math.c:531-546`) — a **monotone Fritsch–Carlson
Hermite spline** over (Δtime, Δlength) triples — to get a distance along the
path for a given time, then marches the curve to that distance
(`cg_demos_camera.c:210-227`). This is a genuinely good constant-ish-velocity
implementation and it is why q3mme dollies feel smooth. `mov_smoothCamPos`
(`cg_main.c:446`, default `0`) tightens the marching tolerance
(`cg_demos_camera.c:135-136`, `208-209`).

> Consequence for us: **the engine will re-time our keyframes.** If we bake
> 50 ms-spaced keyframes with per-keyframe timing intent (e.g. a hold on the
> money shot), the arc-length reparameterisation will partially flatten that
> intent into constant speed. Dense keyframes (our `CURVE_SAMPLE_MS = 50`,
> `timeline.py:32`) mostly defeat the spline anyway. **Recommendation: bake
> dense and use `posLinear` / `CAMERA_INTERP`** — let Python own the curve, and
> use the engine purely as a playback device. That is the lowest-surprise
> configuration and it keeps `camera_paths.py` as the single source of truth.

**Angles** — two modes only (`cg_demos_math.h:33-37`): `angleLinear`,
`angleQuat`. `angleQuat` is the default branch of `cameraAnglesAt()`
(`cg_demos_camera.c:257-274`) and it is a real **quaternion squad** (spherical
cubic) interpolation: `QuatFromAnglesClosest()` picks the hemisphere-consistent
quaternion for each of the 4 control points (`cg_demos_math.c:207-216`), then
`QuatSquad()` (`cg_demos_math.c:342-...`) does the log/exp tangent construction
and a double slerp. So the docstring claim "quaternion angles" is **correct**,
and it is a proper implementation, not a slerp-with-euler-fallback.

> Note `QuatToAngles()` round-trips through an axis matrix and `AxisToAngles()`
> (`cg_demos_math.c:57-99`, `272-276`). Gimbal-adjacent pitches (±90°) will
> lose roll. Our rigs mostly avoid straight-down shots; worth remembering for
> any top-down "geometry match" attempt.

**FOV** — `cameraFovAt()` (`cg_demos_camera.c:279-321`) uses
`VectorTimeSpline()` (`cg_demos_math.c:444-473`), a time-weighted cubic Hermite
over the 4 neighbouring fov values. Confirms `master_profile.py`'s "CAM_FOV
channel" claim.

> **Semantics gotcha:** in q3mme a point's `fov` is stored as an **offset from
> `cg_fov`**, not an absolute: `point->fov = demo.viewFov - cg_fov.value`
> (`cg_demos_camera.c:868`, and identically `cg_q3mme_demos_camera.c:908-912`).
> wolfcamql's **native** camera uses absolute fov instead, and the README says so
> explicitly (`README-wolfcam.txt:1206`: *"spline fov uses the final fov values
> … instead of offset values which q3mme uses"*). Our emitter writes an absolute
> fov (`timeline.py:244`), so it is correct for the native format and **wrong**
> for the q3mme format.

### 1.3 Point storage and time keying

`demoCameraPoint_t` is keyed on `time` (int ms) with a flags mask
(`CAM_ORIGIN 0x001`, `CAM_ANGLES 0x002`, `CAM_FOV 0x004`, `CAM_TIME 0x100`,
`cg_camera.h:13-16`). Each channel is interpolated over *only the points that
carry that flag* (`cameraMatchAt()`, `cg_demos_camera.c:61-83`) — so you can
key origin and angles on different cadences. Useful, and something our current
emitter does not exploit (we always write all three).

### 1.4 What `playq3mmecamera` actually does

`CG_PlayQ3mmeCamera_f` (`cg_consolecmds.c:8003-8035`):
- refuses if `cg.playPath` is active,
- refuses with `< 2` points,
- **unconditionally** issues `seekservertime (points[0].time - 1000*cg_cameraRewindTime)`
  via `trap_SendConsoleCommandNow` (`:8019-8025`),
- sets `cg.cameraQ3mmePlaying = qtrue`.

`cg_cameraRewindTime` exists so local entities (rail trails, marks, blood,
smoke) have time to spawn before the shot starts
(`README-wolfcam.txt:1219`). **We should be setting it** — currently we do not,
and it is exactly the "why do the rail trails pop in" class of artefact.

### 1.5 Live view lock

Playback is gated on `cg_cameraQue` (default `1`, `cg_main.c:2429`), which the
docs describe as *"allow camera to play even without /playcamera command
[1: don't play commands associated with camera points, 2: play camerapoint
commands]"* (`README-wolfcam.txt:1221`).

> **To use per-keyframe commands (§3.4) you must set `cg_cameraQue 2`.** At the
> default `1` the `cp->command` string is parsed, stored, saved, and never run.

### 1.6 REPLACE: how to actually get a baked path into the engine

Both engines have a **file** path that accepts fully-specified points, and both
loaders are trivially writable from Python.

**Option A (recommended) — wolfcamql native `.cam10`.**
Writer: `CG_SaveCamera_f` (`cg_consolecmds.c:2226-2330`).
Reader: `CG_LoadCamera_f` (`cg_consolecmds.c:2401+`) — strictly **line-ordered**
`CG_FS_ReadLine` + `sscanf`; the trailing English labels on each line are
ignored, so the format is a positional record, easy to emit.

```
WolfcamCamera 10
0  camera point number
<x> <y> <z>  origin
<pitch> <yaw> <roll>  angles
<type>  type              # CAMERA_SPLINE_CATMULLROM = 5, CAMERA_INTERP = 1
<viewType>  viewType      # CAMERA_ANGLES_INTERP = 0, CAMERA_ANGLES_ENT = 4
<rollType>  rollType      # CAMERA_ROLL_INTERP = 0
<flags>  flags
<cgtime>  cgtime          # float servertime ms
<splineType>  splineType
<numSplines>  numSplines  # DEFAULT_NUM_SPLINES 40
... viewPointOrigin / viewEnt / offsets / fov / fovType / 6× velocity triples ...
<len>  commandStrLen
<command string if len>
-------------------------------------
```

Written to `cameras/<name>.cam10` (`cg_consolecmds.c:2255`), then
`loadcamera <name>` + `playcamera`. Version constant is
`WOLFCAM_CAMERA_VERSION 10` (`cg_camera.h:7`); the loader also accepts version 9
(`cg_consolecmds.c:2252-2258`). Enum values: `cg_camera.h:61-112`.

This is the only route that gives us `CAMERA_ANGLES_ENT`, the offset channel,
per-channel velocity easing, and per-point commands.

**Option B — q3mme `.q3mmeCam` XML.**
Writer `CG_SaveQ3mmeCamera_f` (`cg_consolecmds.c:8044-8082`), reader
`CG_LoadQ3mmeCamera_f` (`cg_consolecmds.c:8084-8129`). Format is q3mme's
`cameraSave()` (`cg_demos_camera.c:726-748`):

```xml
<camera>
  <smoothPos>1</smoothPos>          <!-- 1 = catmullrom -->
  <smoothAngles>1</smoothAngles>    <!-- 1 = quat -->
  <locked>1</locked>
  <target>-1</target>
  <point><time>...</time><origin>x y z</origin><angles>p y r</angles><fov>f</fov></point>
  ...
</camera>
```

Written to `cameras/<name>.q3mmeCam`. Simpler, and it is the format that
survives if we ever move the whole pipeline to q3mme proper — but remember
`fov` is an **offset** here, and there is no ent-tracking.

**Neither option needs new engine code.** This is a Python-side change to
`timeline.py` plus one `loadcamera`/`playcamera` pair in the generated cfg.

---

## 2. Depth of field and motion blur

### 2.1 Motion blur — accumulation, and `master_profile.py` is CORRECT

`master_profile.py`'s docstring says *"motion blur SUPPORTED (mme_blurFrames
accumulation; cl_aviFrameRateDivider is DECIMATION, leave 1)"*. **Both halves
verified true.**

The mechanism, in wolfcamql (`renderercommon/inc_tr_init.c:188-305`):

1. `CL_Frame` shortens the per-frame sim step by `1/blurFrames`
   (`client/cl_main.c:5646-5650`), so the engine steps and renders
   `blurFrames` **sub-frames** per output frame.
2. Each sub-frame is `glReadPixels`'d and added into a float accumulator
   with a per-sub-frame weight — `R_MME_BlurAccumAdd`
   (`inc_tr_init.c:266`, impl `renderercommon/tr_mme_common.c:293-309`).
   Weights come from `blurCreate(&shotData->control, mme_blurType->string, …)`
   (`tr_mme.c:156`; `median` / `gaussian` / `triangle`, gaussian width scaled by
   `mme_blurStrength`, `tr_mme_common.c:140-141`).
3. Only when `totalIndex >= totalFrames` does it `R_MME_BlurAccumShift()` and
   `memcpy` the accumulator into the AVI fetch buffer
   (`inc_tr_init.c:281-305`). Every other sub-frame `goto dontwrite`
   (`inc_tr_init.c:302`).

So `mme_blurFrames 8` costs 8× the render work and emits the same number of
frames. Correct 180°-shutter-style accumulation blur, not a screen-space hack.

`cl_aviFrameRateDivider` is pure decimation — `if ((picCount+1) % divider != 0)
goto dontwrite` in the no-blur path (`inc_tr_init.c:189-193`) and
`((picCount+1)*blurFrames) % divider` in the blur path (`inc_tr_init.c:296-299`).
Confirms "leave 1".

`mme_blurOverlap` (`tr_mme.c:368`) adds a rolling ring of previously-read
sub-frames so consecutive output frames share tail samples — smoother, more
memory (`inc_tr_init.c:209-256`).

> **Two real constraints the docstring does not mention:**
>
> 1. **Blur and DoF force `GL_BGR` and kill the alpha channel** —
>    `inc_tr_init.c:174-178`: *"if (useBlur || mme_dofFrames->integer > 0)
>    { glMode = GL_BGR; fetchBufferHasAlpha = qfalse; … }"*, and the README says
>    the same at `README-wolfcam.txt:257`. **Any future "capture with alpha for
>    compositing" plan is mutually exclusive with baked blur/DoF.**
> 2. **Blur is incompatible with `wait`-timed scripts.** The wolfcam docs spell
>    this out (`README-wolfcam.txt:~1250`): *"If you try to render at 120fps with
>    20 blur frames the camera speeds up since effective fps is now (120 * 20 ==
>    2400 fps)"*. Anything in our cfg that is frame-count-timed rather than
>    servertime-timed will run `blurFrames`× too fast. Our `at <servertime>`
>    lines are safe; a `wait` would not be.

**Can blur run without baking (a "LIVE" hint of blur)?** **No.** The
accumulation path is gated on the capture command stream
(`RE_TakeVideoFrame` → `inc_tr_init.c`), which only runs while
`CL_VideoRecording(&afdMain)` is true (`client/cl_main.c:5631`). There is no
`mme_blurVisualize` analogue. A live preview can only ever show the raw
sub-frames at whatever real framerate the machine manages. **LIVE = no blur;
MASTER = blur.** Plan the UI accordingly.

### 2.2 Depth of field — multi-pass camera jitter, and it CAN preview live

**DoF is not a depth-buffer post-process.** It is a physically-motivated
aperture simulation: for each output frame the scene is re-rendered
`mme_dofFrames` times with the *eye position and projection centre jittered on
a disc*, converging at the focus plane, and the results are median/accumulated.

- `R_MME_JitterOrigin()` (`renderercommon/tr_mme.c:210-240`) offsets the camera
  origin by `radius * R_MME_FocusScale(focus) * jitter[i]`.
- `R_MME_JitterView()` (`tr_mme.c:242-280`) applies the matching
  `r_znear/focus`-scaled shift to the projection so the focus plane stays put.
- `R_MME_MultiPassNext()` (`tr_mme.c:281-336`) drives the pass loop and
  accumulates into `passData->dof` with a **`"median"`** kernel
  (q3mme: `tr_mme.c:198 blurCreate(passControl, "median", passTotal)`).
- The backend fires it from `RB_SwapBuffers` / draw-surf teardown
  (`renderergl1/tr_backend.c:2349-2360`, `2485-2500`).

Cost is therefore `blurFrames × dofFrames` full re-renders per output frame.
`BLURMAX` caps both (`tr_mme.c:122-145`).

Focus/radius come from `trap_R_UpdateDof(demo.viewFocus, demo.viewRadius)`
(`cg_view.c:6529`), fed either from the keyframed dof track or from a live
target (§2.3).

> **LIVE preview IS possible — wolfcamql added `mme_dofVisualize`.**
> `mme_dofVisualize` is registered `CVAR_TEMP` at `renderercommon/tr_mme.c:375`
> and every DoF gate in the backend is `(tr.recordingVideo || mme_dofVisualize->integer)`
> — `renderergl1/tr_backend.c:1794`, `2279`, `2485`, `2493`. The README confirms
> the intent (`README-wolfcam.txt:1039`: *"added mme_dofVisualize in order to see
> final rendering"*). There is also `cg_q3mmeDofMarker` which draws a
> non-recording focus marker (`cg_view.c:6532-6534`).
>
> **This is a genuine LIVE/MASTER asymmetry in our favour:** DoF can be
> previewed at low `mme_dofFrames` (2–4) in the director session, blur cannot be
> previewed at all.

### 2.3 DoF keyframing and auto-focus

Keyframed track: `demoDofPoint_t {time, focus, radius}` linked list
(q3mme `cg_demos_dof.c:34-58`; wolfcamql `cg_q3mme_demos_dof.c` same shape),
command `/dof add|del|start|end|next|prev|lock|target|…`
(q3mme `cg_demos_dof.c:464-...`; wolfcamql registers `dof`, `saveq3mmedof`,
`loadq3mmedof` at `cg_consolecmds.c:8596-8598`). So DoF is savable/loadable as
XML exactly like the camera — another file we can write from Python.

**Auto-focus on an entity is live and implemented in wolfcamql**
(`cg_view.c:6489-6504`): with `demo.dof.target >= 0` it computes
`focus = dot(viewaxis[0], targetOrigin) - dot(viewaxis[0], vieworg)` — the
perpendicular distance from the camera plane to the entity — **every frame**,
no baked keyframes needed. `demo.viewTarget` (defaulted from `cg.viewEnt`,
`cg_view.c:6485`) does the same at `cg_view.c:6513-6523` using
`mme_dofRadius`.

`master_profile.py`'s `_CINEMATIC_REPLAY` sets `mme_dofFrames: 0` with the
comment "enable per shot with the dof command" — **correct**, and it should
additionally set `mme_dofRadius` and either a `dof target <n>` or a loaded
`.q3mmeDof` track.

### 2.4 Depth passes

`mme_saveDepth` is real and implemented in wolfcamql
(`renderercommon/tr_mme.c:62`, used at `inc_tr_init.c:170-171`, `216-219`,
`244-249`, `269-273`) with `mme_depthRange` (default 2000) and `mme_depthFocus`
(`tr_mme.c:379-380`). `mme_saveDepth 2` writes depth without blur
(`README-wolfcam.txt:1049`). Docstring claim confirmed.

> **Caveat found in the docs:** *"quake3 has an optimization for sprites like
> smoke and blood that will lead to incorrect values if depth buffer is saved"*
> (`README-wolfcam.txt:2953`). A depth pass used for compositing will have holes
> where sprites are — relevant if depth ever backs a transition mask.

---

## 3. `CG_RunQ3mmeScript` / the EffectScripts system

**This is the most under-exploited capability in the engine we already ship,
and it is the correct vehicle for the user's §30-33 impact accents.**

### 3.1 What it is

A complete, interpreted, particle/render DSL. Entry point
`CG_RunQ3mmeScript(const char *script, const char *emitterEnd)` at
`cg_fx_scripts.c:4050`. Scripts are loaded from a single text file named by
`cg_fxfile` (`cg_main.c:2391`, default `""`), parsed by
`CG_ParseQ3mmeScripts()` (`cg_fx_scripts.c:7500+`), reloaded via
`CG_ReloadQ3mmeScripts(cg_fxfile.string)` (`cg_main.c:8447`).

Shipped examples live at
`engine/engines/_canonical/package-files/wolfcam-ql/scripts/*.fx`
(`alltest.fx`, `cpmaRlSmoke.fx`, `dirtest.fx`, `flesh.fx`, `q2railcore.fx`,
`q3mme.fx`) and `engine/engines/_forks/q3mme/trunk/files/scripts/*.fx`.
Language reference: `engine/engines/_forks/q3mme/trunk/files/fxScript.txt`.

### 3.2 What an EffectScript can actually DO

Not a toy. The token table (`cg_fx_scripts.c:~400-560`, enum at `:78+`) covers:

**Render/emit:** `sprite`, `spark`, `quad`, `beam`, `light`, `decal`,
`decalTemp`, `rings`, `dirModel` / `anglesModel` / `axisModel` (place an MD3),
`animFrame`.
**Audio:** `sound`, `soundLocal`, `soundWeapon`, `loopSound`, and list variants
`soundList` / `soundListLocal` / `soundListWeapon`.
**Simulation:** `emitter` / `emitterF` (spawn a persistent entity that re-runs
its body each frame over a lifetime), `moveGravity`, `moveBounce`, `sink`,
`impact`, `trace` (world collision from inside the script), `vibrate` (camera
shake), `rotate`, `rotateAround`, `pushParent`/`pop` (transform hierarchy).
**Control flow:** `if` / `elif` / `else`, `repeat`, `loop`, `distance { }`
(run body every N units of travel), `interval { }`, `return`, `continue`.
**State:** `shader`, `extraShader`, `shaderTime`, `model`, `modelList`,
`shaderList`, `color`, `alphaFade`, `colorFade`, `cullDistanceValue`.
**Math:** full expression parser — `+ - * / %`, comparison/boolean ops,
`sqrt ceil floor sin cos tan asin acos atan atan2 pow wave clip`, constants
`time cgtime loop lerp life pi rand crand`, 10 scratch floats `t0..t9` and
10 scratch vectors `v0..v9`.
**Context:** `clientNum`, `enemy`, `teammate`, `inEyes`, `team`, `gameType`,
`surfaceType`, `inWater`, and every powerup predicate (`pwQuad`, `pwInvis`,
`pwFrozen`, …).

Two escapes that matter enormously for us:

- **`command`** (`cg_fx_scripts.c:492` token, impl `:6663-6700`) — an FX script
  can **issue an arbitrary console command**. So an FX script can set cvars,
  trigger camera commands, start/stop capture — anything.
- **Cvar reads.** Per `fxScript.txt` (final section): *"if the fx math parser
  can't find the variable name it'll try to see if there's a regular q3 cvar
  with that name and then it'll use that value"*. **Every FX script is
  parameterisable at capture time from our generated cfg**, with no reparse.
  This is the clean way to drive per-shot intensity from Python.

### 3.3 How to trigger one — this is the part that unlocks §30-33

Three console commands (`cg_consolecmds.c:8578-8581`):

```
runfx   <fx name> [ox oy oz] [dx dy dz] [vx vy vz]
runfxat <'now' | servertime | clock time> <fx name> [ox oy oz] [dx dy dz] [vx vy vz]
runfxall
listfxscripts
```

`CG_RunFx()` (`cg_consolecmds.c:7635-7660`) resets `ScriptVars`, seeds
`origin`/`dir`/`velocity`/`color`, then linearly searches
`EffectScripts.names[]` and runs the match. Omitted origin/dir default to the
current freecam or first-person view (`cg_consolecmds.c:7764-7781`).

`runfxat` (`cg_consolecmds.c:7746-7800`) **schedules by servertime** — exactly
the addressing mode our `hit_anchors.py` / `partNN_beats.json` already speak.

**Crucially, every parsed script is registered by name**, whether it is a known
engine hook or not: `CG_SetQ3mmeFXScript()` unconditionally does
`Q_strncpyz(EffectScripts.names[numEffects], name, …); ptr[numEffects] = dest;
numEffects++` (`cg_fx_scripts.c:6787-6789`), and unknown names fall through to
a free-standing `EffectScripts.extra[]` slot (`cg_fx_scripts.c:7449-7452`).
So we can define `pantheon/railAccent` in our own `.fx` file and call
`runfxat 4546629 pantheon/railAccent <x> <y> <z> <dx> <dy> <dz>` from a
generated cfg.

### 3.4 The engine-side hooks (for *overriding* existing effects)

`effectScripts_t` (`cg_fx_scripts.h:214-268`) has per-weapon slots
`fireScript / flashScript / projectileScript / trailScript / impactScript /
impactFleshScript` for every weapon (`cg_fx_scripts.h:186-192`), bound by name
`weapon/<weapon>/<slot>` (`cg_fx_scripts.c:6992-7100+`), plus global hooks:
`playerTalk`, `playerConnection`, `playerImpressive/Excellent/Holyshit/
Accuracy/Gauntlet`, the QL medal set (`playerMedalComboKill`, `MidAir`,
`Revenge`, `FirstFrag`, `Rampage`, `Perforated`, `Accuracy`, `Headshot`,
`Perfect`, `QuadGod`), `playerHaste/Defend/Assist/Capture/Quad/Flight/Friend`,
`playerHeadTrail/TorsoTrail/LegsTrail`, `playerTeleportIn/Out`, `jumpPad`,
`headShot`, `bubbles`, `gibbed`, `thawed`, `impactFlesh`.

Firing sites are all over the cgame:
`cg_ents.c:1984, 2081, 2323` (projectile + trail),
`cg_event.c:1997-2000` (jumppad), `:2454-2471` (teleport),
`:2857-2898` (flesh impact), `:3742-3855` (gib / thaw / headshot),
`cg_effects.c:1066, 1088`, `cg_players.c:2681-3822` (powerups, medals, talk).

There is a fourth trigger route: **per-camera-point commands.**
`/ecam command <console command>` (`README-wolfcam.txt:1133`) stores a string on
a `cameraPoint_t` that fires when the camera reaches that point — a natural
place to hang `runfx` — but it requires `cg_cameraQue 2` (§1.5).

### 3.5 Honest assessment for §30-33

| Ask | Verdict |
|---|---|
| Rail / rocket / LG **impact accents** | **Fully native, today.** Override `weapon/rail/impact`, `weapon/rocket/impact`, `weapon/lightning/impact` in our own `.fx`, or fire a `pantheon/*` accent via `runfxat` at the exact `hit_anchors.py` servertime. Zero new C. The shipped `dirtest.fx` / `q2railcore.fx` are working reference implementations of exactly this. |
| **Projectile bridge** (a visual thread from shooter to victim across a cut) | **Mostly native.** `beam` (image stretched between two points) + `emitter` + `origin`/`end` vectors is exactly the primitive. What is *not* native is that it does not survive a cut — the FX must be re-fired in the destination shot; the "bridge" is an editorial illusion we compose from two engine-native beams. Feasible with no new C. |
| **Teleporter pass** | **Native-ish.** `playerTeleportIn/Out` hooks exist and fire on real events (`cg_event.c:2454-2471`); a bespoke script can be run at any time/place via `runfxat`. What is missing is the *screen-space wipe* — see §6.3. |
| **Impact portal** (using an impact as a screen wipe/mask) | **Not native in wolfcamql.** The FX language draws *in the world*, not to a full-screen mask. See §6.2/§6.3. |
| **Geometry match / morph** | **Not native anywhere.** See §6.5. |

**Verdict: EffectScripts is not a toy.** It is a mature DSL with world
collision, transform hierarchies, conditionals, sound, decals, models, camera
shake and a console escape. The realistic limit is that it is a *world-space
particle system* — it has no framebuffer, no render-target, and no notion of
"the whole screen".

---

## 4. Time control

### 4.1 The `at` command is real

`/at <'now' | servertime | clock time> <command>`
(`README-wolfcam.txt:2247-2258`), with `/listat`, `/clearat`, `/removeat`,
`/saveat <file.cfg>`. Dispatched from `cg_view.c:5293` behind
`cg_enableAtCommands`.

> **Gotcha:** `cg_enableAtCommands` is `CVAR_ARCHIVE` (`cg_main.c:2460`). Default
> is `1`, but a stale `wolfcamconfig.cfg` in the staging gamedir can set it `0`
> and **every `at` line we emit silently stops firing** — including
> `wolfcam_capture.py:136`'s `at <t> seekservertime …`. Our generated profile
> should assert `seta cg_enableAtCommands 1`. It currently does not
> (`master_profile.py`).

### 4.2 `timescale` during AVI capture — the P1-BB-analogous finding

This is the second load-bearing finding of this audit.

**Video.** `client/cl_main.c:5631-5665`. Per captured output frame the sim
advance is:

```c
f = ( (1000.0 / (cl_aviFrameRate->value * frameRateDivider)) * com_timescale->value )
    * (1.0 / blurFrames);
msec = (int)floor(f);
Overf += f - floor(f);            // fractional carry
if (Overf > 1.0) { msec += floor(Overf); Overf -= floor(Overf); }
```

So `timescale 0.5` advances half as much game time per captured frame → **true
slow motion baked into the AVI at the full capture framerate**, no frame
duplication, no ffmpeg `setpts`. That is a genuinely better slow-mo than
anything `effects/speed_ramp.py` can do in post, because every frame is
freshly rendered.

**Audio.** `client/snd_dma.c:1419-1465`, `S_GetSoundtime()` capture branch:

```c
msec = dma.speed / (cl_aviFrameRate->value * blurFrames * frameRateDivider);
s_soundtime += (int)floor(msec);   // + its own Overf carry
```

> ### ⚠ `com_timescale` is absent from the audio advance.
>
> Video sim-time per output frame scales with `com_timescale`; **audio sample
> count per output frame does not.** At `timescale 0.5` the sim advances 8.33 ms
> per frame while the mixer is handed 16.67 ms worth of samples. The game audio
> therefore runs **1/timescale times too fast against the picture**, drifting
> linearly for the whole duration of the slowed section.
>
> This is directly analogous to the AAC-priming/`xfade`-timeline defect behind
> **P1-BB** — a per-frame constant offset that compounds — and it must be
> treated with the same discipline: an **explicit drift audit on the captured
> AVI**, not an assumption.
>
> **Mitigations, in order of preference:**
> 1. **Capture at `timescale 1` and do nothing else.** Any slow-mo comes from
>    ffmpeg-side `speed_ramp.py` as today. Zero risk. (Costs the "freshly
>    rendered slow-mo" benefit.)
> 2. **Capture slowed, then discard the engine's game audio for that clip** and
>    re-derive it. We already own the frag-audio problem end-to-end
>    (`audio_onsets.py`, `sound_templates/`, rule P1-DD) — the templates mean we
>    do not actually need wolfcam's mix for a slowed shot.
> 3. **Set `s_useTimescale 1`.** Registered at `snd_main.c:572` (default `0`),
>    read in `snd_dma.c:1341-1346` and five places in `snd_mix.c`
>    (`:368, 572, 628, 690, 781`). The README describes it as *"adjust audio
>    pitch according to timescale"* (`README-wolfcam.txt:976`). This resamples
>    the channels so a slowed shot gets pitch-shifted-down audio — a different
>    creative choice, and it is **not verified here to fix the sample-budget
>    mismatch**; it changes playback rate inside the mixer, not the per-frame
>    `s_soundtime` step. **Treat as unproven until measured.**
>
> **Recommended verification before any slowed capture ships:** capture the same
> 10 s window at `timescale 1.0` and `0.5`, ffprobe both for `v:0` vs `a:0`
> duration and per-minute drift into `output/*_sync_audit.json` exactly as
> P1-BB's ship gate does, and gate on `max_drift_ms <= 40`.

**Contrast — q3mme does this properly.** q3mme does not reuse `com_timescale`
for capture speed at all. It keeps a sub-millisecond demo clock and steps it by
`frameDelay * demo.play.speed` (`cg_demos.c:485-489`), carrying
`demo.play.fraction` between frames, and its audio hook is fed the *same*
`1.0f/fps` the video uses (`client/cl_main.c:2138 S_MMERecord(shotName, 1.0f/fps)`
where `fps = cl_avidemo * com_timescale * blurFrames`, `:2131`). q3mme's speed
control is capture-coherent by construction; wolfcamql's is a retrofit onto an
integer-millisecond clock.

### 4.3 `cl_freezeDemo` and frame-stepping

`cl_freezeDemo` is `CVAR_TEMP` (`client/cl_main.c:6961`).

> **Gotcha:** by default **freeze does NOT pause capture**.
> `cl_freezeDemoPauseVideoRecording` defaults to `0`
> (`client/cl_main.c:6980`), and the capture branch is gated
> `… && !(cl_freezeDemoPauseVideoRecording && cl_freezeDemo)`
> (`client/cl_main.c:5631`). So `at <t> cl_freezeDemo 1` — which
> `timeline.py:264-268` emits for `freeze` and `impact_hold` — **keeps writing
> identical frames to the AVI** for the hold duration. That is almost certainly
> the behaviour we want (a real held frame in the master), but it is worth
> stating explicitly, because the other default is one cvar away and would
> instead produce a *shorter* clip with a jump cut.
>
> `cl_freezeDemoPauseMusic` defaults to `1` (`client/cl_main.c:6981`) —
> background track pauses on freeze while game audio and the AVI keep running.
> Another small A/V asymmetry to be aware of.

### 4.4 Speed *ramps*: q3mme has a native one, wolfcamql does not

q3mme's "line" system (`cg_demos_line.c`) is a keyframed **time remap**:
`demoLinePoint_t` maps play-time → demo-time, and `lineAt()`
(`cg_demos_line.c:147-166`) returns `(demoTime, demoTimeFraction, demoSpeed)`
in fixed point (`SPEED_SHIFT 14`), interpolating between points when
`demo.line.locked` (`:160`). Commands `line add|del|clear|sync|speed`
(`cg_demos_line.c:364-395`). Result flows straight into the capture clock
(`cg_demos.c:527-535`, `frameSpeed *= demo.play.speed`).

That is a **native, sub-millisecond, capture-coherent speed ramp** — precisely
the primitive P1-Q-AUTO wants.

> **wolfcamql never imported it.** The wolfcamql cgame contains only
> `cg_q3mme_demos{,_camera,_capture,_dof,_math}.c` — there is no
> `cg_q3mme_demos_line.c`, and a grep for `lineAt` / `demo.line` across
> `engine/engines/_canonical/code/cgame/` returns nothing. On wolfcamql, ramps
> must come from `com_timescale` (§4.2, with its A/V caveat) or from ffmpeg.
> **This is a concrete, well-scoped argument for the q3mme migration in
> `replay-runtime-feasibility.md`.**

### 4.5 `com_timescalesafe`

`README-wolfcam.txt:646`: *"com_timescalesafe default 1 — high timescales will
skip demo snapshots and **will break things like camera paths that are synced to
server times**"*. Since every camera path we bake is servertime-keyed, this must
stay `1`, and fast-forward-by-timescale must never overlap a camera path.

---

## 5. Entity tracking / look-at

### 5.1 The q3mme camera target is DISABLED in wolfcamql

q3mme has a live look-at: `cameraUpdate()` (`cg_demos_camera.c:525-547`) resolves
`demoTargetEntity(demo.camera.target)`, calls `chaseEntityOrigin()`, and
overwrites `angles[YAW]` and `angles[PITCH]` every frame — no baked keyframes,
and it composes on top of a keyframed *position* path.

**In wolfcamql that entire function is inside `#if 0 // wolfcamql unused`**
(`cg_q3mme_demos_camera.c:533-563`). The `target` subcommand still parses and
stores a number (`cg_q3mme_demos_camera.c:1002-1030`), and the interactive
"aim at what I'm looking at" picker is `#if 0`'d out inside it. The README
states it plainly: *"FIXME target (Note: target selection isn't available)"*
(`README-wolfcam.txt:1271`).

So: **on the engine we ship, `q3mmecamera target` is dead.**

### 5.2 But the NATIVE wolfcam camera has it, and it is better

`CAMERA_ANGLES_ENT` (`cg_camera.h:76`), exposed as
`/ecam angles ent [entity number]` (`README-wolfcam.txt:1130-1131`), with the
entity number and a starting-origin stored per point
(`cp->viewEnt`, `cp->viewEntStartingOrigin`, serialised at
`cg_consolecmds.c:2286-2289`). There are also viewpoint modes —
`CAMERA_ANGLES_VIEWPOINT_INTERP / _FIXED / _PASS` (`cg_camera.h:77-79`) —
that aim at a fixed world point instead of an entity, plus
`*_USE_PREVIOUS` variants specifically designed for *transitioning out of*
entity-following without an angle jump (`README-wolfcam.txt:1180`).

**Answer to the question: yes, a live dynamic look-at exists that requires no
pre-computed keyframes — but it lives in the native `.cam10` camera, not the
q3mme one.** This makes the §1.6 Option A recommendation stronger: writing
`.cam10` gets us live entity tracking *for free*, and lets
`camera_paths.py::follow_entity` (`creative_suite/engine/camera_paths.py:171-184`)
stop baking angles entirely — bake the *position* rig, set
`viewType = CAMERA_ANGLES_ENT`, and let the engine aim. That removes a whole
class of aim-jitter caused by our 50 ms keyframe sampling of a 20 ms-tick
entity track.

### 5.3 DoF target

Separately live and working — see §2.3. `cg_view.c:6489-6504`.

---

## 6. Transition primitives — honest assessment

### 6.1 What exists

| Primitive | Where | Available to us? |
|---|---|---|
| World-space particles / beams / lights / decals / models / sound | FX scripts, §3 | **Yes, today** |
| Camera shake | FX `vibrate` (`cg_fx_scripts.c` TOKEN_VIBRATE); `cg_vibrate` cvar, recorded into camera points (`README-wolfcam.txt:1230`) | **Yes** |
| World collision from script | FX `trace` | **Yes** |
| Mirror / portal surfaces | `/addmirrorsurface <x> <y> <z>` + `cg_customMirrorSurfaces` (`cg_consolecmds.c:7523-7530, 8575`; `README-wolfcam.txt:1032-1033`); `r_portalBobbing` (`:1306`) | **Yes, but** it renders a mirror of the *same* scene at a world plane — not an arbitrary second source |
| Depth pass | `mme_saveDepth` §2.4 | **Yes** |
| Stencil / entity matte pass | q3mme `mme_saveStencil` + `mov_stencilMask` | **NO — see §6.2** |
| World-shader replacement (flat matte of all world geo) | q3mme `mme_worldShader` (`tr_mme.c:827`, applied `tr_cmds.c:438-444`) | **NO — q3mme only** |
| Chroma-key sky | q3mme `mme_skykey` (`tr_mme.c:825`, `tr_backend.c:535-538`, `tr_sky.c:808`) | **NO — q3mme only** |
| Picture-in-picture | q3mme `mme_pip` (`tr_mme.c:826`, `tr_cmds.c:447`) | **NO — q3mme only** |
| Full-screen shader / render-target compositing | — | **NO — does not exist in either** |
| Mesh deformation / geometry morph | — | **NO — does not exist in either** |

### 6.2 The matte toolkit is q3mme-only, and this contradicts an assumption worth flagging

q3mme has a real compositing kit:

- `mov_filterMask` — bitmask to **hide** entity classes:
  `1` demo-taker, `2` other players, `4` missiles/grenades, `8` items/weapons,
  `16` smoke, `32` blood (`q3mme/trunk/files/cvarlist.txt:160-167`), enforced at
  `q3mme/trunk/code/cgame/cg_ents.c:236, 403` and `cg_players.c:1604, 1642, 2217, 2234`.
- `mov_stencilMask` — same bitmask, but selected entities render **white into the
  stencil output** (`cvarlist.txt:200-201`; `cg_ents.c:267, 351, 489`;
  `cg_players.c:1618, 1653, 1667, 2220, 2237`).
- `mme_saveStencil` writes that buffer out (`cvarlist.txt:107-108`).

Together: *render the same second twice, once normally, once as a black-and-white
matte of just the rocket / just the player.* That is the foundation for every
serious masked transition.

**None of it survived into wolfcamql.** `mov_filterMask` / `mov_stencilMask` do
not exist anywhere in `engine/engines/_canonical/code/` (verified by grep), and
wolfcamql's own stencil path is stubbed out in three places:

```c
#if 0  //FIXME implement
    if ( mme_saveStencil->integer ) { R_MME_BlurOverlapAdd( blurStencil, j ); }
#endif
```
— `renderercommon/inc_tr_init.c:222-227`, `250-256`, `271-277`.

> **Contradiction with `master_profile.py`:** the docstring's MME audit lists
> *"depth passes SUPPORTED (mme_saveDepth)"*, which is correct, but a reader
> naturally generalises that to "MME's auxiliary passes are available". They are
> not — **depth is the only aux pass wolfcamql implements. Stencil is a stub and
> the mask cvars are absent.** Recommend the docstring be amended to say so
> explicitly, because "we can matte out the rocket" is exactly the assumption a
> transitions workstream would make.

### 6.3 On screen-space wipes generally

Neither engine exposes a post-process render-target chain to game code. There is
no `R_PostProcess`, no full-screen shader stage addressable from cgame, and the
FX language has no screen-space primitive (`fxScript.txt` render commands are
`sprite` / `spark` / `quad` / `beam`, all world-space).

The nearest native approximations, in descending order of honesty:

1. **A world-space "curtain"** — an FX `quad` or `beam` wall spawned right in
   front of the camera and scaled to cover the frustum, driven by `lerp`.
   Genuinely native, cheap, and reads as a wipe. Limited to whatever shaders
   already exist.
2. **A depth-hacked sprite** (`Sprite depthhack`, seen in
   `package-files/wolfcam-ql/scripts/dirtest.fx`) — draws over world geometry.
3. **ffmpeg-side.** Everything else.

### 6.4 The four requested primitives, ranked by native feasibility

**1. PROJECTILE BRIDGE — most native-feasible. Ships with zero new C.**
A beam/trail following a projectile is literally what
`weapon/<w>/projectileScript` and `trailScript` are for
(`cg_ents.c:1984, 2081, 2323`), and `q2railcore.fx` is a working example of a
custom beam-along-a-direction. `runfxat` gives exact servertime placement.
The projectile's own position is already in our data — `hit_anchors.py` and the
dm73 parser give us shooter origin, impact origin and time. Build the bridge as
a `pantheon/projectileBridge` script parameterised by cvars (§3.2) and fire it
on both sides of the cut. **Effort: days, all in `.fx` + Python.**

**2. IMPACT PORTAL — feasible as a *stylised approximation*, not a true portal.**
Native today: an impact-triggered expanding `rings` / `quad` / `light` burst that
grows to fill frame (§6.3 approach 1), timed to a cut. That reads convincingly.
A *true* portal — seeing the destination scene through the burst — needs either
the q3mme stencil/worldShader kit ported (§6.2, a bounded renderer port) or an
ffmpeg-side luma-matte using the burst itself as the key, which is achievable
today by capturing the burst pass separately. **Effort: approximation = days;
true portal = weeks, and it is a renderer change.**

**3. TELEPORTER PASS — half native, half not.**
The *event* and the *world effect* are fully native (`playerTeleportIn/Out`
hooks, `cg_event.c:2454-2471`, plus `runfxat`). The *screen transition* is not.
Ranked below IMPACT PORTAL only because the teleport idiom implies the camera
travelling *through* something, which is a camera problem the native camera
solves (`CAMERA_JUMP` between points, `cg_camera.h:64`) but whose visual
continuity depends on the same missing mask machinery. **Effort: days for the
world FX, weeks for a convincing pass-through.**

**4. GEOMETRY MATCH / MORPH — least feasible. Needs new engine code. Say so plainly.**
There is **no mesh deformation, vertex-blend, or model-morph capability anywhere
in either tree.** Q3's MD3 pipeline interpolates between *baked animation
frames* of the *same* model only; there is no cross-model correspondence, no
render-to-texture, and no post-process stage to warp in screen space. FX scripts
can *place* models (`dirModel` / `anglesModel` / `axisModel`) but cannot deform
them. A genuine "morph map A geometry into map B geometry" is a new renderer
feature — new C, a new asset correspondence format, and almost certainly a
GL2-path shader. **This is the one the workstream should either descope or fund
as a real engineering project. It is not a configuration exercise.**

A pragmatic substitute exists and should be considered: the *optical-flow /
frame-morph* approach in post (ffmpeg `minterpolate`, or a learned flow model),
operating on two captured shots that were framed to match. That gets 80% of the
Annihilation-style morph (already noted as an FT-3 ambition) with none of the
engine work — and it makes "GEOMETRY MATCH" primarily a **camera-framing**
problem, which the native camera *can* solve: bake two paths whose final and
initial `origin`/`angles`/`fov` are identical.

---

## 7. Contradictions and corrections to `master_profile.py`'s docstring

`creative_suite/engine/master_profile.py:29-33` currently reads:

> *MME capability audit: motion blur SUPPORTED (mme_blurFrames accumulation;
> cl_aviFrameRateDivider is DECIMATION, leave 1); DoF SUPPORTED (mme_dof* +
> keyframed dof cmd); q3mme camera paths SUPPORTED (catmullrom/bezier smoothing,
> quaternion angles, CAM_FOV channel); depth passes SUPPORTED (mme_saveDepth);
> supersampling = MSAA-in-FBO only.*

| Claim | Verdict | Correction |
|---|---|---|
| motion blur = `mme_blurFrames` accumulation | ✅ **Confirmed** | `inc_tr_init.c:256-305`. Add: forces `GL_BGR`, **kills alpha** (`:174-178`); cannot preview live. |
| `cl_aviFrameRateDivider` is decimation, leave 1 | ✅ **Confirmed** | `inc_tr_init.c:189-193`, `296-299`. |
| DoF supported, `mme_dof*` + keyframed dof cmd | ✅ **Confirmed**, and **understated** | It is multi-pass jittered re-render (`tr_mme.c:210-336`), cost `dofFrames×`. Also: **`mme_dofVisualize` gives a live preview** (`tr_mme.c:375`; `tr_backend.c:1794, 2279, 2485`) and **`dof target` gives live auto-focus** (`cg_view.c:6489-6504`). Both should be in the profile. |
| q3mme camera paths supported, "catmullrom/bezier smoothing" | ⚠️ **Misleading** | `posBezier` is a **uniform cubic B-spline — approximating, not interpolating** (`cg_demos_math.h:154-159`). It will not pass through our baked keyframes. It is also the **default** in q3mme (`cg_demos.c:963`) and in wolfcamql's native camera (`cg_main.c:2432`). Must be explicitly overridden to catmullrom or linear. |
| quaternion angles | ✅ **Confirmed** | Real squad (`cg_demos_camera.c:257-274`, `cg_demos_math.c:342+`). |
| `CAM_FOV` channel | ✅ **Confirmed** | `cg_demos_camera.c:279-321`. **But** q3mme stores fov as an *offset from `cg_fov`* (`cg_demos_camera.c:868`); wolfcamql's native camera stores it absolute (`README-wolfcam.txt:1206`). |
| depth passes supported (`mme_saveDepth`) | ✅ **Confirmed**, but **narrow it** | Depth is the **only** aux pass wolfcamql implements. `mme_saveStencil` is `#if 0` in three places (`inc_tr_init.c:222-227, 250-256, 271-277`) and `mov_filterMask`/`mov_stencilMask` do not exist in wolfcamql at all. |
| "no baked blur/DoF for gameplay masters; those belong to `TR4SH_CINEMATIC_REPLAY`" | ✅ **Sound policy** | Reinforced by the alpha-channel constraint and the render-cost multiplier. |

**Additional gaps in the frozen profiles, all one-liners:**
- `_CINEMATIC_REPLAY` should set `mme_dofRadius` (default 2 is small,
  `tr_mme.c:374`) and `mme_blurOverlap` alongside `mme_blurFrames`.
- No profile asserts `cg_enableAtCommands 1` — a `CVAR_ARCHIVE` cvar that our
  entire `at`-based cfg depends on (§4.1).
- No profile sets `cg_cameraRewindTime`, so any camera playback starts before
  rail trails / marks / smoke have spawned (§1.4).
- `com_timescalesafe` should be pinned to `1` for any servertime-synced path
  (§4.5).

---

## 8. Which q3mme modules wolfcamql did NOT import

For migration scoping. wolfcamql's cgame contains only
`cg_q3mme_demos.c`, `cg_q3mme_demos_camera.c`, `cg_q3mme_demos_capture.c`,
`cg_q3mme_demos_dof.c`, `cg_q3mme_demos_math.c` (+ headers).

| q3mme module | Purpose | In wolfcamql? |
|---|---|---|
| `cg_demos_camera.c` | camera points/splines | ✅ imported (target look-at `#if 0`'d) |
| `cg_demos_dof.c` | DoF keyframes | ✅ imported |
| `cg_demos_capture.c` | capture ranges, project save/load | ✅ imported (partially) |
| `cg_demos_math.c` | quat/spline math | ✅ imported |
| **`cg_demos_line.c`** | **keyframed time remap = native speed ramps** | ❌ **absent** (§4.4) |
| **`cg_demos_script.c`** | timeline script points (`init`/`run` console strings at a demo time) | ❌ absent — but `/at` (§4.1) covers the same ground |
| `cg_demos_effects.c` | in-game effect *editor* | ❌ absent (wolfcamql has its own, larger `cg_fx_scripts.c` instead) |
| `cg_demos_fov.c` | separate fov keyframe track | ❌ absent (fov rides on camera points) |
| `cg_demos_move.c`, `_cut.c`, `_hud.c`, `_lists.c` | editor UI | ❌ absent |
| **`mme_worldShader` / `mme_skykey` / `mme_pip`** | matte + chroma + PiP | ❌ **absent** (§6.2) |
| **`mov_filterMask` / `mov_stencilMask`** | entity filtering + matte | ❌ **absent** (§6.2) |

Conversely, wolfcamql has capabilities q3mme lacks that we already depend on:
protocol-73 / QL demo support, the far richer native camera (§1.1, §5.2), the
expanded FX script language (§3), `mme_dofVisualize`, `runfx`/`runfxat`, and
`/at`. **A migration to q3mme proper would trade §4.4 + §6.2 for all of that.**
That trade is *not* obviously good, and it argues for a third option:
**port the two missing q3mme pieces (`cg_demos_line.c`, the mask/worldShader
cvars) into our wolfcamql fork** rather than migrating wholesale.

---

## 9. Recommended next actions (ordered)

1. **Fix `to_wolfcam_script`** — stop emitting `camera add <args>`; emit a
   `cameras/*.cam10` file plus `loadcamera` / `playcamera`, and drop the
   argument from `playq3mmecamera`. Pin `type = CAMERA_INTERP` (or
   `CAMERA_SPLINE_CATMULLROM`), never `splineBezier`. (§0.1, §1.6)
2. **Add a regression test** that a generated cfg contains no unparseable
   camera command — the current bug survived because nothing asserted the
   grammar against the engine's command table.
3. **Assert the missing cvars** in `master_profile.py`: `cg_enableAtCommands 1`,
   `com_timescalesafe 1`, `cg_cameraRewindTime`, and for
   `_CINEMATIC_REPLAY` also `mme_dofRadius` / `mme_blurOverlap`. (§7)
4. **Correct the `master_profile.py` docstring** on the four points in §7 —
   especially "bezier is not interpolating" and "stencil/mask passes are absent".
5. **Prototype one `pantheon/*.fx` accent** (rail impact) driven by
   `runfxat` at a `hit_anchors.py` servertime, with intensity read from a cvar.
   This is the highest-value/lowest-risk item in the whole workstream. (§3)
6. **Before any `timescale != 1` capture ships**, run the A/V drift audit in
   §4.2 and gate on it the way P1-BB gates.
7. **Move `follow_entity` rigs to `viewType = CAMERA_ANGLES_ENT`** and stop
   baking angles for tracked shots. (§5.2)
8. **Descope GEOMETRY MATCH/MORPH from "engine transition" to "matched-framing +
   post-process flow morph"**, or fund it as a renderer project. (§6.4)
