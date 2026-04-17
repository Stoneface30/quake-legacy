# .dm_73 Format — Deep Dive

**Purpose.** Comprehensive, source-cited reference for the Quake Live `.dm_73`
demo format, sufficient to write a standalone C/C++ parser that matches
WolfcamQL behaviour exactly. Every non-trivial claim is cited as `file:line` in
the local `tools/quake-source/` tree.

Companion to:
- `docs/reference/phase2-kill-query-architecture.md` (kill-query syscall API)
- `docs/reference/phase5-bugs-fixed.md` (unrelated — Comfy pipeline)
- `docs/reference/wolfcam-commands.md` (cvar/cmd inventory)

**Primary tree:** `G:/QUAKE_LEGACY/tools/quake-source/wolfcamql-src/code/`

Unless otherwise stated, line numbers below refer to files inside
`tools/quake-source/wolfcamql-src/code/` in the currently checked-out local
copy.

---

## 0. TL;DR cheat sheet

```
.dm_73 file = repeat{ seqLE32 + lenLE32 + huffmanCompressed(payload) }
              terminator: seq==-1 or len==-1

Inside each decompressed payload:
  reliableAck : LE32
  loop svc_ops (1 byte) -> dispatch { gamestate | snapshot | serverCommand | download | EOF }
  EOF closes the message

Encoding:                 Adaptive Huffman (order-0), per-byte, seeded from msg_hData[256]
Protocol values:          43..48 = Q3 era (non-huffman for 43, huffman from 46)
                          66..71 = Q3 standard                         (protocol constants: q_shared.h:29-32)
                          73, 90, 91 = Quake Live eras
Field tables (QL dm_73):  entityStateFieldsQldm73[] (msg.c:1081)
                          playerStateFieldsQ3[]   reused for dm_73 (msg.c:2990-2991)

Kill record:              entityState event == EV_OBITUARY (bg_public.h:865)
                          mask off event-toggle bits first: (event & ~EV_EVENT_BITS)
                          EV_EVENT_BITS = 0x00000300 (bg_public.h:784-786)
                          killer = otherEntityNum2
                          victim = otherEntityNum
                          mod    = eventParm    (meansOfDeath_t, bg_public.h:1294-1339)
```

---

## 1. File container — the outer frame

`.dm_73` is **not** a fixed-header format. It is an uninterrupted sequence of
server→client network messages dumped to disk as-is, each prefixed with
`(sequenceNumber:int32, length:int32)`. There is **no file magic**, no version
field, no index/TOC — you infer the protocol from the first gamestate message.

**Source of truth: `client/cl_main.c:1566` (`CL_ReadDemoMessage`).**

Read loop (simplified, from `client/cl_main.c:1759-1806`):

```c
int32_t seq;
int32_t msgLen;

// 1) sequence number (little-endian)
if (FS_Read(&seq, 4, demoReadFile) != 4) return EOF;
clc.serverMessageSequence = LittleLong(seq);

// 2) payload length (little-endian)
if (FS_Read(&msgLen, 4, demoReadFile) != 4) return EOF;
msgLen = LittleLong(msgLen);

// 3) `/stoprecord` writes (seq=-1, len=-1) as a sentinel
if (msgLen == -1) return EOF;

// 4) sanity check: msgLen must be within [0, MAX_MSGLEN]
//    MAX_MSGLEN in wolfcam = 49152 bytes (see qcommon.h)
if (msgLen < 0 || msgLen > MAX_MSGLEN) demo_error();

// 5) read the payload verbatim (still Huffman-compressed for protocol >= 46)
FS_Read(buf.data, msgLen, demoReadFile);

// 6) hand to the bitstream parser
CL_ParseServerMessage(&buf);     // cl_parse.c:2090
```

### Byte layout per message

```
offset  size  field                  notes
------  ----  ---------------------  -----------------------------------
   0      4   sequenceNumber  LE32   monotonically increasing; -1 = EOF
   4      4   messageLength   LE32   bytes of payload; -1 = EOF
   8    len   payload                Huffman-compressed bitstream
```

### Payload bitstream dispatch

Inside each (decompressed) payload, `CL_ParseServerMessage` (cl_parse.c:2090)
reads:

1. `MSG_Bitstream(msg)` — flip to Huffman-bit-reader mode.  
   (Skipped for legacy uncompressed demos with `olderUncompressedDemoProtocol < 46`.)
2. `reliableAcknowledge : LE32` (protocol ≥ 46; absent for dm3 protocol 43).
3. Loop: read one `svc_ops_e` byte; dispatch; break on `svc_EOF`.

The `svc_ops_e` enum is **load-bearing**. From `qcommon/qcommon.h:281-296`:

| byte | name               | meaning                                                |
|-----:|--------------------|--------------------------------------------------------|
| 0    | `svc_bad`          | invalid — also used as "broken demo" marker in dm3    |
| 1    | `svc_nop`          | no-op; skip                                            |
| 2    | `svc_gamestate`    | configstrings + baselines; only once per connection    |
| 3    | `svc_configstring` | only legal inside `svc_gamestate`                      |
| 4    | `svc_baseline`     | only legal inside `svc_gamestate`                      |
| 5    | `svc_serverCommand`| reliable string command (`[string]`)                   |
| 6    | `svc_download`     | `[short size][size bytes]` — file transfer            |
| 7    | `svc_snapshot`     | delta-compressed playerstate + entities                |
| 8    | `svc_EOF`          | end of this message payload                            |
| 9    | `svc_extension`    | voip extension follows (appears after `svc_EOF`)       |
| 10   | `svc_voip`         | opus VoIP payload (reserved; protocol 70/71)           |

Dispatch switch verbatim: `cl_parse.c:2183-2222`.

---

## 2. Huffman coding (the bit layer)

Quake uses **order-0 adaptive Huffman** (Sayood). Compressor and decompressor
state are mirror images; both are **pre-seeded** by replaying every byte in a
fixed 256-entry frequency table so the first symbol already has a useful
codebook. Without this seeding, the first few bytes of a demo are unreadable.

### The frequency seed table

File: `qcommon/msg.c:3126-3383`. This is the sacred 256-entry int array
`msg_hData[]` — if your decoder does not initialise with these exact counts you
will desynchronise on byte 1. First 16 entries:

```c
int msg_hData[256] = {
  250315,  //   0  — by far the most common byte (zero-padding / no-change flags)
   41193,  //   1
    6292,  //   2
    7106,  //   3
    3730,  //   4
    3750,  //   5
    6110,  //   6
   23283,  //   7
   33317,  //   8
    6950,  //   9
    7838,  //  10
    9714,  //  11
    9257,  //  12
   17259,  //  13
    3949,  //  14
    1778,  //  15
    ...
   11457,  // 254
   13504,  // 255
};
```

### The init routine (this is the entire seeding logic)

From `qcommon/msg.c:3385-3396`:

```c
void MSG_initHuffman(void) {
    int i, j;
    msgInit = qtrue;
    Huff_Init(&msgHuff);
    for (i = 0; i < 256; i++) {
        for (j = 0; j < msg_hData[i]; j++) {
            Huff_addRef(&msgHuff.compressor,   (byte)i);   // Do update
            Huff_addRef(&msgHuff.decompressor, (byte)i);   // Do update
        }
    }
}
```

So the decoder is initialised by **calling `Huff_addRef(byte)` exactly
`msg_hData[byte]` times, for each byte 0..255, in order**. The total loop count
is ≈1.3M calls (the sum of the table). `Huff_addRef` both adds the byte to the
tree and re-balances ranks — this is adaptive huffman, not static.

### Reusing the reference implementation — `qldemo-python`

The in-tree `tools/quake-source/qldemo-python/huffman/huffman.c` is a
byte-for-byte lift of `qcommon/huffman.c` (same copyright header, same
`Huff_putBit`/`Huff_getBit`/`Huff_addRef` API — see huffman.c:1-80 there). It
ships a compiled `huffman.cp311-win_amd64.pyd` that exposes:

```python
huffman.init()              # calls MSG_initHuffman equivalent
huffman.open(filename)      # opens the demo; positions at byte 0
huffman.readrawlong()       # plain 4-byte LE32 (used for seq/len headers)
huffman.readlong()          # huffman-coded 32-bit int inside payloads
huffman.readbyte()          # huffman-coded byte
huffman.readshort()         # huffman-coded 16-bit
huffman.readbigstring()     # BIG_INFO_STRING (0..8192) zero-terminated
huffman.fill(length)        # load `length` bytes of compressed payload into bitbuf
```

Usage exemplar — `tools/quake-source/qldemo-python/qldemo/demo.py:39-59`:

