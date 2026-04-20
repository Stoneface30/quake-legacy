# quake3-source — Architecture

**Upstream:** https://github.com/id-Software/Quake-III-Arena
**Size (original):** 31 MB (shallow)
**Role in our project:** id Software ground-truth for Q3. Authority for Q3 demo protocol, Huffman compression, and the entityState/playerState structs that every Q3 fork inherits.

## Module map
code/
├── qcommon/       — msg.c, huffman.c, net_chan.c, common.c (THE reference)
├── client/        — cl_demo.c, cl_parse.c, cl_main.c
├── server/        — full authoritative server
├── game/, cgame/, ui/ — VM sources
├── renderer/      — OpenGL renderer
└── botlib/        — bot AI

## Key files
- `code/qcommon/huffman.c` — Huffman codec — every byte in dm_68/66 is encoded with this
- `code/qcommon/msg.c` — MSG_* read/write and entityState/playerState field tables — foundation of the protocol
- `code/client/cl_demo.c` — Demo record/playback, client side
- `code/server/sv_demo.c` — Demo write, server side
- `code/qcommon/q_shared.h` — Entity state fields, playerState_t, snapshot_t, MOD_*, EV_*, WP_*

## See also
- `_canonical/` — canonical copy of files from this tree that are unique or authority-winners
- `engine/engines/quake3-source/` — near-duplicate variants preserved for diff
- `_diffs/` — per-file diffs where this tree differs from canonical
