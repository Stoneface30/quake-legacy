# Proto-73 Port Review — 2026-04-17

> Source: deep code-reviewer agent over `game-dissection/engines/_diffs/` + `docs/reference/dm73-format-deep-dive.md`.
> Goal: blueprint for FT-1 / Phase 3.5 Track A — port wolfcamql's `.dm_73` playback into q3mme so we can retire wolfcam and get max-quality captures through q3mme's renderer.

---

## Executive Summary

- The wolfcamql proto-73 surface is concentrated in **three files**: `qcommon/msg.c` (entity/playerstate field tables + huffman seed), `client/cl_parse.c` (message dispatch + gamestate protocol detection), and `client/client.h` (the `demoInfo_t` / `rewindBackups_t` / `demoFile_t` structs that are entirely wolfcamql-specific). Everything else is either cosmetic or already present in q3mme.
- The huffman layer itself (`qcommon/huffman.c`) is functionally identical between wolfcamql-src and ioquake3 — the only wolfcamql additions are `Huff_getBloc`/`Huff_setBloc` accessors and the `maxoffset` bounds-checking guards that vanilla engines removed. **These guards are a real buffer-overread risk in q3mme if removed naively.**
- Protocol-version constants are the sharpest divergence: wolfcamql defines `PROTOCOL_VERSION 91` and `NUM_DEMO_PROTOCOLS 15` (covering 43..48, 66..71, 73, 90, 91) while ioquake3/q3mme use `PROTOCOL_VERSION 71` and a dynamically-sized array. Porting means carrying wolfcamql's full `demo_protocols[]` table verbatim.

---

## Per-File Analysis

### 1. `code/qcommon/msg.c` — bit-level message encode/decode

**Diff size (wolfcamql vs ioquake3):** +86 / −1802 lines. wolfcamql is the canonical (85 KB); ioquake3 is 40 KB. wolfcamql contains roughly twice as much code.

**Confidence: HIGH** for the following findings.

#### Q1 — What functions changed?

wolfcamql-specific additions not present in any other tree:

| Function | Location | Purpose |
|---|---|---|
| `MSG_ReadDeltaEntity` (protocol dispatch) | msg.c:1944-2120 | Selects field table based on `di.protocol` (73 / 90 / 91 / Q3) |
| `entityStateFieldsQldm73[]` | msg.c:1081-1142 | 53-entry field table for dm_73 entity states |
| `entityStateFieldsQldm90[]` | msg.c:1015-1079 | 57-entry table adding `jumpTime`, `doubleJumped` |
| `entityStateFieldsQldm91[]` | msg.c:948-1013 | 60-entry table adding `health`, `armor`, `location` |
| `playerStateFieldsQldm90[]` | msg.c:2190-2242 | Extends PS with `jumpTime : 32`, `doubleJumped : 1` |
| `playerStateFieldsQldm91[]` | msg.c:2123-2188 | Further extends with `crouchTime`, `fov`, `forwardmove`, etc. |
| `MSG_initHuffman` | msg.c:3385-3396 | Seeds huffman from `msg_hData[256]` — identical across all trees |
| `MSG_ReadDeltaPlayerstate` | msg.c:2949-3124 | Selects field table by protocol |

#### Q2 — What data formats changed?

Three new entity-state field tables encode QL-specific entity fields absent from Q3:

| Field | Q3? | dm_73? | Notes |
|---|---|---|---|
| `pos.gravity` | No | **Yes** (field 9, 32 bits) | QL gravity per-entity |
| `apos.gravity` | No | **Yes** (field 46, 32 bits) | angular gravity |
| `event` | Yes (8 bits) | **Yes (10 bits)** | Extra 2 bits = toggle bits `EV_EVENT_BIT1/2` |
| `eFlags` | Yes (16 bits) | **Yes (19 bits)** | Three extra flag bits |
| `powerups` | Yes (16) | **Yes (16)** | Same |
| `jumpTime` (PS) | No | No (dm_73), Yes (dm_90) | Protocol-90 addition |
| `health/armor/location` (entity) | No | No (dm_73), Yes (dm_91) | Spectator-only |

