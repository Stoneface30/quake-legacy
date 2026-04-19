# quake3e — Extension Points

## Capture via ffmpeg

**Location:** `code/client/cl_avi.c` (replaced ioquake3's AVI writer)

- Spawns `ffmpeg -f rawvideo -pix_fmt rgb24 -s <w>x<h> -r <fps> -i - -c:v libx264 ... output.mp4`
- Pipes raw framebuffer bytes to stdin via `popen` (POSIX) or `CreatePipe` (Win32)
- Process lifecycle: open on capture start, write per frame, close on capture stop

**Hook for us:** this is **the template** for upgrading q3mme's capture pipeline.
Steal this code wholesale during the Tr4sH Quake work.

## Vulkan renderer switching

**Location:** `cl_cgame.c` + `tr_init.c` equivalents

- `cl_renderer` cvar: `"opengl1"` or `"vulkan"`
- At engine init, loads the corresponding `renderer*` module
- Runtime switch requires `vid_restart`

**For automation:** set `cl_renderer vulkan` in autoexec.cfg; no user action needed.

## CMake targets

- `quake3e` — client binary
- `quake3e-server` — dedicated server binary (we don't need this)
- Renderer modules built as `renderer_gl1`, `renderer_vulkan` shared objects

## Cvars worth knowing

- `cl_renderer` — opengl1 / vulkan
- `r_mode` — resolution index (or -1 for custom via r_customwidth/height)
- `r_fullscreen` — obvious
- `r_vsync`
- `r_msaa` — multi-sample anti-aliasing (0/2/4/8 on GL; up to 16 on Vulkan)
- `r_hdr` — Vulkan-only, 16-bit color pipeline
- Capture: ffmpeg-path cvars (e.g. `cl_aviCodec`, `cl_aviFormat`) — extensible via
  recompiling the cl_avi.c stub

## See also

- `_docs/quake3e/RENDERER_NOTES.md` — Vulkan specifics
- `_docs/q3mme/EXTENSION_POINTS.md` — how to graft these into q3mme
