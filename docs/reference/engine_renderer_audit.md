# PANTHEON Engine & Renderer Capability Audit (2026-08-31)

Companion to [`replay-runtime-feasibility.md`](replay-runtime-feasibility.md).
That doc settled **buildability** (Path C: MSVC 2022 present, quake3e is the
cheapest smoke test, q3mme is the fork that matters). This doc settles
**capability**: what our local engine source trees already do, natively, for
materials, models, animation, cameras, entity rendering, post-processing,
FBOs, depth/normal/motion passes, and multi-pass rendering.

Verdicts are **REUSE** (works today, use as-is) / **EXTEND** (partial, needs
work) / **REPLACE** (absent, needs new code). Every claim carries a
`file:line` citation.

---

## 0. Method, and how to read the paths

### 0.1 The trees are SHA-256 deduped — read this before citing anything

`engine/engines/` is a deduped union of 18 engine trees
(`_manifest/build_canonical.py`, map in `_manifest/canonical_map.json`).
Consequence: **`engine/engines/_canonical/code/` IS effectively the
wolfcamql-src tree.** Per the manifest, canonical-tree ownership of the
directories that matter:

| Directory | Owner (files) |
|---|---|
| `_canonical/code/renderergl1/` | wolfcamql-src **24 / 24** |
| `_canonical/code/renderergl2/` | wolfcamql-src **70 / 70** |
| `_canonical/code/renderercommon/` | wolfcamql-src 22, quake3e 6, openarena 1 |
| `_canonical/code/cgame/` | wolfcamql-src 97, quake3-source 11, openarena 2 |
| `_canonical/code/client/` | wolfcamql-src 43, ioquake3 36, quake3e 1 |
| `_canonical/code/qcommon/` | wolfcamql-src 39, quake3e 7, quake3-source 3 |
| `_canonical/code/renderer/`, `renderer2/`, `renderervk/` | quake3e (all) |
| `_forks/q3mme/trunk/code/` | q3mme (clean, un-deduped tree) |
| `variants/ioquake3/code/` | only ioq3 files that DIFFER from wolfcam's |

Two corrections to earlier notes this forced:

- `replay-runtime-feasibility.md:156` states wolfcamql-src's `code/client`,
  `code/cgame` etc. "**do** have real source — only the 3rd-party folders are
  stubbed." **The directory `_canonical/wolfcamql-src/` on disk contains 0
  files, total.** Nothing is stubbed there because nothing is there — the
  wolfcam source lives at `_canonical/code/`, having been deduped up one
  level. The source *is* present and complete; the path in that doc is wrong.
- `dissection/wolfcamql-src/RENDERER_NOTES.md:9-26` describes wolfcam's
  renderer as a single `code/renderer/` directory. **Wrong.** Wolfcam ships
  `renderergl1/` (24 files) *and* a complete `renderergl2/` rend2 renderer
  (70 files incl. `tr_fbo.c`, `tr_postprocess.c`, 34 GLSL programs). That
  doc also lists `tr_bloom.c` inside `code/renderer/` — no such file exists;
  wolfcam's bloom lives inline in `renderergl1/tr_backend.c:703-1028`.

### 0.2 Shipped binary vs. source — they are NOT the same

Critical for scoping: much of what follows exists in *source* but is not in
the binary we run today. Verified by string-scanning the exact staged binary
the pipeline launches, `output/demo_v2/_wolfcam_staging/wolfcamql.exe`
(10,838,297 bytes, wolfcamql-11.3+LAA) and its `wolfcam-ql/cgamex86.dll`:

| Symbol | in shipped `.exe` | Meaning |
|---|---|---|
| `r_enablePostProcess`, `r_enableBloom`, `r_enableColorCorrect` | ✅ 7 / 4 / 6 | **renderergl1 GLSL post-process stack is live today** |
| `r_BloomIntensity`, `r_BloomBrightThreshold`, `r_BloomTextureScale` | ✅ | bloom cvars live |
| `scripts/colorcorrect.fs`, `posteffect.vs`, `brightpass.fs`, `combine.fs`, `blurhoriz.fs`, `downsample1.fs` | ✅ all present | shaders loaded **from the VFS** |
| `r_useFbo`, `r_fboAntiAlias` | ✅ | FBO path live (already used, see §1.1) |
| `r_singleShader`, `r_singleShaderName` | ✅ 9 / 5 | live global map-shader override |
| `ReplaceShaderImage`, `RegisterShaderFromData`, `GetShaderImageData` | ✅ 11 / 10 / 10 | **runtime texture replacement API is live** |
| `R_RemapShader`, `remapshader`, `listremappedshaders`, `clearallremappedshaders` | ✅ | live material remap |
| `mme_blurFrames`, `mme_blurOverlap`, `mme_blurType` | ✅ | accumulation motion blur live |
| `mme_saveDepth`, `mme_depthFocus`, `mme_depthRange` | ✅ | **depth-pass export live** |
| `cl_renderer`, `renderer_opengl*` | ❌ 0 | **monolithic build; no renderer-DLL switching** |
| `r_hdr`, `r_toneMap`, `r_ssao`, `r_drawSunRays`, `r_depthPrepass` | ❌ 0 | **renderergl2 is NOT compiled into the shipped exe** |
| `mme_dofFrames`, `mme_dofRadius` | ❌ 0 | **DOF is not in the shipped binary** |
| `mme_worldShader`, `mme_pip`, `mme_renderWidth` | ❌ 0 | q3mme-only, never back-ported |

`cgamex86.dll` (6,322,796 bytes) confirms the cgame side is equally rich:
`freecam` ×252, `camera` ×951, `customShader` ×41, `wolfcam_` ×150,
`cg_playerShader`, `cg_whShader`, `cg_whEnemyShader`, `cg_enemyModel`,
`cg_teamModel`, `cg_ourModel`, `cg_forcePovModel`, `cg_deadBodyColor`,
`cg_playerModelForceScale`, `cg_flagStyle`, `remapshader`,
`clearremappedshader`, `fxload` — all present.

**Rule of thumb for everything below: renderergl1 + MME-blur + MME-depth +
remap/replace = free today. renderergl2 (HDR/tonemap/SSAO/DOF/sun) and all
q3mme-only features = Path C rebuild.**

---

## 1. FBO / render targets

### 1.1 renderergl1 (the shipped renderer) — **REUSE**

Wolfcam added a real offscreen framebuffer path that stock ioquake3
renderergl1 does not have (`grep r_useFbo variants/ioquake3/code/` → 0 hits).

- `InitFrameBufferAndRenderBuffer()` —
  `engine/engines/_canonical/code/renderergl1/tr_init.c:237`
  - Color: `GL_RGB8` texture on `GL_TEXTURE_RECTANGLE_ARB` bound to
    `GL_COLOR_ATTACHMENT0_EXT` — `tr_init.c:278-291` (`tr.sceneTexture`)
  - **Depth as a sampleable texture**, `GL_DEPTH24_STENCIL8_EXT`, attached to
    both `GL_DEPTH_ATTACHMENT_EXT` and `GL_STENCIL_ATTACHMENT_EXT` —
    `tr_init.c:296-310` (`tr.depthTexture`); renderbuffer fallback
    `tr_init.c:313-317`
  - Second MSAA FBO + resolve blit — `tr_init.c:361-459`
    (`tr.frameBufferMultiSample`, samples from `r_fboAntiAlias`,
    clamped to `GL_MAX_SAMPLES_EXT` at `tr_init.c:378-382`)
  - State flags in `tr`: `sceneTexture` / `depthTexture` /
    `usingFinalFrameBufferObject` — `renderergl1/tr_local.h:1113,1114,1117`
- Cvars: `r_useFbo` default `0` and `r_fboAntiAlias` default `0`, both
  `CVAR_ARCHIVE|CVAR_LATCH` — `tr_init.c:1974-1975`
- Present path: MSAA resolve blit → `RB_ColorCorrect()` → bind FBO 0 → full-
  screen textured quad of `tr.sceneTexture` — `renderergl1/tr_backend.c:2026-2113`
- **Already in production use**: `creative_suite/engine/master_profile.py:61-62`
  sets `r_useFbo=1, r_fboAntiAlias=4` for every master, documented at
  `master_profile.py:13-15` as also removing NVIDIA overlay contamination.