The Q3 entity state table has 51 fields. dm_73 has 53. dm_90 has 57. dm_91 has 60.

**Player state for dm_73 reuses the Q3 table** (`playerStateFieldsQ3`, msg.c:2244-2295, 48 fields) — confirmed at msg.c:2990-2991. No new PS fields for proto-73 specifically.

The stat-array block (stats / persistant / ammo / powerups) is identical across all protocols — 4 optional masked bitmask blocks, each 16 entries.

#### Q3 — What magic numbers / protocol IDs are wolfcamql-specific?

| Constant | Value | Location | Significance |
|---|---|---|---|
| `PROTOCOL_VERSION` | **91** (wolfcamql) vs 71 (ioquake3/q3mme) | qcommon.h | Must be 91 to accept newest QL demos |
| `NUM_DEMO_PROTOCOLS` | **15** | qcommon.h | Covers 43,44,45,46,47,48,66,67,68,69,70,71,**73,90,91** |
| `EV_OBITUARY` | **58** | bg_public.h | QL event code — Q3 uses a different value (`EVQ3_OBITUARY`) |
| `EV_EVENT_BITS` | **0x00000300** | bg_public.h:782-788 | High-2-bits toggle mask; strip before event compare |
| `FLOAT_INT_BITS` | 13 | msg.c | Compact float encoding for positions |
| `FLOAT_INT_BIAS` | 4096 | msg.c | Bias for the 13-bit int-float range |
| `MAX_MSGLEN` | **49152** (16384×3) vs 16384 (ioquake3) | qcommon.h | wolfcamql uses 3× larger message buffer |
| `PROTOCOL_QL` | defined in wolfcamql | qcommon.h | Symbolic alias for 73 |
| `MOD_THAW` (30), `MOD_LIGHTNING_DISCHARGE` (31), `MOD_RAILGUN_HEADSHOT` (33) | QL-only | bg_public.h:1294-1339 | MOD > 28 are QL-only; filter `MOD_SWITCH_TEAMS (29)` from kill stats |

#### Q4 — Which changes are strictly needed for proto-73 playback vs cosmetic?

**MANDATORY for playback:**

1. `entityStateFieldsQldm73[]` — the 53-field table. Without it, entity delta-decoding selects the wrong field count and all positions/events are corrupt.
2. `event` field width: **10 bits** (not 8). The 2 extra bits are the sequence-toggle. Vanilla Q3 engines read only 8 bits, dropping the toggle bits and causing event mismatches.
3. `eFlags` field width: **19 bits** (not 16). Reading 16 produces corrupt flags.
4. Protocol detection ladder in `MSG_ReadDeltaEntity`: the `if (di.protocol == 73)` branch that selects `entityStateFieldsQldm73` over `entityStateFieldsQ3`.
5. `demo_protocols[]` array extended to include 73 (and 90, 91 for forward compat).
6. `PROTOCOL_VERSION 91` (or at minimum acceptance of protocol 73 in the demo-open path).
7. The huffman seed table `msg_hData[256]` (msg.c:3126-3383) — already in q3mme/ioquake3; confirm it matches wolfcamql's verbatim copy.
8. `MSG_initHuffman` called at startup.
9. Protocol detection from `CS_SERVERINFO` (`\protocol\73`) in `CL_ParseGamestate` — wolfcamql code at cl_parse.c:954-1015.

**OPTIONAL / cosmetic:**

- wolfcamql's `di` (demoInfo_t) struct tracking — wolfcamql-specific analytics (team tracking, round starts, seeking). Needed for kill extraction; not for basic playback.
- `rewindBackups_t` / demo seeking — wolfcamql-specific, not needed for a capture pipeline.
- Extended AVI capture cvars — wolfcamql-specific additions irrelevant to the port.
- `Huff_getBloc`/`Huff_setBloc` — only needed if external code peeks into huffman state mid-message.

#### Q5 — Bugs, security, integer overflow

