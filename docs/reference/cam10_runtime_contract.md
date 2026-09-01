# `.cam10` runtime contract — source-verified (2026-09-01)

Traced directly in `engine/engines/_canonical/code/cgame/` (this tree IS the
wolfcamql source — confirmed by the project-audit dedup manifest; the
`replay-runtime-feasibility.md` reference to a separate empty
`wolfcamql-src/` was wrong and is corrected there). This supersedes the
prior research-agent prose on `to_wolfcam_script()` — every claim below is
a direct read of the implementation, not a summary of documentation.

## Why the old output was a no-op

`creative_suite/engine/timeline.py` emitted `camera add <8 numbers>` and
`at <t> playq3mmecamera`. Neither works on the engine we run:

- The registered command is **`playcamera`** (`cg_consolecmds.c:8512`), not
  `playq3mmecamera` (that name belongs to a different, q3mme-specific
  command — `cg_consolecmds.c:8590` — which is not what our `wolfcam_cmd`
  launch path uses).
- **`camera add` takes no positional arguments in this engine.** There is
  no such registered command that parses 8 floats; the closest verb,
  `camera`, is a snapshot/edit command family (`cg_consolecmds.c:1856` area)
  operating on the CURRENT view, not a path loader.
- Even a correctly-named `playcamera` does nothing by itself — see the gate
  below.

## The three real commands

| Command | Handler | Registration |
|---|---|---|
| `savecamera <name>` | `CG_SaveCamera_f` | `cg_consolecmds.c:2226`, bound `:8514` |
| `loadcamera <name>` | `CG_LoadCamera_f` | `cg_consolecmds.c:2401`, bound `:8516` |
| `playcamera` | `CG_PlayCamera_f` | `cg_consolecmds.c:2183`, bound `:8512` |

## File location and naming

`cameras/<name>.cam<VERSION>` inside the game dir's search path (writer:
`cg_consolecmds.c:2255`; reader: `:2427`, with a fallback to
`VERSION - 1` at `:2429` if the exact version isn't found).
`WOLFCAM_CAMERA_VERSION` is `10` (`cg_camera.h:7`) — hence `.cam10`. A
name containing `/` is treated as a full path relative to the game dir
instead of `cameras/`.

## File grammar — exact, line-positional, NOT label-parsed

`CG_LoadCamera_f` (`cg_consolecmds.c:2401-2596`) reads every field with
`CG_FS_ReadLine` + `sscanf` on the line's LEADING tokens only. **The
trailing text after each value (`"  origin"`, `"  angles"`, etc.) is a
human-readable comment the parser never looks at** — only line position
and value count matter. A writer must reproduce the exact line sequence
`CG_SaveCamera_f` (`:2226-2331`) produces, or the reader desyncs silently
(no per-field validation — a missing line shifts every subsequent field).

Header line (read once, before any point):
```
WolfcamCamera 10
```

Per camera point, in this exact order (all versions we write are 10, so
every version-gated branch below takes the "yes" path):

| # | Line format | Field | Type |
|---|---|---|---|
| 1 | `%d` | (point index — value ignored on read, line only consumed) | int |
| 2 | `%f %f %f` | origin (x y z) | float |
| 3 | `%f %f %f` | angles (pitch yaw roll) | float |
| 4 | `%d` | type | int, see enum below |
| 5 | `%d` | viewType | int |
| 6 | `%d` | rollType | int |
| 7 | `%d` | flags | int, bitmask — **only present for version > 8**; we always write it |
| 8 | `%lf` | cgtime | double, **milliseconds**, same clock as `cg.time`/demo serverTime |
| 9 | `%d` | splineType | int |
| 10 | `%d` | numSplines | int |
| 11 | `%f %f %f` | viewPointOrigin | float |
| 12 | `%d` | viewPointOriginSet | bool-as-int |
| 13 | `%d` | viewEnt | int |
| 14 | `%f %f %f` | viewEntStartingOrigin | float |
| 15 | `%d` | viewEntStartingOriginSet | bool-as-int |
| 16 | `%d` | offsetType | int |
| 17 | `%lf` | xoffset | double |
| 18 | `%lf` | yoffset | double |
| 19 | `%lf` | zoffset | double |
| 20 | `%lf` | fov | double |
| 21 | `%d` | fovType | int |
| — | *(version < 10 only: 2 dead lines for a removed `timescale` field — we never write these)* | | |
| 22-24 | `%d`,`%lf`,`%lf` | useOriginVelocity, originInitialVelocity, originFinalVelocity | (version > 7, always for us) |
| 25-27 | same shape | angles velocity triple | |
| 28-30 | same shape | xoffset velocity triple | |
| 31-33 | same shape | yoffset velocity triple | |
| 34-36 | same shape | zoffset velocity triple | |
| 37-39 | same shape | fov velocity triple | |
| 40-42 | same shape | roll velocity triple | |
| 43 | `%d` | commandStrLen | int — if > 0, exactly that many RAW bytes follow with no added newline, read via `trap_FS_Read` (not line-based) |
| 44 | *(blank line)* | | |
| 45 | `-------------------------------------` | | (unparsed separator) |