**Why this matters for PANTHEON:** every capture we already take renders into
an offscreen buffer with a depth texture attached. The plumbing for a
custom full-screen pass is not hypothetical — it runs on every frame we ship.

### 1.2 renderergl2 / rend2 (source only) — **REUSE (as source), REPLACE (as runtime)**

Wolfcam ships James Canete's full rend2 FBO manager. It is **not** in the
shipped exe, so it is a Path C deliverable.

- Generic manager: `FBO_Create(name, w, h)` —
  `_canonical/code/renderergl2/tr_fbo.c:80`;
  `FBO_CreateBuffer(fbo, format, index, multisample)` — `tr_fbo.c:122`
- `FBO_t` struct carries **`colorBuffers[16]` / `colorImage[16]`** —
  `renderergl2/tr_fbo.h:38,40` — i.e. the struct is MRT-shaped
- 15 named render targets already built at init (`tr_fbo.c:300-429`):
  `renderFbo`, `msaaResolveFbo`, `finalFbo`, `screenScratchFbo`,
  `sunRaysFbo`, `pshadowFbos[]`, `sunShadowFbo[]`, `screenShadowFbo`,
  `textureScratchFbo[]`, `calcLevelsFbo`, `targetLevelsFbo`, `quarterFbo[]`,
  `hdrDepthFbo`, `screenSsaoFbo`, `renderCubeFbo`

### 1.3 Multiple *simultaneous* render targets (true MRT) — **EXTEND**

The struct supports 16 attachments but **`qglDrawBuffers` is called nowhere**
in `renderergl2/` — grep for `qglDrawBuffers`, `GL_COLOR_ATTACHMENT1`,
`colorImage[1]` across `_canonical/code/renderergl2/*.c|*.h` returns **zero
hits**. Every FBO in practice uses attachment 0 only. Writing colour + normal
+ velocity in one geometry pass is a genuine extension, not a config change —
but it starts from a manager that already models it.

### 1.4 q3mme — **REUSE (source), REPLACE (runtime)**

q3mme has its own independent FBO stack with GLSL program objects:

- `_forks/q3mme/trunk/code/renderer/tr_framebuffer.c` —
  `R_FrameBuffer_Init` :399, `_StartFrame` :479, `_Blur(scale,frame,total)`
  :494, `_EndFrame` :528, `_Shutdown` :554, plus `R_Build_glsl` :356 /
  `R_Delete_glsl` :384 and `R_DrawQuadMT` :120
- `tr_mme_fbo.c` — the MME-integrated version: `R_FrameBuffer_BlurInit` :636,
  `_BlurDraw` :679, `_RotoInit` :743, `_RotoDraw` :769, `_BloomInit` :802,
  `_BloomDraw` :816, `_DoEffect` :976
- `tr_bloom.c` — a second, Warsow-derived bloom: `R_BloomScreen` :394,
  `R_Bloom_WarsowEffect` :200, `R_BloomInit` :444

---

## 2. Depth, normal and motion-vector passes

| Pass | Verdict | Evidence |
|---|---|---|
| **Depth buffer, sampleable in a shader** | **REUSE** | `renderergl1/tr_init.c:296-310` attaches `GL_DEPTH24_STENCIL8_EXT` as a texture (`tr.depthTexture`), live whenever `r_useFbo 1` — which our masters already set |
| **Depth exported as a parallel image/video stream** | **REUSE** | `mme_saveDepth` (`renderercommon/tr_mme.c:382`, `CVAR_ARCHIVE`, live-settable) allocates a `GLfloat`-per-pixel buffer and opens a **second AVI/tga/jpg/png/pipe writer** — `_canonical/code/client/cl_main.c:6212-6224`. Present in the shipped exe. Accumulated across blur sub-frames at `tr_mme.c:170-171,431` |
| **Linearised depth as a colour render target** | **REUSE (rgl2 source)** | `tr.hdrDepthImage` = `R_CreateImage("*hdrDepth", ..., GL_R32F)` — `renderergl2/tr_image.c:3148`; produced by `FBO_BlitFromTexture(tr.renderDepthImage, ... tr.hdrDepthFbo ...)` — `renderergl2/tr_backend.c:2209`; consumed by SSAO/depthblur at `tr_backend.c:2302-2382` |
| **Depth-of-field focus/range metadata** | **REUSE (partial)** | `mme_depthFocus` / `mme_depthRange` present in the shipped exe (`tr_mme.c:380`), but `mme_dofFrames`/`mme_dofRadius` are **not** — accumulation DOF is source-only |
| **Stencil export** | **EXTEND** | `mme_saveStencil` exists in source (`_forks/q3mme/.../tr_mme.c:847`) and wolfcam allocates a stencil blur block (`renderercommon/tr_mme.c:180`), but the string is **absent from the shipped exe** |
| **Normal buffer / G-buffer** | **REPLACE** | Nothing. `grep -l "normalBuffer\|GBuffer\|NORMAL_ATTACHMENT"` across `_canonical/code`, `_forks/q3mme`, `variants/ioquake3` returns only `cl_cin.c` and `q_shared.c` — false positives. No fork in this repo has a normal pass |
| **Motion vectors / velocity buffer** | **REPLACE** | Same grep, same result: `motionVector` / `velocityBuffer` do not exist anywhere. Note that q3mme/wolfcam get *motion blur* by **temporal accumulation** (§3), not by velocity buffers — a different technique with no reusable velocity data |

**Why this matters for PANTHEON:** we can already export a synchronized depth
sequence alongside every capture with one cvar. That unlocks post-DOF, fog,
relighting, depth-keyed grading and depth-conditioned ComfyUI/ControlNet work
in the ffmpeg pipeline with **zero engine work**. Motion vectors — which
would unlock optical-flow-free frame interpolation and true per-object motion
blur — do not exist and would be real renderer engineering.

---

## 3. Multi-pass rendering

### 3.1 Temporal accumulation (MME) — **REUSE**

The MME system renders N jittered sub-frames per output frame and combines
them with a named weighting kernel. Wolfcam back-ported it into
`renderercommon/tr_mme.c`:

- Cvars — `renderercommon/tr_mme.c:367-382`: `mme_blurFrames` (0),
  `mme_blurOverlap` (0), `mme_blurType` (**"gaussian"**), `mme_blurJitter`
  (1), `mme_blurStrength` (0), `mme_dofFrames` (0), `mme_dofRadius` (2),
  `mme_depthFocus` (0), `mme_saveDepth` (0) — all `CVAR_ARCHIVE`, no LATCH,
  no CHEAT
- Sub-frame jitter: `R_MME_JitterOrigin` :210, `R_MME_JitterView` :242,
  `R_MME_MultiPassNext` :281, `R_MME_GetPassData` :351
- Backend integration: `renderergl1/tr_backend.c:1796-1798` (jitter the
  view), `:2280` (`R_MME_CheckCvars`), `:2486-2497` (multi-pass DOF branch)
- q3mme original for comparison: `_forks/q3mme/trunk/code/renderer/tr_mme.c:176-208`
  — `blurTotal = mme_blurFrames + mme_blurOverlap`, `passTotal = mme_dofFrames`,
  separate accumulation blocks for **shot, stencil and depth**
  (`R_MME_MakeBlurBlock` at :191-193) and a "median" combine for the DOF pass
  (:198)

Shipped-binary reality: `mme_blurFrames` / `mme_blurOverlap` / `mme_blurType`
are **in** the exe; `mme_dofFrames` / `mme_dofRadius` are **not**. So
**accumulation motion blur is free today; accumulation DOF is not**.

### 3.2 Multiple scenes per frame — **REUSE**

`RE_RenderScene` is explicitly re-entrant per frame. The comment at
`renderergl1/tr_scene.c:422-426` says a frame may contain several scenes, and
`tr.frameSceneNum++` / `tr.sceneCount++` (`tr_scene.c:427-428`) plus the
`r_firstSceneDrawSurf/Entity/Dlight/Poly` advance (`tr_scene.c:458-461`) make
consecutive scenes append rather than clobber.

