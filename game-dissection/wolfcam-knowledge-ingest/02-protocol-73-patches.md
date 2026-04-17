# 02 — Protocol-73 Patches (wolfcamql vs ioquake3)

License: GPL-2.0 — diff hunks reproduced under fair use for interoperability
documentation. Source trees compared:
- wolfcam: `G:/QUAKE_LEGACY/tools/quake-source/wolfcamql-src/code/`
- ioquake3 baseline: `G:/QUAKE_LEGACY/tools/quake-source/ioquake3/code/`

Cross-reference: `docs/reference/dm73-format-deep-dive.md` (the byte-level
`.dm_73` container format; this doc is the *bit-level delta* content of the
snapshots inside that container).

---

## Summary

- **Protocol 73 is NOT a single `#define`.** Wolfcam's headline
  `PROTOCOL_VERSION` is actually `91` (current QL); protocol 73 is a
  *transitional* QL protocol handled by runtime branches on
  `com_protocol->integer`. The constant literal `73` appears inline.
  - `qcommon/qcommon.h:242` `#define PROTOCOL_VERSION 91`
  - `qcommon/qcommon.h:243` `#define PROTOCOL_LEGACY_VERSION 68`
  - `qcommon/qcommon.h:241` `//#define PROTOCOL_VERSION 73` (commented out,
    proves 73 was historically the active version)
  - `qcommon/q_shared.h:31-32`: `PROTOCOL_Q3 68`, `PROTOCOL_QL 91`. Protocol
    73 has no macro — it's a magic number.
  - `qcommon/common.c:75`
    `int demo_protocols[NUM_DEMO_PROTOCOLS] = { 43, 44, 45, 46, 47, 48, 66, 67, 68, 69, 70, 71, 73, 90, 91 };`
    (NUM_DEMO_PROTOCOLS = 15, declared in qcommon.h:249)

- **Family membership:** wolfcam repeatedly treats protocols **73, 90, 91**
  as "the QL family" with one guard idiom:
  `if (com_protocol->integer == PROTOCOL_QL || com_protocol->integer == 73 || com_protocol->integer == 90)`.
  Protocols 68 and below are the Q3 family. Protocols 43-48 are the
  very old "DM3" subfamily (Q3 1.16 / beta) and have their own write/read
  path.

- **Files modified for proto-73 playback (semantic changes):** 4 of 9
  inspected — msg.c, q_shared.h, bg_public.h, cl_parse.c (plus cl_cgame.c
  for VM bridging).
  Byte-identical or cosmetic-only: **huffman.c** (identical), **net_chan.c**
  (dead `#if 0` block only), **sv_snapshot.c** (cosmetic + `svc_voip`
  rename), **qcommon.h** (version constants + svc/clc enum rename, no
  wire-level change for proto-73).

- **Net-channel changes:** NO. `net_chan.c` is semantically unchanged —
  fragmentation and reliable-command layer are protocol-agnostic.

- **Huffman table changes:** NO. `huffman.c` is byte-identical; the adaptive
  Huffman tree the server builds during gamestate is protocol-agnostic.
  (Confirmed via `diff -q`: files identical.)

- **`entityState_t` field-table changes: YES.** Seven separate delta-field
  tables exist (vs. one in ioquake3). For protocol 73 specifically:
  `entityStateFieldsQldm73` is `entityStateFieldsQ3` + `pos.gravity` +
  `apos.gravity` (two new 32-bit trajectory-gravity fields).

- **`playerState_t` field-table changes for proto-73: NO NEW FIELDS.**
  Protocol 73 uses `playerStateFieldsQ3` (same as protocol 68). The
  differences between Q3 and QL playerstate only appear at protocols 90/91
  (double-jump, crouch slide, etc.). This is the key insight — proto-73's
  PS layout is protocol-68 compatible.

- **Struct additions in q_shared.h (used conditionally):**
  - `trajectory_t`: `+ int gravity;`
  - `playerState_t`: `+ qboolean doubleJumped; int jumpTime;`
    (QL ≥ 90 only) `+ int crouchTime, crouchSlideTime, location, fov,
    forwardmove, rightmove, upmove, weaponPrimary;` (QL 91 only)
  - `entityState_t`: `+ int jumpTime; qboolean doubleJumped;` (QL ≥ 90) +
    `+ int health, armor, location;` (QL 91 only)
  - `connstate_t`: `+ CA_DOWNLOADINGWORKSHOPS` (new state between
    `CA_AUTHORIZING` and `CA_CONNECTING`)

- **New EV_\* events (proto-73 cares about):** the entire
  `entity_event_t` enum in `game/bg_public.h` was renumbered to match QL
  (EV_OBITUARY = 58). Old Q3 enum preserved as `EVQ3_*`, ancient DM3 enum
  as `EVQ3DM3_*`. New QL events visible to proto-73 snapshots include
  `EV_POWERUP_ARMOR_REGEN (62)`, `EV_PROXIMITY_MINE_STICK (65)`,
  `EV_KAMIKAZE (67)` through `EV_LIGHTNINGBOLT (72)`,
  `EV_TAUNT_YES/NO/FOLLOWME/GETFLAG/GUARDBASE/PATROL`,
  `EV_FOOTSTEP_SNOW (81)`, `EV_FOOTSTEP_WOOD (82)`,
  `EV_ITEM_PICKUP_SPEC (83)`, `EV_OVERTIME (84)`, `EV_GAMEOVER (85)`,
  `EV_THAW_PLAYER (87)`, `EV_THAW_TICK (88)`, `EV_HEADSHOT (89)`,
  `EV_POI (90)`, `EV_RACE_START/CHECKPOINT/END (93/94/95)`,
  `EV_DAMAGEPLUM (96)`, `EV_AWARD (97)`, `EV_INFECTED (98)`,
  `EV_NEW_HIGH_SCORE (99)`. Values numbered as inline comments in
  `bg_public.h` (many marked "guess" — wolfcam authors reverse-engineered
  from live demos).

- **Configstring layout changed:** Q3 `CSQ3_PLAYERS = 544` (CSQ3_MODELS +
  MAX_MODELS + MAX_SOUNDS + etc). QL `CS_PLAYERS = 529` because QL
  re-indexes (`CS_MODELS = 17`, `CS_SOUNDS = 274`). `cl_parse.c` guards
  every configstring dereference with the
  `di.protocol == PROTOCOL_QL || == 73 || == 90` idiom to pick the right
  offset table. This is *critical* for `.dm_73` playback — player names,
  scores, team info all live at different string indices than Q3.

