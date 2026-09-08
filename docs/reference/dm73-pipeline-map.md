# dm_73 — verified format map and extraction pipeline

*Written 2026-08-29 from a working parser. Every field table, offset and
constant below was confirmed against real demos in `demos/`, not copied from a
spec. Where something is still unverified it says so.*

Companion to `dm73-format-deep-dive.md` (the format reference). This document is
the **operational** map: what the bytes are, what we extract, what we do NOT yet
extract, and what each downstream stage needs.

---

## 0. Why this document exists

Two bugs cost this project months, and both were invisible:

1. **The areamask off-by-one.** `_parse_snapshot` read `areamaskLen + 1` bytes.
   One extra byte desynced the bitstream at the head of every snapshot, so the
   playerstate and every entity delta after it decoded as garbage.
   **73.6% of all packets failed** and were swallowed by a bare
   `except Exception: pass`. The parser reported success the whole time.

2. **Discarded entity state.** The parser decoded per-entity state and threw it
   away, exporting only the playerstate. That stream covers **only the player the
   demo followed** — 4 clients, and just **7% of kills had victim coverage** — so
   airshot detection was impossible for 93% of frags.

Both were fixed. The lesson generalises: **a demo parser that "mostly works" is
a red flag.** A healthy demo must decode with **zero** failed packets.

---

## 1. File framing

A `.dm_73` file is a flat sequence of length-prefixed messages. No header, no
index, no footer beyond the EOF marker.

```
repeat until EOF:
    int32   sequence        little-endian
    int32   length          little-endian
    byte[length]  payload   Huffman-compressed message
```

Terminate on `sequence == -1` or `length <= 0`. Both appear at a clean EOF.

**Hardening not yet applied:** `length` is used directly for the read with no
`MAX_MSGLEN` (16384) sanity check. A corrupt length triggers a huge allocation.

---

## 2. Compression — adaptive Huffman

Payloads are Huffman-coded with Q3's tree, seeded once from the static
`msg_hData` frequency table (256 entries).

**Critical subtlety:** the tree is *adaptive by construction* but Q3's MSG layer
**never adapts it during a message** — it is seeded once and then read-only.
`receive()` must NOT call `add_ref()`. Getting this wrong desyncs everything.

Bit reading follows `MSG_ReadBits` exactly, and it is *not* uniform:

| Portion | How it is read |
|---|---|
| `bits & 7` sub-byte remainder | **RAW bits**, LSB-first, no Huffman |
| Remaining whole bytes | **Huffman-decoded**, 8 bits at a time |

```
value  = 0
nbits  = n & 7
for i in range(nbits):            # raw
    value |= raw_bit() << i
shift = nbits
for each remaining byte:          # Huffman
    value |= huff_byte() << shift
    shift += 8
```

**Known gap:** Q3 sign-extends when `MSG_ReadBits` is called with a negative bit
count. Our reader has no sign extension, and `_PS_BITS` is documented as holding
"abs values of signed fields". Signed playerState fields therefore decode as
large positives. Not yet fixed; affects delta_angles and similar.

---

## 3. Message structure

Each payload begins:

```
int32   reliable-acknowledge sequence
byte    svc command
```

`svc_ops_e` — confirmed against a real demo's histogram:

| id | command | seen in one 20-min CA demo |
|---|---|---|
| 0 | `svc_bad` | — |
| 1 | `svc_nop` | — |
| 2 | `svc_gamestate` | 1 |
| 3 | `svc_configstring` | — |
| 4 | `svc_baseline` | — |
| 5 | `svc_serverCommand` | 1,480 |
| 6 | `svc_download` | — |
| 7 | `svc_snapshot` | **19,908** |
| 8 | `svc_EOF` | — |

Snapshots are ~93% of all traffic. Everything expensive happens there.

---

## 4. Snapshot layout — **the byte that broke everything**

```
int32   serverTime
byte    deltaNum           0 = full update, else delta from that snapshot
byte    snapFlags
byte    areamaskLen
byte[areamaskLen]          <-- EXACTLY areamaskLen. NOT +1.
        playerState delta
        entity deltas, terminated by entityNum == 1023
```

> `areamask byte[areamaskLen]` — `dm73-format-deep-dive.md:348`, matching Q3's
> `CL_ParseSnapshot` → `MSG_ReadData(msg, &areamask, len)`.

Measured impact of the off-by-one on `CA-...asylum-2012_11_11`:

| | packets OK | failed | dropped |
|---|---|---|---|
| reading `+1` | 5,652 | 15,737 | **73.6%** |
| reading exactly | 21,389 | 0 | **0.0%** |

Guarded by `creative_suite/tests/test_dm73_netcode.py`, which asserts **zero**
dropped packets across a real demo.

