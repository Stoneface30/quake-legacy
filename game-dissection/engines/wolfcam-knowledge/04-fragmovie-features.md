# 04 — Fragmovie Features (wolfcamql)

License: GPL-2.0 (wolfcamql) — feature inventory extracted from source.
Root: `tools/quake-source/wolfcamql-src/code/`
Scope: features needed to replicate wolfcamql's fragmovie capture in q3mme / Tr4sH Quake.

---

## Feature: Freecam (free-floating spectator camera)

**Implementing files:**
- `cgame/wolfcam_main.c:16` — global `qboolean wolfcam_following;`
- `cgame/cg_consolecmds.c:558-740` — `CG_FreeCam_f()` command handler + subcommands
- `cgame/cg_view.c:227-379` — `CG_CheckThirdPersonKeys()`, `CG_CheckChaseKeys()` (key-driven motion while freecam is active — uses `cg_freecam_speed`)
- `cgame/cg_view.c:2700-3100` — freecam pmove integration (`cg.freecamPlayerState.velocity`, `cg.freecamSet`)
- `cgame/cg_view.c:2893-2900` — per-frame: copy `cg.fpos/fang` into `cg.refdef.vieworg/refdefViewAngles`
- `cgame/wolfcam_ents.c:248-253` — `cg_freecam_useServerView` branch controlling entity visibility
- `cgame/cg_main.c:728-737, 1966-1975` — cvar declarations + defaults

**Surface API:**
| Name | Type | Default | Purpose |
|------|------|---------|---------|
| `freecam` | cmd | — | Toggle freecam on/off. Subcommands: `freecam [offset|move|set|last]`. `freecam move f r u pitch yaw roll` relative nudge; `freecam set x y z pitch yaw roll` absolute; `freecam last` restore last position. |
| `cg_freecam_noclip` | cvar | `0` | Allow passing through geometry when `1`. |
| `cg_freecam_sensitivity` | cvar | `0.1` | Mouse sensitivity multiplier in freecam mode. |
| `cg_freecam_yaw` | cvar | `1.0` | Yaw scale. |
| `cg_freecam_pitch` | cvar | `1.0` | Pitch scale. |
| `cg_freecam_speed` | cvar | `400` | Movement speed (units / sec, used as `/1000.0f` tick rate). Also used by chase-offset keys. |
| `cg_freecam_crosshair` | cvar | `1` | Draw crosshair while in freecam. |
| `cg_freecam_useTeamSettings` | cvar | `2` | Apply team-relative weapon colour/skin logic while freecamming. |
| `cg_freecam_rollValue` | cvar | `0.5` | Roll amount when using roll keybinds. |
| `cg_freecam_useServerView` | cvar | `1` | If `1`, use server-side visibility culling; `0` = render all entities regardless of PVS. Critical for fragmovie coverage shots. |
| `cg_freecam_unlockPitch` | cvar | `1` | Allow pitch beyond ±90° (barrel-roll / look-straight-up). |
| `cg_cameraUpdateFreeCam` | cvar | — | Toggle whether spline camera updates `cg.fpos` continuously (see `cg_view.c:2755`). |

**Algorithm:** Toggling `freecam` flips `cg.freecam`; on transition to `qtrue` the code captures the current view origin/angles (from followed player or demo taker, `cg_consolecmds.c:584-594`) into `cg.fpos`/`cg.fang` and drops viewheight (`cg.fpos[2] -= DEFAULT_VIEWHEIGHT`). Each frame `CG_CheckThirdPersonKeys`/`CG_CheckChaseKeys` integrate velocity from WASD-style key flags (`cg.keyf/b/r/l/u/d`) scaled by `cg_freecam_speed / 1000.0f` and a `delta` time, with a halving factor when `cg.keyspeed` (shift) is held. A separate pmove runs with `PM_SPECTATOR` semantics (or noclip if `cg_freecam_noclip`) so collision is real unless disabled. At draw time `cg.fpos` + `DEFAULT_VIEWHEIGHT` is copied into `cg.refdef.vieworg` and `cg.fang` → `cg.refdef.viewaxis` via `AnglesToAxis`. When `cg_freecam_useServerView == 0`, the snapshot-PVS filter is bypassed so the fly-cam sees all entities.

**Notes for re-implementation:** q3mme already has `mov_` spectator cam; mapping is `cg.freecam` ↔ q3mme's `demo.cmd.pos` with the `CAM_ORIGIN|CAM_ANGLES` flags. The "useServerView" cvar is the non-trivial feature to port — wolfcam overrides the ClientThink PVS so it can show enemies through walls from outside the demo-taker's POV (essential for 3rd-person kill shots). The "last" restore state needs one extra slot beyond q3mme's single camera.

---

## Feature: Kill-cam / First-person Follow

