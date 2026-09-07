# PANTHEON native renderer — source base, architecture, and where the build stands

**2026-09-07.** Sprint objective: a PANTHEON-owned renderer that turns PANTHEON
game truth into Quake frames without `wolfcamql.exe` as the production
rasteriser.

## The correction this starts from

`PANTHEON_QUAKE_OFFSCREEN` is **not** a native renderer and must not be
described as one. It launches `wolfcamql.exe` on a hidden Windows desktop.
Wolfcam rasterises every pixel; "offscreen" says where the window went, not
who drew. Everything above the backend row — parsing, PerformanceTrace,
FrameTruth, Scene, ChoreographyPlan, ShotSpec — is genuinely ours and needs
no game. The renderer is not.

Today demonstrated the cost of that dependency: the client began exiting
`rc=1` three seconds into every capture, and a headless *engine* cannot help
when an OpenGL framebuffer refuses a mode.

## A. Source base decision

**Chosen: WolfcamQL 11.3 source**, from
`WOLF WHISPERER/WolfcamQL/wolfcamql-src.tar.gz` (tarball dated 2016-08-13,
929 files), extracted to `engine/pantheon_renderer/wolfcamql-11.3-src/`.

| candidate | verdict |
|---|---|
| **WolfcamQL 11.3 (this tarball)** | **CHOSEN.** Intact tree. It is the source of the binary we actually ship, and the binary the green-Keel proof is banked against. Carries protocol-73 demo playback and QL cgame semantics. |
| WolfcamQL 12.7test49 (`engine/engines/_canonical`) | Not buildable as-is. `_canonical` is a SHA-256 **deduplicated merge** of every engine in the knowledge base — darkplaces, radiant and ioquake3 files sit in the same tree. It is a reference corpus, not a project. It is also not the shipped binary. |
| quake3e | Best renderer of the candidates (Vulkan/GL2, maintained) and the worst fit: vanilla Q3, no protocol-73, no QL asset or model semantics. Adopting it means porting QL compatibility *into* it. |
| ioquake3 / Q3 official | Same objection, with an older renderer. A build that compiles is not QL compatibility. |
| q3mme | Not needed as a base — see below, its movie renderer is **already inside** the chosen tree. |

**The finding that settles it:** WolfcamQL 11.3 already contains Q3MME's movie
renderer as `code/renderer/tr_mme.c`, with `mme_saveDepth`, `mme_saveStencil`,
`mme_depthFocus`, `mme_depthRange`, `mme_blurFrames`, `mme_blurType`. Depth
and stencil passes — a primary goal of section 8 — exist in the base before we
write a line. No other candidate offers QL compatibility *and* movie passes
together.

## B. Architecture

```
PANTHEON FrameTruth  (ours, headless, no game)
        |
        v
   RenderFrame        exact server/edit time, camera transform + FOV,
                      actors and observed transforms, model/skin/material
                      identity, animation state, weapons and projectiles,
                      event effects, world state, visual profile, passes
        |
        v
 libpantheon_render   the 11.3 renderer, forked and owned:
                      tr_* + a headless host that owns the GL context
        |
        v
   pass artifacts     BEAUTY first; DEPTH and masks after
```

Boundary rules, unchanged from HL-1: the renderer decides **nothing** about
game truth. It receives transforms; it never infers a missing observation, and
it never fabricates a projectile path, a damage figure or an outcome.

The visual profile is resolved by the renderer's own model/material system.
`cg_enemyModel` and friends are cvars of the *compatibility backend* and must
not reach the reviewer.

## C. Build state — verified, not claimed

Toolchain present: **MinGW-w64 `i686-w64-mingw32` gcc 14.2.0**, with cmake and
ninja. 32-bit is the correct target — Wolfcam is x86 and loads `cgamex86.dll`.

**All 29 renderer translation units compile.**

```
gcc -c -w -msse2 \
    -Icode/SDL12/include -Icode/renderer -Icode/qcommon \
    -Icode/jpeg-6b -Icode/freetype2/include \
    code/renderer/<file>.c
```

`tr_mme.c` needs `-msse2` (it includes `xmmintrin.h`); `tr_font.c` needs the
bundled freetype include path. Neither is a structural problem.

## D. PANTHEON RENDERED A REAL QUAKE MAP AND A REAL ACTOR

**2026-09-07.** `engine/pantheon_renderer/build/pantheon_frame.exe` — a
PANTHEON-owned executable — mounted `pak00.pk3`, loaded the real `bloodrun` BSP
(2,408 faces, 228 meshes, 97 trisurfs), registered a real MD3, rendered one
frame and read it back. **No `wolfcamql.exe` process was involved.**

Artifacts:

- `docs/visual-record/2026-09-07/pantheon_first_native_frame_bloodrun.png`
  — world only. 63,702 unique colours, 90.9% non-black.
- `docs/visual-record/2026-09-07/pantheon_native_bsp_and_actor_bloodrun.png`
  — world + actor. Differs from the identical no-actor render by 8,022 pixels,
  which is what makes the actor's presence a measurement rather than an
  impression.

