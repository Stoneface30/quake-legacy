#!/usr/bin/env python3
"""engine/parser/demo_parse.py

Pure-Python .dm_73 (Quake Live protocol-73) demo parser.

Extracts ALL game events, per-snapshot player state, round boundaries, and
player roster from a demo. Writes stream.json and optionally ingests into
frags.db via --db flag.

Usage:
    python demo_parse.py <demo.dm_73> [--out stream.json] [--db frags.db]

Performance note: Huffman tree seeding is ~3-8s on first run (one-time per process).
"""
from __future__ import annotations

import argparse
import json
import math
import struct
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Q3A / Quake Live constants (protocol 73)
# ---------------------------------------------------------------------------

_FLOAT_INT_BITS = 13
_FLOAT_INT_BIAS = 1 << (_FLOAT_INT_BITS - 1)  # 4096
_GENTITYNUM_BITS = 10
_SENTINEL = (1 << _GENTITYNUM_BITS) - 1        # 1023 = end of packet entities

_SVC_GAMESTATE     = 2
_SVC_CONFIGSTRING  = 3
_SVC_BASELINE      = 4
_SVC_SERVERCOMMAND = 5
_SVC_SNAPSHOT      = 7
_SVC_EOF           = 8

_MAX_CLIENTS    = 64
_MAX_STATS      = 16
_MAX_PERSISTANT = 16
_MAX_WEAPONS    = 16
_MAX_POWERUPS   = 16

# Config string indices (from qldemo constants.py)
_CS_SERVERINFO   = 0
_CS_MODELS       = 17
_CS_SOUNDS       = _CS_MODELS + 256   # 273
_CS_PLAYERS      = _CS_SOUNDS  + 256  # 529
_CS_ROUND_START  = 662

# Entity type constants
_ET_PLAYER  = 1
_ET_EVENTS  = 13   # eType > _ET_EVENTS → temp entity, event = eType - ET_EVENTS

# EV_* event codes (QL extension of Q3A — from wolfcam patches)
_EV_ITEM_PICKUP    = 18
_EV_NOAMMO         = 20
_EV_CHANGE_WEAPON  = 21
_EV_DROP_WEAPON    = 22
_EV_FIRE_WEAPON    = 23
_EV_GIB_PLAYER     = 33
_EV_MISSILE_HIT    = 36
_EV_MISSILE_MISS   = 37
_EV_RAILTRAIL      = 39
_EV_TAUNT          = 50
_EV_PAIN           = 53
_EV_DEATH1         = 54
_EV_DEATH2         = 55
_EV_DEATH3         = 56
_EV_DROWN          = 57
_EV_OBITUARY       = 58

# Human-readable event type names
_EV_NAMES: dict[int, str] = {
    _EV_ITEM_PICKUP:   'item_pickup',
    _EV_NOAMMO:        'noammo',
    _EV_CHANGE_WEAPON: 'change_weapon',
    _EV_DROP_WEAPON:   'drop_weapon',
    _EV_FIRE_WEAPON:   'fire_weapon',
    _EV_GIB_PLAYER:    'gib_player',
    _EV_MISSILE_HIT:   'missile_hit',
    _EV_MISSILE_MISS:  'missile_miss',
    _EV_RAILTRAIL:     'railtrail',
    _EV_TAUNT:         'taunt',
    _EV_PAIN:          'pain',
    _EV_DEATH1:        'death',
    _EV_DEATH2:        'death',
    _EV_DEATH3:        'death',
    _EV_DROWN:         'drown',
    _EV_OBITUARY:      'obituary',
}

# Which event codes we capture (others are footstep sounds, water events, etc.)
_CAPTURE_EVENTS: frozenset[int] = frozenset(_EV_NAMES.keys())

# Means of death names (MOD_*)
_MOD_NAMES = {
    0: 'UNKNOWN',      1: 'SHOTGUN',      2: 'GAUNTLET',   3: 'MACHINEGUN',
    4: 'GRENADE',      5: 'GRENADE_SPLASH', 6: 'ROCKET',   7: 'ROCKET_SPLASH',
    8: 'PLASMA',       9: 'PLASMA_SPLASH', 10: 'RAILGUN',  11: 'LIGHTNING',
    12: 'BFG',        13: 'BFG_SPLASH',   14: 'WATER',     15: 'SLIME',
    16: 'LAVA',       17: 'CRUSH',        18: 'TELEFRAG',  19: 'FALLING',
    20: 'SUICIDE',    21: 'TARGET_LASER', 22: 'TRIGGER_HURT', 23: 'GRAPPLE',
}

