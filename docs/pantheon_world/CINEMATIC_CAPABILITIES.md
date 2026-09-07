# What the renderer can already do for a title — researched, then verified here

Researched from primary sources (q3mme and WolfcamQL repositories, their own
`cvars.txt`/`cmds.txt`, and the `Cvar_Get` registrations in the source), then
checked against **our** forked tree at
`engine/pantheon_renderer/wolfcamql-11.3-src/`. Defaults below are the ones
our source registers, not the ones a forum remembers.

## The finding that matters

**WolfcamQL 11.3 — the tree PANTHEON's renderer is forked from — already
contains q3mme's MME renderer and a bloom pipeline.** They were there before
we started. `renderer/tr_mme.c`, `renderer/tr_mme.h`, the `r_Bloom*` set in
`tr_init.c` and the GLSL passes in `tr_backend.c`.

## Bloom — WORKS in our host, verified 2026-09-07

Registered in `renderer/tr_init.c:2623-2634`:

| cvar | default | note |
|---|---|---|
| `r_enableBloom` | `0` | needs `r_useFbo 1` |
| `r_BloomPasses` | `1` | 2-3 widens the glow |
| `r_BloomIntensity` | `0.750` | |
| `r_BloomBrightThreshold` | `0.125` | lower = more of the frame blooms |
| `r_BloomSaturation` | `0.800` | |
| `r_BloomSceneIntensity` / `r_BloomSceneSaturation` | `1.000` | the untouched scene |
| `r_BloomTextureScale` | `0.5` | `CVAR_LATCH` |
| `r_BloomBlurScale` / `Falloff` / `Radius` | `1.0` / `0.75` / `5` | wolfcam's README says the last two are **not implemented** |
| `r_useFbo`, `r_fboAntiAlias` | `0`, `0` | both `CVAR_LATCH`; AA needs the FBO |

Filmed on the PANTHEON lockup at off / subtle / strong / +FBO AA:
`docs/visual-record/2026-09-07/bloom/panel_bloom.png`. All four rendered, on
software Mesa, with the Gallium driver pinned.

## Motion blur and depth of field — present in the source, NOT yet wired here

`mme_blurFrames` (default `0`), `mme_blurType` (`gaussian`; also `triangle`,
`median`), `mme_blurOverlap`, `mme_blurJitter`, `mme_dofFrames` (`0`),
`mme_dofRadius` (`2`), `mme_saveDepth`, `mme_depthFocus`, `mme_depthRange`
(wolfcam registers `2000`, q3mme `0`).

**Why they will not just work for us yet:** both accumulate *several engine
frames* into one output frame through the MME capture path. Our host renders
one frame and reads the pixels back itself, so it bypasses that path. Wiring
it is a real task, not a cvar.

Values people who ship movies actually use, quoted rather than invented:
`mme_blurFrames` 12-32 ("values between 12 and 32 give nice motion blur",
q3mme camera tutorial); `mme_blurOverlap` **leave at 0** — the q3mme
maintainer: "nobody is supposed to use it, it has no useful function anymore";
`mme_dofFrames` 40+ with `mme_dofRadius` under 10; `mme_depthFocus` ~1024,
`mme_depthRange` 512+.

**The timing trap, from both READMEs:** effective engine fps = capture fps x
blur frames. 120 fps with 20 blur frames is 2400 fps of work, and a camera
driven by real time will speed up. Record the path first, play it back while
capturing.

## Capture, for when we film motion

* WolfcamQL: `/video [avi|avins|tga|jpg|png|pipe] name <base>`, `/stopvideo`;
  `cl_aviFrameRate` `50`, `cl_aviCodec` `uncompressed|mjpeg|huffyuv`,
  `cl_aviPipeCommand` pipes raw frames to ffmpeg (`-crf 19`, mkv).
  `cl_aviMotionJpeg` is **removed**; `cl_avidemo` does not exist here.
* The `at` scheduler is a real command: `at <servertime|clock> <command>` —
  the same mechanism `shot.py` already uses for timed cvars.
* q3mme: `capture avi|png|pipe <fps> <name>`, `mme_renderWidth/Height` for
  offscreen above screen resolution, `mme_pipeCommand` with `%o %a %f %w %h`.

## Camera systems worth consuming rather than reinventing

WolfcamQL has both its own keyframe camera (`addcamerapoint`, `ecam` with
`spline`, `interp`, `curve`, `splineBezier`, `splineCatmullRom`, per-point
`fov`/`angles`/`offset`/`roll` modes) **and** a q3mme compatibility layer
(`q3mmecamera`, `playq3mmecamera`, `cg_q3mmeCameraSmoothPos`). PANTHEON's own
camera planner produces dense keyframes and does not need these, but they are
the reference for what a camera keyframe should carry.

## Sources

q3mme: <https://github.com/entdark/q3mme> (`cvars.txt`, `cmds.txt`,
`trunk/code/renderer/tr_mme.c`, `tr_bloom.c`, `tr_framebuffer.c`) ·
tutorials at <https://q3mme.proboards.com/thread/12>,
<https://q3mme.proboards.com/thread/18>,
<https://q3mme.proboards.com/thread/490> ·
WolfcamQL: <https://github.com/brugal/wolfcamql> (`README-wolfcam.txt`).

Flagged as unverified by the research: q3mme `camera smoothPos`/`smoothAngles`
defaults (not documented), `fx_*` defaults, and an older jaMME pipe command
string that contradicts current master.
