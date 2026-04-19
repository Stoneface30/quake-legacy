# wolfcamql-src — Renderer Notes

Renderer is **inherited from ioquake3** with minor patches. It is OpenGL-only;
no Vulkan, no D3D. For modern capture we cross-port from quake3e.

## Renderer module layout

```
code/renderer/
  tr_backend.c      — GL state management, draw call batching
  tr_main.c         — top-level frame submission, view setup
  tr_world.c        — BSP world rendering
  tr_surface.c      — surface type dispatch (brushes, patches, md3, md4)
  tr_shade.c        — shader stage execution (multitexture loops)
  tr_shader.c       — shader parsing (.shader files)
  tr_model.c        — md3/md4/iqm model loading + rendering
  tr_animation.c    — bone animation (md4)
  tr_mesh.c         — mesh drawing
  tr_light.c        — light grid, dynamic lights
  tr_sky.c          — skybox
  tr_marks.c        — decal / bullet-hole rendering
  tr_cmds.c         — command buffer (RB_* handlers)
  tr_image.c        — texture loading, mipmap, upload
  tr_bloom.c        — bloom post-process (ioquake3 addition)
  tr_glsl.c         — GLSL shader support (ioquake3 rend2 backend)
```

## Capture pipeline

Entry: `code/client/cl_avi.c::CL_TakeVideoFrame`
- Called from `SCR_UpdateScreen` every rendered frame when `cl_avidemo > 0`
- Reads framebuffer via `glReadPixels(GL_BGR, GL_UNSIGNED_BYTE, ...)`
- Writes frame to RIFF AVI file (either uncompressed or MJPEG via libjpeg)

**Known issues with wolfcam's AVI pipeline:**
- Uncompressed AVI hits 4 GB RIFF limit at ~40 seconds of 1080p60. Forces mid-split.
- MJPEG compression is single-threaded; bottleneck at 1080p60.
- No alpha channel capture.
- Frame-rate locking is approximate (cl_avidemo is a hint, not hard-locked).

**For Tr4sH Quake, port quake3e's capture approach instead:**
- Pipe raw frames to an ffmpeg child process over stdin
- ffmpeg handles encoding (x264/x265/AV1) and container (mp4/mkv/webm)
- No 4 GB limit, no CPU bottleneck, alpha via YUVA if needed
- Drop-in replacement at the `CL_TakeVideoFrame` call site

## Font system

- Bitmap fonts via `CG_LoadDeferredPlayers` path
- TrueType via `freetype2` (ioquake3 addition)
- `cg_drawText` is the main entry for HUD text
- **For PANTHEON title cards we DON'T render in-engine** — they go through ffmpeg
  drawtext in `phase1/title_card.py` per Rule P1-N

## Shader system

- `.shader` scripts in `baseq3/scripts/*.shader`
- Each shader has multiple stages, each stage is a texture + blend mode + TCmod chain
- Parse at map load in `tr_shader.c::ParseShader`
- **Relevant for our style-pack work:** shaders can override texture binding at the
  stage level. A `zzz_*.pk3` pack (per Rule ENG-2) with shader overrides replaces
  the visual appearance of anything without touching textures.

## Known quirks

- `r_fastsky 1` disables skybox entirely — important for clean captures without skybox
- `r_showtris`, `r_shownormals` leak into AVI capture if left on
- `r_fullbright 1` can be used to kill lighting (debug cvar, works at runtime)
- `cg_gun 0` hides the first-person weapon (useful for spectator-only captures)
- Viewport size must be set BEFORE `cl_avidemo` starts, not during

## Porting implications

For Tr4sH Quake (q3mme target):
- q3mme already has a more advanced renderer (motion blur accumulation, DOF)
- **We keep q3mme's renderer and port wolfcam's protocol, not the other way around**
- Any wolfcam-specific renderer patches should NOT be ported — they're stale vs q3mme
- Exception: wolfcam's `r_fixstencilwraps` cvar for z-fail shadows with QL maps
  (verify if q3mme has it, if not port just that one)