```python
while True:
    seq    = huffman.readrawlong()
    length = huffman.readrawlong()
    if seq == -1 or length == -1:
        break
    huffman.fill(length)
    ack = huffman.readlong()
    cmd = huffman.readbyte()
    if   cmd == SVC_GAMESTATE:      r = self.parse_gamestate()
    elif cmd == SVC_SERVERCOMMAND:  r = self.parse_servercommand()
    elif cmd == SVC_SNAPSHOT:       r = self.parse_snapshot()
```

**For our own C++ parser**, the fastest path is: copy `qcommon/huffman.c` +
`qcommon/msg.c` into our tree, drop all writer paths, keep `MSG_ReadBits`,
`MSG_ReadByte`, `MSG_ReadShort`, `MSG_ReadLong`, `MSG_ReadBigString`,
`MSG_ReadDeltaPlayerstate`, `MSG_ReadDeltaEntity`, and `MSG_initHuffman`. That
is ~1500 LOC vs UberDemoTools' 60 kLOC and gives us bit-exact fidelity.

### `MSG_ReadBits` — the atom

From `qcommon/msg.c:274-409`. Two branches:

- **OOB (out-of-band) mode**, set via `MSG_InitOOB`: plain little-endian for
  protocols > 48, else fallback to UberDemoTools' 64-bit window
  (msg.c:341-367). Used for the legacy uncompressed dm_48 path.
- **Normal mode** (this is what dm_73 uses): per-bit calls to `Huff_getBit` and
  `Huff_offsetReceive` to pull one decoded byte at a time, accumulating into
  `value` 8 bits at a time (msg.c:371-398).

Negative `bits` means "signed" — `MSG_ReadBits` applies sign extension on return
(msg.c:402-406). This matters for fields like `weaponTime : -16` and
`viewheight : -8` in the playerstate table.

---

## 3. `svc_gamestate` — the configstring + baseline payload

Parser: `CL_ParseGamestate`, `cl_parse.c:886-1068`.

### Wire format (inside payload, after the `svc_gamestate` byte)

```
serverCommandSequence     LE32 (huffman bits)
loop:
    cmd : byte
    if cmd == svc_EOF:
        break
    if cmd == svc_configstring:
        index  : int16            (0..MAX_CONFIGSTRINGS-1, so 0..1023)
        string : bigString        (zero-terminated, 0..BIG_INFO_STRING=8192)
    if cmd == svc_baseline:
        entityNum  : bits(GENTITYNUM_BITS=10)    (q_shared.h:1182)
        deltaEntity(against NULL state)          (see §5)
    else: error
clientNum       : LE32     (our slot, 0..63)
checksumFeed    : LE32     (seed for file checksums; irrelevant for parsing)
```

`MAX_CONFIGSTRINGS = 1024` (`q_shared.h:1198`).  
`MAX_GAMESTATE_CHARS = 16000` — the concatenated string-data pool for all
configstrings. Fragmented configstrings (>`MAX_STRING_CHARS - 24` = 1000 bytes)
are delivered mid-game via `bcs0`/`bcs1`/`bcs2` server commands instead; see §9.

### Detecting the protocol

Configstring `0` is `CS_SERVERINFO` (q_shared.h:1202). Parse the
info-string-encoded key `\protocol\<n>` from it — if `n == 73` this is a
vanilla QL dm_73, if `n == 90` or `91` newer QL. Wolfcam's own detection
logic is at `cl_parse.c:954-1015` and is the authoritative fallback ladder
(if the serverinfo lacks `\protocol`, it falls back to file extension).

### Critical configstring indices

`q_shared.h:1202-1203`:

| idx | symbol            | contents                                                |
|----:|-------------------|---------------------------------------------------------|
|   0 | `CS_SERVERINFO`   | info string — `\g_gametype\\mapname\\protocol\\sv_maxclients...\\sv_hostname\\...` |
|   1 | `CS_SYSTEMINFO`   | info string — `\sv_serverid\\sv_paks\\sv_pakNames\\fs_game...` |

`game/bg_public.h:73-287`:

| idx       | symbol                         | notes                                    |
|----------:|--------------------------------|------------------------------------------|
|   2       | `CS_MUSIC`                     | ambient music path                       |
|   3       | `CS_MESSAGE`                   | worldspawn message                       |
|   4       | `CS_MOTD`                      | server MOTD                              |
|   5       | `CS_WARMUP`                    | server time when match (re)starts        |
|   6, 7    | `CS_SCORES1`, `CS_SCORES2`     | team scores (red, blue)                  |
|   8, 9    | `CS_VOTE_TIME`, `CS_VOTE_STRING` |                                        |
|  12       | `CS_GAME_VERSION`              |                                          |
|  13       | `CS_LEVEL_START_TIME`          | **ms**: match start time                 |
|  14       | `CS_INTERMISSION`              | `1` = intermission live                  |
|  15       | `CS_ITEMS`                     | bitstring of items present in the map    |
|  17..272  | `CS_MODELS[+i]`                | 256 model slots (17 unused, first@18)    |
| 274..528  | `CS_SOUNDS[+i]`                | sound slots                              |
| 529..592  | `CS_PLAYERS[+i]`               | **one slot per client (0..63)**. info string includes `n=<name>`, `t=<team>`, `cn=<clan>`, `hc=<handicap>`, `skill=`, `xcn=`, etc. This is how we recover nicknames. |
| 593..656  | `CS_LOCATIONS[+i]`             | location names (for team-chat location filter) |
| 657       | `CS_PARTICLES`                 | (first particle of 64)                   |
| 658       | `CS_FLAGSTATUS`                | CTF flag state                           |
| 659, 660  | `CS_FIRSTPLACE`, `CS_SECONDPLACE` |                                       |
| **661**   | `CS_ROUND_STATUS`              | FT / CA round state                      |
| **662**   | `CS_ROUND_TIME`                | **CA round start time (ms); -1 = round over** — load-bearing for round detection, see §10 |
| 663, 664  | `CS_RED_PLAYERS_LEFT`, `CS_BLUE_PLAYERS_LEFT` | CA "alive" count            |
| 665       | `CS_SHADERSTATE`               | runtime shader switches                  |
| 669, 670  | `CS_TIMEOUT_BEGIN_TIME`, `CS_TIMEOUT_END_TIME` | ms since level start     |
| 671, 672  | `CS_RED_TEAM_TIMEOUTS_LEFT`, `CS_BLUE_TEAM_TIMEOUTS_LEFT` |             |
| 679, 680  | `CS_MAP_CREATOR`, `CS_ORIGINAL_MAP_CREATOR` |                             |
| 682       | `CS_PMOVE_SETTINGS`            | info: air-accel, jump velocities, etc    |
| 683       | `CS_WEAPON_SETTINGS`           | per-weapon reload times                  |
| 684       | `CS_CUSTOM_PLAYER_MODELS`      |                                          |
| 685..688  | scoreboard scores/clientnums   | 1st/2nd place                            |
| 690..692  | award configstrings            | most_damage / most_accurate / best_item  |
| 693..696  | team clan names + tags         |                                          |
| 699..703  | MVP + domination points        |                                          |
| 705       | `CS_ROUND_WINNERS`             |                                          |
| 706..713  | custom settings, map vote, ...  |                                         |

**CS_PLAYERS is the nickname recovery dictionary.** Each slot is a
`\k\v\k\v` infostring; parse `n` for name, `t` for team (QL teams:
0=FREE, 1=RED, 2=BLUE, 3=SPECTATOR — `team_t` in bg_public.h). For the
player-dictionary design see §13.

**Protocol 91 re-shuffles 666..715** into `CS91_*` (bg_public.h:237-287). Key
differences: CS91_MATCH_GUID (712), CS91_STEAM_ID (714),
CS91_STEAM_WORKSHOP_IDS (715), CS91_PAUSE_START_TIME/END_TIME (669/670) — if
the demo is pro-91 the round-time machinery moves around.

---

## 4. `svc_snapshot` — the delta frame

Parser: `CL_ParseSnapshot`, `cl_parse.c:405-641`.

### Wire format

```
serverTime           LE32                  (ms; absolute server clock)
deltaNum             byte                  (0 = non-delta; else N=messageNum-delta)
snapFlags            byte                  (see SNAPFLAG_* in q_shared.h)
areamaskLen          byte
areamask             byte[areamaskLen]     (portal visibility)
deltaPlayerState     variable              (see §6)
deltaEntities        variable              (see §5; terminated by entityNum==MAX_GENTITIES-1)
```

### Key derived fields

- `newSnap.messageNum = serverMessageSequence` (the outer `seq` from §1).
- `deltaNum == 0` means "full frame, delta from NULL" — bootstrapping or
  rewind. Also sets `clc.demowaiting = qfalse` so recording can start here.
