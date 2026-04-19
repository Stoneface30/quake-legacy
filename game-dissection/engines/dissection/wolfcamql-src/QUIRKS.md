# wolfcamql-src — Quirks and Gotchas

Things that cost real debugging time. Future-you will thank you for this.

## Protocol quirks

- **Demo magic is -1, not a string.** First 4 bytes of `.dm_73` = `0xFFFFFFFF` little-endian.
  Not a printable magic string. Naive hexdump-based detection fails.
- **Huffman table is fixed.** No per-demo table. Same for proto-68 and proto-73.
  Don't try to parse a table out of the file.
- **Delta base wraps.** `deltaNum` in a snapshot refers to `serverTime` modulo
  `PACKET_BACKUP`. An out-of-window delta is treated as "from scratch" silently.
- **Event toggle bits.** `entity->event & ~0x300` masks the toggle bits the server
  uses to distinguish repeated events. `& 0xFF` is wrong.
- **otherEntityNum2 is the killer, otherEntityNum is the victim.** This is flipped
  from intuition. Double-check every frag extractor.

## Build quirks

- Makefile assumes `gcc` at exact path — MinGW builds need `CC=x86_64-w64-mingw32-gcc`
- SDL2 headers must be in the include path BEFORE libjpeg (order-dependent on Windows)
- `build/release-mingw64-x86_64/` is the canonical Windows output dir, not `bin/`
- `make release debug` in one invocation breaks object-dir sharing — run separately
- `USE_VULKAN` flag exists in the Makefile but does nothing (wolfcam is GL-only)

## Runtime quirks

- **First frame of a demo has no snapshot.** `cl.snap.valid == qfalse` until the
  second snapshot arrives. Code reading `cl.snap.entities` on frame 1 = crash.
- **Demo-time vs real-time:** `trap_GetServerTime` returns demo-time during playback,
  but `Sys_Milliseconds` returns real-time. Mixing them = drift.
- **`seekclock` only lands on snapshot boundaries.** Requesting seek to 8:52.5 will
  land at 8:52.4 or 8:52.5 depending on snapshot rate. Not a bug, a spec.
- **AVI capture rate floats.** `cl_avidemo 60` does not guarantee exactly 60 fps.
  Variation ±1 fps over a 10-minute capture is normal.
- **`video avi name :demoname`** — the `:` prefix is important; without it the output
  filename is literal "demoname.avi".

## Source-tree quirks

- **wolfcamql-src (GitHub) lags the installed .exe.** The shipped `wolfcamql.exe`
  has patches the public source doesn't. See FT-4: we Ghidra the .exe to find them.
- **wolfcamql-local-src (tarball) is CLOSER to the .exe but still not identical.**
  Tarball date 2016-08-13; .exe timestamp is later. Lost patches exist.
- **Duplicate cgame source dirs.** `code/cgame/` has both ioquake3-style `cg_*.c` AND
  wolfcam-style `wolfcam_*.c`. Some ioquake3 files are dead code (never called) but
  still compile. Grep before assuming a file is live.
- **`Makefile.local`** can override base Makefile — check for it before assuming
  build settings from `Makefile` alone.

## Data quirks

- **Configstrings up to CS_MAX (2048 in QL).** Q3 hardcodes 1024 in some places.
  Wolfcam patched most, but a few `1024` literals remain in `cl_parse.c` — watch.
- **MAX_CLIENTS = 64 in QL.** Q3 was 32. Client arrays must be sized 64+.
- **MAX_WEAPONS = 16** (same as Q3), but weapon constants go up to 15 (WP_HMG).
  Index math is fine, but a few Q3 engines assume weapon <= 9 (gauntlet..BFG).

## Gotchas we've hit in THIS project

- **FT-1 parser discrepancy:** our custom parser briefly reported wrong `serverTime`
  because we didn't mask the toggle bits on snapshot events (see "event toggle bits"
  above). Fixed 2026-04-12.
- **Part 2 audio desync:** wolfcam's AVI capture was 59.97 fps when we asked for 60,
  causing 1-frame drift per 30 seconds. Fixed by using ffmpeg pipe approach.
- **Corrupt demo at frag 14 in Part 5:** demo had `svc_gamestate` mid-stream (match
  restart). Our parser reset correctly but wolfcam's AVI capture dropped frames.
  Workaround: seek past the restart before `video avi`.

## See also

- `_diffs/code/qcommon/msg.c.diff.md` — exact proto-73 delta vs ioquake3
- `_diffs/code/client/cl_parse.c.diff.md` — parser divergences
- `docs/reference/dm73-format-deep-dive.md` — our 1,337-line authoritative doc
- `docs/reference/wolfcam-commands.md` — (to be written in Phase 2) full console cmd inventory
