# q3mme — Protocol Layer

q3mme is **protocol-68 only** (vanilla Q3 demos). It cannot play `.dm_73` (QL) demos
without the port we're planning.

## Current state: proto-68 / proto-66

q3mme's `qcommon/` is ioquake3-stock for the protocol layer:
- `msg.c` uses ioquake3's `entityStateFields[]` and `playerStateFields[]`
- `cl_parse.c` dispatches the standard svc_* opcodes
- `q_shared.h` has Q3 constants (MAX_CLIENTS=32, MAX_WEAPONS=16, Q3 WP_* and MOD_*)
- Huffman table is stock Q3 (identical to QL's, so this layer doesn't need patching)

## What the port adds (from wolfcamql)

See the full plan in `SYNTHESIS.md` "Migration Paths" section. Summary of files
touched in `qcommon/` + `client/`:

### qcommon/msg.c — field table deltas
Replace or extend:
- `entityStateFields[]` — add QL fields (generic1 meaning, extended event parms)
- `playerStateFields[]` — add QL stats/persistant/powerups array sizes
- `MSG_ReadDeltaEntity` / `MSG_ReadDeltaPlayerstate` — use the patched tables

### qcommon/q_shared.h — constant deltas
- `MAX_CLIENTS` → 64 (QL) or keep 32 with a new `QL_MAX_CLIENTS` alias
- `MAX_WEAPONS` → typically 16 (same), but ensure WP_* enum covers WP_HMG etc.
- `CS_*` indices — add QL-extended slots past CS_MAX_Q3
- `weapon_t` — add WP_NAILGUN, WP_PROX_LAUNCHER, WP_CHAINGUN, WP_HMG, WP_GRAPPLING_HOOK
- `meansOfDeath_t` — add MOD_* for each QL weapon + MOD_HEADSHOT, MOD_TELEFRAG variants

### qcommon/huffman.c — verify only
Same algorithm and table as Q3. Just confirm bit ordering matches.

### client/cl_parse.c — proto-73 branches
- `CL_ParseGamestate` — parse extended serverInfo + configstring count
- `CL_ParseSnapshot` — use the patched MSG_ReadDelta* calls (automatic via msg.c)
- `CL_ParseServerMessage` — dispatch extended svc_ opcodes if any (proto-73 didn't
  add new opcodes AFAIK, just extended existing message formats)

### client/cl_demo.c — file-open dispatch
- Accept `.dm_73` extension in `CL_PlayDemo_f` (currently only `.dm_68` / `.dm_66`)
- Read protocol version from demo header and set `clc.serverProtocol` accordingly

## Why the merge is clean

- q3mme's demo subsystem (`cg_demos_*.c`) is **protocol-agnostic**: it operates on
  `cl.snap.entities[]` and `cl.snap.ps` after they've already been parsed. Whether
  those structures were populated from proto-68 or proto-73 doesn't matter to
  the camera spline code.
- q3mme's capture pipeline is **also protocol-agnostic**: it renders whatever the
  renderer produces.
- Conflict is confined to `qcommon/msg.c`, `qcommon/q_shared.h`, `client/cl_parse.c`,
  `client/cl_demo.c`. ~4 files with deltas.

## Validation plan

After merge:
1. Build q3mme-with-proto73 — must compile with no warnings
2. Play a known proto-68 demo — must work identically to stock q3mme
3. Play a known proto-73 demo — must reproduce wolfcamql's rendering byte-for-byte
   on the `cl.snap` structures (validate via in-engine JSONL dump)
4. Run q3mme's demo-cut tool on a proto-73 demo — must produce a valid proto-73
   sub-demo (this exercises the WRITE side of the protocol, not just read)

## Open questions (resolve during port)

- Does q3mme's demo-cut write code need proto-73 awareness? (Likely yes — it
  re-encodes the message stream.)
- Does the `com_protocol` cvar need to be selectable, or auto-detected per demo?
  (Auto-detect is cleaner but ioquake3 uses cvar.)
- Do we maintain compat with proto-66 (Q3 1.16n) demos? (Our corpus is dm_73 only,
  but upstreaming the patch would need this.)

## See also

- `_docs/wolfcamql-src/PROTOCOL_LAYER.md` — full proto-73 reference
- `_diffs/code/qcommon/msg.c.diff.md` — line-by-line delta
- `docs/reference/dm73-format-deep-dive.md` — authoritative format doc
