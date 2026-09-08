# WolfcamQL 11.3 — Moviemaking Feature Matrix

Source-grounded inventory for the fragmovie master-capture profile.
**Primary authority:** local source tree `engine/engines/_canonical/code/` (the WolfcamQL 11.3
tree — `cgame/wolfcam_*.c`, `renderergl1/`, `renderergl2/`, `renderercommon/tr_mme*.c`) plus
`engine/engines/wolfcam-knowledge/*.md`. All `file:line` references below are relative to
`engine/engines/_canonical/code/` unless prefixed. No web sources used.

Q3MME reference tree: `engine/engines/_forks/q3mme` / `engine/engines/variants/q3mme`
(wolfcam's `cg_q3mme_demos_camera.c` / `cg_q3mme_demos_dof.c` ARE ported q3mme code, so
"Q3MME impl" and "Wolfcam impl" converge for camera/DoF).

---

## Feature Matrix

| FEATURE | Q3MME impl | Wolfcam impl | Best current option | Source location | Recommended value / method |
|---|---|---|---|---|---|
| Motion blur | `mme_blurFrames` accumulation | Same code, ported: `mme_blurFrames`, `mme_blurType`, `mme_blurStrength`, `mme_blurJitter` | Wolfcam (identical) | `renderercommon/tr_mme.c:367-371`; pacing `client/cl_main.c:5646-5650` | `mme_blurFrames 16` for cinematic pass; `0` for master (blur in post instead). Capture-only — inactive in live playback (`renderercommon/inc_tr_init.c:112-124`) |
| Blur accumulation window | `mme_blurOverlap` rolling window | Same: `mme_blurOverlap` (default 0) | Wolfcam | `renderercommon/tr_mme.c:368` | Leave `0` unless deliberate frame-bleed look wanted |
| DoF | `mme_dofFrames` jittered accumulation | Same + q3mme keypoint DoF (`dof` command, XML save/load) | Wolfcam | `renderercommon/tr_mme.c:373-375`; `cgame/cg_q3mme_demos_dof.c:476-657` | `mme_dofFrames 12`, `mme_dofRadius 2`, aim with `mme_dofVisualize 1` (CVAR_TEMP). Needs `r_depthbits 24` |
| Camera splines | Catmull-Rom / Bezier per-keyframe (`camera smoothPos 0-2`) | Ported verbatim: `camera` command family, `q3mmecamera`, save/load XML | Wolfcam (is q3mme code) | `cgame/cg_q3mme_demos_camera.c:888-1260`; cmd table `cgame/cg_consolecmds.c:8590-8598` | `camera add/lock/smoothPos 1` (catmullrom); `smoothAngles 1` (quaternion). Legacy wolfcam path (`addcamerapoint`/`playcamera`) also present — prefer q3mme path |
| FOV interpolation | Camera keyframe `CAM_FOV` channel, spline/interp/fixed | Same: `fovType` = USE_CURRENT / SPLINE / INTERP / FIXED, with fov velocity control | Wolfcam | `cgame/cg_view.c:3935-4045`; `cg_q3mme_demos_camera.c:895-915` | Set fov per camera keypoint; falls back to `cg_fov` (or `cg.demoFov` when `cg_useDemoFov 1` + protocol ≥ 91) |
| Freecam | `mov_` spectator cam | `freecam` cmd + `cg_freecam_*` cvar family; PVS override via `cg_freecam_useServerView 0` | Wolfcam (richer) | `cgame/cg_consolecmds.c:558-740`; `cgame/cg_view.c:4560-4650` | `freecam` / `freecam set x y z pitch yaw roll`; `cg_freecam_useServerView 0` to render entities outside demo-taker PVS |
| Timescale | `demo_setSpeed` (own accumulator) | Engine cvar `timescale` (CVAR_CHEAT, works in demos) — scales everything incl. audio; decoupled from AVI clock | Wolfcam | `qcommon/common.c:3089-3090`; AVI interaction `client/cl_main.c:5650` | `timescale 0.25` = 4x slow-mo at constant output fps; audio auto-corrected by `cl_aviAudioMatchVideoLength 1` |
| Freeze / pause | q3mme pause | `cl_freezeDemo 1` + `cl_freezeDemoPauseVideoRecording` + `cl_freezeDemoPauseMusic`; `pause` cmd | Wolfcam | `client/cl_main.c:82, 5631, 6961-6981` | `cl_freezeDemoPauseVideoRecording 1` so the writer halts during freezes |
| Supersampling / AA | FBO SSAA (fork-dependent) | GL1: `r_ext_multisample` (0/2/4, window MSAA) AND FBO MSAA `r_useFbo 1` + `r_fboAntiAlias N`; GL2: `r_ext_framebuffer_multisample` | Wolfcam GL1 FBO path | `renderergl1/tr_init.c:1974-1975, 240-400`; `renderergl2/tr_init.c:1922-1924` | `r_useFbo 1; r_fboAntiAlias 8` (silently capped at GL_MAX_SAMPLES). True SSAA only via `r_mode -1` + oversized `r_customwidth/height` + downscale in ffmpeg |
| Temporal AA (via blur jitter) | `mme_blurJitter` | Same (default 1) | Wolfcam | `renderercommon/tr_mme.c:370` | Free AA side-effect whenever `mme_blurFrames > 1` |
| Frame accumulation vs decimation | fps controlled internally | `cl_aviFrameRateDivider` = render at fps×divider, WRITE every divider-th frame (decimation, not averaging) | Wolfcam | `client/cl_main.c:5638-5650`; skip logic `renderercommon/inc_tr_init.c:191, 298` | Keep `1` for master. With blur: engine steps `1/(fps·divider·blurFrames)` s per sub-frame |
| HUD suppression (per element) | q3mme hud cvars | ~30 independent `cg_draw*` cvars + time-gated elements (see Answers §1) | Wolfcam | `cgame/cg_main.c` cvar table (lines cited §1) | Two cfg profiles below |
| Weapon model suppression | `cg_drawGun` | `cg_drawGun 0/1/2/3` (0=hidden, LG beam explicitly preserved) | Wolfcam | `cgame/cg_weapons.c:2790-2812, 1671` | `cg_drawGun 0` for clean POV |
| Projectile preservation | n/a (never hidden) | Projectiles/beams are entities — untouched by `cg_drawGun`; LG beam has explicit keep-hack when gun hidden | Wolfcam | `cgame/cg_weapons.c:2802-2811` | Nothing to do; do NOT use `entityfilter` in the master profile |
| Audio capture | wav writer | PCM 16-bit stereo from software mixer into AVI / wav / pipe; OpenAL hard-blocked | Wolfcam | `client/cl_avi.c:857-880`; `client/cl_main.c:6197-6210` | `s_backend` must not be OpenAL; `s_sdlBits 16`, `s_sdlChannels 2` (enforced at `cl_main.c:6198-6208`) |
| Frame pacing | own clock | Fixed-step: msec forced to `1000/(fps·divider)·timescale·(1/blurFrames)` with fractional carry (`Overf`) | Wolfcam | `client/cl_main.c:5631-5665` | Deterministic; wall-clock speed irrelevant to output timing |
| Lossless capture | own AVI writer | `cl_aviCodec` = `uncompressed` / `huffyuv` (embedded encoder) / `mjpeg`; OpenDML >2 GB | Wolfcam | `client/cl_avi.c:577-1000`; `client/cl_huffyuv.c:363-700` | Prefer pipe+FFV1 (below) over huffyuv AVI — smaller and standard |
| FFmpeg pipe | absent in q3mme | `video pipe` → `ffmpeg -f avi -i - <cl_aviPipeCommand> "<out>" 2> "<log>"` via `_popen` | Wolfcam (killer feature) | `client/cl_avi.c:697-766`; `qcommon/files.c:4720-4757`; `sys/sys_win32.c:2059-2070` | See Answers §3 for mezzanine command |
| Depth pass | `mme_saveDepth` | Same: parallel `-depth` AVI; `mme_depthRange`, `mme_depthFocus` | Wolfcam | `renderercommon/tr_mme.c:379-382`; `client/cl_main.c:6212-6223` | `mme_saveDepth 1` for post-DoF; allocates float buffer per frame |
| Demo seek automation | `demo_seek` | `seekclock mm:ss` / `rewind` / `fastforward` / `seekservertime`; `at <clock> <command>` scheduler | Wolfcam | `cgame/cg_consolecmds.c:838-950, 8546-8551`; `client/cl_main.c:6441-6700` | `seekclock 8:52; video pipe name :demoname; at 9:05 stopvideo; at 9:05 quit` |
| Demo re-record | `demo_record` (rewrite demo from new POV) | **Absent** — `record` refuses during playback ("must be in a level") | q3mme only | `client/cl_main.c:754-900, 7153` | Not available; capture video instead |

