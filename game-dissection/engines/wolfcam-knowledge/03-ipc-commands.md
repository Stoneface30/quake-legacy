# 03 — IPC Commands (WolfWhisperer to wolfcamql)

NOTE: WolfWhisperer.exe Ghidra RE is not yet complete. This doc captures the
**command surface wolfcamql exposes**; WolfWhisperer's chosen subset is inferred
from (a) the Python helper scripts shipped alongside it under
`WOLF WHISPERER/WolfcamQL/*.py` and (b) the cfg files under
`WOLF WHISPERER/WolfcamQL/wolfcam-ql/*.cfg`. WolfWhisperer.exe almost certainly
re-implements the same pattern those scripts do (write-cfg + spawn-process).

Bottom line: **wolfcamql has no bespoke IPC surface.** It is driven by exactly
two mechanisms — Q3 engine startup command-line tokens (`+set` / `+exec` /
`+demo` / `+cmd`) and on-disk cfg files that those tokens exec. There is no
named pipe, no socket, no file-watcher, no RCON-over-LAN path that a spawner
can use to inject commands into an already-running client. The running client
will execute cfg files written on disk after it started ONLY IF the cfg
is exec'd by something already inside the game — e.g. a deferred `at 9:05
exec commandsRecord` that was queued at launch, or via one of the event
handlers (`cgamepostinit.cfg`, `gamestart.cfg`, `roundstart.cfg`, etc.).

---

## Mechanism 1: Command-line startup vars (`+set`, `+exec`, `+demo`, `+cmd`)

**How it parses:** the Q3 engine concatenates argv[1..] into a single buffer,
then splits on `+` tokens to build a list of "console lines" before anything
else runs. Two passes happen:

1. `Com_StartupVariable()` — pulls every `+set X Y` token and applies it as a
   cvar BEFORE filesystem / q3config.cfg load. This is why `+set fs_homepath`
   and `+set fs_game` must go on the command line; they are read before the
   config file that could override them.
   - **File:** `code/qcommon/common.c:615-644`, header comment explicit:
     *"cddir and basedir need to be set before the filesystem is started"*
2. `Com_AddStartupCommands()` — everything that is not a `+set` is appended to
   `Cbuf` as a script statement, executed AFTER config load.
   - **File:** `code/qcommon/common.c:649-680`
   - Called from the main loop init at `common.c:3174`.
   - Return value `qtrue` means "late commands were added" which
     **suppresses the demoloop autostart**. Relevant because `+demo foo.dm_73`
     returns qtrue.

**Engine-side command registrations the spawner cares about:**

| Token | Registered at | Handler |
|-------|---------------|---------|
| `+demo <name>` | `client/cl_main.c:7154` | `CL_PlayDemo_f` |
| `+record <name>` | `client/cl_main.c:7153` | `CL_Record_f` |
| `+stoprecord` | `client/cl_main.c:7160` | `CL_StopRecord_f` |
| `+video [name]` | `client/cl_main.c:7174` | `CL_Video_f` — starts AVI capture |
| `+stopvideo` | `client/cl_main.c:7175` | `CL_StopVideo_f` |
| `+rewind <sec>` | `client/cl_main.c:7182` | `CL_Rewind_f` |
| `+fastforward <sec>` | `client/cl_main.c:7183` | `CL_FastForward_f` |
| `+seek <ms>` | `client/cl_main.c:7185` | `CL_Seek_f` |
| `+pause` | `client/cl_main.c:7189` | `CL_Pause_f` |
| `+quit` | `qcommon/common.c:3047` | `Com_Quit_f` |
| `+exec <file.cfg>` | standard Q3 | executes named cfg from search path |
| `+screenshot` / `+screenshotJPEG` | `renderergl{1,2}/tr_init.c` approx 2187 / 1994 | screenshot |

**Practical invocation pattern (observed):**
```
wolfcamql.exe +set fs_homepath <out_dir> \
              +set fs_game wolfcam-ql \
              +set r_customwidth 1920 +set r_customheight 1080 \
              +exec commandsRecord.cfg \
              +demo mydemo.dm_73
