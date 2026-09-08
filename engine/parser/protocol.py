"""DemoProtocolRegistry — the one authority on what a .dm_73 byte means.

Every field index, bit width, event code, means-of-death, entity type,
configstring slot, animation number and weapon slot this project depends on
is named here, once, with where it came from. Feature code says
`ES.LEGS_ANIM`; it never says `15`.

WHERE THE NUMBERS COME FROM. `engine/engines/_canonical/code/qcommon/msg.c`
carries the engine's own tables. Protocol 73 reads entities through
`entityStateFieldsQldm73` and — the source says so in a comment at the
dispatch, `// also qldm 73` — reads the playerstate through
`playerStateFieldsQ3`. Both tables are transcribed below in wire order, and
`creative_suite/tests/test_demo_protocol.py` re-parses that .c file on every
run and fails if this file drifts from it. The tables are not "agreed" with
the parser; both are checked against the engine.

WHAT THE RECONCILIATION FOUND (2026-09-06). Nothing wrong. All 53 entity
fields and all 48 playerstate fields, including every bit width, already
matched `demo_parse._ES_BITS` / `_PS_BITS` and every `_F_*` index the parser
uses. The playerstate ordinals `torsoAnim=14` and `legsAnim=17`, which had
been established empirically on a real demo, are confirmed by the table. The
value of this module is therefore not a correction; it is that the numbers
now have ONE home and a test that keeps them tied to the engine.

OBSERVABILITY IS PART OF THE CONTRACT. A field the wire carries is not the
same as a field PANTHEON can trust: `origin[]` on an entity is the render
position the client interpolates, while `pos.trBase[]` is what the server
sent. Each field carries a note where that distinction matters.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path

def _project_root() -> Path:
    """`engine/engines/_canonical/` is gitignored, so it exists once, in the
    main checkout. A worktree under `.claude/worktrees/<name>/` must look
    above its own `.claude`, the same way the data store does."""
    import os
    raw = os.getenv("QUAKE_LEGACY_ROOT", "").strip()
    if raw:
        return Path(raw)
    here = Path(__file__).resolve().parents[2]
    parts = here.parts
    if ".claude" in parts and "worktrees" in parts:
        return Path(*parts[:parts.index(".claude")])
    return here


CANONICAL_MSG_C = (_project_root() / "engine" / "engines" / "_canonical"
                   / "code" / "qcommon" / "msg.c")

# Widths the engine writes as symbols rather than literals.
GENTITYNUM_BITS = 10
MAX_POWERUPS = 16
FLOAT_INT_BITS = 13
FLOAT_INT_BIAS = 1 << (FLOAT_INT_BITS - 1)
ENTITYNUM_NONE = (1 << GENTITYNUM_BITS) - 1          # 1023
MAX_CLIENTS = 64


@dataclass(frozen=True)
class Field:
    """One netfield: where it sits on the wire and what it means."""
    index: int
    name: str                 # the engine's own member name
    bits: int                 # 0 = float; negative in source means signed
    note: str = ""

    @property
    def is_float(self) -> bool:
        return self.bits == 0


def _table(rows: list[tuple[str, int, str]]) -> tuple[Field, ...]:
    return tuple(Field(i, n, b, note) for i, (n, b, note) in enumerate(rows))


# ── entityState, protocol 73 (entityStateFieldsQldm73) ─────────────────────
ENTITY_FIELDS = _table([
    ("pos.trTime", 32, ""),
    ("pos.trBase[0]", 0, "server-sent position X"),
    ("pos.trBase[1]", 0, "server-sent position Y"),
    ("pos.trDelta[0]", 0, "velocity X"),
    ("pos.trDelta[1]", 0, "velocity Y"),
    ("pos.trBase[2]", 0, "server-sent position Z"),
    ("apos.trBase[1]", 0, "view yaw"),
    ("pos.trDelta[2]", 0, "velocity Z"),
    ("apos.trBase[0]", 0, "view pitch"),
    ("pos.gravity", 32, "Quake Live addition; absent from stock Q3"),
    ("event", 10, "player-carried event; low bits code, 0x300 sequence"),
    ("angles2[1]", 0, ""),
    ("eType", 8, "ET_*; >= ET_EVENTS means a temp entity carrying an event"),
    ("torsoAnim", 8, "animNumber_t, ANIM_TOGGLEBIT at 128"),
    ("eventParm", 8, ""),
    ("legsAnim", 8, "animNumber_t, ANIM_TOGGLEBIT at 128"),
    ("groundEntityNum", GENTITYNUM_BITS, "ENTITYNUM_NONE means airborne"),
    ("pos.trType", 8, "trajectory_t"),
    ("eFlags", 19, ""),
    ("otherEntityNum", GENTITYNUM_BITS, "obituary victim; missile target"),
    ("weapon", 8, "weapon_t on a player; WP_* on a missile"),
    ("clientNum", 8, ""),
    ("angles[1]", 0, ""),
    ("pos.trDuration", 32, ""),
    ("apos.trType", 8, ""),
    ("origin[0]", 0, "render position, NOT the server's pos.trBase"),
    ("origin[1]", 0, "render position, NOT the server's pos.trBase"),
    ("origin[2]", 0, "render position, NOT the server's pos.trBase"),
    ("solid", 24, ""),
    ("powerups", MAX_POWERUPS, ""),
    ("modelindex", 8, ""),
    ("otherEntityNum2", GENTITYNUM_BITS, "obituary killer"),
    ("loopSound", 8, ""),
    ("generic1", 8, ""),
    ("origin2[2]", 0, ""),
    ("origin2[0]", 0, "rail trail muzzle end; unread when cg_railFromMuzzle=1"),
    ("origin2[1]", 0, ""),
    ("modelindex2", 8, ""),
    ("angles[0]", 0, ""),
    ("time", 32, ""),
    ("apos.trTime", 32, ""),
    ("apos.trDuration", 32, ""),
    ("apos.trBase[2]", 0, "view roll"),
    ("apos.trDelta[0]", 0, ""),
    ("apos.trDelta[1]", 0, ""),
    ("apos.trDelta[2]", 0, ""),
    ("apos.gravity", 32, "Quake Live addition"),
    ("time2", 32, ""),
    ("angles[2]", 0, ""),
    ("angles2[0]", 0, ""),
    ("angles2[2]", 0, ""),
    ("constantLight", 32, ""),
    ("frame", 16, ""),
])

# ── playerState, protocol 73 (playerStateFieldsQ3 — see the module docstring)
PLAYER_FIELDS = _table([
    ("commandTime", 32, ""),
    ("origin[0]", 0, "the POV's own position; authoritative, not interpolated"),
    ("origin[1]", 0, ""),
    ("bobCycle", 8, ""),
    ("velocity[0]", 0, ""),
    ("velocity[1]", 0, ""),
    ("viewangles[1]", 0, "yaw"),
    ("viewangles[0]", 0, "pitch"),
    ("weaponTime", 16, "signed in source (-16)"),
    ("origin[2]", 0, ""),
    ("velocity[2]", 0, ""),
    ("legsTimer", 8, ""),
    ("pm_time", 16, "signed in source (-16)"),
    ("eventSequence", 16, ""),
    ("torsoAnim", 8, "confirmed against entityStateFieldsQ3 ordering"),
    ("movementDir", 4, ""),
    ("events[0]", 8, ""),
    ("legsAnim", 8, "confirmed against entityStateFieldsQ3 ordering"),
    ("events[1]", 8, ""),
    ("pm_flags", 16, ""),
    ("groundEntityNum", GENTITYNUM_BITS, "ENTITYNUM_NONE means airborne"),
    ("weaponstate", 4, ""),
    ("eFlags", 16, ""),
    ("externalEvent", 10, ""),
    ("gravity", 16, ""),
    ("speed", 16, ""),
    ("delta_angles[1]", 16, ""),
    ("externalEventParm", 8, ""),
    ("viewheight", 8, "signed in source (-8)"),
    ("damageEvent", 8, ""),
    ("damageYaw", 8, ""),
    ("damagePitch", 8, ""),
    ("damageCount", 8, ""),
    ("generic1", 8, ""),
    ("pm_type", 8, ""),
    ("delta_angles[0]", 16, ""),
    ("delta_angles[2]", 16, ""),
    ("torsoTimer", 12, ""),
    ("eventParms[0]", 8, ""),
    ("eventParms[1]", 8, ""),
    ("clientNum", 8, "which client the POV is"),
    ("weapon", 5, ""),
    ("viewangles[2]", 0, "roll"),
    ("grapplePoint[0]", 0, ""),
    ("grapplePoint[1]", 0, ""),
    ("grapplePoint[2]", 0, ""),
    ("jumppad_ent", 10, ""),
    ("loopSound", 16, ""),
])


def _index_of(table: tuple[Field, ...], name: str) -> int:
    for f in table:
        if f.name == name:
            return f.index
    raise KeyError(f"no netfield named {name!r}")


class _Named:
    """Semantic names over one table. `ES.LEGS_ANIM` instead of 15."""

    def __init__(self, table: tuple[Field, ...], names: dict[str, str]) -> None:
        self._table = table
        for attr, member in names.items():
            setattr(self, attr, _index_of(table, member))

    def field(self, index: int) -> Field:
        return self._table[index]

    def bits(self) -> list[int]:
        return [f.bits for f in self._table]

    def __len__(self) -> int:
        return len(self._table)


ES = _Named(ENTITY_FIELDS, {
    "POS_X": "pos.trBase[0]", "POS_Y": "pos.trBase[1]", "POS_Z": "pos.trBase[2]",
    "VEL_X": "pos.trDelta[0]", "VEL_Y": "pos.trDelta[1]", "VEL_Z": "pos.trDelta[2]",
    "YAW": "apos.trBase[1]", "PITCH": "apos.trBase[0]", "ROLL": "apos.trBase[2]",
    "EVENT": "event", "ETYPE": "eType", "EVENTPARM": "eventParm",
    "TORSO_ANIM": "torsoAnim", "LEGS_ANIM": "legsAnim",
    "GROUND": "groundEntityNum", "EFLAGS": "eFlags",
    "OTHER_ENTITY": "otherEntityNum", "OTHER_ENTITY2": "otherEntityNum2",
    "WEAPON": "weapon", "CLIENTNUM": "clientNum",
    "ORIGIN2_X": "origin2[0]", "ORIGIN2_Y": "origin2[1]", "ORIGIN2_Z": "origin2[2]",
    "TR_TYPE": "pos.trType", "TR_TIME": "pos.trTime", "TR_DURATION": "pos.trDuration",
    "MODELINDEX": "modelindex", "FRAME": "frame", "SOLID": "solid",
})

PS = _Named(PLAYER_FIELDS, {
    "ORIGIN_X": "origin[0]", "ORIGIN_Y": "origin[1]", "ORIGIN_Z": "origin[2]",
    "VEL_X": "velocity[0]", "VEL_Y": "velocity[1]", "VEL_Z": "velocity[2]",
    "YAW": "viewangles[1]", "PITCH": "viewangles[0]", "ROLL": "viewangles[2]",
    "TORSO_ANIM": "torsoAnim", "LEGS_ANIM": "legsAnim",
    "GROUND": "groundEntityNum", "CLIENTNUM": "clientNum", "WEAPON": "weapon",
    "EVENT_SEQUENCE": "eventSequence", "EVENT0": "events[0]", "EVENT1": "events[1]",
    "EVENTPARM0": "eventParms[0]", "EVENTPARM1": "eventParms[1]",
    "EXTERNAL_EVENT": "externalEvent", "COMMAND_TIME": "commandTime",
    "JUMPPAD_ENT": "jumppad_ent", "PM_FLAGS": "pm_flags", "PM_TYPE": "pm_type",
})


# ── enumerations, from bg_public.h via the parser's verified tables ────────

class EntityType(IntEnum):
    GENERAL = 0
    PLAYER = 1
    ITEM = 2
    MISSILE = 3
    MOVER = 4
    BEAM = 5
    PORTAL = 6
    SPEAKER = 7
    PUSH_TRIGGER = 8
    TELEPORT_TRIGGER = 9
    INVISIBLE = 10
    GRAPPLE = 11
    TEAM = 12
    EVENTS = 13                 # eType >= this is a temp entity carrying EV_*


class Trajectory(IntEnum):
    STATIONARY = 0
    INTERPOLATE = 1
    LINEAR = 2
    LINEAR_STOP = 3
    SINE = 4
    GRAVITY = 5


class Event(IntEnum):
    """EV_* values PANTHEON reads. Verified against two independent readers
    (QLDT's entityEvents_QL and UberDemoTools' EntityEvents_73p) and against
    frequency in the corpus: code 20 fires ~9,800 times per demo, which is
    FIRE_WEAPON and not the stock-Q3 meaning of that slot."""
    ITEM_PICKUP = 15
    CHANGE_WEAPON = 18
    FIRE_WEAPON = 20
    USE_ITEM = 21
    DROP_WEAPON = 22
    NOAMMO = 23
    JUMP_PAD = 9
    JUMP = 10
    PLAYER_TELEPORT_IN = 39
    PLAYER_TELEPORT_OUT = 40
    MISSILE_HIT = 47
    MISSILE_MISS = 48
    MISSILE_MISS_METAL = 49
    RAILTRAIL = 50
    PAIN = 53
    DEATH1 = 54
    DEATH2 = 55
    DEATH3 = 56
    DROWN = 57
    OBITUARY = 58
    GIB_PLAYER = 63
    SCOREPLUM = 64


EVENT_SEQUENCE_BITS = 0x300      # EV_EVENT_BIT1|BIT2, masked off a raw event
ANIM_TOGGLEBIT = 128


class Weapon(IntEnum):
    """weapon_t. What an entity's `weapon` field holds."""
    NONE = 0
    GAUNTLET = 1
    MACHINEGUN = 2
    SHOTGUN = 3
    GRENADE_LAUNCHER = 4
    ROCKET_LAUNCHER = 5
    LIGHTNING = 6
    RAILGUN = 7
    PLASMAGUN = 8
    BFG = 9
    GRAPPLING_HOOK = 10
    NAILGUN = 11
    PROX_LAUNCHER = 12
    CHAINGUN = 13
    HMG = 14


