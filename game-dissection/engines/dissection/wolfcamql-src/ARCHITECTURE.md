# wolfcamql-src — Architecture

**Upstream:** https://github.com/brugal/wolfcamql (shallow clone, 127 MB original)
**Role in our project:** Golden tree for protocol-73 / Quake Live demo support.
**Canonical copy:** `game-dissection/engines/_canonical/` (wolfcamql-src-authoritative files) + `game-dissection/engines/wolfcamql-src/` (near-dup variants).

## What it is

A fork of ioquake3 repurposed as a **demo player** for Quake Live's `.dm_73` format
(network protocol 73). It is the most complete public implementation of proto-73
parsing — more complete than qldemo-python, more readable than uberdemotools' C++.

## High-level module map

```
code/
├── qcommon/     — protocol / message / huffman / cvar / cmd (shared with server)
│   msg.c, msg.h         ← BIG DELTA vs ioquake3: proto-73 fields
│   huffman.c            ← same algorithm, QL may have quirks in tables (verify)
│   net_chan.c           ← connectionless packets; QL has an extra header
│   common.c, q_shared.* ← constants + helpers
├── client/      — demo read loop, renderer front-end, input, cinematics
│   cl_parse.c           ← BIG DELTA: entity/playerstate deserialization for proto-73
│   cl_demo.c            ← demo file read loop (ioquake3 + QL extensions)
│   cl_cgame.c           ← trap_ dispatch into cgame VM
│   cl_main.c            ← state machine (CA_* states, disconnect/connect)
│   cl_avi.c             ← AVI capture (inherited from ioquake3, local wolfcam patches)
├── server/      — stub (wolfcamql doesn't serve, but keeps symbols for link)
├── cgame/       — ENTIRELY rewritten from ioquake3 to understand QL game state
│   wolfcam_main.c       ← demo loading entry + frame tick
│   wolfcam_consolecmds.c← full list of custom console commands (CRITICAL for automation)
│   wolfcam_servercmds.c ← configstring/score event handlers
│   wolfcam_ents.c       ← entity rendering (model overrides, QL powerups)
│   wolfcam_gamestate.c  ← track scores/weapons/powerups across snapshots
│   cg_fx_scripts.c      ← FX scripting (particle effects)
│   cg_draw.c, cg_event.c, cg_weapons.c, cg_players.c — standard Q3 cgame files
├── game/        — not used (playback only)
├── renderer/    — OpenGL renderer, ioquake3-derived, minor wolfcam patches
├── ui/          — menu system (wolfcam added demo-browse menus)
├── botlib/      — unused at runtime but linked
└── sdl/         — SDL platform layer
```

## Entry points

- **Binary entry:** `code/sys/sys_main.c` → `Com_Init` → `CL_Init` → `CL_Main` loop
- **Demo playback:** `cl_main.c::CL_PlayDemo_f` → `cl_demo.c::CL_DemoCompleted/ReadDemoMessage`
- **Per-frame:** `CL_Frame` → `CL_ParseMessage` (cl_parse.c) → `CG_DrawActiveFrame` via cgame VM
- **cgame VM init:** `cl_cgame.c::CL_InitCGame` → cgame's `vmMain(CG_INIT, ...)`

## How proto-73 demos flow

1. `CL_PlayDemo_f` opens `.dm_73`, reads magic + protocol version
2. `CL_ReadDemoMessage` extracts a Huffman-compressed message
3. `MSG_ReadBits` + `MSG_ReadDeltaEntity` / `MSG_ReadDeltaPlayerstate` in `msg.c`
   unpack the delta-encoded snapshot — **this is where proto-73 diverges from proto-68**
4. `CL_ParseSnapshot` reconstructs full entities from delta-base
5. `CL_ParseServerMessage` dispatches ss to cgame (SV_* configstring updates, CS_ events)
6. cgame module's `CG_ProcessSnapshots` consumes the state and draws

## Why this tree is the authority

- Only public tree with byte-correct dm_73 parsing (uberdemotools reimplements in C++,
  qldemo-python is slow + incomplete for edge cases)
- All QL-specific fields (powerups beyond PW_*, weapon slots beyond MAX_WEAPONS,
  team-based scoring extensions) are correctly decoded here
- The `wolfcam_*` cgame files encode hundreds of QL gameplay observations we'd otherwise
  have to reverse-engineer from binaries

## Build system

- Makefile-driven (no CMake). Entry: top-level `Makefile` → `make release`
- Depends on SDL2, libjpeg, libcurl. On Windows: MSYS2 + MinGW-w64
- Output: `build/release-<platform>-<arch>/wolfcamql.<ext>`