Working in-tree proof: `CG_Draw3DModelExt` builds a **local stack
`refdef_t`** with its own fov and viewport and calls
`trap_R_RenderScene(&refdef)` — `_canonical/code/cgame/cg_draw.c:2866-2908`
— a second independent camera in the same frame, after the main one at
`cg_draw.c:11211`. Zero engine changes needed for split-screen / inset /
multi-angle-in-one-frame.

### 3.3 Portal / mirror recursion — **EXTEND (capped at 1)**

`R_MirrorViewBySurface` — `renderergl1/tr_main.c:1031`; clones viewParms
(:1055), sets `isPortal` (:1056), mirrors origin/axes (:1062-1069), recurses
into `R_RenderView` (:1074). Depth is hard-capped: `if (tr.viewParms.isPortal)
return qfalse;` — `tr_main.c:1038-1041`. There is no `MAX_*_VIEWS`; the real
budget is `MAX_DRAWSURFS 0x10000` (`tr_local.h:66`), clamped at
`tr_main.c:1500-1502`.

### 3.4 Offscreen virtual-camera passes (rgl2) — **REUSE (source)**

`renderergl2/tr_main.c` already builds hand-rolled `viewParms_t` and calls
`R_RenderView` for dlight cubemaps (:1932), point shadows (:2174-2181),
4-cascade sun shadows (:2697-2700), and — the template we want —
**cubemap capture with arbitrary origin/axis, `fovX=fovY=90`, into
`tr.renderCubeFbo` via `targetFbo`/`targetFboLayer`** (:2727-2749). rgl1's
`viewParms_t` has no `targetFbo` field, so render-to-texture from a second
camera is rgl2-only.

---

## 4. Post-processing — the headline finding

### 4.1 wolfcamql renderergl1 already runs a user-editable GLSL post chain — **REUSE**

This is the single most valuable discovery in the audit and it needs **no
rebuild, no engine change, and no new C code.**

**The chain**, all in `_canonical/code/renderergl1/`:

| Stage | Function | Line |
|---|---|---|
| Downsample | `RB_QLBloomDownSample` | `tr_backend.c:703` |
| Bright-pass threshold | `RB_QLBloomBrightness` | `tr_backend.c:765` |
| Horizontal blur | `RB_QLBloomBlurHorizontal` | `tr_backend.c:817` |
| Vertical blur | `RB_QLBloomBlurVertical` | `tr_backend.c:863` |
| Combine scene + bloom | `RB_QLBloomCombine` | `tr_backend.c:909` |
| N-pass driver | `RB_QLBloom` | `tr_backend.c:1005` |
| Gate + MSAA handling | `RB_QLPostProcessing` | `tr_backend.c:1030` |
| **Final full-screen grade** | `RB_ColorCorrect` | `tr_backend.c:1092`, called at `tr_backend.c:2046` |

**The programs are compiled from files on the game VFS at renderer init:**

```
G:\QUAKE_LEGACY\engine\engines\_canonical\code\renderergl1\tr_init.c:580-615
  ri.FS_ReadFile("scripts/posteffect.vs", ...)          // :581
  R_InitFragmentShader("scripts/colorcorrect.fs", ...)  // :610
  R_InitFragmentShader("scripts/blurhoriz.fs",   ...)   // :611
  R_InitFragmentShader("scripts/blurvertical.fs",...)   // :612
  R_InitFragmentShader("scripts/brightpass.fs",  ...)   // :613
  R_InitFragmentShader("scripts/combine.fs",     ...)   // :614
  R_InitFragmentShader("scripts/downsample1.fs", ...)   // :615
```

`R_InitFragmentShader` — `tr_init.c:487` — reads the file, prepends
`ShaderExtensions`, compiles, links (`:516-528`). Loader invoked from
`InitQLGlslShadersAndPrograms` (`tr_init.c:532`), itself called from
`InitOpenGL()` at `tr_init.c:842`.

**Those 7 files exist and are overridable.** Verified inside
`C:\Program Files (x86)\Steam\steamapps\common\Quake Live\baseq3\pak00.pk3`:
`scripts/posteffect.vs` (122 B), `colorcorrect.fs` (926 B), `combine.fs`
(711 B), `blurhoriz.fs` / `blurvertical.fs` (1070 B each), `brightpass.fs`
(256 B), `downsample1.fs` (213 B). The FS resolves later-added search paths
first (`paksort` + `qsort` at `_canonical/code/qcommon/files.c:3082-3088,3134`;
each pak prepended to `fs_searchpaths` at `files.c:3184-3187`), and the
`fs_game` dir is searched ahead of `baseq3`. The staging dir already proves
the override slot works — `output/demo_v2/_wolfcam_staging/wolfcam-ql/`
carries `zzz_uhd_01..05.pk3`, `zzz_zz_moviehud.pk3`,
`zzz_zz_pantheon_ads.pk3` today (Rule ENG-2).

**What `colorcorrect.fs` actually is** (the pass that sees the finished frame):

```glsl
uniform sampler2DRect backBufferTex;   // the entire rendered scene
uniform float p_gammaRecip;            // 1.0 / r_gamma
uniform float p_overbright;            // (1<<overbrightBits) * r_overBrightBitsValue
uniform float p_contrast;              // r_contrast
```

`RB_ColorCorrect` feeds exactly those four (`tr_backend.c:1124-1153`) and
draws one full-screen quad (`:1155-1169`). **Replacing this file with a
PANTHEON grade — film LUT, teal/orange split-tone, vignette, chromatic
aberration, grain, letterbox, halation — is a pk3 drop.** `combine.fs` gives
a second injection point with both the scene *and* the bloom texture plus
four more live uniforms (`p_bloomsaturation`, `p_scenesaturation`,
`p_bloomintensity`, `p_sceneintensity` — set at `tr_backend.c:946-968`).

**Three hard constraints to design around:**

1. `RB_ColorCorrect` calls `ri.Error(ERR_FATAL, ...)` if any of
   `p_gammaRecip`, `p_overbright`, `p_contrast`, `backBufferTex` is missing
   from the linked program (`tr_backend.c:1126-1153`). GLSL compilers strip
   unused uniforms, so a replacement shader **must reference all four** or
   the engine hard-crashes on the first frame.
2. Gating cvars: `r_enablePostProcess` default `1`
   **`CVAR_ARCHIVE|CVAR_LATCH`** (`tr_init.c:1958`), `r_enableColorCorrect`
   default `1` **LATCH** (`:1959`), `r_enableBloom` default **`0`** but plain
   `CVAR_ARCHIVE` — live-toggleable (`:1961`). All eleven `r_Bloom*` tuning
   cvars are plain `CVAR_ARCHIVE` except `r_BloomTextureScale` (LATCH) —
   `tr_init.c:1962-1972`. So bloom look can be dialled **live, mid-demo**.
3. `glConfig.qlGlsl` must be true — set by GL capability detection at
   `_canonical/code/sdl/sdl_glimp.c:1200`, cleared on any shader
   compile/link failure (`tr_init.c:504,513,593,607`). A broken replacement
   silently disables the whole chain rather than erroring loudly.

Also live and cheap: `r_gamma` (`tr_init.c:1880`), `r_contrast`
(`tr_init.c:1960`), `r_greyscale` + `r_greyscaleValue`
(`tr_init.c:1833-1835`, LATCH), `r_overBrightBitsValue`.

### 4.2 renderergl2 post stack (source only) — **REUSE (source), REPLACE (runtime)**

`_canonical/code/renderergl2/tr_postprocess.c` — a modern post pipeline
wolfcam carries but does not ship:

| Effect | Entry point |
|---|---|
| HDR tone mapping + auto-exposure | `RB_ToneMap(hdrFbo, hdrBox, ldrFbo, ldrBox, autoExposure)` :25 |
| **Bokeh depth-of-field** | `RB_BokehBlur(src, srcBox, dst, dstBox, blur)` :106 |
| Radial blur | `RB_RadialBlur(...)` :227 |
| **Sun rays / god rays** | `RB_SunRays(srcFbo, srcBox, dstFbo, dstBox)` :299 |
| Separable Gaussian blur | `RB_GaussianBlur(srcFbo, dstFbo, blur)` :452 (`RB_HBlur` :442, `RB_VBlur` :447) |