**Implementing files:**
- `cgame/wolfcam_consolecmds.c:150-225` — `Wolfcam_Follow_f()` (the `follow` command)
- `cgame/wolfcam_local.h:11-17` — `WOLFCAM_FOLLOW_DEMO_TAKER | WOLFCAM_FOLLOW_SELECTED_PLAYER | WOLFCAM_FOLLOW_KILLER | WOLFCAM_FOLLOW_VICTIM` enum
- `cgame/cg_event.c:104, 138-145` — event-driven follow-killer / follow-victim transitions (on obituary events)
- `cgame/cg_ents.c:2773-2775` — rendering skip for the followed client's own model
- `cgame/wolfcam_main.c:189-280` — per-frame state sync (`wcg.clientNum`, `wcg.selectedClientNum`)
- `cgame/cg_consolecmds.c:8471, 8672` — command registration + `trap_AddCommand("follow")`

**Surface API:**
| Name | Type | Purpose |
|------|------|---------|
| `follow <clientNum>` | cmd | Follow specific client slot (0-63). |
| `follow -1` | cmd | Return to demo-taker POV. |
| `follow killer` | cmd | Auto-switch to whoever just got a kill (via `WOLFCAM_FOLLOW_KILLER` mode). |
| `follow victim` | cmd | Auto-switch to the most recent victim. |
| `wolfcamfirstpersonviewdemotaker.cfg` | exec | Config executed when returning to demo-taker POV. |
| `wolfcamfirstpersonviewother.cfg` | exec | Config executed when following a non-demo-taker. |
| `follow.cfg` / `spectator.cfg` / `ingame.cfg` | exec | Context configs chained on transitions. |

**Algorithm:** `Wolfcam_Follow_f` parses arg1: `-1` resets (`wolfcam_following = qfalse`, `wcg.clientNum = -1`, execs spectator/ingame cfg), `"killer"`/`"victim"` sets the auto-mode, otherwise parses an integer client slot and validates `cgs.clientinfo[n].infoValid`. On success it sets `wcg.selectedClientNum = clientNum`, `wcg.clientNum = clientNum`, `wolfcam_following = qtrue`, `cg.freecam = qfalse`, and chains `exec follow.cfg` plus one of the two view configs based on whether the target equals the demo taker. In auto modes, `cg_event.c:138/142` intercepts `EV_OBITUARY` events and rewrites `wcg.clientNum` to the most recent `attacker` (killer mode) or `target` (victim mode) so the POV "jumps" with every frag. Rendering uses `cg.snap->ps` for the demo taker only when `!wolfcam_following`; otherwise entity state `cg_entities[wcg.clientNum]` drives `cg.refdef.vieworg` via the normal `CG_DrawActiveFrame` path.

**Notes for re-implementation:** The auto-kill/victim follow is wolfcam-exclusive — q3mme requires manual client switching. For Tr4sH Quake, hook `EV_OBITUARY` (see `dm73-format-deep-dive.md` §events) and expose `follow killer|victim` as a first-class fragmovie primitive. The "demo taker" concept only exists because `.dm_73` is a client-side recording with a fixed POV slot; it maps to `cl.snap.ps.clientNum` at the moment of demo start.

---

## Feature: Time-scale (slow-mo / fast-forward)

**Implementing files:**
- `qcommon/common.c:110-111, 3089-3090` — `com_timescale` cvar (`"timescale"`, default `1`, `CVAR_CHEAT | CVAR_SYSTEMINFO`), `com_timescaleSafe` clamp.
- `qcommon/common.c:3381-3430` — msec scaling in main loop (`fmsec = msec * com_timescale->value`).
- `client/cl_main.c:5574, 5650, 5667-5731` — AVI frame pacing factors timescale into `cl_aviFrameRate`: effective frame time = `1000.0 / (cl_aviFrameRate * frameRateDivider) * com_timescale->value * blurFramesFactor`.
- `client/cl_main.c:82, 6961, 6980-6981` — `cl_freezeDemo` / `cl_freezeDemoPauseVideoRecording` / `cl_freezeDemoPauseMusic` pause stack.

**Surface API:**
| Name | Type | Default | Purpose |
|------|------|---------|---------|
| `timescale` | cvar | `1` | Global time-scale multiplier. `0.25` = 4× slow-mo; `4` = 4× fast-forward. `CVAR_CHEAT`, set during demo is allowed. |
| `com_timescaleSafe` | cvar | `1` | Clamp wildly large values to avoid missed server snapshots. |
| `cl_freezeDemo` | cvar | `0` | `1` = pause demo playback (still renders, still accepts input). |
| `cl_freezeDemoPauseVideoRecording` | cvar | `0` | If `1`, AVI writer halts while frozen. |
| `cl_freezeDemoPauseMusic` | cvar | `1` | If `1`, music pauses while frozen. |
| `pause` | cmd | — | Toggles `cl_freezeDemo` (`cl_main.c:6709`). |