---

## File-by-file patches

### qcommon/huffman.c

**Purpose:** Adaptive Huffman compression used on every packet body after
the first sequence byte. Shared code; tree adapts to symbol frequency.

**Why patched:** Not patched. Bit-for-bit identical between wolfcam and
ioquake3.

> No changes. `diff -q` reports files identical (11,626 bytes each).
> **Port note for q3mme:** Huffman layer can be lifted verbatim — or if
> q3mme already ships this file, leave it alone.

---

### qcommon/net_chan.c

**Purpose:** Reliable fragment reassembly, sequence numbers, rate limiting.

**Why patched:** Only a commented-out `#if 0 ... #endif` block was added
containing `Netchan_ScramblePacket` / `Netchan_UnScramblePacket` — dead
code, commented by id ("TTimo: unused, commenting out to make gcc happy").
No live protocol-73 changes.

#### Patch 1: dead-code anti-proxy scrambler restored (disabled)
```diff
@@ -99,6 +99,92 @@
+// TTimo: unused, commenting out to make gcc happy
+#if 0
+/*
+==============
+Netchan_ScramblePacket
+A probably futile attempt to make proxy hacking somewhat more difficult.
+==============
+*/
+#define	SCRAMBLE_START	6
+static void Netchan_ScramblePacket( msg_t *buf ) { ... }
+static void Netchan_UnScramblePacket( msg_t *buf ) { ... }
+#endif
```
**Plain English:** Wolfcam vendored an older id-era packet scrambler but
kept it compiled-out. Purely historical — does not run.

**Port note for q3mme:** Skip. No semantic change.

Remaining diffs in this file are pure whitespace (`\t` vs spaces, trailing
whitespace) — not worth porting.

---

### qcommon/qcommon.h

**Purpose:** Declares protocol constants, svc_\* / clc_\* command enums,
MSG buffer size ceiling, core function prototypes.

**Why patched:** (1) version constants advanced to QL 91, (2) svc/clc
extension points renamed to make QL's opus-less voip layer fit back-compat,
(3) `MAX_MSGLEN` doubled to handle QL's bigger snapshots, (4) a raft of
wolfcam-specific infrastructure additions (UTF-8 field editor, Steam/QL
path helpers, broken-demo cvar) — those last are not protocol-73 semantics
per se but are PREREQUISITES for the demo-replay code to compile.

#### Patch 1: protocol version block
```diff
@@ -244,13 +236,18 @@
-#define	PROTOCOL_VERSION	71
-#define PROTOCOL_LEGACY_VERSION	68
+//#define	PROTOCOL_VERSION	73
+#define PROTOCOL_VERSION 91
+#define PROTOCOL_LEGACY_VERSION 68
 // 1.31 - 67

 // maintain a list of compatible protocols for demo playing
 // NOTE: that stuff only works with two digits protocols
-extern int demo_protocols[];
+// 43, 44, 45, 46, 47, 48, 66, 67, 68, 69, 70, 71, 73, 90, 91
+#define NUM_DEMO_PROTOCOLS 15  //FIXME err....  ARRAY_LEN()
+extern int demo_protocols[NUM_DEMO_PROTOCOLS];
```
**Plain English:** wolfcam elevates the live protocol to 91 and whitelists
15 historical protocols for demo playback, with proto-73 sitting in the
middle of the QL block. The commented `//#define PROTOCOL_VERSION 73`
shows 73 was the original standalone-QL version the code was built
against.

**Port note for q3mme:** q3mme today defines `PROTOCOL_VERSION 68`. For a
protocol-73 playback port, do NOT change q3mme's server-side
`PROTOCOL_VERSION`. Instead, introduce a **demo-only** cvar (wolfcam's
`com_protocol`) whose value is sniffed from the `.dm_73`'s first gamestate
message and routed through all msg.c delta functions. Add the
`demo_protocols[]` whitelist and `NUM_DEMO_PROTOCOLS`.

#### Patch 2: svc_\* / clc_\* enum extension slots
```diff
@@ -292,9 +289,10 @@
 	svc_snapshot,
 	svc_EOF,
-// new commands, supported only by ioquake3 protocol but not legacy
-	svc_voipSpeex,
-	svc_voipOpus,
+	// svc_extension follows a svc_EOF, followed by another svc_* ...
+	//  this keeps legacy clients compatible.
+	svc_extension,
+	svc_voip,
 };
```
(Same shape for `clc_voipOpus → clc_voip` / `clc_extension`.)

**Plain English:** ioquake3 has TWO voip opcodes (Speex legacy + Opus
current). Wolfcam keeps ONE QL-style `svc_voip` and adds a generic
`svc_extension` escape so future commands can be bolted on after an
`svc_EOF`. For demo playback this matters only insofar as the parser
must not crash on an unknown `svc_voip` opcode.

**Port note for q3mme:** q3mme should add `svc_extension` as a no-op and
`svc_voip` as a silent-skip (no audio decode needed for fragmovie use
case).

#### Patch 3: MAX_MSGLEN doubled
```diff
-#define	MAX_MSGLEN				16384
+#define	MAX_MSGLEN				(16384 * 2)
```
**Plain English:** QL snapshots at higher player counts overflow the
16KB Q3 buffer. Wolfcam bumps to 32KB.

**Port note for q3mme:** REQUIRED. Without this any proto-73 snapshot
parse that exceeds 16KB will be rejected. Set to `32768`.

#### Patch 4: UTF-8 field editor (infrastructure)
```diff
-#define	MAX_EDIT_LINE	256
 typedef struct {
 	int		cursor;
 	int		scroll;
 	int		widthInChars;
-	char	buffer[MAX_EDIT_LINE];
+	fieldChar_t	xbuffer[MAX_EDIT_LINE];
 } field_t;
+typedef struct { int codePoint; char utf8Bytes[4]; int numUtf8Bytes; } fieldChar_t;
```
**Plain English:** QL strings can contain Unicode code points. Wolfcam's
field editor stores each character as a decoded code point + its UTF-8
byte sequence.

**Port note for q3mme:** Only needed if q3mme re-exposes the console field
in playback UI. For headless demo parsing, skip — the UTF-8 passes
through as bytes in configstrings.

Other qcommon.h additions (`Sys_QuakeLiveDir`, `FS_FindSystemFile`,
`Cvar_Exists`, `com_brokenDemo`) are wolfcam replay infrastructure —
document them in the port plan under "harness code", not
"wire-format changes."