---

## Answers

### 1. Clean cinematic POV — per-element HUD control

**Weapon model without losing projectiles/beams:** `cg_drawGun 0`
(`cgame/cg_main.c:1372`, default `1`). `CG_AddViewWeapon` returns early when
`!cg_drawGun.integer` but first re-emits the lightning beam
(`cgame/cg_weapons.c:2800-2811` — "special hack for lightning gun"), and rockets /
grenades / plasma / rail trails are world entities rendered by `cg_ents.c` /
`cg_weapons.c` trail code — completely independent of `cg_drawGun`. Values: `1` gun+bob,
`2`/`3` gun without bob (`cg_weapons.c:1671`), `3` additionally ghost-shader
(`cg_weapons.c:2523`). **`0` is the clean-POV setting.**

Master kill switch: `cg_draw2D 0` (`cg_main.c:1418`) removes every 2D pass in one cvar,
but it also removes elements you may want in REFERENCE_POV, so the profiles below toggle
individually. All defaults from the `cg_main.c` cvar table; all `CVAR_ARCHIVE`.

| Element | Cvar (default) | Off | Source (cg_main.c) | Gotcha |
|---|---|---|---|---|
| HUD/status bar (HP/armor/ammo) | `cg_drawStatus` (1) | 0 | :1419 | QL superhud elements also honour it |
| Scorebox / score bar | `cg_drawScores` (1) | 0 | :1869; gate `cg_draw.c:5851` | — |
| Powerup row | `cg_drawPowerups` (1) | 0 | :1871 | — |
| Timer / game clock | `cg_drawTimer` (1) | 0 | :1421 | — |
| Item timers (wolfcam) | `cg_drawClientItemTimer` (1) | 0 | :1422 | — |
| Crosshair | `cg_drawCrosshair` (5) | 0 | :1528 | Separate `cg_freecam_crosshair 0` for freecam (`:728-737` area) |
| Crosshair names | `cg_drawCrosshairNames` (1) | 0 | :1531 | — |
| Frag message ("You fragged …") | `cg_drawFragMessageTime` (3000) | 0 | :2261; gate `cg_draw.c:8358` | No boolean master cvar — the time gate IS the toggle. `clearfragmessage` cmd flushes a pending one (`cg_consolecmds.c:8489`). Style: `cg_fragMessageStyle` (:2250) |
| Killfeed / obituaries | `cg_obituaryTime` (3000) | 0 | :2276; gate `cg_newdraw.c:6004` | Ownerdraw `CG_PLAYER_OBIT` (`cg_newdraw.c:8299`); time gate 0 = never drawn. Tokens: `cg_obituaryTokens` (:2274) |
| Chat lines | `cg_chatTime` (5000), `cg_chatLines` (10) | 0 / 0 | :1977-1978 | Team chat separately: `cg_teamChatTime` (:1681), `cg_teamChatHeight 0` (:1682) |
| Vote UI | `cg_drawVote` (1) | 0 | :2010 | Team vote separately: `cg_drawTeamVote` (:2022) |
| Center-print (help/announce text) | `cg_drawCenterPrint` (1) | 0 | :1993 | Kills "You have taken the lead" etc. |
| Reward medals (excellent/impressive) | `cg_drawRewards` (1) | 0 | :1561 | — |
| Follow/spectator text | `cg_drawFollowing` (1) + `wolfcam_drawFollowing` (2) | 0 / 0 | :1902, :2222 | BOTH needed — wolfcam draws its own "following X" when `wolfcam_following` |
| Spec messages | `cg_drawSpecMessages` (1) | 0 | :2419 | — |
| Console notify lines | `con_notifytime` (3) | 0 | `client/cl_console.c:496`; gate `:850` (`time > con_notifytime*1000`) | Engine cvar, not cgame. 0 = expire instantly |
| Item pickup text/icon | `cg_drawItemPickups` (3) | 0 | :1885 | — |
| Attacker portrait | `cg_drawAttacker` (1) | 0 | :1512 | — |
| Low-ammo warning | `cg_drawAmmoWarning` (1) | 0 | :1479 | — |
| FPS counter | `cg_drawFPS` (**1**!) | 0 | :1448 | Default ON in wolfcam — must be zeroed |
| Lagometer | `cg_lagometer` (1) | 0 | :1605 | — |
| Snapshot counter | `cg_drawSnapshot` (0) | 0 | :1464 | already off |
| 2D/3D pickup icons | `cg_drawIcons` (1), `cg_draw3dIcons` (1) | 0 | :1476-1477 | — |