**Algorithm:** The main frame loop computes `fmsec = msec * com_timescale->value` before passing to `CL_Frame` (`common.c:3389-3404`); this scales every subsystem (snapshots, physics, sound mixing) uniformly. For AVI capture the frame clock is decoupled: wolfcam counts real demo milliseconds and emits `1 / cl_aviFrameRate` of demo time per written frame, multiplied by `com_timescale` (`cl_main.c:5650`) — so at `timescale 0.25` with `cl_aviFrameRate 60` each captured second of video covers 0.25s of demo time, yielding 4× slow-mo output. `cl_freezeDemo` halts snapshot advance entirely (`cl_main.c:1578, 4308, 5670-5731`); if `cl_freezeDemoPauseVideoRecording == 0`, the AVI keeps writing duplicate frames (useful for ramp-in/ramp-out holds).

**Notes for re-implementation:** q3mme has `demo_setSpeed` and its own time accumulator; wolfcam's advantage is that `timescale` is just the engine cvar and applies everywhere (including sound playback), which is both a feature (slowed-down rail crack) and a footgun (broken audio at timescale < 0.5 without `cl_aviAudioMatchVideoLength`). Port `cl_freezeDemo` semantics explicitly — q3mme's pause and wolfcam's freeze diverge on what happens to the AVI writer.

---

## Feature: AVI / HuffYUV / ffmpeg pipe writer

**Implementing files:**
- `client/cl_avi.c:577-1000` — `CL_OpenAVIForWriting()` (codec selection, OpenDML, ffmpeg-pipe spawn).
- `client/cl_avi.c:1100-1400` — `CL_WriteAVIVideoFrame()` / `CL_WriteAVIAudioFrame()`.
- `client/cl_avi.c:1985-2100` — `CL_CloseAVI()` (finalise OpenDML index).
- `client/cl_huffyuv.c:363-700` — embedded HuffYUV encoder (`huffyuv_encode_init/frame/end`, lifted from libavcodec).
- `client/cl_main.c:6117-6240` — `CL_Video_f` (`video` cmd parser).
- `client/cl_main.c:6247-6290` — `CL_StopVideo_f` (`stopvideo`).
- `client/cl_main.c:6968-6981` — all `cl_avi*` cvars registered.

**Surface API — commands:**
| Name | Args | Purpose |
|------|------|---------|
| `video` | `[avi|avins|wav|tga|jpg|png|split|pipe] [name <file|:demoname>]` | Start capture. `avi` = container, `avins` = avi no-sound, `pipe` = spawn ffmpeg, `tga/jpg/png` = per-frame stills, `split` = stereo split-screen (left+right AVIs), `:demoname` substitutes demo basename. Default if no type specified: `avi`. |
| `stopvideo` | — | Flush & close writer. |

**Surface API — cvars (all `CVAR_ARCHIVE`):**
| Cvar | Default | Purpose |
|------|---------|---------|
| `cl_aviFrameRate` | `50` | Output framerate (Hz). MUST be ≥1. |
| `cl_aviFrameRateDivider` | `1` | Divider for motion-blur accumulation (capture runs at `fps × divider`, averages `divider` frames into one output). |
| `cl_aviCodec` | `"uncompressed"` | Codec: `uncompressed`, `mjpeg`, `huffyuv`. |
| `cl_aviAllowLargeFiles` | `1` | Enable OpenDML (>2 GB single-file AVIs). When `0`, auto-splits into `-0001.avi`, `-0002.avi`, … |
| `cl_aviFetchMode` | `"GL_RGB"` | glReadPixels format (`GL_RGB` or `GL_RGBA`). |
| `cl_aviExtension` | `"avi"` | File extension for AVI output. |
| `cl_aviPipeCommand` | `"-threads 0 -c:a aac -c:v libx264 -preset ultrafast -y -pix_fmt yuv420p -crf 19"` | ffmpeg CLI args when `pipe` mode used. Full cmd becomes `ffmpeg -f avi -i - <this> "<output>"`. |
| `cl_aviPipeExtension` | `"mkv"` | Container extension for pipe output. |
| `cl_aviNoAudioHWOutput` | `1` | Mute system audio while capturing (avoid stutter from HW mixer contention). |
| `cl_aviAudioWaitForVideoFrame` | `1` | Hold audio samples until N video frames are queued (prevents audio-ahead-of-video). |
| `cl_aviAudioMatchVideoLength` | `1` | Pad/trim audio to exact video duration on close. |

**Algorithm:** `CL_Video_f` parses subcommands into booleans and dispatches to `CL_OpenAVIForWriting`, which picks codec (`cl_aviCodec` → `CODEC_MJPEG | CODEC_HUFFYUV | CODEC_UNCOMPRESSED`), allocates RGB and encode buffers sized `w*h*4 + 18 + 16`, and either writes an OpenDML RIFF header directly or spawns ffmpeg via popen (`ffmpeg -f avi -i - <cl_aviPipeCommand> "<out>" 2> "<log>"`) and feeds AVI frames to its stdin. Per-frame: renderer emits a `RE_TakeVideoFrame` which calls `glReadPixels` (format from `cl_aviFetchMode`), optionally averages `cl_aviFrameRateDivider` frames for motion blur, compresses (HuffYUV via `huffyuv_encode_frame`, MJPEG via libjpeg, or raw), and appends to the AVI index. Audio is captured from the software mixer `S_TransferStereo16` path (OpenAL unsupported — see `cl_main.c:6198`), requires 16-bit stereo, and is synchronised via `cl_aviAudioWaitForVideoFrame`. `CL_CloseAVI` writes the final OpenDML superindex and closes the ffmpeg pipe.

