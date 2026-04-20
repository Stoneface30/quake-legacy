# .dm_73 Format — Binary Reference

Source tree: `G:/QUAKE_LEGACY/tools/quake-source/wolfcamql-src/code/`

---

## File Container

No file magic, no version field, no TOC. Uninterrupted sequence of
server-to-client messages prefixed with `(sequenceNumber:LE32, length:LE32)`.

```
offset  size  field                  notes
------  ----  ---------------------  -----------------------------------
   0      4   sequenceNumber  LE32   monotonically increasing; -1 = EOF
   4      4   messageLength   LE32   bytes of payload; -1 = EOF
   8    len   payload                Huffman-compressed bitstream
```

Terminator: seq==-1 or len==-1. MAX_MSGLEN = 49152 bytes (`qcommon.h`).
Source: `client/cl_main.c:1566` (`CL_ReadDemoMessage`).

---

## Payload Dispatch (svc_ops_e)

After `MSG_Bitstream()` (decompression), each payload contains:
1. `reliableAcknowledge : LE32` (protocol >= 46)
2. Loop: read one byte `svc_ops_e`, dispatch, break on `svc_EOF`

| byte | name               | meaning                                              |
|-----:|--------------------|------------------------------------------------------|
|  0   | `svc_bad`          | invalid                                              |
|  1   | `svc_nop`          | no-op                                                |
|  2   | `svc_gamestate`    | configstrings + baselines; once per connection       |
|  3   | `svc_configstring` | inside svc_gamestate only                            |
|  4   | `svc_baseline`     | inside svc_gamestate only                            |
|  5   | `svc_serverCommand`| reliable ASCII string command                        |
|  6   | `svc_download`     | file transfer (never in demos)                       |
|  7   | `svc_snapshot`     | delta-compressed playerstate + entities              |
|  8   | `svc_EOF`          | end of message payload                               |

Dispatch: `client/cl_parse.c:2090` (`CL_ParseServerMessage`).

Protocol detection: parse `\protocol\<n>` from configstring 0 (`CS_SERVERINFO`).
Protocol 73 = vanilla QL dm_73. Protocols 90/91 = newer QL.

---

## Huffman Coding

Order-0 adaptive Huffman (Sayood). State pre-seeded by calling
`Huff_addRef(byte)` exactly `msg_hData[byte]` times for each byte 0..255.

Seed table: `qcommon/msg.c:3126-3383` (`msg_hData[256]`). First entry: `250315` (byte 0).
Init routine: `qcommon/msg.c:3385-3396` (`MSG_initHuffman`).
Core reader: `qcommon/msg.c:274-409` (`MSG_ReadBits`).

**Without exact seeding, decompression desyncs on byte 1.**

Python reference implementation: `tools/quake-source/qldemo-python/huffman/huffman.c`
(same copyright header, same API: `huffman.init()`, `huffman.fill(len)`, `huffman.readbyte()`).

Negative `bits` in field tables = signed field (sign extension applied on return).
`FLOAT_INT_BITS=13, FLOAT_INT_BIAS=4096` encodes integral floats in [-4096..4095] in 13 bits.

---

## svc_gamestate Wire Format

Parser: `client/cl_parse.c:886-1068` (`CL_ParseGamestate`).

```
serverCommandSequence    LE32
loop:
    cmd : byte
    if cmd == svc_EOF: break
    if cmd == svc_configstring:
        index  : int16          (0..1023)
        string : bigString      (0..8192 zero-terminated)
    if cmd == svc_baseline:
        entityNum : bits(10)
        deltaEntity(against NULL state)
clientNum     : LE32
checksumFeed  : LE32
```

`MAX_CONFIGSTRINGS = 1024`. `MAX_GAMESTATE_CHARS = 16000`.

---

## Critical Configstring Indices

| idx     | symbol                       | contents                                                  |
|--------:|------------------------------|-----------------------------------------------------------|
|  0      | `CS_SERVERINFO`              | `\protocol\73\g_gametype\...\mapname\...`                 |
|  5      | `CS_WARMUP`                  | server time when match restarts                           |
|  13     | `CS_LEVEL_START_TIME`        | match start time (ms)                                     |
|  14     | `CS_INTERMISSION`            | `1` = intermission active                                 |
| 529..592| `CS_PLAYERS[i]`              | per-client infostring: `n=<name>\t=<team>\cn=<clan>...`  |
| **662** | `CS_ROUND_TIME`              | CA round start time (ms); `-1` = round over               |
| 663,664 | `CS_RED/BLUE_PLAYERS_LEFT`   | CA alive count                                            |
| 669,670 | `CS_TIMEOUT_BEGIN/END_TIME`  | timeout windows                                           |