- Invalid-frame handling: if the delta source `old->messageNum != deltaNum`
  the snapshot is discarded (cl_parse.c:481-501).
- After parse, the snap is stored in a ring buffer `cl.snapshots[0][messageNum
  & PACKET_MASK]` (cl_parse.c:630). `PACKET_BACKUP = 32`.

### How `MSG_ReadDeltaPlayerstate` terminates

There is **no end-of-entities marker for the player state** — the number of
fields is communicated as `lc : byte` (the "last-changed" field index) at
`msg.c:2994`. Fields `[0..lc)` may carry changes; fields `[lc..N)` are copied
from `from` unchanged (`msg.c:3055-3060`).

### Packet entities terminator

After the playerstate, `CL_ParsePacketEntities` loops reading entity numbers
until it sees `entityNum == MAX_GENTITIES-1 == 1023` (which is also
`ENTITYNUM_NONE`, q_shared.h:1188). That value is encoded as "all 10 bits set"
and signals end-of-entities for this snapshot.

---

## 5. `MSG_ReadDeltaEntity` — field tables & decode loop

Decoder: `msg.c:1944-2120`. The wire format is:

```
entityNum   : bits(GENTITYNUM_BITS=10)
removeBit   : 1                 // if 1 → zeroed-out entity, done
deltaBit    : 1                 // if 0 → *to = *from, done
lc          : byte              // 0..numFields; last field index that might change
for i in [0..lc):
    changed : 1
    if changed:
        if field.bits == 0:             // float
            nonzero : 1
            if nonzero:
                isFullFloat : 1
                if isFullFloat: value = readBits(32)      // raw IEEE754 bits
                else:           value = readBits(FLOAT_INT_BITS=13) - FLOAT_INT_BIAS(=4096)
            else: value = 0.0f
        else:                          // integer
            nonzero : 1
            if nonzero: value = readBits(field.bits)
            else:       value = 0
    else:
        value = from[field]
```

The `FLOAT_INT_BITS=13, FLOAT_INT_BIAS=4096` pair encodes signed integral
floats in [-4096, 4095] in only 13 bits — the common case for
positions/velocities that happen to be whole numbers (msg.c:2049-2052).

### dm_73 entity field table

`entityStateFieldsQldm73[]` at `msg.c:1081-1142`. **45 fields in this
order** (field index = delta bit offset):

| idx | field                 | bits | notes |
|----:|-----------------------|-----:|-------|
|  0  | `pos.trTime`          | 32   |       |
|  1  | `pos.trBase[0]`       | 0 (float) |  |
|  2  | `pos.trBase[1]`       | 0    |       |
|  3  | `pos.trDelta[0]`      | 0    |       |
|  4  | `pos.trDelta[1]`      | 0    |       |
|  5  | `pos.trBase[2]`       | 0    |       |
|  6  | `apos.trBase[1]`      | 0    | (yaw) |
|  7  | `pos.trDelta[2]`      | 0    |       |
|  8  | `apos.trBase[0]`      | 0    | (pitch) |
|  9  | `pos.gravity`         | 32   | **QL-specific addition** (not in Q3 table) |
| 10  | `event`               | 10   | **1024 event codes; high 2 bits are toggle bits** |
| 11  | `angles2[1]`          | 0    |       |
| 12  | `eType`               | 8    | `entityType_t` |
| 13  | `torsoAnim`           | 8    |       |
| 14  | `eventParm`           | 8    | **MOD_* for EV_OBITUARY, weapon for EV_FIRE_WEAPON, etc** |
| 15  | `legsAnim`            | 8    |       |
| 16  | `groundEntityNum`     | 10   |       |
| 17  | `pos.trType`          | 8    |       |
| 18  | `eFlags`              | 19   |       |
| 19  | `otherEntityNum`      | 10   | **victim slot for obituaries** |
| 20  | `weapon`              | 8    |       |
| 21  | `clientNum`           | 8    | event entity's own slot (or attached player) |
| 22  | `angles[1]`           | 0    |       |
| 23  | `pos.trDuration`      | 32   |       |
| 24  | `apos.trType`         | 8    |       |
| 25  | `origin[0]`           | 0    |       |
| 26  | `origin[1]`           | 0    |       |
| 27  | `origin[2]`           | 0    |       |
| 28  | `solid`               | 24   |       |
| 29  | `powerups`            | 16   | (MAX_POWERUPS=16 bits) |
| 30  | `modelindex`          | 8    |       |
| 31  | `otherEntityNum2`     | 10   | **killer slot for obituaries** |
| 32  | `loopSound`           | 8    |       |
| 33  | `generic1`            | 8    |       |
| 34  | `origin2[2]`          | 0    |       |
| 35  | `origin2[0]`          | 0    |       |
| 36  | `origin2[1]`          | 0    |       |
| 37  | `modelindex2`         | 8    |       |
| 38  | `angles[0]`           | 0    |       |
| 39  | `time`                | 32   |       |
| 40  | `apos.trTime`         | 32   |       |
| 41  | `apos.trDuration`     | 32   |       |
| 42  | `apos.trBase[2]`      | 0    |       |
| 43  | `apos.trDelta[0]`     | 0    |       |
| 44  | `apos.trDelta[1]`     | 0    |       |
| 45  | `apos.trDelta[2]`     | 0    |       |
| 46  | `apos.gravity`        | 32   | **QL-specific** |
| 47  | `time2`               | 32   |       |
| 48  | `angles[2]`           | 0    |       |
| 49  | `angles2[0]`          | 0    |       |
| 50  | `angles2[2]`          | 0    |       |
| 51  | `constantLight`       | 32   |       |
| 52  | `frame`               | 16   |       |

(53 fields total. The comment `NETF(pos.gravity)` at msg.c:1093 is what
distinguishes dm_73 from Q3's 51-field table at msg.c:1144. The Q3 table
omits `pos.gravity` and `apos.gravity`.)

**Protocol 90** (`entityStateFieldsQldm90`, msg.c:1015-1079) adds `jumpTime`,
`doubleJumped`, and reorders a few fields. **Protocol 91**
(`entityStateFieldsQldm91`, msg.c:948-1013) additionally adds `health`,
`armor`, `location` for player-entities — only visible if you're spectating.

---

## 6. `MSG_ReadDeltaPlayerstate` — fields & stat-bitmasks

Decoder: `msg.c:2949-3124`.

### Wire format

```
lc          : byte                  // last-changed field index
for i in [0..lc):
    changed : 1
    if changed:
        if field.bits == 0:         // float (same encoding as entity, but with
            isIntFloat : 1          //  NO zero-fast-path shortcut; always have a value)
            if isIntFloat: value = readBits(13) - 4096
            else:          value = readBits(32)
        else:
            value = readBits(abs(field.bits))   // sign-extended if field.bits < 0
// fields [lc..N) implicitly copied from `from`

// Statarray block:
hasArrays   : 1
if hasArrays:
    hasStats    : 1
    if hasStats:
        statMask : bits(MAX_STATS=16)
        for i in 0..16: if statMask & (1<<i): stats[i]      = readShort()
    hasPersistant : 1
    if hasPersistant:
        persMask : bits(MAX_PERSISTANT=16)
        for i in 0..16: if persMask & (1<<i): persistant[i] = readShort()
    hasAmmo     : 1
    if hasAmmo:
        ammoMask : bits(MAX_WEAPONS=16)
        for i in 0..16: if ammoMask & (1<<i): ammo[i]        = readShort()
    hasPowerups : 1
    if hasPowerups:
        powMask  : bits(MAX_POWERUPS=16)
        for i in 0..16: if powMask  & (1<<i): powerups[i]    = readLong()  // level.time out
```

The four array masks are the "statBits / persBits / ammoBits / powBits"
pattern. Verbatim from `msg.c:3064-3107`.

### dm_73 playerstate field table

Protocol 73 **reuses the Q3 playerstate table** (msg.c:2990-2991):
`playerStateFieldsQ3`, msg.c:2244-2295. 48 fields. Key entries:

| field                   | bits | notes |
|-------------------------|-----:|-------|
| `commandTime`           | 32   | last executed usercmd server time |
| `origin[0..2]`          | 0    | position |
| `velocity[0..2]`        | 0    |       |
| `viewangles[0..2]`      | 0    | yaw, pitch, roll |
| `weaponTime`            | -16  | signed |
| `bobCycle`              | 8    |       |
| `pm_time`               | -16  |       |
| `pm_flags`              | 16   | (`PMF_*`) |
| `pm_type`               | 8    | `pmove_t` (spectator vs alive vs intermission) |
| `eventSequence`         | 16   | ring-index for `events[0..1]` |
| `events[0..1]`          | 8    | two queued events for next snapshot |
| `eventParms[0..1]`      | 8    |       |
| `externalEvent`         | 10   |       |
| `externalEventParm`     | 8    |       |
| `movementDir`           | 4    | 0..7 (octant) |
| `groundEntityNum`       | 10   |       |
| `weaponstate`           | 4    |       |
| `eFlags`                | 16   |       |
| `gravity`               | 16   |       |
| `speed`                 | 16   |       |
| `delta_angles[0..2]`    | 16   |       |
| `viewheight`            | -8   | signed |
| `damageEvent/Yaw/Pitch/Count` | 8 | |
| `generic1`              | 8    |       |
| `torsoTimer`, `legsTimer` | 12, 8 | |
| `torsoAnim`, `legsAnim` | 8    |       |
| `clientNum`             | 8    | **the demo-recorder's own slot** |
| `weapon`                | 5    |       |
| `grapplePoint[0..2]`    | 0    |       |
| `jumppad_ent`           | 10   |       |
| `loopSound`             | 16   |       |

Protocol 90 adds `jumpTime : 32` and `doubleJumped : 1` at the end (see
`playerStateFieldsQldm90`, msg.c:2190-2242). Protocol 91 further extends with
`crouchTime`, `crouchSlideTime`, `location`, `fov`, `forwardmove`, `rightmove`,
`upmove`, `weaponPrimary` (see the struct at `q_shared.h:1304-1316` and table
at msg.c:2123-2188).

### `stats[]` indices (STAT_*)

From `bg_public.h` (grep `STAT_` around lines 1150-1200). Most relevant for
highlight scoring: `STAT_HEALTH`, `STAT_ARMOR`, `STAT_WEAPONS` (bitmask of
owned weapons), `STAT_HOLDABLE_ITEM`, `STAT_CLIENTS_READY`.

### `persistant[]` indices (PERS_*)

`PERS_SCORE`, `PERS_HITS`, `PERS_RANK`, `PERS_TEAM`, `PERS_SPAWN_COUNT`,
`PERS_PLAYEREVENTS`, `PERS_ATTACKER`, `PERS_ATTACKEE_ARMOR`, `PERS_KILLED`.
`PERS_KILLED` ticks every time this client dies — useful as a correlation
check against `EV_OBITUARY`.

---

## 7. Entity events — the `event` field and the toggle bits

The `event` field in `entityState_t` is a 10-bit value (msg.c:1095, field 10
of dm_73), of which **the high 2 bits are sequence-toggle bits** to let the
client notice a repeated event (e.g. two shotgun blasts in consecutive
frames). From `bg_public.h:782-788`:

```c
// if the track changes, C side event bits go along with it.
// These can be masked off with ~EV_EVENT_BITS.
#define EV_EVENT_BIT1   0x00000100
#define EV_EVENT_BIT2   0x00000200
#define EV_EVENT_BITS   (EV_EVENT_BIT1|EV_EVENT_BIT2)    // = 0x300

#define EVENT_VALID_MSEC 300
```

So to compare an event code against the `entity_event_t` enum, always mask:

```c
int eventCode = es->event & ~EV_EVENT_BITS;
if (eventCode == EV_OBITUARY) { ... }
```

### `entity_event_t` — the QL-era enum

From `bg_public.h:790-923`. **Indices are gospel** — the server hard-codes
these numbers. The full relevant subset:

| code | name                       | fields used                                     |
|-----:|----------------------------|-------------------------------------------------|
|   0  | `EV_NONE`                  | —                                               |
|   1  | `EV_FOOTSTEP`              | —                                               |
|   2  | `EV_FOOTSTEP_METAL`        | —                                               |
|   3  | `EV_FOOTSPLASH`            | —                                               |
|   6  | `EV_FALL_SHORT`            | —                                               |
|   7  | `EV_FALL_MEDIUM`           | fall damage tier — useful for "dangerous landing" |
|   8  | `EV_FALL_FAR`              | —                                               |
|   9  | `EV_JUMP_PAD`              | `eventParm` = pad entity                        |
|  10  | `EV_JUMP`                  | —                                               |
|  11  | `EV_WATER_TOUCH`           | —                                               |
|  12  | `EV_WATER_LEAVE`           | —                                               |
|  15  | `EV_ITEM_PICKUP`           | `eventParm` = item index (`bg_itemlist` slot)   |
|  16  | `EV_GLOBAL_ITEM_PICKUP`    | megahealth, powerups — broadcast to all         |
|  17  | `EV_NOAMMO`                | `eventParm` = weapon that ran out               |
|  18  | `EV_CHANGE_WEAPON`         | —                                               |
|  19  | `EV_DROP_WEAPON`           | —                                               |
|  20  | `EV_FIRE_WEAPON`           | `eventParm` implicit via `playerState.weapon`   |
|  22  | `EV_USE_ITEM1`             | medkit                                          |
|  23..36 | `EV_USE_ITEM2..EV_USE_ITEM15` | holdable items (powerups mostly)           |
|  37  | `EV_ITEM_RESPAWN`          | —                                               |
|  39  | `EV_PLAYER_TELEPORT_IN`    | `clientNum` = who teleported                    |
|  40  | `EV_PLAYER_TELEPORT_OUT`   | `clientNum` = who teleported                    |
|  41  | `EV_GRENADE_BOUNCE`        | —                                               |
|  42  | `EV_GENERAL_SOUND`         | `eventParm` = sound index                       |
|  43  | `EV_GLOBAL_SOUND`          | `eventParm` = sound index; broadcast            |
|  45  | `EV_BULLET_HIT_FLESH`      | `eventParm` = victim client num                 |
|  46  | `EV_BULLET_HIT_WALL`       | —                                               |
|  47  | `EV_MISSILE_HIT`           | **rocket/grenade/plasma direct hit on flesh**. `otherEntityNum` = victim |
|  48  | `EV_MISSILE_MISS`          | **missile impact on wall** — use for follow-cam trigger when pov actor is not attacker |
|  49  | `EV_MISSILE_MISS_METAL`    | metal surface variant                           |
|  50  | `EV_RAILTRAIL`             | `eventParm` = weapon (rail)                     |
|  51  | `EV_SHOTGUN`               | pellet pattern                                  |
|  53  | `EV_PAIN`                  | `eventParm` = health 0..100 after hit           |
|  54..56 | `EV_DEATH1..3`          | —                                               |
|  57  | `EV_DROWN`                 | —                                               |
| **58** | **`EV_OBITUARY`**        | **see §8**                                      |
|  60  | `EV_POWERUP_BATTLESUIT`    | —                                               |
|  61  | `EV_POWERUP_REGEN`         | —                                               |
|  62  | `EV_POWERUP_ARMOR_REGEN`   | —                                               |
|  63  | `EV_GIB_PLAYER`            | gib explosion                                   |
|  64  | `EV_SCOREPLUM`             | score floats                                    |
|  65  | `EV_PROXIMITY_MINE_STICK`  | —                                               |
|  66  | `EV_PROXIMITY_MINE_TRIGGER`| —                                               |
|  67  | `EV_KAMIKAZE`              | —                                               |
|  70  | `EV_INVUL_IMPACT`          | battlesuit absorb                               |
|  72  | `EV_LIGHTNINGBOLT`         | bounce off battlesuit                           |
|  74  | `EV_TAUNT`                 | —                                               |
|  81  | `EV_FOOTSTEP_SNOW`         | —                                               |
|  82  | `EV_FOOTSTEP_WOOD`         | —                                               |
|  83  | `EV_ITEM_PICKUP_SPEC`      | spec-visible variant of pickup                  |
|  84  | `EV_OVERTIME`              | —                                               |
|  85  | `EV_GAMEOVER`              | —                                               |
|  87  | `EV_THAW_PLAYER`           | FreezeTag                                       |
|  88  | `EV_THAW_TICK`             | FreezeTag                                       |
|  89  | `EV_HEADSHOT`              | marker for rail headshot (mod 33)               |
|  90  | `EV_POI`                   | point of interest                               |
|  93..95 | `EV_RACE_START/CHECKPOINT/END` | racemode                                 |
|  96  | `EV_DAMAGEPLUM`            | damage numbers                                  |
|  97  | `EV_AWARD`                 | award unlock                                    |
|  98  | `EV_INFECTED`              | infected gamemode                               |

**Q3 has a different numbering** — see `EVQ3_*` enum starting at
bg_public.h:926. Wolfcam's obituary-mining code handles the fork at
`cl_main.c:2078`:

```c
if (((di.protocol == PROTOCOL_QL  ||  di.protocol == 73  ||  di.protocol == 90)
         &&  event == EV_OBITUARY)
    ||  ((di.protocol <= 71  &&  di.protocol >= 48)  &&  event == EVQ3_OBITUARY)
    ||  (di.protocol < 48  &&  event == EVQ3DM3_OBITUARY)) { ... }
```

So for dm_73: **always use `EV_OBITUARY = 58`**. For Q3 demos use the Q3
enum. Do not hardcode 58 for mixed-protocol code.

---

## 8. Decoding `EV_OBITUARY`

Verbatim from `cgame/cg_event.c:85-112`:

```c
static void CG_Obituary( const entityState_t *ent ) {
    int mod;
    int target, attacker;
    ...
    target   = ent->otherEntityNum;      // victim slot
    attacker = ent->otherEntityNum2;     // killer slot
    mod      = ent->eventParm;           // means-of-death
    ...
}
```

And the client-side obit ingestion from snapshots (`cl_main.c:2086-2088`):

```c
target   = es->otherEntityNum;
attacker = es->otherEntityNum2;
mod      = es->eventParm;
```

So decoding is trivial **once you've snapshot-streamed the entities**:

```c
if ((es->event & ~0x300) == EV_OBITUARY) {
    int victim   = es->otherEntityNum;     // 0..63, or MAX_CLIENTS for world
    int killer   = es->otherEntityNum2;    // 0..63, or -1 if world/env kill
    int mod      = es->eventParm;          // meansOfDeath_t
    int when_ms  = snap->serverTime;       // the snapshot's server time
}
```

### Deduplication

Because events live in `entity.event` and entities replay across snapshots,
a single obituary appears in **multiple consecutive snapshots** until
`EVENT_VALID_MSEC = 300 ms` (bg_public.h:788). Wolfcam uses the combination
`(entity.number, messageNum, firstServerTime)` to collapse dupes — see the
ingestion loop `cl_main.c:2092-2167`:

- Same `number` in same `messageNum` → ignored (dup in same snap).
- Same `number`, `messageNum` adjacent, or within 300 ms of `firstServerTime`
  → update `lastServerTime`/`lastMessageNum`, do not re-append.
- Else: new obit record.

Our parser must reproduce this dedup or it will double-count.

### `meansOfDeath_t` (MOD_*)

`bg_public.h:1294-1339`:

| value | name                   | weapon                       | Q3 vs QL? |
|------:|------------------------|------------------------------|-----------|
|   0   | `MOD_UNKNOWN`          | —                            | both      |
|   1   | `MOD_SHOTGUN`          | shotgun                      | both      |
|   2   | `MOD_GAUNTLET`         | gauntlet (humiliation)       | both      |
|   3   | `MOD_MACHINEGUN`       | MG                           | both      |
|   4   | `MOD_GRENADE`          | grenade direct               | both      |
|   5   | `MOD_GRENADE_SPLASH`   | grenade splash               | both      |
|   6   | `MOD_ROCKET`           | rocket direct                | both      |
|   7   | `MOD_ROCKET_SPLASH`    | rocket splash                | both      |
|   8   | `MOD_PLASMA`           | plasma direct                | both      |
|   9   | `MOD_PLASMA_SPLASH`    | plasma splash                | both      |
|  10   | `MOD_RAILGUN`          | railgun body                 | both      |
|  11   | `MOD_LIGHTNING`        | LG                           | both      |
|  12   | `MOD_BFG`              | BFG direct                   | both      |
|  13   | `MOD_BFG_SPLASH`       | BFG splash                   | both      |
|  14   | `MOD_WATER`            | drown                        | both      |
|  15   | `MOD_SLIME`            | slime                        | both      |
|  16   | `MOD_LAVA`             | lava                         | both      |
|  17   | `MOD_CRUSH`            | door/elevator crush          | both      |
|  18   | `MOD_TELEFRAG`         | telefrag                     | both      |
|  19   | `MOD_FALLING`          | fall damage                  | both      |
|  20   | `MOD_SUICIDE`          | `/kill`                      | both      |
|  21   | `MOD_TARGET_LASER`     | laser trap                   | both      |
|  22   | `MOD_TRIGGER_HURT`     | trigger_hurt                 | both      |
|  23   | `MOD_NAIL`             | nailgun (TA/OSP)             | mission pack |
|  24   | `MOD_CHAINGUN`         | chaingun (TA)                | mission pack |
|  25   | `MOD_PROXIMITY_MINE`   | prox                         | mission pack |
|  26   | `MOD_KAMIKAZE`         | kamikaze                     | mission pack |
|  27   | `MOD_JUICED`           | juiced                       | mission pack |
|  28   | `MOD_GRAPPLE`          | grapple                      | both (rarely used) |
|  29   | `MOD_SWITCH_TEAMS`     | team switch (not a real kill)| QL        |
|  30   | `MOD_THAW`             | FreezeTag thaw (credit only) | **QL only**   |
|  31   | `MOD_LIGHTNING_DISCHARGE` | LG discharge in water     | **QL only**   |
|  32   | `MOD_HMG`              | heavy machinegun             | **QL only** (late-era) |
|  33   | `MOD_RAILGUN_HEADSHOT` | rail headshot                | **QL only**   |

**Q3 originally stopped at MOD_GRAPPLE (28).** If a dm_73 demo carries mod
30/31/33, it is a QL-era capture. `MOD_SWITCH_TEAMS` (29) means "this obit is
synthetic — player changed teams", and should be filtered out of kill stats.

### Mapping MOD → weapon for highlight scoring

`BG_ModToWeapon` exists in `bg_misc.c:6595` — use that table rather than
rolling our own. Summary:

```
rocket      <- MOD_ROCKET / MOD_ROCKET_SPLASH
grenade     <- MOD_GRENADE / MOD_GRENADE_SPLASH
plasma      <- MOD_PLASMA / MOD_PLASMA_SPLASH
rail        <- MOD_RAILGUN / MOD_RAILGUN_HEADSHOT
lg          <- MOD_LIGHTNING / MOD_LIGHTNING_DISCHARGE
shotgun     <- MOD_SHOTGUN
mg          <- MOD_MACHINEGUN / MOD_HMG
gauntlet    <- MOD_GAUNTLET
bfg         <- MOD_BFG / MOD_BFG_SPLASH
env/suicide <- rest
```

---

## 9. Server commands worth mining

`svc_serverCommand` payloads are ASCII command strings. They carry data that
does **not** fit in the snapshot format — scoreboards, stat dumps, chat,
center prints, and fragmented configstrings. Parser (cgame side):
`cgame/cg_servercmds.c` dispatch starts around line 5640.

### Core commands (cgame/cg_servercmds.c)

| cmd        | line   | format                                      | mine for                                     |
|------------|-------:|---------------------------------------------|----------------------------------------------|
| `cs`       | 5664   | `cs <index> "<value>"`                      | configstring updates mid-game. **Round time (662), score (6/7), timeout (669/670) all arrive as `cs`.** |
| `cp`       | 5650   | `cp "<text>"`                               | centerprint — "Red Wins Round 3", "Timeout called" |
| `print`    | 5669   | `print "<text>"`                            | generic console prints; includes "vote passed", "Team X Forfeits" |
| `chat`     | 5708   | `chat "<name^7: text>"` or `chat <cn> "..."` for q3plus | player chat |
| `tchat`    | 5746   | `tchat "<text>"`                            | team chat (includes `(location)` filter)     |
| `scores`   | 5791   | `scores <numScores> [score tuples...]`      | scoreboard snapshot                          |
| `tinfo`    | 5803   | `tinfo <...>`                               | team mini-info (HUD team overlay)            |
| `mstats`   | 5844   | `mstats <...>`                              | per-match player stats dump (per-player, one per line) |
| `xstats2`  | 5875   | `xstats2 <clientNum> <weapon stats...>`     | end-of-match stats (CPMA)                    |
| `xstats2a` | 5881   | `xstats2a <clientNum> <weapon stats...>`    | variant                                      |

### Fragmented configstrings: `bcs0` / `bcs1` / `bcs2`

Emitted by the server when a configstring exceeds ~1000 bytes (common for
CS_PLAYERS slots with long info, or `CS_CUSTOM_PLAYER_MODELS`).
Server emitter: `server/sv_init.c:34-71` — **`SV_SendConfigstring`**:

```
bcs0 <index> "<first chunk>"     // opening (no closing quote)
bcs1 <index> "<middle chunk>"    // middle (neither)
bcs2 <index> "<last chunk>"      // closing (adds closing quote)
```