**Notes for re-implementation:** q3mme has its own capture pipeline but lacks the ffmpeg-pipe mode — that is wolfcam's killer feature (direct x264/NVENC encode, no intermediate HuffYUV). The pipe command is a shell string, so Tr4sH Quake should keep it configurable. Note OpenAL is hard-blocked for capture — snd_dma is the only working backend. Also note `cl_aviFrameRate` being a divisor of audio sample rate is only warned, not enforced (`cl_avi.c:860`); Tr4sH should auto-suggest 50/100/200 Hz for 44.1 kHz audio.

---

## Feature: MSAA / Supersampling

**Implementing files:**
- `renderergl1/tr_init.c:121, 1816-1817` — `r_ext_multisample` cvar (range 0..4 enforced).
- `sdl/sdl_glimp.c:600` — SDL2 `SDL_GL_MULTISAMPLEBUFFERS` / `SDL_GL_MULTISAMPLESAMPLES` context attribute.

**Surface API:**
| Name | Type | Default | Range | Purpose |
|------|------|---------|-------|---------|
| `r_ext_multisample` | cvar `CVAR_ARCHIVE|CVAR_LATCH` | `0` | 0, 2, 4 | MSAA sample count. 0 disables. LATCH = requires `vid_restart`. |

**Algorithm:** On context creation, `sdl_glimp.c:600` reads `r_ext_multisample->value`, passes it to `SDL_GL_SetAttribute(SDL_GL_MULTISAMPLESAMPLES, samples)` and sets `SDL_GL_MULTISAMPLEBUFFERS=1` if samples > 0. If context creation fails with MSAA, SDL falls back to 0. No supersampling cvar (`r_ext_supersample`) exists in this fork — **not present**. Render-target supersampling could only be achieved via `r_mode -1` + `r_customwidth/height` set higher than the monitor, then captured and downscaled externally.

**Notes for re-implementation:** GL1 renderer is MSAA-only; GL2 renderer (`renderergl2/`) uses its own FBO path and exposes `r_ext_multisample` + internal SSAA via `r_superSampleMultiplier`-style cvars (grep `tr_fbo.c` in q3mme-derived forks). For Tr4sH Quake aim for GL2/Vulkan with proper downsample SSAA — wolfcam's MSAA is a raster-AA hack only and misses sub-pixel shader aliasing.

---

## Feature: Demo navigation (seekclock, rewind, fastforward, seek, pause, step)

**Implementing files:**
- `cgame/cg_consolecmds.c:838-950, 8482` — `CG_SeekClock_f` (`seekclock mm:ss` and `seekclock w<mm:ss>` for warmup).
- `client/cl_main.c:6441-6478` — `CL_Rewind_f`.
- `client/cl_main.c:6481-6550` — `CL_FastForward_f`.
- `client/cl_main.c:6589-6700` — `CL_Seek_f`, `CL_SeekEnd_f`, `CL_SeekNext_f`, `CL_SeekPrev_f`, `CL_SeekServerTime_f`.
- `client/cl_main.c:6709-6720` — `CL_Pause_f` (toggles `cl_freezeDemo`).
- `client/cl_main.c:1578, 1623, 6400-6410` — `demoSeekPoints[MAX_DEMO_FILES]` re-scan table (snapshot byte offsets).
- `cgame/cg_snapshot.c:650` / `cgame/cg_view.c:5734, 5799, 5887, 5964, 6565` — `cg.demoSeeking` flag suppresses effect/sound playback during seek rebuild.

**Surface API:**
| Name | Args | Purpose |
|------|------|---------|
| `seekclock` | `<mm:ss>` or `w<mm:ss>` or `<seconds>` | Seek to absolute in-game clock time (or warmup time with `w` prefix). Computes delta vs current, dispatches `rewind <s>` or `fastforward <s>`. |
| `rewind` | `<seconds>` | Rewind by N real seconds. Accepts either numeric or cvar name. |
| `fastforward` / `ff` | `<seconds>` | Skip forward N real seconds. |
| `seek` | `<seconds>` | Seek absolute server time (seconds from demo start). |
| `seekend` | — | Jump to last snapshot. |
| `seeknext` / `seekprev` | — | Step one snapshot forward/back. |
| `seekservertime` | `<ms>` | Absolute server-time seek (milliseconds). |
| `pause` | — | Toggle `cl_freezeDemo`. |