`deltaNum == 0` resets accumulated entity state to the gamestate baseline.

---

## 5. Entity delta encoding

```
1 bit   removed?        -> entity gone this snapshot
1 bit   has delta?      -> 0 means unchanged
byte    lastField       highest field index present
for i in 0..lastField-1:
    1 bit  changed?
        if _ES_BITS[i] == 0:            # float field
            1 bit non-zero?
                1 bit  0 -> 13-bit truncated int, value = n - 4096
                       1 -> full 32-bit IEEE float
            (non-zero bit 0 => value is 0.0)
        else:                            # integer field
            1 bit non-zero?  -> read _ES_BITS[i] bits
```

### EntityState field table — VERIFIED indices

Field order matches Q3's `entityStateFields` exactly, which is how
`groundEntityNum` was located.

| idx | bits | field | used for |
|---|---|---|---|
| 0 | 32 | `pos.trTime` | |
| 1 | 0 | `pos.trBase[0]` | **origin X** |
| 2 | 0 | `pos.trBase[1]` | **origin Y** |
| 3 | 0 | `pos.trDelta[0]` | **velocity X** |
| 4 | 0 | `pos.trDelta[1]` | **velocity Y** |
| 5 | 0 | `pos.trBase[2]` | **origin Z** |
| 6 | 0 | `apos.trBase[1]` | **view yaw** |
| 7 | 0 | `pos.trDelta[2]` | **velocity Z** |
| 8 | 0 | `apos.trBase[0]` | **view pitch** |
| 10 | 10 | `event` | event code (mask `& ~0x300` for sequence bits) |
| 12 | 8 | `eType` | `> ET_EVENTS` means a temp-entity event |
| 14 | 8 | `eventParm` | |
| **16** | **10** | **`groundEntityNum`** | **`== 1023` (ENTITYNUM_NONE) = AIRBORNE** |
| 18 | 19 | `eFlags` | |
| 19 | 10 | `otherEntityNum` | **victim** client slot |
| 20 | 8 | `weapon` | |
| 21 | 8 | `clientNum` | |
| 31 | 10 | `otherEntityNum2` | **killer** client slot |

Entity numbers **below 64 (MAX_CLIENTS) are players.** That is the whole basis
of the per-player tracking in §7.

---

## 6. Frag detection

```python
entity.event & ~0x300 == EV_OBITUARY
killer = entity.otherEntityNum2     # idx 31
victim = entity.otherEntityNum      # idx 19
weapon = entity.eventParm           # MOD_* constant
time   = snapshot.serverTime
```

`0x300` masks the event sequence bits the engine toggles to force a re-send of
an otherwise-identical event.

MOD_* ids confirmed in the obituary stream: 1 gauntlet, 2 machinegun,
3 shotgun, 4/5 grenade (+splash), 6/7 rocket (+splash), 8/9 plasma (+splash),
10 railgun, 11 lightning.

---

## 7. What we now export

`DM73Parser.parse()` returns:

| key | contents | coverage |
|---|---|---|
| `events` | obituary, pain, item_pickup, taunt, railtrail, death, … | 9,162 in one demo |
| `snapshots` | **playerstate only** — the followed player | 4 clients (of 9) |
| `entities` | **every player entity** per snapshot | **7 clients, 83k records** |
| `accuracy` | server scoreboard accuracy per client | 459 records, 9 clients |
| `players`, `rounds`, `player_stats` | derived | 9 players, 16 rounds |

`entities` rows carry: `server_time_ms, entity_num, client_num, origin_x/y/z,
vel_x/y/z, angle_yaw, angle_pitch, weapon, ground_entity, airborne`.

**Use `entities`, not `snapshots`, for anything about a player who is not the
demo taker.** That is the whole difference between 7% and 100% frag coverage.

### Scoreboard (`scores` servercommand)

```
scores <numScores> <teamScore1> <teamScore2>  then numScores rows of 18 ints
```

QL extends Q3's 13-field row to **18**. Verified offsets:

| idx | meaning |
|---|---|
| 0 | clientNum |
| 1 | score |
| 2 | ping |
| **6** | **accuracy %** — validated 0..100 across the corpus |

**Limit:** this is OVERALL accuracy. QL's CA scoreboard carries **no per-weapon
breakdown**, so a shaft-specific figure is not obtainable from the demo.

---

## 8. Frag classification

`engine/parser/frag_classify.py`. On one demo: 63 kills, 24 tagged.