Plus 34 GLSL programs in `_canonical/code/renderergl2/glsl/` — including
`ssao_fp/vp`, `tonemap_fp/vp`, `bokeh_fp/vp`, `depthblur_fp/vp`,
`calclevels4x`, `down4x`, `shadowmask`, `shadowfill`, `pshadow`,
`lightall`, `greyscale`. Note `rectscreen_*.glsl` and `texturenocolor_*.glsl`
are **wolfcam-only** (absent from ioquake3 per the dedup manifest).

Controlling cvars — `renderergl2/tr_init.c`: `r_hdr` (1, LATCH) :1968,
`r_postProcess` (1) :1970, `r_toneMap` (1) :1972, `r_cameraExposure` (CHEAT)
:1983, `r_depthPrepass` (1) :1985, `r_ssao` (0, LATCH) :1986, `r_forceSun`
:2012, `r_drawSunRays` (0, LATCH) :2015, `r_sunlightMode` (1, LATCH) :2016.

**None of these strings are in the shipped exe.** Getting them requires the
Path C rebuild — but the payoff is a *huge* jump: real SSAO, cascaded sun
shadows, HDR tonemapping, bokeh DOF and god rays, all already written.

### 4.3 q3mme post-processing — **REUSE (source), REPLACE (runtime)**

`_forks/q3mme/trunk/code/renderer/tr_init.c:900-907` registers
`r_framebuffer_bloom`, `r_framebuffer_blur_size`, `r_framebuffer_blur_amount`,
`r_framebuffer_blur_samples`, `r_framebuffer_bloom_sharpness`,
`r_framebuffer_bloom_brightness`, **`r_framebuffer_rotoscope`** and
**`r_framebuffer_rotoscope_zedge`**. The rotoscope + depth-edge pass is a
built-in cel-shade / outline post effect — directly relevant to the PANTHEON
stylised-asset direction, and the only *real* outline implementation anywhere
in the family (§7.4).

---

## 5. Materials — shader and texture hot-reload

### 5.1 `.shader` script re-parse — **REPLACE**

There is no path short of a renderer restart.

- `R_InitShaders()` — `renderergl1/tr_shader.c:3525` (gl2: `tr_shader.c:4221`)
  — called exactly once, from `R_Init` at `renderergl1/tr_init.c:2090`
- `ScanAndLoadShaderFiles()` — `tr_shader.c:3226` — lists
  `shaderoverride/*.shader` (:3243) and `scripts/*.shader` (:3244),
  concatenates into `s_shaderText` via **`ri.Hunk_Alloc`** (:3319) and builds
  `shaderTextHashTable` pointing *into* that block (:3376-3402). Hunk
  allocation is the blocker: it cannot be re-run without a hunk reset.
- `R_FindShader()` — `tr_shader.c:2679` — hits the hash table first
  (:2750-2761) and returns the cached `shader_t`; disk is never re-consulted.
- No `r_reloadImages` / `reloadShaders` / `R_Reload` exists **in any tree** —
  a case-insensitive sweep of `engine/engines/` (excluding `ghidra/`) returns
  zero hits. That ioquake3-family feature is simply not here.

### 5.2 `vid_restart` — **REPLACE / avoid**

`CL_Vid_Restart_f` — `_canonical/code/client/cl_main.c:4230`. It is the only
thing that re-runs `R_InitShaders` (via `CL_InitRef` at :4296), and it is
destructive: stops demo *recording* (:4255-4256), `Hunk_Clear()` (:4264-4273),
`CL_ShutdownUI()` (:4276), **`CL_ShutdownCGame()` (:4278)** which destroys the
cgame VM and every piece of accumulated demo state, `CL_ShutdownRef()` (:4280),
force-clears `cl_paused` (:4293). It does not disconnect demo *playback*
(`clc` is never memset, hence the `cl_freezeDemo` fixup at :4308-4310), but
the source itself flags it as crash-prone with demos —
`cl_main.c:3491`: *"This can crash with /vid_restart since the cm data is
invalid"*, with a `CM_ClearMap()` workaround at :3493-3495.

### 5.3 Runtime material→material swap — **REUSE** ⭐

Wolfcam's `R_RemapShader` is the strongest variant in the family and it is
live in the shipped binaries.

```c
/* _canonical/code/renderergl1/tr_shader.c:68  (gl2: tr_shader.c:70) */
void R_RemapShader (const char *shaderName, const char *newShaderName,
                    const char *timeOffset, qboolean keepLightmap, qboolean userSet);
```

Two params more than stock Q3 / q3mme / quake3e (all 3-arg, single channel —
q3mme `_forks/q3mme/trunk/code/renderer/tr_shader.c:169`; quake3e
`_canonical/code/renderervk/tr_shader.c:54`).

- Remaps **every** shader sharing the stripped name across lightmap variants
  via the hash chain — `tr_shader.c:100-122`
- **Dual channel**: `userSet` writes `sh->userRemappedShader`, otherwise
  `sh->gameRemappedShader` (`tr_shader.c:105-119`; fields at
  `renderergl1/tr_local.h:451-453`). **User remaps override anything the mod
  does** — exactly the authoring-layer semantics we want.
- `keepLightmap` preserves the original surface's lightmap (:107/:110)
- **Resolution happens per-surface, per-frame** in `RB_BeginSurface` —
  `renderergl1/tr_shade.c:345`, priority chain at `:355-373`:
  1. `r_singleShader` (map surfaces, non-sky) → `tr.singleShader` — :355-359
  2. `shader->userRemappedShader` — :360-367
  3. `shader->gameRemappedShader` — :368-370
  4. the shader itself — :372

  Flipping a pointer takes effect on the very next frame. No reload, no handle
  invalidation, no demo disturbance.
- Console UX, all present: `remapshader <orig> <new> [timeoffset]
  [keepLightmap]` → `CG_RemapShader_f` at `_canonical/code/cgame/cg_consolecmds.c:7437`
  (registered :8571, hardcodes `userSet=qtrue` at :7462); `clearremappedshader`
  :7465 / :8572; renderer-side `remaplasttwoshaders`
  (`renderergl1/tr_init.c:1771`), `listremappedshaders`
  (`tr_shader.c:3203`), `clearallremappedshaders` (`tr_shader.c:156`),
  registered `tr_init.c:2001-2003`
- VM path: `refexport_t` slot `renderercommon/tr_public.h:112`, wired
  `renderergl1/tr_init.c:2244`, syscall `client/cl_cgame.c:1292-1298`, trap
  `cgame/cg_syscalls.c:350`

**Global map-wide override, also live:** `r_singleShader` +
`r_singleShaderName` — `renderergl1/tr_init.c:1853-1854`, both plain
`CVAR_ARCHIVE` (no LATCH, no CHEAT). Applies to `shader->mapShader &&
!shader->isSky`; modes 2/4 keep the original lightmap (`tr_shade.c:355-359`).
q3mme's equivalent is `mme_worldShader`, re-resolved per frame at
`_forks/q3mme/trunk/code/renderer/tr_cmds.c:438-445` and applied at
`tr_world.c:300-301` — but that cvar is **not** in our binary.

### 5.4 Runtime *texture pixel* replacement — **EXTEND** ⭐

Wolfcam ships a complete texture-replacement API that ioquake3, q3mme and
quake3e do **not** have:

```c
/* _canonical/code/renderercommon/tr_public.h:123-127 */
void      (*ReplaceShaderImage)(qhandle_t h, const ubyte *data, int w, int h);
qhandle_t (*RegisterShaderFromData)(const char *name, ubyte *data, int w, int h,
                                    qboolean mipmap, qboolean allowPicmip,
                                    int wrapClampMode, int lightmapIndex);
void      (*GetShaderImageDimensions)(qhandle_t h, int *width, int *height);
void      (*GetShaderImageData)(qhandle_t h, ubyte *data);
```

- `RE_ReplaceShaderImage` — `renderergl1/tr_shader.c:3598`; resolves the
  shader (:3604), takes `stages[0]->bundle[0].image[0]` (:3610), `GL_Bind`
  (:3622), `R_Upload32` into the **existing `texnum`** (:3642-3649). **The
  `qhandle_t` survives** — every cached reference sees new pixels instantly.
  gl2 equivalent `renderergl2/tr_shader.c:4235`.