**Algorithm:** `rewind` is the primitive. During demo open (`cl_main.c:1623`), wolfcam pre-scans the demo and writes byte offsets for each snapshot into `rb->demoSeekPoints[]`. `CL_Rewind_f` computes `wantedTime = cl.serverTime + Overf - t*1000`, clamps to `di.firstServerTime`, calls `CIN_SeekCinematic(-t)` to unwind any playing cinematic, then `rewind_demo(wantedTime)` which `FS_Seek`s the demo file to the nearest prior snapshot offset and replays forward to `wantedTime`. During the replay `cg.demoSeeking = qtrue` so the cgame suppresses particle effects, obituary events, and sounds. `seekclock` translates an in-game clock (respecting timeouts via `CG_AdjustTimeForTimeouts`) into a delta and dispatches `rewind` or `fastforward` with `trap_SendConsoleCommandNow` (immediate, not queued) to avoid frame-ordering bugs. Warmup seeks use `cg.warmupTimeStart` as the zero.

**Notes for re-implementation:** `seekclock` is the crown jewel for fragmovie automation — maps directly to our pipeline's `seekclock 8:52; video avi; at 9:05 quit` pattern. Port this exactly, including the `w` warmup prefix. The `demoSeekPoints` table must be rebuilt (q3mme scans differently); expect that alone to take a day. The `cg.demoSeeking` effect-suppression flag is critical — without it, seeking produces a burst of stale grenade explosions and rail trails.

---

## Feature: Camera paths / cinematic camera (q3mme-derived splines)

**Implementing files:**
- `cgame/cg_camera.c` + `cgame/cg_camera.h` — wolfcam's original camera-point system (`cg.cameraPoints[]`, `cg.numCameraPoints`).
- `cgame/cg_view.c:2755-2834, 2880-3100` — camera playback + freecam hand-off.
- `cgame/cg_q3mme_demos_camera.c:13-400` — q3mme-ported Catmull-Rom spline interpolators: `CG_Q3mmeCameraOriginAt`, `CG_Q3mmeCameraAnglesAt`, `CG_Q3mmeCameraFovAt`.
- `cgame/cg_q3mme_demos_camera.h` — `CAM_ORIGIN | CAM_ANGLES | CAM_FOV | CAM_TIME` flags.
- `cgame/cg_consolecmds.c:2149-2160, 8003-8095, 8512, 8592-8595` — q3mme command handlers.
- `splines/splines.cpp:756` — reference spline math (idSoftware id1 splines library, mostly legacy).

**Surface API:**
| Name | Purpose |
|------|---------|
| `addCameraPoint` / `addq3mmecamerapoint` | Add a camera keypoint at current time with current freecam origin/angles/fov. |
| `playcamera` | Play legacy wolfcam camera path. |
| `playq3mmecamera` | Play q3mme-style Catmull-Rom path (higher quality). |
| `stopq3mmecamera` | Halt q3mme camera playback. |
| `saveq3mmecamera` / `loadq3mmecamera` | Save/load XML camera file. |
| `cg_cameraSmoothFactor` | cvar (default `1.5`) — smoothing tension for legacy path. |
| `cg_cameraQue` | cvar — queue mode for legacy `playcamera`. |
| `cg_cameraDebugPath` | cvar — overlay spline visualisation. |
| `cg_cameraUpdateFreeCam` | cvar — continuously overwrite `cg.fpos` during playback (so stopping mid-path leaves freecam where camera was). |

**Algorithm:** Wolfcam supports two parallel systems. Legacy (`cg_camera.c`) uses linear/Catmull-Rom-lite interpolation over `cg.cameraPoints[]`, each point holding `cgtime`, `origin`, `angles`, `fov`, and an optional `command` string that fires via `trap_SendConsoleCommand` when the point is hit (used for chaining timescale changes, `fov` ramps, etc.). Per-frame `cg_view.c:2887-3100` finds the two bracketing points and interpolates; if `cg.freecam` is active it copies `cg.fpos/fang` into the refdef first so the camera can be "caught" live. The q3mme path (`cg_q3mme_demos_camera.c`) adds proper piecewise Catmull-Rom with separate `CAM_ORIGIN/ANGLES/FOV/TIME` flag masks so keyframes can animate individual channels independently. XML persistence via `BG_XMLParse_t` tables (`cg_consolecmds.c:8092`).

**Notes for re-implementation:** q3mme already *has* this natively — the wolfcam port lives in `cg_q3mme_demos_camera.c` specifically because the author respected q3mme's implementation. For Tr4sH Quake: keep q3mme's code, drop the legacy `cg_camera.c` system, add the `cg_cameraUpdateFreeCam` live-handoff behaviour, and preserve the per-keypoint `command` hook — it is how wolfcamql scripts fov ramps and timescale changes mid-shot.

---

## Feature: Depth-of-field / motion blur

