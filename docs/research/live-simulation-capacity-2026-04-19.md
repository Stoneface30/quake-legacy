# Live Simulation Capacity — 2026-04-19

## Executive Summary

Live-sim is **mostly a concept**, with one thin end-to-end path that is
technically working but fragile. We have (a) a real `EngineSupervisor`
that spawns `wolfcamql.exe`, writes `seekclock` over stdin, screen-grabs
frames with PIL `ImageGrab`, and pushes JPEG bytes over a FastAPI
WebSocket at ~4 Hz, and (b) a single-worker `JobQueue` (depth=1) that
drives both the Tier A preview (fresh wolfcam capture → ffmpeg
transcode) and the Tier B rebuild (subprocess of
`phase1/render_part_v6.py`). Everything else — the TR4SH vision of a
forked engine exposing a scene-graph via JSON-over-pipe, agent-driven
kill-cam / free-cam, ComfyUI hot-swap per capture — is spec text only.
Panel 8's "engine scrub" is a **pure canvas mock** with no backend
binding; the real WebSocket client lives in `panel-preview.js`. Net: we
can trigger one draft mp4 render and one live scrub session from the UI
today; we cannot yet drive a scene-graph-aware render in real time.

> **Source caveat:** the Python modules covered below live on branch
> `creative-suite-v2-step2`, not on the current
> `design/phase1-pantheon-system` branch. The working tree has
> `__pycache__` only — content was read via
> `git show creative-suite-v2-step2:<path>`.

## The TR4SH Vision (what "live" means here)

From `docs/superpowers/specs/2026-04-17-tr4sh-quake-manifesto.md`:
TR4SH QUAKE is supposed to be **one binary** — a q3mme fork with
protocol 73 patches, a new C module `cg_scene_export.c` that emits scene
state as JSON-over-WebSocket every frame, and an embedded FastAPI child
process that exposes three agent primitives (`free_cam_at`,
`kill_cam_of_frag`, `read_framebuffer_as_png`). "Live" in this vision
is: demo time-index ↔ scene tree ↔ agent decision ↔ render, all
in-process, with ComfyUI style swaps applied between captures without
restarting the engine. Gate T5 = one Part 4 clip end-to-end through
TR4SH Quake with wolfcam untouched. None of this C / fork / scene-graph
code exists yet.

## Engine Supervisor (creative_suite/engine/supervisor.py)

**Real, 90 LOC, one test.** `EngineSupervisor.start()` uses
`asyncio.create_subprocess_exec` to launch `engine_cmd` (the wolfcamql
CLI) with stdin=PIPE, stdout/stderr=DEVNULL. `seek(ms=…)` formats
`seekclock M:SS.s\n` and writes to the process stdin (the test verifies
the bytes reach the child). A background `_grab_loop` sleeps 250 ms (=
4 Hz), calls `PIL.ImageGrab.grab(all_screens=False)`, encodes JPEG
quality=70, and pushes into an `asyncio.Queue[bytes]` of maxsize 4
(drops oldest when full — producer never blocks). `next_frame(timeout_s)`
is what the WebSocket handler awaits. `mock_grab=True` short-circuits
grab to a hard-coded `b"\xff\xd8\xff\xe0mockjpeg"` so the test passes
without a GUI.

Known limitations baked in:
- Frames come from *the user's whole desktop*, not the wolfcam window —
  `ImageGrab.grab(all_screens=False)` grabs the primary monitor. Wolfcam
  needs to be topmost for frames to be useful.
- 4 Hz is hard-coded (`await asyncio.sleep(0.25)`); no dynamic rate.
- There is no health check — if wolfcam fails to launch or segfaults,
  the grab loop just keeps returning desktop frames until stop.
- Seek latency is open-loop; we send `seekclock` but don't confirm the
  engine reached that frame before grabbing.

## Job Queue & Workers

`creative_suite/api/_render_worker.py` — a single **`JobQueue`** class.
- Depth = 1 enforced in `submit()`: second submit raises
  `RuntimeError("busy — another render is running")` which the routers
  translate to HTTP **409**.
- Worker is one `asyncio.Task` started at app boot via `start()` /
  stopped at shutdown via `stop()`, driven by an `asyncio.Event`.
- `emit(phase, pct, msg)` is passed to each job. Events are appended to
  a per-job list; SSE endpoint polls at 500 ms with a ~10 min cap
  (`range(1200)`).

Three job types consume this queue, all in `creative_suite/api/`:

1. **`_preview_job.run_preview_tier_a`** — launches wolfcam with
   `+exec preview.cfg`, awaits its exit, globs the produced AVI,
   transcodes via ffmpeg `libx264 -crf 23 -preset veryfast`.
   Cancellation path explicitly terminates the subprocess.
   `CS_PREVIEW_MOCK` env var skips the actual subprocesses and writes a
   stub mp4 for tests.
