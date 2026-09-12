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
_SVC_EOF           = 8
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

# EV_* event codes -- QUAKE LIVE numbering for protocol 73.
#
# Cross-checked against two independent implementations that agree: QLDT's
# entityEvents_QL and UberDemoTools' EntityEvents_73p.
#
# The previous table used stock-Q3 values, which mislabelled the four commonest
# events in the stream. The frequencies corroborate the correction: code 20
# fires ~9800x per demo, which is FIRE_WEAPON, not NOAMMO.
#
# HISTORY: a first attempt at this change appeared to collapse obituaries from
# 101 to 15. That measurement was wrong -- the rewrite deleted constants still
# referenced in _build_event, the resulting NameError was swallowed by the bare
# `except Exception: pass` around _dispatch, and every obituary packet was
# dropped. Every name referenced below is therefore defined here.
_EV_ITEM_PICKUP    = 15
_EV_CHANGE_WEAPON  = 18
_EV_FIRE_WEAPON    = 20
_EV_USE_ITEM       = 21
_EV_DROP_WEAPON    = 22      # retained: referenced by _build_event
_EV_NOAMMO         = 23      # retained: referenced by _build_event
_EV_MISSILE_HIT    = 47
_EV_MISSILE_MISS   = 48
_EV_PLAYER_TELEPORT_IN = 39
_EV_PLAYER_TELEPORT_OUT = 40   # enrichment 2026-09-02: bg_public.h
_EV_JUMP_PAD       = 9         # enrichment 2026-09-02: bg_public.h
_EV_JUMP           = 10        # enrichment 2026-09-02: bg_public.h
_EV_RAILTRAIL      = 50
_EV_PAIN           = 53
_EV_DEATH1         = 54
_EV_DEATH2         = 55
_EV_DEATH3         = 56
_EV_DROWN          = 57
_EV_OBITUARY       = 58
_EV_GIB_PLAYER     = 63
_EV_SCOREPLUM      = 64

# Human-readable event type names
_EV_NAMES: dict[int, str] = {
    _EV_ITEM_PICKUP:        'item_pickup',
    _EV_CHANGE_WEAPON:      'change_weapon',
    _EV_FIRE_WEAPON:        'fire_weapon',
    _EV_USE_ITEM:           'use_item',
    _EV_DROP_WEAPON:        'drop_weapon',
    _EV_NOAMMO:             'noammo',
    _EV_MISSILE_HIT:        'missile_hit',
    _EV_MISSILE_MISS:       'missile_miss',
    _EV_PLAYER_TELEPORT_IN: 'teleport_in',
    _EV_PLAYER_TELEPORT_OUT: 'teleport_out',
    _EV_JUMP_PAD:           'jump_pad',
    _EV_JUMP:               'jump',
    _EV_RAILTRAIL:          'railtrail',
    _EV_PAIN:               'pain',
    _EV_DEATH1:             'death',
    _EV_DEATH2:             'death',
    _EV_DEATH3:             'death',
    _EV_DROWN:              'drown',
    _EV_OBITUARY:           'obituary',
    _EV_GIB_PLAYER:         'gib_player',
    _EV_SCOREPLUM:          'scoreplum',
}

# Which event codes we capture (others are footstep sounds, water events, etc.)
_CAPTURE_EVENTS: frozenset[int] = frozenset(_EV_NAMES.keys())

# Means of death names (MOD_*)
# WP_* launcher space (bg_public.h weapon_t), Quake Live numbering.
_WP_NAMES = {
    1: 'GAUNTLET', 2: 'MACHINEGUN', 3: 'SHOTGUN', 4: 'GRENADE_LAUNCHER',
    5: 'ROCKET_LAUNCHER', 6: 'LIGHTNING', 7: 'RAILGUN', 8: 'PLASMAGUN', 9: 'BFG',
    10: 'GRAPPLING_HOOK', 11: 'NAILGUN', 12: 'PROX_LAUNCHER', 13: 'CHAINGUN', 14: 'HMG',
}

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
# THE TRAJECTORY IS NOT JUST A POINT. pos.trBase alone is meaningless for a
# moving entity: a Q3 missile sets trBase/trDelta/trTime once at spawn and
# never changes them, so trBase repeats identically across snapshots while the
# missile crosses the map. Reading it as a position is the classic mistake.
# Indices from the protocol-73 entityState field table (docs/reference/
# dm73-format-deep-dive.md, confirmed against qldemo EntityStateNETF).
_F_POS_TIME = 0   # pos.trTime — 32 bits, the trajectory's own start time
_F_POS_TRTYPE = 17  # pos.trType — 8 bits (TR_STATIONARY/TR_LINEAR/TR_GRAVITY…)
_F_POS_TRDUR = 23  # pos.trDuration — 32 bits
_F_POS_X   =  1   # pos.trBase[0] — float
_F_POS_Y   =  2   # pos.trBase[1] — float
_F_VEL_X   =  3   # pos.trDelta[0] — float
_F_VEL_Y   =  4   # pos.trDelta[1] — float
_F_POS_Z   =  5   # pos.trBase[2] — float
_F_YAW     =  6   # apos.trBase[1] — float
_F_VEL_Z   =  7   # pos.trDelta[2] — float
_F_PITCH   =  8   # apos.trBase[0] — float
# angles2[YAW] on a player is NOT an angle: it is the 0-7 movement
# direction index cgame uses to offset the legs from the view
# (CG_PlayerAngles movementOffsets). Without it a strafing player's
# legs face his aim instead of his travel.
_F_ANGLES2_YAW = 11
_F_EVENT   = 10   # event (10 bits)
_F_ETYPE   = 12   # eType (8 bits)
_F_EVPARM  = 14   # eventParm (8 bits)
_F_EFLAGS  = 18   # eFlags (19 bits)
_F_VICTIM  = 19   # otherEntityNum (victim, 10 bits)
_F_WEAPON  = 20   # weapon (8 bits)
_F_CLIENT  = 21   # clientNum (8 bits)
_F_KILLER  = 31   # otherEntityNum2 (killer, 10 bits)
_F_GROUND  = 16   # groundEntityNum (10 bits). ENTITYNUM_NONE (1023) = AIRBORNE.
                  #   Field order matches Q3 entityStateFields exactly, so this
                  #   is ground truth -- no velocity heuristic needed.