Client re-assembly: `client/cl_cgame.c:704-767`:

```c
static char bigConfigString[BIG_INFO_STRING];   // = 8192

if (!strcmp(cmd, "bcs0")) {
    Com_sprintf(bigConfigString, BIG_INFO_STRING,
                "cs %s \"%s", Cmd_Argv(1), Cmd_Argv(2));
    return false;  // not complete
}
if (!strcmp(cmd, "bcs1")) {
    strcat(bigConfigString, Cmd_Argv(2));
    return false;
}
if (!strcmp(cmd, "bcs2")) {
    strcat(bigConfigString, Cmd_Argv(2));
    strcat(bigConfigString, "\"");
    // re-dispatch as `cs` command
}
```

Our parser must mirror this: buffer `bcs0/1/2`, emit a synthetic `cs` to
the same handler.

### Command rate

On a dm_73, reliable `serverCommand`s arrive in order on
`serverCommandSequence` (the first LE32 of the gamestate payload and the
`reliableAcknowledge` of each subsequent message). They arrive asynchronously
from snapshot ticks — a `cs 662 ...` can come mid-frame and is actioned at
the next snapshot's server time.

---

## 10. Round detection in CA (from demo data only)

**Single-source-of-truth: `cs 662 <ms>`.**

From `client/cl_parse.c:1947-1959`:

```c
if (di.protocol == PROTOCOL_QL || di.protocol == 73 || di.protocol == 90) {
    if (!Q_stricmpn(s, "cs 662 ", strlen("cs 662 "))) {
        s2 = s + strlen("cs 662 ") + 1;   // skip past opening quote
        if (Q_isdigit(s2[0])) {
            n = atoi(s2);
            if (di.numRoundStarts < MAX_DEMO_ROUND_STARTS) {
                di.roundStarts[di.numRoundStarts] = n;
                di.numRoundStarts++;
            }
        }
    }
}
```

CS index 662 = `CS_ROUND_TIME` (bg_public.h:109). Every time the server
issues `cs 662 "<ms>"` with a positive integer, that is a new round start at
that server time. When the round ends, the server sets it to `-1`. So the
algorithm is:

```
roundStarts = []
on serverCommand "cs 662 <value>":
    if value > 0 and value != roundStarts[-1]:
        roundStarts.append(value)
```

For CA matches you get exactly one entry per round played; for freezetag it
also ticks. **Max 256 round starts** (`MAX_DEMO_ROUND_STARTS`,
cg_public.h:11).

### CPMA Q3 variant

For CPMA demos (protocol 68, not 73), round time comes via
`cs 710 "\\tw\\<ms>..."` for CA and `cs 672` for CTFS — see cl_parse.c:1961-2003.
Not relevant for QL dm_73 but listed here for parser completeness.

### Deriving game boundaries

- `trap_GetFirstServerTime()` = first snapshot's `serverTime`.
- `trap_GetLastServerTime()` = last snapshot's `serverTime`.
- `trap_GetGameStartTime()` = warmup-end transition, detected from
  `cs 5` (`CS_WARMUP`) going to `-1` then match restart, OR from
  `cs 13` (`CS_LEVEL_START_TIME`) updating.
- `trap_GetGameEndTime()` = first snapshot with `CS_INTERMISSION == 1`
  (cs index 14).

All four are recoverable from configstrings alone — no proprietary data.

---

## 11. `trap_AddAt` is disabled — the replacement is the `at` console command

### What happened to `trap_AddAt`

Inspection of `cgame/cg_syscalls.c:595-600`:

```c
#if 0
void trap_AddAt (int serverTime, const char *clockTime, const char *command)
{
    syscall(CG_ADDAT, serverTime, clockTime, command);
}
#endif
```

The syscall is `#if 0`'d out. The cgame module cannot call it; attempting to
use it in a cgame extension would fail to link, or at best call a no-op. The
engine-side dispatch for `CG_ADDAT` may still exist but the **cgame-facing
VM trap is compiled out**. Consequence: we **cannot schedule capture
start/stop from inside a custom cgame mod** via this syscall.

### The replacement: the `at` console command

The wolfcam cgame implements a console command `at` (source:
`cgame/cg_consolecmds.c:6783-6825`, `CG_AddAtCommand_f`) that schedules a
wolfcam console command to be auto-executed at a specific server time or
clock time.

```
usage: at <'now' | server time | clock time> <command>
example:
  at now timescale 0.5
  at 4546629.50 stopvideo          // server time in ms (fractional allowed)
  at 8:52.33 cg_fov 90             // in-match clock time mm:ss.cs
  at w2:05 r_gamma 1.4             // warmup clock time
```

Parse logic:

1. If arg1 == `"now"`: target time = `cg.ftime` (current frame time).
2. Else: call `CG_GetServerTimeFromClockString(timeString)` which accepts
   `mm:ss`, `mm:ss.cc`, `w<mm:ss>` (warmup prefix), or a raw float server
   time.
3. `CG_AddAtFtimeCommand(ftime)` inserts a sorted entry into
   `cg.atCommands[MAX_AT_COMMANDS]` (array size is defined elsewhere in
   cg_local.h).
4. Each frame, the engine tick runs any `at` commands whose `ftime` has
   been passed since the last check.

### Implication for Phase 2 capture scheduling

Our automation must **write a `.cfg` file** of `at` commands and feed it to
wolfcam at launch via `+exec myfile.cfg`. Example for a single frag at
`killTime_ms = 1_840_250`:

```
// phase2_capture.cfg — generated by extract_frags.py
at 1832250.0 video avi name :frag_007
at 1845250.0 stopvideo
at 1832250.0 cg_drawHUD 0          // optional: hide HUD during capture
at 1845250.0 cg_drawHUD 1
```

Launch:

```
wolfcamql.exe +set fs_homepath <out_dir> +exec phase2_capture.cfg +demo <demo>
```

This is the canonical pattern. The `gamestart.cfg + seekclock ... quit`
example quoted in CLAUDE.md is equivalent for the single-clip case; the
scheduled pattern generalises to multi-frag batches in one pass.

---

## 12. Kill-query API status & failure modes

See `docs/reference/phase2-kill-query-architecture.md` for the full API
surface. Engine-side implementation:

- `CG_GetNextKiller` — `client/cl_cgame.c:873-899`
- `CG_GetNextVictim` — `client/cl_cgame.c:901-927`
- `CG_GetRoundStartTimes` — dispatched at `client/cl_cgame.c:1423-1432`
- Backing store: `di.obit[MAX_DEMO_OBITS]` (2048 entries max) populated by
  the obit ingestion loop at `client/cl_main.c:2078-2167`
- Round-starts backing store: `di.roundStarts[MAX_DEMO_ROUND_STARTS]`
  (256 entries max) populated at `cl_parse.c:1947-1959`

### The known failures

1. **No weapon field in kill-query output.** `demoObit_t` (cg_public.h:22-31)
   records `mod`, BUT the `CG_GetNextKiller` / `CG_GetNextVictim` signatures
   only return `(clientNum, serverTime)` — they do not expose `mod`.
   Confirmed by reading `client/cl_cgame.c:873-927` and
   `cgame/cg_syscalls.h:234` (the trap sig has no weapon out-param).
   → **Workaround**: iterate `di.obit[0..obitNum)` directly via a custom
   `wolfcam_extract_frags` command (see phase2-kill-query-architecture.md
   §"Implementation Path"). Each `demoObit_t` has `mod` populated.

2. **Max 2048 kills per demo.** `MAX_DEMO_OBITS = 2 * 1024`
   (cg_public.h:8). 2048 obits over a 90-minute CA map with ~50 kills/round
   over 40 rounds = plenty of headroom, but long FFA/TDM sessions could
   clip. Our Phase-2 extractor should log a warning if `obitNum` reaches
   the cap.

3. **Max 256 rounds.** `MAX_DEMO_ROUND_STARTS = 256` (cg_public.h:11). No
   real-world demo exceeds this.

4. **Obituary dedup relies on `EVENT_VALID_MSEC = 300`.** Two legitimate
   kills of the same victim by the same killer within 300 ms are possible
   (e.g. rocket splash + direct hit on same frame) but the wolfcam ingestor
   collapses them. If we need frame-precise kill counts for accuracy
   stats, we must re-implement ingestion without the 300 ms window — but
   we lose robustness to packet-duplicate obits.

---

## 13. Nickname dictionary schema

### The data we can extract

For each demo:

- **CS_PLAYERS[slot]** infostring (`CS_PLAYERS = 529`). Keys present in QL:
  - `n`  — player name, includes `^N` color codes
  - `t`  — team (0/1/2/3)
  - `cn` — clan name
  - `c1`, `c2` — head/body colors
  - `hc` — handicap
  - `model`, `hmodel` — body/head model
  - `xcn`, `c` — extra clan / country (QL-specific)