---

### qcommon/msg.c — **THE HEART OF PROTOCOL 73**

**Purpose:** Bit-level serialization/deserialization of all network
messages. `MSG_WriteBits/ReadBits`, `MSG_WriteDeltaEntity/ReadDeltaEntity`,
`MSG_WriteDeltaPlayerstate/ReadDeltaPlayerstate` live here.

**Why patched:** Because the wire format for entityState and playerState
delta-compression differs between protocol families. Wolfcam forks every
delta function into per-protocol branches keyed on `com_protocol->integer`.
File grew from 39,884 bytes (ioquake3) to 85,463 bytes (wolfcam) — more
than doubled.

#### Patch 1: Error handling turns soft (MSG_Error vs Com_Error)
```diff
+qboolean Msg_TestParse = qfalse;
+qboolean Msg_Abort = qfalse;
+
+static void MSG_Error (int code, const char *fmt, ...)
+{
+	va_list argptr;
+	char errorMsg[MAX_PRINT_MSG];
+    va_start(argptr, fmt);
+	Q_vsnprintf (errorMsg, sizeof(errorMsg), fmt, argptr);
+	va_end(argptr);
+	if (Msg_TestParse) {
+		if (!com_brokenDemo->integer) { Msg_Abort = qtrue; }
+		Com_Printf(S_COLOR_RED "demo error: '%s'\n", errorMsg);
+	} else {
+		if (com_brokenDemo->integer) {
+			Com_Printf(S_COLOR_RED "demo error: '%s'\n", errorMsg);
+		} else {
+			Com_Error(code, "%s", errorMsg);
+		}
+	}
+}
```
Then every `Com_Error(ERR_DROP, ...)` inside msg.c is replaced with
`MSG_Error(ERR_DROP, ...); return;`.