1. **`MAX_MSGLEN` mismatch risk.** wolfcamql = 49152, q3mme = 16384. If a QL server sends a snapshot larger than 16384 bytes (possible with 64 clients and many entities), q3mme's `msg_t` buffer overflows on read. **Silent memory corruption.** Fix: adopt wolfcamql's value.

2. **huffman `maxoffset` guard removal is a regression in ioquake3/q3mme.**
   ```c
   // wolfcamql HAS this guard:
   if (bloc >= maxoffset) { *ch = 0; *offset = maxoffset + 1; return; }
   // ioquake3 / q3mme REMOVED it
   ```
   Without the guard, a truncated or corrupt demo message can cause `get_bit` to read past the end of the input buffer — classic OOB read. **Keep the maxoffset parameter and its guard.** Do not regress.

3. **`buffer = mbuf->data+ + offset`** typo in quake3-source and openarena-engine (double-plus). wolfcamql has the correct `mbuf->data + offset`. **Do not copy from those trees.**

4. **`seq[65536]` stack buffer in `Huff_Decompress`/`Huff_Compress`** — wolfcamql uses stack-allocated 65536-byte buffers. Safe on modern Windows/Linux; wasteful. Not a bug but a stack-pressure consideration.

5. **`Huff_Init` gated with `#if 0` in quake3e.** If q3mme inherited this, `MSG_initHuffman` is never called and the huffman tree is zero-initialized. **All decompression silently produces garbage — no crash, just wrong data.** Verify the call site in q3mme's startup sequence before anything else.

6. **Integer narrowing in `event` field.** Q3-era code stores `event` in `byte` (8 bits). wolfcamql's 10-bit read silently truncates on strict C implementations. **Widen `entityState_t.event` storage to `short`/`int`** in the port — check `bg_public.h` and `cg_local.h`.

---

### 2. `code/qcommon/huffman.c` — demo huffman tables

**Diff size (wolfcamql vs ioquake3):** **IDENTICAL** — sha256 matches. No porting work needed here if targeting ioquake3 lineage.

**vs quake3-source:** +17 / −34 lines — cosmetic except:
- wolfcamql adds `Huff_getBloc(void)` / `Huff_setBloc(int)` — LOW risk.
- quake3-source missing `huff.loc[NYT] = huff.tree` initializer in `Huff_Compress` and `Huff_Init` — **real bug** (compressor tree has dangling NYT pointer). wolfcamql and ioquake3 both have the fix. **Do not copy from quake3-source.**
- quake3-source has the `mbuf->data+ + offset` typo (see above).

**vs quake3e:** +53 / −77 lines. quake3e refactored huffman to use instance-local `blocNode`/`blocPtrs` fields instead of a global `bloc`. Improvement but significant API break. For a port targeting q3mme (closer to ioquake3 ancestry), stay with the wolfcamql/ioquake3 API.

---

### 3. `code/qcommon/common.c` — engine bootstrap

**Diff size (wolfcamql vs ioquake3):** +220 / −897 lines. wolfcamql 109 KB vs ioquake3 90 KB — wolfcamql is a superset.

wolfcamql-specific additions:

- `Com_RealTime` signature extended: adds `qboolean now` and `int convertTime` params — used for demo timestamp conversion. ioquake3 has `Com_RealTime(qtime_t*)`. **Port must provide the richer signature or update all callers.**
- wolfcamql exposes `com_timescaleSafe`, `com_autoWriteConfig`, `com_execVerbose`, `com_qlColors`, `com_brokenDemo` cvars — wolfcamql-specific, not needed for playback.
- `Sys_QuakeLiveDir()` — locates the QL installation. Needed for file path resolution when loading demos from Steam. **q3mme will need a stub or equivalent.**
- `mapNames_t MapNames[]` extern — map-name lookup table for UI display. Not needed for parse pipeline.

**For proto-73 playback specifically**, common.c changes are mostly cosmetic. The only load-bearing delta is the `demo_protocols[]` array initialization, which must include 73.

**Confidence: MED** (large diff, no inline content available; findings derived from qcommon.h diff).

---

### 4. `code/client/cl_parse.c` — message dispatch + gamestate protocol detection

**Diff size:** +82 / −1505 lines. wolfcamql is 71 KB vs ioquake3 26 KB — ~3× larger.

