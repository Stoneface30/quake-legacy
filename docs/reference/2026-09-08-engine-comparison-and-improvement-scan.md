# Quake · WolfcamQL · PANTHEON — what each one actually is, and what we can take next

*2026-09-08. Every row below is grounded in a file on disk; paths are given so
any claim can be checked. Nothing here is inferred from reputation.*

---

## 0. What PANTHEON is, precisely

PANTHEON is **not** a launcher, a wrapper, or a config for someone else's
binary. `engine/pantheon_renderer/build/pantheon_cgame.exe` is our executable.
It links the WolfcamQL 11.3 renderer **and the whole cgame** statically — no
virtual machine, no DLL, no `wolfcamql.exe` process — and it draws from
**snapshots we compose**, not from a demo file it plays.

That last point is the difference that matters:

| | Where the world comes from | What the camera can be |
|---|---|---|
| Quake III / WolfcamQL | a `.dm_73` parsed by the client | wherever the file allows |
| **PANTHEON** | a `snapshot_t` **we build** — from a parsed demo, from FrameTruth, or from a composed scenario | anywhere, for any moment, including moments no recording contains |

`engine/pantheon_renderer/host/pantheon_cg_feed.c` is that seam.
`pantheon_frame.c::PANTHEON_ShotSnapshot` is the bridge: a RenderFrame and a
`snapshot_t` are the same statement in two vocabularies — a time, a camera, and
what existed.

---

## 1. Feature comparison

Trees on disk: `engine/engines/variants/*` (residual-only, deduped against
`engine/engines/_canonical/`), `engine/engines/_forks/q3mme/` (intact git
checkout), and `engine/pantheon_renderer/wolfcamql-11.3-src/` (intact).

