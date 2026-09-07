# The `glColor*` / `glNormal*` blocker

**2026-09-07.** The PANTHEON native renderer reaches the graphics driver and
stops there. This is the evidence, kept separate from what it means.

> **Two corrections to the first version of this document, both load-bearing.**
>
> 1. **The directory name is wrong and is kept only so existing links resolve.**
>    This is **not** 32-bit specific. A native **x64** build fails identically.
> 2. **"Immediate mode" was imprecise.** `glColor*` and `glNormal*` are
>    *current vertex-attribute setters*. They are legal outside `glBegin`/`glEnd`
>    and are not exclusively immediate-mode calls. The distinction matters
>    because the failing set is defined by *what the call writes* (current
>    vertex attribute state), not by a drawing mode.

## The result

`glchar.c` makes exactly **one** GL call per process, then forces the driver to
synchronise. One call per process, so a crash names one culprit and cannot be
blamed on anything queued earlier.

| call | x86 (gcc 14.2, MinGW) | x64 (MSVC 19.44) | software GL (x86) |
|---|---|---|---|
| none | SURVIVED | SURVIVED | SURVIVED |
| **glColor4f** | **CRASHED** | **CRASHED** | SURVIVED |
| **glColor3f** | **CRASHED** | **CRASHED** | SURVIVED |
| **glColor4ub** | **CRASHED** | **CRASHED** | — |
| **glColor4fv** | **CRASHED** | **CRASHED** | — |
| **glNormal3f** | **CRASHED** | **CRASHED** | SURVIVED |
| glShadeModel | SURVIVED | SURVIVED | — |
| glDepthFunc | SURVIVED | SURVIVED | — |
| glEnable(GL_TEXTURE_2D) | SURVIVED | SURVIVED | — |
| glMatrixMode+glLoadIdentity | SURVIVED | SURVIVED | — |
| glEnableClientState | SURVIVED | SURVIVED | — |
| glTexEnvi | SURVIVED | SURVIVED | — |
| glClearColor | SURVIVED | SURVIVED | SURVIVED |

Accelerated context: `NVIDIA GeForce RTX 5060 Ti`, `4.6.0 NVIDIA 610.88`.
Software column: a generic (`PFD_GENERIC_FORMAT`, not accelerated) pixel format,
which reports `Microsoft Corporation | 1.1.0` — the Microsoft rasteriser, with
the NVIDIA ICD out of the picture. No download, no DLL beside the executable,
no system setting changed.

## The application side was audited before the driver was blamed

Given that this session had already shipped a wrong function-pointer prefix and
a wrong `refimport_t` cast, the caller was treated as the prime suspect first.

- **No function pointers at all.** `glchar.c` and `glabi.c` link `opengl32`
  directly. The entire class of bug that bit us twice cannot occur here.
- **Clean under `-Wall -Wextra -Wstrict-prototypes -Wmissing-prototypes
  -Werror=implicit-function-declaration`.** No implicit declarations.
- **Correct stdcall decoration, proven by the import table:**
  `_glColor4f@16`, `_glColor3f@12`, `_glColor4ub@16`, `_glColor4fv@4`,
  `_glNormal3f@12`, `__imp__glClearColor@16`. On Windows a wrong `@n` is a
  **link-time** failure, not a runtime one — these linked.
- **Stack balance measured across the call** (`glabi.c`): `esp` delta is **0**.
- **The call RETURNS.** It does not fault inside. The process dies at the next
  synchronising call, i.e. when the driver actually processes the command.
- **Guard buffers around the locals are intact** — 0 corrupt bytes.
- **The paired control is the strongest single piece.** `glClearColor` takes the
  same four floats, carries the same `@16` decoration, and travels the identical
  code path — and survives. An ABI or calling-convention fault cannot affect
  `glColor4f` while sparing `glClearColor`.
- **A different compiler, CRT and calling convention reproduce it exactly.**
  MSVC x64 is not GCC x86 in any respect that an ABI bug could survive.