- **playerState.clientNum** — the recording client's own slot (available
  from first snapshot).
- **CS_SERVERINFO** → `sv_hostname`, `g_gametype`, `mapname`.
- **Protocol 91 only**: `CS91_STEAM_ID` (index 714) gives a 64-bit Steam
  community ID for the demo recorder. Dm_73 (protocol 73) predates this
  and does **not** carry Steam IDs per-client.

### Why aliases are hard on dm_73

dm_73 era has **no stable identifier** per player. The same human rotates
nicknames (`^1xXgG`, `XxX`, `tragedy`, etc.), clan prefixes, and handicap
values. We must deduplicate behaviourally.

### Proposed schema

```sql
-- players.db (SQLite)

CREATE TABLE players (
    canonical_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_name      TEXT NOT NULL,       -- chosen "display" nick
    first_seen_demo     TEXT,                -- demo filename
    first_seen_ts       INTEGER,             -- unix ts
    last_seen_demo      TEXT,
    last_seen_ts        INTEGER,
    steam_guid_hash     TEXT,                -- NULL for pure dm_73; populated for dm_90/91 capture of same human
    fingerprint_vec     BLOB                 -- 32-dim f32 behavioural embedding (see below)
);

CREATE TABLE aliases (
    alias_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_id    INTEGER NOT NULL REFERENCES players(canonical_id),
    raw_name        TEXT NOT NULL,           -- exactly as in CS_PLAYERS 'n' key (with ^N codes)
    normalised      TEXT NOT NULL,           -- color-code-stripped, lowercased
    demo_path       TEXT NOT NULL,
    slot            INTEGER NOT NULL,        -- CS_PLAYERS slot index (0..63)
    seen_ts         INTEGER NOT NULL,
    clan_tag        TEXT,
    model           TEXT,
    country         TEXT,
    UNIQUE (raw_name, demo_path, slot)
);

CREATE INDEX idx_aliases_norm  ON aliases(normalised);
CREATE INDEX idx_aliases_canon ON aliases(canonical_id);

CREATE TABLE demo_index (
    demo_path       TEXT PRIMARY KEY,
    protocol        INTEGER NOT NULL,        -- 73 / 90 / 91
    map             TEXT,
    gametype        INTEGER,
    server_hostname TEXT,
    recorder_slot   INTEGER,                 -- playerState.clientNum
    first_server_ms INTEGER,
    last_server_ms  INTEGER,
    duration_ms     INTEGER,
    total_frags     INTEGER,
    parsed_ts       INTEGER
);
```

### Deduplication algorithm

**Priority order** for merging two aliases into one canonical player:

1. **If both demos are dm_90/91** and both carry matching Steam IDs → merge
   unconditionally. (Ground truth.)
2. **Exact normalised match** (`lower(strip_color_codes(name))`) within one
   year → merge with confidence 0.85. Downgrade if clan tag differs.
3. **Behavioural fingerprint cosine similarity > 0.92** across ≥3 shared
   maps → merge with confidence 0.7.

The behavioural fingerprint is a 32-dim vector built from aggregated
statistics:

```
[ rail_frag_ratio, lg_frag_ratio, rocket_frag_ratio, grenade_frag_ratio,
  airshot_ratio, telefrag_ratio, avg_ttk_ms, avg_ca_round_survival_s,
  preferred_maps[top-4 one-hot], weapon-accuracy histogram (8 bins),
  avg_movement_speed, jump_frequency_hz, circle-strafe-direction-bias,
  weapon-swap-frequency_hz, ... ]
```

Most of these components are computable from snapshot streams alone:
positions (playerstate.origin), velocities, weapon-changes (events[0..1]
== EV_CHANGE_WEAPON), kill weapons (obit stream).

### Pragmatic first cut

For the first pass of 2,277 demos, skip the behavioural fingerprint:

1. Parse every demo, emit `(demo_path, slot, raw_name, seen_ts, clan_tag,
   model)` rows into `aliases_raw`.
2. Normalise: strip `^[0-9]` color codes, lowercase, strip surrounding
   whitespace and clan tags in `[...]` / `(...)` / `|...|` patterns.
3. Cluster by exact normalised name. This catches 80% of aliases for free.
4. Manual review UI shows clusters with <100% string match for user
   confirmation. Batch-confirm via CLI.
5. Defer behavioural fingerprint to Phase 3 when we have hard kill data.

### Edge cases

- Empty `n` (spec-only slot): skip.
- `(Bot)` prefix / `skill=` key set: tag as bot, exclude from stats.
- Same demo has two slots with identical name: data is truncated (client
  came in twice on a map restart). Keep both aliases linked to same
  canonical ID.
- QL's `xcn` (extra clan) and `xclan` occasionally encode guild info —
  store in `clan_tag` preferring `cn` over `xcn`.

---

## 14. File source inventory

Every file pulled from in writing this doc. All paths relative to
`G:/QUAKE_LEGACY/tools/quake-source/`.

### Primary refs (all in `wolfcamql-src/code/`)

| path                              | purpose                                      |
|-----------------------------------|----------------------------------------------|
| `qcommon/qcommon.h:281`           | `svc_ops_e` enum (packet-dispatch bytes)     |
| `qcommon/q_shared.h:29-32`        | `PROTOCOL_Q3DEMO=43`, `PROTOCOL_Q3=68`, `PROTOCOL_QL=91` |
| `qcommon/q_shared.h:1179-1220`    | `MAX_CLIENTS`, `GENTITYNUM_BITS`, `MAX_CONFIGSTRINGS`, `MAX_GAMESTATE_CHARS`, `MAX_STATS`, `MAX_PERSISTANT`, `MAX_WEAPONS`, `MAX_POWERUPS`, `CS_SERVERINFO`, `CS_SYSTEMINFO` |
| `qcommon/q_shared.h:1236-1331`    | `playerState_s` struct (incl. QL protocol 90/91 extensions) |
| `qcommon/q_shared.h:1403-1465`    | `entityState_s` struct                       |
| `qcommon/msg.c:136`               | `MSG_WriteBits` (for reference)              |
| `qcommon/msg.c:274-409`           | `MSG_ReadBits` — the core bit reader         |
| `qcommon/msg.c:552`               | `MSG_ReadChar/Byte/Short/Long`               |
| `qcommon/msg.c:658`               | `MSG_ReadBigString`                          |
| `qcommon/msg.c:948-1142`          | `entityStateFieldsQldm91/90/73[]` — the dm_73 field table |
| `qcommon/msg.c:1944-2120`         | `MSG_ReadDeltaEntity` — decode loop          |
| `qcommon/msg.c:2123-2398`         | `playerStateFieldsQldm91/90[]`, `playerStateFieldsQ3[]` (dm_73 reuses Q3 table) |
| `qcommon/msg.c:2949-3124`         | `MSG_ReadDeltaPlayerstate` — decode loop     |
| `qcommon/msg.c:3126-3396`         | `msg_hData[256]` + `MSG_initHuffman`         |
| `qcommon/huffman.c`               | order-0 adaptive huffman impl (`Huff_getBit`, `Huff_offsetReceive`, `Huff_addRef`) |
| `client/cl_main.c:1566-1896`      | `CL_ReadDemoMessage` — the file-container reader |
| `client/cl_main.c:2060-2167`      | obituary ingestion from snapshot entities    |
| `client/cl_parse.c:405-641`       | `CL_ParseSnapshot`                           |
| `client/cl_parse.c:886-1068`      | `CL_ParseGamestate`                          |
| `client/cl_parse.c:1184-1230`     | `CL_ParseDownload` (skip; not used in demos) |
| `client/cl_parse.c:1710-1780`     | `CL_ParseCommandString` — reliable server command ingestion |
| `client/cl_parse.c:1947-2003`     | round-start detection (`cs 662 <ms>`)        |
| `client/cl_parse.c:2087-2233`     | `CL_ParseServerMessage` — the outer dispatch |
| `client/cl_cgame.c:704-767`       | `bcs0`/`bcs1`/`bcs2` configstring reassembly |
| `client/cl_cgame.c:873-927`       | `CG_GetNextKiller`, `CG_GetNextVictim` impl  |
| `client/cl_cgame.c:1335-1432`     | VM syscall dispatch for kill-query + round-starts |
| `client/client.h:477-478`         | `di.roundStarts[MAX_DEMO_ROUND_STARTS]` backing store |
| `game/bg_public.h:74-287`         | `CS_*` configstring index map                |
| `game/bg_public.h:782-788`        | `EV_EVENT_BIT1/2`, `EV_EVENT_BITS`, `EVENT_VALID_MSEC` |
| `game/bg_public.h:790-923`        | `entity_event_t` enum (EV_* codes incl. EV_OBITUARY=58) |
| `game/bg_public.h:1294-1339`      | `meansOfDeath_t` enum (MOD_*)                |
| `game/bg_misc.c:6595`             | `BG_ModToWeapon` — MOD→weapon mapping        |
| `cgame/cg_public.h:8-31`          | `MAX_DEMO_OBITS`, `MAX_DEMO_ROUND_STARTS`, `demoObit_t`, `itemPickup_t`, `timeOut_t` |
| `cgame/cg_event.c:85-166`         | `CG_Obituary` — cgame-side obit display      |
| `cgame/cg_event.c:3598-3615`      | `case EV_OBITUARY:` dispatch                 |
| `cgame/cg_syscalls.c:585-625`     | `trap_GetFirstServerTime` et al; **`trap_AddAt` `#if 0`d out** (line 595-600) |
| `cgame/cg_syscalls.h:234`         | `trap_AddAt` prototype (the still-declared-but-unwired signature) |
| `cgame/cg_consolecmds.c:6783-6825`| `CG_AddAtCommand_f` — the **actual** scheduling mechanism (console `at` command) |
| `cgame/cg_consolecmds.c:6740-6781`| `CG_AddAtFtimeCommand` — sorted insertion into `cg.atCommands[]` |
| `cgame/cg_servercmds.c:5640-5921` | dispatch table for all reliable server commands |
| `server/sv_init.c:34-71`          | `SV_SendConfigstring` — where `bcs0/1/2` come from |