**MASTER_POV_CLEAN** (paste into cfg):

```
cg_draw2D 0
cg_drawGun 0
cg_drawStatus 0; cg_drawScores 0; cg_drawPowerups 0; cg_drawTimer 0
cg_drawClientItemTimer 0; cg_drawCrosshair 0; cg_drawCrosshairNames 0
cg_drawFragMessageTime 0; cg_obituaryTime 0
cg_chatTime 0; cg_chatLines 0; cg_teamChatTime 0; cg_teamChatHeight 0
cg_drawVote 0; cg_drawTeamVote 0; cg_drawCenterPrint 0; cg_drawRewards 0
cg_drawFollowing 0; wolfcam_drawFollowing 0; cg_drawSpecMessages 0
con_notifytime 0
cg_drawItemPickups 0; cg_drawAttacker 0; cg_drawAmmoWarning 0
cg_drawFPS 0; cg_lagometer 0; cg_drawSnapshot 0
cg_drawIcons 0; cg_draw3dIcons 0
cg_viewsize 100
```

(`cg_draw2D 0` is belt-and-braces on top of the individual zeros; drop it if any
2D element is ever wanted.)

**REFERENCE_POV** (verification info on):

```
cg_draw2D 1
cg_drawGun 1
cg_drawStatus 1; cg_drawScores 1; cg_drawTimer 1; cg_drawCrosshair 5
cg_drawFragMessageTime 3000; cg_obituaryTime 3000
cg_drawFollowing 1; wolfcam_drawFollowing 2; cg_drawSpecMessages 1
con_notifytime 3
cg_drawItemPickups 3; cg_drawFPS 1; cg_lagometer 0
cg_drawVote 0; cg_drawTeamVote 0; cg_chatTime 0
```