2. **`_rebuild_job.rebuild_part`** — spawns
   `python phase1/render_part_v6.py` as a child, streams its stdout
   line-by-line as events, infers phase strings via keyword matching
   ("xfade", "ebur128", "sync_audit"), writes a `render_versions`
   SQLite row + flow-plan git tag on success. This is the one that
   actually produces a shipping Part mp4.
3. **`capture.py` POST /api/capture/gamestart** — synchronous (no job),
   just writes a gamestart.cfg file for out-of-process Phase 2
   launchers to pick up.

## Panel 8 Engine Scrub Prototype

`creative_suite/frontend/prototypes/panel8/index.html` — **24,821 bytes,
100% mock**. Not wired to backend. Canvas rendering only.

What it demos:
- Header bar with `conn-led` + `ENGINE IDLE` / `ENGINE LIVE` indicator
  (fake; just `setInterval` on 1000/STREAM_HZ = 250 ms)
- Frame area that draws a simulated Quake arena in canvas: gradient sky,
  floor grid, fake HUD overlay ("SEEKCLOCK 8:52.1", "FRAME 532/5700"),
  crosshair, weapon silhouette, seam-proximity red vignette
- Time ruler with seam markers at hard-coded SEAM_TIMES (8 values)
- **Scrub-by-drag** on the frame area (mousemove →
  `dragStartTime + dx * 0.1s`)
- Full scrub track + ruler click-to-seek

It ships the UX pattern; the *real* engine WebSocket binding lives in a
different file (`panel-preview.js::wireEngine`) on the
`creative-suite-v2-step2` branch — that one opens
`ws://.../api/phase1/parts/{n}/engine`, sends `{cmd:"seek", t_ms}`,
receives `{kind:"frame", t_ms, jpeg_b64}` and stuffs it into an
`<img src="data:image/jpeg;base64,...">`.

## Capture Config Writer

`creative_suite/capture/gamestart.py` — the "§4.4 max-quality block"
verbatim (any reorder breaks the cfg-diff smoke test):

```
r_mode -1
r_customwidth 3840
r_customheight 2160
cg_fov 100
r_picmip 0
r_textureMode GL_LINEAR_MIPMAP_LINEAR
r_ext_texture_filter_anisotropic 1
r_ext_max_anisotropy 16
r_lodbias -2
r_subdivisions 1
cg_drawFPS 0 / cg_draw2D 0 / cg_drawCrosshair 0
com_maxfps 125
com_hunkmegs 512
set sv_pure 0
cg_drawGun {1|0}         ← FP spine vs FL angle
seekclock M:SS; video avi name :<demo>; at M:SS quit
```

Semicolon / newline injection in `demo_name`, `seek_clock`, `quit_at`
is rejected with `ValueError` (HTTPException 400 at the API layer).
There's also a **`PREVIEW_CVARS`** block that downgrades to 1080p /
picmip 1 / 60fps / aniso 4 / HUD off, used by Tier A draft capture —
that's the `write_preview_cfg()` function wolfcam reads on each preview
launch.

## Live-Preview Loop (ComfyUI + wolfcam)

**ComfyUI**: `creative_suite/comfy/` has a real HTTP client
(`httpx.Client` → `/prompt`, `/upload`, `/view`, `/history`) and a
runner that pulls asset bytes from a pk3, sends an SDXL img2img
workflow, polls history until done, writes a PNG, updates the variants
DB row. This is batch-only — no live preview loop, no per-frame
ComfyUI. Runtime is measured in seconds per image. The TR4SH "ComfyUI
hot-swap between captures" is not implemented; nothing reloads
`fs_homepath` dynamically.

**Wolfcam**: always launched, always exits. There is no persistent
wolfcam process that we drive continuously — each Tier A preview is a
fresh spawn. The one exception is the Tier B **engine WebSocket** in
`phase1.py::engine_ws`, which holds one wolfcam alive for the duration
of the WS connection. That's the only "live" engine in the codebase.

**Frame streaming** plumbing: only one place ships bytes. `engine_ws`
base64-encodes each JPEG from `EngineSupervisor.next_frame` and sends
`{kind:"frame", t_ms, jpeg_b64}` JSON over the accepted WebSocket. No
SSE video, no HLS, no WebRTC, no MSE.

## Scene Graph / JSON-over-Pipe

**Zero code hits.** Grep for `scene_graph`, `cg_scene_export`,
`free_cam_at`, `kill_cam_of_frag`, `read_framebuffer` finds only the
manifesto spec file (+ worktree copies). There is no Python parser of a
scene graph, no C module emitting one, no named pipe / UDS plumbing on
the engine side. The `.dm_73` parser in `phase2/dm73parser/` extracts
obituary events offline — that's our only "scene" knowledge today, and
it's batch JSON Lines, not a live stream.

## End-to-End Dry Run

**Can we trigger a live scene render from the UI today?** Partially
yes.

