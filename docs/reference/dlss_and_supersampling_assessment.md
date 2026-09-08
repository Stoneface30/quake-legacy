# Can we render in DLSS?

**No — and it is the wrong tool for this pipeline anyway.** Both halves of
that sentence matter, because the first half sounds like a limitation and the
second half is the actual finding.

Assessed 2026-09-08 against the shipped binary, the engine source trees, and
NVIDIA's current SDK documentation.

---

## 1. Why it cannot run

DLSS reconstructs a cheaply-rendered frame into an expensive-looking one. To
do that it needs three things from the renderer every frame:

| DLSS requires | wolfcamql 11.3 has |
|---|---|
| per-pixel screen-space **motion vectors**, 16 or 32 bit | **nothing.** No velocity buffer, no previous-frame view-projection matrix, no multiple-render-target path in the binary's GL imports |
| the **depth buffer** | **yes**, but written to disk as a per-frame TGA sequence (`mme_saveDepth`), not exposed as a live GPU resource |
| sub-pixel **jitter**, ≥16 phases | **nothing.** Every "jitter" symbol in the binary belongs to libspeex's *audio* jitter buffer. The projection matrix is unjittered |

And the API is the harder blocker. The capture renderer is **fixed-function
OpenGL 1.x** — `glBegin`, `glVertex3f`, `glMatrixMode`, ARB/EXT extensions,
SDL 1.2. The only shader calls in the binary are the ARB shader-object
generation used for the bloom and colour-correction post-pass. The NGX SDK
that DLSS ships in provides **CUDA, Vulkan, D3D11 and D3D12** bindings. There
is no OpenGL entry point, and there never was one to deprecate.

Two corrections worth recording, because both are easy to get wrong:

- **DLSS 5 does exist.** Announced March 2026, shipped September 2026. It is
  "3D-Guided Neural Rendering", RTX 50-series only, and it is a *different
  stage* rather than a new upscaler generation — the mainline upscaling stack
  is DLSS 4.5. It still consumes motion vectors, so it does not relax the
  requirement this engine fails.
- **The hardware is not the problem.** An RTX 5060 Ti qualifies for every DLSS
  component including the 50-series-only ones. The engine is the problem.

### Nothing bolts it on afterwards

| Approach | What it really is | Verdict |
|---|---|---|
| NVIDIA App "DLSS Override" | Swaps the model inside an integration the game **already ships** | Cannot add DLSS where none exists |
| OptiScaler | Intercepts **existing** DLSS/FSR/XeSS calls; DX11/DX12/Vulkan only | No OpenGL, and nothing to intercept |
| NVIDIA Image Scaling | A real driver-level **spatial** upscale + sharpen, works on anything | Works, but it is a sharpen filter with no temporal history — and doing the same thing offline in ffmpeg is strictly better, because offline we are not racing a frame budget |
| DLDSR | Render *above* native, AI-downscale. The right *idea* | Injects into display mode lists; our capture is windowed on a hidden desktop with no display attached. Not applicable |
| Third-party "DLSS feeder" DLL hooks | Synthesise fake motion vectors from optical flow via a ReShade `opengl32.dll` hook | No. Guessed flow is not geometric motion, **the source still has no jitter**, and unvetted DLL injection is exactly what the project's supply-chain policy exists to refuse |

---

## 2. Why it is the wrong question

DLSS exists to buy **frame rate**. It trades image fidelity for speed so an
interactive game hits a budget.

This pipeline renders offline, from recorded demos, once. There is no frame
budget. Trading fidelity for speed is backwards here.

The one idea in the DLSS family that points the right way is DLDSR's —
**render above the delivery size and filter down** — and we do not need NVIDIA
for it, because we control both the render size and the downscale.

---

## 3. What we do instead, and what was wired today

The engine has **no supersampling switch**. The only mechanism is to request a
custom mode larger than the delivery size and downsample outside the engine.
That was already designed: `RenderProfile.internal_scale` in
`creative_suite/engine/render_profile.py` has described exactly this since it
was written.