Source: `game/bg_public.h:73-287`.

Protocol 91 reshuffles indices 666..715 into `CS91_*` variants. For dm_73
(protocol 73) use the table above.

---

## svc_snapshot Wire Format

Parser: `client/cl_parse.c:405-641` (`CL_ParseSnapshot`).

```
serverTime       LE32                (ms, absolute server clock)
deltaNum         byte                (0 = non-delta / full frame)
snapFlags        byte
areamaskLen      byte
areamask         byte[areamaskLen]
deltaPlayerState variable            (see playerstate section)
deltaEntities    variable            (terminated by entityNum == 1023)
```

Snapshot ring buffer: `cl.snapshots[messageNum & PACKET_MASK]`, `PACKET_BACKUP = 32`.

---

## MSG_ReadDeltaEntity Wire Format

Decoder: `qcommon/msg.c:1944-2120`.

```
entityNum   : bits(10)
removeBit   : 1           if 1 -> zeroed entity, done
deltaBit    : 1           if 0 -> *to = *from, done
lc          : byte        last changed field index
for i in [0..lc):
    changed : 1
    if changed:
        if field.bits == 0:    (float)
            nonzero : 1
            if nonzero:
                isFullFloat : 1
                if isFullFloat: value = readBits(32)
                else:           value = readBits(13) - 4096
            else: value = 0.0
        else:                  (integer)
            nonzero : 1
            if nonzero: value = readBits(field.bits)
            else:       value = 0
```

End-of-entities marker: `entityNum == 1023` (`ENTITYNUM_NONE`).

---

## dm_73 Entity Field Table

`entityStateFieldsQldm73[]` at `qcommon/msg.c:1081`. 53 fields total.
QL-specific additions vs Q3: `pos.gravity` (idx 9) and `apos.gravity` (idx 46).

| idx | field             | bits | notes                                     |
|----:|-------------------|-----:|-------------------------------------------|
|  0  | `pos.trTime`      | 32   |                                           |
|  1  | `pos.trBase[0]`   | 0    | float                                     |
|  2  | `pos.trBase[1]`   | 0    |                                           |
|  3  | `pos.trDelta[0]`  | 0    |                                           |
|  4  | `pos.trDelta[1]`  | 0    |                                           |
|  5  | `pos.trBase[2]`   | 0    |                                           |
|  9  | `pos.gravity`     | 32   | QL-specific                               |
| 10  | `event`           | 10   | high 2 bits = toggle bits; mask with ~0x300 |
| 12  | `eType`           | 8    | `entityType_t`                            |
| 14  | `eventParm`       | 8    | MOD_* for EV_OBITUARY; weapon for EV_FIRE_WEAPON |
| 18  | `eFlags`          | 19   |                                           |
| 19  | `otherEntityNum`  | 10   | victim slot for obituaries                |
| 21  | `clientNum`       | 8    | event entity's own slot                   |
| 28  | `solid`           | 24   |                                           |
| 29  | `powerups`        | 16   |                                           |
| 31  | `otherEntityNum2` | 10   | killer slot for obituaries                |
| 46  | `apos.gravity`    | 32   | QL-specific                               |

Protocol 90 adds `jumpTime`, `doubleJumped`. Protocol 91 adds `health`, `armor`, `location`.

---

## MSG_ReadDeltaPlayerstate Wire Format

Decoder: `qcommon/msg.c:2949-3124`. Protocol 73 reuses `playerStateFieldsQ3[]`
(`qcommon/msg.c:2244-2295`, 48 fields).

```
lc          : byte          last changed field index
for i in [0..lc):
    changed : 1
    if changed:
        if field.bits == 0:
            isIntFloat : 1
            if isIntFloat: value = readBits(13) - 4096
            else:          value = readBits(32)
        else:
            value = readBits(abs(field.bits))   # sign-extended if < 0

hasArrays : 1
if hasArrays:
    hasStats : 1       -> statMask : bits(16) -> stats[i] : short
    hasPersistant : 1  -> persMask : bits(16) -> persistant[i] : short
    hasAmmo : 1        -> ammoMask : bits(16) -> ammo[i] : short
    hasPowerups : 1    -> powMask  : bits(16) -> powerups[i] : long
```