1. User opens `http://localhost:8000/cinema` → `panel-preview.js`
   initializes.
2. User clicks `LAUNCH ENGINE (B)` → browser opens
   `ws://localhost:8000/api/phase1/parts/{n}/engine`.
3. Server reads `partNN_flow_plan.json`, extracts first clip's `demo`
   field, spawns wolfcam `+demo <demo> +set cg_drawHUD 0`, starts
   `EngineSupervisor` grab loop.
4. Browser starts receiving `{kind:"frame", jpeg_b64}` at ~4 Hz,
   displays as `<img>` src.
5. User can send `{cmd:"seek", t_ms: 343500}` — server writes
   `seekclock 5:43.5\n` to wolfcam stdin. Seek takes effect whenever
   wolfcam processes the console line; no confirmation back.

What we **cannot** do today:
- No scene-graph query at the seek time (no "what was the rocket doing
  at t=343500?"). The only data flowing back is screen-grabbed JPEG.
- No ComfyUI applied to the live frames.
- No agent loop reading the framebuffer and deciding the next render.
- No multi-angle FL pov swap live — would need a new wolfcam spawn.
- Panel 8's scrub UI isn't connected; panel-preview.js renders a plain
  `<img>`, not the Panel 8 canvas shell.

## Gap to TR4SH MVP

Minimum work to hit **Gate T5** (Part 4 clip through TR4SH Quake
alone):

1. **Fork q3mme** into `tr4sh-quake/engine/` (Track A sprint 1, ~3
   days).
2. **Port protocol 73** from `wolfcamql-src/code/client/cl_parse.c` +
   `msg.c` + `bg_demos.c` into the q3mme client (Track A sprint 2-3,
   ~8 days) — see `docs/reference/dm73-format-deep-dive.md` (1,337
   lines, already authoritative).
3. **Scene export module** `cg_scene_export.c` emitting the client
   game state every snapshot as JSON over a named pipe on Windows
   (`\\.\pipe\tr4sh_scene`) — Track A sprint 4, ~4 days.
4. **Embedded FastAPI child** launched from the engine process,
   connecting back to the pipe — Track A sprint 5, ~3 days.
5. **Replace** `EngineSupervisor` wolfcam subprocess with the TR4SH
   binary; replace the JPEG grab loop with a real FFV1/HuffYUV capture
   bus that ffmpeg muxes to mp4 on the fly — Track A sprint 5-6, ~4
   days.
6. **Agent primitives**: re-render Part 4 clip once via `free_cam_at`
   so Gate T5 is objectively met — Track C, ~5 days.

Rough MVP path: ~25 engineering days of C + Python glue, assuming the
q3mme codebase compiles clean on our toolchain and the protocol 73
patches apply without conflict. Everything on the Python side already
works — the queue, SSE, WebSocket frame fan-out, gamestart.cfg writer,
and SQLite versioning are production quality. The bottleneck is the
engine fork, which has not started.

## Files of Note

- `G:/QUAKE_LEGACY/creative_suite/engine/supervisor.py` (on branch
  `creative-suite-v2-step2`)
- `G:/QUAKE_LEGACY/creative_suite/api/phase1.py` (engine_ws, preview,
  rebuild, versions — 350+ LOC)
- `G:/QUAKE_LEGACY/creative_suite/api/_preview_job.py`
- `G:/QUAKE_LEGACY/creative_suite/api/_render_worker.py` (single-worker
  depth=1 JobQueue)
- `G:/QUAKE_LEGACY/creative_suite/api/_rebuild_job.py` (subprocess →
  SSE, git tag, SQLite)
- `G:/QUAKE_LEGACY/creative_suite/api/capture.py` (POST
  /api/capture/gamestart)
- `G:/QUAKE_LEGACY/creative_suite/capture/gamestart.py` (§4.4
  max-quality cvars + PREVIEW_CVARS)
- `G:/QUAKE_LEGACY/creative_suite/tests/test_engine_supervisor.py`
  (stdin seek test, mock_grab)
- `G:/QUAKE_LEGACY/creative_suite/frontend/prototypes/panel8/index.html`
  (24 KB, 100% mock canvas)
- `G:/QUAKE_LEGACY/creative_suite/frontend/panel-preview.js` (the real
  WS binding — wireEngine)
- `G:/QUAKE_LEGACY/creative_suite/comfy/client.py` + `runner.py` (HTTP
  img2img, batch only)
- `G:/QUAKE_LEGACY/docs/superpowers/specs/2026-04-17-tr4sh-quake-manifesto.md`
  (the vision, 243 lines)
- `G:/QUAKE_LEGACY/docs/superpowers/specs/2026-04-19-phase1-cinema-suite-design.md`
  (current Phase 1 console spec)
- `G:/QUAKE_LEGACY/docs/specs/2026-04-18-directing-vocabulary-and-pattern-extraction.md`
  (layer A/B/C directing map)