**Nothing read it.** `internal_size` had one consumer in the whole tree, and
that consumer was its own test — so every master render silently shipped at
1×, and the ladder was decoration.

Wired 2026-09-08:

- `render_profile.capture_geometry(profile)` — the size to **capture** at, the
  size to **deliver**, whether a downsample is mandatory, and the linear-light
  `zscale` filter to do it with. Filtering in gamma space would lose the very
  contrast the extra pixels were rendered to capture; the bundled ffmpeg
  carries libzimg, so linear-light Lanczos is available.
- `render_profile.supersample_blockers(profile)` — what stands between a
  profile and a trustworthy capture, so the failure modes are named rather
  than discovered overnight.

| Profile | Captures | Delivers | Cost | Verified |
|---|---|---|---|---|
| `REVIEW` | 2560×1440 | 2560×1440 | 1.0× | yes |
| `MASTER_RASTER` | **5760×3240** | 3840×2160 | 2.25× | **no** |
| `MASTER_HERO` | 7680×4320 | 3840×2160 | 4.0× | no — and its backend does not exist |

### The blockers, stated plainly

`MASTER_RASTER` has **never been captured end to end** at 5760×3240.
Framebuffer limits, depth precision, stability and disk throughput are all
unproven until one canary runs. Beyond that:

- The capture window is smaller than the requested render size. Whether the
  platform layer grants an oversized framebuffer is a question for a **frame
  grab**, not for reading source. The FBO path (`r_useFbo`) blits a large
  render target down to a smaller visible window in the gl2 renderer; whether
  the **gl1** renderer we actually use honours that is the single thing one
  canary would settle.
- A lossy intermediate throws away the detail the extra pixels were rendered
  to capture. `MASTER_RASTER` already specifies `huffyuv`, which is correct;
  `supersample_blockers` flags any profile that does not.

### Also already available, also unused

`mme_blurFrames` is registered in the runtime and accumulates N sub-frames per
output frame. That is **temporal supersampling**, and it is the honest offline
analogue of what TAA and DLSS approximate in real time — without any of the
ghosting, because it accumulates *within* a frame rather than across output
frames. It is deliberately off for gameplay masters as a creative choice, not
a technical limit.

(`mme_dofFrames` is accepted by the console but never registered — a silent
no-op in 11.3. Depth of field is not available, whatever the name suggests.)

---

## 4. The recommendation

1. **Run one canary** at 5760×3240 with `huffyuv`, and grab a frame. That
   single capture either promotes `MASTER_RASTER` to verified or tells us the
   framebuffer ceiling. Everything above is a plan until it runs.
2. **Downsample with `zscale` in linear light**, not the default `scale`.
3. **Do not** reach for an offline AI upscaler on rendered frames as the
   quality ceiling. ESRGAN-class models *hallucinate* plausible detail; they
   do not recover real detail. Since every clip can be re-rendered from the
   demo corpus, supersampling strictly dominates. AI upscaling is a rescue
   tool for footage that cannot be re-rendered — which is exactly what the
   existing PH5 routing rules already say.
4. **Do not** mistake any of this for a path to DLSS. Everything here tops out
   at a sharper Quake 3 frame. HDR, shadow maps, material response and real
   motion vectors need a different renderer — which the profile table already
   calls `MASTER_HERO` on `BACKEND_MODERN_RASTER`, `exists_today=False`, and
   which Rule HL-4 says not to build in order to remove Wolfcam.

**One line:** DLSS cannot run here because the renderer is fixed-function
OpenGL with no motion vectors and no jitter, and no DLSS generation has ever
supported OpenGL. The right technique for an offline pipeline is the opposite
one — render high, filter down — which the engine already permits, which the
profile table already described, which nothing was reading, and which now has
a consumer and one canary standing between it and use.
