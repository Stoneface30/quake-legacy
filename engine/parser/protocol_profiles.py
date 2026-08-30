"""Per-build netfield profiles for Quake Live dm_73.

Quake Live kept the `.dm_73` extension and Q3-style netcode across years of
builds while changing protocol-level details. One hardcoded entity-state table
is therefore wrong for part of the corpus, and wrong quietly: the bitstream
still consumes perfectly (zero dropped packets) while field ordinals carry
different meanings.

    Zero dropped packets proves FRAMING. It says nothing about SEMANTICS.

Four concepts are kept strictly separate here, because conflating them is what
produced a wasted investigation cycle:

    wire ordinal      index of the field on the wire (0..N)
    semantic field    what that ordinal MEANS under a profile
    raw eType         the entity's reconstructed eType byte
    normalized event  (raw_eType & ~EV_EVENT_BITS) - ET_EVENTS
    `event` field     wire ordinal 10 -- a DIFFERENT field from eType

Obituary recognition (QLDT old-dm_73 semantics):

    (eType & ~EV_EVENT_BITS) == ET_EVENTS + EV_OBITUARY
    eventParm      -> means of death
    otherEntityNum -> victim
    otherEntityNum2-> attacker

For the 2012-era profile ET_EVENTS=13 and EV_OBITUARY=58, so the obituary
entity's base eType is 71 -- verified: 117 such entities in
CA-Gr0sTR4SH-asylum-2012_11_11, each carrying MOD/victim/attacker with
lastField=32 and changed ordinals [1,2,5,12,14,19,31].

STATUS OF THE 2010-2011 PROFILE: PROVEN (2026-08-30). See RESOLVED below.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

EV_EVENT_BITS = 0x300


@dataclass(frozen=True)
class Profile:
    """One build's entity-state wire layout and event enum."""

    name: str
    et_events: int                    # ET_EVENTS
    ev_obituary: int                  # EV_OBITUARY enum for this build
    bits: tuple[int, ...]             # wire ordinal -> bit width (0 = float)
    ordinals: dict[str, int]          # semantic name -> wire ordinal
    verified_on: tuple[str, ...] = ()
    proven: bool = False

    @property
    def obituary_base_etype(self) -> int:
        """Raw eType (event bits masked off) of an obituary event entity."""
        return self.et_events + self.ev_obituary

    def is_obituary(self, raw_etype: int | None) -> bool:
        if raw_etype is None:
            return False
        return (raw_etype & ~EV_EVENT_BITS) == self.obituary_base_etype

    def normalized_event(self, raw_etype: int | None) -> int | None:
        """Event number encoded in an event entity's eType, or None."""
        if raw_etype is None:
            return None
        base = raw_etype & ~EV_EVENT_BITS
        return base - self.et_events if base > self.et_events else None

    def ord_of(self, semantic: str) -> int | None:
        return self.ordinals.get(semantic)

    def semantic_of(self, ordinal: int) -> str | None:
        for k, v in self.ordinals.items():
            if v == ordinal:
                return k
        return None


# ── QL late-2012 (VERIFIED) ─────────────────────────────────────────────────
# Matches the old-dm_73 table published by QLDT (redrumrobot/qldt, Dm73.cpp):
# ordinal 9 is QL's pos.gravity, which is the insertion that shifts every
# later ordinal by one relative to stock Q3. A single-field insertion is enough
# to consume the bitstream perfectly while attaching wrong meanings.
QL_2012 = Profile(
    name="ql-2012",
    et_events=13,
    ev_obituary=58,
    bits=(
        32, 0, 0, 0, 0, 0, 0, 0, 0, 32,
        10, 0, 8, 8, 8, 8, 10, 8, 19, 10,
        8, 8, 0, 32, 8, 0, 0, 0, 24, 16,
        8, 10, 8, 8, 0, 0, 0, 8, 0, 32,
        32, 32, 0, 0, 0, 0, 32, 32, 0, 0,
        0, 32, 16,
    ),
    ordinals={
        "pos.trTime": 0,
        "pos.trBase[0]": 1, "pos.trBase[1]": 2,
        "pos.trDelta[0]": 3, "pos.trDelta[1]": 4,
        "pos.trBase[2]": 5, "apos.trBase[1]": 6,
        "pos.trDelta[2]": 7, "apos.trBase[0]": 8,
        "pos.gravity": 9,
        "event": 10, "eType": 12, "eventParm": 14,
        "groundEntityNum": 16, "eFlags": 18,
        "otherEntityNum": 19, "weapon": 20, "clientNum": 21,
        "otherEntityNum2": 31,
        "origin2[2]": 34, "origin2[0]": 35, "origin2[1]": 36,
    },
    verified_on=("CA-Gr0sTR4SH-asylum-2012_11_11-19_54_18.dm_73",),
    proven=True,
)