### 2. FOV during demo playback

- **`cg_fov`** (default `DEFAULT_FOV`, `cg_main.c:1377`) is ALWAYS the playback FOV by
  default — it overrides whatever fov the recording player used.
- **`cg_useDemoFov`** exists (`cg_main.c:1336, 2607`, default `0`, CVAR_ARCHIVE):
  - `1` = use the fov recorded in the demo's playerstate (`cg.demoFov = ps->fov`,
    `cg_playerstate.c:1335`), applied in `CG_CalcFov` (`cg_view.c:1163-1167`), freecam
    (`cg_view.c:4578`), gun positioning (`cg_weapons.c:2824`), and camera USE_CURRENT
    keyframes (`cg_q3mme_demos_camera.c:895`).
  - `2` = additionally track live fov changes (zoom) of the POV player when not
    wolfcam-following (`cg_playerstate.c:1337-1360`).
  - **HARD GOTCHA: every use is gated `cgs.realProtocol >= 91`.** `ps->fov` only exists
    in QL protocol 90/91 playerstate. Our corpus is `.dm_73` (protocol 73) → `cg_useDemoFov`
    is a NO-OP on our demos; `cg_fov` always wins. There is no recorded fov to recover.
- **Zoom:** `cg_zoomFov` (default 60, `cg_main.c:1373`) + `CG_CalcZoom` applied after fov
  selection (`cg_view.c:1176`). The demo-taker's zoom key presses are not in the demo
  stream for protocol 73, so original zooms do not replay; on 90/91 they surface through
  `ps->fov` with `cg_useDemoFov 1|2`.
- **Followed-player POV (`follow <n>`):** same path — `cg_fov` (or demoFov on ≥ 91). No
  per-player fov is stored for other clients in any protocol.
- **Recommendation:** treat FOV as a production choice: `cg_fov 105` master; interpolate
  via camera keyframes (`CAM_FOV`) for ramps.

### 3. FFmpeg pipe capture (`video pipe`)

Mechanics (`client/cl_avi.c:697-766`):

