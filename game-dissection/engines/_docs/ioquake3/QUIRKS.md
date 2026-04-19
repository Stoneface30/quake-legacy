# ioquake3 — Quirks and Gotchas

- Shader pipeline uses both fixed-function and GLSL depending on r_ext_framebuffer_object
- VM cgame vs native cgame — ioquake3 supports both; our port decisions follow
- cl_avi.c AVI writer hits RIFF 4 GB limit at ~40 seconds of 1080p60 — that's why quake3e replaced it

## See also
- `_docs/ioquake3/ARCHITECTURE.md`
- `_docs/ioquake3/EXTENSION_POINTS.md`
