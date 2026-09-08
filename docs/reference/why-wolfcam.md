# Why WolfcamQL (and not our own engine) — for the tool release

Written for the public release FAQ. Every claim below was verified in this
repo's own pipeline work (2026-08-30/31); source refs in
`moviemaking-feature-matrix.md` and `visible-weapon-master-config.md`.

## What WolfcamQL gives us for free

- **Protocol-73 playback that is already correct.** A decade of edge cases
  (QL server quirks, minqlx workarounds, `MAX_MSGLEN` doubling) is baked in.
  Reimplementing faithful *rendering* of demos is a different, much larger
  problem than parsing them — our parser proves the data side; wolfcam
  proves the pixels.
- **A real moviemaking toolkit**: `seekservertime` (raw ms seeks), the `at`
  scheduler (experimentally verified to take absolute demo serverTime),
  q3mme camera splines (Catmull-Rom/Bezier + quaternion angles + FOV
  keyframes), mme accumulation blur, DoF, depth passes, timescale-aware AVI
  capture, per-element HUD control, and a working AVI/MJPEG writer.
- **Deterministic offscreen capture**: `r_useFbo 1` renders to an offscreen
  target — capture is pixel-identical whether the window is visible,
  occluded or minimized, and (proven by A/B frames) immune to OS overlays
  like the NVIDIA toast.
- **Scriptability without IPC**: cfg + command line is enough to drive
  thousands of captures; no code injection needed.

## The problems we hit (and worked around)

These are the "graphics issues" a from-scratch engine would avoid — and
what they actually cost us in practice:

| Issue | Impact | Workaround |
|---|---|---|
| `fs_quakelivedir` ignored by the 11.3 build | no QL assets → `Com_Error` on default.cfg | stage pak00.pk3 into `baseq3/` next to the install |
| 32-bit binary, small zone/hunk | UHD texture set crashed `Z_Malloc` (one 2048² RGBA = 16.7 MB) | LAA flag on our staged exe + `com_zoneMegs 96` / `com_hunkMegs 256` |
| gun distorts at high FOV, no separate gun-FOV | limits world FOV to ≤110 with weapon visible | FOV 110 frozen from a visible-gun benchmark grid |
| `cl_aviCodec` defaults to uncompressed (376 MB/s) | first capture was 9.4 GB per 25 s | MJPEG q90 (bench-chosen); huffyuv/FFV1-pipe rejected/deferred |
| ffmpeg pipe mode silently falls back to AVI | no lossless mezzanine | accepted MJPEG q90 as master |
| occasional shader/asset fallbacks (`RE_RegisterShader` failures on missing QL DLC files) | cosmetic log noise, some stock effects fall back | harmless; the frames validated clean |
| GUI window required (no true headless) | a window flashes during batch capture | FBO capture makes window contents irrelevant |

## Why not our own engine (yet)

We *do* own the source and already modify our environment (LAA flag,
override paks, cfg-driven automation). A custom renderer would buy:
separate gun FOV, native segmentation/depth/mask passes, 64-bit memory,
and a real headless mode. It would cost: re-validating ten years of
protocol/rendering correctness, every shader path, and the entire q3mme
toolchain — months of work to reach the fidelity wolfcam gives today.

The pipeline is therefore split by strength:
- **our parser** owns truth (kills, trajectories, aim curves, visibility);
- **wolfcam** owns pixels (capture + q3mme cinematics);
- **our tooling** owns everything around them (selection, ranking, shot
  plans, assembly) — and treats wolfcam as a replaceable renderer behind a
  frozen capture-profile contract, so a future engine swap changes one
  layer, not the archive.
