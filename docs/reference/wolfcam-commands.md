# WolfcamQL Command & CVAR Reference

Source-verified from `wolfcamql-src/code/client/cl_main.c` and `code/cgame/cg_consolecmds.c`.
Date compiled: 2026-04-16

---

## 1. Video Capture Commands

### `video` — Start video recording
Registered in `cl_main.c` via `Cmd_AddCommand("video", CL_Video_f)`.
Only works during demo playback (`clc.demoplaying` must be true).

```
video [avi|avins|wav|tga|jpg|png|pipe|split] [name <filename|:demoname>]
```

**Format flags (mutually exclusive groups):**

| Flag | Meaning |
|---|---|
| `avi` | AVI with audio (default if no flag given) |
| `avins` | AVI without audio |
| `wav` | Audio-only WAV |
| `tga` | TGA screenshot sequence (no AVI) |
| `jpg` / `jpeg` | JPEG screenshot sequence |
| `png` | PNG screenshot sequence |
| `pipe` | Pipe raw video through ffmpeg (uses `cl_aviPipeCommand`) |
| `split` | Split stereo/anaglyph video into left/right files |

**Name option:**
- `name :demoname` — auto-name output file from the demo filename (strips extension)
- `name myfile` — explicit output filename

**Automation example (gamestart.cfg pattern):**
```
video avi name :demoname
```

**Audio requirements:** OpenAL backend will refuse audio (`s_backend` must NOT be `OpenAL`).
Sound must be 16-bit stereo (`s_sdlBits 16`, `s_sdlChannels 2`).

---

### `stopvideo` — Stop video recording
```
stopvideo
```
Registered in `cl_main.c`. Closes all open AVI/pipe streams. Safe to call even if not recording.

---

### Key Video CVARs

| CVAR | Default | Purpose |
|---|---|---|
| `cl_aviFrameRate` | `50` | Capture frame rate (fps) |
| `cl_aviFrameRateDivider` | `1` | Divide frame rate (for sub-frame blending) |
| `cl_aviPipeCommand` | `-threads 0 -c:a aac -c:v libx264 -preset ultrafast -y -pix_fmt yuv420p -crf 19` | FFmpeg flags appended when using `pipe` mode |
| `cl_aviPipeExtension` | `mkv` | Output container extension for pipe mode |
| `cl_freezeDemo` | `0` | Pause demo (also pauses recording if `cl_freezeDemoPauseVideoRecording` is set) |
| `cl_freezeDemoPauseVideoRecording` | `0` | When 1: pausing demo also pauses video recording |
| `cl_demoFileBaseName` | `""` (ROM) | Auto-set to the base filename of the playing demo. Used by `name :demoname`. |
| `r_usefbo` | — | Framebuffer override: record at different res than window size |
| `mme_saveDepth` | — | Save a depth-buffer mask video alongside main video (for DOF) |

---

## 2. Demo Playback Commands

All seek commands are client-level (registered in `cl_main.c`) unless noted.

### `seekclock` — Seek to game-clock timestamp (cgame-level)
```
seekclock <time>
seekclock w<time>       // warmup time
```
Time formats: `MM:SS`, `MM:SS.mm`, or bare seconds.
Internally resolves to `rewind` or `fastforward`.

**Examples:**
```
seekclock 8:52          // seek to 8:52 game clock
seekclock w2:05         // seek to 2:05 in warmup
seekclock 15            // seek to 15 seconds
```

---

### `fastforward` — Jump forward N seconds
```
fastforward <seconds>
```
Can accept a cvar name instead of a literal number.

---

### `rewind` — Jump backward N seconds
```
rewind <seconds>
```

---

### `seek` — Seek to N seconds from demo start (absolute)
```
seek <seconds>
```
Seeks to `firstServerTime + N*1000` ms.

---

### `seekend` — Seek to N seconds before demo end
```
seekend <seconds>
```

---

### `seekservertime` — Seek to exact server time in milliseconds
```
seekservertime <milliseconds>
```
Useful when you know the exact server timestamp from frag detection.

---

### `seeknext` / `seekprev` — Step one snapshot forward/backward
```
seeknext
seekprev
```

---

