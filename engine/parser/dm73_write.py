"""Write a .dm_73 Quake Live demo. The inverse of `demo_parse.py`.

WHY THIS EXISTS. The Clan Arena explainer must teach the rules on a round we
control completely -- known team sizes, known positions, a kill happening
where the camera is looking -- without spending a historically important round
on a tutorial and without a single synthetic event touching career statistics.
That means authoring a demo file rather than finding one.

THE THING THAT MAKES THIS TRACTABLE. `demo_parse.py` seeds the Q3 Huffman tree
once from the frequency table and then never updates it -- `receive()` does not
call `add_ref()`. The tree is STATIC. So encoding is not an adaptive-coder
problem at all: walk each symbol's node up to the root once, cache the bit
path, and writing becomes a table lookup that is byte-exact with the reader by
construction.

HOW IT IS PROVEN. Every demo this module writes is read back by the project's
own `DM73Parser` and compared field by field. A writer validated against its
own idea of the format proves nothing; validated against the reader that
consumes 4,292 real demos, it proves a great deal. The final gate is
WolfcamQL actually playing the file.

Byte order is little-endian throughout, matching msg.c.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

from engine.parser.demo_parse import (
    _ES_BITS, _PS_BITS, _INT_NODE, _NYT, _get_huff)

# ── container constants (docs/reference/dm73-format-deep-dive.md §1) ────────
# Each message is [int32 sequence][int32 length][payload], and the file ends
# with a sequence of -1. The length is the payload length in bytes.
DEMO_EOF = -1

# svc_* opcodes, read as 8 bits at the top of each payload
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
MAX_GAMESTATE_CHARS = 16000
PACKET_ENTITY_TERMINATOR = 1023      # 10-bit "no more entities"
MAX_PS_EVENTS = 2


# ── the code table ──────────────────────────────────────────────────────────

_CODES: list[tuple[int, int]] | None = None      # (bits, length) per symbol


def _build_codes() -> list[tuple[int, int]]:
    """Bit path from root to each symbol, from the reader's own seeded tree.

    Emitted least-significant-bit-first to match how `receive` consumes them:
    it walks `node.left` on a 0 bit and `node.right` on a 1, reading bits in
    ascending order within each byte.
    """
    huff = _get_huff()
    codes: list[tuple[int, int]] = [(0, 0)] * 256
    for sym in range(256):
        node = huff.loc[sym]
        if node is None:                          # pragma: no cover - seeded
            raise RuntimeError(f"symbol {sym} absent from the seeded tree")
        path: list[int] = []
        while node.parent is not None:
            path.append(1 if node.parent.right is node else 0)
            node = node.parent
        path.reverse()                            # root -> leaf
        value = 0
        for i, b in enumerate(path):
            value |= b << i
        codes[sym] = (value, len(path))
    return codes


def codes() -> list[tuple[int, int]]:
    global _CODES
    if _CODES is None:
        _CODES = _build_codes()
    return _CODES


# ── bit writer ──────────────────────────────────────────────────────────────

class BitWriter:
    """The mirror of `demo_parse._Bits`.

    `writebits` splits exactly as the reader's `readbits` does: the low `n & 7`
    bits go out raw, one per bit position, and the remainder goes out as whole
    Huffman-coded bytes, least significant byte first.
    """

    __slots__ = ("_buf", "_bit")

    def __init__(self) -> None:
        self._buf = bytearray()
        self._bit = 0

    # -- raw ---------------------------------------------------------------
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

    # -- the MSG_Write* family ---------------------------------------------
    def writebits(self, value: int, n: int) -> None:
        value &= (1 << n) - 1 if n < 64 else value
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
        for b in struct.pack("<f", v):
            self._put_symbol(b)

    def writestring(self, s: str) -> None:
        for ch in s.encode("latin-1", errors="replace"):
            self._put_symbol(ch)
        self._put_symbol(0)

    def bytes(self) -> bytes:
        return bytes(self._buf)


# ── delta encoders ──────────────────────────────────────────────────────────
# The reader's field tables are reused directly rather than restated. A second
# copy of a 53-entry table is a second thing to drift.

def _write_delta_fields(w: BitWriter, bits: Sequence[int],
                        from_state: dict, to_state: dict,
                        names: Sequence[str]) -> None:
    """Shared body of entity and playerstate delta encoding.

    Writes the count of fields up to the last changed one, then per field a
    single "changed" bit, then the value. A float field is sent either as a
    13-bit truncated integer when it is a small whole number, or as a full 32
    bits -- the same two cases the reader decodes.
    """
    last_changed = 0
    for i, name in enumerate(names):
        if from_state.get(name, 0) != to_state.get(name, 0):
            last_changed = i + 1
    w.writebyte(last_changed)
    for i in range(last_changed):
        name = names[i]
        old = from_state.get(name, 0)
        new = to_state.get(name, 0)
        if old == new:
            w.writebits(0, 1)
            continue
        w.writebits(1, 1)
        nbits = bits[i]
        if nbits == 0:                            # float field
            if new == 0:
                w.writebits(0, 1)                 # "is zero"
            else:
                w.writebits(1, 1)
                fv = float(new)
                trunc = int(fv)
                if fv == trunc and 0 <= trunc + 4096 < (1 << 13):
                    w.writebits(0, 1)             # small integral
                    w.writebits(trunc + 4096, 13)
                else:
                    w.writebits(1, 1)             # full float
                    w.writefloat(fv)
        else:
            if new == 0:
                w.writebits(0, 1)
            else:
                w.writebits(1, 1)
                w.writebits(int(new), nbits)


@dataclass
class EntityState:
    """One packet entity. Only the fields the explainer needs are modelled;
    everything else stays at its baseline value, which is what a delta is
    for."""
    number: int
    pos_trBase: tuple[float, float, float] = (0.0, 0.0, 0.0)
    apos_trBase: tuple[float, float, float] = (0.0, 0.0, 0.0)
    eType: int = 0
    eFlags: int = 0
    clientNum: int = 0
    modelindex: int = 0
    event: int = 0
    eventParm: int = 0
    otherEntityNum: int = 0
    otherEntityNum2: int = 0

    def as_fields(self) -> dict:
        x, y, z = self.pos_trBase
        _, yaw, _ = self.apos_trBase
        return {
            "pos.trBase[0]": x, "pos.trBase[1]": y, "pos.trBase[2]": z,
            "apos.trBase[1]": yaw,
            "eType": self.eType, "eFlags": self.eFlags,
            "clientNum": self.clientNum, "modelindex": self.modelindex,
            "event": self.event, "eventParm": self.eventParm,
            "otherEntityNum": self.otherEntityNum,
            "otherEntityNum2": self.otherEntityNum2,
        }


# ── the file container ──────────────────────────────────────────────────────

_GENTITYNUM_BITS = 10
_CS_SERVERINFO = 0
_CS_PLAYERS = 529


@dataclass
class Packet:
    """One [seq][len][payload] record. The payload holds a sequence of
    messages terminated by svc_EOF, exactly as CL_ParseServerMessage loops."""
    sequence: int
    payload: bytes

    def encode(self) -> bytes:
        return (struct.pack("<i", self.sequence)
                + struct.pack("<i", len(self.payload)) + self.payload)


class DemoWriter:
    """Assemble a .dm_73.

    The demo is built as whole packets and flushed at the end, because the
    length prefix has to be known before the payload is written and a demo
    that teaches an eight-player round is far too small to be worth streaming.
    """

    def __init__(self, *, client_num: int = 0, checksum_feed: int = 0) -> None:
        self._packets: list[Packet] = []
        self._seq = 0
        self.client_num = client_num
        self.checksum_feed = checksum_feed

    # -- packet plumbing ---------------------------------------------------
    def _new_payload(self) -> BitWriter:
        w = BitWriter()
        w.writelong(self._seq)          # reliable-acknowledge; the reader
        return w                        # reads and discards this

    def _flush(self, w: BitWriter) -> None:
        w.writebyte(SVC_EOF)
        self._packets.append(Packet(self._seq, w.bytes()))
        self._seq += 1

    # -- gamestate ---------------------------------------------------------
    def write_gamestate(self, configstrings: dict[int, str],
                        baselines: dict[int, dict] | None = None) -> None:
        """The opening packet: every configstring, then entity baselines.

        Configstring 0 carries the serverinfo -- `\g_gametype\4\mapname\...`
        -- which is where the reader learns the map and that this is Clan
        Arena. Player configstrings start at 529.
        """
        w = self._new_payload()
        w.writebyte(SVC_GAMESTATE)
        w.writelong(self._seq)                    # inner ack
        for idx in sorted(configstrings):
            value = configstrings[idx]
            if not value:
                continue
            if idx >= MAX_CONFIGSTRINGS:
                raise ValueError(f"configstring index {idx} out of range")
            w.writebyte(SVC_CONFIGSTRING)
            w.writeshort(idx)
            w.writestring(value)
        for num, state in sorted((baselines or {}).items()):
            w.writebyte(SVC_BASELINE)
            w.writebits(num, _GENTITYNUM_BITS)
            write_entity_delta(w, {}, state)
        w.writebyte(SVC_EOF)                      # end of the gamestate list
        w.writelong(self.client_num)
        w.writelong(self.checksum_feed)
        self._flush(w)

    # -- server command ----------------------------------------------------
    def write_server_command(self, seq: int, text: str) -> None:
        """A reliable server command -- `print`, `cp`, `scores`, and the
        round announcements the explainer needs."""
        w = self._new_payload()
        w.writebyte(SVC_SERVERCOMMAND)
        w.writelong(seq)
        w.writestring(text)
        self._flush(w)

    # -- output ------------------------------------------------------------
    def to_bytes(self) -> bytes:
        out = bytearray()
        for p in self._packets:
            out += p.encode()
        # The reader stops on a sequence of -1 or a non-positive length.
        out += struct.pack("<i", DEMO_EOF) + struct.pack("<i", DEMO_EOF)
        return bytes(out)

    def save(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.to_bytes())
        return path


# Field names in wire order, matching demo_parse's _ES_BITS table positions.
# Only the ones the explainer sets are named; the rest are placeholders so the
# index of every named field stays correct.
ES_NAMES: list[str] = [f"_es{i}" for i in range(len(_ES_BITS))]
for _i, _n in ((0, "pos.trTime"), (5, "pos.trBase[0]"), (6, "pos.trBase[1]"),
               (7, "pos.trBase[2]"), (12, "apos.trBase[1]"), (16, "event"),
               (17, "angles2[1]"), (18, "eType"), (19, "eFlags"),
               (20, "otherEntityNum"), (21, "eventParm"), (24, "modelindex"),
               (28, "clientNum"), (30, "otherEntityNum2")):
    ES_NAMES[_i] = _n


def write_entity_delta(w: BitWriter, from_state: dict, to_state: dict) -> None:
    _write_delta_fields(w, _ES_BITS, from_state, to_state, ES_NAMES)


SEP = chr(92)          # a single backslash


def info_string(pairs: Sequence[tuple[str, str]]) -> str:
    r"""Build a Q3 info string: \key\value\key\value.

    Assembled from pairs rather than written as a literal, because the literal
    form is a trap. Two separate bugs came out of it: `\t` in an f-string is a
    TAB, not backslash-t, so the team key silently became whitespace glued to
    the player's name, and `\0` became a NUL that truncated the rest. Joining
    real separators has no escapes to get wrong.

    The leading separator matters too -- the reader pairs key/value by
    position after stripping it, so a missing one shifts every field.
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
    pairs = [("g_gametype", str(gametype)), ("mapname", mapname),
             ("sv_hostname", hostname), ("sv_maxclients", str(maxclients)),
             ("protocol", "73")]
    pairs += list((extra or {}).items())
    return info_string(pairs)


def player_configstring(name: str, *, team: int, model: str = "sarge",
                        handicap: int = 100) -> str:
    """A CS_PLAYERS entry. `t` is the team: 1 red, 2 blue."""
    return info_string([
        ("n", name), ("t", str(team)), ("model", model), ("hmodel", model),
        ("hc", str(handicap)), ("w", "0"), ("l", "0"), ("skill", " 5.00"),
        ("tt", "0"), ("tl", "0"),
    ])