**Plain English:** ioquake3 aborts on malformed messages. Wolfcam must
tolerate partially-corrupt demos (the user's 10-year-old recordings).
When `com_brokenDemo` is set, parse errors become printed warnings and
the parser continues.

**Port note for q3mme:** High value for fragmovie work. Port this pattern
— bad demos are the default, not the exception. Also add `Msg_TestParse`
harness so a first-pass validator can refuse without a crash.

#### Patch 2: MSG_WriteBits forks on protocol for byte-aligned optimization
```diff
@@ -125,22 +157,89 @@
-		if ( bits == 8 ) {
-			msg->data[msg->cursize] = value;
-			msg->cursize += 1;
-			msg->bit += 8;
-		} else if ( bits == 16 ) { ... }
-		else if ( bits==32 ) { ... }
-		else {
-			Com_Error( ERR_DROP, "can't write %d bits", bits );
-		}
+		if (com_protocol->integer > 48) {
+			// fast path: byte-aligned 8/16/32 writes
+			if ( bits == 8 ) { ... }
+			else if ( bits == 16 ) { ... }
+			else if ( bits==32 ) { ... }
+			else { MSG_Error(...); return; }
+		} else {
+			// slow path: bit-by-bit little-endian copy, loop for (i=0;i<bits;i++)
+			// supports arbitrary bit counts for ancient DM3 (proto 43-48)
+			if (bits > 32) { MSG_Error(...); return; }
+			byte ldata[4];
+			...
+			for (i = 0;  i < bits;  i++) {
+				// pack one bit at a time via BitValue/BitSet/BitClear macros
+			}
+		}
```
**Plain English:** For modern protocols (68, 73, 90, 91) wolfcam keeps the
fast byte-aligned Q3 writer. For ancient protocols (43-48) it falls back
to a per-bit loop because DM3 stores some fields at non-byte-multiple
bit widths.

**Port note for q3mme:** Protocol 73 uses the **same fast path** as
q3mme's existing proto-68. No change required for 73 in this function.
Only needed if q3mme wants to also parse DM3 (proto 43-48), which is a
stretch goal.

#### Patch 3: MSG_ReadBits forks similarly, with a 64-bit UDT fast path
```diff
@@ -198,29 +297,77 @@
-		if(bits==8) { ... }
-		else if(bits==16) { ... }
-		else if(bits==32) { ... }
-		else { Com_Error(ERR_DROP, ...); }
+		if (com_protocol->integer > 48) {
+			// same byte-aligned fast path as ioquake3
+		} else {
+			// from Uber Demo Tools
+			uint64_t readBits = *(const uint64_t*)&msg->data[msg->readcount];
+			// big-endian swap if needed
+			const uint64_t bitPosition = (uint64_t)msg->bit & 7;
+			const uint64_t diff = 64 - (uint64_t)bits;
+			readBits >>= bitPosition;
+			readBits <<= diff;
+			readBits >>= diff;
+			value = (int32_t)readBits;
+			msg->bit += bits;
+			msg->readcount = msg->bit >> 3;
+		}
```
**Plain English:** Same story as the writer — proto-73 uses fast path,
DM3 uses UDT's shift-based 64-bit read.

**Port note for q3mme:** Same as Patch 2. Protocol 73 requires zero bit-
layer change.

#### Patch 4: UTF-8-tolerant string encoders
```diff
-		if ( ((byte *)string)[i] > 127 || string[i] == '%' ) {
+		// UTF-8
+		if (com_protocol->integer < 91  &&  ((byte *)string)[i] > 127) {
+			string[i] = '.';
+		}
+		// ok to check each byte when parsing UTF-8 since '%' (0x25) isn't a valid UTF-8 byte
+		if (string[i] == '%') {
 			string[i] = '.';
 		}
```
**Plain English:** For protocols < 91 (which includes 73) wolfcam still
strips high-ASCII bytes because those configstrings are Latin-1. Only
protocol 91 passes UTF-8 bytes through. The `%` filter stays on all
protocols for format-string safety.

**Port note for q3mme:** For proto-73 playback, retain the Q3 behavior
(strip > 127). Only when/if q3mme adds proto-91 support does it need to
flip to UTF-8 passthrough. Patch affects `MSG_WriteString`,
`MSG_WriteBigString`, `MSG_ReadString`, `MSG_ReadBigString`,
`MSG_ReadStringLine`, `MSG_HashKey` — apply the same idiom to all six.

#### Patch 5: **Seven entityState delta-field tables**
The single `entityStateFields[]` from ioquake3 is replaced with seven
protocol-keyed tables. Listed in order they appear in wolfcam/msg.c:

1. `entityStateFieldsQldm91[]` — QL 91 (current). Adds `jumpTime`,
   `doubleJumped`, `health`, `armor`, `location` beyond Q3.
2. `entityStateFieldsQldm90[]` — QL 90. Adds `pos.gravity`, `apos.gravity`,
   `jumpTime`, `doubleJumped`.
3. **`entityStateFieldsQldm73[]` — PROTOCOL 73 (our target).** Identical
   to Q3 layout + two inserted fields: `pos.gravity` (32 bits) after
   `apos.trBase[0]`, and `apos.gravity` (32 bits) inserted after
   `apos.trDelta[2]`. No `jumpTime`/`doubleJumped`.
4. `entityStateFieldsQ3[]` — vanilla Q3 proto-68 field order.
5. `entityStateFieldsQ3dm43[]`, `Q3dm46[]`, `Q3dm48[]` — three DM3 variants
   for ancient demos (eFlags bit-width changes, `generic1` appears in 48).

The `entityStateFieldsQldm73[]` table (reproduced from
wolfcam `qcommon/msg.c` around line 1089):
```c
netField_t entityStateFieldsQldm73[] = {
    { NETF(pos.trTime), 32 },
    { NETF(pos.trBase[0]), 0 },
    { NETF(pos.trBase[1]), 0 },
    { NETF(pos.trDelta[0]), 0 },
    { NETF(pos.trDelta[1]), 0 },
    { NETF(pos.trBase[2]), 0 },
    { NETF(apos.trBase[1]), 0 },
    { NETF(pos.trDelta[2]), 0 },
    { NETF(apos.trBase[0]), 0 },
    { NETF(pos.gravity), 32 },           // NEW in proto 73
    { NETF(event), 10 },
    { NETF(angles2[1]), 0 },
    { NETF(eType), 8 },
    { NETF(torsoAnim), 8 },
    { NETF(eventParm), 8 },
    { NETF(legsAnim), 8 },
    { NETF(groundEntityNum), GENTITYNUM_BITS },
    { NETF(pos.trType), 8 },
    { NETF(eFlags), 19 },
    { NETF(otherEntityNum), GENTITYNUM_BITS },
    { NETF(weapon), 8 },
    { NETF(clientNum), 8 },
    { NETF(angles[1]), 0 },
    { NETF(pos.trDuration), 32 },
    { NETF(apos.trType), 8 },
    { NETF(origin[0]), 0 },
    { NETF(origin[1]), 0 },
    { NETF(origin[2]), 0 },
    { NETF(solid), 24 },
    { NETF(powerups), MAX_POWERUPS },
    { NETF(modelindex), 8 },
    { NETF(otherEntityNum2), GENTITYNUM_BITS },
    { NETF(loopSound), 8 },
    { NETF(generic1), 8 },
    { NETF(origin2[2]), 0 },
    { NETF(origin2[0]), 0 },
    { NETF(origin2[1]), 0 },
    { NETF(modelindex2), 8 },
    { NETF(angles[0]), 0 },
    { NETF(time), 32 },
    { NETF(apos.trTime), 32 },
    { NETF(apos.trDuration), 32 },
    { NETF(apos.trBase[2]), 0 },
    { NETF(apos.trDelta[0]), 0 },
    { NETF(apos.trDelta[1]), 0 },
    { NETF(apos.trDelta[2]), 0 },
    { NETF(apos.gravity), 32 },          // NEW in proto 73
    { NETF(time2), 32 },
    { NETF(angles[2]), 0 },
    { NETF(angles2[0]), 0 },
    { NETF(angles2[2]), 0 },
    { NETF(constantLight), 32 },
    { NETF(frame), 16 },
};
```
**Total fields: 52** (Q3 has 50; proto-73 adds 2 gravity fields).
Field count (`numFields`) determines the `lc` (last changed) byte written
on the wire, which means **swapping tables silently corrupts deltas** —
you MUST use the proto-73 table for proto-73 demos.

**Plain English:** Protocol 73 is "Q3 proto-68 plus per-entity gravity
trajectories." The gravity extension lets QL's physics apply custom gravity
to projectiles/players per-entity instead of via a global cvar. Field
positions 9 and 47 hold the new 32-bit integers.

**Port note for q3mme:** Add `entityStateFieldsQldm73[]` verbatim (with
the `int gravity` field added to `trajectory_t` in q_shared.h). The
existing q3mme `entityStateFields` is `entityStateFieldsQ3` under a
different name — keep that for proto-68 demos. Select via
`com_protocol` cvar.

#### Patch 6: MSG_WriteDeltaEntity protocol-aware dispatch
```diff
@@ -822,13 +1634,27 @@
-	numFields = ARRAY_LEN( entityStateFields );
+	if (com_protocol->integer >= 43  &&  com_protocol->integer <= 48) {
+		MSG_WriteDeltaEntityDM3(msg, from, to, force);
+		return;
+	}
+	if (com_protocol->integer == PROTOCOL_Q3) {
+		numFields = ARRAY_LEN(entityStateFieldsQ3);
+	} else if (com_protocol->integer == 73) {
+		numFields = ARRAY_LEN(entityStateFieldsQldm73);
+	} else if (com_protocol->integer == 90) {
+		numFields = ARRAY_LEN(entityStateFieldsQldm90);
+	} else {
+		numFields = ARRAY_LEN(entityStateFieldsQldm91);
+	}
```
Same pattern repeats inside the function when it picks the `field` pointer
(initial build of change vector, then the write-out loop).
Assertion `assert( numFields + 1 == sizeof(*from)/4 )` is **commented out**
because different tables pick different subsets of the struct — it no
longer holds.

**Plain English:** At demo playback time we're not writing, only reading.
But if q3mme ever re-emits (e.g. for Protocol-73-to-68 transcoding or
for the dm3-style scratch recorder), the write side is the inverse of
the read side and this dispatch is required.

**Port note for q3mme:** Port the dispatch, comment out the assert, keep
the MSG_WriteDeltaEntityDM3 branch only if DM3 is a scope goal
(fragmovie use: yes, for archival Q3 1.16 demos).

#### Patch 7: MSG_ReadDeltaEntity protocol-aware dispatch
```diff
@@ -939,9 +1950,17 @@
+	if (com_protocol->integer >= 43  &&  com_protocol->integer <= 48) {
+		MSG_ReadDeltaEntityDM3(msg, from, to, number);
+		return;
+	}
 	if ( msg->bit == 0 ) { ... }
-	numFields = ARRAY_LEN( entityStateFields );
+	if (com_protocol->integer == PROTOCOL_Q3) {
+		numFields = ARRAY_LEN(entityStateFieldsQ3);
+	} else if (com_protocol->integer == 73) {
+		numFields = ARRAY_LEN(entityStateFieldsQldm73);
+	} else if (com_protocol->integer == 90) {
+		numFields = ARRAY_LEN(entityStateFieldsQldm90);
+	} else {
+		numFields = ARRAY_LEN(entityStateFieldsQldm91);
+	}
 	lc = MSG_ReadByte(msg);
```
Plus: the `lc > numFields` check prints the protocol before erroring, and
both the "changed fields" loop and the "copy unchanged tail" loop select
the correct `field` pointer via the same ladder. The tail loop also gains
defensive bound: `for ( i = lc; i < numFields && i >= 0; i++, field++)`.

**Plain English:** This is THE function q3mme must get right for demo
playback. Every snapshot frame calls it N times (N = number of visible
entities, typically 40-80). Getting the wrong field table = ragdoll
entities teleporting everywhere.

**Port note for q3mme:** Copy this function wholesale. It's the minimum
viable proto-73 reader.

#### Patch 8: Three playerState delta-field tables
Same pattern as entityState. The key insight for proto-73:
- `playerStateFieldsQldm91[]` — 58 fields, includes crouch/fov/move.
- `playerStateFieldsQldm90[]` — 48 fields.
- **`playerStateFieldsQ3[]` — this is used by BOTH proto-68 AND proto-73.**
  The wolfcam dispatch: `else { field = playerStateFieldsQ3; } // also qldm 73`
  (see `qcommon/msg.c:2626`).

**CRITICAL:** Unlike entityState, protocol 73's playerState layout is
**identical to Q3 proto-68's** (no `doubleJumped`, no `jumpTime` in PS —
those are QL 90+ only).