| milestone | state |
|---|---|
| A. renderer initialises | **done** |
| B. clear frame | **done** |
| C. real BSP loads and renders | **done** — visually confirmed |
| D. one real MD3 actor renders | **done** — visually confirmed, and isolated with `--no-world` |
| E. actor/camera from FrameTruth | **NOT DONE** — inputs are still command-line |
| F. valid image readback | **done** — TGA, exact size, converted to PNG |

**Read D honestly.** It is one `upper.md3` torso placed by a hand-supplied
origin, not a three-part player assembled and posed from a PerformanceTrace.
The camera came from an `info_player_deathmatch` read out of the BSP, chosen
because spawn points are guaranteed to be in open space. Nothing here has
touched game truth yet — which is exactly the boundary HL-1 asks for, and also
exactly why E is still open.

### The GL implementation

Hardware GL on this machine still crashes on `glColor*` / `glNormal*`. These
frames were produced on **application-local Mesa 24.3.3 `softpipe`**, staged
beside the executable with its full dependency closure; see
`engine/pantheon_renderer/gl_software/README.md` and `PROVENANCE.md`. No system
DLL was replaced, no registry key written, no driver changed. The loaded module
path is verified per run by `glwho.exe` rather than assumed, so a failed Mesa
load cannot masquerade as a successful one.

`softpipe` is slow and is a bring-up tool only. It proves the host and the
renderer are correct; it does not answer production capture, which still needs
the hardware path resolved.

### Four defects fixed to get here

Each found from a running process, not from reading source.

1. **`printCriticalSection` was never initialised.** `Com_Printf` opens with
   `EnterCriticalSection` on it, and only `sys_main.c` ever initialises it —
   the file the host deliberately does not compile, because it owns `main()`.
   The first print inside `Com_Init` died in ntdll with no output at all, which
   reads like a crash before `main` and is not.
2. **`ri.Printf` is not `Com_Printf`.** The refimport version takes a print
   level first. The cast between them compiled silently and passed `PRINT_ALL`
   — which is `0` — as the format string. Rebuilding the host *without* `-w`
   then proved every other `refimport_t` assignment matches exactly.
3. **`BIND` asked the driver for names it has never heard of.** It stripped
   three characters from `qglActiveTextureARB`, giving `"ActiveTextureARB"`.
   Only the leading `q` should go. Every extension pointer stayed NULL — and
   the renderer uses `qglActiveTextureARB != NULL` **as** its multitexture
   capability flag, so it concluded the hardware had none.
4. **GL was bound after first use.** `PANTHEON_BindGL()` ran after
   `BeginRegistration` returned; the renderer calls those pointers *inside* it.
   Binding now happens in `GLimp_Init`.

### One process note worth keeping

When the actor first failed to appear, the frame was byte-identical to the
no-actor render — and so was the *binary*, because an edit script reported
success without asserting its anchors had matched. The rebuild had silently not
happened. Verifying that the flag was actually present in the linked executable
(`strings ... | grep -c no-world`) is what caught it. **A build step that
cannot fail loudly will eventually lie about what you are testing.**

## E–G. Outstanding

- **E. FrameTruth-driven camera and actor** — the next milestone, and the one
  that makes this a renderer for PANTHEON rather than a renderer that happens to
  run.
- **F. Reference comparison** against Wolfcam 11.3 — still blocked; the
  reference itself will not start, and that remains a *separate* investigation.
- **G. Hardware GL for production** — `softpipe` cannot carry bulk capture.

## Engine maturity, stated separately

| component | state |
|---|---|
| PANTHEON GAME TRUTH | working — 34.3M semantic events, protocol registry, demo509 dissection |
| PANTHEON PERFORMANCE | working — traces, retarget, compare, headless |
| PANTHEON DIRECTOR | working — Scene, round bounds, choreography inputs |
| **PANTHEON NATIVE RENDERER** | **RENDERS. Real BSP + real MD3, no wolfcamql.exe. On software GL; hardware GL still blocked; FrameTruth not yet wired** |
| PANTHEON WOLFCAM BACKEND | **BROKEN as of 2026-09-07** — every profile exits `rc=1`; a 32-bit driver defect is the leading hypothesis, not yet proven |
| PANTHEON BLENDER BACKEND | not started |

## The Wolfcam backend is currently down

Every profile fails, including `TR4SH_REVIEW_V2` and `GAMEPLAY_MASTER_V2`,
which were not modified. The client dies about three seconds in, immediately
after GL extension initialisation, on the hidden desktop and in a normal
window, with staging rebuilt from canonical. The most likely trigger is a
`Stop-Process -Force` on a running client; the mechanism is not established.

Real defects found and fixed before that wall, each from the engine's own log
rather than from reading source:

- the bulk profile had no `_CFG_FILES` entry, so captures silently ran
  `master_capture.cfg` — authentic enemy, **no green Keel**
- clips were 1280x540 (stretched) at 60 fps; `cl_aviFrameRate` had been set in
  the cvar profile, which nothing reads for that purpose
- 960x540 is not an available display mode on this hardware
- resolution cvars in the profile dict override the command line, because the
  cfg is exec'd *after* it

249 clips filmed at the wrong spec are **quarantined, not deleted**. 190 good
clips remain and the live reviewer still serves them.