```

The `fs_homepath` override is **load-bearing** — it is the only clean way to
make wolfcam write AVIs to an alternate path for batch renders. Documented as
a TODO in the project FIXME list: *"doc fs_homepath"* (under camera section).

---

## Mechanism 2: cfg file commands (the real brains of automation)

A cfg file is just a semicolon/newline-delimited list of console commands
buffered via `Cbuf_Execute`. WolfWhisperer's automation leverages **four**
deferred-execution hooks that wolfcamql auto-executes at known lifecycle
points, plus one power-command (`at`) that defers arbitrary commands to
future demo time.

### 2a. Auto-exec'd lifecycle cfgs

Discovered under `WOLF WHISPERER/WolfcamQL/wolfcam-ql/` and mirrored in
`WOLF WHISPERER/Stuff/Configs/`:

| cfg filename | When wolfcamql auto-execs it | Usage observed in WolfWhisperer |
|--------------|------------------------------|---------------------------------|
| `autoexec.cfg` | Once at engine init, AFTER `q3config.cfg` | `wcstatsresetall` |
| `cgamepostinit.cfg` | When cgame VM finishes init (demo/server load) | `/record aaa; exec commandsRecord` |
| `gamestart.cfg` | At start of a round/game | custom |
| `gameend.cfg` | At end of game | custom |
| `roundstart.cfg` | Round begin (CA etc.) | custom |
| `roundend.cfg` | Round end | custom |
| `firstpersonswitch.cfg` | Player POV change | custom |
| `wolfcamfirstpersonswitch.cfg` | Wolfcam follow target change | custom |
| `follow.cfg` / `spectator.cfg` / `freecam.cfg` / `ingame.cfg` | viewmode changes | custom |
| `fragforwardnext.cfg` / `fragforwarddone.cfg` | fragforward mode steps | custom |
| `shutdown.cfg` | Engine shutdown | custom |
| `initial.cfg` / `defaultwolfwhisperer.cfg` | base overrides, user-exec'd | custom |

The WolfWhisperer install ships pre-populated copies in `Stuff/Configs/` and
sync-drops them to `wolfcam-ql/` at runtime (the `Backup/` directory contains
dated snapshots of user-modified copies — confirms WolfWhisperer writes these
files during a session).

### 2b. cfg commands the pipeline actually writes

Harvested from the Python scripts (these are effectively WolfWhisperer's
"ground truth" since WolfWhisperer predates this Python port and uses the
same primitives):

| Command | Usage | Source / file:line |
|---------|-------|---------------------|
| `seekclock <mm:ss[.ff]>` | Jump to game-clock time; accepts `w12:53` for warmup | `cgame/cg_consolecmds.c:855` usage print; `cg_consolecmds.c:8482` registration |
| `at <time> <command>` | Queue command at future server time or clock time | `cgame/cg_consolecmds.c:6783-6825` (`CG_AddAtCommand_f`), registered `cg_consolecmds.c:8546` |
| `video [name]` / `video name <n>` | Start AVI capture with filename | `client/cl_main.c:7174` |
| `stopvideo` | Stop AVI capture | `client/cl_main.c:7175` |
| `record <name>` | Record a wolfcam demo (NOT AVI — a new `.dm_73`) | `client/cl_main.c:7153` |
| `stoprecord` | Stop demo recording | `client/cl_main.c:7160` |
| `quit` | Exit process (use `at <endTime> quit` for bounded batch) | `qcommon/common.c:3047` |
| `timescale <f>` | Slow-mo / fast-forward during capture | engine cvar command |
| `cl_freezedemo 0\|1` | Freeze/unfreeze demo playback | bound to F7/F8 by default |
| `fastforward <sec>` / `rewind <sec>` | Non-destructive seek | `cl_main.c:7182-7183` |

**The `at` command is the crown jewel.** Full syntax from the usage print:
```
at now <command>              ; run next frame
at 4546629.50 stopvideo       ; at server time (ms)
at 8:52.33 cg_fov 90          ; at clock time
at w2:05 r_gamma 1.4          ; at warmup clock time
```
Gated by cvar `cg_enableAtCommands` (default `1`, see `cg_main.c:2460`).
Execution site: `cg_view.c:5273 CG_CheckAtCommands()` called once per frame
from `cg_view.c:5813`, fires via `trap_SendConsoleCommand()`
(`cg_view.c:5297`). Stored in `cg.atCommands[MAX_AT_COMMANDS]`.

**Canonical WolfWhisperer cfg recipe** (reconstructed from `TRIMMING.py:44-49`
and `recorddemolist.py`, confirmed matches `cgamepostinit.cfg` semantics):
```
seekclock 7:55;
video name demo1 - 0;
at 8:31 quit;
```
Then launch: `wolfcamql.exe +demo demo1.dm_73` with `cgamepostinit.cfg`
containing `exec commandsRecord`. The wolfcamql client:
1. Loads the demo
2. When cgame finishes init, execs `cgamepostinit.cfg` which then execs
   `commandsRecord.cfg`: `seekclock` seeks to 7:55, `video name ...` starts
   capture, `at 8:31 quit` queues quit for 8:31
3. Demo plays; at server time 8:31 the queued command fires → process exits

### 2c. `nextdemo` / `vstr` chain (for play-only batch)

`playdemolist.py:36` uses a cleaner pattern that avoids `at`:
```
wolfcamql.exe +demo foo.dm_73 +set quitdemo quit +set nextdemo "vstr quitdemo"
```
The `nextdemo` cvar is checked at demo end (`cl_main.c:3406-3419`); if set,
its contents are run as a console command. `vstr` expands a cvar and runs it.
Net effect: "when this demo finishes, run `quit`". Good for play-only
automation where you do not need mid-demo commands.

---

## Mechanism 3: stdin

**Not used on Windows client builds.** The client path on win32 explicitly
does NOT read stdin:

```
// Client Sys_Sleep doesn't support waiting on stdin
```
**File:** `code/sys/sys_win32.c:923`.

`#ifdef DEDICATED` stdin IS read via `WaitForSingleObject(GetStdHandle(
STD_INPUT_HANDLE), ...)` at `sys_win32.c:917-921`, but wolfcamql ships as the
non-DEDICATED client. `Sys_ConsoleInput()` is wired (`sys_main.c:141`) but the
win32 client's console is driven from the allocated console window input, not
the piped stdin of the parent process.

The stdin-pipe-creation code at `sys/sys_win32.c:1685-1704` is wolfcamql
*spawning child processes* (e.g. ffmpeg pipe capture via
`cl_aviPipeCommand` — see `cl_avi.c:739-753`). It is **not** a mechanism for a
parent to inject commands into a running wolfcam. Do not mistake this for
bidirectional IPC.

On Linux/Mac the con_tty TTY path (`sys/con_tty.c:305-588`) does read stdin
via non-blocking `FD_SET(STDIN_FILENO, ...)` — if WolfWhisperer ever shipped
a Linux build, stdin piping would be a viable channel there. It is not on
Windows.

---

## Mechanism 4: Filesystem polling

**None found.** No `FindFirstChangeNotification`, no inotify, no cvar-driven
file-watch loop in wolfcamql source. The closest is the `at` command's
per-frame clock check — time-based, not file-based.

The fact that cfg files re-exec'd **during** a session only fire when
something inside the game calls `exec <name>` is the reason the
lifecycle-hook cfgs (`roundstart.cfg` etc.) exist — they are wolfcamql's
built-in "file polling" by proxy. WolfWhisperer's workflow for live editing
is: write to `roundstart.cfg` on disk, then the next round boundary in the
demo auto-execs it.

---

## Mechanism 5: Network / RCON

**Not usable for local IPC.** `rcon` is server-side only and requires a
running dedicated server plus `rconpassword`. wolfcamql-as-demo-player is a
pure client; there is no `rcon` listener. Searched `server/sv_ccmds.c` etc.
— all rcon paths are `sv_*` scoped. Dead end.

---

## Observed pattern (from WOLF WHISPERER/ scripts)

Three scripts all shell out via a blocking process-spawn call to
`wolfcamql.exe` and let the cfg dance do the rest:

**`PLAYDEMO.py`** — simplest case, iterates `wolfcam-ql/playdemos.txt` and
runs `wolfcamql.exe +demo <fname>` per line. No cfg write; interactive
playback.

**`playdemolist.py`** — same loop but adds `+set quitdemo quit +set nextdemo
"vstr quitdemo"` for clean unattended playthrough batches.

**`TRIMMING.py` / `recorddemolist.py`** (the batch AVI renderer):
1. Parses `wolfcam-ql/TRIMMING.txt` (or `recorddemos.txt`) lines:
   `<startTime> <endTime> <demo.dm_73>`.
2. Writes `wolfcam-ql/commandsRecord.cfg`:
   ```
   seekclock <startTime>;
   video name <basename - index>;
   at <endTime> quit;
   ```
3. Blocking call to `wolfcamql.exe +demo <name>` — blocks until
   wolfcamql quits at `endTime`.
4. Removes `commandsRecord.cfg` for the next iteration.

Pre-req: `cgamepostinit.cfg` must contain `exec commandsRecord` (documented
in the script header at `recorddemolist.py:8-10`). WolfWhisperer.exe either
ships this pre-configured OR writes `cgamepostinit.cfg` itself at install —
the `Stuff/Configs/` template directory suggests the latter.

**Source files cited (this section):**
- `WOLF WHISPERER/WolfcamQL/PLAYDEMO.py:1-16`
- `WOLF WHISPERER/WolfcamQL/playdemolist.py:23-39`
- `WOLF WHISPERER/WolfcamQL/TRIMMING.py:1-57`
- `WOLF WHISPERER/WolfcamQL/demtoavidemolist.py:1-57`
- `WOLF WHISPERER/WolfcamQL/wolfcam-ql/cgamepostinit.cfg:1-2`
  (two-liner: `/record aaa\nexec commandsRecord`)
- `WOLF WHISPERER/WolfcamQL/wolfcam-ql/autoexec.cfg:1`
  (one-liner: `wcstatsresetall`)

---

## Open questions for Ghidra RE pass on WolfWhisperer.exe

- [ ] Does WolfWhisperer use named pipes (`\\.\pipe\*`)? — search binary
      strings for `\\\\.\\pipe\\`. If yes, it bypasses this doc entirely and
      talks to something other than wolfcamql. Given the Python scripts
      shipped alongside suggest the cfg-write pattern, this is unlikely.
- [ ] Does WolfWhisperer spawn wolfcamql with `CREATE_NO_WINDOW` (like
      wolfcam's own child-process path at `sys_win32.c:1732`) or with a
      visible console? Billboard screenshots suggest visible window.
- [ ] Does WolfWhisperer read wolfcamql's stdout/stderr? If so it must be
      piping `CreateProcess` handles (observed pattern in cl_avi.c ffmpeg
      path). Search binary for `CreatePipe` calls.
- [ ] How does WolfWhisperer know a batch job finished? Options:
      `WaitForSingleObject` on process handle (most likely, matches the
      Python blocking-spawn behavior), poll for output AVI file existence,
      or parse stdout. Ghidra should disambiguate.
- [ ] WolfWhisperer billboard / HUD override — grep binary for `hud_edited`
      (present in `WolfcamQL/wolfcam-ql/ui/hud_edited.cfg`). Confirms the
      HUD customization path.
- [ ] Does WolfWhisperer rewrite `q3config.cfg` between runs? `Backup/`
      contains dated `q3config.cfg` snapshots — strongly suggests yes.
      Ghidra should surface the write path; impacts any port that wants to
      coexist with WolfWhisperer state.
- [ ] Check if WolfWhisperer calls `StartupWizard.exe` as a separate process
      or links statically. Two binaries shipped in the install dir.
- [ ] `youtube.ini` + `options.ini` + `sizes.ini` format — not wolfcam
      concerns but document in separate RE pass for full tool replacement.

---

## Summary for the Tr4sH Quake port

The mechanism inventory above is the entire IPC surface to replicate.
Replacement engine (q3mme, per Engine Pivot spec) needs **at minimum**:

1. Q3 startup-variable parser preserved (`Com_StartupVariable` equivalent).
   q3mme already has this — no work.
2. All lifecycle-hook cfg auto-execs (`cgamepostinit.cfg`, `gamestart.cfg`,
   etc.). q3mme has its own naming — compat layer needed OR Tr4sH migrates
   cfgs to q3mme's names. Recommend compat layer so WolfWhisperer cfg
   corpus keeps working.
3. `seekclock`, `at`, `video`, `stopvideo`, `quit` commands — all present
   in q3mme under different names. Port to add the
   wolfcam names as aliases for drop-in compatibility.
4. `cg_enableAtCommands` cvar + `atCommands[]` scheduler.
5. AVI pipe to ffmpeg (already exists in both engines).

No named pipes, no RCON, no file-watchers required. The cfg-write plus
child-process-spawn pattern is the IPC, and it is dead simple.