- `RE_RegisterShaderFromData` — `tr_shader.c:3692`
- Wired: `renderergl1/tr_init.c:2251-2254`; syscalls
  `client/cl_cgame.c:1339-1349`; traps `cgame/cg_syscalls.c:545-560`
- **Proven in production** — the live crosshair recolour round trip:
  `cgame/cg_main.c:3955` (`trap_GetShaderImageData` caches originals) →
  `cgame/cg_draw.c:8698` (`trap_ReplaceShaderImage` writes recoloured pixels)
  → `cg_draw.c:8612` (restore). Also `cg_main.c:8107`
  (`trap_RegisterShaderFromData` builds shaders from memory) and an existing
  console test hook at `cg_consolecmds.c:1228`.

**Why EXTEND and not REUSE:** it is hardwired to `stages[0].bundle[0].image[0]`
(`tr_shader.c:3610`) with `//FIXME lightmaps?` at :3618 and
`//FIXME allowPicmip` at :3644 — it cannot touch multi-stage shaders or
animated bundles. A dead `#if 0` block at `tr_shader.c:3539-3596` already
sketches the all-stages loop. There is also **no "load a PNG/TGA from disk →
feed it in" front end** — the data must come from the caller. Note
`R_FindImageFile` (`renderergl1/tr_image.c:1254`) returns cached before
touching disk (:1270-1279), so re-registering a path can never pull new bytes.

**Why this matters for PANTHEON:** the hot-swap asset-pack goal has a live,
shipping seam. `R_RemapShader` swaps material→material per frame; the
`ReplaceShaderImage` family swaps pixels under a stable handle. Combined with
`r_singleShader` and per-entity `customShader` (§7), a "PANTHEON skin" can be
applied and toggled **mid-demo, at capture time**, without a rebuild — which
is exactly what the ComfyUI photoreal pipeline (Phase 5) needs to see its own
output in-engine instead of only in a gallery.

---

## 6. Model rendering, animation and skins

### 6.1 Format dispatch and MD3 entry — **REUSE**

- `R_AddEntitySurfaces()` — `renderergl1/tr_main.c:1331-1364`; model fetched
  at :1339, switch at :1343-1352: `MOD_MESH→R_AddMD3Surfaces` (:1344),
  `MOD_MDR→R_MDRAddAnimSurfaces` (:1347), `MOD_IQM→R_AddIQMSurfaces` (:1350),
  `MOD_BRUSH→R_AddBrushModelSurfaces` (:1353)
- **Wolfcam refactor worth knowing:** `trRefEntity_t` carries both
  `refEntity_t ent` and `refEntity_t *ePtr` — `renderergl1/tr_local.h:82-94`
  — and the renderer reads `ent->ePtr->...` throughout. An override layer can
  repoint `ePtr` at a substituted struct.
- `R_AddMD3Surfaces` — `renderergl1/tr_mesh.c:282`; `R_ComputeLOD` —
  `tr_mesh.c:166` (driven by `r_lodscale` / `r_lodbias`, :204-234)

**Shader-selection chain per surface — `renderergl1/tr_mesh.c:352-381`:**

1. `ent->ePtr->customShader` → one shader for the whole model (:352-353)
2. `ent->ePtr->customSkin` → per-surface `.skin` remap (:354-374)
3. `surface->numShaders <= 0` → `tr.defaultShader` (:375-376)
4. else `md3Shader += ent->ePtr->skinNum % surface->numShaders` (:377-381)
   — `skinNum` is a free per-entity selector among the model's baked variants

**Duplicated in the other two adders** — `tr_animation.c:257-276` (MDR) and
`tr_model_iqm.c:1118-1130` (IQM). Any 5th priority (e.g. a director override)
must be inserted in all three, or factored into one shared helper.

### 6.2 Formats supported — **REUSE**

`RE_RegisterModel` accepts, in preference order, **`.iqm`, `.mdr`, `.md3`** —
loader table `renderergl1/tr_model.c:193-198`. `modtype_t` is
`MOD_BAD, MOD_BRUSH, MOD_MESH, MOD_MDR, MOD_IQM` (`tr_local.h:834-840`).
**MD4 is not supported** — no `MD4_IDENT` anywhere in `renderergl1`. IQM
means modern skeletal animation with arbitrary bone counts is already
available for any new PANTHEON models — a significant, under-used capability.

### 6.3 Model handle lifecycle — **EXTEND (with care)**

`RE_RegisterModel` — `tr_model.c:267`; linear name scan returns the existing
handle (:290-298); `R_AllocModel` — `tr_model.c:240` — is `ri.Hunk_Alloc`,
capped at `MAX_MOD_KNOWN` **1024** (`tr_local.h:856`), **never freed, never
reused**, reset only in `R_ModelInit` (`tr_model.c:938`). A handle is bound to
its name string at :310 and never rewritten, so **re-registering a handle to a
different file at runtime is impossible** without a new export. Fine for a
fixed override set loaded at map start; **not** fine for interactive
"type a model name and see it" churn, which leaks a slot per unique name and
dies at 1024.

### 6.4 Skins — **REUSE**

`RE_RegisterSkin` — `renderergl1/tr_image.c:2175`. Wolfcam lowercases the name
first (:2200-2209, not in stock ioq3), caches by `Q_stricmp` (:2212-2221),
caps at `MAX_SKINS` **1024** (`tr_local.h:63`), `Hunk_Alloc` again.
**If the name does not end in `.skin` it is treated as a single shader for the
whole model** (`R_FindShader` at :2238-2243) — the cheap whole-model recolour
seam. Parse loop :2246-2283, `MAX_SKIN_SURFACES` 256 (`tr_local.h:511`).
`R_InitSkins` :2310, `R_GetSkinByHandle` :2328, `skinlist` command registered
`tr_init.c:1990`.

Runtime skin swap is genuinely free: `customSkin` / `customShader` are read
fresh from the refEntity every frame. Register the palette once at map load,
swap handles per frame at zero cost.

### 6.5 Runtime model swap per player — **REUSE**

Already fully built by wolfcam. `CG_CheckForModelChange()` —
`_canonical/code/cgame/cg_players.c:5027` — rewrites the clientInfo just
before `CG_Player` reads it. Backing store: `cg.enemyModel`, `teamModel`,
`redTeamModel`, `blueTeamModel`, `ourModel`, `fallbackModel`, `ntfClassModel`,
loaded by `Wolfcam_LoadEnemyModel` (`cgame/wolfcam_view.c:985`),
`Wolfcam_LoadTeammateModel` (:83), `_LoadRedTeamModel` (:231),
`_LoadBlueTeamModel` (:402), `_LoadOurModel` (:649), `_LoadFallbackModel`
(:813). Transplant primitive `CG_CopyClientInfoModel` —
`cg_players.c:1173-1208`. A pristine server copy is kept in
`cgs.clientinfoOrig[]` (`cg_players.c:6022` et al.) — the exact
"original vs. effective appearance" split a director override layer wants.

Registration path: `CG_RegisterClientModelname` — `cg_players.c:721-837`;
skins `CG_RegisterClientSkin` — `cg_players.c:521`. Binding into refEntities:
`legs.hModel/customSkin` `cg_players.c:6966,7038-7039`, torso :7103-7108,
head :7403-7407.

---

## 7. Entity rendering hooks

### 7.1 `refEntity_t` override surface — **REUSE**

`_canonical/code/renderercommon/tr_types.h:115-157`. Every field a
per-entity override layer needs is already there:

| Field | Line | Role |
|---|---|---|
| `hModel` | 119 | model swap |
| `skinNum` | 136 | pick among the model's baked shader variants |
| `customSkin` | 137 | per-surface `.skin` remap |
| `customShader` | 138 | one shader for the whole entity, beats `customSkin` |
| `shaderRGBA[4]` | 141 | drives `rgbGen entity` / `alphaGen entity` |
| `shaderTexCoord[2]` | 142 | drives `tcMod entity` |
| `shaderTime` | 143 | per-entity effect phase |
| `axis[3]`, `nonNormalizedAxes`, `origin` | 125-127 | transform + scale |
| `frame`, `oldframe`, `backlerp` | 128-133 | animation |
| `renderfx` | 117 | RF_* bitfield |

