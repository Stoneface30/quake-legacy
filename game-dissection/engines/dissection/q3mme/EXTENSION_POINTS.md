# q3mme — Extension Points

## Camera scripting API

**Location:** `trunk/code/cgame/cg_demos_camera.c`

Public-ish functions (invoked from the `demos` console command dispatcher):
- `demoCameraCommand` — parses `/demos camera <subcmd>` and dispatches
- `demoCameraAdd/Del/Clear` — keyframe management
- `demoCameraSetAngles/Origin/Fov` — per-keyframe property setters
- `demoCameraSmoothPos/Angles` — spline interpolation at time t

**Adding a new camera effect (e.g. "follow target" mode):**
1. Add a camera type enum in `cg_demos.h::demoCameraType_t`
2. Add a branch in `demoCameraInterpolate` that computes pos/angles for your type
3. Add command parsing in `demoCameraCommand` for `/demos camera follow <entity>`

## Capture API

**Location:** `trunk/code/cgame/cg_demos_capture.c`

- `/demos capture start` — begin capture with current settings
- `/demos capture stop`  — end capture
- `/demos capture config <key> <val>` — set fps, sampleCount, motionBlur, output format

**Hook for external encoder (Tr4sH Quake goal):**
Replace `demoCaptureFlushFrame` (which currently writes TGA/PNG/AVI) with a
pipe-to-ffmpeg: write raw RGB24 to stdin of a pre-spawned ffmpeg child.
Drop-in: only this one function changes.

## Script language

**Location:** `trunk/code/cgame/cg_demos_script.c`

q3mme has a higher-level script language on top of the `/demos` commands — loads
from `.demoscript` files. Syntax:
```
camera add 0 origin 100 0 50 angles 0 0 0 fov 90
camera add 1000 origin 200 0 50 angles 45 0 0 fov 60
capture start
capture stop
```

**For Tr4sH Quake automation:** emit these scripts from our Python pipeline and
load with `/demos load <name>`. This is the cleanest automation surface — no
keyboard/mouse scripting, no IPC, just text files.

## Cut-demo (virtual demos)

**Location:** `trunk/code/cgame/cg_demos_cut.c`

Define time ranges inside a demo that become a "virtual demo" — playback concats
the ranges seamlessly.

**Relevance:** this is exactly the FFmpeg concat-demuxer approach we use in phase1,
but at the demo level. Potential replacement for the full_length-clip path: cut
the interesting second out of the demo with q3mme, render once, done.

## DOF / FOV / HUD scripting

Each has a `/demos <subsys>` command with keyframe API identical to camera.
Timeline-indexed arrays interpolated at playback.

## Effects scripting

**Location:** `trunk/code/cgame/cg_demos_effects.c`

Per-demo visual effect state changes (e.g. "at t=5s, turn on bloom; at t=8s,
change rail color"). Lightweight; uses the cvar system with timeline entries.

**Relevance:** STYLE PACK RULE ENG-2 — `zzz_*.pk3` packs override baseq3 textures
for whole-demo re-skinning. But for per-moment effects (rocket trails change color
mid-frag), this effects system is the right hook.

## VM trap surface

**Location:** `trunk/code/cgame/cg_syscalls.c`

Standard Q3 trap_ calls plus q3mme additions:
- `trap_R_ClearScene`, `trap_R_AddPolyToScene` — used by camera path viz
- `trap_GetUserCmd` normally demo-only; q3mme uses it for edit-mode input
- No proto-73 specific traps needed here — those live in qcommon/

## Cvars to know

- `cg_demoMoveSpeed` — edit-mode free-cam speed
- `mme_saveShot` — TGA/PNG/JPG output format for capture
- `mme_saveWav` — capture audio to separate .wav
- `mme_motionBlur` — master motion blur toggle
- `mme_motionBlurFrames` — subframes per output frame (8-32 typical)
- `mme_dofFrames` — DOF sample count
- `mme_aviLimit` — AVI file size split point (bytes)

## Adding our proto-73 patches (the PORT)

1. In `qcommon/msg.c`: splice wolfcam's field tables. Use `_diffs/code/qcommon/msg.c.diff.md`
2. In `client/cl_parse.c`: add proto-73 branches. Conditional on `clc.serverProtocol == 73`
3. In `cgame/`: add wolfcam_*.c files as new sources, register via Makefile CGOBJ list
4. In `Makefile`: add new CGOBJ entries, bump VERSION to mark our fork

No changes to q3mme's cg_demos_*.c required — those are protocol-agnostic.