# ---------------------------------------------------------------------------
# EntityState NETF field indices (from qldemo EntityStateNETF.update())
# ---------------------------------------------------------------------------
_F_POS_X   =  1   # pos.trBase[0] — float
_F_POS_Y   =  2   # pos.trBase[1] — float
_F_VEL_X   =  3   # pos.trDelta[0] — float
_F_VEL_Y   =  4   # pos.trDelta[1] — float
_F_POS_Z   =  5   # pos.trBase[2] — float
_F_YAW     =  6   # apos.trBase[1] — float
_F_VEL_Z   =  7   # pos.trDelta[2] — float
_F_PITCH   =  8   # apos.trBase[0] — float
_F_EVENT   = 10   # event (10 bits)
_F_ETYPE   = 12   # eType (8 bits)
_F_EVPARM  = 14   # eventParm (8 bits)
_F_EFLAGS  = 18   # eFlags (19 bits)
_F_VICTIM  = 19   # otherEntityNum (victim, 10 bits)
_F_WEAPON  = 20   # weapon (8 bits)
_F_CLIENT  = 21   # clientNum (8 bits)
_F_KILLER  = 31   # otherEntityNum2 (killer, 10 bits)

# PlayerState NETF field indices (from qldemo PlayerStateNETF.update())
_PS_ORIGIN_X  =  1   # float
_PS_ORIGIN_Y  =  2   # float
_PS_VEL_X     =  4   # float
_PS_VEL_Y     =  5   # float
_PS_YAW       =  6   # viewangles[1] — float
_PS_PITCH     =  7   # viewangles[0] — float
_PS_ORIGIN_Z  =  9   # float
_PS_VEL_Z     = 10   # float
_PS_CLIENT    = 40   # clientNum (8 bits)
_PS_WEAPON    = 41   # weapon slot (5 bits)

# ---------------------------------------------------------------------------
# Q3A msg_hData[256] frequency table (from engine/_canonical/src/qcommon/msg.c)
# ---------------------------------------------------------------------------

_MSG_HDATA = [
    250315, 41193,  6292,  7106,  3730,  3750,  6110, 23283,
     33317,  6950,  7838,  9714,  9257, 17259,  3949,  1778,
      8288,  1604,  1590,  1663,  1100,  1213,  1238,  1134,
      1749,  1059,  1246,  1149,  1273,  4486,  2805,  3472,
     21819,  1159,  1670,  1066,  1043,  1012,  1053,  1070,
      1726,   888,  1180,   850,   960,   780,  1752,  3296,
     10630,  4514,  5881,  2685,  4650,  3837,  2093,  1867,
      2584,  1949,  1972,   940,  1134,  1788,  1670,  1206,
      5719,  6128,  7222,  6654,  3710,  3795,  1492,  1524,
      2215,  1140,  1355,   971,  2180,  1248,  1328,  1195,
      1770,  1078,  1264,  1266,  1168,   965,  1155,  1186,
      1347,  1228,  1529,  1600,  2617,  2048,  2546,  3275,
      2410,  3585,  2504,  2800,  2675,  6146,  3663,  2840,
     14253,  3164,  2221,  1687,  3208,  2739,  3512,  4796,
      4091,  3515,  5288,  4016,  7937,  6031,  5360,  3924,
      4892,  3743,  4566,  4807,  5852,  6400,  6225,  8291,
     23243,  7838,  7073,  8935,  5437,  4483,  3641,  5256,
      5312,  5328,  5370,  3492,  2458,  1694,  1821,  2121,
      1916,  1149,  1516,  1367,  1236,  1029,  1258,  1104,
      1245,  1006,  1149,  1025,  1241,   952,  1287,   997,
      1713,  1009,  1187,   879,  1099,   929,  1078,   951,
      1656,   930,  1153,  1030,  1262,  1062,  1214,  1060,
      1621,   930,  1106,   912,  1034,   892,  1158,   990,
      1175,   850,  1121,   903,  1087,   920,  1144,  1056,
      3462,  2240,  4397, 12136,  7758,  1345,  1307,  3278,
      1950,   886,  1023,  1112,  1077,  1042,  1061,  1071,
      1484,  1001,  1096,   915,  1052,   995,  1070,   876,
      1111,   851,  1059,   805,  1112,   923,  1103,   817,
      1899,  1872,   976,   841,  1127,   956,  1159,   950,
      7791,   954,  1289,   933,  1127,  3207,  1020,   927,
      1355,   768,  1040,   745,   952,   805,  1073,   740,
      1013,   805,  1008,   796,   996,  1057, 11457, 13504,
]

# ---------------------------------------------------------------------------
# Q3A adaptive Huffman tree (Vitter's algorithm)
# ---------------------------------------------------------------------------

_NYT      = 256
_INT_NODE = 257