```c
netField_t playerStateFieldsQ3[] = {
    { PSF(commandTime), 32 },
    { PSF(origin[0]), 0 },
    { PSF(origin[1]), 0 },
    { PSF(bobCycle), 8 },
    { PSF(velocity[0]), 0 },
    { PSF(velocity[1]), 0 },
    { PSF(viewangles[1]), 0 },
    { PSF(viewangles[0]), 0 },
    { PSF(weaponTime), -16 },           // negative = signed
    { PSF(origin[2]), 0 },
    { PSF(velocity[2]), 0 },
    { PSF(legsTimer), 8 },
    { PSF(pm_time), -16 },
    { PSF(eventSequence), 16 },
    { PSF(torsoAnim), 8 },
    { PSF(movementDir), 4 },
    { PSF(events[0]), 8 },
    { PSF(legsAnim), 8 },
    { PSF(events[1]), 8 },
    { PSF(pm_flags), 24 },
    { PSF(groundEntityNum), GENTITYNUM_BITS },
    { PSF(weaponstate), 4 },
    { PSF(eFlags), 16 },
    { PSF(externalEvent), 10 },
    { PSF(gravity), 16 },
    { PSF(speed), 16 },
    { PSF(delta_angles[1]), 16 },
    { PSF(externalEventParm), 8 },
    { PSF(viewheight), -8 },
    { PSF(damageEvent), 8 },
    { PSF(damageYaw), 8 },
    { PSF(damagePitch), 8 },
    { PSF(damageCount), 8 },
    { PSF(generic1), 8 },
    { PSF(pm_type), 8 },
    { PSF(delta_angles[0]), 16 },
    { PSF(delta_angles[2]), 16 },
    { PSF(torsoTimer), 12 },
    { PSF(eventParms[0]), 8 },
    { PSF(eventParms[1]), 8 },
    { PSF(clientNum), 8 },
    { PSF(weapon), 5 },
    { PSF(viewangles[2]), 0 },
    { PSF(grapplePoint[0]), 0 },
    { PSF(grapplePoint[1]), 0 },
    { PSF(grapplePoint[2]), 0 },
    { PSF(jumppad_ent), 10 },           // was GENTITYNUM_BITS; forced to 10
    { PSF(loopSound), 16 },
};
```
**Total fields: 48.** Two diffs from ioquake3's single `playerStateFields[]`:
- `externalEvent`: was 10 bits in ioquake3 (same in wolfcam Q3 table); in
  wolfcam this is 10 across the board — matches.
- `jumppad_ent`: ioquake3 uses `GENTITYNUM_BITS` (10 on Q3), wolfcam
  hard-codes to `10`. Functionally identical when GENTITYNUM_BITS==10.

**Plain English:** Protocol 73's playerState is wire-compatible with
proto-68. A correct proto-73 reader can literally reuse the proto-68
playerState field table.

**Port note for q3mme:** The lowest-cost proto-73 port is: keep q3mme's
existing playerState reader verbatim, and only add the proto-73
entityState table + dispatch. **This is the single most important
insight in this document for porting effort estimation.**

#### Patch 9: MSG_WriteDeltaPlayerstate / MSG_ReadDeltaPlayerstate dispatch

```diff
-	numFields = ARRAY_LEN( playerStateFields );
+	if (com_protocol->integer == 90) {
+		numFields = ARRAY_LEN(playerStateFieldsQldm90);
+	} else if (com_protocol->integer == 91) {
+		numFields = ARRAY_LEN(playerStateFieldsQldm91);
+	} else {  // also qldm 73
+		numFields = ARRAY_LEN(playerStateFieldsQ3);
+	}
```
Identical dispatch pattern inside read (`MSG_ReadDeltaPlayerstate`) plus
defensive bound on tail-copy loop.

DM3 protocols (43-48) go through separate `MSG_WriteDeltaPlayerstateDM3`
/ `MSG_ReadDeltaPlayerstateDM3` functions which use a one-bit-per-field
changed mask (instead of the Q3/QL lc-byte + per-field-bit scheme) plus
explicit stats/persistant/ammo/powerups arrays.

**Plain English:** Reader just picks the right table based on protocol
and runs the generic delta engine. The generic engine is unchanged.

**Port note for q3mme:** 10 lines of dispatch. Trivial.

#### Patch 10: MSG_ReadDeltaPlayerstate end-of-record QL 91 trailer (stub)
```diff
+	//FIXME testing
+	if (com_protocol->integer == 91) {
+		//FIXME where do these go?
+		//MSG_ReadBits(msg, 7);
+	}
```
**Plain English:** Author flags unknown trailing bits in QL 91; currently
disabled. Proto-73 is untouched.

**Port note for q3mme:** Ignore for proto-73. Revisit if/when porting QL 91.