`RF_*` flags — `tr_types.h:56-76`: `RF_MINLIGHT` 0x0001 (:57),
`RF_THIRD_PERSON` 0x0002 (:58), `RF_FIRST_PERSON` 0x0004 (:59),
`RF_DEPTHHACK` 0x0008 (:60), `RF_CROSSHAIR` 0x0010 (:62-65),
`RF_NOSHADOW` 0x0040 (:67), `RF_LIGHTING_ORIGIN` 0x0080 (:69-72),
`RF_SHADOW_PLANE` 0x0100 (:74), `RF_WRAP_FRAMES` 0x0200 (:75-76).
**Bit 0x0020 is free** and `renderfx` is an `int` with 10 bits used — room
for e.g. `RF_PANTHEON_OUTLINE`. Adding one means handling it in all three
surface adders plus `tr_main.c:1331`. Verdict for the flag space: **EXTEND**.

Wolfcam raised `REFENTITYNUM_BITS` 10→14, `MAX_REFENTITIES` **16383**
(`tr_types.h:48-54`) — no entity-budget pressure for extra overlay passes.
`refEntityType_t` additions: `RT_MODEL_FX_DIR/_ANGLES/_AXIS` (:96-98),
`RT_SPRITE_FIXED` (:101), `RT_SPARK` (:102), `RT_BEAM_Q3MME` (:108),
`RT_RAIL_RINGS_Q3MME` (:109), `RT_GRAPPLE` (:110).

### 7.2 Existing per-entity override call sites — **REUSE**

`customShader` has 61 call sites in cgame. The load-bearing ones:

- **`CG_AddRefEntityWithPowerups` — `cg_players.c:4245`** — a working N-pass
  overlay engine: `PW_INVIS`→`invisShader` (:4248), spawn armor (:4265),
  `PW_QUAD` (:4272/4274), `PW_REGEN` (:4279), `PW_BATTLESUIT` (:4288),
  freeze-tag ice (:4309). Re-adds the same refEntity with a different
  `customShader`.
- **`cg_playerShader` — `cg_players.c:4314-4320`** — forces an arbitrary
  shader over **every player** as an extra pass with `shaderRGBA` white.
  Registered `{ &cg_playerShader, "cg_playerShader", "", CVAR_ARCHIVE }` at
  `cg_main.c:2078` — **no cheat flag, no LATCH, live at runtime, and present
  in the shipped `cgamex86.dll`.**
- **`cg_wh*` x-ray system — `cg_players.c:4323-4358`** — `cg_wh`,
  `cg_whShader`, `cg_whEnemyShader`, `cg_whColor`, `cg_whEnemyColor`,
  `cg_whAlpha`, `cg_whEnemyAlpha`, `cg_whIncludeDeadBody`,
  `cg_whIncludeProjectile` (cvar table `cg_main.c:2074-2083`, all plain
  `CVAR_ARCHIVE`). Sets `customShader` + `shaderRGBA` + `renderfx |=
  RF_DEPTHHACK` (:4356) and re-adds. **A complete per-entity see-through-walls
  overlay already exists and is live.**
- Overlay passes must go through `CG_AddRefEntity` —
  `cg_localents.c:3231-3249` — which allocates a dummy local entity with
  `LEF_ALREADY_ADDED` so cgame's entity accounting stays correct. Do not call
  `trap_R_AddRefEntityToScene` directly.

### 7.3 Colorisation cvars — **REUSE**

`CG_CheckForModelChange` (`cg_players.c:5027`) already writes `shaderRGBA`
onto head/torso/legs from ~20 cvars: `cg_enemy{Head,Torso,Legs}Color`
(`cg_main.c:2101-2103`), `cg_team*Color` (:2117-2119), `cg_redTeam*Color`
(:2133-2135), `cg_blueTeam*Color` (:2149-2151), **`cg_deadBodyColor`**
default `0x101010` (:2198, applied `cg_players.c:5060-5069` on `EF_DEAD`),
CPMA per-client colours (`cg_players.c:5033-5036`), model scaling
`cg_playerModelForce{,Legs,Torso,Head}Scale` (`cg_main.c:2490-2498`, applied
`cg_players.c:6988+`). All present in the shipped cgame DLL.

### 7.4 Outline / rim light / chrome — **split verdict**

- **Chrome / envmap: REUSE, today.** `tcGen environment` →
  `TCGEN_ENVIRONMENT_MAPPED` — `renderergl1/tr_shader.c:1062`, computed in
  `RB_CalcEnvironmentTexCoords` — `renderergl1/tr_shade_calc.c:890-892`.
  Point `customShader` (or `cg_playerShader`) at a `tcGen environment` shader
  and you have chrome/gold players with zero engine changes.
- **True outline / rim: REPLACE.** Nothing exists in wolfcam. `grep -i
  outline` in cgame hits only `ITEM_TEXTSTYLE_OUTLINED` (`cg_local.h:106-107`)
  — UI text. Options: (a) fake it with an additive `tcGen environment` +
  inverse-ramp overlay pass through the existing `CG_AddRefEntityWithPowerups`
  machinery — cheapest, works today; (b) real inverted-hull, which needs a
  `GL_CULL_FRONT` + vertex-offset backend variant in `tr_shade.c` — genuine
  renderer work; (c) **q3mme's `r_framebuffer_rotoscope_zedge`**
  (`_forks/q3mme/trunk/code/renderer/tr_init.c:907`), a real depth-edge post
  pass — but q3mme-only, Path C.

### 7.5 EffectScripts

Wolfcam's cgame carries a full port of q3mme's script system —
`_canonical/code/cgame/cg_fx_scripts.c` (7739 lines), with
`re->customShader = trap_R_RegisterShader(ScriptVars.shader)` at :3390, :3497,
:3665, and a **hot-reload console command `fxload` → `CG_FXLoad_f`**
(`cg_consolecmds.c:6136`, registered :8535) →
`CG_ReloadQ3mmeScripts` (`cg_fx_scripts.c:7626`) → `CG_ParseQ3mmeScripts`
(:7502). `fxload` is present in the shipped `cgamex86.dll`. Semantics are
covered by the sibling EffectScripts research — noted here only because it is
the **existing precedent for a re-entrant, non-hunk hot-reload** in this
codebase, i.e. the template a future `shaderload` would copy.

### 7.6 Two defects found in passing

1. `_canonical/code/cgame/cg_effects.c:816` —
   `re->customSkin = trap_R_RegisterShader("xgibs");` assigns a **shader**
   handle to `customSkin`, which the renderer indexes into `tr.skins[]`
   (`tr_mesh.c:354-374`). Works only by accident when the handle lands in
   range; otherwise silently falls through to `tr.defaultShader`. Should be
   `customShader`, or `trap_R_RegisterSkin`.
2. `renderergl1/tr_mesh.c:307-316` and `tr_animation.c:209-218` mutate
   `ent->ePtr->frame/oldframe` in place. Since `ePtr` may alias a
   caller-owned struct, any override layer that reuses one `refEntity_t`
   across several `AddRefEntityToScene` calls — which
   `CG_AddRefEntityWithPowerups` does — inherits clamped frames from the
   previous pass.

---

## 8. Camera / view system

### 8.1 The per-frame chain, cgame → renderer

```
CG_DrawActiveFrame()                    cgame/cg_view.c:5710
 ├─ trap_R_ClearScene()                 cg_view.c:5897
 ├─ CG_CalcViewValues()   <-- builds cg.refdef        cg_view.c:6172
 ├─ CG_AddPacketEntities()                            cg_view.c:6187
 ├─ Wolfcam_OffsetFirstPersonView / Wolfcam_CalcFov   cg_view.c:6226 / 6254
 ├─ CG_VibrateCamera()                                cg_view.c:6323
 ├─ cg.refdef.time = cg.time; areamask memcpy         cg_view.c:6347-6348
 ├─ if (cg.freecam) CG_FreeCam()                      cg_view.c:6424-6427
 ├─ if (camera playing) CG_PlayCamera()               cg_view.c:6429-6439
 │                                        <== INJECTION SEAM (cg_view.c:6440)
 ├─ CG_AddLocalEntities()                             cg_view.c:6462
 ├─ q3mme DOF: CG_Q3mmeDofUpdate / trap_R_UpdateDof   cg_view.c:6488 / 6529
 └─ CG_DrawActive()                      cgame/cg_draw.c:11136
    ├─ cg.viewEnt look-at override                    cg_draw.c:11184-11197
    └─ trap_R_RenderScene(&cg.refdef)                 cg_draw.c:11211
       └─ syscall CG_R_RENDERSCENE       cgame/cg_syscalls.c:328-329
          └─ re.RenderScene(VMA(1))      client/cl_cgame.c:1175  (gated on cl.draw at :1174)
             └─ RE_RenderScene()         renderergl1/tr_scene.c:340
                ├─ fd -> tr.refdef copy                tr_scene.c:361-374
                ├─ viewParms_t built                   tr_scene.c:436-453
                └─ R_RenderView(&parms)  renderergl1/tr_main.c:1471 (called tr_scene.c:455)
```