_ENTITYNUM_NONE = 1023
_MAX_CLIENTS = 64

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
# Enrichment 2026-09-02: the recorder's own events live in the playerstate,
# not in entity events. Indices from the canonical playerStateFields table;
# their bit widths (16, 8, 8, 8, 8) match _PS_BITS at these positions.
_PS_EVENT_SEQ = 13   # eventSequence (16 bits)
_PS_EVENT0    = 16   # events[0] (8 bits)
_PS_EVENT1    = 18   # events[1] (8 bits)
_PS_EVPARM0   = 38   # eventParms[0] (8 bits)
_PS_EVPARM1   = 39   # eventParms[1] (8 bits)
_MAX_PS_EVENTS = 2
_PS_GROUND    = 20   # groundEntityNum (10 bits); 1023 = airborne
_PS_WEAPON    = 41   # weapon slot (5 bits)
# From the GENERATED schema (engine/parser/netfields_generated.py,
# playerStateFieldsQ3, which msg.c selects for protocol 73). Not transcribed
# by hand: a test regenerates the table from the engine source and fails on
# drift. The previous hand audit skipped the one entry whose bit width is a
# macro and concluded, wrongly, that protocol 73 used a different table.
_PS_MOVEDIR    = 15  # movementDir (4 bits): 0-7 octant, own-POV
_PS_LEGSTIMER  = 11  # legsTimer
_PS_PM_FLAGS   = 19  # pm_flags
_PS_VIEWHEIGHT = 28  # viewheight (signed 8) -- NOT always 26
_PS_DMG_EVENT  = 29  # damageEvent
_PS_DMG_YAW    = 30  # damageYaw
_PS_DMG_PITCH  = 31  # damagePitch
_PS_DMG_COUNT  = 32  # damageCount
_PS_PM_TYPE    = 34  # pm_type: PM_NORMAL / PM_DEAD / PM_SPECTATOR / ...
_PS_TORSOTIMER = 37  # torsoTimer

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
        """MSG_ReadShort. SIGNED, like the engine.

        msg.c does `c = (short)MSG_ReadBits(msg, 16)` -- an explicit cast to a
        signed short -- and readlong() below already sign-extends. This one did
        not, and the STAT_ array is read through it (see the playerstate
        decode), so a dead player's negative health came back as its unsigned
        complement: 23 stored health_at_frag values sat between 65,459 and
        65,535, which are -77 to -1. Those are exactly the interesting ones,
        the heavy overkill deaths.

        Sign-extending is safe for the other callers: the configstring index
        is bounded well below 32,767, and the stats/persistant bitmasks are
        used with `&`, where Python's arbitrary-precision -1 behaves as
        all-ones exactly as the 16-bit mask intends.
        """
        lo, self._bit = self._h.receive(self._data, self._bit)
        hi, self._bit = self._h.receive(self._data, self._bit)
        v = lo | (hi << 8)
        return v - 0x10000 if v >= 0x8000 else v

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
        """MSG_ReadString (msg.c:479) for protocol < 91: '%' and bytes above
        127 become '.'. The '%' rule was missing, so any command carrying a
        percent sign disagreed with what the client stored."""
        buf = []
        while True:
            c = self.readbyte()
            if c <= 0:
                break
            if c == 0x25 or c > 127:
                c = 0x2E
            buf.append(chr(c))
        return ''.join(buf)

    def readbigstring(self) -> str:
        """MSG_ReadBigString (msg.c:511), used for gamestate configstrings:
        '%' becomes '.', and bytes above 127 are KEPT (latin-1). Reading
        these with readstring turned every high byte in a name into '.'."""
        buf = []
        while True:
            c = self.readbyte()
            if c <= 0:
                break
            buf.append(chr(0x2E if c == 0x25 else c))
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