**Implementing files:**
- `renderercommon/tr_mme.c:46-55, 367-395` — all `mme_*` cvars and accumulator setup.
- `renderercommon/tr_mme.c:113-165` — per-frame blur/dof control (`blurCreate`, jitter tables, frame budget calc).
- `renderercommon/tr_mme_common.c:140-160, 463-470` — blur kernel types (`gaussian`, etc.), DoF radius math.
- `renderercommon/inc_tr_init.c:112-180` — capture-time entry `if (useBlur || mme_dofFrames > 0)` triggers multi-pass accumulation.
- `renderergl1/tr_backend.c:1794` / `renderergl2/tr_backend.c:2133, 3345-3652` — GL backend drives the N-pass jitter-render + average.
- `cgame/cg_q3mme_demos_dof.c:323-460` — cgame-side DoF focus/radius control (`CG_Q3mmeDofUpdate`, `CG_Q3mmeDofDraw`, XML parse/save).

**Surface API:**
| Cvar | Default | Purpose |
|------|---------|---------|
| `mme_blurFrames` | `0` | # of accumulated frames per output frame for motion blur. 0 disables. Max `BLURMAX` (hardcoded). |
| `mme_blurType` | — | `gaussian`, `median`, or other kernel (see `tr_mme_common.c:140`). |
| `mme_blurOverlap` | `0` | Extra rolling-window frames (blend across output frames). |
| `mme_blurJitter` | — | Sub-pixel jitter magnitude per accum frame (also provides AA). |
| `mme_blurStrength` | — | Kernel strength multiplier. |
| `mme_dofFrames` | `0` | # of DoF accumulation passes. 0 disables. |
| `mme_dofRadius` | `2` | Defocus disk radius (units). |
| `mme_dofVisualize` | `0` | `CVAR_TEMP` — overlay focus plane for tuning. |
| `mme_saveDepth` | — | Write a parallel depth-buffer AVI (see `cl_main.c:6212`). |

**Algorithm:** Classic temporal-accumulation: for each output frame, render `mme_blurFrames + mme_blurOverlap` sub-frames with (a) sub-frame time offsets (motion blur) and (b) camera-origin jittered by `mme_blurJitter * jitter[i]` on a pre-computed Poisson disk (`tr_mme.c:260-265`), then weight-average in a shader-less CPU accumulate buffer. DoF uses the same accumulator but jitters *camera position* on a disk of radius `mme_dofRadius` around the focus point (radius comes from cvar or per-keypoint override in `cg_q3mme_demos_dof.c`); `mme_dofFrames` controls sample count. Active only when `tr.recordingVideo` is true or `mme_dofVisualize` is set — meaning DoF/blur DO NOT work in live playback, only during `video` capture. The GL2 backend additionally routes through FBOs (`tr_backend.c:3487-3652`) and splits blur between `shotDataLeft`/`shotDataMain` for stereo/anaglyph.

**Notes for re-implementation:** This is accumulation-buffer blur, not velocity-buffer or post-process — quality is excellent but at `mme_blurFrames 16` the capture is 16× slower. For Tr4sH Quake consider keeping the accumulation path as "quality mode" and adding a modern velocity-buffer post path for "preview mode". The `mme_dofVisualize` overlay is the UX key — users cannot aim DoF without it.

---

## Feature: Screenshot capture (TGA / JPEG / PNG)

**Implementing files:**
- `renderergl1/tr_init.c:1187-1526, 1994-1996` — `R_TakeScreenshot(x, y, w, h, name, type)` + cmd registration. Types: `SCREENSHOT_TGA`, `SCREENSHOT_JPEG`, `SCREENSHOT_PNG`.
- `renderergl2/tr_init.c:1269-1601, 2187-2189` — GL2 equivalents.
- `renderergl1/tr_main.c` / `tr_image*.c` — file writers (TGA: raw BGR dump; JPEG: libjpeg-turbo; PNG: stb_image_write).

**Surface API:**
| Name | Args | Purpose |
|------|------|---------|
| `screenshot` | `[filename]` | Write TGA to `screenshots/shot<NNNN>.tga`. |
| `screenshotJPEG` | `[filename]` | JPEG (quality fixed ~90, no public cvar in this fork). |
| `screenshotPNG` | `[filename]` | PNG (lossless). |

**Algorithm:** Each command queues a render command that, at backend flush, calls `R_TakeScreenshot(0, 0, glConfig.vidWidth, glConfig.vidHeight, checkname, type)`. Implementation: `glReadPixels(GL_RGB)` into a CPU buffer, rearrange row order (GL is bottom-up, files are top-down), dispatch to the writer. Filename auto-numbers by scanning `screenshots/` for the next free slot unless a name is given. No `screenshotBMP`, no `cl_aviMotionJpegQuality` cvar present — those are q3mme-specific.

**Notes for re-implementation:** Trivial to port. JPEG quality should become a cvar in Tr4sH Quake (wolfcam hardcodes it). Useful combination: `mme_dofVisualize 1` + `screenshotPNG` for composing focus passes in post.

---

## Feature: Demo recording from demo (re-record)

**Status:** **Not present in this fork.**