We always write `commandStrLen 0` (no per-point console command) and
therefore write lines 44-45 as the literal two-line block
`"\n-------------------------------------\n"` immediately after line 43,
exactly matching `CG_SaveCamera_f`'s unconditional trailer write.

## Type enums (`cg_camera.h:61-112`)

```
type      (CAMERA_SPLINE=0, CAMERA_INTERP=1, CAMERA_JUMP=2, CAMERA_CURVE=3,
           CAMERA_SPLINE_BEZIER=4, CAMERA_SPLINE_CATMULLROM=5)
viewType  (CAMERA_ANGLES_INTERP=0, ..._INTERP_USE_PREVIOUS=1, _FIXED=2,
           _FIXED_USE_PREVIOUS=3, _ENT=4, _VIEWPOINT_INTERP=5,
           _VIEWPOINT_PASS=6, _VIEWPOINT_FIXED=7, _SPLINE=8)
rollType  (CAMERA_ROLL_INTERP=0, _FIXED=1, _PASS=2, _AS_ANGLES=3)
fovType   (CAMERA_FOV_USE_CURRENT=0, _INTERP=1, _FIXED=2, _PASS=3, _SPLINE=4)
flags     bitmask: CAM_ORIGIN=0x001, CAM_ANGLES=0x002, CAM_FOV=0x004,
                   CAM_TIME=0x100
```

## Our chosen configuration, and why (verified against playback code)

Playback for `type=CAMERA_INTERP` (`cg_view.c:3137-3178`) is a **plain
piecewise-linear interpolation directly between two consecutive points'
raw `origin` fields**, parameterized by
`f = (cg.ftime - cp->cgtime) / (cpnext->cgtime - cp->cgtime)` — it visits
every keyframe's exact position at its exact `cgtime`, with no spline
fitting. This is the deterministic, keyframe-exact behavior we want; the
spline types (`CAMERA_SPLINE*`) route through `CG_CameraSplineOriginAt`
(`cg_camera.c:177`), which for `posBezier` is confirmed (by a sibling
research pass this session) to be a **non-interpolating uniform B-spline
approximation** — it does not reliably pass through keyframes and is
explicitly NOT used here.

`viewType=CAMERA_ANGLES_INTERP` (`cg_view.c:3453`) and
`fovType=CAMERA_FOV_INTERP` (`cg_view.c:4004`) are the direct angle/FOV
analogs — same linear-between-keyframes behavior, confirmed by reading
both call sites. `rollType=CAMERA_ROLL_AS_ANGLES` takes roll straight
from `angles[2]` with no cross-point matching logic — appropriate since
our keyframes always compute roll=0 and we want that value used directly,
not reinterpreted.

`flags = CAM_ORIGIN | CAM_ANGLES | CAM_FOV | CAM_TIME` (`0x107`) is set on
**every** point. `cg_camera.c`'s `wolfcamCameraPointMatch`/
`wolfcamCameraMatchAt` walk forward/backward for the nearest point with a
given flag bit set — setting all three data bits on every point means
every point is always its own anchor; no gap-filling/masking logic is
ever exercised (that logic exists to let sparse point sets share data
across points, which we never need to rely on).

## The gate the earlier research pass missed

**`cg_view.c:3092-3094`: `if (!cg.freecam) { return qtrue; }`.** The
entire origin/angle/fov path-sampling block — everything described
above — is skipped unless `cg.freecam` is active, REGARDLESS of whether
`playcamera` was called and a path is loaded. `playcamera` alone, without
`freecam`, changes internal camera-playback state (`cg.cameraPlaying`,
`cg.currentCameraPoint`) but **never touches `cg.refdef.vieworg`**. This
was found by reading the enclosing function, not by reading the isolated
playback snippet — exactly the kind of miss "trace the source, not the
prose" is meant to catch.

## Known engine bug: `playcamera` corrupts the snapshot stream