---

### qcommon/q_shared.h

**Purpose:** Shared client/server types (vectors, trajectory, entityState,
playerState, connstate, font glyphs, player stats).

**Why patched:** Struct expansion to hold QL fields that the wire-format
delta tables reference. **For protocol 73 only one of these additions is
load-bearing: `trajectory_t.gravity`** (referenced by
`entityStateFieldsQldm73`).

#### Patch 1: trajectory_t gains gravity
```diff
@@ -1260,9 +1386,11 @@
 typedef struct {
 	trType_t	trType;
 	int		trTime;
+	//double trTimef;  // hack for fx scripts
 	int		trDuration;
 	vec3_t	trBase;
 	vec3_t	trDelta;
+	int		gravity;
 } trajectory_t;
```
**Plain English:** Every entity's linear (`pos`) and angular (`apos`)
trajectory now carries its own gravity integer. Needed because
`entityStateFieldsQldm73` includes `pos.gravity` and `apos.gravity` as
offsets into this struct.

**Port note for q3mme:** REQUIRED. Without this field the
`(byte*)&entity->pos + offsetof(pos.gravity)` delta-write/read will clobber
adjacent memory. Must be added even though q3mme's own server code
never touches `gravity` — it only needs to exist as a storage slot for the
reader to deposit into.

#### Patch 2: playerState_t QL fields (NOT NEEDED FOR PROTO-73)
```diff
@@ -1202,6 +1300,34 @@
 	int		jumppad_frame;
 	int		entityEventSequence;
+	// ql protocol 90
+	qboolean doubleJumped;
+	int jumpTime;
+	// ql protocol 91
+	int crouchTime;
+	int crouchSlideTime;
+	int location;
+	int fov;
+	int forwardmove;
+	int rightmove;
+	int upmove;
+	int weaponPrimary;
 } playerState_t;
```
**Plain English:** Fields only referenced by protocols 90 and 91
playerState tables. Protocol 73 reader doesn't read them.

**Port note for q3mme:** Skip for pure proto-73 scope. Add them later if
extending to QL 90/91.

#### Patch 3: entityState_t QL fields (NOT NEEDED FOR PROTO-73)
```diff
@@ -1314,12 +1442,31 @@
 	int		generic1;
+	// ql protocol 90
+	int jumpTime;
+	qboolean doubleJumped;
+	// ql protocol 91
+	int health;
+	int armor;
+	int location;
 } entityState_t;
```
**Plain English:** Same story — QL 90/91 entityState extras. Proto-73
ignores them because `entityStateFieldsQldm73` doesn't list them.

**Port note for q3mme:** Skip for pure proto-73 scope.

#### Patch 4: connstate_t CA_DOWNLOADINGWORKSHOPS
```diff
 	CA_AUTHORIZING,
+	CA_DOWNLOADINGWORKSHOPS,
 	CA_CONNECTING,
```
**Plain English:** QL has a pre-connect phase for downloading map
workshops. Irrelevant for demo playback (demos already contain all
content they need).

**Port note for q3mme:** Skip. Or add with a no-op.

Other q_shared.h additions (MAX_FONTS, fontInfo_t expansion, additional
MAX_MASTER_SERVERS etc.) are wolfcam render/font infrastructure —
document under "harness", not "protocol 73."

---

### game/bg_public.h

**Purpose:** Shared game/cgame types. Holds the `entity_event_t` enum
(EV_\*), weapon indices, powerup indices, configstring layout.

**Why patched:** QL renumbers the event enum (EV_OBITUARY is 58 in
QL; 57 in Q3 proto-68). Wolfcam preserves BOTH by renaming the Q3 enum to
`entityEventQ3_t` / `EVQ3_*`, adds the ancient Q3 1.16 enum as
`EVQ3DM3_*`, and makes `entity_event_t` / `EV_*` the current QL numbering.

Configstring indices are redefined for QL (CS_PLAYERS = 529) while Q3
versions are preserved as `CSQ3_PLAYERS` etc.

#### Patch 1: Three parallel event enums

Wolfcam `bg_public.h` contains, in order:
- `entity_event_t { EV_NONE, EV_FOOTSTEP=1, ..., EV_OBITUARY=58, ..., EV_NEW_HIGH_SCORE=99 }`
  — current QL numbering. Values up to 99, with gaps marked "guess"
  (wolfcam authors reverse-engineered from live demos).
- `typedef enum { EVQ3_NONE, EVQ3_FOOTSTEP, ... EVQ3_OBITUARY, ... } entity_eventQ3_t;`
  — Q3 proto-66..71 numbering.
- `typedef enum { ..., EVQ3DM3_OBITUARY, // 58 ... } entity_eventQ3dm3_t;`
  — Q3 proto-43..48 (1.16) numbering.

**Plain English:** A snapshot's entity `event` field is an 8-bit integer.
Its meaning depends on the demo's protocol. Wolfcam maintains three
parallel enums and translates at the cgame layer when firing visual/audio
FX.

**Port note for q3mme:** For proto-73 scope, add the QL `entity_event_t`
enum verbatim. Keep q3mme's existing Q3 enum but rename its symbols to
`EVQ3_*` to avoid collision — OR keep them and do the event-number
translation in the demo reader. The `.dm_73` deep-dive doc lists which
event numbers matter for fragmovie work (EV_OBITUARY=58 is THE key one).

For PROTO-73-SPECIFIC handling: proto-73 uses the QL enum (EV_OBITUARY=58).
Confirm via `client/cl_main.c:2078` which dispatches obituary events:
```c
if (((di.protocol == PROTOCOL_QL || di.protocol == 73 || di.protocol == 90)
     && event == EV_OBITUARY)
    || ((di.protocol <= 71 && di.protocol >= 48) && event == EVQ3_OBITUARY)
    || (di.protocol < 48 && event == EVQ3DM3_OBITUARY)) { ... }
```

#### Patch 2: Configstring layout (CS_\* vs CSQ3_\*)

Wolfcam defines QL constants like:
- `CS_MODELS 17`, `CS_SOUNDS 274`, `CS_PLAYERS 529`, `CS_LOCATIONS 593`,
  `CS_PARTICLES (CS_LOCATIONS+MAX_LOCATIONS) = 657`, `CS_FLAGSTATUS 658`,
  `CS_FIRSTPLACE 659`, `CS_SECONDPLACE 660`, `CS_ROUND_STATUS 661`,
  `CS_ROUND_TIME 662`, `CS_SHADERSTATE 665`, ...