1. `video pipe [name :demoname]` sets `afd->pipe` (`CL_Video_f`, `cl_main.c:6117-6240`).
   Output path: `<fs_homepath>/<fs_game>/videos/<name>.<cl_aviPipeExtension>`; log:
   `videos/<name>-ffmpeg.log`.
2. Command built at `cl_avi.c:755`:
   `ffmpeg -f avi -i - <cl_aviPipeCommand> "<videoFileName>" 2> "<logFileName>"`
   — the binary name **`ffmpeg` is hardcoded**; there is **no cvar for its location**.
3. Spawn: `FS_PipeOpen` (`qcommon/files.c:4720`) → `Sys_Popen` → Win32 `_popen(cmd, "wb")`
   (`sys/sys_win32.c:2059`). `_popen` runs the string through `cmd.exe /c`, so
   **ffmpeg.exe must be on PATH or in the process working directory** (the dir wolfcamql
   was launched from). Practical method for our pipeline: prepend
   `creative_suite/tools/ffmpeg/` to PATH in the launcher, or copy ffmpeg.exe next to
   wolfcamql.exe.
4. Frames: the same AVI byte stream (header + movi chunks) that would go to disk is
   written to ffmpeg's stdin. The header is intentionally "broken" (sizes unknown while
   streaming) — comment at `cl_avi.c:703-705`: relies on ffmpeg's error correction.
   **Audio is carried inside that AVI stream** as PCM s16 stereo interleaved with video —
   no separate wav; ffmpeg demuxes both from stdin.
5. Debugging: `debug_ffmpeg_pipe 1` prints the full command (`cl_avi.c:757`); write errors
   drop with "error writing to video pipe, see *-ffmpeg.log" (`cl_avi.c:77-81`).

Failure modes:
- ffmpeg not found → `_popen` still succeeds (cmd.exe spawns), first write fails or the
  log shows nothing; check `videos/*-ffmpeg.log`.
- OpenAL sound backend → capture refuses audio (`cl_main.c:6198`); `s_sdlBits != 16` or
  channels != 2 → refused (`cl_main.c:6202-6208`).
- Only ONE pipe at a time (`PipeUsed` global, `cl_avi.c:64`); `mme_saveDepth` +
  pipe would open a second pipe writer — avoid combining.