`CG_CalcViewValues` — `cg_view.c:1302`. Key assignment points:
`memset(&cg.refdef, 0, ...)` :1305, `CG_CalcVrect` :1312, id-camera path
:1331-1365, intermission :1369-1374, demo-smoothing :1451-1464, normal
`vieworg`/`refdefViewAngles` from playerState :1470-1471, offsets
:1521-1533, **the single canonical `AnglesToAxis(cg.refdefViewAngles,
cg.refdef.viewaxis)` at :1541**, `return CG_CalcFov()` :1548.

`refdef_t` — `renderercommon/tr_types.h:163-179`: `x,y,width,height` :164,
`fov_x,fov_y` :165, `vieworg` :166, `viewaxis[3]` :167, `time` :170,
`rdflags` :172, `areamask` :175, `text[8][32]` :178. **Wolfcam added nothing**
— it is byte-identical to stock Q3, which matters because it crosses the VM
boundary. `RDF_` flags are only two: `RDF_NOWORLDMODEL` 0x0001 and
`RDF_HYPERSPACE` 0x0004 (`tr_types.h:78-80`) — **0x0002 and everything ≥
0x0008 are free bits** for a virtual-camera flag. Wolfcam's real additions
live one level down in `trRefdef_t` (`renderergl1/tr_local.h:461-496`):
`realTime` :470, `floatTime` :477, `realFloatTime` :478 — the
timescale-independent clock the MME path needs.

### 8.2 Virtual-camera injection seam — **EXTEND**

The seam exists; it just is not named. The cleanest point is
**`cgame/cg_view.c:6440`** — after every existing camera writer has finished
(`CG_CalcViewValues` :6172, wolfcam offsets :6226/:6254, `CG_VibrateCamera`
:6323, `CG_FreeCam` :6425, `CG_PlayCamera` :6430) but **before**
`CG_AddLocalEntities` (:6462), the DOF focus computation (:6497/:6521),
`trap_R_UpdateDof` (:6529) and `CG_DrawActive` (:6549) — so all of those see
the virtual camera. Four lines:

```c
VectorCopy(vcam.origin, cg.refdef.vieworg);
VectorCopy(vcam.angles, cg.refdefViewAngles);
AnglesToAxis(cg.refdefViewAngles, cg.refdef.viewaxis);
CG_AdjustedFov(vcam.fov, &cg.refdef.fov_x, &cg.refdef.fov_y);
```

The absolute-last alternative is `cg_draw.c:11210`, immediately before
`trap_R_RenderScene` at :11211 — nothing in cgame reads `cg.refdef` after
that, and there is precedent (`cg.viewEnt` look-at at :11184-11197,
`refdef.time` at :11201-11206). But it lands *after* entities/marks/particles
were added, so billboarding, LOD and RF_FIRST/THIRD_PERSON culling would have
been computed against the old camera. Use :6440 primarily, :11210 only as a
hard clamp, and guard against the `cg.viewEnt` re-stomp at :11184-11197.

Do **not** rewrite `CG_OffsetFirstPersonView` (`cg_view.c:755`, 160 lines of
bob/kick/land/duck feel, duplicated for follow mode at
`cgame/wolfcam_view.c:1324`). Override after; leave it alone.

**Structural note for later:** q3mme routes every view mode through **one**
funnel — `demoSetupView()` (`_forks/q3mme/trunk/code/cgame/cg_demos.c:107`)
switches on `demo.viewType` and writes only `demo.viewOrigin/viewAngles/
viewFov`, then commits to the refdef exactly once at `cg_demos.c:181-182` and
`:231-232`, *before* `CG_AddPacketEntities` (:616). Wolfcam by contrast has
~40 scattered `cg.refdef.vieworg` writes and three separate
`memset(&cg.refdef, 0, ...)` sites (`cg_view.c:1305`,
`wolfcam_view.c:1343`, `cg_draw.c:2880`). Adopting q3mme's funnel is a
**REPLACE of the plumbing, REUSE of all the math** — only worth it if many
camera modes are planned.

### 8.3 Spline / keyframe camera — **REUSE**

Wolfcam ships a production keyframe camera. Do not write another.

- Data model `cameraPoint_t` — `cgame/cg_camera.h:114-242`: origin, angles,
  `cgtime`, per-channel type, viewpoint/viewEnt with x/y/z offsets, fov +
  fovType, per-channel initial/final velocity for ease curves, and a
  `command[MAX_STRING_CHARS]` console command fired at the point.
  6 position modes (`cg_camera.h:61-69` — incl. `CAMERA_SPLINE_BEZIER`,
  `CAMERA_SPLINE_CATMULLROM`), 9 angle modes (:71-82), 4 roll modes (:84-90),
  5 fov modes (:92-99). `MAX_CAMERAPOINTS 512` (:7).
- **Evaluators are pure** — they take a time and fill an out-param, never
  touching `cg.refdef`: `CG_CameraSplineOriginAt` — `cgame/cg_camera.c:177`
  (arc-length parameterised, memoized at :250-265);
  `CG_CameraSplineAnglesAt` — :314 (quaternion slerp of 4 control points);
  `CG_CameraSplineFovAt` — :368.
- A **second**, independently imported q3mme evaluator also exists:
  `cgame/cg_q3mme_demos_camera.c` — `CG_Q3mmeCameraOriginAt` :157,
  `...AnglesAt` :231, `...FovAt` :280.
- Console commands (`cgame/cg_consolecmds.c`): `addcamerapoint` :8510,
  `clearcamerapoints` :8511, `playcamera` :8512, `stopcamera` :8513,
  `savecamera` :8514, `loadcamera` :8516, `selectcamerapoint` :8517,
  `deletecamerapoint` :8518, `editcamerapoint` :8520; q3mme variants
  :8590-8595; `freecam` :8478, `freecamsetpos` :8480,
  `freecamlookatplayer` :8570. In-world editor overlays at `cg_view.c:4769`,
  :4813, :4965.

**The evaluator is the asset; `CG_PlayCamera` (`cg_view.c:2843`, ~1370 lines
of mode dispatch, cvar coupling and freecam feedback) is the liability.**
Call the three `CG_Camera*At` functions directly from a virtual-camera hook.

**Direct relevance to `creative_suite/engine/director_session.py`:** that
module currently harvests keyframes by parsing `viewpos` console output out
of `qconsole.log`. The `savecamera` / `loadcamera` commands
(`cg_consolecmds.c:8514,8516`) plus the `cameraPoint_t` on-disk format
(`WOLFCAM_CAMERA_VERSION 10`, `cg_camera.h:10`) are a richer, structured
round-trip for the same data — worth evaluating as a replacement or
complement to the log-tailing approach.

### 8.4 Per-frame FOV — **REUSE**

No new plumbing needed. `CG_AdjustedFov(fov_x, *new_x, *new_y)` —
`cg_view.c:1018` — is a pure function honouring `cg_fovStyle` (0 = Quake3
hor+ :1035-1046, 1 = vert- :1109-1118, 2 = QL aspect buckets :1062-1080).
Five call sites already pass non-cvar values: :1350 (id camera), :2748
(q3mme cam), :4125 (wolfcam cam), :4300 / :4590 (freecam).
`CG_CalcZoom(fov_x)` — `cg_view.c:965` — is likewise pure.
`cg_fov.value` is consulted only as a *default* at `cg_view.c:1152` and
:1166 (cvar registered `cg_main.c:1377`).