### `seeknextround` / `seekprevround` — Jump between rounds (cgame-level)
```
seeknextround
seekprevround
```

---

### `pause` — Toggle demo pause
```
pause
```
Toggles `cl_freezeDemo` between 0 and 1.

---

### `demo` — Load and play a demo
```
demo <filename>
```
Filename relative to `baseq3/demos/`. Extension `.dm_73` is implied.

---

### `timescale` — Playback speed multiplier
Not a command but a CVAR (`com_timescale`). Set via:
```
timescale 0.5          // half speed (slow-mo)
timescale 1            // real-time
timescale 0.01         // extreme slow-mo
```
The video capture system accounts for timescale when computing frame timing:
`frameTime = (1000 / (cl_aviFrameRate * divider)) * timescale`.

---

## 3. Camera Commands

All camera commands are cgame-level (registered in `cg_consolecmds.c`).

### `follow` — Switch POV to another player
```
follow <clientNum>      // follow client slot 0-63
follow -1               // return to demo taker's POV
follow killer           // auto-follow whoever kills next
follow victim           // auto-follow whoever dies next
follow                  // print current follow state
```
Executes `follow.cfg`, `spectator.cfg`, or `ingame.cfg` as appropriate.

---

### `freecam` — Toggle free camera mode
```
freecam                              // toggle
freecam offset [x] [y] [z] [pitch] [yaw] [roll]
freecam move [f] [r] [u] [pitch] [yaw] [roll]
freecam set [x] [y] [z] [pitch] [yaw] [roll]
freecam last                         // restore last freecam position
```
Executes `freecam.cfg` on activation, `follow.cfg` or `spectator.cfg` on deactivation.
Freecam keys: `WASD` to move, `Space` up, `Shift` down.

---

### `setviewpos` — Set freecam position directly
```
setviewpos <x> <y> <z>
setviewpos <x> <y> <z> <pitch> <yaw> <roll>
```
Alias `freecamsetpos` is also registered.

---

### `setviewangles` — Set freecam angles directly
```
setviewangles <pitch> <yaw> <roll>
```

---

### `chase` — Lock camera behind an entity with offset
```
chase <entityNum> [xOffset] [yOffset] [zOffset] [range] [angle]
chase -1                // disable chase
```
Range can be a number, `here` (compute from current view position), or `herez`.

---

### `view` — Lock camera onto an entity (look-at, not chase)
```
view <entityNum> [xOffset] [yOffset] [zOffset]
view -1                 // disable
view here               // use current freecam position as view mark
```

---

### `addcamerapoint` — Add a spline camera keyframe
```
addcamerapoint
```
Records current freecam position+angles+time as a keyframe. Press `V` in freecam mode.

---

### `clearcamerapoints` — Delete all camera keyframes
```
clearcamerapoints
```
Press `R` in freecam mode.

---

### `playcamera` — Play the recorded camera path
```
playcamera
```
Plays the spline camera from its first keyframe.

---

### `stopcamera` — Stop camera path playback
```
stopcamera
```

---

### `savecamera` — Save camera path to file
```
savecamera [filename]
```
Default saves to `cameras/wolfcam-autosave.cam8`.

---

### `loadcamera` — Load a saved camera path
```
loadcamera <filename>
```

---

### `recordpath` — Record freecam movement as a path
```
recordpath [filename]   // start recording; call again to stop
```
Records position+angles in realtime. Different from `addcamerapoint` (which is keyframe-based).

---

### `playpath` — Play a recorded freecam path
```
playpath [filename]
```

---

### `stopplaypath` — Stop path playback
```
stopplaypath
```

---

### `selectcamerapoint` — Select a specific keyframe for editing
```
selectcamerapoint <num>
selectcamerapoint all | first | last | inner
```

---

### `editcamerapoint` — Move to a camera point in space/time
```
editcamerapoint         // edit currently selected point
editcamerapoint next | previous
```

---

### `deletecamerapoint` — Remove a specific keyframe
```
deletecamerapoint
```

---

### `q3mmecamera` — q3mme-style camera system commands
```
q3mmecamera [subcommand]
```
Advanced spline camera imported from q3mme. See `cg_q3mme_demos_camera.c`.

---