class MeansOfDeath(IntEnum):
    """MOD_*. What an obituary's eventParm holds. A DIFFERENT SPACE from
    weapon_t: a rocket kill is weapon 5 but MOD 6/7."""
    UNKNOWN = 0
    SHOTGUN = 1
    GAUNTLET = 2
    MACHINEGUN = 3
    GRENADE = 4
    GRENADE_SPLASH = 5
    ROCKET = 6
    ROCKET_SPLASH = 7
    PLASMA = 8
    PLASMA_SPLASH = 9
    RAILGUN = 10
    LIGHTNING = 11
    BFG = 12
    BFG_SPLASH = 13
    WATER = 14
    SLIME = 15
    LAVA = 16
    CRUSH = 17
    TELEFRAG = 18
    FALLING = 19
    SUICIDE = 20
    TARGET_LASER = 21
    TRIGGER_HURT = 22
    GRAPPLE = 23


# weapon_t -> the MOD a direct kill with it produces. Derived, not guessed:
# the direct/splash pairs are how bg_public.h orders them.
MOD_FOR_WEAPON = {
    Weapon.GAUNTLET: MeansOfDeath.GAUNTLET,
    Weapon.MACHINEGUN: MeansOfDeath.MACHINEGUN,
    Weapon.SHOTGUN: MeansOfDeath.SHOTGUN,
    Weapon.GRENADE_LAUNCHER: MeansOfDeath.GRENADE,
    Weapon.ROCKET_LAUNCHER: MeansOfDeath.ROCKET,
    Weapon.LIGHTNING: MeansOfDeath.LIGHTNING,
    Weapon.RAILGUN: MeansOfDeath.RAILGUN,
    Weapon.PLASMAGUN: MeansOfDeath.PLASMA,
}
MOD_SPLASH = {
    MeansOfDeath.GRENADE: MeansOfDeath.GRENADE_SPLASH,
    MeansOfDeath.ROCKET: MeansOfDeath.ROCKET_SPLASH,
    MeansOfDeath.PLASMA: MeansOfDeath.PLASMA_SPLASH,
    MeansOfDeath.BFG: MeansOfDeath.BFG_SPLASH,
}