`Cmd_AddCommand("record", CL_Record_f)` at `cl_main.c:7153` registers only the standard online-game demo recorder; `CL_Record_f` (`cl_main.c:754-900`) explicitly rejects demo playback with "`you must be in a level to record`" (standard ioq3 behaviour). Wolfcam does **not** have a "re-record current demo from freecam POV" feature comparable to q3mme's `demo_record`. The intended workflow is: capture AVI with `video` from whatever view you want (freecam / follow killer / camera path), not generate a new `.dm_73`.

**Notes for re-implementation:** q3mme has `demo_record` which rewrites the demo from the chosen POV — this is worth porting to Tr4sH Quake *instead of* wolfcam's approach, because it makes clips re-compressible/re-editable without re-running the capture pipeline. This is the single biggest missing feature in wolfcamql for fragmovie work.

---

## Renderer cvars affecting capture quality

| Cvar | Default | Range | Effect | Source |
|------|---------|-------|--------|--------|
| `r_mode` | `11` | -1, 0..N | Video mode preset. `-1` = use `r_customwidth/height`. | `renderergl1/tr_init.c:1821` |
| `r_customwidth` | `1600` | — | Horizontal render resolution when `r_mode -1`. `CVAR_LATCH`. | `tr_init.c:1824` |
| `r_customheight` | `1024` | — | Vertical render resolution when `r_mode -1`. `CVAR_LATCH`. | `tr_init.c:1825` |
| `r_customPixelAspect` | `1` | — | Pixel aspect ratio (for anamorphic). | `tr_init.c:1826` |
| `r_ext_multisample` | `0` | 0,2,4 | MSAA samples. `CVAR_LATCH`. | `tr_init.c:1816` |
| `r_picmip` | `0` | 0..16 | Texture LOD bias (higher = blurrier). Keep `0` for capture. | `tr_init.c:1805` |
| `r_ignoreShaderNoMipMaps` | `0` | 0/1 | Force mipmaps even on shaders that disable them. | `tr_init.c:1806` |
| `r_ignoreShaderNoPicMip` | `0` | 0/1 | Apply picmip even on shaders that disable it. | `tr_init.c:1807` |
| `r_roundImagesDown` | `1` | 0/1 | Round texture sizes down to POT (quality: set `0`). | `tr_init.c:1808` |
| `r_texturebits` | `0` | 0,16,32 | Texture colour depth. `0` = default. | `tr_init.c:1812` |
| `r_colorbits` | `0` | 0,16,32 | Framebuffer colour depth. | `tr_init.c:1813` |
| `r_stencilbits` | `8` | — | Stencil depth. Needed for shadows. | `tr_init.c:1814` |
| `r_depthbits` | `0` | 0,16,24,32 | Depth buffer precision. Set `24` for DoF. | `tr_init.c:1815` |
| `r_overBrightBits` | `1` | 0..2 | Global over-bright bit-shift for lighting. | `tr_init.c:1818` |
| `r_overBrightBitsValue` | `1.0` | — | Multiplier paired with `r_overBrightBits`. | `tr_init.c:1819` |
| `r_mapOverBrightBits` | `2` | — | Static map lighting over-bright. | `tr_init.c:1847` |
| `r_mapOverBrightBitsValue` | `1.0` | — | Multiplier. | `tr_init.c:1848` |
| `r_mapOverBrightBitsCap` | `255` | 0..255 | Clamp after over-bright (prevents blowout). | `tr_init.c:1849` |
| `r_intensity` | `1` | — | Global texture brightness. | `tr_init.c:1852` |
| `r_gamma` | `1` | — | Display gamma (HW when available). | `tr_init.c:1880` |
| `r_ignorehwgamma` | `0` | 0/1 | Force software gamma (better for capture — bakes into frames). | `tr_init.c:1820` |
| `r_lodbias` | `-2` | — | Negative = higher detail LOD (capture should use ≤ -2). | `tr_init.c:1860` |
| `r_lodCurveError` | `250` | — | Curve tessellation threshold. Lower = smoother curves. | `tr_init.c:1859` |
| `r_subdivisions` | `4` | — | Curve subdivision distance. Lower = smoother. `CVAR_LATCH`. | `tr_init.c:1830` |
| `r_simpleMipMaps` | `1` | 0/1 | Set `0` for proper Gaussian mipmap filter (quality). | `tr_init.c:1827` |
| `r_ext_max_anisotropy` | `2` | — | Max AF samples. Raise to 8-16 for capture. | `tr_init.c:1803` |
| `r_detailtextures` | `1` | 0/1 | Enable detail texture stage. | `tr_init.c:1811` |
| `r_vertexLight` | `0` | 0/1 | `1` disables lightmaps (fast, ugly — keep `0` for capture). | `tr_init.c:1828` |
| `r_fullbright` | `0` | 0/1 | Flat-lit debug mode. Keep `0`. | `tr_init.c:1846` |
| `r_znear` | `4` | — | Near clip plane. Lower = less z-fighting at close range. `CVAR_CHEAT`. | `tr_init.c:1862` |
| `r_flares` | `0` | 0/1 | Lens flares on point lights. | `tr_init.c:1861` |
| `r_dynamiclight` | `1` | 0/1 | Dynamic light pass. | `tr_init.c:1874` |
| `r_fastsky` | `0` | 0/1 | Replace skybox with flat colour. Keep `0` for capture. | `tr_init.c:1867` |
| `r_drawSun` | `0` | 0/1 | Sun sprite. | `tr_init.c:1873` |
| `r_swapInterval` | `0` | 0/1 | VSync. Set `0` during capture. | `tr_init.c:1878` |
| `r_finish` | `0` | 0/1 | `glFinish` each frame — set `1` for deterministic capture timing. | `tr_init.c:1876` |
| `r_anaglyphMode` | `0` | 0..19+ | Stereo rendering mode (19 = split depth buffer output — see `cl_main.c:6218`). | `tr_init.c:1892` |
| `r_greyscale` | `0` | 0/1 | Greyscale output. `CVAR_LATCH`. | `tr_init.c:1833` |
| `r_greyscaleValue` | `1.0` | 0..1 | Desaturation amount. | `tr_init.c:1835` |
| `r_mapGreyScale` | `0` | 0/1 | Desaturate world textures only. | `tr_init.c:1836` |
| `r_singleShader` | `0` | 0/1 | Force every surface through one shader (stylistic). | `tr_init.c:1853` |
| `r_singleShaderName` | `""` | — | Name of that shader. | `tr_init.c:1854` |
| `mme_saveDepth` | `0` | 0/1 | Write depth buffer as parallel AVI for post-DoF. | `cl_main.c:6212` |