### `playq3mmecamera` / `stopq3mmecamera` — Play/stop q3mme camera
```
playq3mmecamera
stopq3mmecamera
```

---

### `saveq3mmecamera` / `loadq3mmecamera` — Persist q3mme camera data
```
saveq3mmecamera [filename]
loadq3mmecamera [filename]
```

---

### Key Camera CVARs

| CVAR | Default | Purpose |
|---|---|---|
| `cg_cameraDefaultOriginType` | — | Interpolation type: 1=Curve, 2=Spline, 3=Jump, 4=Interp |
| `cg_cameraRewindTime` | — | Seek N seconds back when playing camera (for animation sync) |
| `cg_cameraUpdateFreeCam` | — | Transfer camera state to freecam on play |
| `cg_cameraQue` | — | 1=play without /playcamera; 2=also exec camera point commands |
| `cg_drawCameraPath` | — | Draw the spline path and keyframes in-game |
| `cg_drawCameraPointInfo` | — | Show keyframe info on HUD |
| `cg_q3mmeCameraSmoothPos` | `0` | q3mme smoothing factor for position spline |
| `wolfcam_fixedViewAngles` | `0` | Only update follow-POV angles every N ms |
| `cg_thirdPerson` | `0` | Enable 3rd-person camera |
| `cg_thirdPersonAngle` | — | Angle offset for 3rd-person |
| `cg_thirdPersonRange` | — | Distance for 3rd-person |

---

## 4. WolfcamQL-specific CVARs (`wolfcam_*`)

| CVAR | Default | Purpose |
|---|---|---|
| `wolfcam_switchMode` | — | Follow-switching behavior: 0=try selected/closest/demo, 1=fallback to demo taker, 2=try selected/killer/victim/demo |
| `wolfcam_hovertimer` | — | ms to wait before auto-switching POV after death |
| `wolfcam_firstPersonSwitchSoundStyle` | — | When to play switch sound: 0=never, 1=on explicit follow change, 2=always |
| `wolfcam_fixedViewAngles` | `0` | Update follow-POV angles only every N ms (smooth camera) |
| `wolfcam_drawFollowing` | — | Show name of player being followed |
| `wolfcam_drawFollowingOnlyName` | — | Strip "Following" prefix, show only name |
| `wolfcam_painHealth` | `1` | Use pain events to infer enemy health when not available |
| `wolfcam_painHealthColor` | `0xff00ff` | Color of pain-health display |
| `wolfcam_painHealthAlpha` | `255` | Alpha of pain-health display |
| `wolfcam_painHealthFade` | `1` | Fade pain-health display |
| `wolfcam_painHealthFadeTime` | `4000` | Fade duration in ms |
| `wolfcam_painHealthValidTime` | `5000` | ms after pain event that value stays valid |
| `wolfcam_painHealthStyle` | `1` | Style of pain-health indicator |

---

## 5. Automation-critical Commands

### `at` — Schedule a command to execute at a specific time
The primary automation primitive in WolfcamQL.

```
at <time> <command>
```

Time formats:
- `now` — execute immediately at current demo time
- `8:52.33` — clock time MM:SS.mm
- `w2:05` — warmup clock time
- `4546629.50` — raw server time (float, milliseconds)

**Examples:**
```
at 8:52 video avi name :demoname    // start recording at clock 8:52
at 9:05 quit                         // quit at 9:05
at 9:05 stopvideo                    // stop recording at 9:05
at now timescale 0.5                // slow-mo from current time
at 4:30 follow 3                    // switch POV at 4:30
```

**gamestart.cfg pattern (the canonical automation approach):**
```
seekclock 8:52; video avi name :demoname; at 9:05 quit
```
This is the core automation loop used in Phase 1/Phase 2.

---

### `listat` — List all pending at-commands
```
listat
```

---

### `clearat` — Clear all pending at-commands
```
clearat
```

---

### `removeat` — Remove a specific at-command by number
```
removeat <num>
```

---

### `saveat` — Save at-commands to a cfg file
```
saveat [filename]       // default: atcommands.cfg
```

---

### `exec_at_time` — Exec a cfg at a specific server time
```
exec_at_time <servertime_ms> <cfgfile>
```
Convenience wrapper that creates an `at` command internally.

---

