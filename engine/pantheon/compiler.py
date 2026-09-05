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


# ── recorded events, as the engine sends them ──────────────────────────────
# Event codes come from the parser's own table (bg_public.h via demo_parse),
# never restated. Two delivery forms exist in the protocol and both are
# reproduced:
#   * on the PLAYER ENTITY (es->event | sequence bits): fire, jump pad, jump,
#     pain, death, teleport, weapon change, pickups. cgame plays them off the
#     body they belong to, so the sound and the flash come from the right
#     place.
#   * as a TEMP ENTITY (eType = ET_EVENTS + code): missile impacts, rail
#     trails, gibs. They happen at a world position, not on a body.
# A same-tick second event on one body goes out as a temp entity carrying the
# body's clientNum -- the engine's own "external event" path -- because an
# entity has one event field per snapshot.
def _event_codes() -> dict[str, int]:
    from engine.parser.demo_parse import _EV_NAMES
    codes: dict[str, int] = {}
    for code, name in _EV_NAMES.items():
        codes.setdefault(name, code)          # death -> EV_DEATH1
    return codes


EVENT_CODE = _event_codes()
ENTITY_EVENTS = {"fire_weapon", "jump_pad", "jump", "change_weapon", "pain",
                 "death", "drown", "teleport_in", "teleport_out",
                 "item_pickup", "use_item", "noammo", "drop_weapon"}
TEMP_EVENTS = {"missile_hit", "missile_miss", "railtrail", "gib_player"}
EV_SEQ_SHIFT = 8            # EV_EVENT_BIT1/2 live at 0x100/0x200
ENTITYNUM_WORLD = 1022
EVENT_SLOT0 = 640           # temp-entity slots for recorded impacts

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

    # ── recorded projectiles, by tick ──────────────────────────────────
    projectiles: dict[int, list] = {}
    for pk in getattr(scn, "_projectiles", []):
        projectiles.setdefault(ms(pk.t), []).append(pk)

    # ── recorded events, by tick ───────────────────────────────────────
    recorded: dict[int, list] = {}
    for e in scn._events:
        if not e.kind.startswith("recorded:"):
            continue
        kind = e.kind.split(":", 1)[1]
        if kind == "obituary":
            continue                    # authored through kill(), if the victim is cast
        if kind in ENTITY_EVENTS or kind in TEMP_EVENTS:
            recorded.setdefault(ms(e.t), []).append((kind, e))
    ev_seq: dict[int, int] = {}         # per entity, the sequence bits
    ent_by_actor = {name: a.client for name, a in scn.actors.items()}
    real_to_synth = {}
    for name, a in scn.actors.items():
        real_client = getattr(a, "_recorded_client", None)
        if real_client is not None:
            real_to_synth[real_client] = a.client

    obit_slot = 512
    MISSILE_SLOT0 = 700
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
            if k.stance is Stance.DEAD or not k.alive:
                continue                    # eliminated or not yet spawned
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
            if k.recorded:
                # A RECORDED performance: the demo's own numbers, verbatim.
                # The stance-derived animation above is only a fallback for
                # samples that carried no anim field.
                if k.legs_anim is not None:
                    st[W.ES_LEGS_ANIM] = k.legs_anim
                if k.torso_anim is not None:
                    st[W.ES_TORSO_ANIM] = k.torso_anim
                st[W.ES_APOS_PITCH] = k.pitch
                if k.velocity is not None:
                    st[W.ES_VEL_X], st[W.ES_VEL_Y], st[W.ES_VEL_Z] = k.velocity
                st[W.ES_GROUND] = 1023 if k.airborne else 0
                if k.weapon_num is not None:
                    st[W.ES_WEAPON] = k.weapon_num
            ents[a.client] = st

        # recorded missiles: each observed sample becomes the missile entity's
        # state for that tick, in the slot the demo used
        for pk in projectiles.get(now, []):
            ents[MISSILE_SLOT0 + (pk.entity % 200)] = {
                W.ES_ETYPE: 3,                          # ET_MISSILE
                W.ES_POS_X: pk.origin[0], W.ES_POS_Y: pk.origin[1],
                W.ES_POS_Z: pk.origin[2],
                W.ES_VEL_X: pk.velocity[0], W.ES_VEL_Y: pk.velocity[1],
                W.ES_VEL_Z: pk.velocity[2],
                W.ES_WEAPON: pk.weapon,
                W.ES_OTHER_ENT: scn.actors[pk.actor].client,   # the firer
                W.ES_CLIENTNUM: scn.actors[pk.actor].client,
            }

        for i, e in enumerate(rails.get(now, [])):
            slot = RAIL_SLOT0 + i
            toggles[slot] = toggles.get(slot, 0) ^ 0x100
            end = tuple(p if p else 0.5 for p in e.position)
            ents[slot] = W.railtrail_entity(scn.actors[e.actor].client, end,
                                            toggle=toggles[slot])

        # recorded events: the body's own event field first, then temp
        # entities for impacts and for any second same-tick event
        used_entity: set[int] = set()
        temp_i = 0
        for kind, e in recorded.get(now, []):
            client = ent_by_actor[e.actor]
            code = EVENT_CODE[kind]
            parm = int(e.parm) if e.parm is not None else 0
            weapon_num = e.weapon_num
            if kind in ENTITY_EVENTS and client in ents and client not in used_entity:
                seq = ev_seq.get(client, 0)
                ents[client][W.ES_EVENT] = code | ((seq & 3) << EV_SEQ_SHIFT)
                ents[client][W.ES_EVENTPARM] = parm
                ev_seq[client] = seq + 1
                used_entity.add(client)
                continue
            slot = EVENT_SLOT0 + temp_i
            temp_i += 1
            toggles[slot] = toggles.get(slot, 0) ^ 0x100
            pos = e.position or scn.actors[e.actor]._at(t).origin
            pos = tuple(p if p else 0.5 for p in pos)
            st = {
                W.ES_ETYPE: W.ET_EVENTS + code + (W.EV_TOGGLE_BITS & toggles[slot]),
                W.ES_POS_X: pos[0], W.ES_POS_Y: pos[1], W.ES_POS_Z: pos[2],
                W.ES_EVENTPARM: parm,
                W.ES_CLIENTNUM: client,
            }
            if weapon_num is not None:
                st[W.ES_WEAPON] = int(weapon_num)
            elif kind in ("fire_weapon", "missile_hit", "missile_miss"):
                st[W.ES_WEAPON] = ents.get(client, {}).get(W.ES_WEAPON, 0)
            if kind == "missile_hit":
                other = e.other_client
                st[W.ES_OTHER_ENT] = (real_to_synth.get(other, other)
                                      if other is not None else W.ENTITYNUM_NONE)
            elif kind == "missile_miss":
                st[W.ES_OTHER_ENT] = ENTITYNUM_WORLD
            ents[slot] = st

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

        cam = scn.camera_at(t)                     # the POV may move
        ps = {
            W.PS_CLIENTNUM: 0,
            W.PS_ORIGIN_X: cam.origin[0], W.PS_ORIGIN_Y: cam.origin[1],
            W.PS_ORIGIN_Z: cam.origin[2],
            W.PS_YAW: cam.yaw, W.PS_PITCH: getattr(cam, "pitch", 0.0),
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
