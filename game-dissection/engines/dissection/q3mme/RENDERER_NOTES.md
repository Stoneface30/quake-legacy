# q3mme — Renderer Notes

q3mme's renderer is **ioquake3-derived OpenGL** with movie-capture extensions:
- Accumulation buffer for motion blur + DOF
- Multi-pass rendering for anti-aliasing
- TGA/PNG/JPG frame output in addition to AVI
- External .wav audio capture

No Vulkan, no D3D. For Tr4sH Quake, we may eventually graft quake3e's Vulkan backend
on top — but proto-73 port comes first.

## Motion blur (the killer feature)

**Location:** `trunk/code/cgame/cg_demos_capture.c::CG_DemosCaptureFrame`

Algorithm:
```
For each output frame at time t:
  Clear accumulation buffer
  For i in 0..N-1:
    Render scene at time t + i * shutterOpen / N   // shutter samples
    glAccum(GL_ACCUM, 1.0 / N)                     // accumulate weighted
  glAccum(GL_RETURN, 1.0)                          // read out blurred frame
  Write frame to disk / AVI
```

Typical `mme_motionBlurFrames = 16`. At 60 fps output → 960 subframes per second of
rendering. **Fragmovie-quality.**

**Precision issue:** 8-bit accumulation buffer clips when N > 16. For higher-quality
captures we need GL_FLOAT accumulation — available on modern GL but requires code
changes in `cg_demos_capture.c`.

## Depth of field

**Location:** `trunk/code/cgame/cg_demos_dof.c`

Algorithm: render multiple passes with jittered view positions around the
focal point, accumulate. Same accumulation-buffer pattern as motion blur.

`mme_dofFrames = 16` is typical.

**Performance:** DOF + motion blur combine multiplicatively — `mme_motionBlurFrames * mme_dofFrames`
subframes per output frame. 16 x 16 = 256 subframes per output frame. Fragmovie-quality
(1080p60) can take 10-30× realtime to render. Acceptable for offline use.

## Capture formats

- `mme_saveShot` = `tga` | `png` | `jpg` — per-frame stills
- `mme_saveStats` — write statistics sidecar
- AVI via stock ioquake3 path (`cl_avi.c`) with mme_aviLimit for size splits
- `mme_saveWav = 1` — separate audio capture to .wav (mux externally)

**Recommended workflow:** TGA frame sequence + .wav audio, muxed with ffmpeg
externally. Avoids the AVI 4GB limit entirely and gives us lossless input to our
final encoder pass.

## Supported extensions (OpenGL)

- ARB_multisample (hardware AA)
- ARB_texture_compression (shipping baseq3 shaders)
- EXT_blend_subtract (bloom, some shaders)
- Accumulation buffer (legacy GL, critical for motion blur)

**The accumulation buffer is LEGACY GL.** Modern GL contexts (3.0+ core) don't have
it. q3mme requests a compat-profile context. If we ever move to core-profile OpenGL
or Vulkan, we'll need to replace accumulation with shader-based temporal blending
in a custom framebuffer.

## Shader system

Standard Q3 `.shader` scripts, same as wolfcam. q3mme adds:
- `mme_depthRange` cvar for adjusting DOF focal plane per-demo
- Shader stage overrides via the demo effects subsystem

## Relevant cvars

- `mme_blurFrames` — motion blur count (default 8, push to 16-32 for quality)
- `mme_blurShutter` — shutter open time as fraction of frame time (0.5 default)
- `mme_dofFrames` — DOF sample count (default 8)
- `mme_dofRadius` — bokeh radius
- `mme_dofFocus` — focal distance
- `mme_saveShot` — output format
- `mme_jpegQuality` — JPG quality if using .jpg output
- `mme_aviLimit` — AVI split size in bytes (default ~2GB)

## Porting notes (Tr4sH Quake)

- Keep q3mme's renderer as the baseline. It's fragmovie-grade already.
- Do not port wolfcam's renderer patches over — they're ioquake3-baseline, stale.
- Future (Phase 3.5+): graft quake3e's Vulkan backend via conditional `#ifdef USE_VULKAN`
  — preserves q3mme's GL path for users who want accumulation-buffer motion blur,
  adds a Vulkan path for 4K/HDR work via frame-by-frame export to ffmpeg.

## Known quirks

- `mme_motionBlurFrames > 32` → visible banding due to 8-bit accum buffer
- `mme_saveWav = 1` + AVI at same time = sync drift. Use TGA-sequence workflow.
- DOF + motion blur + bloom stacked → GPU VRAM can OOM at 4K. Drop bloom first.
- TGA output is uncompressed; 10 minutes of 1080p60 TGA = ~120 GB. Plan disk.