### Secondary / cross-checks

| path                                                     | purpose                            |
|----------------------------------------------------------|------------------------------------|
| `qldemo-python/huffman/huffman.c`                        | independent implementation of Q3 adaptive huffman (identical to wolfcam's) |
| `qldemo-python/huffman/pyhuffman.c`                      | Python C-ext wrapper over `huffman.c` |
| `qldemo-python/qldemo/demo.py`                           | reference Python parser — canonical iterate/dispatch loop |
| `qldemo-python/qldemo/constants.py`                      | `SVC_*` constants mirrored in Python |
| `qldemo-python/qldemo/data.py`                           | `GameState`, `EntityStateNETF`, `PlayerStateNETF` dataclasses (mirror of `netField_t` tables) |
| `uberdemotools/TECHNICAL_NOTES.md`                       | UDT's own notes on dm_73 (useful for sanity checks) |
| `uberdemotools/CUSTOM_PARSING.md`                        | UDT's plugin architecture — worth reading before writing our own parser |
| `demodumper/demodumper.py`                               | older independent parser — same algorithm, different shape |
| `wolfcamql-src/code/cgame/cg_main.c:8522`                | `trap_GetRoundStartTimes` call-site (how the cgame consumes round data) |
| `quake3-source/code/`                                    | stock id tree — useful for checking original Q3 field orderings when dm_73 inherits them |

### Not used (but available)

- `darkplaces/`, `openarena-*`, `yamagi-quake2/`, `q3mme/`, `q3vm/`,
  `ioquake3/`, `quake3e/`, `wolfet-source/`, `quake1-source/`,
  `quake2-source/`, `gtkradiant/` — out of scope for dm_73. The darkplaces
  and openarena trees carry different demo formats; q3mme has a fork with
  cinematic-camera extensions that might be worth mining for Phase 3 camera
  math but is not part of the format spec.

---

## 15. Recommended build plan for our own parser

Total: ~2500 LOC of C, single-binary CLI, statically linked. Target: 3 days
of focused work.

1. **Vendored bits from wolfcam** (copy verbatim, no edits):
   - `qcommon/huffman.c` + its header in `q_shared.h`
   - `msg_hData[256]` and `MSG_initHuffman` from `qcommon/msg.c:3126-3396`
   - `MSG_ReadBits`, `MSG_ReadByte`, `MSG_ReadShort`, `MSG_ReadLong`,
     `MSG_ReadBigString` from `qcommon/msg.c:274-730`
   - `MSG_ReadDeltaEntity`, `MSG_ReadDeltaPlayerstate`
   - The `entityStateFieldsQldm73[]` and `playerStateFieldsQ3[]` tables

2. **Our thin wrapper:**
   - `dm73_open(path)` — mmap file, seek offset 0
   - `dm73_next_message(dm73, &seq, &len, &payload)` — read the 8-byte
     header and `len` bytes, invoke huffman init-once
   - `dm73_parse_message(payload, len, callbacks)` — reimplement
     `CL_ParseServerMessage` with callbacks for gamestate / snapshot /
     serverCommand; *do not* build the full `clientActive_t` machinery
   - snapshot callback gets `(serverTime, playerState, entities[])` with
     delta already applied against the baseline + previous snapshot
   - serverCommand callback gets raw ASCII string; caller handles `cs`,
     `bcs0/1/2`, `print`, `scores`, etc.

3. **Built-in derivations:**
   - Maintain `configstrings[MAX_CONFIGSTRINGS]` string table — update on
     `svc_configstring` in gamestate, on reliable `cs <idx> "<val>"`, and
     on reassembled `bcs0/1/2`.
   - Maintain `roundStarts[]` — push every new `cs 662 <ms>` with value > 0.
   - Maintain `obits[]` — on each snapshot, scan entities; for any where
     `(event & ~0x300) == EV_OBITUARY`, run the dedup logic from
     `cl_main.c:2092-2167`.

4. **JSON output:** one JSON line per "event of interest" —
   `{type:"obit", t:<ms>, killer:<slot>, victim:<slot>, mod:<n>,
   killer_name:"<from CS_PLAYERS>", victim_name:"..."}`. Phase 2/3
   consume this as stdin.

5. **What we deliberately skip:**
   - Download blocks (demos never contain these — `svc_download` data is
     in-game file transfer, not demo recording).
   - VoIP extensions — we mute in renders anyway.
   - The full `clSnapshot_t` ring buffer for prediction; we're
     replay-only.
   - Legacy uncompressed protocol 43/46/48 — those are `.dm3` not `.dm_73`.
     If we ever need them add `MSG_InitOOB` + `MSG_ReadDeltaEntityDM3` +
     `MSG_ReadDeltaPlayerstateDM3` (msg.c:1769, 2794). Not for Phase 2.

The result is a parser with **exact** byte-for-byte fidelity to wolfcamql,
shares its Huffman table (so it will never disagree on a byte), and is
small enough to audit in an afternoon. UberDemoTools' advantage (cut/seek
operations) is irrelevant — we only *read*.

---

## Appendix A. Quick reference: "how do I find X?"

| I want to find...                  | source of truth                                      |
|------------------------------------|------------------------------------------------------|
| A player's name                    | `CS_PLAYERS + clientSlot` infostring, key `n`       |
| Current match map                  | `CS_SERVERINFO` key `mapname`                        |
| Gametype (CA/CTF/TDM/FFA)          | `CS_SERVERINFO` key `g_gametype`                     |
| Demo protocol                      | `CS_SERVERINFO` key `protocol` (also file extension) |
| Match start time (ms)              | `CS_LEVEL_START_TIME` (index 13)                     |
| When warmup ended                  | `CS_WARMUP` (index 5) transitioning to -1            |
| CA round start times               | every `cs 662 <ms>` event                            |
| Kill events                        | entities with `(event & ~0x300) == 58` per snapshot  |
| Killer of a kill                   | `entity.otherEntityNum2`                             |
| Victim of a kill                   | `entity.otherEntityNum`                              |
| Weapon of a kill                   | `entity.eventParm` → `meansOfDeath_t`                |
| Player position                    | `playerState.origin` (own player)  or                |
|                                    | `entity.pos.trBase[]` + trajectory extrapolation (others) |
| Player velocity                    | `playerState.velocity` / `entity.pos.trDelta[]`      |
| Armor/health                       | `playerState.stats[STAT_ARMOR]`, `stats[STAT_HEALTH]`|
| Chat messages                      | server command `chat "<text>"` / `tchat "<text>"`    |
| Scoreboard snapshots               | server command `scores <...>`                        |
| Timeouts                           | `CS_TIMEOUT_BEGIN_TIME` / `CS_TIMEOUT_END_TIME`       |
| Match end                          | `CS_INTERMISSION` (index 14) → 1                     |

All of it — every bit of it — is recoverable from the demo alone, without
re-rendering in wolfcamql. This is why Phase 2's kill-query API works at all:
wolfcamql itself is just replaying the same bytes and deriving the same
truth during playback.
