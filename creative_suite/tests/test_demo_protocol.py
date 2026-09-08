"""The protocol registry is tied to the engine's own tables, not to us.

Every check here re-reads `engine/engines/_canonical/code/qcommon/msg.c` and
compares. The parser and the writer are then compared against the REGISTRY,
so the three cannot drift into agreeing with each other while all being
wrong -- which is the failure mode that produced a byte-perfect round trip
rendering nothing, twice.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from engine.parser import demo_parse as dp
from engine.parser import dm73_write as W
from engine.parser import protocol as P

pytestmark = pytest.mark.skipif(
    not P.CANONICAL_MSG_C.exists(),
    reason=f"canonical engine source not on this machine ({P.CANONICAL_MSG_C})")


# ── the registry against the engine ────────────────────────────────────────

def test_entity_table_matches_entityStateFieldsQldm73():
    """Protocol 73 reads entities through this table and no other."""
    rows = P.parse_canonical_table("entityStateFieldsQldm73")
    assert len(rows) == len(P.ENTITY_FIELDS), (
        f"engine has {len(rows)} entity fields, the registry has {len(P.ENTITY_FIELDS)}")
    for (member, width), field in zip(rows, P.ENTITY_FIELDS):
        assert member == field.name, f"index {field.index}: engine {member}, registry {field.name}"
        assert P.canonical_bits(width) == field.bits, f"{member}: bits differ"


def test_playerstate_table_is_the_q3_one_and_matches():
    """There is no playerStateFieldsQldm73. The engine falls through to the
    Q3 table for protocol 73 -- the dispatch says so in a comment -- and
    that is the table the registry transcribes."""
    src = P.CANONICAL_MSG_C.read_text(encoding="utf-8", errors="replace")
    assert "playerStateFieldsQldm73" not in src
    i = src.index("field = playerStateFieldsQ3;")
    assert "also qldm 73" in src[i - 200:i], "the fall-through comment moved; re-derive"

    rows = P.parse_canonical_table("playerStateFieldsQ3")
    assert len(rows) == len(P.PLAYER_FIELDS)
    for (member, width), field in zip(rows, P.PLAYER_FIELDS):
        assert member == field.name, f"index {field.index}: engine {member}, registry {field.name}"
        assert P.canonical_bits(width) == field.bits, f"{member}: bits differ"


# ── the parser and writer against the registry ─────────────────────────────

def test_the_parser_bit_tables_are_the_registry_tables():
    assert dp._ES_BITS == P.ES.bits()
    assert dp._PS_BITS == P.PS.bits()


@pytest.mark.parametrize("attr,member", [
    ("_F_POS_X", "pos.trBase[0]"), ("_F_POS_Y", "pos.trBase[1]"),
    ("_F_POS_Z", "pos.trBase[2]"), ("_F_VEL_X", "pos.trDelta[0]"),
    ("_F_VEL_Y", "pos.trDelta[1]"), ("_F_VEL_Z", "pos.trDelta[2]"),
    ("_F_YAW", "apos.trBase[1]"), ("_F_PITCH", "apos.trBase[0]"),
    ("_F_EVENT", "event"), ("_F_ETYPE", "eType"), ("_F_EVPARM", "eventParm"),
    ("_F_GROUND", "groundEntityNum"), ("_F_EFLAGS", "eFlags"),
    ("_F_VICTIM", "otherEntityNum"), ("_F_KILLER", "otherEntityNum2"),
    ("_F_WEAPON", "weapon"), ("_F_CLIENT", "clientNum"),
])
def test_every_parser_field_constant_is_the_engine_index(attr: str, member: str):
    assert getattr(dp, attr) == P._index_of(P.ENTITY_FIELDS, member), (
        f"demo_parse.{attr} does not point at {member}")


def test_the_writer_reuses_the_parser_indices_rather_than_inventing_them():
    """A first version of the writer invented its own indices; every
    round-trip test passed because it compared them against themselves, and
    the engine drew nothing."""
    assert (W.ES_POS_X, W.ES_POS_Y, W.ES_POS_Z) == (P.ES.POS_X, P.ES.POS_Y, P.ES.POS_Z)
    assert (W.ES_VEL_X, W.ES_VEL_Y, W.ES_VEL_Z) == (P.ES.VEL_X, P.ES.VEL_Y, P.ES.VEL_Z)
    assert W.ES_APOS_YAW == P.ES.YAW and W.ES_APOS_PITCH == P.ES.PITCH
    assert W.ES_ETYPE == P.ES.ETYPE and W.ES_EVENT == P.ES.EVENT
    assert W.ES_EVENTPARM == P.ES.EVENTPARM and W.ES_GROUND == P.ES.GROUND
    assert W.ES_OTHER_ENT == P.ES.OTHER_ENTITY and W.ES_OTHER_ENT2 == P.ES.OTHER_ENTITY2
    assert W.ES_WEAPON == P.ES.WEAPON and W.ES_CLIENTNUM == P.ES.CLIENTNUM
    assert W.ES_LEGS_ANIM == P.ES.LEGS_ANIM and W.ES_TORSO_ANIM == P.ES.TORSO_ANIM
    assert (W.PS_ORIGIN_X, W.PS_ORIGIN_Y, W.PS_ORIGIN_Z) == (
        P.PS.ORIGIN_X, P.PS.ORIGIN_Y, P.PS.ORIGIN_Z)
    assert W.PS_YAW == P.PS.YAW and W.PS_PITCH == P.PS.PITCH
    assert W.PS_CLIENTNUM == P.PS.CLIENTNUM and W.PS_WEAPON == P.PS.WEAPON
    assert W.PS_GROUND == P.PS.GROUND


def test_the_playerstate_animation_ordinals_are_confirmed_not_guessed():
    """PS torsoAnim=14 / legsAnim=17 were established empirically on a real
    demo before the table was read. The table agrees."""
    assert P.PS.TORSO_ANIM == 14 and P.PS.LEGS_ANIM == 17
    from engine.pantheon import performance as perf
    assert perf.PS_TORSO_ANIM == P.PS.TORSO_ANIM
    assert perf.PS_LEGS_ANIM == P.PS.LEGS_ANIM
    assert perf.PS_ORIGIN == (P.PS.ORIGIN_X, P.PS.ORIGIN_Y, P.PS.ORIGIN_Z)
    assert perf.PS_VELOCITY == (P.PS.VEL_X, P.PS.VEL_Y, P.PS.VEL_Z)
    assert (perf.PS_YAW, perf.PS_PITCH) == (P.PS.YAW, P.PS.PITCH)
    assert (perf.PS_GROUND, perf.PS_CLIENT, perf.PS_WEAPON) == (
        P.PS.GROUND, P.PS.CLIENTNUM, P.PS.WEAPON)
    assert (perf.ES_TORSO_ANIM, perf.ES_LEGS_ANIM) == (P.ES.TORSO_ANIM, P.ES.LEGS_ANIM)


# ── the enumerations against the parser's verified tables ──────────────────

def test_event_codes_match_the_parsers_verified_names():
    """The registry is the PROTOCOL authority and knows codes the parser does
    not capture (EV_MISSILE_MISS_METAL, for one). What must hold is the other
    direction: every code the parser captures is named here, with the same
    meaning."""
    for code, name in dp._EV_NAMES.items():
        assert code in {int(e) for e in P.Event}, f"parser captures {code} ({name}); registry does not name it"
    # The parser shortens three engine names; every other name is the enum's
    # own, lower-cased. Stated here so a NEW divergence is a failure rather
    # than another quiet alias.
    SHORTENED = {P.Event.PLAYER_TELEPORT_IN: "teleport_in",
                 P.Event.PLAYER_TELEPORT_OUT: "teleport_out",
                 P.Event.DEATH1: "death", P.Event.DEATH2: "death",
                 P.Event.DEATH3: "death"}
    for ev in P.Event:
        got = dp._EV_NAMES.get(int(ev))
        if got is None:
            continue
        want = SHORTENED.get(ev, ev.name.lower())
        assert got == want, f"{ev.name}: parser says {got!r}, expected {want!r}"
    assert dp._EV_NAMES[int(P.Event.FIRE_WEAPON)] == "fire_weapon"
    assert dp._EV_NAMES[int(P.Event.OBITUARY)] == "obituary"
    assert dp._EV_NAMES[int(P.Event.JUMP_PAD)] == "jump_pad"


def test_means_of_death_is_a_different_space_from_weapon():
    """A rocket kill is weapon 5 and MOD 6/7. Conflating the two put
    LIGHTNING on a rail teaching card once."""
    assert int(P.Weapon.ROCKET_LAUNCHER) == 5
    assert int(P.MeansOfDeath.ROCKET) == 6 and int(P.MeansOfDeath.ROCKET_SPLASH) == 7
    assert P.MOD_FOR_WEAPON[P.Weapon.ROCKET_LAUNCHER] is P.MeansOfDeath.ROCKET
    assert P.MOD_FOR_WEAPON[P.Weapon.RAILGUN] is P.MeansOfDeath.RAILGUN
    for mod in P.MeansOfDeath:
        assert dp._MOD_NAMES[int(mod)] == mod.name, f"{mod!r} disagrees with the parser"
    for w in P.Weapon:
        if int(w):
            assert dp._WP_NAMES[int(w)] == w.name


def test_entity_types_and_the_temp_entity_rule():
    assert int(P.EntityType.EVENTS) == 13 == dp._ET_EVENTS
    assert int(P.EntityType.MISSILE) == 3
    assert P.EVENT_SEQUENCE_BITS == 0x300
    assert P.ANIM_TOGGLEBIT == 128
    assert P.ENTITYNUM_NONE == 1023 == dp._ENTITYNUM_NONE


def test_configstrings_name_the_slots_the_compiler_writes():
    from engine.pantheon import compiler as C
    assert C.CS_ROUND_STATUS == int(P.ConfigString.ROUND_STATUS)
    assert C.CS_ROUND_TIME == int(P.ConfigString.ROUND_TIME)
    assert C.CS_RED_PLAYERS_LEFT == int(P.ConfigString.RED_PLAYERS_LEFT)
    assert C.CS_BLUE_PLAYERS_LEFT == int(P.ConfigString.BLUE_PLAYERS_LEFT)
    assert C.CS_ROUND_WINNERS == int(P.ConfigString.ROUND_WINNERS)
    assert W.CS_PLAYERS == int(P.ConfigString.PLAYERS)


def test_animation_numbers_match_the_writers_profiled_values():
    assert W.LEGS_RUN == int(P.Anim.LEGS_RUN) == 15
    assert W.LEGS_JUMP == int(P.Anim.LEGS_JUMP) == 18
    assert W.LEGS_LAND == int(P.Anim.LEGS_LAND) == 19
    assert W.LEGS_IDLE == int(P.Anim.LEGS_IDLE) == 22
    assert W.TORSO_ATTACK == int(P.Anim.TORSO_ATTACK) == 7
    assert W.TORSO_STAND == int(P.Anim.TORSO_STAND) == 11
    assert P.Anim.LEGS_JUMP not in P.LEGS_GROUNDED
    assert P.Anim.LEGS_RUN in P.LEGS_GROUNDED and P.Anim.LEGS_RUN in P.LEGS_RUNNING


# ── no magic numbers above the protocol layer ──────────────────────────────

PROTOCOL_LAYER = {"engine/parser/protocol.py", "engine/parser/demo_parse.py",
                  "engine/parser/dm73_write.py", "engine/pantheon/compiler.py",
                  "engine/parser/synthetic_ca.py", "engine/parser/ca_reference.py"}
REPO = Path(__file__).resolve().parents[2]
# Numbers that mean something on the wire and must not appear as literals in
# feature code: the CA configstring slots and the event codes we act on.
BANNED_LITERALS = {661, 662, 663, 664, 705, 1023}


def test_feature_code_does_not_spell_protocol_numbers():
    offenders: list[str] = []
    for base in ("engine/pantheon", "creative_suite/engine"):
        for path in (REPO / base).rglob("*.py"):
            rel = path.relative_to(REPO).as_posix()
            if rel in PROTOCOL_LAYER or "/tests/" in rel or "__pycache__" in rel:
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, int) \
                        and node.value in BANNED_LITERALS:
                    offenders.append(f"{rel}:{node.lineno} -> {node.value}")
    assert not offenders, ("protocol numbers spelled outside the protocol layer; "
                           f"use engine.parser.protocol: {offenders[:8]}")