| tag | basis | confidence |
|---|---|---|
| `airshot` | `groundEntityNum == ENTITYNUM_NONE` **plus** ≥55u clearance above the floor the victim last stood on | SOLID |
| `air_rocket` / `air_nade` / `air_shaft` | airshot + MOD | SOLID |
| `air_combo` | ≥2 airshots by one killer within 3 s | SOLID |
| `multikill` / `quadkill` | 2–3 / 4+ kills in QL's 3 s window | SOLID |
| `rocket_rail`, `shaft_rail`, `shaft_rocket`, `rocket_shaft` | consecutive kills, different weapons, ≤2 s | SOLID |
| `big_flick` | ≥65° of yaw swept in the 300 ms before the kill | SOLID |
| `pixel_shot` | rail kill at ≥2200 units | SOLID |
| `high_acc_shaft` | shaft kill while server-reported accuracy ≥40% | SOLID (overall acc) |
| `preshot` | aim parked within 6° for 500 ms before the kill | **PROXY** |

**Why the clearance gate matters:** `groundEntityNum` alone is true during
ordinary strafe-jumping and tagged **46%** of kills as airshots. With the gate,
**11%** — which matches what a human calls an airshot.

**`preshot` is the one remaining heuristic.** A true preshot means firing before
the victim was *visible*, which needs a PVS/trace we do not compute. We detect
the observable half: the aim was parked, not tracking.

---

## 9. Pipeline stages and what each needs

| Stage | Status | Needs |
|---|---|---|
| **1. Parse** | ✅ working, 0 dropped packets | — |
| **2. Classify frags** | ✅ working | — |
| **3. Rebuild `frags.db`** | ⛔ **not done** | The existing 222 frags / 11 demos were built on the BROKEN parser and must be discarded |
| **4. Extract clips** | partial | WolfcamQL automation exists; needs frag timestamps from stage 2 |
| **5. Third-person / follow-up angles** | manual today | See below |
| **6. Textures** | Phase 5 pipeline exists | — |
| **7. 3D map/scene rendering** | ⛔ research only | FT-3 has no pipeline; `/api/forge/intro` is a stub |

### Stage 4 — clip extraction

`/fragforward [pre-kill seconds] [death hover seconds]` is WolfcamQL's own
frag-to-frag command. Wolf Whisperer's docs describe the frag scan as "kill
minus 2.5 seconds". The kill is the anchor; lead-in is a parameter.

Per-frag capture:
```
seekclock <mm:ss>; video avi name :<demo>; at <mm:ss> quit
```

### Stage 5 — third-person, and the thing to get right

Research (ESReality moviemaking interviews, 29 editors) is consistent on two
points that contradict a naive implementation:

- **The alt angle REPLACES a slice of the POV on one continuous timeline** — it
  is not appended as a repeat. ashr: the camera pass goes "on a separate layer
  directly on top of the first person footage… easy to cut back and forth."
- **It must be earned.** myT: "Most of the recams don't help appreciate or
  understand the frags better." A second angle is justified when one angle
  cannot convey the frag — multikill, through-wall, long projectile flight,
  victim off-screen. Stage 2's tags are exactly the gate for this.
- **Never cut out of POV before the kill lands.** That is the single sharpest
  named failure mode.

### Slow motion — a structural limitation worth stating

The reference movies capture at **200–300 fps in-engine with 0.1 timescale**,
and q3mme's timeline "affect[s] the playback of the action in the demo, **but
not the camera run**." Camera glides at authored speed through a slowed world.

**From finished 30 fps AVIs that look is unreachable** — `setpts` slows the
camera too. Motion interpolation buys smoothness, not the reference aesthetic.
Reproducing it properly requires re-capturing from demos (stage 4), which is
exactly why the demo track matters.

---

## 10. Known gaps

| # | Gap | Impact |
|---|---|---|
| 1 | `parse()` swallows packet errors with no counter | A systematic desync is indistinguishable from trailing garbage — this is how the areamask bug hid |
| 2 | No sign extension in `readbits` | Signed playerState fields decode as large positives |
| 3 | `readstring` has no length cap (Q3 caps at 1024) | Unbounded read on malformed input |
| 4 | No `MAX_MSGLEN` check on packet length | Huge allocation on corrupt length |
| 5 | No bounds check on `data[offset >> 3]` | Overruns surface as IndexError, not a framing error |
| 6 | `seq` / ack read and discarded | No ordering or duplicate validation |
| 7 | P1-DD sound-template library is **empty** | Audio event recognition degrades to loudest-onset |
| 8 | FT-1 documented as a C++17 parser with CMake/dm73dump | **Does not exist.** The parser is Python |

---

## 11. Reproducing from scratch

```bash
# parse one demo
python engine/parser/demo_parse.py "demos/<name>.dm_73"

# classify its frags
python engine/parser/frag_classify.py "demos/<name>.dm_73" --top 20

# prove the bitstream is healthy (must be ZERO dropped packets)
pytest creative_suite/tests/test_dm73_netcode.py -v
```

If the netcode test fails, **stop** — every number downstream is wrong.