class _HNode:
    __slots__ = ['sym', 'wt', 'parent', 'left', 'right', 'nxt', 'prv', 'head']

    def __init__(self):
        self.sym    = _INT_NODE
        self.wt     = 0
        self.parent = None
        self.left   = None
        self.right  = None
        self.nxt    = None
        self.prv    = None
        self.head   = None


class _AdaptiveHuff:
    _POOL_SZ = 600
    _PTR_SZ  = 1200

    def __init__(self):
        pool = [_HNode() for _ in range(self._POOL_SZ)]
        self._pool  = pool
        self._bloc  = 0
        self._ptrs  = [[None] for _ in range(self._PTR_SZ)]
        self._bptr  = 0
        self._fpts: list = []
        self.loc: list   = [None] * (_NYT + 2)
        root = pool[0]
        self._bloc = 1
        root.sym = _NYT
        root.wt  = 0
        self.tree = self.lhead = root
        self.loc[_NYT] = root

    def _pp(self):
        if self._fpts:
            p = self._fpts.pop()
            p[0] = None
            return p
        p = self._ptrs[self._bptr]
        self._bptr += 1
        return p

    def _fp(self, p):
        self._fpts.append(p)

    def _swap(self, n1, n2):
        p1, p2 = n1.parent, n2.parent
        if p1:
            if p1.left is n1: p1.left = n2
            else: p1.right = n2
        else:
            self.tree = n2
        if p2:
            if p2.left is n2: p2.left = n1
            else: p2.right = n1
        else:
            self.tree = n1
        n1.parent, n2.parent = p2, p1

    def _swaplist(self, n1, n2):
        t = n1.nxt; n1.nxt = n2.nxt; n2.nxt = t
        t = n1.prv; n1.prv = n2.prv; n2.prv = t
        if n1.nxt is n1: n1.nxt = n2
        if n2.nxt is n2: n2.nxt = n1
        if n1.nxt: n1.nxt.prv = n1
        if n2.nxt: n2.nxt.prv = n2
        if n1.prv: n1.prv.nxt = n1
        if n2.prv: n2.prv.nxt = n2

    def _incr_recursive(self, node):
        if node is None:
            return
        if node.nxt and node.nxt.wt == node.wt:
            lnode = node.head[0]
            if lnode is not node.parent:
                self._swap(lnode, node)
            self._swaplist(lnode, node)
        if node.prv and node.prv.wt == node.wt:
            node.head[0] = node.prv
        else:
            node.head[0] = None
            self._fp(node.head)
        node.wt += 1
        if node.nxt and node.nxt.wt == node.wt:
            node.head = node.nxt.head
        else:
            node.head = self._pp()
            node.head[0] = node
        if node.parent:
            self._incr_recursive(node.parent)
            if node.prv is node.parent:
                self._swaplist(node, node.parent)
                if node.head[0] is node:
                    node.head[0] = node.parent

    def add_ref(self, ch: int):
        if self.loc[ch] is None:
            pool = self._pool
            b = self._bloc
            t2 = pool[b];     b += 1
            t  = pool[b];     b += 1
            self._bloc = b
            t2.sym = _INT_NODE
            t2.wt  = 1
            t2.nxt = self.lhead.nxt
            if self.lhead.nxt:
                self.lhead.nxt.prv = t2
                if self.lhead.nxt.wt == 1:
                    t2.head = self.lhead.nxt.head
                else:
                    t2.head = self._pp()
                    t2.head[0] = t2
            else:
                t2.head = self._pp()
                t2.head[0] = t2
            self.lhead.nxt = t2
            t2.prv = self.lhead
            t.sym = ch
            t.wt  = 1
            t.nxt = self.lhead.nxt
            if self.lhead.nxt:
                self.lhead.nxt.prv = t
                if self.lhead.nxt.wt == 1:
                    t.head = self.lhead.nxt.head
                else:
                    t.head = self._pp()
                    t.head[0] = t2
            else:
                t.head = self._pp()
                t.head[0] = t
            self.lhead.nxt = t
            t.prv = self.lhead
            t.left = t.right = None
            lh = self.lhead
            if lh.parent:
                if lh.parent.left is lh: lh.parent.left = t2
                else:                    lh.parent.right = t2
            else:
                self.tree = t2
            t2.right   = t
            t2.left    = lh
            t2.parent  = lh.parent
            lh.parent  = t2
            t.parent   = t2
            self.loc[ch] = t
            self._incr_recursive(t2.parent)
        else:
            self._incr_recursive(self.loc[ch])

    def receive(self, data: bytes, offset: int):
        node = self.tree
        while node.sym == _INT_NODE:
            b = (data[offset >> 3] >> (offset & 7)) & 1
            offset += 1
            node = node.right if b else node.left
        return node.sym, offset


_HUFF: _AdaptiveHuff | None = None