class Anim(IntEnum):
    """animNumber_t. Profiled on real players across five demos before it was
    trusted: torso carried {7,9,10,11} and legs {15,16,18,19,22}, each also
    appearing +128 (ANIM_TOGGLEBIT)."""
    TORSO_GESTURE = 6
    TORSO_ATTACK = 7
    TORSO_ATTACK2 = 8
    TORSO_DROP = 9
    TORSO_RAISE = 10
    TORSO_STAND = 11
    TORSO_STAND2 = 12
    LEGS_WALKCR = 13
    LEGS_WALK = 14
    LEGS_RUN = 15
    LEGS_BACK = 16
    LEGS_SWIM = 17
    LEGS_JUMP = 18
    LEGS_LAND = 19
    LEGS_JUMPB = 20
    LEGS_LANDB = 21
    LEGS_IDLE = 22
    LEGS_IDLECR = 23
    LEGS_TURN = 24


LEGS_GROUNDED = frozenset({Anim.LEGS_RUN, Anim.LEGS_BACK, Anim.LEGS_IDLE,
                           Anim.LEGS_LAND, Anim.LEGS_WALK, Anim.LEGS_WALKCR,
                           Anim.LEGS_IDLECR, Anim.LEGS_TURN})
LEGS_RUNNING = frozenset({Anim.LEGS_RUN, Anim.LEGS_BACK, Anim.LEGS_WALK})
LEGS_AIRBORNE = frozenset({Anim.LEGS_JUMP, Anim.LEGS_JUMPB})