---

## HUD-off cvars (clean capture)

All are `CVAR_ARCHIVE` unless noted. Default values shown are from `cg_main.c` cvar table — set to `0` for a clean fragmovie frame.

| Cvar | Default | Setting for clean capture | Source |
|------|---------|---------------------------|--------|
| `cg_draw2D` | `1` | `0` (master HUD kill — disables ALL 2D overlay) | `cgame/cg_main.c:340, 1418` |
| `cg_drawStatus` | `1` | `0` (status bar: health/armor/ammo) | `cgame/cg_main.c:341, 1419` |
| `cg_drawTimer` | `1` | `0` (game clock) | `cgame/cg_main.c:184, 1421` |
| `cg_drawFPS` | `1` | `0` | `cgame/cg_main.c:211, 1448` |
| `cg_drawGun` | `1` | `0` or `2` for viewmodel-only (no weapon bob) | `cgame/cg_main.c:361, 1372` |
| `cg_drawCrosshair` | `5` | `0` (crosshair sprite selector; 0 = none) | `cgame/cg_main.c:276, 1528` |
| `cg_drawCrosshairNames` | — | `0` (name of player under crosshair) | `cgame/cg_main.c:278` |
| `cg_drawCrosshairTeammateHealth` | — | `0` | `cgame/cg_main.c:293` |
| `cg_drawAttacker` | `1` | `0` (recent attacker portrait) | `cgame/cg_main.c:1512` |
| `cg_drawAmmoWarning` | `1` | `0` (low-ammo flash) | `cgame/cg_main.c:1479` |
| `cg_draw3dIcons` | `1` | `0` (3D pickup icons on HUD) | `cgame/cg_main.c:1476` |
| `cg_drawIcons` | `1` | `0` (2D pickup icons) | `cgame/cg_main.c:1477` |
| `cg_drawScores` | — | `0` (scoreboard auto-display) | `cgame/cg_main.c:635` |

Additional: `cg_viewsize 100` (full viewport, no black border; `cg_view.c:204-212`), `cg_thirdPerson 0`, `cg_fov` set to desired fragmovie FOV (typically 100-110), `cg_drawSpeedometer 0` (if registered). The single biggest lever is `cg_draw2D 0` — it kills every 2D pass in one shot and is what all the reference fragmovie cfgs use.

---

## Summary table for Tr4sH Quake port priority

| Feature | Port difficulty | q3mme already has it? | Notes |
|---------|-----------------|-----------------------|-------|
| Freecam | Medium | Similar; port `cg_freecam_useServerView` | Wolfcam's through-walls PVS override is unique |
| Follow killer/victim | Low | No | Small cgame hook on `EV_OBITUARY` |
| Timescale | Low | Yes | Keep wolfcam's `cl_freezeDemo*` triad |
| AVI + ffmpeg pipe | Medium | Partially (no pipe) | ffmpeg pipe is the killer feature — port |
| HuffYUV encoder | Low | ? | Consider dropping; let ffmpeg do it |
| MSAA | Trivial | Yes | — |
| Seek / seekclock | High | Partial | `seekclock` + `demoSeeking` suppression is gold |
| Camera paths | Trivial | Yes | Already ported code IS q3mme code |
| DoF / motion blur | Medium | Yes (mme_*) | Same code — keep as-is |
| Screenshots | Trivial | Yes | Add quality cvars |
| Demo re-record | N/A (wolfcam lacks) | Yes | Port q3mme's, not wolfcam's absence |