wolfcamql-specific demo playback logic:

| Function | Source ref | Significance |
|---|---|---|
| `CL_ParseGamestate` | cl_parse.c:886-1068 | Protocol detection from `CS_SERVERINFO \protocol\73`. Ladder checks 43..91. |
| `CL_ParseSnapshot` | cl_parse.c:405-641 | wolfcamql adds `justPeek` param for seeking |
| `CL_ReadDemoMessage` | cl_main.c:1759-1806 | wolfcamql adds `qboolean seeking` param |
| `CL_ParseExtraServerMessage` | cl_parse.c (wolfcamql only) | Multi-demo file parsing — not needed for port |
| `CL_ParseVoipSpeex` / `CL_ParseVoip` | cl_parse.c | Handles Speex and Opus VoIP after `svc_EOF` |
| `svc_extension` / `svc_voip` dispatch | qcommon.h:289-300 | wolfcamql: `svc_extension=9`, `svc_voip=10`. ioquake3: `svc_voipSpeex=9`, `svc_voipOpus=10`. **Wire values differ — must use wolfcamql's numbering for dm_73 compat.** |

**Confidence: HIGH** for protocol dispatch; **MED** for seeking/multi-demo details.

---

### 5. `code/game/bg_public.h` — entity state / event format

**Diff size (wolfcamql vs quake3-source):** +173 / −929 lines. wolfcamql 40 KB vs quake3-source 20 KB.

Key wolfcamql additions:

| Addition | Location | Notes |
|---|---|---|
| Full QL configstring index table (CS_ROUND_STATUS 661, CS_ROUND_TIME 662, etc.) | bg_public.h:73-287 | Essential for CA round detection. Q3 stops at ~200. |
| CS_PMOVE_SETTINGS (682), CS_WEAPON_SETTINGS (683) | bg_public.h | QL physics tuning per-server |
| Protocol-91 re-shuffle `CS91_*` (666..715) | bg_public.h:237-287 | GUID, Steam ID, workshop IDs |
| `entity_event_t` extended to EV_HEADSHOT (89), EV_POI (90), EV_RACE_* (93-95), EV_DAMAGEPLUM (96), EV_AWARD (97), EV_INFECTED (98) | bg_public.h:790-923 | QL-only events; Q3 stops at ~70 |
| `EVQ3_*` parallel enum for Q3 protocol compat | bg_public.h:926+ | Wolfcam handles Q3 + QL in same binary |
| `MOD_THAW` (30), `MOD_LIGHTNING_DISCHARGE` (31), `MOD_HMG` (32), `MOD_RAILGUN_HEADSHOT` (33) | bg_public.h:1294-1339 | QL-only MOD values |
| `meansOfDeath_t` max value = 33 | bg_public.h | Q3 stops at 28 (MOD_GRAPPLE) |

**Confidence: HIGH** — all confirmed by dm73-format-deep-dive.md §§7-8 with exact line citations.

---

### 6. `code/client/client.h` — wolfcamql-specific client state

**wolfcamql-only structures:**

```c
#define MAX_DEMO_FILES 64

typedef struct { qboolean valid; int num; qhandle_t f; int serverTime;
                 clSnapshot_t snap; int serverMessageSequence; } demoFile_t;

typedef struct {
    qboolean olderUncompressedDemo;
    int olderUncompressedDemoProtocol;   // handles 43-48 (pre-huffman)
    demoObit_t obit[MAX_DEMO_OBITS];
    qboolean cpma; int cpmaLastTs/Td/Te;
    demoFile_t demoFiles[MAX_DEMO_FILES];
    int roundStarts[MAX_DEMO_ROUND_STARTS];
    teamSwitch_t teamSwitches[MAX_TEAM_SWITCHES];
    // ... 50+ fields tracking demo state
} demoInfo_t;
extern demoInfo_t di;

typedef struct {
    clientActive_t cl; clientConnection_t clc; clientStatic_t cls;
} rewindBackups_t;
#define MAX_REWIND_BACKUPS 12  // ~1.75 MB each
extern rewindBackups_t *rewindBackups;
```

