# wolfcamql-src — Extension Points

Points in the codebase where we add functionality without forking the engine core.
Relevant for Phase 2 automation and Tr4sH Quake porting.

## Console commands (add a new command)

**Location:** `code/cgame/wolfcam_consolecmds.c`

Pattern (grep for `trap_AddCommand` in that file):
```c
trap_AddCommand("wolfcam_foo");
// ...in handler switch:
if (!Q_stricmp(cmd, "wolfcam_foo")) { WolfcamFoo(); return qtrue; }
```

**Why this matters:** every automation path (video capture, seeking, frame
dumping) goes through a console command. Full inventory lives here.

## Cvars (tunable state)

**Location:** `code/cgame/cg_main.c::CG_RegisterCvars` + `wolfcam_main.c`

Pattern: `cg_foo = trap_Cvar_Get("cg_foo", "1", CVAR_ARCHIVE);`

**Relevant cvars for capture automation:**
- `cl_avidemo`, `cl_aviMotionJpeg`, `cl_aviFrameRate` (inherited from ioquake3)
- `wolfcam_speed`, `wolfcam_pause`, `wolfcam_timescale` (wolfcam-specific)
- `cg_drawTimer`, `cg_drawSpeed`, `cg_drawFPS` (HUD visibility for clean captures)

## FX scripts (particle / visual effects)

**Location:** `code/cgame/cg_fx_scripts.c`

Scripts live outside the binary in `baseq3/scripts/*.fx` files. Parser reads them at
cgame init. **This is the mechanism to inject custom muzzle flash / rail colors /
rocket trails without recompiling.**

## Trap_* imports (engine → cgame)

**Location:** `code/cgame/cg_syscalls.c` + `code/game/g_syscalls.asm`

The VM → engine bridge. If we're running cgame native (not as .qvm), changes to
`trap_*` require rebuilding the engine AND cgame.

**Notable trap_ additions in wolfcam:**
- `trap_FS_FOpenFileRead` with extended path handling
- `trap_Cmd_ExecuteText` for internal command queuing
- Demo-time trap_ calls (`trap_GetServerTime` returns demo-time, not real-time)

## Configstring handlers (wire-format → game state)

**Location:** `code/cgame/wolfcam_servercmds.c::WolfCG_ServerCommand`

Every server-originated event (frag, capture, chat, scoreboard update) arrives as a
configstring update or `cs` command. The handler dispatches by command name
(`print`, `chat`, `tchat`, `scores`, `pmc`, `cs`, `tinfo`, ...).

**Adding a new event:** add a case in the switch + a corresponding C function. This
is how FT-2 highlight criteria v2 will tag "notable victim" events.

## Renderer hooks (for capture automation)

**Location:** `code/client/cl_avi.c`

- `CL_OpenAVIForWriting` — start an AVI recording
- `CL_TakeVideoFrame` — called per rendered frame from `SCR_UpdateScreen`
- `CL_CloseAVI` — flush and write RIFF header

**Extension path for quake3e-style MP4:** replace `cl_avi.c`'s AVI writer with an
ffmpeg libav pipe (what quake3e does). Drop-in in terms of call sites.

## Adding a new demo event handler (Phase 2)

To emit a structured event (e.g. "T1 frag detected") during demo playback:

1. Hook in `CL_ParseSnapshot` (`code/client/cl_parse.c`) after the snapshot is built
2. Scan `cl.snap.entities` for `ET_EVENTS` with `event == EV_OBITUARY`
3. Write a JSONL line to a capture file (opened via `trap_FS_FOpenFileWrite`)

This is how uberdemotools' `analysis_obituaries.cpp` works in C++; we have the
wolfcam equivalent path if we want in-engine capture during playback.