The fault itself lands on a thread the **driver** created, on the driver's own
bad pointer:

```
Thread 8 received signal SIGSEGV
#0  0x51d1cc74 in nvoglv32!DrvPresentBuffers ()
=> movl $0xa0050e76,0x4(%ecx)          <- %ecx is not a valid pointer
#4  0x51b86fc2 in nvoglv32!DrvValidateVersion ()
#5  0x76955d49 in KERNEL32!BaseThreadInitThunk ()
```

Those symbol names are nearest-export guesses, not the real functions. A
driver-thread fault does **not** by itself exclude application-side corruption —
which is exactly why the audit above was done separately and does exclude it.

## What is established, and what is not

**Established:**
- The failure follows the **GL implementation**, not the architecture, the
  compiler, the calling convention, or the application.
- It is **not 32-bit specific**. The x64 hypothesis is dead as an explanation
  *and* as a fix.
- The failing set is `glColor*` and `glNormal*`; every state-setting call tested
  succeeds, including one with a byte-identical signature.
- Microsoft's software rasteriser runs the same calls fine on this machine.

**Not established:**
- **Why** the NVIDIA driver does this. We have a reproduction, not a root cause
  inside NVIDIA's code. Do not call it a filed, confirmed driver bug.
- Whether **Threaded Optimization** is implicated. The fault is on a driver
  worker thread, which makes it worth exactly one reversible test. Untested.
- Whether **another driver version** behaves differently. Untested by choice —
  no driver change without operator approval.
- Whether this caused **Wolfcam's** separate failure. Same driver, same call
  family, same day — but Wolfcam exits `rc=1` and PANTHEON takes a SIGSEGV.
  That difference is unexplained and the theory is not accepted. The earlier
  MME shader-asset investigation remains separate evidence.

## Why PANTHEON cannot route around it

The Q3 renderer is fixed-function. `GL_SetDefaultState` in `tr_init.c` calls
`qglColor4f(1,1,1,1)` before anything is drawn, and `tess` sets colours per
vertex for the rest of every frame. There is no version of "render a Quake
frame with this renderer" that avoids `glColor*`.

Traced through a clean build of the host, PANTHEON dies at exactly that call. A
`glGenTextures` probe after each init step returned a fresh name with `err=0x0`
every time — through `InitOpenGL`, command buffers, FBO, GLSL, and the first
three calls of `GL_SetDefaultState` — until `glColor4f`.

## Where this leaves the four options

1. **Threaded Optimization off** — still the cheapest test, still untested,
   still worth doing. Reversible, program-specific, no rebuild.
2. **x64** — **ruled out as a fix.** Already built and run: identical failure.
   x64 may still be desirable for the host on its own merits (PANTHEON loads no
   `cgamex86.dll`, so nothing binds it to x86), but it does not unblock the
   frame and should not be pursued for that reason.
3. **Software GL** — now the strongest path to a first frame. Microsoft's
   generic GL is 1.1 and too old for this renderer, but it proves the approach:
   an application-local Mesa `llvmpipe` `opengl32.dll` + WGL DLL, matched to the
   executable's architecture, would give a driver-independent correctness
   baseline. No system DLL replaced, no global registry change.
4. **Driver change** — last, and only with operator approval.

## Reproducing

```bash
gcc -m32 -o glchar.exe  glchar.c  -lopengl32 -lgdi32 -luser32   # per-call matrix
gcc -m32 -o glabi32.exe glabi.c   -lopengl32 -lgdi32 -luser32   # ABI audit
gcc -m32 -o glsw32.exe  glsw.c    -lopengl32 -lgdi32 -luser32   # software GL control
build_x64_msvc.bat                                              # x64, MSVC already installed

./glchar.exe color4f      # the one-line test
```

`build_x64_msvc.bat` uses the MSVC 14.44 BuildTools already present at
`C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools`. **No toolchain
download was needed.** It only ever emits x64, into `*64.exe` names; 32-bit and
64-bit objects, import libraries and runtimes are never mixed.