class ConfigString(IntEnum):
    """Slots PANTHEON reads or writes. The CA round slots (661-664, 705) are
    not stock Q3: they were derived from five real Clan Arena demos and are
    documented in docs/reference/ca_round_grammar.md."""
    SERVERINFO = 0
    SYSTEMINFO = 1
    MESSAGE = 3
    MOTD = 4
    WARMUP = 5
    SCORES1 = 6
    SCORES2 = 7
    GAME_VERSION = 12
    LEVEL_START_TIME = 13
    INTERMISSION = 14
    ITEMS = 15
    ROUND_STATUS = 661          # \\time\\<future_ms>\\round\\<N>
    ROUND_TIME = 662
    RED_PLAYERS_LEFT = 663
    BLUE_PLAYERS_LEFT = 664
    ROUND_WINNERS = 705
    PLAYERS = 529               # + client number


class ServerCommand(IntEnum):
    BAD = 0
    NOP = 1
    GAMESTATE = 2
    CONFIGSTRING = 3
    BASELINE = 4
    SERVERCOMMAND = 5
    DOWNLOAD = 6
    SNAPSHOT = 7
    EOF = 8


# ── reading the engine's own tables back, for the test ─────────────────────

def parse_canonical_table(name: str, path: Path | None = None) -> list[tuple[str, str]]:
    """(member, width_expression) for one netField_t table in the engine
    source. Used by the test that keeps this file honest; not needed at
    runtime."""
    src = (path or CANONICAL_MSG_C).read_text(encoding="utf-8", errors="replace")
    start = src.index(f"netField_t\t{name}[]")
    body = src[src.index("{", start) + 1:src.index("};", start)]
    out: list[tuple[str, str]] = []
    for line in body.splitlines():
        line = line.split("//")[0].strip()
        if not line.startswith("{"):
            continue
        inner = line[line.index("(") + 1:line.rindex(")")] if "(" in line else ""
        rest = line[line.rindex(")") + 1:].strip(" ,{}")
        if inner and rest:
            out.append((inner, rest))
    return out


def canonical_bits(expr: str) -> int:
    """The engine writes widths as symbols; resolve them the way it does."""
    expr = expr.strip()
    table = {"GENTITYNUM_BITS": GENTITYNUM_BITS, "MAX_POWERUPS": MAX_POWERUPS}
    if expr in table:
        return table[expr]
    return abs(int(expr))