**Modified `clientActive_t`:**
- `snapshots[PACKET_BACKUP][MAX_DEMO_FILES]` — 2D array for multi-demo support. ioquake3 has 1D. **ABI break.**
- `qboolean draw` field added.
- `cgameTime`, `realProtocol` fields added to `clientConnection_t`.

**Modified `clientConnection_t`:**
- `demoReadFile` / `demoWriteFile` (two separate handles) vs ioquake3's single `demofile`.
- `int demoPlayBegin` — seek start position.
- `popenData_t *wfp` — pipe handle for streaming demos.

**Modified function signatures:**
```c
void CL_ReadDemoMessage(qboolean seeking);                         // vs ioquake3: void CL_ReadDemoMessage(void)
void CL_ParseExtraServerMessage(demoFile_t *df, msg_t *msg, qboolean justPeek);
void CL_ParseSnapshot(msg_t *msg, clSnapshot_t *sn, int serverMessageSequence, qboolean justPeek);
qboolean CL_PeekSnapshot(int snapshotNumber, snapshot_t *snapshot);
void CL_AddAt(int serverTime, const char *clockTime, const char *command);  // `at` command
```

**Confidence: HIGH** — inline diff fully available.

---

### 7. `code/qcommon/qcommon.h` — protocol constants

| Constant | wolfcamql | ioquake3 |
|---|---|---|
| `PROTOCOL_VERSION` | **91** | 71 |
| `PROTOCOL_LEGACY_VERSION` | 68 | 68 (same) |
| `NUM_DEMO_PROTOCOLS` | **15** | dynamic array |
| `MAX_MSGLEN` | **49152** | 16384 |
| `svc_extension` / `svc_voip` | 9 / 10 | `svc_voipSpeex` (9) / `svc_voipOpus` (10) |
| `PACKET_BACKUP` | defined in wolfcamql's qcommon.h | moved to ioquake3's |
| `MAX_SNAPSHOT_ENTITIES` | 256 | 256 |

The wolfcamql `demo_protocols[]` array must be initialized to:
```c
{ 43, 44, 45, 46, 47, 48, 66, 67, 68, 69, 70, 71, 73, 90, 91 }
```
15 entries.

---

## Port Checklist — Ordered for q3mme