- `stopvideo` before `quit`, or rely on quit's close path; abrupt kill truncates the
  mkv (usually recoverable since mkv, but don't).

**Mezzanine verdict:** yes —
`cl_aviPipeCommand "-threads 0 -c:v ffv1 -level 3 -c:a pcm_s16le -y"` with
`cl_aviPipeExtension "mkv"` is exactly what the mechanism supports (defaults at
`cl_main.c:6974-6975` are x264/aac/mkv; any ffmpeg args are legal). FFV1 level 3 in
Matroska + pcm_s16le is a proper lossless mezzanine and far smaller than
`cl_aviCodec uncompressed`. Add `-g 1` implicitly satisfied (FFV1 is intra),
`-slices 16 -slicecrc 1` optional for parallel decode + integrity.

### 4. Motion blur / DoF / camera

- **`mme_blurFrames N`** (`renderercommon/tr_mme.c:367`, default 0): renders N sub-frames
  per output frame and accumulates (`gaussian`/`median`… kernel via `mme_blurType`,
  weight via `mme_blurStrength`, sub-pixel AA via `mme_blurJitter`). The client clock
  compensates: per rendered sub-frame the engine advances
  `1000/(cl_aviFrameRate × divider) × timescale × (1/blurFrames)` ms
  (`client/cl_main.c:5646-5650`) — so output duration is unchanged, capture cost ×N.
  Active ONLY while `video` is recording (`inc_tr_init.c:112-124`).
- **`cl_aviFrameRateDivider D`** (`cl_main.c:6969`, default 1) is frame DECIMATION, not
  averaging: engine renders at fps×D and the writer keeps every D-th frame
  (`inc_tr_init.c:191`); with blur active the keep test is
  `((picCount+1)*blurFrames) % D` (`inc_tr_init.c:298`). Using D>1 with blurFrames=N
  gives an N-frame shutter sampled from an fps×D timeline → shutter angle 360°×N/(N·D)
  — i.e. D>1 narrows the effective shutter. For a plain 360° shutter leave D=1 and use
  blurFrames alone.
- **DoF:** `mme_dofFrames` (passes), `mme_dofRadius` (disk), `mme_dofVisualize 1`
  focus-plane overlay (`tr_mme.c:373-375`); focus/radius keyframable via the `dof`
  command (`cg_q3mme_demos_dof.c:476`, usage at :644-656): `dof add|del|clear|lock|
  shift|next|prev|start|end|focus (a)N|radius (a)N|target|list`; persistence
  `saveq3mmedof` / `loadq3mmedof` (`cg_consolecmds.c:8597-8598`). Depth pass:
  `mme_saveDepth 1` (+ `mme_depthRange`, `mme_depthFocus`, `tr_mme.c:379-382`).
- **Camera (q3mme system in this build)** — command table `cg_consolecmds.c:8590-8595`,
  usage `cg_q3mme_demos_camera.c:1241-1259`:
  `camera add|del|clear|lock|shift <t>|next|prev|start|end|pos/angles (a)x (a)y (a)z|
  target|targetNext|targetPrev|smoothPos 0-2 (linear/catmullrom/bezier)|
  smoothAngles 0-1 (linear/quaternion)|toggle <flags>|smooth|move here/x y z|
  rotate pitch yaw roll`; play state via `playq3mmecamera` / `stopq3mmecamera`;
  persistence `saveq3mmecamera` / `loadq3mmecamera` (XML). Per-channel keyframe flags
  CAM_ORIGIN|CAM_ANGLES|CAM_FOV|CAM_TIME. Legacy wolfcam path
  (`addcamerapoint`/`playcamera`/`ecam`, `cg_consolecmds.c:8510-8530`) coexists; the
  q3mme path is the scriptable one for a cinematic profile.
  Scheduler: `at <mm:ss> <command>` / `listat` / `clearat` / `saveat` / `exec_at_time`
  (`cg_consolecmds.c:8546-8551`) — fixed-size ring, over-queueing silently drops
  (wolfcam-knowledge/05 §limits).

### 5. Renderer quality — beyond the usual suspects

Registered defaults from `renderergl1/tr_init.c` (:1803-1892) and `cgame/cg_main.c`:

| Cvar | Default | Note |
|---|---|---|
| `cg_railQL` | 1 (`cg_main.c:1625`) | QL-style rail; `cg_railQLRailRingWhiteValue 0.45` (:1626) |
| `cg_railTrailTime` | 400 (:1624) | Trail persistence ms — raise (800-1000) for cinematic rails |
| `cg_railRings` / `cg_railRadius` / `cg_railRotation` | 0 / 4 / 1 (:1628-1630) | Classic-style ring controls (used when not QL style) |
| `cg_railUseOwnColors` / `cg_railFromMuzzle` | 0 / 1 (:1633-1634) | — |
| `cg_lightningStyle` | 1 (:2306) | LG beam style; `cg_lightningRenderStyle 1` (:2307) |
| `cg_trueLightning` | 1.0 (:1840) | Beam-follows-crosshair fraction |
| `cg_lightningImpact*` | :2300-2305 | Impact sprite size/cap |
| `cg_impactSparks(+Lifetime/Size/Velocity)` | 1/250/8/128 (:1408-1411) | Spark quality |
| `cg_smokeRadius_RL/GL/SG/NG/PL` | 64/32/32/16/32 (:1818-1822) | Smoke trail radii |
| `cg_gibs` | 15 (:1387) | Gib count (wolfcam extends stock 0/1) |
| `cg_shadows` | 1 (:1385) | 2=stencil, 3=projected (r_stencilbits 8 needed) |
| `cg_marks` | 1 (:1600) | Impact marks |
| `cg_brassTime` | 2500 (:1592) | Shell casing lifetime |
| `cg_muzzleFlash` | 1 (:2340) | — |
| `cg_simpleItems` | 0 (:1593) | Keep 0 — 3D items |
| `r_textureMode` | GL_LINEAR_MIPMAP_LINEAR (`tr_init.c:1877`) | Correct already |
| `r_ignorehwgamma` | 0 (`tr_init.c:1820`) | Set 1 for capture — bakes gamma into frames |
| `r_simpleMipMaps` | 1 (`tr_init.c:1827`) | Set 0 — proper mip filter |
| `r_roundImagesDown` | 1 (`tr_init.c:1808`) | Set 0 |
| `r_finish` | 0 (`tr_init.c:1876`) | Set 1 for deterministic capture pacing |
| `r_swapInterval` | 0 | Keep 0 during capture |
| `mme_saveDepth` | 0 (`tr_mme.c:382`) | 1 = parallel `-depth` AVI for post-DoF; 2 = depth-only variant (`inc_tr_init.c:218,864`) |
| `r_greyscale`/`r_mapGreyScale` | 0 (`tr_init.c:1833,1836`) | Stylistic desat available in-engine |

**gl1 vs gl2:** `cl_renderer` (default **`"opengl1"`**, CVAR_ARCHIVE|CVAR_LATCH,
`client/cl_main.c:5951`; loads `renderer_<name>_x86.dll`, falls back to opengl1 on
failure `:5955-5958`). The wolfcam-specific capture features — offscreen FBO
(`r_useFbo`, `r_fboAntiAlias`, `renderergl1/tr_init.c:240-400`), the mme blur/DoF
accumulator backend and depth output — are mature in **gl1**; gl2 is the ioq3
renderergl2 port with its own FBO cvars (`r_ext_framebuffer_object`,
`r_ext_framebuffer_multisample`, `renderergl2/tr_init.c:1922-1924`) plus tonemapping
etc. that alter the QL look. **Use opengl1 + r_useFbo 1 for faithful QL rendering and
proven FBO capture.** (Knowledge doc 04 concurs; also gl2 animmap-limit history in
wolfcam-knowledge/05.)

### 6. Headless / offscreen

- **No true headless mode.** No `r_headless` anywhere in the tree; the shipped binary is
  a client build (dedicated code paths exist but have no renderer/demo playback).
  A GL context + window are required.
- **Offscreen-FBO-in-a-window is the supported option:** `r_useFbo 1` renders the scene
  into an FBO texture (`renderergl1/tr_init.c:251-340`), so captured pixels never depend
  on window visibility/pixel-ownership; `r_fboAntiAlias N` adds multisample resolve
  (`:355-400`). Combine with `r_mode -1; r_customwidth/height` for capture larger than
  the desktop.
- **Minimized:** `com_maxfpsMinimized` and `com_maxfpsUnfocused` (both default `0` =
  no throttle, `qcommon/common.c:3107-3109`; applied `:3521-3528` only when > 0).
  `com_minimized` is a ROM cvar set by SDL events. With defaults, the frame loop keeps
  running full speed while minimized, and during AVI capture the pacing block
  (`cl_main.c:5631`) overrides msec anyway. **Do not set com_maxfpsMinimized/Unfocused
  to nonzero in capture cfgs** — they'd throttle wall-clock progress. Rendering
  correctness while minimized is guaranteed only with `r_useFbo 1`.
- **Do not `vid_restart` or change `r_mode`/`r_fboAntiAlias` mid-capture** — set
  everything pre-launch (wolfcam-knowledge/05:196; latched cvars).
- Windows automation gotcha: client stdin is unusable for IPC (`sys/sys_win32.c:922-928`)
  — drive via command line `+exec` cfgs and the `at` scheduler, as our pipeline already
  does (CS-5 injection guard applies).

---

## Master-capture cfg skeleton (mezzanine)

```
// renderer (set BEFORE launch; latched)
cl_renderer opengl1
r_mode -1; r_customwidth 1920; r_customheight 1080
r_useFbo 1; r_fboAntiAlias 8
r_picmip 0; r_ext_max_anisotropy 16; r_lodbias -2; r_lodCurveError 10000
r_subdivisions 1; r_simpleMipMaps 0; r_roundImagesDown 0
r_ignorehwgamma 1; r_finish 1; r_swapInterval 0
com_maxfpsMinimized 0; com_maxfpsUnfocused 0

// capture
cl_aviFrameRate 60
cl_aviFrameRateDivider 1
cl_aviPipeExtension "mkv"
cl_aviPipeCommand "-threads 0 -c:v ffv1 -level 3 -slices 16 -slicecrc 1 -c:a pcm_s16le -y"
cl_aviNoAudioHWOutput 1
cl_aviAudioWaitForVideoFrame 1
cl_aviAudioMatchVideoLength 1

// POV
cg_fov 105
// + MASTER_POV_CLEAN block from Answers §1

// run:  seekclock 8:52; video pipe name :demoname; at 9:05 stopvideo; at 9:05 quit
```
