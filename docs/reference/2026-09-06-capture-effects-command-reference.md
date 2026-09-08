# Capture, camera and effect commands: source reference

Date: 2026-09-06. Scope: 20 useful command/control families, inspected source and primary upstream references. No engine was launched, no cfg executed and no capture made for this document. **Every row is source-confirmed; none is runtime-tested here.**

## Engine boundary

WolfcamQL is the relevant candidate for the existing Quake Live demo pipeline. Its configured capture backend is 11.3 (`creative_suite/engine/wolfcam_capture.py:39`), whereas the canonical source says 12.7test49 (`engine/engines/_canonical/version.txt:1`). Source support in the latter does not establish support in the installed executable or cgame DLL. Preserve both binary hashes in a future visual proof.

Quake III Arena, retail Quake Live, WolfcamQL and q3mme are distinct command environments. Stock Quake III registers `timescale` as a cheat/system-info cvar; that does not imply it includes Wolfcam's scheduler or camera commands. See [id Software's original common.c](https://github.com/id-Software/Quake-III-Arena/blob/master/code/qcommon/common.c). Retail Quake Live command availability was not independently established here; do not copy this table into its console and assume equivalence.

q3mme is a Quake III moviemaking engine modification, identified as 1.9 in its [upstream repository](https://github.com/entdark/q3mme). Wolfcam imports parts of its camera/FX machinery with different entry points. Native q3mme support for this project's protocol-73 input is not established by this audit.

Local citation aliases (repository-relative; exact inspected checkout):

- **W** = `engine/engines/_canonical/code/cgame/cg_consolecmds.c`
- **L** = `engine/engines/_canonical/code/client/cl_main.c`
- **M** = `engine/engines/_canonical/code/cgame/cg_main.c`
- **R** = `engine/engines/_canonical/code/renderergl1/tr_init.c`
- **Q** = `engine/engines/_forks/q3mme/trunk/code/cgame/`

## Useful controls

Commands act during playback unless noted. “Not latched” describes source registration, not a guarantee of visible response in every camera mode.

| # | Environment and exact syntax | Purpose and boundary | Evidence |
|---|---|---|---|
| 1 | Wolfcam: `seekservertime <milliseconds>` | Seek to the document's absolute server timestamp. Keep countdown clocks out of generated schedules. | L:6568–6588 |
| 2 | Wolfcam: `at <server_ms> <command>`; `listat`; `clearat` | Schedule, inspect and reset a shot's commands. `cg_enableAtCommands 1` enables scheduler. Clock strings also exist but are inappropriate as the cross-demo data key. | W:6783–6828, registrations W:8546; M:2460 |
| 3 | Wolfcam: `video avi name <safe_basename>`; `stopvideo` | Begin/end video capture during demo playback. Explicit anonymized basename avoids importing the demo filename into output. | L:6123–6185, L:7174 |
| 4 | Wolfcam: `cl_aviFrameRate 30` | Candidate review capture rate; configure before capture. Registered ARCHIVE, not LATCH. Final mastering is a separate profile. | L:6968 |
| 5 | Wolfcam GL1: `r_mode -1`; `r_customwidth 1280`; `r_customheight 720` | Candidate 720p review viewport. These controls are **LATCHED**: set before renderer initialization or apply via a separately managed renderer restart. Never interpolate resolution. | R:950–961, R:1821–1825 |
| 6 | Wolfcam: `timescale 0.5`; `timescale 1` | Engine-time speed change, affecting simulation playback rather than finished-video resampling. Registered CHEAT/SYSTEMINFO, not LATCH; demo permission and audio behavior require proof. | `_canonical/code/qcommon/common.c:3089` |
| 7 | Wolfcam: `cvarinterp <cvar> <from> <to> <seconds> [real/game]`; `clearcvarinterp` | Continuous ramp. Default clock is game time; `real` uses system milliseconds and can behave differently during offline capture. Do not assume real-clock ramps give deterministic output-frame timing. | W:7244–7298 |
| 8 | Wolfcam: `cg_fov 90` | Live FOV candidate for a zoom ramp, subject to active camera overrides. ARCHIVE, not LATCH. | M:1377 |
| 9 | Wolfcam: `follow <client_slot>`; `follow -1` | Select recorded subject POV / return to demo-taker POV. Slot mapping is demo-local. Cannot reconstruct entities absent from recorded snapshots. | `_canonical/code/cgame/wolfcam_consolecmds.c:169`; W:8471 |
| 10 | Wolfcam: `freecam`; `setviewpos <x> <y> <z>`; `setviewangles <pitch> <yaw> <roll>` | Place a shot explicitly. `freecam` is a toggle, so generated jobs must establish initial mode instead of toggling blindly. | W:560–710 |
| 11 | Wolfcam: `chase <entity> [x_offset] [y_offset] [z_offset] [range] [angle]`; `view <entity> [x_offset] [y_offset] [z_offset]` | Follow an entity or aim at it. Resolve projectile entity and lifetime from the selected time window; entity numbers can be reused. | W:1024–1125 |
| 12 | Wolfcam: `addcamerapoint`; `savecamera <name>`; `loadcamera <name>`; `playcamera`; `stopcamera` | Author/load/play a path. Playback requires at least two points. With `cg_cameraQue` enabled it seeks to first point minus rewind lead; it is **not an unconditional seek**. Canonical camera format is 10, not a promise for 11.3. | W:2183–2237, W:2401–2427; `_canonical/code/cgame/cg_camera.h:7` |
| 13 | Wolfcam: `ecam shifttime <milliseconds>`; `ecam smooth velocity` | Retime selected camera points and author velocity smoothing. Inspect selections before applying; smoothing behavior still needs a visual check. | W:4480, W:5162 |
| 14 | Wolfcam: `entityfreeze <entity>`; `entityfreeze clear` | Toggle a selected entity's frozen state while other action continues. Repeating the entity command unfreezes it. This is not a blanket scene or particle freeze. | W:7055–7095 |
| 15 | Wolfcam: `remapshader <original> <replacement> [time_offset] [keep_lightmap]`; `clearremappedshader <original>` | Live material substitution using existing shader assets. Default keeps original lightmap. Clear takes a shader name; do not invent a blanket reset grammar. | W:7437–7476 |
| 16 | Wolfcam: `fxload [file]`; `runfx <name> [x] [y] [z] [dx] [dy] [dz] [vx] [vy] [vz]` | Load an authored FX definition and invoke it. Schedule `at <ms> runfx ...` to defer resolution to the event. Names must exist in the loaded FX library. | W:6136, W:7661–7730 |
| 17 | Wolfcam: `runfxat <server_ms> <name> [x] [y] [z] ...` | FX-specific scheduler. Omitted position/direction are captured when the command is processed, so pre-seek setup can bind the wrong origin. Prefer explicit event coordinates or deferred `at ... runfx`. | W:7747–7845 |
| 18 | Native q3mme: `capture avi <fps> <name>`; `capture stop`; `capture start`; `capture end`; `capture lock` | Separate capture grammar; start/end define range at current timeline position, lock toggles range locking. Not an alias for Wolfcam `video`. | Q`cg_demos_capture.c:486–543` |
| 19 | Native q3mme: `camera add`; `camera lock`; `camera pos <x> <y> <z>`; `camera angles <pitch> <yaw> <roll>` | Keypoint camera system; lock toggles. Wolfcam uses `q3mmecamera` for its imported system, so do not substitute command prefixes without checking handler. | Q`cg_demos_camera.c:1069–1078`; W:8590 |
| 20 | Native q3mme: `dof focus <distance>`; `dof radius <value>`; `dof add`; `dof lock` | Depth-of-field keypoints. Radius/quality have visual and render-cost consequences. Wolfcam's similarly named imported handler is a separate compatibility proof. | Q`cg_demos_dof.c:581–590`; W:8596 |

Wolfcam's primary [upstream README](https://github.com/brugal/wolfcamql/blob/master/README-wolfcam.txt) independently documents FX loading and explicit/implicit origins for `runfx` and `runfxat`. Local handler behavior above is the reference for this checkout.

## Minimal templates for a future single-shot proof

Illustrative only: replace bracketed values from the reviewed demo ledger before use. These were not executed. Keep generated user strings restricted and reject semicolons/newlines in filenames or other substituted arguments. Execute through the existing single-worker capture lifecycle, which owns cancellation and output paths.

Review setup, before renderer initialization:

```cfg
r_mode -1
r_customwidth 1280
r_customheight 720
cl_aviFrameRate 30
```

The pixel-frame workload of 720p30 is 2/9 of 1080p60, an arithmetic comparison, **not a measured generation speedup**. I/O, codec, simulation and FX costs remain. Preserve full round duration and use no expensive experimental FX in the first review pass.

Post-initialization bounded playback, matching the existing `cgamepostinit.cfg` approach:

```cfg
clearat
clearcvarinterp
cg_enableAtCommands 1
timescale 1
follow <subject_slot>
seekservertime <guard_start_ms>
at <round_start_ms> video avi name review_round_001
at <round_end_ms> stopvideo
```

Worker cleanup must still stop the process; this template intentionally does not make `quit` a second same-timestamp command whose ordering would need proof. Include lead-in sufficient for sound/particles and schedule only after demo initialization.

Event-local zoom candidate, separate from the plain review proof:

```cfg
at <effect_in_ms> cvarinterp cg_fov 90 75 0.15 game
at <effect_out_ms> cvarinterp cg_fov 75 90 0.15 game
```

These timestamps and FOV values are illustrative creative choices, not a recommendation to apply a zoom to every event. Existing camera FOV overrides must be accounted for. Speed ramps, stutter and repeats require a documented mapping from server time to output time; the raw action ledger must remain unmodified.

## Corrections and proof requirements

- Older `wolfcam-commands.md` specifies cvar interpolation milliseconds. Handler W:7252 and W:7283–7286 establish **seconds**. A value of `2000` does not mean a two-second ramp.
- Older `engine_moviemaking_commands.md` describes `nextframe`/`prevframe` as demo stepping. W:8416 binds `nextframe` to `CG_TestModelNextFrame_f`; `_canonical/code/cgame/cg_view.c:129` increments the test model frame. This is a model-animation debug control, not a demo frame-step primitive.
- Neither successful `set` of a new variable nor presence in a source table proves the binary implements a visual effect. Confirm executable/DLL identity, runtime command listing, then one on/off frame pair with the same demo, timestamp and POV.
- `entityfilter` does not hide BSP geometry. `entityfreeze` does not establish a bullet-time scene. Camera travel does not recover unseen world state. Keep requested visual intent separate from the verified primitive.
- Store each approved effect with input demo checksum, server-time window, command file checksum, engine/DLL hashes, baseline and treated frame, output frame timestamp, and the actual result. Reference those proof records from future demos; revalidate when engine or renderer changes.

This document complements `2026-09-05-wolfcam-command-verification.md`; it does not upgrade source-only candidates to runtime-proven capabilities.

## Subsequent bounded runtime proof

The DEMO509 audit subsequently ran the installed capture path for one round using `seekservertime`, `at`, `video avi`, `stopvideo` and `quit` through the existing adapter. It produced a playable 1280×720/30fps MP4, with three observed outcome frames. See [the recorded evidence](demo509/source-of-truth.md#rendered-round-6-proof) for binary hashes and limits. This spot-check does not validate the other camera, interpolation, animation or FX commands listed above.