### `fragforward` — Auto-advance to next frag
```
fragforward [preKillSeconds] [deathHoverSeconds]
fragforward stop
```
Defaults: 5 seconds before kill, 3 seconds hover after death.
Toggles `cg.fragForwarding`. Used by Wolf Whisperer's "Scan Frags" button.

When fragforward is active, the demo fast-forwards to each frag minus `preKillSeconds`,
plays through death, hovers for `deathHoverSeconds`, then jumps to the next frag.
When no more frags exist, a message is displayed on-screen.

**Automation use:** Run `fragforward` to find a frag's approximate timestamp, then seek
back to it for precise recording.

---

### `quit` — Exit WolfcamQL
```
quit
```
Standard q3 quit. Used in `at 9:05 quit` to auto-terminate after recording.

---

### `exec` — Execute a config file
```
exec <cfgfile>
```
Standard q3 exec. Used to chain config scripts.
WolfcamQL auto-executes these based on state transitions:
- `gamestart.cfg` — executed at game start (the capture automation hook)
- `follow.cfg` — executed when entering follow mode
- `freecam.cfg` — executed when entering freecam mode
- `spectator.cfg` — executed when spectator state detected
- `ingame.cfg` — executed when in-game state detected
- `wolfcamfirstpersonviewdemotaker.cfg` — demo-taker first-person view
- `wolfcamfirstpersonviewother.cfg` — following another player first-person

---

### `servertime` — Print current server time to console
```
servertime
```
Useful for finding exact timestamps for `at` commands.

---

### `viewpos` — Print current camera position and angles
```
viewpos
```
Outputs: `(x y z) pitch yaw roll serverTime`

---

### `players` / `playersw` — List players with client slots
```
players        // with color codes
playersw       // stripped of color codes (width-safe)
```
Gives you the client slot numbers needed for `follow <N>`.

---

### `wcstats` — Print weapon stats for a player
```
wcstats [clientNum]     // default: current follow target
```

---

### `wcstatsall` — Print weapon stats for all players
```
wcstatsall
```

---

### `loop` / `setloopstart` / `setloopend` — Demo loop section
```
setloopstart
setloopend
loop
```
Mark a section of the demo to loop continuously.

---

### `cvarinterp` — Interpolate a CVAR between two values over time
```
cvarinterp <cvar> <startValue> <endValue> <durationMs>
clearcvarinterp
```
Useful for smooth timescale transitions or fade effects.

---

### `dof` — Depth of Field control (q3mme-style)
```
dof [subcommand]
saveq3mmedof [filename]
loadq3mmedof [filename]
```

---

## 6. Quick Reference Table