def _get_huff() -> _AdaptiveHuff:
    global _HUFF
    if _HUFF is None:
        print('Seeding Q3A Huffman tree (one-time, ~3-8s)...', flush=True)
        h = _AdaptiveHuff()
        for ch, freq in enumerate(_MSG_HDATA):
            for _ in range(freq):
                h.add_ref(ch)
        _HUFF = h
        print('Huffman tree ready.', flush=True)
    return _HUFF


# ---------------------------------------------------------------------------
# Bit-stream reader
# ---------------------------------------------------------------------------

class _Bits:
    __slots__ = ('_h', '_data', '_bit')

    def __init__(self, huff: _AdaptiveHuff, data: bytes):
        self._h    = huff
        self._data = data
        self._bit  = 0

    def readbits(self, n: int) -> int:
        value  = 0
        nbits  = n & 7
        data   = self._data
        bit    = self._bit
        for i in range(nbits):
            value |= ((data[bit >> 3] >> (bit & 7)) & 1) << i
            bit   += 1
        self._bit = bit
        rem = n - nbits
        shift = nbits
        while rem > 0:
            sym, self._bit = self._h.receive(data, self._bit)
            value |= sym << shift
            shift += 8
            rem   -= 8
        return value

    def readbyte(self) -> int:
        sym, self._bit = self._h.receive(self._data, self._bit)
        return sym

    def readshort(self) -> int:
        lo, self._bit = self._h.receive(self._data, self._bit)
        hi, self._bit = self._h.receive(self._data, self._bit)
        return lo | (hi << 8)

    def readlong(self) -> int:
        b0, self._bit = self._h.receive(self._data, self._bit)
        b1, self._bit = self._h.receive(self._data, self._bit)
        b2, self._bit = self._h.receive(self._data, self._bit)
        b3, self._bit = self._h.receive(self._data, self._bit)
        v = b0 | (b1 << 8) | (b2 << 16) | (b3 << 24)
        return v - 0x100000000 if v >= 0x80000000 else v

    def readfloat(self) -> float:
        b0, self._bit = self._h.receive(self._data, self._bit)
        b1, self._bit = self._h.receive(self._data, self._bit)
        b2, self._bit = self._h.receive(self._data, self._bit)
        b3, self._bit = self._h.receive(self._data, self._bit)
        return struct.unpack_from('<f', bytes([b0, b1, b2, b3]))[0]

    def readstring(self) -> str:
        buf = []
        while True:
            c = self.readbyte()
            if c <= 0:
                break
            buf.append(chr(c if c < 128 else ord('.')))
        return ''.join(buf)


# ---------------------------------------------------------------------------
# EntityState NETF bits (53 fields — from qldemo EntityStateNETF)
# 0 = float field; non-zero = integer field of that many bits
# ---------------------------------------------------------------------------
_ES_BITS = [
    32, 0,  0,  0,  0,  0,  0,  0,  0, 32,   # 0-9
    10, 0,  8,  8,  8,  8, 10,  8, 19, 10,   # 10-19
     8, 8,  0, 32,  8,  0,  0,  0, 24, 16,   # 20-29
     8, 10, 8,  8,  0,  0,  0,  8,  0, 32,   # 30-39
    32, 32,  0,  0,  0,  0, 32, 32,  0,  0,  # 40-49
     0, 32, 16,                               # 50-52
]

# PlayerState NETF bits (48 fields — abs values of signed fields)
_PS_BITS = [
    32, 0, 0,  8, 0, 0,  0,  0, 16, 0,
     0, 8, 16, 16, 8, 4,  8,  8,  8, 16,
    10, 4, 16, 10, 16, 16, 16, 8,  8,  8,
     8, 8,  8,  8,  8, 16, 16, 12, 8,  8,
     8, 5,  0,  0,  0,  0, 10, 16,
]


# ---------------------------------------------------------------------------
# DM73 parser
# ---------------------------------------------------------------------------

