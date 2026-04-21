# q3mme — Architecture

**Upstream:** https://github.com/entdark/q3mme (shallow clone, 70 MB)
**Role:** Movie-maker engine. **Tr4sH Quake port target** — proto-73 merges INTO q3mme.
**Canonical copy:** `engine/engines/_canonical/` + per-tree variants.

## What it is

Quake 3 Movie Maker's Edition. A fork of ioquake3 with an entire **demo-editing and
cinematography subsystem** on top of normal Q3 playback:
- Camera path scripting (splines, keyframes)
- Motion blur via accumulation buffer (temporal sampling)
- Depth-of-field rendering
- Dynamic FOV animation
- HUD visibility scripting
- Demo cut/trim (virtual demos that reference ranges of real demos)
- Multi-pass rendering for high-quality still frames

## Module map

```
trunk/code/
├── qcommon/     — baseline Q3 common, minor q3mme tweaks
├── client/      — demo load, render, input — LIGHTLY touched
├── server/      — full Q3 server, unmodified
├── cgame/       — THIS IS WHERE Q3MME LIVES
│   cg_demos.c, cg_demos.h              — core demo scripting state machine
│   cg_demos_camera.c                   — camera path splines, keyframes
│   cg_demos_capture.c                  — multi-sample frame capture, motion blur
│   cg_demos_cut.c                      — virtual demos (cut out time ranges)
│   cg_demos_dof.c                      — depth-of-field
│   cg_demos_effects.c                  — per-demo visual effect scripts
│   cg_demos_fov.c                      — FOV animation
│   cg_demos_hud.c                      — HUD visibility scripting
│   cg_demos_line.c                     — line entities (debug viz)
│   cg_demos_script.c                   — high-level script language
│   cg_demos_save.c                     — save/load demo scripts
│   cg_demos_zoom.c                     — zoom effects
│   cg_*.c (standard Q3)                — draw, event, players, weapons, main
├── renderer/    — ioquake3 renderer with motion blur accumulation hooks
└── botlib/, game/, ui/ — unused at runtime (playback-focused)
```

## How demo playback works in q3mme

Unlike wolfcam (which gutted the server), q3mme keeps Q3's full client/server with
`com_dedicated 0` for loopback. The demo subsystem runs on top as an **overlay**:

1. Normal demo playback via `CL_PlayDemo_f` — same as ioquake3
2. When the user enters demo-edit mode (`demos` console command), `cg_demos.c`
   takes over the `CG_DrawActiveFrame` path
3. During playback, the **play position is scrubbed** via `demoPlay` (play/pause/seek)
   and `demoTimeLine` (t-along-demo)
4. Camera comes from `cg_demos_camera.c` instead of the first-person view
5. Frame capture pulls N subframes per output frame (via `demoCaptureStage`) and
   accumulates them for motion blur

## Entry points

- **Demo-edit mode toggle:** `/demos` console command → `CG_DemosEnter` in cg_demos.c
- **Camera keyframe:** `/demos camera add` → `demoCameraSmoothPos/Angles`
- **Capture start:** `/demos capture start` → `demoCaptureStart` with sampling config
- **Script load:** `/demos save/load <name>` → `demoSaveCmds` / `demoLoadCmds`

## Core data structures

```c
// cg_demos.h
demoMain_t demo = {
    .play       = { state: DP_PLAY, time: ..., speed: 1.0 },
    .camera     = { pos[], angles[], fov, points: demoCameraPoint_t*, ... },
    .capture    = { active, startTime, endTime, fps, sampleCount, motionBlur },
    .dof        = { active, focus, radius, fov },
    .fov        = { active, points: demoFovPoint_t* },
    .hud        = { active, cg_draw*, points },
    .line       = ..., .script = ..., .cut = ...
};
```

Each subsystem has its own "points" array — timeline-indexed keyframes that get
interpolated at playback time via splines (Catmull-Rom by default).

## Rendering pipeline extensions

- **Motion blur:** `cg_demos_capture.c::CG_DemosCaptureFrame` renders N subframes
  per output frame, each at offset `capture.shutterTime * i / N` within the output
  frame window. Accumulates via `glAccum(GL_ACCUM, 1.0/N)` and reads via `glAccum(GL_RETURN, 1.0)`.
- **DOF:** `cg_demos_dof.c` renders multiple passes with jittered view positions
  around the focal point, accumulates like motion blur.
- **Multi-sample AA:** combined with motion blur → 16-32 subframes for offline quality.

## Build system

- Makefile-driven. Top-level `Makefile` in `trunk/`.
- Output: `trunk/build/release-<platform>-<arch>/q3mme.<ext>`
- MSYS2 + MinGW-w64 on Windows (same as wolfcam)
- Bundled q3lcc / q3asm for VM compilation (required even if running native cgame)

## Why q3mme is the target for Tr4sH Quake

1. **Cinematography is already there.** Camera splines, motion blur, DOF — all features
   the fragmovie pipeline needs. Wolfcam has none of this.
2. **Modern-ish codebase.** Based on a later ioquake3 than wolfcam's base. Easier to
   port proto-73 IN than to port q3mme features OUT.
3. **Active movie-maker community.** If we land a clean dm_73 patch, upstream
   would likely take it. Wolfcam is unmaintained.
4. **Clean renderer.** Q3mme's renderer is ioquake3-stock + accumulation hooks. Easy
   to swap to quake3e's Vulkan backend later.

## Merge strategy with wolfcamql

See `_diffs/code/qcommon/` and `_diffs/code/client/cl_parse.c.diff.md` for exact file-
level diffs. High-level:

- **qcommon/**: take wolfcam's msg.c + q_shared.h + cl_parse.c deltas, drop into q3mme
- **cgame/**: KEEP q3mme's cg_demos_*.c UNTOUCHED; ADD wolfcam_*.c files as new modules;
  namespace conflicts resolve by prefixing wolfcam's to `wolfcam_*` (already done)
- **client/**: cl_demo.c + cl_parse.c get proto-73 paths added to ioquake3's logic

## Gotchas during port

- q3mme's `entityState_t` is ioquake3-baseline; wolfcam added fields — match exactly
- q3mme uses VM cgame by default; wolfcam prefers native — build system flag differs
- q3mme has `cg_drawAttacker` behavior wolfcam changed — pick one
- q3mme's accumulation buffer assumes 8-bit per channel; 1080p60 with 16-sample
  motion blur is already at precision limit. For 4K work we'll need HDR buffers.
