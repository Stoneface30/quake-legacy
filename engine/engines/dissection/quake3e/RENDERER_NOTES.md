# quake3e — Renderer Notes

Two parallel renderers ship: OpenGL (stock ioquake3 + patches) and Vulkan (novel).

## OpenGL renderer (`code/renderer/`)

Close to ioquake3 baseline. Minor additions:
- Better high-DPI window creation
- Improved `r_modeFallback` handling (doesn't brick on missing mode)
- GLSL shader pass bugfixes

For motion blur / DOF, relies on standard accumulation-buffer tricks (same as
q3mme's approach). Not as polished as q3mme's implementation.

## Vulkan renderer (`code/renderervk/`)

Full Vulkan 1.0 implementation. Highlights:
- Pipeline caching (faster cold-start than OpenGL)
- MSAA up to 16x
- HDR color pipeline (16-bit per channel with `r_hdr 1`)
- Tessellation for curved surfaces (optional)
- Better draw-call batching than GL renderer

**For Tr4sH Quake final-render phase:** Vulkan at 4K + HDR is the target for the
highest-quality pass. Our workflow becomes:
1. Render demo in q3mme with motion blur + DOF (GL path, 1080p, TGA sequence)
2. Post-process in ffmpeg (grade, title overlay, music mix)
3. For "showcase" quality: re-render key moments in quake3e Vulkan at 4K HDR,
   composite with the 1080p edit

## Capture pipeline (THE killer feature for us)

**Location:** `code/client/cl_avi.c` (fully replaced from ioquake3)

Pseudocode:
```c
void CL_OpenAVIForWriting(const char *name) {
    // spawn: ffmpeg -f rawvideo -pix_fmt rgb24 -s WxH -r FPS -i - -c:v libx264 -preset slow -crf 17 name.mp4
    afd = open_ffmpeg_pipe(w, h, fps, codec_args, name);
}
void CL_TakeVideoFrame(void) {
    glReadPixels(0,0,w,h, GL_RGB, GL_UNSIGNED_BYTE, framebuf);
    flip_rows_inplace(framebuf, w, h);  // OpenGL origin is bottom-left
    write(afd->stdin_fd, framebuf, w*h*3);
}
void CL_CloseAVI(void) {
    close(afd->stdin_fd);  // signals ffmpeg EOF
    waitpid(afd->pid, &status, 0);
}
```

**For us:** this is the ~50 lines we graft into q3mme. Easy port. Gets us:
- Unlimited file size
- Hardware-encoder support (via ffmpeg's h264_nvenc / hevc_nvenc)
- Direct mp4/webm/av1 without an intermediate step

## Quirks

- Vulkan renderer requires `r_fullscreen 0` on some Windows drivers during dev —
  fullscreen Vulkan can deadlock on window activation
- HDR path (`r_hdr 1`) requires tone-mapping via a shader pass at output — otherwise
  colors look washed out on SDR displays. Tone-map config via `r_hdrExposure`.
- MSAA and HDR don't combine on some GPUs (driver bugs) — fall back to MSAA-off for
  HDR captures

## See also

- `_docs/q3mme/RENDERER_NOTES.md` — accumulation-buffer motion blur (what we port WITH)
- `_diffs/code/client/cl_avi.c.diff.md` — line-by-line diff vs ioquake3