class DM73Parser:
    """Parse a .dm_73 Quake Live demo. Extracts all events, positions, rounds."""

    def __init__(self, path: str | Path):
        self._path   = Path(path)
        self._huff   = _get_huff()
        # Player metadata keyed by client number
        self._players: dict[int, dict] = {}
        # Configstring cache
        self._cs: dict[int, str] = {}
        # Round tracking
        self._rounds: list[dict]        = []
        self._cur_round: int            = 0
        self._round_start_ms: int       = 0
        self._last_round_start_val: str = ''
        self._last_server_time: int     = 0
        # Game metadata
        self._map: str      = ''
        self._gametype: str = ''
        # Delta-accumulation state
        self._ps_state: dict   = {}           # accumulated playerstate fields
        self._entity_states: dict[int, dict] = {}   # entity_num → accumulated fields
        self._baseline_entities: dict[int, dict] = {}  # saved gamestate baselines
        # Event dedup: entity_num → last eType that fired (temp entities)
        self._entity_prev_etype: dict[int, int] = {}
        # Event dedup: entity_num → last event field value (attachment events)
        self._entity_prev_ev: dict[int, int]    = {}

    # ── public ────────────────────────────────────────────────────────────────

    def parse(self) -> dict:
        """Parse the demo. Returns stream dict ready for JSON output."""
        events:    list[dict] = []
        snapshots: list[dict] = []
        with open(self._path, 'rb') as fh:
            while True:
                hdr = fh.read(8)
                if len(hdr) < 8:
                    break
                seq    = struct.unpack_from('<i', hdr, 0)[0]
                length = struct.unpack_from('<i', hdr, 4)[0]
                if seq == -1 or length <= 0:
                    break
                payload = fh.read(length)
                if len(payload) < length:
                    break
                try:
                    self._dispatch(payload, events, snapshots)
                except Exception:
                    pass  # tolerate corrupt / trailing packets

        # Close the final open round
        if self._cur_round > 0:
            if self._rounds and self._rounds[-1].get('end_ms') is None:
                self._rounds[-1]['end_ms'] = self._last_server_time

        # Compute per-player stats from events
        stats = _compute_player_stats(events, self._players)

        return {
            'demo':         self._path.name,
            'map':          self._map,
            'gametype':     self._gametype,
            'players':      self._players,
            'rounds':       self._rounds,
            'event_count':  len(events),
            'events':       events,
            'snapshot_count': len(snapshots),
            'snapshots':    snapshots,
            'player_stats': stats,
        }

    # ── packet dispatcher ─────────────────────────────────────────────────────

    def _dispatch(self, payload: bytes, events: list, snapshots: list):
        s   = _Bits(self._huff, payload)
        _   = s.readlong()    # ack sequence
        cmd = s.readbyte()
        if cmd == _SVC_GAMESTATE:
            self._parse_gamestate(s)
        elif cmd == _SVC_SERVERCOMMAND:
            self._parse_servercommand(s)
        elif cmd == _SVC_SNAPSHOT:
            self._parse_snapshot(s, events, snapshots)

    # ── gamestate ─────────────────────────────────────────────────────────────

    def _parse_gamestate(self, s: _Bits):
        _ = s.readlong()    # inner ack
        while True:
            cmd = s.readbyte()
            if cmd == _SVC_EOF:
                break
            if cmd == _SVC_CONFIGSTRING:
                idx    = s.readshort()
                string = s.readstring()
                self._absorb_cs(idx, string)
            elif cmd == _SVC_BASELINE:
                num   = s.readbits(_GENTITYNUM_BITS)
                delta = self._read_entity_delta(s)
                if delta is not None:
                    self._entity_states[num] = dict(delta)
        _ = s.readlong()    # clientNum
        _ = s.readlong()    # checksumFeed
        # Snapshot baselines: when deltaNum=0 arrives, restore these
        self._baseline_entities = {k: dict(v) for k, v in self._entity_states.items()}

    def _absorb_cs(self, idx: int, val: str):
        self._cs[idx] = val
        if idx == _CS_SERVERINFO:
            self._map      = self._cs_field(val, 'mapname')
            gt_raw         = self._cs_field(val, 'g_gametype')
            self._gametype = _GT_NAMES.get(gt_raw, gt_raw)
        elif _CS_PLAYERS <= idx < _CS_PLAYERS + _MAX_CLIENTS:
            client = idx - _CS_PLAYERS
            name   = self._cs_field(val, 'n') or f'CLIENT_{client}'
            team   = self._cs_field(val, 't')
            entry  = self._players.setdefault(client, {})
            entry['name'] = name
            entry['team'] = _TEAM_NAMES.get(team, team)
        elif idx == _CS_ROUND_START:
            if val and val != self._last_round_start_val:
                # Close previous round
                if self._rounds:
                    self._rounds[-1]['end_ms'] = self._last_server_time
                self._last_round_start_val = val
                try:
                    self._round_start_ms = int(val)
                except ValueError:
                    pass
                self._cur_round += 1
                self._rounds.append({
                    'round':    self._cur_round,
                    'start_ms': self._round_start_ms,
                    'end_ms':   None,
                })

    @staticmethod
    def _cs_field(s: str, key: str) -> str:
        parts = s.lstrip('\\').split('\\')
        for i in range(0, len(parts) - 1, 2):
            if parts[i] == key:
                return parts[i + 1]
        return ''

    # ── server command ────────────────────────────────────────────────────────

    def _parse_servercommand(self, s: _Bits):
        _   = s.readlong()
        raw = s.readstring()
        tok = raw.split(None, 2)
        if not tok:
            return
        cmd = tok[0]
        if cmd in ('cs', 'bcs') and len(tok) >= 2:
            rest  = tok[1] if len(tok) == 2 else tok[1] + ' ' + tok[2]
            parts = rest.split(None, 1)
            if len(parts) == 2:
                try:
                    self._absorb_cs(int(parts[0]), parts[1].strip('"'))
                except ValueError:
                    pass

    # ── snapshot ──────────────────────────────────────────────────────────────

    def _parse_snapshot(self, s: _Bits, events: list, snapshots: list):
        server_time           = s.readlong()
        self._last_server_time = server_time
        delta_num             = s.readbyte()
        _                     = s.readbyte()    # snapFlags
        if delta_num == 0:
            # Full update — reset accumulated state to gamestate baseline
            self._ps_state = {}
            self._entity_states = {k: dict(v) for k, v in self._baseline_entities.items()}
            self._entity_prev_etype.clear()
            self._entity_prev_ev.clear()
        area_len              = s.readbyte()
        for _ in range(area_len + 1):           # QL stores count-1
            s.readbyte()

        # Read playerstate and collect snapshot
        snap = self._read_playerstate(s)
        snap['server_time_ms'] = server_time
        snap['round_num']      = self._cur_round
        snapshots.append(snap)

        # Read all entity deltas
        while True:
            entity_num = s.readbits(_GENTITYNUM_BITS)
            if entity_num == _SENTINEL:
                break
            delta = self._read_entity_delta(s)

            if delta is None:
                # Entity removed — clear state and dedup tracking
                self._entity_states.pop(entity_num, None)
                self._entity_prev_etype.pop(entity_num, None)
                self._entity_prev_ev.pop(entity_num, None)
                continue

            if not delta:
                # No-change delta — nothing new to detect
                continue

            # Merge delta into accumulated state
            if entity_num not in self._entity_states:
                self._entity_states[entity_num] = {}
            self._entity_states[entity_num].update(delta)
            accumulated = self._entity_states[entity_num]

            # ── event detection: only fire on fields present in this delta ──
            raw_et = delta.get(_F_ETYPE, 0)  # eType changed THIS snapshot
            raw_ev = delta.get(_F_EVENT, 0)  # event field changed THIS snapshot

            event_code = 0
            if raw_et and raw_et > _ET_EVENTS:
                # Temp entity — event encoded in eType
                ec = (raw_et - _ET_EVENTS) & ~0x300
                prev = self._entity_prev_etype.get(entity_num, 0)
                if ec and ec != prev:
                    self._entity_prev_etype[entity_num] = ec
                    event_code = ec
            elif raw_ev:
                # Attachment event on player entity — full value includes seq bits
                ec = raw_ev & ~0x300
                prev = self._entity_prev_ev.get(entity_num, 0)
                if ec and raw_ev != prev:   # compare full value (seq bits matter)
                    self._entity_prev_ev[entity_num] = raw_ev
                    event_code = ec

            if event_code not in _CAPTURE_EVENTS:
                continue

            # Build event record from accumulated state (delta has positional fields)
            ev = self._build_event(
                entity_num, event_code, delta, accumulated,
                server_time, self._cur_round,
            )
            if ev:
                events.append(ev)

    # ── event record builder ──────────────────────────────────────────────────

    def _build_event(
        self,
        entity_num: int,
        event_code: int,
        delta: dict,
        accumulated: dict,
        server_time: int,
        round_num: int,
    ) -> dict | None:
        ev_type = _EV_NAMES.get(event_code, f'ev_{event_code}')

        # Position: prefer delta (freshly set), fall back to accumulated
        source = delta if delta else accumulated
        px = source.get(_F_POS_X)
        py = source.get(_F_POS_Y)
        pz = source.get(_F_POS_Z)

        ev: dict = {
            'type':           ev_type,
            'event_code':     event_code,
            'entity_num':     entity_num,
            'server_time_ms': server_time,
            'round':          round_num,
            'client_num':     accumulated.get(_F_CLIENT),
            'pos_x':          round(px, 2) if px is not None else None,
            'pos_y':          round(py, 2) if py is not None else None,
            'pos_z':          round(pz, 2) if pz is not None else None,
        }

        if event_code == _EV_OBITUARY:
            weapon  = accumulated.get(_F_EVPARM, 0)
            victim  = accumulated.get(_F_VICTIM, 0)
            killer  = accumulated.get(_F_KILLER, 0)
            v_info  = self._players.get(victim, {})
            k_info  = self._players.get(killer, {})
            ev.update({
                'victim_client': victim,
                'victim_name':   v_info.get('name', f'CLIENT_{victim}'),
                'victim_team':   v_info.get('team', ''),
                'killer_client': killer,
                'killer_name':   k_info.get('name', f'CLIENT_{killer}'),
                'killer_team':   k_info.get('team', ''),
                'weapon':        weapon,
                'weapon_name':   _MOD_NAMES.get(weapon, f'MOD_{weapon}'),
            })
        elif event_code in (_EV_CHANGE_WEAPON, _EV_DROP_WEAPON, _EV_FIRE_WEAPON,
                            _EV_NOAMMO, _EV_RAILTRAIL, _EV_MISSILE_HIT,
                            _EV_MISSILE_MISS, _EV_GIB_PLAYER):
            ev['weapon']      = accumulated.get(_F_WEAPON)
            ev['weapon_name'] = _MOD_NAMES.get(ev['weapon'], None)
            ev['event_parm']  = accumulated.get(_F_EVPARM)
        elif event_code == _EV_ITEM_PICKUP:
            ev['event_parm'] = accumulated.get(_F_EVPARM)   # item type
        elif event_code in (_EV_PAIN, _EV_DEATH1, _EV_DEATH2, _EV_DEATH3, _EV_DROWN):
            ev['event_parm'] = accumulated.get(_F_EVPARM)   # health at pain

        return ev

    # ── playerstate reader ────────────────────────────────────────────────────

    def _read_playerstate(self, s: _Bits) -> dict:
        """Read playerstate delta, accumulate into self._ps_state, return snapshot."""
        last = s.readbyte()
        for i in range(min(last, len(_PS_BITS))):
            if s.readbits(1):   # changed?
                bits = _PS_BITS[i]
                if bits == 0:   # float field
                    if s.readbits(1) == 0:   # small int encoding
                        trunc = s.readbits(_FLOAT_INT_BITS)
                        self._ps_state[i] = float(trunc - _FLOAT_INT_BIAS)
                    else:
                        self._ps_state[i] = s.readfloat()
                else:           # integer field — direct read, no non-zero prefix
                    self._ps_state[i] = s.readbits(bits)
        if s.readbits(1):   # has extra sections
            if s.readbits(1):   # stats
                c = s.readshort()
                for j in range(_MAX_STATS):
                    if c & (1 << j):
                        self._ps_state[f's{j}'] = s.readshort()
            if s.readbits(1):   # persistant
                c = s.readshort()
                for j in range(_MAX_PERSISTANT):
                    if c & (1 << j): s.readshort()
            if s.readbits(1):   # ammo
                c = s.readshort()
                for j in range(_MAX_WEAPONS):
                    if c & (1 << j): s.readshort()
            if s.readbits(1):   # powerups
                c = s.readshort()
                for j in range(_MAX_POWERUPS):
                    if c & (1 << j): s.readlong()

        ps = self._ps_state
        ox = ps.get(_PS_ORIGIN_X)
        oy = ps.get(_PS_ORIGIN_Y)
        oz = ps.get(_PS_ORIGIN_Z)
        vx = ps.get(_PS_VEL_X)
        vy = ps.get(_PS_VEL_Y)
        vz = ps.get(_PS_VEL_Z)
        speed: float | None = None
        if vx is not None and vy is not None and vz is not None:
            speed = math.sqrt(vx * vx + vy * vy + vz * vz)

        # Sanity bounds: Q3 maps are ±32768 units; velocities rarely exceed ±4000
        def _coord(v): return round(v, 2) if v is not None and abs(v) < 65536 else None
        def _vel(v):   return round(v, 2) if v is not None and abs(v) < 32768 else None
        def _ang(v):   return round(v % 360, 2) if v is not None and abs(v) < 1e6 else None

        ox, oy, oz = _coord(ox), _coord(oy), _coord(oz)
        vx, vy, vz = _vel(vx), _vel(vy), _vel(vz)
        if vx is not None and vy is not None and vz is not None:
            speed = round(math.sqrt(vx * vx + vy * vy + vz * vz), 2)
        else:
            speed = None

        return {
            'client_num':  ps.get(_PS_CLIENT),
            'weapon':      ps.get(_PS_WEAPON),
            'origin_x':    ox,
            'origin_y':    oy,
            'origin_z':    oz,
            'vel_x':       vx,
            'vel_y':       vy,
            'vel_z':       vz,
            'angle_pitch': _ang(ps.get(_PS_PITCH)),
            'angle_yaw':   _ang(ps.get(_PS_YAW)),
            'speed':       speed,
            'health':      ps.get('s0'),   # STAT_HEALTH
            'armor':       ps.get('s4'),   # STAT_ARMOR
        }

    # ── entity delta reader ───────────────────────────────────────────────────

    def _read_entity_delta(self, s: _Bits) -> dict | None:
        """Read one entity delta. Returns dict of changed field→value, None if removed."""
        if s.readbits(1):
            return None    # entity removed
        if s.readbits(1) == 0:
            return {}      # no delta
        last = s.readbyte()
        out: dict = {}
        for i in range(min(last, len(_ES_BITS))):
            if s.readbits(1):   # field changed
                bits = _ES_BITS[i]
                if bits == 0:   # float field
                    if s.readbits(1):   # non-zero
                        if s.readbits(1) == 0:  # small int
                            trunc = s.readbits(_FLOAT_INT_BITS)
                            out[i] = float(trunc - _FLOAT_INT_BIAS)
                        else:
                            out[i] = s.readfloat()
                    # non-zero bit = 0 → value is 0.0, leave absent (default)
                else:           # integer field
                    if s.readbits(1):   # non-zero
                        out[i] = s.readbits(bits)
        return out