# Signed playerstate fields (negative width in playerStateFieldsQ3):
# weaponTime, pm_time, viewheight. Asserted against netfields_generated by
# creative_suite/tests/test_pantheon_demo_feed.py.
_PS_SIGNED = frozenset({8, 12, 28})
_MAX_CONFIGSTRINGS = 1024
_MAX_STRING_TOKENS = 1024
_BIG_INFO_STRING = 8192


def cmd_tokenize(text: str) -> list[str]:
    """Cmd_TokenizeString (qcommon/cmd.c:939, ignoreQuotes=qfalse).

    Whitespace is any byte <= ' '. A // comment ends the line; /* */ is
    skipped. A quoted token runs to the next quote (no escapes); a bare token
    stops at whitespace, a quote, // or /*.
    """
    args: list[str] = []
    i, n = 0, len(text)
    while True:
        if len(args) == _MAX_STRING_TOKENS:
            return args
        while True:
            while i < n and ord(text[i]) <= 32:
                i += 1
            if i >= n:
                return args
            if text.startswith('//', i):
                return args
            if text.startswith('/*', i):
                j = text.find('*/', i + 2)
                if j < 0:
                    return args
                i = j + 2
            else:
                break
        if text[i] == '"':
            j = text.find('"', i + 1)
            if j < 0:
                args.append(text[i + 1:])
                return args
            args.append(text[i + 1:j])
            i = j + 1
            continue
        j = i
        while j < n and ord(text[j]) > 32:
            if text[j] == '"' or text.startswith('//', j) or text.startswith('/*', j):
                break
            j += 1
        args.append(text[i:j])
        i = j
        if i >= n:
            return args


def _atoi(s: str) -> int:
    """C atoi: optional sign and leading digits, 0 when there are none."""
    s = s.lstrip()
    k = 1 if s[:1] in '+-' else 0
    while k < len(s) and s[k].isdigit():
        k += 1
    try:
        return int(s[:k])
    except ValueError:
        return 0


def server_command_cs(bigcs: list[str], text: str):
    """The configstring half of CL_GetServerCommand (cl_cgame.c:619-663).

    Returns (argv cgame would see, (index, value) or None). bcs0/bcs1 pieces
    are absorbed into bigcs[0] and return ([], None); bcs2 completes the
    string and it is re-scanned as the `cs` it assembles. A `cs` value is
    Cmd_ArgsFrom(2): the tokens after the index, joined by single spaces.
    """
    argv = cmd_tokenize(text)
    if not argv:
        return argv, None
    a = lambda k: argv[k] if k < len(argv) else ''
    cmd = argv[0]
    if cmd == 'bcs0':
        bigcs[0] = 'cs %s "%s' % (a(1), a(2))
        return [], None
    if cmd == 'bcs1':
        if len(bigcs[0]) + len(a(2)) >= _BIG_INFO_STRING:
            raise ValueError('bcs exceeded BIG_INFO_STRING')
        bigcs[0] += a(2)
        return [], None
    if cmd == 'bcs2':
        if len(bigcs[0]) + len(a(2)) + 1 >= _BIG_INFO_STRING:
            raise ValueError('bcs exceeded BIG_INFO_STRING')
        bigcs[0] += a(2) + '"'
        argv = cmd_tokenize(bigcs[0])
        a = lambda k: argv[k] if k < len(argv) else ''
        cmd = argv[0] if argv else ''
    if cmd == 'cs':
        return argv, (_atoi(a(1)), ' '.join(argv[2:]))
    return argv, None


