# wolfcamql-src — Protocol Layer (dm_73)

This is the core reason this tree is our authority. Everything in this doc is about
how the Quake Live network protocol (and thus the `.dm_73` demo file format) differs
from vanilla Q3's protocol 68 / 66.

## File layout of `.dm_73`

```
[4 bytes] int32 sequence  = -1      — magic header for start-of-demo
[4 bytes] int32 msgLen              — length of first message
[N bytes] Huffman-compressed message bitstream
[...repeat...]
[4 bytes] int32 sequence  = -1      — EOF sentinel
```

Messages decompressed with the fixed Huffman table in `code/qcommon/huffman.c`.

## Major proto-73 deltas vs proto-68 (vanilla Q3)

### 1. entityState_t field additions

`code/qcommon/msg.c::entityStateFields[]`

QL added / reordered several entityState fields relative to Q3:
- `pos.trTime`, `pos.trDuration` encoding uses more bits
- `generic1` repurposed for QL-specific state
- Event parm packing extended (weapon indices exceed 16)

The full field table is the single source of truth — diff against ioquake3's
`msg.c` to see every delta. Use `_diffs/code/qcommon/msg.c.diff.md` for the
line-by-line view.

### 2. playerState_t field additions

`code/qcommon/msg.c::playerStateFields[]`

- `ping` encoding
- `stats[]` array extended (QL has more stat slots)
- `persistant[]` array extended
- `powerups[]` encoding includes QL-specific powerups (PW_*_QL)
- `ammo[]` and `weapons` bitmask expanded

### 3. Configstring additions

`code/qcommon/q_shared.h` + `cl_parse.c`

New CS_* indices for QL:
- CS_STEAM_ID, CS_MATCH_STATE, CS_READY_* (pre-match state machine)
- Extended CS_PLAYERS_* slots (up to 64 clients)

### 4. Weapon constants

`code/qcommon/q_shared.h::weapon_t`

- WP_GRAPPLING_HOOK, WP_NAILGUN, WP_PROX_LAUNCHER, WP_CHAINGUN, WP_HMG
- MOD_* obituary constants extended accordingly in `code/game/bg_public.h`

### 5. Event constants

`code/game/bg_public.h::entity_event_t`

QL-specific events: EV_HEADSHOT, EV_OBITUARY (with QL MOD range), EV_RAILROCKET,
EV_GESTURE extensions, EV_QL_ACCURACY_UPDATE, EV_POWERUP_QUAD_QL, ...

## Parsing pipeline

```
raw bytes from .dm_73
  ↓
CL_ReadDemoMessage (cl_demo.c)          — read 4-byte len, read N bytes
  ↓
Huffman_Decompress (huffman.c)          — into a msg_t bitstream
  ↓
CL_ParseServerMessage (cl_parse.c)      — dispatch by svc_* opcode
  ├── svc_gamestate  → CL_ParseGamestate (init: configstrings + baselines)
  ├── svc_snapshot   → CL_ParseSnapshot  (delta-encoded entity + player state)
  ├── svc_serverCommand → cgame trap SC event
  └── svc_download   → ignored in demo playback
  ↓
MSG_ReadDeltaEntity / MSG_ReadDeltaPlayerstate (msg.c)
  ├── field-by-field using entityStateFields[]
  └── bit-level encoding per field type (angle/coord/uint16/etc.)
  ↓
snapshot_t cl.snap                       — reconstructed game state
  ↓
cgame VM vmMain(CG_DRAW_ACTIVE_FRAME)
```

## Critical functions for porting

If porting proto-73 into another engine (q3mme path), these are the exact function
bodies that must come over from wolfcamql:

1. **`msg.c::MSG_ReadDeltaEntity`** + its `entityStateFields[]` table
2. **`msg.c::MSG_ReadDeltaPlayerstate`** + its `playerStateFields[]` table
3. **`cl_parse.c::CL_ParseGamestate`** — especially the systemInfo / serverInfo parse
4. **`cl_parse.c::CL_ParseSnapshot`** — the delta-from-base logic
5. **`q_shared.h`** constants — WP_*, MOD_*, CS_*, EV_*, MAX_* (all the limits)
6. **`huffman.c`** — verify the symbol table matches Q3's (it does, but confirm)

## Validation strategy (FT-1)

Our custom C++ parser at `phase2/dm73parser/` cross-checks against:
- `UDT_json.exe` output (uberdemotools) — authoritative
- wolfcamql-src behavior at runtime — byte-identical snapshot reconstruction

If any of the three disagree, the authoritative answer is the one matching actual
Quake Live server behavior (observable via live play), not the wolfcam source tree.

## Gotchas we've already hit

- **Baseline entities:** `svc_gamestate` sends MAX_GENTITIES baselines, most empty.
  Naive parsers that stop at "first empty" miss mid-list populated baselines.
- **Delta-from-none:** first snapshot after a gamestate has `deltaNum == 0`, meaning
  delta from the implicit-zero state. Not from the previous snapshot.
- **Event wrap-around:** `event & ~0x300` masks toggle bits the server flips each
  consecutive event of the same type. Forgetting the mask = missed events.
- **Configstring overflow:** CS_* past 1023 are allowed in QL but not in Q3.
  Q3-only parsers truncate and lose end-of-match state.