The sequence documented in the previous section — `seekservertime` /
`freecam` / `loadcamera <name>` / `playcamera` — is what a correct
reading of the source says SHOULD work, and `loadcamera` does work
(`qconsole.log` prints `camera loaded (version 10)` and the file parses
without error). But **`playcamera` itself reproducibly hangs the demo**:
`processsnapshots() couldn't get nextsnap <N>` repeats forever at a fixed
point and every subsequently-scheduled `at` command (`stopvideo`, `quit`,
even a bare `echo`) never fires again.

Root cause, traced in `cg_view.c:3005-3018`: the first per-frame update
after `playcamera` is issued runs

```c
if (cg.playCameraCommandIssued) {
    ...
    extraTime = 1000.0 * cg_cameraRewindTime.value;   // 0 by default
    trap_SendConsoleCommand(va("seekservertime %f\n", cp->cgtime - extraTime));
    ...
    return qfalse;
}
```

**unconditionally** — this is a SEPARATE internal auto-seek from the one
gated by `cg_cameraQue` inside `CG_PlayCamera_f` itself, and it fires
every time regardless of that cvar. Reproduced identically across 6
variants on 2026-09-01: with/without our own pre-seek, with/without
`cg_cameraQue 0`, with the `freecam`/`loadcamera`/`playcamera` block
issued instantly vs. deferred via `at`, and with a >2 minute timeout to
rule out "just slow." Every variant stalls at the exact same point
(`processsnapshots()` waiting on snapshot 76689, game-clock `1:59`,
regardless of the actual seek target used across different keyframe
sets) — `loadcamera` alone (no `playcamera`) does not stall. This is a
genuine defect in the shipped wolfcamql binary/source, not a usage error;
fixing it would mean patching and rebuilding the engine (Path C
territory), not a cfg change.

## Correct — and runtime-proven — capture command sequence

Given the above, camera paths are executed with `freecamsetpos`
(`CG_SetViewPos_f`, `cg_consolecmds.c:673`, registered as both
`setviewpos` and `freecamsetpos`) instead of `loadcamera`/`playcamera`:
a simple, argument-taking command with no internal re-seek of any kind.

```
seekservertime <first_keyframe_ms - settle_ms>
freecam
at <t0> freecamsetpos <x> <y> <z> <pitch> <yaw> <roll>
at <t1> freecamsetpos <x> <y> <z> <pitch> <yaw> <roll>
... one per keyframe ...
```
then the existing `video`/`at <end> stopvideo` capture wrapping. Every
primitive here (`seekservertime`, `at`, `freecam`, `freecamsetpos`) was
already independently proven reliable elsewhere in this codebase before
this fix; none of it depends on the buggy `playcamera` internal re-seek.

**Runtime-proven, 2026-09-01**: a compiled 9-keyframe, 180°, 4-second
orbit was captured end-to-end (real demo, real wolfcam session, real AVI)
and two frames 2.4s apart showed completely different, correctly
rendered world geometry — confirmed real camera motion, not a static
shot or a silent no-op. `creative_suite/engine/cam10_writer.py`'s
`compile_camera()` emits this sequence via `to_freecamsetpos_lines()`.

The `.cam10` file is still written and hashed by `compile_camera()` — it
remains a correct, portable, versioned representation of the path
(verified byte-for-byte against the real grammar, see
`test_cam10_writer.py`), useful for archival, for round-tripping a human-
flown `savecamera` recording, or once `playcamera` is patched via a
future Path C engine fix. It is simply not what drives execution today.

## What still works from the old output (unaffected by this fix)

The `at <t> timescale <v>` / `at <t> cg_fov <v>` / `at <t> cl_freezeDemo
<0|1>` lines were never camera-path-dependent and are confirmed real,
registered, working commands — `to_wolfcam_script()` keeps emitting them
unchanged.

## Compiler versioning

- `camera_compiler_version = "cam10-v1"` — this writer, this document's
  grammar.
- `camera_runtime_backend = "wolfcamql-cam10"` — identifies which engine
  command surface the artifact targets (distinct from a hypothetical
  future q3mme-native `.cam10`-adjacent backend, since q3mme's own
  camera commands differ — noted in `q3mme_cinematic_audit.md`).
- Tracked per-compilation in `cinematic.db`'s `camera_compilations` table
  (plan_id, compiler_version, file_hash, runtime_backend, compiled_utc) —
  separate from `shot_plans`, so compiling (or recompiling under a new
  compiler version) never changes a plan's identity hash. SceneRecipe
  intent and compiled execution artifact are tracked independently.