class DM73Parser:
    """Parse a .dm_73 Quake Live demo. Extracts all events, positions, rounds."""

    def __init__(self, path: str | Path, *, track_missiles: bool = False,
                 capture_entities: bool = False):
        self._path   = Path(path)
        # Gate G1 (PANTHEON capture): the entity state after every snapshot,
        # so an independent C reader can be compared with this one. Off by
        # default; every existing caller's output is unchanged.
        self._capture_entities = bool(capture_entities)
        # ('G', configstrings, clientNum, checksumFeed, commandSeq) |
        # ('Q', seq, text) | ('S', serverTime, snapFlags, messageNum, ps, ents)
        # in stream order.
        self._g1_log: list[tuple] = []
        self._cmd_seq: int | None = None      # clc.serverCommandSequence
        self._bigcs: list[str] = ['']         # bcs0/1/2 reassembly
        self._client_num: int | None = None
        self._checksum_feed: int | None = None
        # Enrichment 2026-09-02. Off by default so every existing caller
        # gets byte-identical output; the corpus job turns it on.
        self._track_missiles = bool(track_missiles)
        self._missile_track: list[dict] = []
        self._server_text: list[dict] = []
        self._round_results: list[dict] = []
        self._ps_prev_seq: int | None = None
        self._ps_events: list[dict] = []     # recorder events, edge-deduped by eventSequence
        self._team_changes: list[dict] = []  # (time, client, team) as configstrings change
        self._name_changes: list[dict] = []  # (time, client, name) as configstrings change
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
        # Snapshot history for delta references: messageNum -> (playerstate,
        # entity states) AFTER that snapshot was applied. PACKET_BACKUP is 32
        # in the engine; anything older cannot be referenced.
        # ENTITY LIFETIMES. One span per continuous occupancy of a slot, so a
        # slot that is removed and later reused yields two spans and never one
        # merged history of two different occupants.
        self._ent_lifetime: list[dict] = []
        self._ent_open: dict[int, dict] = {}
        self._snapshot_presence: list[dict] = []
        self._snap_history: dict[int, tuple] = {}
        self._missing_delta_refs = 0
        self._ps_state: dict   = {}           # accumulated playerstate fields
        self._entity_states: dict[int, dict] = {}   # entity_num → accumulated fields
        # Initialised here, NOT in parse(): callers (and tests) drive _dispatch()
        # directly, and a missing attribute there raised AttributeError on every
        # snapshot -- which looked exactly like an 89% packet-drop rate.
        self._ent_track: list[dict] = []
        self._acc_track: list[dict] = []
        self._packet_errors = 0
        self._first_packet_error: str | None = None
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
                    self._dispatch(payload, events, snapshots, seq)
                except Exception as exc:
                    # COUNT failures. A silent `pass` here hid a NameError that
                    # dropped every obituary packet and produced a completely
                    # believable but wrong measurement.
                    self._packet_errors += 1
                    if self._first_packet_error is None:
                        self._first_packet_error = f"{type(exc).__name__}: {exc}"

        # Close the final open round
        if self._cur_round > 0:
            if self._rounds and self._rounds[-1].get('end_ms') is None:
                self._rounds[-1]['end_ms'] = self._last_server_time

        # Spans still open at EOF ended because the RECORDING ended, which is
        # not the same fact as the entity being removed. Label it as such.
        for entity_num in list(self._ent_open):
            self._close_span(entity_num, self._last_server_time,
                             'RECORDING_ENDED')

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
            'entities':     self._ent_track,
            'entity_lifetimes': self._ent_lifetime,
            'snapshot_presence': self._snapshot_presence,
            'server_text':  self._server_text,
            'round_results': self._round_results,
            'missiles':     self._missile_track,
            'team_changes': self._team_changes,
            'name_changes': self._name_changes,
            'accuracy':     self._acc_track,
            'packet_errors': self._packet_errors,
            'first_packet_error': self._first_packet_error,
            **({'g1_log': self._g1_log} if self._capture_entities else {}),
            'player_stats': stats,
        }

    # ── packet dispatcher ─────────────────────────────────────────────────────

    def _dispatch(self, payload: bytes, events: list, snapshots: list,
                  message_num: int = 0):
        """Read EVERY message in the packet, not just the first.

        A packet carries an ack sequence then a SEQUENCE of messages terminated
        by svc_EOF -- Q3's CL_ParseServerMessage and QLDT's DtDemo both loop
        here. Reading one command and returning silently discarded every
        message behind it: measured at ~9% of packets in a 2010 demo starting
        with svc_serverCommand, so any snapshot bundled after one was lost
        along with the obituary entities it carried.
        """
        s = _Bits(self._huff, payload)
        _ = s.readlong()                      # reliable-acknowledge sequence

        while True:
            try:
                cmd = s.readbyte()
            except (IndexError, ValueError):
                return
            if cmd == _SVC_EOF or cmd < 0:
                return
            if cmd == _SVC_GAMESTATE:
                self._parse_gamestate(s)
            elif cmd == _SVC_SERVERCOMMAND:
                self._parse_servercommand(s)
            elif cmd == _SVC_SNAPSHOT:
                self._parse_snapshot(s, events, snapshots, message_num)
            else:
                # Unknown/unhandled opcode: the bit position is no longer
                # trustworthy, so stop rather than decode garbage.
                return

    # ── gamestate ─────────────────────────────────────────────────────────────

    def _parse_gamestate(self, s: _Bits):
        # A gamestate always marks a server command sequence (cl_parse.c:852);
        # commands at or below it are already in the gamestate.
        self._cmd_seq = s.readlong()
        self._bigcs = ['']
        while True:
            cmd = s.readbyte()
            if cmd == _SVC_EOF:
                break
            if cmd == _SVC_CONFIGSTRING:
                idx    = s.readshort()
                string = s.readbigstring()
                self._absorb_cs(idx, string)
            elif cmd == _SVC_BASELINE:
                num   = s.readbits(_GENTITYNUM_BITS)
                delta = self._read_entity_delta(s)
                if delta is not None:
                    self._entity_states[num] = dict(delta)
        self._client_num = s.readlong()       # clientNum
        self._checksum_feed = s.readlong()    # checksumFeed
        if self._capture_entities:
            self._g1_log.append(('G', dict(self._cs), self._client_num,
                                 self._checksum_feed, self._cmd_seq))
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
            # Names change mid-match: renames, reconnects, a freed slot taken
            # by somebody else. One static name->slot map for a whole demo
            # would attribute a chat line to whoever holds the slot LAST, so
            # keep the timeline and let consumers resolve at the chat's time.
            if entry.get('name') != name:
                self._name_changes.append({'server_time_ms': self._last_server_time,
                                           'client': client, 'name': name})
            entry['name'] = name
            entry['team'] = _TEAM_NAMES.get(team, team)
            # Side switches matter for round attribution: keep the timeline.
            if not self._team_changes or self._team_changes[-1].get('client') != client \
                    or self._team_changes[-1].get('team') != entry['team']:
                self._team_changes.append({'server_time_ms': self._last_server_time,
                                           'client': client, 'team': entry['team']})
        if idx in (6, 7, 661, 662, 705):
            # Recorded WITHOUT consuming the index: 662 is also
            # _CS_ROUND_START below, and an elif here silently zeroed the
            # round tracker. 6/7 are CS_SCORES1/2 (team scores): the round
            # winner is the team whose score rises when 662 goes to -1.
            self._round_results.append({
                'server_time_ms': self._last_server_time, 'cs': idx,
                'value': val, 'round': self._cur_round,
            })
        if idx == _CS_ROUND_START:
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
        seq = s.readlong()
        raw = s.readstring()
        # CL_ParseCommandString (cl_parse.c:1356): a reliable command is resent
        # until acknowledged, so a demo carries repeats; the client stores
        # each sequence ONCE. Without this every resent chat line, print and
        # scoreboard was recorded again.
        if self._cmd_seq is not None and seq <= self._cmd_seq:
            return
        self._cmd_seq = seq
        if self._capture_entities:
            self._g1_log.append(('Q', seq, raw))
        argv, change = server_command_cs(self._bigcs, raw)
        if not argv:
            return
        cmd = argv[0]
        if change is not None:
            idx, value = change
            if 0 <= idx < _MAX_CONFIGSTRINGS:
                self._absorb_cs(idx, value)
        elif cmd == 'scores':
            self._absorb_scores(raw)
        elif cmd in ('chat', 'tchat', 'print', 'cp'):
            # Kept raw. Sender names live in this text; consumers that
            # export must redact. Round-win announcements arrive as print/cp.
            self._server_text.append({
                'server_time_ms': self._last_server_time,
                'kind': cmd,
                'text': raw[len(cmd):].strip().strip('"'),
                'round': self._cur_round,
            })

    def _absorb_scores(self, raw: str) -> None:
        """Record per-client accuracy from the Quake Live scoreboard.

        Layout: "scores <n> <team1> <team2>" then n rows of 18 ints. QL extends
        Q3's 13-field row to 18; index 0 is clientNum, 1 score, 2 ping, and
        index 6 is ACCURACY as a percentage. Validated on this corpus: every
        value lands in 0..100 and is stable across successive scoreboards.

        This is OVERALL accuracy -- QL's CA scoreboard carries no per-weapon
        breakdown, so a shaft-specific figure is not available from the demo.
        """
        try:
            tk = raw.split()[1:]
            n = int(tk[0])
            rest = tk[3:]
        except (ValueError, IndexError):
            return
        if n <= 0 or not rest or len(rest) % n:
            return
        w = len(rest) // n
        if w <= 6:
            return
        for i in range(n):
            row = rest[i * w:(i + 1) * w]
            try:
                acc = int(row[6])
                if 0 <= acc <= 100:
                    self._acc_track.append({
                        'server_time_ms': self._last_server_time,
                        'client_num':     int(row[0]),
                        'accuracy':       acc,
                        'score':          int(row[1]),
                    })
            except (ValueError, IndexError):
                continue

    def _parse_snapshot(self, s: _Bits, events: list, snapshots: list,
                        message_num: int = 0):
        """Decode one snapshot against its declared reference."""
        server_time           = s.readlong()
        self._last_server_time = server_time
        delta_num             = s.readbyte()
        snap_flags            = s.readbyte()
        if delta_num == 0:
            # Full update. The frame lists every entity it holds, each decoded
            # against its gamestate baseline (CL_ParsePacketEntities with no
            # old frame). Nothing is present until the frame names it: seeding
            # every baseline here made baseline entities the frame never sent
            # look present.
            self._ps_state = {}
            self._entity_states = {}
            self._entity_prev_etype.clear()
            self._entity_prev_ev.clear()
        else:
            # THE DELTA REFERENCE. The engine decodes against the snapshot at
            # messageNum - deltaNum, not against whatever state happens to be
            # accumulated. Those differ whenever deltaNum > 1, which is 19.34%
            # of snapshots measured over 12 demos: a field changed in a
            # skipped snapshot and then omitted from this delta must revert to
            # the older reference value, and accumulating keeps the skipped one.
            ref = self._snap_history.get(message_num - delta_num)
            if ref is not None:
                self._ps_state = dict(ref[0])
                self._entity_states = {k: dict(v) for k, v in ref[1].items()}
            # A reference we no longer hold (older than the history, or a lost
            # packet) leaves the accumulated state in place. That is the same
            # fallback the client has, and it is recorded rather than hidden.
            elif delta_num:
                self._missing_delta_refs += 1

        area_len              = s.readbyte()
        # Exactly areamaskLen bytes -- see docs/reference/dm73-format-deep-dive.md
        # line 348 ("areamask byte[areamaskLen]") and Q3 CL_ParseSnapshot, which
        # does MSG_ReadData(msg, &areamask, len).
        #
        # This previously read `area_len + 1` on a belief that "QL stores
        # count-1". It does not. The extra byte desynced the bitstream at the
        # start of every snapshot, so the playerstate and every entity delta
        # after it decoded as garbage and ran off the end of the payload.
        # Measured on CA-...asylum-2012_11_11: 15737 of 21389 packets (73.6%)
        # raised IndexError and were silently swallowed by the bare `except`
        # in parse(). With this fix: 0 failures.
        for _ in range(area_len):
            s.readbyte()

        # Read playerstate and collect snapshot
        snap = self._read_playerstate(s)
        snap['server_time_ms'] = server_time
        snap['round_num']      = self._cur_round
        snapshots.append(snap)

        if self._ps_events:
            for pe in self._ps_events:
                code = pe['event_code']
                if code in _CAPTURE_EVENTS:
                    events.append({
                        'type': _EV_NAMES.get(code, f'ev_{code}'),
                        'event_code': code, 'entity_num': None,
                        'server_time_ms': server_time, 'round': self._cur_round,
                        'client_num': self._ps_state.get(_PS_CLIENT),
                        'pos_x': snap.get('origin_x'), 'pos_y': snap.get('origin_y'),
                        'pos_z': snap.get('origin_z'),
                        'weapon': self._ps_state.get(_PS_WEAPON), 'weapon_name': None,
                        'event_parm': pe['parm'], 'source': 'playerstate',
                    })
            self._ps_events = []

        # Read all entity deltas
        changed_this_snapshot: set[int] = set()
        while True:
            entity_num = s.readbits(_GENTITYNUM_BITS)
            if entity_num == _SENTINEL:
                break
            delta = self._read_entity_delta(s)

            if delta is None:
                # Entity removed — clear state and dedup tracking
                if self._track_missiles and \
                        self._entity_states.get(entity_num, {}).get(_F_ETYPE) == 3:
                    self._missile_track.append({
                        'server_time_ms': server_time, 'entity_num': entity_num,
                        'removed': True,
                    })
                self._entity_states.pop(entity_num, None)
                self._entity_prev_etype.pop(entity_num, None)
                self._entity_prev_ev.pop(entity_num, None)
                self._close_span(entity_num, server_time, 'EXPLICIT_REMOVAL')
                continue

            if entity_num not in self._entity_states:
                # Not in the reference frame: the engine decodes it against its
                # gamestate baseline (cl_parse.c:186), and an empty delta means
                # "exactly the baseline" -- present, not absent.
                self._entity_states[entity_num] = dict(
                    self._baseline_entities.get(entity_num, {}))

            if not delta:
                # No-change delta — nothing new to detect
                continue

            # Merge delta into accumulated state
            if entity_num not in self._entity_states:
                self._entity_states[entity_num] = {}
            self._entity_states[entity_num].update(delta)
            accumulated = self._entity_states[entity_num]
            changed_this_snapshot.add(entity_num)

            # Record every PLAYER entity's state this snapshot. Entity numbers
            # below MAX_CLIENTS are players. The playerstate stream only covers
            # whoever the demo followed (measured: 4 clients, 7% of kills had
            # victim coverage), so without this an airshot can only be judged
            # for the demo taker. groundEntityNum makes it exact.
            if self._track_missiles and accumulated.get(_F_ETYPE) == 3:
                # ET_MISSILE = 3 (bg_public.h entityType_t). pos.trBase and
                # pos.trDelta share the player field indices.
                self._missile_track.append({
                    'server_time_ms': server_time, 'entity_num': entity_num,
                    'owner': accumulated.get(_F_CLIENT),
                    # g_missile.c sets s.otherEntityNum to the firer; clientNum
                    # is not reliably the owner on a missile. Both are kept.
                    'other': accumulated.get(_F_VICTIM),
                    'weapon': accumulated.get(_F_WEAPON),
                    'origin_x': accumulated.get(_F_POS_X),
                    'origin_y': accumulated.get(_F_POS_Y),
                    'origin_z': accumulated.get(_F_POS_Z),
                    'vel_x': accumulated.get(_F_VEL_X),
                    'vel_y': accumulated.get(_F_VEL_Y),
                    'vel_z': accumulated.get(_F_VEL_Z),
                    # Without trTime the base and delta cannot be evaluated at
                    # any instant, which is the whole point of a trajectory.
                    'tr_time': accumulated.get(_F_POS_TIME),
                    'tr_type': accumulated.get(_F_POS_TRTYPE),
                    'tr_duration': accumulated.get(_F_POS_TRDUR),
                    'eflags': accumulated.get(_F_EFLAGS),
                    'removed': False,
                })

            # ── event detection: only fire on fields present in this delta ──
            raw_et = delta.get(_F_ETYPE, 0)  # eType changed THIS snapshot
            raw_ev = delta.get(_F_EVENT, 0)  # event field changed THIS snapshot

            event_code = 0
            if raw_et and raw_et > _ET_EVENTS:
                # Temp entity — event encoded in eType
                # Mask THEN subtract. Subtract-then-mask fabricates
                # phantom event numbers when the low byte borrows.
                ec = (raw_et & ~0x300) - _ET_EVENTS
                prev = self._entity_prev_etype.get(entity_num, 0)
                # Compare the RAW eType: EV_EVENT_BIT1/BIT2 exist precisely so
                # two identical consecutive events can be told apart.
                if ec and raw_et != prev:
                    self._entity_prev_etype[entity_num] = raw_et
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

        # Record the state AFTER this snapshot so a later delta can reference
        # it -- HERE, once the entity deltas above are applied. It used to be
        # recorded before the entity loop (while the comment claimed the
        # entities were already decoded), so every reference held the frame
        # BEFORE the one the server deltaed from: a field that changed in the
        # reference and not since reverted a frame, and after an uncompressed
        # frame the reference held only the gamestate baselines, so every
        # player was rebuilt from a partial delta with no eType. Found by gate
        # G1 (the engine's own decoder, host/pantheon_demo_feed.c), 2026-09-12.
        #
        # PACKET_BACKUP is 32 in the engine, so a reference older than that
        # cannot exist; keeping a little more than that costs nothing and
        # avoids evicting an entry a valid delta still wants.
        self._snap_history[message_num] = (
            dict(self._ps_state),
            {k: dict(v) for k, v in self._entity_states.items()})
        if len(self._snap_history) > 64:
            for old_num in sorted(self._snap_history)[:-64]:
                del self._snap_history[old_num]

        if self._capture_entities:
            # G1: the whole playerstate and every entity, every field, as they
            # stand AFTER this snapshot -- what the engine's cl.snap holds.
            self._g1_log.append((
                'S', server_time, snap_flags, message_num,
                dict(self._ps_state),
                {k: dict(v) for k, v in self._entity_states.items()}))

        # ── PRESENCE. _entity_states now holds exactly the entities in this
        # snapshot: entries arrive on a delta and leave only on an explicit
        # removal bit, and the engine writes nothing at all for an entity that
        # did not change (msg.c MSG_WriteDeltaEntity, force=qfalse, !lc). So a
        # player present and motionless is real presence with no bytes, and it
        # gets a row here labelled DELTA_INHERITED rather than vanishing.
        n_present = 0
        for entity_num in sorted(self._entity_states):
            if entity_num >= _MAX_CLIENTS:
                continue
            accumulated = self._entity_states[entity_num]
            n_present += 1
            recorded = entity_num in changed_this_snapshot
            span = self._ent_open.get(entity_num)
            if span is None:
                span = {'entity_num': entity_num, 'first_ms': server_time,
                        'last_ms': server_time, 'samples': 0,
                        'client_num': accumulated.get(_F_CLIENT, entity_num),
                        'end_reason': None}
                self._ent_open[entity_num] = span
                self._ent_lifetime.append(span)
            span['last_ms'] = server_time
            span['samples'] += 1
            g = accumulated.get(_F_GROUND)
            self._ent_track.append({
                'server_time_ms': server_time,
                'entity_num':     entity_num,
                'client_num':     accumulated.get(_F_CLIENT, entity_num),
                'origin_x':       accumulated.get(_F_POS_X),
                'origin_y':       accumulated.get(_F_POS_Y),
                'origin_z':       accumulated.get(_F_POS_Z),
                'vel_x':          accumulated.get(_F_VEL_X),
                'vel_y':          accumulated.get(_F_VEL_Y),
                'vel_z':          accumulated.get(_F_VEL_Z),
                'angle_yaw':      accumulated.get(_F_YAW),
                'angle_pitch':    accumulated.get(_F_PITCH),
                'move_dir':       accumulated.get(_F_ANGLES2_YAW),
                'weapon':         accumulated.get(_F_WEAPON),
                'ground_entity':  g,
                # None = field never sent = standing on world (default 0).
                'airborne':       (g == _ENTITYNUM_NONE),
                # HOW this row came to exist. RECORDED means this snapshot's
                # delta carried at least one field for the entity;
                # DELTA_INHERITED means every value is carried forward from the
                # delta reference and the entity simply did not change.
                'state_provenance': 'RECORDED' if recorded else 'DELTA_INHERITED',
            })
        self._snapshot_presence.append({
            'server_time_ms': server_time,
            'players_present': n_present,
            'players_recorded': len(
                [e for e in changed_this_snapshot if e < _MAX_CLIENTS]),
            'entities_present': len(self._entity_states),
        })

    def _close_span(self, entity_num: int, server_time: int, reason: str):
        """End a lifetime span. A later re-add opens a NEW span, which is what
        makes entity slot reuse visible instead of silently splicing two
        occupants into one history."""
        span = self._ent_open.pop(entity_num, None)
        if span is not None:
            span['end_ms'] = server_time
            span['end_reason'] = reason

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
            # A PLAYER ENTITY'S NUMBER IS ITS CLIENT NUMBER. Entity slots
            # 0..MAX_CLIENTS-1 are the players (bg_public.h; verified against
            # the corpus, where pain and death match entity_num == client_num
            # 100% of the time). The clientNum FIELD is delta-compressed and
            # usually absent, so reading only that left client_num null on
            # most events -- fire_weapon resolved a client on 38.9% of rows,
            # and every per-player attribution built on it silently lost the
            # rest. Entities at or above MAX_CLIENTS stay null: those are
            # missiles, movers and freestanding ET_EVENTS, which have no
            # client by construction.
            'client_num':     (accumulated.get(_F_CLIENT)
                               if accumulated.get(_F_CLIENT) is not None
                               else (entity_num if entity_num is not None
                                     and 0 <= entity_num < _MAX_CLIENTS
                                     else None)),
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
            # Entity-sourced missile events carry the MISSILE's s.weapon, which is
            # the WP_ launcher space (g_missile.c: bolt->s.weapon = WP_*), not the
            # MOD_ means-of-death space used by obituaries. Measured 2026-09-02
            # over v1.0.3 demos: grenade frags -> 4, rocket -> 5, plasma -> 8.
            ev['weapon_name'] = _WP_NAMES.get(ev['weapon'], None)
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
                    v = s.readbits(bits)
                    # A negative declared width is a SIGNED field (msg.c
                    # MSG_ReadBits sign-extends): weaponTime, pm_time,
                    # viewheight. Read unsigned, a crouch viewheight of -8
                    # came back as 248.
                    if i in _PS_SIGNED and v >= 1 << (bits - 1):
                        v -= 1 << bits
                    self._ps_state[i] = v
        if s.readbits(1):   # has extra sections
            if s.readbits(1):   # stats
                c = s.readshort()
                for j in range(_MAX_STATS):
                    if c & (1 << j):
                        self._ps_state[f's{j}'] = s.readshort()
            # Kept, not discarded: cgame draws from all four arrays, and gate
            # G1 compares every field the engine holds.
            if s.readbits(1):   # persistant
                c = s.readshort()
                for j in range(_MAX_PERSISTANT):
                    if c & (1 << j):
                        self._ps_state[f'p{j}'] = s.readshort()
            if s.readbits(1):   # ammo
                c = s.readshort()
                for j in range(_MAX_WEAPONS):
                    if c & (1 << j):
                        self._ps_state[f'a{j}'] = s.readshort()
            if s.readbits(1):   # powerups
                c = s.readshort()
                for j in range(_MAX_POWERUPS):
                    if c & (1 << j):
                        self._ps_state[f'w{j}'] = s.readlong()

        ps = self._ps_state
        seq = ps.get(_PS_EVENT_SEQ)
        if seq is not None:
            if self._ps_prev_seq is None:
                self._ps_prev_seq = seq          # first snapshot: no edge yet
            else:
                start = max(self._ps_prev_seq, seq - _MAX_PS_EVENTS)
                for i in range(start, seq):
                    code = ps.get(_PS_EVENT0 if (i & 1) == 0 else _PS_EVENT1, 0)
                    parm = ps.get(_PS_EVPARM0 if (i & 1) == 0 else _PS_EVPARM1, 0)
                    code = (code or 0) & ~0x300
                    if code:
                        self._ps_events.append({'seq': i, 'event_code': code, 'parm': parm})
                self._ps_prev_seq = seq
        ox = ps.get(_PS_ORIGIN_X)
        oy = ps.get(_PS_ORIGIN_Y)
        ps_ground = ps.get(_PS_GROUND)
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
            'airborne':    (ps_ground == _ENTITYNUM_NONE) if ps_ground is not None else None,
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

            # DAMAGE TAKEN BY THE POV PLAYER, straight out of the playerstate.
            # g_active.c::P_DamageFeedback:
            #     count = client->damage_blood + client->damage_armor;
            #     if (count > 255) count = 255;
            #     G_AddEvent(player, EV_PAIN, player->health);
            #     client->ps.damageCount = count;
            #
            # So EV_PAIN's parm is HEALTH AFTER, not damage -- a pain event is
            # not a per-hit damage ledger. damageCount is the damage number,
            # and it is AGGREGATED (blood + armour, possibly several hits in
            # one server frame) and CLAMPED AT 255. It says how much the POV
            # player was hurt, never how much they dealt.
            #
            # damageYaw/damagePitch give the direction it came from, which is
            # evidence toward an attacker but not an identity.
            'damage_count': ps.get(_PS_DMG_COUNT),
            'damage_event': ps.get(_PS_DMG_EVENT),
            'damage_yaw':   ps.get(_PS_DMG_YAW),
            'damage_pitch': ps.get(_PS_DMG_PITCH),
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
                    else:
                        # Changed TO zero (msg.c:1347). Recorded, not left out:
                        # an absent key means "unchanged", so omitting it kept
                        # the old value alive in the accumulated state.
                        out[i] = 0.0
                else:           # integer field
                    if s.readbits(1):   # non-zero
                        out[i] = s.readbits(bits)
                    else:
                        out[i] = 0      # changed to zero (msg.c:1368)
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