# ---------------------------------------------------------------------------
# Stats computation
# ---------------------------------------------------------------------------

def _compute_player_stats(events: list[dict], players: dict) -> list[dict]:
    """Derive kills/deaths/suicides per player from event list."""
    stats: dict[int, dict] = {}

    def _entry(client: int) -> dict:
        if client not in stats:
            info = players.get(client, {})
            stats[client] = {
                'client_num':      client,
                'player_name':     info.get('name', f'CLIENT_{client}'),
                'team':            info.get('team', ''),
                'kills':           0,
                'deaths':          0,
                'suicides':        0,
                'kills_by_weapon': {},
                'deaths_by_weapon': {},
            }
        return stats[client]

    for ev in events:
        if ev['type'] != 'obituary':
            continue
        victim = ev.get('victim_client')
        killer = ev.get('killer_client')
        weapon = ev.get('weapon_name', 'UNKNOWN')

        if victim is not None and victim < _MAX_CLIENTS:
            e = _entry(victim)
            if victim == killer:
                e['suicides'] += 1
            else:
                e['deaths'] += 1
                e['deaths_by_weapon'][weapon] = e['deaths_by_weapon'].get(weapon, 0) + 1

        if killer is not None and killer < _MAX_CLIENTS and killer != victim:
            e = _entry(killer)
            e['kills'] += 1
            e['kills_by_weapon'][weapon] = e['kills_by_weapon'].get(weapon, 0) + 1

    return list(stats.values())


