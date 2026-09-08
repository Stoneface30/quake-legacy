# PANTHEON owns the engine — the cgame layer links

2026-09-08. The goal is one homemade engine that takes the best of every
source tree, improves it, and belongs to us. This records how far that is,
measured rather than estimated.

## What was already true

`pantheon_frame.exe` links wolfcam's **actual renderer** — 28 `tr_*` objects,
35,620 lines — into our own host, with our own WGL init, our own actor
placement and our own frame writer. It draws real BSP with lightmaps and real
MD3 actors, and re-derives a recorded camera to 0.0000 units of error.

What it could not draw was everything cgame draws: rockets, rail trails,
explosions, blood, marks, muzzle flashes, item spin, powerup shells, the HUD.

## What changed today

**The renderer runs on the GPU.** The belief that the NVIDIA driver kills it
during `R_Init` does not reproduce:

    GL_VENDOR:   NVIDIA Corporation
    GL_RENDERER: NVIDIA GeForce RTX 5060 Ti/PCIe/SSE2
    GL_VERSION:  4.6.0 NVIDIA 610.88
    ----- finished R_Init -----

Its `PANTHEON_GetProcAddress` already handled the `wglGetProcAddress`
NULL-and-sentinel problem correctly, so that was never the fault either.
1920x1080 in ~1.9 s per frame, and that is a fresh process per frame -- most
of it is BSP and texture load, not drawing.

**And the whole cgame links.** Measured, not guessed:

| | |
|---|---|
| cgame files that compile unmodified | **43 of 44** |
| the 44th | `cg_particles.c`, which calls `trap_R_AddPolyToScene` with three arguments where it takes four. Upstream does not build it either -- Q3 legacy that has rotted |
| external symbols after compiling | 133 |
| ...already defined by the PANTHEON host | 61 |
| ...libc and Win32 | ~47, free from the C runtime |
| ...genuinely needed | **~25**, all in `ui/ui_shared.c`, already in the tree |
| link errors after adding it | **0** |
| binary | 1.0 MB -> **2.2 MB**, 658 `CG_*` symbols |

Two collisions had to be resolved, both trivial: our redundant
`q_math`/`q_shared`, and cgame's own `Com_Printf`/`Com_Error` -- which exist
because a VM has no host to call, and which the host's versions should win.

Reproducible: `engine/pantheon_renderer/build_cgame.sh`.

## What this settles, and what it does not

**Settles:** there is no missing code. The gap between PANTHEON and everything
WolfcamQL draws was never something to author -- it was something to link. The
source has been in the tree the whole time.

**Does not settle:** cgame is linked but **not called**. Nothing invokes
`CG_Init` or `CG_DrawActiveFrame`, and the host feeds it no snapshots. The
`trap_*` layer in `cg_syscalls.c` still routes through the VM `syscall`
dispatcher, which in a static link must become direct calls.

So the remaining work is WIRING, not writing:

1. Replace `cg_syscalls.c`'s `syscall()` dispatch with direct calls into the
   host. The host side is already written -- `client/cl_cgame.c` implements
   **145 syscalls in 1,927 lines**, and it is in the tree.
2. Feed `cg.snap` / `cg.nextSnap` from **FrameTruth** rather than from
   wolfcam's client. This is the part that makes PANTHEON better than what it
   borrowed from: wolfcam PLAYS a demo, PANTHEON would COMPOSE one. Camera
   anywhere, entities we choose, moments no recording contains.
3. Drive `CG_DrawActiveFrame(serverTime, ...)` per frame.

## The rule this supersedes

Rule **HL-4** says "do not reimplement the Quake renderer to remove Wolfcam",
on the grounds that "replacing the rasterizer buys no truth". That was written
when the renderer was stuck on a CPU rasteriser at 0.67 s/frame and the effort
looked unbounded.

Neither premise holds now. Nothing is being reimplemented -- the code is
linked, not rewritten -- and the renderer is on the GPU. HL-4 should be
rewritten to say what is actually true: **do not AUTHOR what the source
already contains; link it, own it, then improve it.**


---

## Update: the seam is built

`engine/pantheon_renderer/host/pantheon_cg_syscall.c`.

WolfcamQL compiles cgame to a DLL and reaches it through a virtual machine.
Every `trap_` call marshals its arguments into `syscall()`, which the client
dispatches in `CL_CgameSystemCalls`. PANTHEON links cgame **statically**:
there is no VM, no DLL and no address translation, so the `VMA()` macro that
existed to translate VM addresses becomes a plain cast.

`cg_syscalls.c` is kept **exactly as upstream wrote it**. This file supplies
the one function it calls.

    660  CG_*    symbols   (cgame itself)
    134  trap_*  symbols   (upstream's wrappers, untouched)
      1  syscall dispatcher (ours)

One binary, 2.2 MB, and it still renders: 3,329 faces, 1280x720, on the GPU.

### What is implemented, and what stops loudly

Implemented by copying `cl_cgame.c` verbatim where the mapping is mechanical:
console and time, cvars, command args, files, the whole collision model, and
the renderer -- `LoadWorld`, `RegisterModel/Skin/Shader`, `ClearScene`,
`AddRefEntityToScene`, `AddPolyToScene`, `AddLightToScene`, `RenderScene`,
`SetColor`, `DrawStretchPic`, `ModelBounds`, `LerpTag`, `MarkFragments`,
`RemapShader`. Three signatures had drifted from what cgame calls and were
corrected against `cl_cgame.c` rather than guessed: `Com_RealTime`,
`Q_SnapVector`, `RemapShader`.

**Sound is counted, not silently dropped.** PANTHEON links no mixer -- a still
frame has nothing to play and the mixer drags in the whole client -- so the
eight sound syscalls increment `PANTHEON_CG_SoundCallCount()`. "cgame asked
for sound N times" is a fact we can report; silence is not.

**Everything else calls `Com_Error` with its own syscall number.** Returning 0
from an unknown syscall is how an engine draws a frame quietly missing a third
of its content, and this project has been bitten by silent no-ops repeatedly:
a cvar accepted and never registered, a capture exiting rc=0 having written
nothing. A missing syscall here stops loudly and names itself, so the next
piece of work is never a guess.

### Still not called

`CG_Init` and `CG_DrawActiveFrame` are linked and now *callable*, but the host
does not yet invoke them, and cgame is fed no gamestate and no snapshots.
That is the next step, and it is the interesting one: `cg.snap` comes from
**FrameTruth**, not from a demo player. Wolfcam PLAYS a recording; PANTHEON
composes one.
