# wolfcamql-src — Client/Server Split

wolfcamql is **playback-only**: no dedicated server, no listen server with real players.
But the code keeps both sides for linking reasons (and to enable future live-server
work). This doc explains what's live, what's dead, and what matters for porting.

## What's live

### Client side (fully functional)
- `code/client/` — demo load, parse, render, input
- `code/cgame/` — game-logic VM for playback visualization
- `code/renderer/` — OpenGL renderer, capture, fonts, shaders
- `code/ui/` — menus, demo browser, config
- `code/sdl/` — platform layer (window, audio, input)

### Shared (live, used by both sides at build time)
- `code/qcommon/` — msg, huffman, net_chan, cvar, cmd, fs, parse
- `code/game/bg_*.c` — shared pmove, public constants, weapon defs

## What's dead (but kept)

### Server side (linked but never run)
- `code/server/sv_*.c` — SV_Init, SV_MapStart are stubs or unreachable
- `code/game/g_*.c` (server-side game logic) — compiled but not executed
- `code/botlib/` — bot AI, compiled for link but no bots during playback

### Why keep dead code?
- Symbols referenced in shared headers (g_spawn, sv_init) would break at link
- Future work (live-server mode, replay-with-spectators) could resurrect this
- Deleting it means a deeper fork from ioquake3 — maintenance cost

## Differences from ioquake3 split

In ioquake3, server is fully live: dedicated server, listen server, bot matches,
VM game logic. wolfcam **cut the server loop's top-level drive** but left the
function bodies alone.

Entry points that differ:
- `com_dedicated` cvar is always 0 in wolfcam (force client-only)
- `SV_Frame` is called with `msec = 0` during demo playback (no simulation)
- Botlib is not initialized (`BotLibSetup` never called)

## Porting into q3mme (where this matters)

q3mme is **also** playback-oriented but has different architecture:
- q3mme uses ioquake3's full client/server split intact
- q3mme's demo system (`cgame/cg_demos*.c`) runs alongside the normal cgame loop
- When porting proto-73 INTO q3mme, we DON'T need wolfcam's "kill server" hacks —
  q3mme's server loop is fine. We just need the proto-73 parser delta on the
  client and qcommon sides.

Keep these wolfcam-only hacks OUT of the port:
- `SV_Frame` no-op wrapper
- `com_dedicated = 0` enforcement
- Botlib init skip
- Dedicated server binary elision (wolfcam only ships a client binary)

## Shared files that matter most for dm_73

Even though client is live and server is dead, the **shared** qcommon files are
what carries proto-73 across the split:

- `msg.c` — used by BOTH sides for packet read/write. Even dead server code compiles
  against the wolfcam-patched version.
- `net_chan.c` — ditto for packet framing
- `huffman.c` — shared compression
- `q_shared.h` — constants seen by everything

When porting, these go into q3mme's `qcommon/` verbatim (minus any wolfcam-specific
assertions that assume client-only state).

## VM boundaries

- **cgame VM:** wolfcam replaced ioquake3's cgame near-entirely with `wolfcam_*.c`
  files. If we run native cgame (not .qvm), this is easy — just compile wolfcam's
  cgame as a shared lib. Running as .qvm needs q3asm or rlxe to compile the VM.
- **game VM:** untouched (wolfcam doesn't simulate, so game VM is dead)
- **ui VM:** lightly modified for demo browser — porting optional
