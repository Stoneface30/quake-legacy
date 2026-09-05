"""Write a .dm_73 Quake Live demo. The inverse of `demo_parse.py`.

WHY THIS EXISTS. The Clan Arena explainer needs a round we control exactly:
known teams, known positions, a kill happening where the camera is looking,
and not one synthetic event touching career statistics. Synthesis is the only
route that gives choreography rather than hope.

WHAT MAKES IT TRACTABLE. `demo_parse.py` seeds the Q3 Huffman tree once and
never updates it -- `receive()` does not call `add_ref()`. The tree is STATIC,
so encoding is a precomputed code table walked from each symbol to the root,
byte-exact with the reader by construction rather than by agreement.

THE FIELD MODEL. States are dicts keyed by the FIELD INDEX, exactly as the
parser returns them (`{5: 1024.0, 18: 1}`), and the bit widths are imported
from the parser rather than restated. Naming the fields here would create a
second table to drift; the parser's index IS the contract, which also makes a
round-trip comparison a plain dict equality.

TWO ENCODINGS, NOT ONE. An entity integer field is prefixed by a "non-zero"
bit; a playerstate integer field is NOT -- it is written directly. An entity
float carries a non-zero bit then a small-int flag; a playerstate float
carries only the small-int flag. Getting this wrong desyncs the bitstream for
the rest of the packet, which is why each is written out separately below
rather than sharing a clever helper.

Byte order is little-endian throughout, matching msg.c.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from engine.parser.demo_parse import (
    _ES_BITS, _F_CLIENT, _F_EFLAGS, _F_ETYPE, _F_EVENT, _F_EVPARM, _F_GROUND,
    _F_KILLER, _F_PITCH, _F_POS_X, _F_POS_Y, _F_POS_Z, _F_VEL_X, _F_VEL_Y,
    _F_VEL_Z, _F_VICTIM, _F_WEAPON, _F_YAW, _FLOAT_INT_BIAS, _FLOAT_INT_BITS,
    _GENTITYNUM_BITS, _MAX_PERSISTANT, _MAX_POWERUPS, _MAX_STATS,
    _MAX_WEAPONS, _PS_BITS, _SENTINEL, _ET_EVENTS, _EV_OBITUARY, _get_huff)

# ── container (docs/reference/dm73-format-deep-dive.md §1) ──────────────────
DEMO_EOF = -1

SVC_BAD = 0
SVC_NOP = 1
SVC_GAMESTATE = 2
SVC_CONFIGSTRING = 3
SVC_BASELINE = 4
SVC_SERVERCOMMAND = 5
SVC_DOWNLOAD = 6
SVC_SNAPSHOT = 7
SVC_EOF = 8

MAX_CONFIGSTRINGS = 1024
CS_SERVERINFO = 0
CS_SYSTEMINFO = 1
CS_PLAYERS = 529
ENTITYNUM_NONE = 1023

# Entity field indices. IMPORTED from the parser, never restated.
#
# The first version of this module invented them -- position at 5/6/7, eType at
# 18, clientNum at 28 -- and every round-trip test passed, because the tests
# compared those indices against themselves. The engine received players whose
# eType landed in eFlags and whose position landed in velocity, and drew
# nothing. There is exactly one authority for these numbers and it is
# `demo_parse`, which reads 4,292 real demos with them.
ES_POS_X = _F_POS_X            # 1  pos.trBase[0]
ES_POS_Y = _F_POS_Y            # 2  pos.trBase[1]
ES_POS_Z = _F_POS_Z            # 5  pos.trBase[2]
ES_VEL_X = _F_VEL_X            # 3  pos.trDelta[0]
ES_VEL_Y = _F_VEL_Y            # 4  pos.trDelta[1]
ES_VEL_Z = _F_VEL_Z            # 7  pos.trDelta[2]
ES_APOS_YAW = _F_YAW           # 6  apos.trBase[1]
ES_APOS_PITCH = _F_PITCH       # 8  apos.trBase[0]
ES_EVENT = _F_EVENT            # 10
ES_ETYPE = _F_ETYPE            # 12
ES_EVENTPARM = _F_EVPARM       # 14
ES_GROUND = _F_GROUND          # 16 groundEntityNum; 1023 = airborne
ES_EFLAGS = _F_EFLAGS          # 18
ES_OTHER_ENT = _F_VICTIM       # 19 otherEntityNum  (obituary victim)
ES_WEAPON = _F_WEAPON          # 20
ES_CLIENTNUM = _F_CLIENT       # 21
ES_OTHER_ENT2 = _F_KILLER      # 31 otherEntityNum2 (obituary killer)

PS_ORIGIN_X, PS_ORIGIN_Y, PS_ORIGIN_Z = 1, 2, 9
PS_VEL_X, PS_VEL_Y, PS_VEL_Z = 4, 5, 10
PS_YAW, PS_PITCH = 6, 7
PS_EVENT_SEQ = 13
PS_EVENT0, PS_EVENT1 = 16, 18
PS_GROUND = 20
PS_EVPARM0, PS_EVPARM1 = 38, 39
PS_CLIENTNUM = 40
PS_WEAPON = 41

STAT_HEALTH = 0
STAT_ARMOR = 4

ET_GENERAL = 0
ET_PLAYER = 1

# ── animation, learned from real players ────────────────────────────────────
# Fields 13 and 15 are the two animation slots. Not guessed: `ca_reference`
# profiled real rendered players across five demos and found 13 carrying
# {7, 9, 10, 11} and 15 carrying {15, 16, 18, 19, 22}, each also appearing
# +128. Read against Q3's animNumber_t those are exactly the torso set
# (ATTACK, DROP, RAISE, STAND) and the legs set (RUN, BACK, JUMP, LAND, IDLE),
# and 128 is ANIM_TOGGLEBIT.
#
# The first synthetic players were built with torso 7 and legs 15+128 held
# constant, i.e. permanently mid-attack and mid-run, which is why they read as
# frozen.
ES_TORSO_ANIM = 13
ES_LEGS_ANIM = 15

ANIM_TOGGLE = 128

TORSO_ATTACK = 7
TORSO_DROP = 9
TORSO_RAISE = 10
TORSO_STAND = 11

LEGS_RUN = 15
LEGS_BACK = 16
LEGS_JUMP = 18
LEGS_LAND = 19
LEGS_IDLE = 22


def anim(value: int, toggle: bool = False) -> int:
    """An animation number, optionally with the restart bit flipped.

    A repeated animation only replays when the toggle bit changes -- the same
    mechanism EV_EVENT_BIT1/BIT2 provide for events. Firing twice without
    flipping it plays once.
    """
    return value | (ANIM_TOGGLE if toggle else 0)

# An event arrives as a TEMP ENTITY whose eType is ET_EVENTS + the event code.
# Both numbers come from the parser, not from memory: the first draft of this
# module had EV_OBITUARY at 60.
ET_EVENTS = _ET_EVENTS         # 13
EV_OBITUARY = _EV_OBITUARY     # 58

# Event entities carry two toggle bits so two identical consecutive events can
# be told apart. The parser masks them off with `& ~0x300` and compares the RAW
# value, so a second obituary at the same entity slot must flip one or it is
# read as a repeat of the first and dropped.
EV_TOGGLE_BITS = 0x300


def obituary_entity(killer: int, victim: int, mod: int,
                    pos: tuple[float, float, float],
                    *, toggle: int = 0) -> dict[int, float]:
    """A death, in the shape the engine actually emits.

    Taken from real obituary deltas in the corpus, which look like
    `{1: x, 2: y, 5: z, 12: 71, 14: mod, 19: victim, 31: killer}` -- eType 71
    being ET_EVENTS + EV_OBITUARY.
    """
    x, y, z = pos
    return {
        ES_ETYPE: ET_EVENTS + EV_OBITUARY + (EV_TOGGLE_BITS & toggle),
        ES_POS_X: x, ES_POS_Y: y, ES_POS_Z: z,
        ES_EVENTPARM: mod,
        ES_OTHER_ENT: victim,
        ES_OTHER_ENT2: killer,
    }


# ── the code table ──────────────────────────────────────────────────────────

_CODES: list[tuple[int, int]] | None = None


def _build_codes() -> list[tuple[int, int]]:
    """Bit path root->leaf for each symbol, from the reader's own seeded tree.

    Emitted least-significant-bit-first, matching how `receive` consumes them:
    it takes `node.left` on a 0 bit and `node.right` on a 1, reading bits in
    ascending order within each byte.
    """
    huff = _get_huff()
    out: list[tuple[int, int]] = [(0, 0)] * 256
    for sym in range(256):
        node = huff.loc[sym]
        if node is None:                          # pragma: no cover - seeded
            raise RuntimeError(f"symbol {sym} absent from the seeded tree")
        path: list[int] = []
        while node.parent is not None:
            path.append(1 if node.parent.right is node else 0)
            node = node.parent
        path.reverse()
        value = 0
        for i, b in enumerate(path):
            value |= b << i
        out[sym] = (value, len(path))
    return out


def codes() -> list[tuple[int, int]]:
    global _CODES
    if _CODES is None:
        _CODES = _build_codes()
    return _CODES


# ── bit writer ──────────────────────────────────────────────────────────────

class BitWriter:
    """The mirror of `demo_parse._Bits`.

    PINNED LAYER. The exhaustive round-trip tests over all 256 symbols, every
    width 1-32 and a mixed primitive stream exist because everything above
    this is undebuggable if a single bit is misplaced. Do not refactor without
    them passing.
    """

    __slots__ = ("_buf", "_bit")

    def __init__(self) -> None:
        self._buf = bytearray()
        self._bit = 0

    def _put_raw_bit(self, b: int) -> None:
        if self._bit >> 3 >= len(self._buf):
            self._buf.append(0)
        if b:
            self._buf[self._bit >> 3] |= 1 << (self._bit & 7)
        self._bit += 1

    def _put_symbol(self, sym: int) -> None:
        value, length = codes()[sym & 0xFF]
        for i in range(length):
            self._put_raw_bit((value >> i) & 1)

    def writebits(self, value: int, n: int) -> None:
        """The low `n & 7` bits go out raw; the rest as Huffman bytes, LSB
        first -- exactly the split `readbits` performs."""
        value &= (1 << n) - 1
        nbits = n & 7
        for i in range(nbits):
            self._put_raw_bit((value >> i) & 1)
        rem = n - nbits
        shift = nbits
        while rem > 0:
            self._put_symbol((value >> shift) & 0xFF)
            shift += 8
            rem -= 8

    def writebyte(self, v: int) -> None:
        self._put_symbol(v & 0xFF)

    def writeshort(self, v: int) -> None:
        v &= 0xFFFF
        self._put_symbol(v & 0xFF)
        self._put_symbol((v >> 8) & 0xFF)

    def writelong(self, v: int) -> None:
        v &= 0xFFFFFFFF
        for i in range(4):
            self._put_symbol((v >> (8 * i)) & 0xFF)

    def writefloat(self, v: float) -> None:
        for b in struct.pack("<f", float(v)):
            self._put_symbol(b)

    def writestring(self, s: str) -> None:
        for ch in s.encode("latin-1", errors="replace"):
            self._put_symbol(ch)
        self._put_symbol(0)

    def bytes(self) -> bytes:
        return bytes(self._buf)


def _is_small_int(v: float) -> bool:
    """Does this float fit the 13-bit biased-integer short form?"""
    t = int(v)
    return float(v) == float(t) and 0 <= t + _FLOAT_INT_BIAS < (1 << _FLOAT_INT_BITS)


# ── entity delta ────────────────────────────────────────────────────────────

def write_entity_delta(w: BitWriter, from_state: Mapping[int, float],
                       to_state: Mapping[int, float] | None) -> None:
    """One packet entity.

    `to_state=None` writes the removal bit. An empty change set writes the
    no-delta form, which is one bit instead of a field sweep.
    """
    if to_state is None:
        w.writebits(1, 1)                      # removed
        return
    w.writebits(0, 1)

    changed = [i for i in range(len(_ES_BITS))
               if from_state.get(i, 0) != to_state.get(i, 0)]
    if not changed:
        w.writebits(0, 1)                      # no delta
        return
    w.writebits(1, 1)

    last = changed[-1] + 1
    w.writebyte(last)
    for i in range(last):
        if i not in changed:
            w.writebits(0, 1)
            continue
        w.writebits(1, 1)
        value = to_state.get(i, 0)
        if _ES_BITS[i] == 0:                   # float field
            if value == 0:
                w.writebits(0, 1)              # zero: nothing follows
            else:
                w.writebits(1, 1)
                if _is_small_int(value):
                    w.writebits(0, 1)
                    w.writebits(int(value) + _FLOAT_INT_BIAS, _FLOAT_INT_BITS)
                else:
                    w.writebits(1, 1)
                    w.writefloat(value)
        else:                                  # integer field
            if value == 0:
                w.writebits(0, 1)
            else:
                w.writebits(1, 1)
                w.writebits(int(value), _ES_BITS[i])


# ── playerstate delta ───────────────────────────────────────────────────────

def write_playerstate_delta(w: BitWriter, from_state: Mapping[int, float],
                            to_state: Mapping[int, float], *,
                            stats: Mapping[int, int] | None = None,
                            persistant: Mapping[int, int] | None = None,
                            ammo: Mapping[int, int] | None = None,
                            powerups: Mapping[int, int] | None = None) -> None:
    """The followed player's state.

    NOT the entity encoding. A playerstate integer field is written directly
    with no non-zero prefix, and a playerstate float carries only the
    small-int flag. `_read_playerstate` is the authority for both.
    """
    changed = [i for i in range(len(_PS_BITS))
               if from_state.get(i, 0) != to_state.get(i, 0)]
    last = (changed[-1] + 1) if changed else 0
    w.writebyte(last)
    for i in range(last):
        if i not in changed:
            w.writebits(0, 1)
            continue
        w.writebits(1, 1)
        value = to_state.get(i, 0)
        if _PS_BITS[i] == 0:                   # float: small-int flag only
            if _is_small_int(value):
                w.writebits(0, 1)
                w.writebits(int(value) + _FLOAT_INT_BIAS, _FLOAT_INT_BITS)
            else:
                w.writebits(1, 1)
                w.writefloat(value)
        else:                                  # integer: direct, no prefix
            w.writebits(int(value), _PS_BITS[i])

    sections = (stats, persistant, ammo, powerups)
    if not any(s for s in sections):
        w.writebits(0, 1)                      # no extra sections
        return
    w.writebits(1, 1)
    for values, count, long_values in ((stats, _MAX_STATS, False),
                                       (persistant, _MAX_PERSISTANT, False),
                                       (ammo, _MAX_WEAPONS, False),
                                       (powerups, _MAX_POWERUPS, True)):
        if not values:
            w.writebits(0, 1)
            continue
        w.writebits(1, 1)
        mask = 0
        for j in values:
            if not 0 <= j < count:
                raise ValueError(f"index {j} outside a {count}-slot section")
            mask |= 1 << j
        w.writeshort(mask)
        for j in range(count):
            if mask & (1 << j):
                if long_values:
                    w.writelong(int(values[j]))
                else:
                    w.writeshort(int(values[j]))


# ── info strings ────────────────────────────────────────────────────────────

SEP = chr(92)          # a single backslash


def info_string(pairs: Sequence[tuple[str, str]]) -> str:
    r"""Build a Q3 info string: \key\value\key\value.

    Assembled from pairs rather than written as a literal, because the literal
    form is a trap that produced two bugs in a row: `\t` in an f-string is a
    TAB, which glued the team key onto every player's name, and `\0` is a NUL
    that truncated the rest. The leading separator matters too -- the reader
    pairs by position after stripping it, so a missing one shifts every field.
    """
    out = []
    for k, v in pairs:
        if SEP in k or SEP in v:
            raise ValueError(f"info string field contains a separator: {k}={v!r}")
        out.append(f"{SEP}{k}{SEP}{v}")
    return "".join(out)


def serverinfo(mapname: str, *, gametype: int = 4, hostname: str,
               maxclients: int = 16, extra: dict[str, str] | None = None) -> str:
    """CS_SERVERINFO. Gametype 4 is Clan Arena (bg_public.h GT_CA)."""
    pairs = [("sv_maxclients", str(maxclients)), ("g_gametype", str(gametype)),
             ("mapname", mapname), ("sv_hostname", hostname),
             ("protocol", "73"), ("gamename", "baseq3"),
             ("g_instagib", "0"), ("sv_privateClients", "0")]
    pairs += list((extra or {}).items())
    return info_string(pairs)


def systeminfo(*, pure: int = 0, extra: dict[str, str] | None = None) -> str:
    """CS_SYSTEMINFO. `sv_pure 0` so playback does not demand pak checksums."""
    pairs = [("sv_pure", str(pure)), ("sv_serverid", "1")]
    pairs += list((extra or {}).items())
    return info_string(pairs)


def player_configstring(name: str, *, team: int, model: str = "sarge",
                        handicap: int = 100) -> str:
    """A CS_PLAYERS entry. `t` is the team: 1 red, 2 blue."""
    return info_string([
        ("n", name), ("t", str(team)), ("model", model), ("hmodel", model),
        ("c1", "4"), ("c2", "5"), ("hc", str(handicap)), ("w", "0"),
        ("l", "0"), ("skill", " 5.00"), ("tt", "0"), ("tl", "0"),
    ])


# ── the file ────────────────────────────────────────────────────────────────

@dataclass
class Packet:
    sequence: int
    payload: bytes

    def encode(self) -> bytes:
        return (struct.pack("<i", self.sequence)
                + struct.pack("<i", len(self.payload)) + self.payload)


class DemoWriter:
    """Assemble a .dm_73.

    Built as whole packets and flushed at the end: the length prefix has to be
    known before the payload is written, and a teaching round is far too small
    to be worth streaming.
    """

    def __init__(self, *, client_num: int = 0, checksum_feed: int = 0) -> None:
        self._packets: list[Packet] = []
        self._seq = 0
        self.client_num = client_num
        self.checksum_feed = checksum_feed
        # accumulated wire state, so each write emits a true delta
        self._ps: dict[int, float] = {}
        self._ents: dict[int, dict[int, float]] = {}

    # -- plumbing ----------------------------------------------------------
    def _new_payload(self) -> BitWriter:
        w = BitWriter()
        w.writelong(self._seq)          # reliable-acknowledge
        return w

    # One spare byte after svc_EOF. Q3 derives its read cursor from the BIT
    # position as `readcount = (bit >> 3) + 1` and then refuses any read where
    # `readcount > cursize`. So when a payload's bits happen to end exactly on
    # a byte boundary, the cursor sits one byte past the buffer and the very
    # next MSG_ReadByte returns -1 -- which the engine reports as
    # "Illegible server message -1".
    #
    # That is why only SOME structurally identical snapshots failed: it
    # depends on the total bit length, not on the contents. Real demos never
    # show it because their payloads come out of a netchan buffer with slack
    # after the terminator. One byte of slack removes the whole class.
    TAIL_PAD = 1

    def _flush(self, w: BitWriter) -> None:
        w.writebyte(SVC_EOF)
        payload = w.bytes() + bytes(self.TAIL_PAD)
        self._packets.append(Packet(self._seq, payload))
        self._seq += 1

    # -- gamestate ---------------------------------------------------------
    def write_gamestate(self, configstrings: Mapping[int, str],
                        baselines: Mapping[int, Mapping[int, float]] | None = None
                        ) -> None:
        w = self._new_payload()
        w.writebyte(SVC_GAMESTATE)
        w.writelong(self._seq)                    # inner ack
        for idx in sorted(configstrings):
            value = configstrings[idx]
            if not value:
                continue
            if not 0 <= idx < MAX_CONFIGSTRINGS:
                raise ValueError(f"configstring index {idx} out of range")
            w.writebyte(SVC_CONFIGSTRING)
            w.writeshort(idx)
            w.writestring(value)
        for num, state in sorted((baselines or {}).items()):
            w.writebyte(SVC_BASELINE)
            w.writebits(num, _GENTITYNUM_BITS)
            write_entity_delta(w, {}, state)
            self._ents[num] = dict(state)
        w.writebyte(SVC_EOF)
        w.writelong(self.client_num)
        w.writelong(self.checksum_feed)
        self._flush(w)

    def write_configstring(self, seq: int, index: int, value: str) -> None:
        """A configstring CHANGE mid-demo.

        Not `svc_configstring` -- that opcode only appears inside the
        gamestate. After it, the server sends `cs <index> "<value>"` as a
        reliable server command, which is what the parser's
        `_parse_servercommand` absorbs and what CA round state rides on.
        """
        self.write_server_command(seq, f'cs {index} "{value}"')

    def write_server_command(self, seq: int, text: str) -> None:
        w = self._new_payload()
        w.writebyte(SVC_SERVERCOMMAND)
        w.writelong(seq)
        w.writestring(text)
        self._flush(w)

    # -- snapshot ----------------------------------------------------------
    def write_snapshot(self, server_time: int,
                       playerstate: Mapping[int, float],
                       entities: Mapping[int, Mapping[int, float] | None],
                       *, stats: Mapping[int, int] | None = None,
                       areamask: bytes = b"",
                       snap_flags: int = 0, full: bool = True) -> None:
        """One frame.

        `full=True` writes deltaNum 0, which tells the client to reset to the
        gamestate baseline. Every frame being a full update costs bandwidth
        nobody is paying for here and removes an entire class of desync from a
        file that has to be right the first time it is played.

        AREAMASK: exactly `len(areamask)` bytes follow the length byte. The
        project previously read len+1 on a belief that QL stores count-1; it
        does not, and the extra byte desynced 73.6% of packets. The writer
        must not reintroduce the asymmetry.
        """
        w = self._new_payload()
        w.writebyte(SVC_SNAPSHOT)
        w.writelong(server_time)
        w.writebyte(0 if full else 1)
        w.writebyte(snap_flags)
        w.writebyte(len(areamask))
        for b in areamask:
            w.writebyte(b)

        from_ps: Mapping[int, float] = {} if full else self._ps
        write_playerstate_delta(w, from_ps, playerstate, stats=stats)
        self._ps = dict(playerstate)

        from_ents = {} if full else self._ents
        for num in sorted(entities):
            state = entities[num]
            w.writebits(num, _GENTITYNUM_BITS)
            write_entity_delta(w, from_ents.get(num, {}), state)
        w.writebits(_SENTINEL, _GENTITYNUM_BITS)
        self._ents = {n: dict(s) for n, s in entities.items() if s is not None}
        self._flush(w)

    # -- output ------------------------------------------------------------
    def to_bytes(self) -> bytes:
        out = bytearray()
        for p in self._packets:
            out += p.encode()
        out += struct.pack("<i", DEMO_EOF) + struct.pack("<i", DEMO_EOF)
        return bytes(out)

    def save(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.to_bytes())
        return path