Key playerstate fields: `clientNum:8`, `origin[3]:float`, `velocity[3]:float`,
`viewangles[3]:float`, `weapon:5`, `pm_type:8`, `groundEntityNum:10`,
`powerups[16]:long` (expiry times), `stats[16]:short`.

---

## Entity Events — Toggle Bits

```c
#define EV_EVENT_BIT1   0x00000100
#define EV_EVENT_BIT2   0x00000200
#define EV_EVENT_BITS   0x00000300
#define EVENT_VALID_MSEC 300
```

Source: `game/bg_public.h:782-788`. Always mask before comparing:

```c
int eventCode = es->event & ~EV_EVENT_BITS;
if (eventCode == EV_OBITUARY) { ... }
```

---

## Key EV_* Codes (dm_73 / QL era)

Source: `game/bg_public.h:790-923`. Use these values for protocol 73.

| code | name                  | fields used                                       |
|-----:|-----------------------|---------------------------------------------------|
|  10  | `EV_JUMP`             | —                                                 |
|  15  | `EV_ITEM_PICKUP`      | `eventParm` = item index                          |
|  20  | `EV_FIRE_WEAPON`      | weapon from playerstate                           |
|  39  | `EV_PLAYER_TELEPORT_IN`  | `clientNum` = who                              |
|  47  | `EV_MISSILE_HIT`      | direct hit on flesh; `otherEntityNum` = victim    |
|  48  | `EV_MISSILE_MISS`     | wall impact                                       |
|  50  | `EV_RAILTRAIL`        | rail fire                                         |
|  53  | `EV_PAIN`             | `eventParm` = health after hit                    |
| **58** | **`EV_OBITUARY`**   | **victim=otherEntityNum, killer=otherEntityNum2, mod=eventParm** |
|  63  | `EV_GIB_PLAYER`       | —                                                 |
|  89  | `EV_HEADSHOT`         | rail headshot marker                              |

For Q3 protocol (<= 71) use `EVQ3_OBITUARY` (different number).
Protocol branch: `client/cl_main.c:2078`.

---

## EV_OBITUARY Decode

```c
// From snapshot entity:
if ((es->event & ~0x300) == EV_OBITUARY) {
    int victim   = es->otherEntityNum;   // client slot 0..63
    int killer   = es->otherEntityNum2;  // 0..63, or ENTITYNUM_WORLD
    int mod      = es->eventParm;        // meansOfDeath_t
    int when_ms  = snap->serverTime;
}
```

Source: `cgame/cg_event.c:85-112`, `client/cl_main.c:2086-2088`.

Deduplication: same entity.number appearing in consecutive snapshots within
`EVENT_VALID_MSEC = 300 ms` = one obituary (not multiple). Use
`(entity.number, messageNum, firstServerTime)` combo to collapse dupes.
Source: `client/cl_main.c:2092-2167`.

---

## meansOfDeath_t (MOD_*)

Source: `game/bg_public.h:1294-1339`.

| value | name                   | weapon                   |
|------:|------------------------|--------------------------|
|  0    | `MOD_UNKNOWN`          | —                        |
|  1    | `MOD_SHOTGUN`          | shotgun                  |
|  2    | `MOD_GAUNTLET`         | gauntlet                 |
|  3    | `MOD_MACHINEGUN`       | MG                       |
|  4    | `MOD_GRENADE`          | grenade direct           |
|  5    | `MOD_GRENADE_SPLASH`   | grenade splash           |
|  6    | `MOD_ROCKET`           | rocket direct            |
|  7    | `MOD_ROCKET_SPLASH`    | rocket splash            |
|  8    | `MOD_PLASMA`           | plasma direct            |
|  9    | `MOD_PLASMA_SPLASH`    | plasma splash            |
| 10    | `MOD_RAILGUN`          | rail body                |
| 11    | `MOD_LIGHTNING`        | LG                       |
| 12    | `MOD_BFG`              | BFG direct               |
| 13    | `MOD_BFG_SPLASH`       | BFG splash               |
| 18    | `MOD_TELEFRAG`         | telefrag                 |
| 20    | `MOD_SUICIDE`          | /kill (filter out)       |
| 29    | `MOD_SWITCH_TEAMS`     | team switch (filter out) |
| 30    | `MOD_THAW`             | FreezeTag (QL only)      |
| 31    | `MOD_LIGHTNING_DISCHARGE` | LG in water (QL only) |
| 32    | `MOD_HMG`              | HMG (QL only)            |
| 33    | `MOD_RAILGUN_HEADSHOT` | rail headshot (QL only)  |