# ── NO SECOND PROFILE ───────────────────────────────────────────────────────
# A `ql-2010-2011` profile was drafted here on the belief that older builds used
# a different wire schema. That belief was WRONG and the profile is deleted.
#
# Root cause of the old-demo undercount was our own packet dispatcher consuming
# only the first service message per packet. After fixing it, demos across
# builds .350 / .386 / .393 / .405 / .419 / .495 all recover plausible Clan
# Arena frag counts (103-296, from 0-3) using THIS ONE TABLE. Three independent
# implementations -- QLDT, wolfcamql, UberDemoTools -- also ship exactly one
# dm_73 entity-state table.
#
# Do not reintroduce date-based protocol guessing.

PROFILES = {p.name: p for p in (QL_2012,)}
DEFAULT = QL_2012


def select(evidence: dict[str, Any] | None = None) -> Profile:
    """Choose a profile from build evidence.

    Deliberately returns the verified profile until a real discriminator
    exists. It must NEVER pick "whichever profile yields more kills" -- that
    optimises a metric instead of decoding the protocol, and would bake a wrong
    table into the corpus.
    """
    return DEFAULT


# RESOLVED (2026-08-30): the 2010-2011 obituary representation
#
# It decodes correctly with THIS table. The earlier "unresolved" note rested on
# measurements from the pre-fix parser, and every one of its premises is now
# contradicted by the bytes.
#
# Evidence, from engine/parser/probe_events.py on
# CA-hearth-2011_08_02-18_48_01.dm_73 (roster: 0 s73rn RED, 1 Tr4sH SPECTATOR,
# 2 NaikoMarie BLUE -- a 1v1 with a spectator):
#
#   probe 1  t=70500   ent 128  raw eType 71 -> base 71 -> event 58
#            ordinals [1,2,5,12,14,19]  eventParm 11 (LIGHTNING)
#            ordinal 19 present (victim=2), ordinal 31 ABSENT
#   probe 2  t=100050  ent 115  raw eType 71 -> base 71 -> event 58
#            ordinals [1,2,5,12,14,31]  eventParm 10 (RAILGUN)
#            ordinal 31 present (attacker=2), ordinal 19 ABSENT
#   probe 3  t=119600  ent 120  same shape as probe 2
#
# The old note claimed "ordinal 31 transmitted 0 times". It IS transmitted --
# probes 2 and 3 carry it. What actually happens: a delta omits whichever of
# victim/attacker equals the BASELINE (0). In a 1v1 between clients 0 and 2,
# exactly one of the pair is 0 in every kill, so exactly one ordinal is omitted.
# An absent ordinal means "equals baseline", not "missing data", and client 0 is
# a real player here rather than a fabricated default.
#
# Independent corroboration on the same demo (engine/parser/score_oracle.py):
# 24 score increments, 24 matched to a decoded obituary within 3000 ms,
# 0 unmatched -- implied detector recall 100%.
#
# eType 95 is CLOSED as an artefact. Scanned across 10 demos spanning 2010-2012:
# base eType 95 occurs ZERO times, and the maximum base eType observed anywhere
# is 77. The earlier sighting came from the pre-fix parser, which both truncated
# packet dispatch and masked in the wrong order -- subtract-then-mask fabricates
# values that mask-then-subtract never produces. It is not an obituary temp
# entity; it does not exist.
#
# tinfo is unavailable as a 2010-2011 oracle, and that is a property of the
# BUILD, not of our decoder. A servercommand census shows the 2011 demo emits
# cs / scores / bcs* / print / rcmd / map_restart and no `tinfo` at all, while
# the 2012 demo emits tinfo 1086 times alongside cascores and castats. For the
# older era, use `scores`.