| Capability | id Quake III | ioquake3 | q3mme | WolfcamQL 11.3 | **PANTHEON** |
|---|---|---|---|---|---|
| **Renderer lineage** | GL1 | GL1 **+ rend2 (GL2)** | GL1 | GL1 | GL1 (wolfcam's) |
| **FBO** | none | `renderergl2/tr_fbo.c` | `tr_framebuffer.c` + `tr_mme_fbo.c` (1,059 ln) | hand-rolled in `tr_backend.c` (EXT entry points, `qgl.h:75-87`) | inherited |
| **Multisample AA** | none | `r_ext_multisample`, SDL MSAA buffers | via FBO | dual FBO + `qglBlitFramebufferEXT` (`tr_backend.c:1047`) | inherited |
| **GLSL** | none | **`tr_glsl.c` (48 KB) + 34 `.glsl` files** — SSAO, tonemap, bokeh DOF, shadowmask, depthblur | `tr_glslprogs.c` (308 ln) + `tr_bloom.c` | 3 ARB programs loaded **as game assets** (`scripts/blurhoriz.fs`, `brightpass.fs`, `downsample1.fs`) | inherited (3 programs) |
| **Vulkan** | none | none | none | none | none — but `_canonical/code/renderervk/` exists (Quake3e) |
| **AVI capture** | **none** | `cl_avi.c` 669 ln | `tr_mme_avi.c` 537 ln | **`cl_avi.c` 1,718 ln** — AVI, no-audio AVI, WAV, TGA/JPG/PNG dumps, **depth-buffer dump**, RIFF split | we write TGA direct from `glReadPixels` |
| **Motion blur** | none | none | **`tr_mme.c` 874 + `tr_mme_sse2.c`** | `tr_mme.c` 291 ln (MMX/SSE accumulation) | inherited, unused |
| **Depth of field** | none | `bokeh_fp.glsl` (rend2) | **`cg_demos_dof.c` 592 ln** | `mme_depthFocus`/`mme_depthRange` cvars (`tr_init.c:2092`) | inherited, unused |
| **Camera splines** | none | none | **`cg_demos_camera.c` 1,086 + `cg_demos_math.c` 815** | `cg_camera.c` 452 + `cg_q3mme_camera.c` 1,290 + `cg_q3mme_math.c` 826 | **not used** — the camera is a ShotSpec decided upstream |
| **FX script engine** | none | none | `cg_demos_effects.c` 775 | **`cg_q3mme_scripts.c` 7,584 ln** | linked, **not yet driven** |
| **Timescale-independent capture** | — | partial | yes | `cl_main.c:4124` — frame step is `(1000/cl_aviFrameRate) * com_timescale` | **not needed** — we render frame N at server time T, directly |
| **Sound: OpenAL** | no | **`snd_openal.c` 2,746 ln** | no | **`snd_openal.c` 2,600 ln** | **not linked** — calls are counted, not played |
| **Sound: offline capture** | no | no | **`snd_mme.c` 228 ln** | no | none |
| **Skeletal models** | MD4 | **MDR + IQM** (`tr_model_iqm.c`) | MD4 + MDR | MD4 + MDR (`tr_animation.c` 658 ln) | MD4 + MDR |
| **Collision (`cm_trace.c`)** | 1,471 ln | 1,470 | 1,473 (+ unique `cm_demos.c`) | **1,491** | wolfcam's |
| **Animation lerp** | `CG_RunLerpFrame(ci, lf, anim, speed)` static | same | same | **`CG_RunLerpFrame(ci, lf, anim, speed, time)`** — non-static, explicit clock, called with `cent->cgtime` (per-entity demo time) | **this one**, and it is why PANTHEON can render one instant |
| **Runs headless / composes moments** | no | no | no | no | **yes** |

### The two rows that are the whole reason PANTHEON exists

- **`CG_RunLerpFrame` takes a `time`.** Wolfcam made it non-static and gave it
  an explicit clock, called with `cent->cgtime` rather than the global
  `cg.time` (`cg_players.c:2280,2282,2291,2880`). Every other tree hard-wires
  the single global clock. Without that parameter, "render the world exactly at
  t=1200750" is not a question the engine can be asked.
- **Nothing above PANTHEON's row can be handed a world.** All four upstream
  engines *read* a world — from a server or from a file. PANTHEON is *given*
  one.

---

## 2. What is already linked and not yet switched on

These cost nothing to reach: the code is compiled into
`pantheon_cgame.exe` today and simply has no caller.

| Asset | Where | What turning it on buys |
|---|---|---|
| **q3mme FX script engine** | `cgame/cg_q3mme_scripts.c` (7,584 ln) | Scripted, cueable effects — the piece the effects/transitions database wanted and `hud.py` documented as `FREE_RUNNING` only because a shader wave cannot be cued. A script can. |
| **Accumulation motion blur** | `renderer/tr_mme.c`, `mme_blurFrames`/`mme_blurOverlap`/`mme_blurType`/`mme_blurGamma` | Real per-frame motion blur instead of an ffmpeg approximation. We render N sub-frames per output frame, which is exactly what a deterministic snapshot feed makes cheap. |
| **Depth-buffer output** | `cl_avi.c:566` (`depth` flag), `mme_saveDepth`, `mme_depthFocus`/`mme_depthRange` | A depth pass per frame → DOF, fog, and compositing done in the NLE, gradeable after the fact. |
| **`cl_avi.c` writers** | `client/cl_avi.c` (1,718 ln) | We currently write a TGA per frame and shell out to ffmpeg. The engine can already emit AVI/PNG/JPG/WAV and split RIFFs. |

## 3. What we should take from the other trees

Ordered by value per unit of work. All sources are on disk.

### 3.1 Renderer — the big one
`engine/engines/_canonical/code/renderergl2/` (ioquake3 rend2) and
`_canonical/code/renderer2/` (Quake3e's fork) carry a **real GLSL renderer**:
`tr_fbo.c`, `tr_glsl.c`, `tr_postprocess.c`, `tr_dsa.c` and 34 shaders
including `ssao_fp.glsl`, `tonemap_fp.glsl`, `bokeh_fp.glsl`,
`depthblur_fp.glsl`, `shadowmask_fp.glsl`, `pshadow_fp.glsl`.

Against wolfcam's three asset-loaded ARB programs, that is: ambient occlusion,
HDR tonemapping, bokeh depth of field, real-time shadows, and a post chain we
can extend. For a fragmovie this is the single largest visual step available,
and it is a port between two trees we already own rather than new work.

**Risk to respect:** rend2 replaces the renderer cgame talks to. The seam
(`pantheon_cg_syscall.c`) is written against `refexport_t`; rend2 keeps that
interface, so the port is the renderer, not the seam.

### 3.2 Vulkan — `_canonical/code/renderervk/`
Quake3e's Vulkan backend (`vk.c`, `vk_flares.c`, `vk_vbo.c`, `shaders/`).
Larger lift than rend2 and a bigger speed win. Worth scoping *after* rend2,
not instead of it — and it would finally close the NVIDIA immediate-mode
blocker documented in `docs/reference/2026-09-07-nvidia-32bit-immediate-mode-blocker/`
by not using immediate mode at all.

### 3.3 Depth of field and the newer MME modules
WolfcamQL 11.3 **does not have** `cg_q3mme_demos_dof.c`, `_demos_camera.c`,
`_demos_capture.c`, `_demos_math.c`, or `renderercommon/tr_mme*.c`. The newer
brugal wolfcam does, and those files are on disk at
`engine/engines/_canonical/code/cgame/cg_q3mme_demos_*.c` and
`_canonical/code/renderercommon/tr_mme*.c`. q3mme's originals are at
`_forks/q3mme/trunk/code/cgame/cg_demos_dof.c` (592 ln) and
`renderer/tr_mme_fbo.c` (1,059 ln).

This is a **generational gap in our own base tree**, not a missing feature of
the family. Porting it forward is mostly copying files we already hold.

### 3.4 Collision
`_canonical/src/qcommon/` (Wolf:ET) has the most extended Q3-lineage collision
in the pool: `cm_trace.c` 1,675 ln and `cm_patch.c` 1,944 ln against wolfcam's
1,491 / 1,805. Quake3e's `cm_load.c` is 985 vs id's 839.

**Honest assessment:** we do not run physics. Collision is used for trace
visibility (`compose_three` sight-lines) and marks. The extra lines are mostly
Wolf:ET gameplay features. **Low priority** — listed because it was asked for,
not because it is a bottleneck.

### 3.5 Skeletal characters — IQM
`engine/engines/variants/ioquake3/code/renderergl1/tr_model_iqm.c` is the only
IQM loader in the pool. MD3/MD4/MDR are frame-interpolated vertex formats; IQM
is a modern skeletal format that Blender exports directly.

For **instructional video and the presenter**, this is the unlock: a rigged
character with real skeletal animation instead of the 7 stances we have. It is
a self-contained loader plus `R_AddAnimSurfaces` support.

### 3.6 Sound — the gap PANTHEON has, not one it inherits
`pantheon_cg_syscall.c` counts sound calls and plays nothing. Two sources:
- `wolfcamql-11.3-src/.../client/snd_openal.c` (2,600 ln) — a full OpenAL
  backend, already in our tree.
- `_forks/q3mme/trunk/code/client/snd_mme.c` (228 ln) — **offline** audio
  capture, which is the one a frame-by-frame renderer actually needs: audio
  written against rendered frames, not against the wall clock.

Rule HL-7 already says `FrameTruth.SemanticEvent.sound` names the intent and a
backend chooses the sample. `snd_mme.c` is that backend.

---

## 4. Defects found and fixed today (for the record)

| Defect | Root cause | Where |
|---|---|---|
| `--cgame` segfault at `0xffffffff` | `cg_syscalls.c:20` declares `syscall` as a **static function pointer** initialised to `(void *)-1`, set only by `dllEntry()`. A global `syscall()` linked cleanly and was never called. | `pantheon_cg_run.c` now calls `dllEntry` |
| Rocket had no model on frame 1 | `CG_RegisterWeapon` wipes weaponInfo before refilling, and CG_Init clears the `registered` flag for the HUD's weapon bar. Lazy re-registration happens *during* the frame. | registered inside the registration window |
| Loading screen composited into the frame | `CG_Init` draws and calls `trap_UpdateScreen`; those 2D commands stayed queued. | drained after `CG_Init` |
| **Every frame was 1264×681 in a 1280×720 file** | A window created at 1280×720 is 1280×720 **including** its title bar and frame. GL draws the client area; `glConfig` reports the request. | `PANTHEON_MatchClientArea` grows the window and verifies |
| A stale shot script looked like a renderer crash | `ParseShot` runs before `Com_Init`; `Com_Error` there reaches `Z_TagMalloc` with no zone allocator. | `ShotError` reports and exits |

The last one is the long-standing "corner artefact". It was never a corner: it
was a margin that was never rendered, filled with whatever was in that memory.

---

## 5. Proof

`docs/visual-record/2026-09-08/` — 66 frames of a recorded frag on campgrounds,
rendered in 4.0 s by `pantheon_cgame.exe` with no `wolfcamql.exe` process:
rocket in flight with its dynamic light, explosion, drifting smoke, scorch mark
burned into the floor, blood decals. None of that is in the shot script. All of
it is cgame reacting to state PANTHEON handed it.