Meanwhile Q3 indices live in `CSQ3_MODELS`, `CSQ3_SOUNDS`, `CSQ3_PLAYERS`
etc. (grep `CSQ3_` in the file to get the full Q3 table.)

**Plain English:** Configstrings are the server → client info channel
(map name, player names, scores). QL re-laid them out because it added
new game-mode state (round timer, particle strings, workshop state). The
indices are completely incompatible with Q3.

**Port note for q3mme:** Port the QL CS_\* constants. Then every place
that indexes a configstring based on demo protocol must pick the right
constant — either via `#ifdef` (hard-coded playback mode) or via runtime
`com_protocol` branch (mixed-demo mode). For minimum viable proto-73
playback, extract only the constants the cgame actually reads:
`CS_PLAYERS`, `CS_SCORES1`, `CS_SCORES2`, `CS_LEVEL_START_TIME`,
`CS_INTERMISSION`, `CS_FLAGSTATUS`, `CS_ROUND_STATUS`, `CS_ROUND_TIME`.

#### Patch 3: Expanded weapon / powerup / mean-of-death enums
Wolfcam adds `WP_NAILGUN`, `WP_PROX_LAUNCHER`, `WP_CHAINGUN`, `WP_HMG`
(heavy machine gun) to the `weapon_t` enum, and extends `meansOfDeath_t`
with QL-specific MODs (`MOD_NAIL`, `MOD_CHAINGUN`, `MOD_PROXIMITY_MINE`,
`MOD_KAMIKAZE`, `MOD_JUICED`, `MOD_GRAPPLE`, `MOD_SWITCH_TEAMS`,
`MOD_THAW`, `MOD_LIGHTNING_DISCHARGE`, `MOD_HMG`, `MOD_RAILGUN_HEADSHOT`).

**Plain English:** Necessary so obituary events can report cause-of-death
correctly.

**Port note for q3mme:** Port the full enum extension. A proto-73 demo may
contain any of these weapon/MOD codes in `obituary.eventParm` and if the
cgame doesn't know them it draws `?` for the weapon icon.

---

### client/cl_parse.c

**Purpose:** Client-side packet parser. Dispatches `svc_*` commands,
processes gamestate/snapshot/download/voip messages, maintains demo-
record file state.

**Why patched:** Extensive. The file doubled from 25,800 bytes to 71,334
bytes. Most additions are demo-replay support (`.dm_73` protocol sniff,
configstring interpretation per protocol, speed/pause controls, CS_\* vs
CSQ3_\* switching) plus workshop downloading code that proto-73 reader
doesn't need.

**Proto-73-relevant patches only:**

#### Patch 1: Protocol sniff from gamestate "protocol" serverinfo
```c
// cl_parse.c around :964-1038
if (p == PROTOCOL_Q3) {
    Cvar_Set("protocol", va("%d", PROTOCOL_Q3));
} else if (p == 73) {  // FIXME define
    Cvar_Set("protocol", "73");
} else if (p == PROTOCOL_QL) {
    Cvar_Set("protocol", va("%d", PROTOCOL_QL));
}
...
if (protocol >= 91) { /* QL 91 specific */ }
```
**Plain English:** First thing in the gamestate is a `protocol` key in
serverinfo. Wolfcam sets the global `com_protocol` cvar based on that
value, and every downstream msg.c dispatch keys off it.

**Port note for q3mme:** Critical. Without this sniff, q3mme would use
whatever `com_protocol` defaults to and mis-parse everything. The sniff
must happen BEFORE the first `svc_snapshot` is read.

#### Patch 2: Per-protocol configstring reader
```c
// cl_parse.c around :1774-1872
if ( ((di.protocol == PROTOCOL_QL || di.protocol == 73 || di.protocol == 90)
      && (csnum >= CS_PLAYERS && csnum < (CS_PLAYERS + MAX_CLIENTS)))
    || (di.protocol <= PROTOCOL_Q3
        && (csnum >= CSQ3_PLAYERS && csnum < (CSQ3_PLAYERS + MAX_CLIENTS)))
   ) {
    // this is a player-info configstring — parse name, clan, model
    if (di.protocol == PROTOCOL_QL || di.protocol == 73 || di.protocol == 90) {
        /* parse QL player string format (n\name\t\team\c\clan\...) */
    } else if (di.protocol <= PROTOCOL_Q3) {
        /* parse Q3 player string format */
    }
}
```
**Plain English:** The same `configstring number N` command means
"player 0's info" on proto-73 (N=529) or "player 0's info" on proto-68
(N=544). Wolfcam normalizes by branching.

**Port note for q3mme:** q3mme already parses Q3 configstrings. Add the
QL branch for proto-73 (same format as QL 90/91 — the user-info key/value
string format is stable from 73 onward).

#### Patch 3: svc_voip / svc_extension tolerance
The parser must accept (and either process or skip) new opcodes
`svc_voip = 9` and `svc_extension = 8`. For proto-73 playback, both can
be silent-skip:
```c
case svc_voip:
    // read and discard: sender(short) + generation(byte) + sequence(long)
    //                   + frames(byte) + packetsize(short) + data(packetsize)
    break;
case svc_extension:
    // followed by another svc_* — recurse one level
    break;
```

**Port note for q3mme:** If q3mme crashes on unknown opcodes, add these
two stubs. Minimum viable path is "skip VOIP payload, parse next opcode."

Other cl_parse.c additions (workshop download progress, demo-record
re-muxing, broken-demo recovery paths) are Wolfcam replay infrastructure,
not proto-73 wire semantics per se.

---

### client/cl_cgame.c

**Purpose:** VM bridge between engine and cgame DLL/QVM. Marshals
snapshot structs over the trap_*/syscall interface.

**Why patched:** Cgame VM ABI is protocol-agnostic on the struct side
(cgame receives a fully-decoded snapshot, not raw bits), so most diffs
here are wolfcam's own FX/camera features (free cam, slow-mo, ghost
rendering) — NOT proto-73 wire changes.

**Proto-73-relevant:** zero direct branches on `== 73`. The cgame
consumes whatever msg.c produced, so as long as the entityState and
playerState structs round-trip correctly, cgame is happy.

**Port note for q3mme:** No protocol-73 work required in the cgame
bridge. Wolfcam's cgame additions are scope-creep (capture framework,
wolfcam-specific cvars) and are documented in `03-wolfcam-cg-features.md`
(TBD), not here.

---

### server/sv_snapshot.c