# ---------------------------------------------------------------------------
# Game type / team name maps
# ---------------------------------------------------------------------------

_GT_NAMES = {
    '0': 'FFA', '1': 'DUEL', '2': 'RACE', '3': 'TEAM',
    '4': 'CA',  '5': 'CTF',  '6': '1FCTF', '7': 'OBELISK',
    '8': 'HARVESTER', '9': 'FREEZETAG', '10': 'DOMINATION',
    '11': 'ATTACK_AND_DEFEND', '12': 'REDROVER',
}
_TEAM_NAMES = {'0': 'FREE', '1': 'RED', '2': 'BLUE', '3': 'SPECTATOR'}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description='Extract ALL events/positions/rounds from a .dm_73 demo.')
    ap.add_argument('demo', help='Path to .dm_73 file')
    ap.add_argument('--out', default='',
                    help='Output JSON (default: engine/parser/stream.json)')
    ap.add_argument('--db', default='',
                    help='Path to frags.db to ingest into (optional)')
    args = ap.parse_args()

    demo_path = Path(args.demo)
    if not demo_path.exists():
        sys.exit(f'Error: {demo_path} not found')

    out_path = Path(args.out) if args.out else Path(__file__).parent / 'stream.json'

    parser = DM73Parser(demo_path)
    result = parser.parse()

    # Compact stream.json: snapshots stored separately to keep it readable
    stream_out = {k: v for k, v in result.items() if k != 'snapshots'}
    stream_out['snapshot_count'] = result['snapshot_count']
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(stream_out, indent=2, ensure_ascii=False),
                        encoding='utf-8')

    obituaries = [e for e in result['events'] if e['type'] == 'obituary']
    print(f'Wrote to {out_path}')
    print(f'  Map: {result["map"]}  Gametype: {result["gametype"]}')
    print(f'  Players: {len(result["players"])}  Rounds: {len(result["rounds"])}')
    print(f'  Events total: {result["event_count"]}  '
          f'(obituaries: {len(obituaries)})')
    print(f'  Snapshots: {result["snapshot_count"]}')

    if args.db:
        import importlib.util
        _spec = importlib.util.spec_from_file_location(
            'db_ingest', Path(__file__).parent / 'db_ingest.py')
        assert _spec is not None and _spec.loader is not None
        _mod = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)  # type: ignore[union-attr]
        demo_id = _mod.ingest(result, Path(args.db))
        print(f'  Ingested into {args.db} as demo_id={demo_id}')


if __name__ == '__main__':
    main()