MOD_SWITCH_TEAMS (29) = synthetic kill, filter from stats.
Q3 originally stopped at MOD_GRAPPLE (28). Values 30+ confirm QL-era capture.

MOD to weapon mapping: `game/bg_misc.c:6595` (`BG_ModToWeapon`).

---

## Round Detection (CA)

Single source of truth: `cs 662 <ms>` server command.

```
roundStarts = []
on serverCommand "cs 662 <value>":
    if value > 0 and value != roundStarts[-1]:
        roundStarts.append(value)
```

Round end: server sets cs 662 to `-1`. Max 256 rounds (`MAX_DEMO_ROUND_STARTS`).
Source: `client/cl_parse.c:1947-1959`.

Game boundaries:
- Start: `cs 5` (CS_WARMUP) goes to `-1`, or `cs 13` (CS_LEVEL_START_TIME) updates
- End: first snapshot with `cs 14` (CS_INTERMISSION) == `"1"`

---

## Server Commands Worth Mining

| cmd    | format                       | use                                                 |
|--------|------------------------------|-----------------------------------------------------|
| `cs`   | `cs <idx> "<val>"`           | configstring update (rounds, scores, timeouts)      |
| `cp`   | `cp "<text>"`                | centerprint ("Red Wins Round 3", "Timeout called")  |
| `print`| `print "<text>"`             | console text (vote passed, team forfeits)           |
| `bcs0` | `bcs0 <idx> "<chunk"`        | fragmented configstring opening                     |
| `bcs1` | `bcs1 <idx> "<chunk"`        | fragmented configstring middle                      |
| `bcs2` | `bcs2 <idx> "<chunk>"`       | fragmented configstring end — reassemble as `cs`    |
| `scores` | `scores <n> [tuples...]`  | scoreboard snapshot                                 |

Fragmented configstring reassembly: `client/cl_cgame.c:704-767`.

---

## Kill-Query Syscalls (WolfcamQL cgame API)

```c
qboolean trap_GetNextVictim(int slot, int serverTime, int *victim, int *foundTime, qboolean onlyOther);
qboolean trap_GetNextKiller(int slot, int serverTime, int *killer, int *foundTime, qboolean onlyOther);
void     trap_GetRoundStartTimes(int *numRoundStarts, int *roundStarts);
int      trap_GetFirstServerTime(void);
int      trap_GetLastServerTime(void);
int      trap_GetGameStartTime(void);   // -1 if no game in demo
int      trap_GetGameEndTime(void);
void     trap_Get_Demo_Timeouts(int *numTimeouts, timeOut_t *timeOuts);
```

Source: `cgame/cg_syscalls.h:234`. Max 2048 obituaries (`MAX_DEMO_OBITS`).
**NOTE: `trap_AddAt` is `#if 0`'d out** (`cgame/cg_syscalls.c:595-600`).
Use the `at` console command instead.

Weapon type (`mod`) is NOT exposed by `trap_GetNextVictim/Killer` return values.
To get weapon: iterate `di.obit[0..obitNum)` directly via custom cgame command.

---

## Phase 2 Capture Scheduling Pattern

```cfg
// phase2_capture.cfg — generated per demo
at 1832250.0 video avi name :frag_007
at 1845250.0 stopvideo
at 1832250.0 cg_drawHUD 0
at 1845250.0 cg_drawHUD 1
```

Launch: `wolfcamql.exe +set fs_homepath <out_dir> +exec phase2_capture.cfg +demo <demo>`

Raw server time (float ms) preferred over clock time for batch scheduling.

---

## Recommended Parser Build (C++17)

Vendor from `wolfcamql-src/code/qcommon/`:
- `huffman.c` + `q_shared.h` (huffman init)
- `msg_hData[256]` + `MSG_initHuffman` from `msg.c:3126-3396`
- `MSG_ReadBits/Byte/Short/Long/BigString` from `msg.c:274-730`
- `MSG_ReadDeltaEntity`, `MSG_ReadDeltaPlayerstate`
- `entityStateFieldsQldm73[]`, `playerStateFieldsQ3[]`

Output format: one JSON line per event:
```json
{"type":"obit","t":1840250,"killer":3,"victim":7,"mod":10,"killer_name":"...","victim_name":"..."}
{"type":"round_start","t":120000}
```