| Command | Type | Description | Automation Example |
|---|---|---|---|
| `video avi name :demoname` | Client | Start AVI recording, name from demo | `video avi name :demoname` |
| `stopvideo` | Client | Stop recording | `at 9:05 stopvideo` |
| `seekclock <MM:SS>` | CGgame | Seek to game-clock time | `seekclock 8:52` |
| `fastforward <sec>` | Client | Jump forward N seconds | `fastforward 10` |
| `rewind <sec>` | Client | Jump backward N seconds | `rewind 5` |
| `seek <sec>` | Client | Absolute seek from demo start | `seek 120` |
| `seekend <sec>` | Client | Seek N sec from demo end | `seekend 0` |
| `seekservertime <ms>` | Client | Seek to exact server timestamp (ms) | `seekservertime 4546630` |
| `seeknext` / `seekprev` | Client | Step one snapshot | `seeknext` |
| `pause` | Client | Toggle demo freeze | `pause` |
| `timescale` | CVAR | Demo/capture speed multiplier | `timescale 0.5` |
| `at <time> <cmd>` | CGgame | Schedule command at game time | `at 9:05 quit` |
| `listat` | CGgame | List pending at-commands | `listat` |
| `clearat` | CGgame | Remove all at-commands | `clearat` |
| `follow <N>` | CGgame | Switch to client slot N POV | `follow 3` |
| `follow -1` | CGgame | Return to demo-taker POV | `follow -1` |
| `follow killer` | CGgame | Auto-follow killer | `follow killer` |
| `follow victim` | CGgame | Auto-follow victim | `follow victim` |
| `freecam` | CGgame | Toggle free camera | `freecam` |
| `setviewpos x y z` | CGgame | Set freecam position | `setviewpos 0 0 64` |
| `chase <ent>` | CGgame | Chase entity with offset | `chase 3 0 0 40` |
| `view <ent>` | CGgame | Look-at camera on entity | `view 3` |
| `addcamerapoint` | CGgame | Add spline keyframe at current pos | `addcamerapoint` |
| `clearcamerapoints` | CGgame | Reset camera spline | `clearcamerapoints` |
| `playcamera` | CGgame | Play camera spline path | `playcamera` |
| `stopcamera` | CGgame | Stop camera spline | `stopcamera` |
| `savecamera [file]` | CGgame | Save camera to file | `savecamera myfrag` |
| `loadcamera <file>` | CGgame | Load camera from file | `loadcamera myfrag` |
| `recordpath` | CGgame | Record freecam movement path | `recordpath myfrag` |
| `playpath [file]` | CGgame | Play a recorded path | `playpath myfrag` |
| `fragforward [preSec] [hoverSec]` | CGgame | Auto-advance through frags | `fragforward 5 3` |
| `fragforward stop` | CGgame | Stop frag scan | `fragforward stop` |
| `players` | CGgame | List players + slot numbers | `players` |
| `viewpos` | CGgame | Print current camera pos | `viewpos` |
| `servertime` | CGgame | Print current server time | `servertime` |
| `quit` | Client | Exit WolfcamQL | `at 9:05 quit` |
| `exec <cfg>` | Client | Execute a config file | `exec gamestart.cfg` |
| `cvarinterp <cvar> <s> <e> <ms>` | CGgame | Tween a CVAR over time | `cvarinterp timescale 1 0.1 2000` |
| `cl_aviFrameRate` | CVAR | Capture fps | `cl_aviFrameRate 60` |
| `cl_aviPipeCommand` | CVAR | FFmpeg encode flags | see default above |
| `cl_aviPipeExtension` | CVAR | Pipe output container | `cl_aviPipeExtension mp4` |
| `cl_freezeDemo` | CVAR | 1=pause demo | `cl_freezeDemo 1` |
| `r_usefbo` | CVAR | Framebuffer override (independent res) | `r_usefbo 1` |

---

## 7. gamestart.cfg Automation Pattern

WolfcamQL executes `gamestart.cfg` at match start. This is the hook for Phase 1/2 automation.

**Basic capture pattern:**
```cfg
// gamestart.cfg
seekclock 8:52
video avi name :demoname
at 9:05 quit
```

**With slow-motion capture:**
```cfg
seekclock 8:52
timescale 0.5
video avi name :demoname
at 9:05 stopvideo
at 9:05 quit
```

**With POV control:**
```cfg
seekclock 8:45
follow 3
seekclock 8:52
video avi name :demoname
at 9:05 quit
```

**With pipe mode (direct to mp4):**
```cfg
// requires cl_aviPipeCommand and cl_aviPipeExtension set first
seekclock 8:52
video pipe name :demoname
at 9:05 stopvideo
at 9:05 quit
```

**WolfcamQL launch command (from Python automation):**
```
wolfcamql.exe +set fs_homepath <outdir> +exec cap.cfg +demo demo.dm_73
```
Where `cap.cfg` contains the seekclock/video/at sequence.

---

## 8. Key State-Transition Config Files

WolfcamQL auto-executes these on state changes. Place them in `baseq3/` or `wolfcam-ql/`:

| File | When executed |
|---|---|
| `gamestart.cfg` | Match start (primary automation hook) |
| `follow.cfg` | Entering follow-player mode |
| `freecam.cfg` | Entering freecam mode |
| `spectator.cfg` | Detected spectator state |
| `ingame.cfg` | Detected in-game state |
| `wolfcamfirstpersonviewdemotaker.cfg` | Demo taker 1st-person view |
| `wolfcamfirstpersonviewother.cfg` | Following another player 1st-person |

---

## 9. Source File Locations

