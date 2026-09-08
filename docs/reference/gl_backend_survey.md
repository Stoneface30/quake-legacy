# Which renderer can this engine actually use?

Surveyed 2026-09-08, because every offscreen capture runs at about **half a
frame per second** and that makes the pipeline impractical: a complete 2.5 s
clip costs ~10 minutes, so a 120-clip Part is ~20 hours of pure capture.

The engine is `wolfcamql 11.3 win_mingw-x86`, built **Aug 2016**. 32-bit,
fixed-function OpenGL 1.x, SDL 1.2 with the `windib` video driver.

## The result

| Driver | Outcome | Evidence |
|---|---|---|
| **`softpipe`** (in use) | works | Mesa reference rasteriser, single-threaded. `GL_RENDERER: softpipe`. ~0.5 written frames/sec at 1080p |
| **`llvmpipe`** | **not present** | Absent from `libgallium_wgl.dll`. This is the **MinGW x86** Mesa build, which ships without LLVM. The MSVC x86 package has it |
| **`d3d12`** | fails | `SDL_SetVideoMode failed: No matching GL pixel format available` for every mode and bpp, then `Couldn't get a visual`, then `Com_Error(): GLimp_Init() - could not load OpenGL subsystem`. Unchanged by dropping stencil, multisample, or FBO. Hangs to the 150 s timeout every time |
| **`zink`** | crashes | Log stops dead after `...setting mode -1: 1280 720` at 430 bytes. The process dies without writing an error |
| **NVIDIA native** | crashes | Access violation during `R_Init`, previously recorded |

Artefacts: `docs/visual-record/2026-09-08/gl_driver/`.

## Two things this settles

**The hidden desktop is innocent.** `d3d12` was also run on the ordinary
interactive desktop and failed identically. A `CreateDesktopW` desktop is a
plausible way to lose hardware acceleration, but it is not what is happening
here.

**Absence of a failure marker is not success.** The first pass scored zink as
working because the string `Couldn't get a visual` was missing from its log.
It was missing because the process died before it could be written. The check
was rewritten to require a positive signal. This is the third time today a
measurement reported nothing where a direct look answered immediately.

## What d3d12's failure actually means

SDL 1.2 asks `ChoosePixelFormat` for a visual built from the engine's colour,
depth, stencil and multisample bits. Mesa's d3d12 WGL layer advertises nothing
matching, for **any** of the sixteen combinations the engine tries. Relaxing
the request did not help, so this is not one stubborn attribute — the d3d12
WGL frontend and SDL 1.2's windib path do not meet.

## The one route not yet tried

**Mesa MSVC x86, for `llvmpipe`.** It is multithreaded and JIT-compiled where
softpipe is a single-threaded reference implementation; Mesa's own
documentation calls llvmpipe "the fastest software rasterizer". With 8 cores
the expectation is roughly **10-30x** over softpipe — which would take a
complete 2.5 s clip from ~10 minutes to well under one.

That is still software rendering. It does not make the GPU do the work, and it
does not fix the NVIDIA crash. It would make the pipeline usable while the
real fix is investigated.

**It requires downloading a third-party binary distribution**, so it is an
operator decision rather than something to do unasked.

## The real fix, and where the evidence points

The prime suspect for the NVIDIA crash is how GL entry points are resolved.
`wglGetProcAddress` is **documented** to return NULL for OpenGL 1.1 core
functions — which is exactly `glColor4f`, `glColor3f`, `glNormal3f`, the three
that fault. Those must come from `GetProcAddress` on `opengl32.dll`. SDL 1.2's
`SDL_GL_GetProcAddress` on Win32 uses `wglGetProcAddress` **without** a
fallback; SDL2 added one, SDL 1.2 never did. Mesa's WGL frontend resolves core
1.1 entry points anyway, which is why the same code works on Mesa and faults
on NVIDIA.

Original id Quake 3 used `GetProcAddress` directly
(`win_qgl.c`: `#define GPA(a) GetProcAddress(glw_state.hinstOpenGL, a)`).
ioquake3's SDL port replaced that with `SDL_GL_GetProcAddress`. That
substitution is where this class of bug enters the id Tech 3 lineage.

Note that stock ioquake3 NULL-checks each resolved pointer and errors cleanly,
so an unchecked pointer is the signature of a **custom host**, not of
WolfcamQL itself.