1. **[CRITICAL] Adopt `entityStateFieldsQldm73[53]`** from `msg.c:1081-1142`.
2. **[CRITICAL] Fix `event` field to 10 bits** (not 8).
3. **[CRITICAL] Fix `eFlags` field to 19 bits** (from 16).
4. **[CRITICAL] Extend `demo_protocols[]`** to include 73 (and 90, 91). Add `PROTOCOL_VERSION 91`.
5. **[CRITICAL] Protocol detection in `CL_ParseGamestate`**: wolfcamql ladder (cl_parse.c:954-1015) reads `\protocol\` from `CS_SERVERINFO` configstring 0.
6. **[CRITICAL] Increase `MAX_MSGLEN` to 49152.**
7. **[CRITICAL] Adopt wolfcamql's `bg_public.h` configstring table** (CS_ROUND_TIME=662, CS_PLAYERS=529..592, etc.).
8. **[CRITICAL] Adopt wolfcamql's `entity_event_t` enum** (EV_OBITUARY=58, QL events up to 98).
9. **[CRITICAL] Retain huffman `maxoffset` guard** in `Huff_offsetReceive`/`send`.
10. **[HIGH] Add `pos.gravity` (field 9) and `apos.gravity` (field 46)** to `entityState_t`.
11. **[HIGH] Add `MOD_THAW` (30), `MOD_LIGHTNING_DISCHARGE` (31), `MOD_HMG` (32), `MOD_RAILGUN_HEADSHOT` (33)** to `meansOfDeath_t`.
12. **[HIGH] Implement `bcs0`/`bcs1`/`bcs2` configstring reassembly** (cl_cgame.c:704-767).
13. **[HIGH] Handle old uncompressed demos** (protocol 43-48). When opening a file, the extension check must accept `.dm_73`.
14. **[MED] Add wolfcamql's `EV_EVENT_BITS` masking** everywhere event codes are compared: `(event & ~0x300)` before comparison.
15. **[MED] EV_OBITUARY deduplication** (cl_main.c:2092-2167): same entity emits an obituary for ~300ms across snapshots.
16. **[MED] `CL_AddAt` / seekclock command** — the `at <clocktime> <command>` scheduling used in WolfcamQL automation scripts.
17. **[LOW] `Huff_getBloc`/`Huff_setBloc`** — only needed if any caller peeks at bit position externally.
18. **[LOW] `demoInfo_t di`** struct — full wolfcamql analytics. Not needed for basic playback; required for kill extraction.

---

## Risks / Sharp Edges

**RISK-1 (HIGH): `snapshots` 2D array ABI break.**
wolfcamql's `cl.snapshots[PACKET_BACKUP][MAX_DEMO_FILES]` is a fundamentally different layout from every other engine's `cl.snapshots[PACKET_BACKUP]`. Every reference to `cl.snapshots` must be audited. **In a pure capture pipeline (no real-time playback UI), consider using a flat 1D ring buffer and not porting the multi-demo feature at all.**

**RISK-2 (HIGH): VoIP op-code collision.**
wolfcamql uses `svc_extension=9`, `svc_voip=10`. ioquake3 uses `svc_voipSpeex=9`, `svc_voipOpus=10`. Same wire values, different handlers. If q3mme inherits ioquake3's dispatch and a QL demo contains VoIP, the wrong handler fires. **Use wolfcamql's dispatch constants.**

**RISK-3 (HIGH): huffman `maxoffset` removal.**
Active out-of-bounds read bug in ioquake3/q3mme if fed a malformed or truncated demo. wolfcamql's guard is correct. **Do not "simplify" by copying ioquake3's version.**

**RISK-4 (MED): Protocol 91 CS-index re-shuffle.**
For newer QL demos (protocol 91), CS indices 666-715 shift to `CS91_*` layout. For a pure dm_73 pipeline this is deferred — flag it for Phase 3.5 if newer demos are ever added.

**RISK-5 (MED): `MAX_MSGLEN` stack pressure.**
wolfcamql's 49152-byte message buffer is stack-allocated in several call paths. Consider heap-allocating in the port if targeting constrained platforms.

**RISK-6 (MED): Huffman init call site.**
quake3e gates `Huff_Init` with `#if 0`. If q3mme inherited this, `MSG_initHuffman` is never called and all decompression silently produces garbage. **Verify the call site in q3mme's startup sequence before anything else.**

**RISK-7 (LOW): `pos.gravity` / `apos.gravity` struct presence.**
If `entityState_t` in q3mme lacks `gravity` fields, the dm_73 field table decoder may silently write to adjacent memory. **Verify the `NETF` macro resolves correctly against q3mme's `entityState_t`.**

---

## Confidence Summary

| Area | Confidence | Basis |
|---|---|---|
| entity field tables (dm_73 vs Q3) | HIGH | dm73-format-deep-dive.md + msg.c line citations |
| huffman layer | HIGH | Full inline diff |
| protocol constants | HIGH | Full inline diff |
| client.h struct deltas | HIGH | Full inline diff |
| bg_public.h event/MOD tables | HIGH | dm73-deep-dive §§7-8 with source citations |
| cl_parse.c internals | MED | Diff stat only; cross-refs from deep-dive |
| common.c internals | MED | Diff stat only |
| q3mme current state | LOW | Not read directly; inferences from manifest |

---

## Mandatory Source Files

Three files are the spine of the port:
- `tools/quake-source/wolfcamql-src/code/qcommon/msg.c` (85 KB — entity/PS field tables, huffman seed)
- `tools/quake-source/wolfcamql-src/code/client/cl_parse.c` (71 KB — protocol detection, gamestate parse)
- `tools/quake-source/wolfcamql-src/code/game/bg_public.h` (40 KB — QL configstring indices, event codes, MOD values)

These are restored by the engine-recovery background agent (see tomorrow's wrap-up doc §3).
