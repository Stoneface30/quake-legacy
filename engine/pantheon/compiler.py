"""Compile a RoundScenario into a .dm_73.

THIS IS THE ONLY PLACE protocol values appear above the codec. A scenario says
"BLUE_1 dies"; this decides that means an obituary temp entity, a decrement of
configstring 664, and a body whose legs stop animating.

THE GRAMMAR IS THE OBSERVED ONE. From `docs/reference/ca_round_grammar.md`,
derived from five real CA demos:

  * A round is ANNOUNCED before it starts. Configstring 661 carries
    `\\time\\<future_ms>\\round\\<N>` -- the countdown window.
  * The alive counters do NOT start at the roster size. Both are driven to 0
    and counted UP one at a time, interleaved between teams, and only then
    count down as players die. Emitting the final level instead of the ramp
    starts the HUD wrong, which is a thing a viewer sees.
  * Mid-demo configstring changes ride `cs <index> "<value>"` server commands.
    `svc_configstring` exists only inside the gamestate.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from engine.parser import dm73_write as W
from engine.pantheon.scenario import Weapon

if TYPE_CHECKING:                                   # pragma: no cover
    from engine.pantheon.scenario import RoundScenario

# Configstring indices, named once. Nothing above the compiler sees them.
CS_MESSAGE = 3
CS_MOTD = 4
CS_WARMUP = 5
CS_SCORES1, CS_SCORES2 = 6, 7
CS_GAME_VERSION = 12
CS_LEVEL_START_TIME = 13
CS_INTERMISSION = 14
CS_ITEMS = 15
CS_ROUND_STATUS = 661
CS_ROUND_TIME = 662
CS_RED_PLAYERS_LEFT = 663
CS_BLUE_PLAYERS_LEFT = 664
CS_ROUND_WINNERS = 705

PROVENANCE = "SYNTHETIC_EXPLAINER"

# Weapon slot -> means-of-death, taken from the parser's own MOD table rather
# than written out here. The first version guessed and mapped RAIL to 11, which
# the parser correctly read back as LIGHTNING -- a wrong weapon name on a
# teaching card, produced by exactly the kind of restated table this project
# has already been bitten by twice.
def _mod_table() -> dict[int, int]:
    from engine.parser.demo_parse import _MOD_NAMES
    by_name = {name: code for code, name in _MOD_NAMES.items()}
    # weapon slot -> the MOD name a kill with it produces
    slot_to_name = {
        1: "GAUNTLET", 2: "MACHINEGUN", 3: "SHOTGUN", 4: "GRENADE_SPLASH",
        5: "ROCKET_SPLASH", 6: "LIGHTNING", 7: "RAILGUN", 8: "PLASMA",
    }
    missing = [n for n in slot_to_name.values() if n not in by_name]
    if missing:                                   # pragma: no cover - guard
        raise RuntimeError(f"MOD names absent from the parser table: {missing}")
    return {slot: by_name[name] for slot, name in slot_to_name.items()}


MOD_BY_WEAPON = _mod_table()

# The alive ramp is interleaved between teams, as observed. One counter step
# per tick keeps it visible rather than instantaneous.
RAMP_STEP_MS = 50


def _alive_cs(team_value: int) -> int:
    return CS_RED_PLAYERS_LEFT if team_value == 1 else CS_BLUE_PLAYERS_LEFT


def compile_scenario(scn: "RoundScenario", *,
                     duration: float | None = None) -> W.DemoWriter:
    from engine.pantheon.scenario import Stance, Team, _LEGS, _TORSO, \
        _PLAYER_STRUCTURAL, SNAPSHOT_HZ, SNAPSHOT_MS

    if not scn.actors:
        raise ValueError("a round needs actors")
    if not scn._camera_path:
        raise ValueError("a demo needs an observer -- call scenario.observer()")

    end = duration if duration is not None else _natural_end(scn)
    frames = int(end * SNAPSHOT_HZ)
    base_ms = 1000                                   # first snapshot time

    def ms(t: float) -> int:
        return base_ms + int(round(t * 1000 / SNAPSHOT_MS)) * SNAPSHOT_MS

    # ── gamestate ──────────────────────────────────────────────────────
    cs: dict[int, str] = {
        W.CS_SERVERINFO: W.serverinfo(scn.map_name, gametype=4,
                                      hostname=scn.hostname, maxclients=16),
        W.CS_SYSTEMINFO: W.systeminfo(pure=0),
        CS_MESSAGE: "PANTHEON synthetic Clan Arena explainer",
        CS_MOTD: PROVENANCE,
        CS_WARMUP: "0",
        CS_SCORES1: "0", CS_SCORES2: "0",
        CS_GAME_VERSION: "baseq3-1",
        CS_LEVEL_START_TIME: "0",
        CS_INTERMISSION: "0",
        CS_ITEMS: "0" * 64,
        # Observed start-of-demo state: no round pending, nobody alive yet.
        CS_ROUND_STATUS: r"\time\-1\round\0",
        CS_ROUND_TIME: "0",
        CS_RED_PLAYERS_LEFT: "0",
        CS_BLUE_PLAYERS_LEFT: "0",
    }
    # Client 0 is the point of view, and it needs a CS_PLAYERS entry like any
    # other player: without one it has no team, and every teammate/enemy
    # decision downstream silently resolves to neither.
    cs[W.CS_PLAYERS + 0] = W.player_configstring(
        scn.observer_name, team=scn.observer_team.value,
        model="sarge/default", c1="4", c2="4")
    for a in scn.actors.values():
        cs[W.CS_PLAYERS + a.client] = W.player_configstring(
            a.name, team=a.team.value, model=f"{a.model}/{a.skin}",
            c1=a.c1, c2=a.c2)

    d = W.DemoWriter(client_num=0)
    d.write_gamestate(cs)
    seq = 1
    d.write_server_command(seq, f'print "{PROVENANCE}\n"'); seq += 1

    # ── the round-state script, in scenario time ───────────────────────
    # Each entry is (t_seconds, index, value). Built here so the snapshot loop
    # can emit them in order without knowing what any of it means.
    script: list[tuple[float, int, str]] = []

    if scn._round_begin is not None:
        announce = max(0.05, scn._round_begin - scn._countdown)
        # counters to zero, then the future announcement, then the ramp
        script.append((announce, CS_RED_PLAYERS_LEFT, "0"))
        script.append((announce, CS_BLUE_PLAYERS_LEFT, "0"))
        script.append((announce, CS_ROUND_STATUS,
                       rf"\time\{ms(scn._round_begin)}\round\1"))
        script.append((announce, CS_ROUND_TIME, str(ms(scn._round_begin))))

        red = [a for a in scn.actors.values() if a.team is Team.RED]
        blue = [a for a in scn.actors.values() if a.team is Team.BLUE]
        step = RAMP_STEP_MS / 1000.0
        t = announce + step
        for i in range(max(len(red), len(blue))):    # interleaved, as observed
            if i < len(red):
                script.append((t, CS_RED_PLAYERS_LEFT, str(i + 1)))
                t += step
            if i < len(blue):
                script.append((t, CS_BLUE_PLAYERS_LEFT, str(i + 1)))
                t += step

    for t, alive in scn._alive_log:                  # deaths decrement
        script.append((t, CS_RED_PLAYERS_LEFT, str(alive[Team.RED])))
        script.append((t, CS_BLUE_PLAYERS_LEFT, str(alive[Team.BLUE])))

    if scn._win:
        wt, team = scn._win
        script.append((wt, CS_ROUND_WINNERS, str(team.value)))
        script.append((wt, CS_SCORES1 if team is Team.RED else CS_SCORES2, "1"))
        script.append((wt + 0.05, CS_ROUND_TIME, "-1"))   # round is over
        script.append((wt + 0.05, CS_ROUND_STATUS, r"\time\-1\round\1"))

    if scn._reset_at is not None:
        rt = scn._reset_at
        script.append((rt, CS_RED_PLAYERS_LEFT, "0"))
        script.append((rt, CS_BLUE_PLAYERS_LEFT, "0"))
        script.append((rt, CS_ROUND_STATUS,
                       rf"\time\{ms(rt + scn._countdown)}\round\2"))
        step = RAMP_STEP_MS / 1000.0
        t = rt + step
        red = [a for a in scn.actors.values() if a.team is Team.RED]
        blue = [a for a in scn.actors.values() if a.team is Team.BLUE]
        for i in range(max(len(red), len(blue))):
            if i < len(red):
                script.append((t, CS_RED_PLAYERS_LEFT, str(i + 1))); t += step
            if i < len(blue):
                script.append((t, CS_BLUE_PLAYERS_LEFT, str(i + 1))); t += step

    script.sort(key=lambda r: r[0])
    pending = list(script)

    # ── kills, indexed by the tick they land on ────────────────────────
    kills: dict[int, list] = {}
    for e in scn._events:
        if e.kind != "kill":
            continue
        kills.setdefault(ms(e.t), []).append(e)

    # ── rail shots, indexed the same way ──────────────────────────────
    # A rail is hitscan: there is no projectile entity to animate, only an
    # event carrying where the beam ended. Authoring that event is not faking
    # a trajectory -- the engine draws the trail itself, with its own colour
    # resolution, which is exactly what a colour proof has to exercise.
    rails: dict[int, list] = {}
    for e in scn._events:
        if e.kind == "fire" and e.weapon is Weapon.RAIL and e.position:
            rails.setdefault(ms(e.t), []).append(e)

    obit_slot = 512
    RAIL_SLOT0 = 600            # well clear of players and of the obituary
    toggles: dict[int, int] = {}
    cam0 = scn._camera_path[0]

    # ── the snapshot stream ────────────────────────────────────────────
    for f in range(frames):
        t = f / SNAPSHOT_HZ
        now = base_ms + f * SNAPSHOT_MS

        ents: dict[int, dict] = {}
        for a in scn.actors.values():
            k = a._at(t)
            if k.stance is Stance.DEAD:
                continue                    # eliminated: the body is gone
            st = dict(_PLAYER_STRUCTURAL)
            st.update({
                W.ES_ETYPE: W.ET_PLAYER,
                W.ES_CLIENTNUM: a.client,
                W.ES_POS_X: k.origin[0], W.ES_POS_Y: k.origin[1],
                W.ES_POS_Z: k.origin[2],
                W.ES_APOS_YAW: k.yaw,
                W.ES_GROUND: 0,
                W.ES_WEAPON: k.weapon.value,
                W.ES_LEGS_ANIM: _LEGS[k.stance],
                W.ES_TORSO_ANIM: _TORSO[k.stance],
            })
            ents[a.client] = st

        for i, e in enumerate(rails.get(now, [])):
            slot = RAIL_SLOT0 + i
            toggles[slot] = toggles.get(slot, 0) ^ 0x100
            end = tuple(p if p else 0.5 for p in e.position)
            ents[slot] = W.railtrail_entity(scn.actors[e.actor].client, end,
                                            toggle=toggles[slot])

        for e in kills.get(now, []):
            victim = scn.actors[e.target]
            killer = scn.actors[e.actor]
            toggles[obit_slot] = toggles.get(obit_slot, 0) ^ 0x100
            pos = e.position or victim._at(t).origin
            # an event at exact zero has no position once encoded, so nudge
            pos = tuple(p if p else 0.5 for p in pos)
            ents[obit_slot] = W.obituary_entity(
                killer.client, victim.client,
                MOD_BY_WEAPON.get(e.weapon.value if e.weapon else 5, 7),
                pos, toggle=toggles[obit_slot])

        ps = {
            W.PS_CLIENTNUM: 0,
            W.PS_ORIGIN_X: cam0.origin[0], W.PS_ORIGIN_Y: cam0.origin[1],
            W.PS_ORIGIN_Z: cam0.origin[2],
            W.PS_YAW: cam0.yaw, W.PS_PITCH: 0.0,
            W.PS_WEAPON: 7,                          # the POV holds a weapon
            W.PS_GROUND: 0,
        }
        d.write_snapshot(now, ps, ents,
                         stats={W.STAT_HEALTH: 200, W.STAT_ARMOR: 100})

        # round-state changes due at or before this tick
        while pending and ms(pending[0][0]) <= now:
            _, idx, value = pending.pop(0)
            d.write_configstring(seq, idx, value)
            seq += 1

    return d


def _natural_end(scn) -> float:
    """How long the round runs if the caller does not say."""
    ends = [1.0]
    for a in scn.actors.values():
        if a._keys:
            ends.append(max(k.t for k in a._keys))
    for e in scn._events:
        ends.append(e.t)
    if scn._win:
        ends.append(scn._win[0])
    if scn._reset_at is not None:
        ends.append(scn._reset_at + scn._countdown + 1.0)
    return max(ends) + 1.0