**Purpose:** Server side only. Builds snapshots to send to connected
clients.

**Why patched:** Two minor things — `sv_broadcastAll` cvar lets the
server bypass PVS for debugging, and `svc_voip` renamed from
`svc_voipOpus`. Neither is proto-73-specific.

> For demo REPLAY (wolfcam's scope) this file is irrelevant. q3mme
> doesn't need to patch it for proto-73 playback.

---

## Append: structs to mirror in any port

Exact field list + bit widths that a proto-73-capable reader must
replicate. Sources: `qcommon/q_shared.h`, wolfcam-patched.

### `trajectory_t` (48 bytes after patch)
```c
typedef enum {
    TR_STATIONARY, TR_INTERPOLATE, TR_LINEAR, TR_LINEAR_STOP,
    TR_SINE, TR_GRAVITY
} trType_t;

typedef struct {
    trType_t  trType;        // 4 bytes (enum as int)
    int       trTime;        // 4
    int       trDuration;    // 4
    vec3_t    trBase;        // 12 (3 × float)
    vec3_t    trDelta;       // 12
    int       gravity;       // 4  ← PROTO-73 REQUIRED
} trajectory_t;
// sizeof = 40 bytes
```

### `entityState_t` (minimum for proto-73, ignoring QL 90/91 fields)
Fields referenced by `entityStateFieldsQldm73`:
```
pos             trajectory_t   (contains gravity, referenced as pos.gravity)
apos            trajectory_t   (contains gravity, referenced as apos.gravity)
time            int
time2           int
origin          vec3_t
origin2         vec3_t
angles          vec3_t
angles2         vec3_t
otherEntityNum  int  (10 bits on wire)
otherEntityNum2 int  (10 bits)
groundEntityNum int  (10 bits)
constantLight   int  (32)
loopSound       int  (8)
modelindex      int  (8)
modelindex2     int  (8)
frame           int  (16)
clientNum       int  (8)
solid           int  (24)
event           int  (10)
eventParm       int  (8)
powerups        int  (MAX_POWERUPS = 16 bits)
weapon          int  (8)
legsAnim        int  (8)
torsoAnim       int  (8)
generic1        int  (8)
eFlags          int  (19)
eType           int  (8)
number          int  (NOT in field table — transmitted separately via GENTITYNUM_BITS)
```
Field count: 52 entries in the delta table (vs Q3's 50 — the two
gravity fields are the difference).

### `playerState_t` (proto-73 — SAME AS PROTO-68)
Uses `playerStateFieldsQ3[]` — see Patch 8 above for the full 48-entry
list. No proto-73-specific fields. Use the same struct as q3mme already
has.

### MAX_\* constants referenced by proto-73 delta code
```c
#define MAX_CLIENTS          64    // (Q3 = 64, QL = 64 — unchanged)
#define MAX_GENTITIES        1024  // unchanged
#define GENTITYNUM_BITS      10
#define MAX_POWERUPS         16
#define MAX_WEAPONS          16
#define MAX_STATS            16
#define MAX_PERSISTANT       16
#define MAX_MODELS           256
#define MAX_SOUNDS           256
#define MAX_CONFIGSTRINGS    1024  // QL uses full 1024; Q3 used 1024 also but
                                   // laid out differently
```
None of these numerical values changed between Q3 and QL — it's the
**offsets inside the configstring range** that changed, not the range
size.

### Configstrings a proto-73 cgame reads (minimum set for fragmovies)
```c
CS_SERVERINFO          0    // contains "protocol" key — sniff here
CS_SYSTEMINFO          1
CS_MUSIC               2
CS_MESSAGE             3
CS_MOTD                4
CS_WARMUP              5
CS_SCORES1             6
CS_SCORES2             7
CS_LEVEL_START_TIME    13
CS_INTERMISSION        14
CS_ITEMS               15
CS_MODELS              17   // QL: 17..272 (was Q3 32..287)
CS_SOUNDS              274  // QL: 274..529
CS_PLAYERS             529  // QL: 529..592 (64 players)
CS_LOCATIONS           593  // QL: 593..656
CS_FLAGSTATUS          658
CS_ROUND_STATUS        661
CS_ROUND_TIME          662
CS_RED_PLAYERS_LEFT    663
CS_BLUE_PLAYERS_LEFT   664
```

---

## Porting summary (bullet form for `06-protocol-73-port-plan.md`)

1. **Zero-risk lifts:** `huffman.c`, `net_chan.c`, `sv_snapshot.c` — copy
   nothing. q3mme's equivalents are fine.
2. **Required single-line bumps in `qcommon.h`:**
   - `#define MAX_MSGLEN 32768` (was 16384)
   - Add `demo_protocols[]` list + NUM_DEMO_PROTOCOLS
   - Add `svc_voip`, `svc_extension` enum values (or verify ordinals match)
3. **Required struct additions in `q_shared.h`:**
   - `trajectory_t.gravity` (int)
   - That's it for proto-73. (Skip QL 90/91 additions.)
4. **Required msg.c work:**
   - Add `entityStateFieldsQldm73[]` verbatim from Patch 5.
   - Add `com_protocol` cvar sniff + dispatch in `MSG_WriteDeltaEntity` and
     `MSG_ReadDeltaEntity`.
   - Keep playerState reader unchanged — proto-73 uses the existing
     proto-68 table.
   - Add `MSG_Error` soft-failure path gated by `com_brokenDemo` cvar.
5. **Required bg_public.h work:**
   - Add QL `entity_event_t` enum (95+ values). Preserve q3mme's existing
     enum as `entityEventQ3_t` / `EVQ3_*`.
   - Add QL configstring constants `CS_*` (see list above).
   - Extend `weapon_t` and `meansOfDeath_t` enums with QL entries.
6. **Required cl_parse.c work:**
   - Protocol sniff from first gamestate.
   - Configstring dispatch: QL indices for proto-73/90/91, Q3 indices for
     proto-68 and below.
   - svc_voip / svc_extension silent-skip.
7. **Cgame bridge:** nothing required for wire compat. Rendering/UI of
   new events is a separate concern.

**Estimated LOC for minimum-viable proto-73 port into q3mme:**
~400 LOC in msg.c, ~50 LOC in q_shared.h, ~200 LOC in bg_public.h (mostly
enum definitions), ~150 LOC in cl_parse.c. Total ~800 LOC of real code
plus the `entity_event_t` / `CS_*` constant tables.

This is tractable. The `entityStateFieldsQldm73[]` table IS the gold.