| File | Location |
|---|---|
| Video commands (`video`, `stopvideo`, seek) | `code/client/cl_main.c` (lines 6123–6715) |
| `at`, `seekclock`, `fragforward`, camera | `code/cgame/cg_consolecmds.c` |
| Command registration table | `code/cgame/cg_consolecmds.c` lines 8413–8606 |
| wolfcam-specific commands (`follow`, `wcstats`) | `code/cgame/wolfcam_consolecmds.c` |
| q3mme spline camera math | `code/cgame/cg_q3mme_demos_camera.c` |
| AVI/pipe write internals | `code/client/cl_avi.c` |
| wolfcam_* CVAR registrations | `code/cgame/cg_main.c` lines 2064–2084 |

---

## 10. Kill-Query API (Phase 2 Core)

WolfcamQL maintains a built-in frag database populated during demo parsing. No .dm_73
binary parsing needed — query kills directly via syscalls.

**Full reference:** `docs/reference/wolfcam-kill-query-api.md`

### Key syscalls (signatures from `cg_syscalls.h`):

```c
// Find next kill of 'slot' (as victim) after serverTime
qboolean trap_GetNextKiller(int slot, int serverTime, int *killer, int *foundTime, qboolean onlyOther);

// Find next kill by 'slot' (as killer) after serverTime
qboolean trap_GetNextVictim(int slot, int serverTime, int *victim, int *foundTime, qboolean onlyOther);

// Get all CA round start times (call once on demo load)
void trap_GetRoundStartTimes(int *numRoundStarts, int *roundStarts);

// Demo temporal boundaries
int trap_GetFirstServerTime(void);
int trap_GetLastServerTime(void);
int trap_GetGameStartTime(void);    // returns -1 if no game in demo
int trap_GetGameEndTime(void);

// Timeout windows (dead time to skip)
void trap_Get_Demo_Timeouts(int *numTimeouts, timeOut_t *timeOuts);

// Item pickups
int trap_GetItemPickupNumber(int pickupTime);
int trap_GetItemPickup(int pickupNumber, itemPickup_t *ip);

// Team switches (for CA alive-status)
qboolean trap_GetTeamSwitchTime(int clientNum, int startTime, int *teamSwitchTime);
```

### Kill enumeration loop pattern:

```c
// Enumerate all kills by subject player across the full demo
int serverTime = trap_GetGameStartTime();
if (serverTime < 0) serverTime = trap_GetFirstServerTime();

int victim, foundTime;
while (trap_GetNextVictim(subjectSlot, serverTime, &victim, &foundTime, qtrue)) {
    // record: kill at foundTime, victim=victim
    serverTime = foundTime + 1;  // advance past this kill
}
```

### CRITICAL: trap_AddAt is DISABLED

`trap_AddAt` is wrapped in `#if 0` in `cg_syscalls.c`. Do not use it.
Use the `at` console command instead (or `trap_SendConsoleCommand("at ...")`).

### Scheduling clips via `at` commands:

```
# In a generated cap.cfg — use raw server time (float), never clock time
at 152340.0 video avi name frag_001
at 156500.0 stopvideo
at 156500.0 seekservertime 248900
at 248900.0 video avi name frag_002
at 253100.0 stopvideo
at 253100.0 quit
```

### Struct definitions (from `cg_public.h`):

```c
typedef struct {
    int startTime;     // timeout start (clock paused)
    int endTime;       // timeout end (clock resumed)
    int serverTime;    // when the command was issued
} timeOut_t;           // MAX_TIMEOUTS = 256

typedef struct {
    int clientNum;     // who picked up
    int index;         // item type (bg_itemlist[] index)
    vec3_t origin;     // world position
    int pickupTime;    // server time of pickup
    int specPickupTime;
    int number;        // entity number
    qboolean spec;     // recorded from spec POV?
} itemPickup_t;        // MAX_ITEM_PICKUPS = 4096

typedef struct {
    int firstServerTime;
    int firstMessageNum;
    int lastServerTime;
    int lastMessageNum;
    int number;        // sequential obit index
    int killer;        // client slot
    int victim;        // client slot
    int mod;           // MOD_* means of death constant
} demoObit_t;          // MAX_DEMO_OBITS = 2048
                       // NOTE: mod (weapon) is NOT exposed by kill-query syscalls
                       // Must parse from snapshot entity events to get weapon type
```
