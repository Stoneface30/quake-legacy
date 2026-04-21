# quake3e — Protocol Layer

**Same as vanilla Q3 / ioquake3: proto-68 / proto-66.** No `.dm_73` support.

## What's in qcommon/

- `msg.c` with ioquake3's `entityStateFields[]` — Q3A standard
- `huffman.c` — standard fixed table
- `net_chan.c` — standard Q3 channel framing
- `q_shared.h` — Q3 constants (MAX_CLIENTS=32, MAX_WEAPONS=16)

Nothing novel vs ioquake3 on the protocol side.

## If we port proto-73 into quake3e

Same story as the q3mme port: patch `msg.c`, `q_shared.h`, `cl_parse.c`, `cl_demo.c`
with wolfcamql-src deltas. Use `_diffs/` docs as roadmap.

But we probably **won't** port proto-73 into quake3e. Tr4sH Quake targets q3mme
(for camera/motion blur/DOF). quake3e is reference for renderer/capture improvements
only.

## Small delta worth noting

quake3e's `msg.c` has some **performance optimizations** over ioquake3 (tighter loops,
SSE hints). When porting proto-73, we should evaluate whether to base on ioquake3's
slower-but-cleaner msg.c or quake3e's optimized variant. The field-table deltas are
the same either way.

## See also

- `_docs/wolfcamql-src/PROTOCOL_LAYER.md` — proto-73 reference
- `_docs/q3mme/PROTOCOL_LAYER.md` — port target