One trap: `cgame/cg_q3mme_demos_camera.c:544-546` writes the fov **back into
the `cg_fov` cvar** via `trap_Cvar_Set` — the source already flags this at
line 1100 with `//FIXME wolfcamql shouldn't really set cg_fov`. That will
fight a per-frame virtual-camera FOV and archive garbage into the config.
Route around it.

### 8.5 Multi-camera — **REUSE (viewports) / EXTEND (offscreen)**

Two cameras into two on-screen viewports in one frame works today —
see §3.2 and the `CG_Draw3DModelExt` proof at `cg_draw.c:2866-2908`.
Render-to-texture from a second camera needs rgl2's `targetFbo` machinery
(`renderergl2/tr_main.c:2727-2749`); rgl1's `viewParms_t` has no such field.

---

## 9. Corrections this audit forces on existing project docs

| Doc | Claim | Reality |
|---|---|---|
| `docs/reference/replay-runtime-feasibility.md:156` | wolfcamql-src's `code/client`, `code/cgame` "do have real source — only the 3rd-party folders are stubbed" | `_canonical/wolfcamql-src/` holds **0 files**. The source is complete but lives at `_canonical/code/` (deduped up a level). The 3rd-party stubs are a separate, real issue |
| `engine/engines/dissection/wolfcamql-src/RENDERER_NOTES.md:9-26` | wolfcam has one `code/renderer/` dir; lists `tr_bloom.c` and `tr_glsl.c` in it | Wolfcam ships `renderergl1/` (24 files) **and** a full `renderergl2/` rend2 renderer (70 files, `tr_fbo.c`, `tr_postprocess.c`, 34 GLSL programs). No `tr_bloom.c` exists; bloom is inline at `renderergl1/tr_backend.c:703-1028` |
| `RENDERER_NOTES.md:41-45` | "For Tr4sH Quake, port quake3e's capture approach — pipe raw frames to ffmpeg" | q3mme **already has** `mme_pipeCommand` (`_forks/q3mme/.../tr_mme.c:815`, consumed `tr_mme_avi.c:258`). The shipped wolfcam exe also contains 41 `ffmpeg` string references and a `pipe` capture flag (`client/cl_main.c:6219-6235`) — worth verifying before writing new code |
| `RENDERER_NOTES.md:74-77` | "q3mme already has a more advanced renderer… we keep q3mme's renderer" | Directionally right for motion blur/DOF/rotoscope, but **wolfcam's renderergl2 is a strictly more modern renderer than q3mme's** (HDR, tonemap, SSAO, cascaded sun shadows, bokeh DOF, sun rays, DDS). The choice is less obvious than stated |
| `creative_suite/engine/master_profile.py:30` | "DoF SUPPORTED (`mme_dof*` + keyframed dof cmd)" | `mme_dofFrames` and `mme_dofRadius` are **absent from the shipped `wolfcamql.exe`** and from `cgamex86.dll`. Accumulation DOF exists only in the newer wolfcamql-src source and in q3mme. Motion blur (`mme_blurFrames`) and depth export (`mme_saveDepth`) **are** present, so the rest of that docstring holds |
| `master_profile.py:26` | "renderer: gl1 (`cl_renderer` default)" | There is no `cl_renderer` cvar in the shipped exe (0 string hits) and no `renderer_opengl*.dll` on disk. The build is **monolithic gl1**; renderer switching is not available at all, not merely defaulted |

None of these change any shipped output. They change scoping.

---

## 10. Ranked: most cinematic value for least engineering cost

### 1. Replace `scripts/colorcorrect.fs` in a `zzz_pantheon_grade.pk3` — full in-engine colour grading, **zero code**

Every frame we capture already passes through `RB_ColorCorrect`
(`renderergl1/tr_backend.c:2046`) running a GLSL program compiled from
`scripts/colorcorrect.fs` on the VFS (`tr_init.c:610`). Overriding that one
file gives film LUT, split-tone, vignette, chromatic aberration, grain,
halation and letterbox **baked into the master at capture time, at full
render resolution, before any ffmpeg re-encode**. `combine.fs` is a second
injection point carrying scene *and* bloom with four more live uniforms.
Turning on `r_enableBloom 1` (`tr_init.c:1961`, plain `CVAR_ARCHIVE`) plus
the eleven live `r_Bloom*` dials is a cfg edit.

Cost: one pk3, ~200 lines of GLSL, one smoke render. Constraint: the
replacement must reference all four uniforms or `ri.Error(ERR_FATAL)` fires
(`tr_backend.c:1126-1153`). Risk: low, isolated, instantly revertible by
deleting the pk3. Effort: **hours.**

### 2. Wire the live material/texture override API into the asset pipeline — hot-swap PANTHEON assets, **zero engine code**

`R_RemapShader` with the `userSet` channel (`renderergl1/tr_shader.c:68`,
resolved per-surface per-frame at `tr_shade.c:360-367`), the console commands
`remapshader` / `clearremappedshader` (`cg_consolecmds.c:7437,7465`),
`r_singleShader` + `r_singleShaderName` (`tr_init.c:1853-1854`) for map-wide
looks, `cg_playerShader` (`cg_main.c:2078`) for all-players looks, and
`RE_ReplaceShaderImage` (`tr_shader.c:3598`) for pixel-level swaps under a
stable handle — **all live in the binaries we launch today.** This is the
missing link that lets the Phase-5 ComfyUI photoreal output be evaluated *in
engine, in motion, at capture time* instead of only in `gallery.html`.
`tcGen environment` (`tr_shade_calc.c:890`) adds chrome/gold for free.

Cost: pk3 authoring plus a cfg/command generator in `creative_suite/engine/`.
No C. Effort: **days.** Caveat: `ReplaceShaderImage` only reaches
`stages[0].bundle[0].image[0]`, so multi-stage shaders need the
`R_RemapShader` route instead.

### 3. Turn on `mme_saveDepth` and consume the depth pass downstream — **one cvar**

`mme_saveDepth` (`renderercommon/tr_mme.c:382`, `CVAR_ARCHIVE`, confirmed in
the shipped exe) opens a second synchronized writer
(`client/cl_main.c:6212-6224`) emitting a `GLfloat`-per-pixel depth stream
alongside the colour capture, correctly accumulated across motion-blur
sub-frames (`tr_mme.c:170-171`). That unlocks, in the existing ffmpeg /
ComfyUI pipeline and with no engine work: post-DOF and rack focus (with far
more control than in-engine accumulation DOF, which is **not** in our binary
anyway), volumetric fog and depth-keyed atmosphere, depth-keyed grading and
sky replacement, and depth-conditioned ControlNet passes for the photoreal
track. Pairs directly with #1 — grade in-engine, relight in post.

Cost: one cvar plus a depth-stream reader in the render pipeline. Effort:
**hours to wire, days to exploit.**

### Runners-up, and why they rank lower

- **renderergl2 (SSAO, HDR tonemap, cascaded sun shadows, bokeh DOF, sun
  rays)** — the biggest visual jump available and already fully written
  (`_canonical/code/renderergl2/`, 70 files, 34 GLSL programs). But it is
  **not in the shipped binary**, and there is no `cl_renderer` switch to
  enable it. It is gated entirely behind Path C — and behind the harder
  half of Path C at that, since wolfcamql-src has no build files at all
  (`replay-runtime-feasibility.md:156`, 3-7 days before a first compile).
- **q3mme motion blur + rotoscope-zedge outlines + `mme_worldShader` +
  `mme_pip`** — genuinely excellent for the stylised direction, but every one
  of those strings is absent from our binary. q3mme is the *buildable* fork,
  so this is the natural Path C payload — just not free.
- **Virtual-camera injection at `cg_view.c:6440`** — only four lines, and
  wolfcam's spline evaluators (`cg_camera.c:177/314/368`) are already
  production-grade. But it needs the cgame VM rebuilt, which is the same
  toolchain gate, and Path A (`director_session.py`) already delivers most of
  the value with none of it.
- **Motion vectors / normal G-buffer** — genuinely absent everywhere
  (§2). Highest cost in the audit, and the accumulation motion blur we
  already ship covers most of what a velocity buffer would buy.

---

*Audit performed read-only. No source modified, nothing built, nothing
committed.*
